#!/usr/bin/env python3
"""Offline safety checks for the DysonX static preview shell."""

from __future__ import annotations

import pathlib
import subprocess
import sys
from html.parser import HTMLParser


ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
ROBOTS = ROOT / "robots.txt"
WORKFLOWS = ROOT / ".github" / "workflows"
RAW_FIXTURE = ROOT / "tests" / "fixtures" / "raw_items_v1.json"
PIPELINE_OUTPUT_DIR = ROOT / "tmp" / "dysonx_static_preview_check" / "v1_pipeline"

REMOVED_PUBLIC_ARTIFACTS = (
    "posts/page1.html",
    "posts/page2.html",
    "posts/page3.html",
    "posts/page4.html",
    "sitemap.xml",
)

DELETED_LEGACY_SCRIPT_TOKENS = (
    "scripts/aggregator.py",
    "scripts/openai_summary.py",
    "scripts/generate_sitemap.py",
    "hashFiles('feeds.json')",
    "git add posts/ sitemap.xml",
    "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}",
)


class IndexMetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.html_lang = ""
        self.title = ""
        self._in_title = False
        self.meta: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.visible_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "html":
            self.html_lang = attr_map.get("lang", "")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            self.meta.append(attr_map)
        elif tag == "link":
            self.links.append(attr_map)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title += text
        self.visible_text.append(text)

    def meta_content(self, key: str, value: str) -> str:
        key = key.lower()
        value = value.lower()
        for item in self.meta:
            if item.get(key, "").lower() == value:
                return item.get("content", "")
        return ""

    def canonical_href(self) -> str:
        for item in self.links:
            if item.get("rel", "").lower() == "canonical":
                return item.get("href", "")
        return ""


def fail(message: str) -> None:
    raise AssertionError(message)


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def parse_index() -> tuple[str, IndexMetadataParser]:
    if not INDEX.exists():
        fail("index.html is missing")
    html = read(INDEX)
    parser = IndexMetadataParser()
    parser.feed(html)
    return html, parser


def check_index_metadata(html: str, parser: IndexMetadataParser) -> None:
    if parser.html_lang.lower() != "en":
        fail('index.html must declare <html lang="en">')
    if "DysonX" not in parser.title or "AGI" not in parser.title:
        fail("index.html title must use DysonX AGI identity")
    if not parser.meta_content("name", "viewport"):
        fail("index.html must include viewport metadata")
    description = parser.meta_content("name", "description")
    if not description:
        fail("index.html must include English description metadata")
    if "DysonX" not in description or "Signals" not in description:
        fail("index.html description must preserve DysonX Signal identity")
    if parser.canonical_href() != "https://dysonx.ai/":
        fail("index.html must use the English canonical root URL")
    if not parser.meta_content("property", "og:title"):
        fail("index.html must include Open Graph title metadata")
    if not parser.meta_content("name", "twitter:title"):
        fail("index.html must include Twitter/X title metadata")
    if "<html lang=\"en\"" not in html:
        fail("index.html English canonical metadata should be explicit")


def check_identity_and_language_placeholder(parser: IndexMetadataParser) -> None:
    text = "\n".join(parser.visible_text)
    required_tokens = (
        "DysonX tracks the signals shaping AGI.",
        "AI / AGI Intelligence OS",
        "Signals",
        "Trackers",
        "AGI Map",
        "EN",
        "中文",
        "Real publishing not enabled yet",
    )
    missing = [token for token in required_tokens if token not in text]
    if missing:
        fail(f"index.html is missing DysonX preview identity tokens: {', '.join(missing)}")


def check_deleted_artifact_references(html: str) -> None:
    robot_text = read(ROBOTS) if ROBOTS.exists() else ""
    lower_html = html.lower()
    lower_robots = robot_text.lower()
    for artifact in REMOVED_PUBLIC_ARTIFACTS:
        if artifact.lower() in lower_html:
            fail(f"index.html references deleted artifact: {artifact}")
    if "sitemap.xml" in lower_robots:
        fail("robots.txt references deleted sitemap.xml")


def check_active_workflows() -> None:
    if not WORKFLOWS.exists():
        return
    offenders: dict[str, list[str]] = {}
    active_workflows = sorted(WORKFLOWS.glob("*.yml")) + sorted(WORKFLOWS.glob("*.yaml"))
    for path in active_workflows:
        text = read(path)
        matches = [token for token in DELETED_LEGACY_SCRIPT_TOKENS if token in text]
        if matches:
            offenders[path.name] = matches
    if offenders:
        details = "; ".join(f"{name}: {', '.join(tokens)}" for name, tokens in offenders.items())
        fail(f"active workflows reference deleted legacy scripts or artifacts: {details}")


def check_v1_dry_run_pipeline() -> None:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "dysonx_v1_pipeline.py"),
        "--raw-fixture",
        str(RAW_FIXTURE),
        "--output-dir",
        str(PIPELINE_OUTPUT_DIR),
        "--dry-run",
    ]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        fail(f"V1 dry-run pipeline failed: {detail}")
    summary_path = PIPELINE_OUTPUT_DIR / "pipeline_summary.json"
    if not summary_path.exists():
        fail("V1 dry-run pipeline did not write pipeline_summary.json")
    summary = read(summary_path)
    required_safety_flags = (
        '"dry_run": true',
        '"network_requests_performed": false',
        '"publishing_performed": false',
        '"real_llm_api_used": false',
        '"social_posting_performed": false',
    )
    missing = [flag for flag in required_safety_flags if flag not in summary]
    if missing:
        fail(f"V1 dry-run pipeline summary is missing safety flags: {', '.join(missing)}")


def run_checks() -> list[str]:
    html, parser = parse_index()
    checks = [
        ("index.html exists", lambda: None),
        ("index.html has English canonical metadata", lambda: check_index_metadata(html, parser)),
        ("index.html has viewport metadata", lambda: parser.meta_content("name", "viewport") or fail("viewport metadata missing")),
        ("index.html has DysonX identity", lambda: check_identity_and_language_placeholder(parser)),
        ("index.html has EN / Chinese switch placeholder", lambda: ("EN" in html and "中文" in html) or fail("language switch placeholder missing")),
        ("index.html avoids deleted public artifacts", lambda: check_deleted_artifact_references(html)),
        ("robots.txt avoids deleted sitemap.xml", lambda: check_deleted_artifact_references(html)),
        ("active workflows avoid deleted legacy scripts", check_active_workflows),
        ("V1 dry-run pipeline still works", check_v1_dry_run_pipeline),
    ]

    passed: list[str] = []
    for name, check in checks:
        check()
        passed.append(name)
    return passed


def main() -> int:
    try:
        passed = run_checks()
    except AssertionError as exc:
        print(f"[dysonx-static-preview-check] FAIL: {exc}")
        return 1
    for name in passed:
        print(f"[dysonx-static-preview-check] PASS: {name}")
    print("[dysonx-static-preview-check] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
