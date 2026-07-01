#!/usr/bin/env python3
"""Strict auto-merge gate for DysonX public Signals sync PRs."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlsplit


GATE_VERSION = "dysonx_public_signals_auto_merge_gate_v1"
ALLOWED_STATIC_FILES = {"signals/index.html", "signals/public_launch_manifest.json"}
MIN_PUBLIC_QUALITY = 80
ALLOWED_SOURCE_PRIORITIES = {"High", "Critical"}
ALLOWED_AGI_RELEVANCE = {"Medium", "High", "Critical"}
OFF_TOPIC_PUBLIC_TERMS = (
    "biology",
    "biomedical",
    "cattle",
    "dairy",
    "eclipse",
    "eclipses",
    "general news",
    "general science",
    "methane",
    "medicine",
    "oceanography",
    "poetry",
    "politics",
    "robot vacuum",
    "vacuum cleaner",
)
FORBIDDEN_TERMS = (
    "https://dysonx." "ai",
    "media." "energizeos.com",
    "source.dysonx." "invalid",
    "." "invalid",
    "." "test/",
    "tmp/" "production_publish_pack",
)
RAW_BODY_MARKERS = (
    "raw article body",
    "source-page body copied",
    "full article text",
    "verbatim article body",
)
INLINE_EVENT_PATTERN = re.compile(r"\son[a-z]+\s*=", re.IGNORECASE)


class AutoMergeGateError(RuntimeError):
    """Raised when the public Signals auto-merge gate must block."""


class HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.ids: set[str] = set()
        self.script_tags = 0
        self.iframe_tags = 0
        self.inline_event_handlers: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "script":
            self.script_tags += 1
        if tag == "iframe":
            self.iframe_tags += 1
        if "id" in attr_map and attr_map["id"]:
            self.ids.add(attr_map["id"])
        if "href" in attr_map:
            self.hrefs.append(attr_map["href"])
        self.inline_event_handlers.extend(key for key in attr_map if key.startswith("on"))


def normalize_path(value: str) -> str:
    return value.strip().lstrip("./")


def signal_slug_from_path(path: str) -> str | None:
    parts = pathlib.PurePosixPath(normalize_path(path)).parts
    if len(parts) == 3 and parts[0] == "signals" and parts[2] == "index.html":
        return parts[1]
    return None


def is_allowed_changed_file(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized in ALLOWED_STATIC_FILES:
        return True
    return signal_slug_from_path(normalized) is not None


def load_changed_files(path: str | None) -> list[str]:
    if not path:
        return []
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise AutoMergeGateError("changed files JSON must be a list of strings")
    return [normalize_path(item) for item in data]


def fail_if_forbidden_text(text: str, label: str) -> None:
    lowered = text.lower()
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            raise AutoMergeGateError(f"{label} contains forbidden term: {term}")
    for marker in RAW_BODY_MARKERS:
        if marker in lowered:
            raise AutoMergeGateError(f"{label} contains raw/source body marker: {marker}")


def public_path_exists(root: pathlib.Path, href: str) -> bool:
    path = urlsplit(href).path
    if path == "/":
        return (root / "index.html").exists()
    relative = path.lstrip("/")
    if path.endswith("/"):
        return (root / relative / "index.html").exists()
    return (root / relative).exists()


def check_html_file(path: pathlib.Path, root: pathlib.Path) -> None:
    if not path.exists():
        raise AutoMergeGateError(f"changed public HTML file is missing: {path}")
    text = path.read_text(encoding="utf-8", errors="ignore")
    fail_if_forbidden_text(text, str(path))
    if INLINE_EVENT_PATTERN.search(text):
        raise AutoMergeGateError(f"{path} contains inline event handler")
    parser = HrefParser()
    parser.feed(text)
    if parser.script_tags:
        raise AutoMergeGateError(f"{path} contains script tag")
    if parser.iframe_tags:
        raise AutoMergeGateError(f"{path} contains iframe tag")
    if parser.inline_event_handlers:
        raise AutoMergeGateError(f"{path} contains inline event handler attribute")
    for href in parser.hrefs:
        lowered = href.lower()
        if not href or href == "#":
            raise AutoMergeGateError(f"{path} contains empty or bare href")
        if any(term in lowered for term in FORBIDDEN_TERMS):
            raise AutoMergeGateError(f"{path} contains forbidden href: {href}")
        if href.startswith("#"):
            if href[1:] not in parser.ids:
                raise AutoMergeGateError(f"{path} links to missing same-page anchor: {href}")
            continue
        if href.startswith("/"):
            if not public_path_exists(root, href):
                raise AutoMergeGateError(f"{path} links to missing public path: {href}")
            continue
        if href.startswith(("http://", "https://")):
            parsed = urlsplit(href)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise AutoMergeGateError(f"{path} contains invalid external source link: {href}")
            continue
        raise AutoMergeGateError(f"{path} contains non-relative unsupported href: {href}")


def launched_by_slug(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    launched = manifest.get("launched")
    if not isinstance(launched, list):
        raise AutoMergeGateError("manifest launched must be a list")
    result: dict[str, dict[str, Any]] = {}
    for entry in launched:
        if not isinstance(entry, dict):
            raise AutoMergeGateError("manifest launched entries must be objects")
        slug = str(entry.get("slug") or "")
        if not slug:
            raise AutoMergeGateError("manifest launched entry is missing slug")
        result[slug] = entry
    return result


def changed_signal_slugs(changed_files: list[str], manifest: dict[str, Any]) -> set[str]:
    slugs = {slug for path in changed_files if (slug := signal_slug_from_path(path))}
    if not changed_files or not slugs:
        slugs = set(launched_by_slug(manifest))
    return slugs


def check_manifest_flags(manifest: dict[str, Any]) -> None:
    expected_false = {
        "openai_call_performed": False,
        "network_source_fetch_performed": False,
        "manual_external_deployment_performed": False,
    }
    for key, expected in expected_false.items():
        if manifest.get(key) is not expected:
            raise AutoMergeGateError(f"manifest {key} must be {expected}")


def off_topic_public_signal(entry: dict[str, Any]) -> bool:
    haystack = " ".join(
        str(entry.get(key) or "")
        for key in ("title", "summary", "source_name", "source_priority", "agi_relevance")
    ).lower()
    return any(term in haystack for term in OFF_TOPIC_PUBLIC_TERMS)


def check_entry(entry: dict[str, Any], *, min_quality: float, allowed_priorities: set[str], allowed_agi_relevance: set[str], require_attribution_complete: bool, require_safe_summary_only: bool) -> None:
    slug = str(entry.get("slug") or "<missing-slug>")
    if not str(entry.get("title") or "").strip():
        raise AutoMergeGateError(f"{slug} title is missing")
    if not str(entry.get("summary") or "").strip():
        raise AutoMergeGateError(f"{slug} summary is missing")
    try:
        quality = float(entry.get("quality_hint"))
    except (TypeError, ValueError):
        raise AutoMergeGateError(f"{slug} quality_hint is missing or non-numeric") from None
    if quality < min_quality:
        raise AutoMergeGateError(f"{slug} quality_hint {quality:g} is below {min_quality:g}")
    if str(entry.get("source_priority") or "") not in allowed_priorities:
        raise AutoMergeGateError(f"{slug} source_priority must be High or Critical")
    if str(entry.get("agi_relevance") or "") not in allowed_agi_relevance:
        raise AutoMergeGateError(f"{slug} agi_relevance must be Medium, High, or Critical")
    if require_attribution_complete and str(entry.get("attribution_status") or "") != "Complete":
        raise AutoMergeGateError(f"{slug} attribution_status must be Complete")
    if require_safe_summary_only and str(entry.get("copyright_status") or "") != "Safe Summary Only":
        raise AutoMergeGateError(f"{slug} copyright_status must be Safe Summary Only")
    source_url = str(entry.get("source_url") or "")
    parsed = urlsplit(source_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise AutoMergeGateError(f"{slug} source_url must be absolute http/https")
    if off_topic_public_signal(entry):
        raise AutoMergeGateError(f"{slug} is off-topic for public Signals")


def run_gate(args: argparse.Namespace) -> None:
    manifest_path = pathlib.Path(args.manifest)
    root = manifest_path.parent.parent
    manifest_text = manifest_path.read_text(encoding="utf-8")
    fail_if_forbidden_text(manifest_text, str(manifest_path))
    manifest = json.loads(manifest_text)
    if not isinstance(manifest, dict):
        raise AutoMergeGateError("manifest must be a JSON object")
    check_manifest_flags(manifest)

    changed_files = load_changed_files(args.changed_files_json)
    for changed_file in changed_files:
        if not is_allowed_changed_file(changed_file):
            raise AutoMergeGateError(f"changed file is outside allowed public Signals paths: {changed_file}")

    entries = launched_by_slug(manifest)
    slugs_to_check = changed_signal_slugs(changed_files, manifest)
    if not slugs_to_check:
        raise AutoMergeGateError("no changed or launched Signal pages found")

    for slug in slugs_to_check:
        entry = entries.get(slug)
        if not entry:
            raise AutoMergeGateError(f"changed Signal page has no manifest entry: {slug}")
        check_entry(
            entry,
            min_quality=args.min_quality,
            allowed_priorities=set(args.allowed_priorities.split(",")),
            allowed_agi_relevance=set(args.allowed_agi_relevance.split(",")),
            require_attribution_complete=args.require_attribution_complete,
            require_safe_summary_only=args.require_safe_summary_only,
        )

    paths_to_check = {path for path in changed_files if path.endswith(".html")}
    if not changed_files:
        paths_to_check = {"signals/index.html", *[f"signals/{slug}/index.html" for slug in slugs_to_check]}
    for relative_path in sorted(paths_to_check):
        check_html_file(root / relative_path, root)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gate DysonX public Signals auto-merge candidates.")
    parser.add_argument("--manifest", required=True, help="Path to signals/public_launch_manifest.json.")
    parser.add_argument("--changed-files-json", help="Optional JSON list of changed files.")
    parser.add_argument("--min-quality", type=float, default=MIN_PUBLIC_QUALITY)
    parser.add_argument("--allowed-priorities", default="High,Critical")
    parser.add_argument("--allowed-agi-relevance", default="Medium,High,Critical")
    parser.add_argument("--require-attribution-complete", action="store_true")
    parser.add_argument("--require-safe-summary-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run_gate(args)
    except (AutoMergeGateError, OSError, json.JSONDecodeError) as exc:
        print(f"[{GATE_VERSION}] FAIL: {exc}", file=sys.stderr)
        return 2
    print(f"[{GATE_VERSION}] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
