#!/usr/bin/env python3
"""Strict auto-merge gate for DysonX public Signals sync PRs."""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlsplit

from dysonx_public_signals_contract import (
    ALLOWED_ARTIFACT_CLASSES,
    ARTIFACT_JSON_FEED,
    ARTIFACT_PUBLIC_ARTIFACT_MANIFEST,
    ARTIFACT_PUBLIC_LAUNCH_MANIFEST,
    ARTIFACT_ROBOTS_TXT,
    ARTIFACT_RSS_XML,
    ARTIFACT_SIGNAL_HTML,
    ARTIFACT_SIGNALS_INDEX_HTML,
    ARTIFACT_SITEMAP_XML,
    PUBLIC_SEO_BASE_URL,
    PUBLIC_SIGNAL_CONTRACT_VERSION,
    artifact_class_for_path,
    allowed_embeds_for_artifact_class,
    is_allowed_public_artifact_path,
    normalize_public_path,
    signal_slug_from_public_path,
)
from dysonx_public_signals_topic_policy import (
    has_core_public_topic as topic_has_core_public_topic,
    off_topic_public_signal as topic_off_topic_public_signal,
)

GATE_VERSION = "dysonx_public_signals_auto_merge_gate_v1"
MIN_PUBLIC_QUALITY = 80
ALLOWED_SOURCE_PRIORITIES = {"High", "Critical"}
ALLOWED_AGI_RELEVANCE = {"Medium", "High", "Critical"}
FORBIDDEN_TERMS = (
    "https://dysonx." "ai",
    "source.dysonx." "invalid",
    "." "invalid",
    "." "test/",
    "tmp/" "production_publish_pack",
)
RAW_BODY_MARKERS = (
    "article body:",
    "full article text",
    "raw source body",
    "raw body",
    "raw_body",
    "scraped body",
    "source body:",
    "source-page body copied",
    "verbatim source",
)
INLINE_EVENT_PATTERN = re.compile(r"\son[a-z]+\s*=", re.IGNORECASE)
ARTIFACT_MANIFEST_ALLOWED_TOP_LEVEL_RAW_VOCABULARY_FIELDS = {"forbidden_content_classes"}
ARTIFACT_MANIFEST_ALLOWED_ENTRY_FIELDS = {
    "allowed_embeds",
    "artifact_class",
    "contract_version",
    "generated_from_public_signal_manifest",
    "material_signature",
    "path",
    "policy_version",
    "slug",
}


class AutoMergeGateError(RuntimeError):
    """Raised when the public Signals auto-merge gate must block."""


class PublicHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []
        self.ids: set[str] = set()
        self.scripts: list[dict[str, Any]] = []
        self._script_stack: list[dict[str, Any]] = []
        self.iframe_tags = 0
        self.inline_event_handlers: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "script":
            script = {"attrs": attr_map, "content": ""}
            self.scripts.append(script)
            self._script_stack.append(script)
        if tag == "iframe":
            self.iframe_tags += 1
        if "id" in attr_map and attr_map["id"]:
            self.ids.add(attr_map["id"])
        if "href" in attr_map:
            self.hrefs.append(attr_map["href"])
        self.inline_event_handlers.extend(key for key in attr_map if key.startswith("on"))

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._script_stack:
            self._script_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._script_stack:
            self._script_stack[-1]["content"] += data


def signal_slug_from_path(path: str) -> str | None:
    return signal_slug_from_public_path(path)


def is_allowed_changed_file(path: str) -> bool:
    return is_allowed_public_artifact_path(path)


def load_changed_files(path: str | None) -> list[str]:
    if not path:
        return []
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
        raise AutoMergeGateError("changed files JSON must be a list of strings")
    return [normalize_public_path(item) for item in data]


def fail_if_forbidden_terms(text: str, label: str) -> None:
    lowered = text.lower()
    for term in FORBIDDEN_TERMS:
        if term in lowered:
            raise AutoMergeGateError(f"{label} contains forbidden term: {term}")


def fail_if_raw_body_markers(text: str, label: str) -> None:
    lowered = text.lower()
    for marker in RAW_BODY_MARKERS:
        if marker in lowered:
            raise AutoMergeGateError(f"{label} contains raw/source body marker: {marker}")


def fail_if_forbidden_text(text: str, label: str) -> None:
    fail_if_forbidden_terms(text, label)
    fail_if_raw_body_markers(text, label)


def fail_if_raw_body_markers_in_values(value: Any, label: str) -> None:
    if isinstance(value, str):
        fail_if_raw_body_markers(value, label)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            fail_if_raw_body_markers_in_values(item, f"{label}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            fail_if_raw_body_markers_in_values(item, f"{label}.{key}")


def load_json_object(path: pathlib.Path, label: str, *, scan_raw_body: bool = True) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    fail_if_forbidden_terms(text, label)
    if scan_raw_body:
        fail_if_raw_body_markers(text, label)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise AutoMergeGateError(f"{label} must be a JSON object")
    return data


def public_path_exists(root: pathlib.Path, href: str) -> bool:
    path = urlsplit(href).path
    if path == "/":
        return (root / "index.html").exists()
    relative = path.lstrip("/")
    if path.endswith("/"):
        return (root / relative / "index.html").exists()
    return (root / relative).exists()


def validate_json_ld_script(script: dict[str, Any], artifact_class: str, label: str) -> None:
    attrs = script["attrs"]
    if attrs.get("src"):
        raise AutoMergeGateError(f"{label} contains external script src")
    if attrs.get("type") != "application/ld+json":
        raise AutoMergeGateError(f"{label} contains non-JSON-LD script tag")
    content = html.unescape(str(script.get("content") or "")).strip()
    fail_if_forbidden_text(content, f"{label} JSON-LD")
    if INLINE_EVENT_PATTERN.search(content) or "javascript:" in content.lower():
        raise AutoMergeGateError(f"{label} JSON-LD contains unsafe script-like text")
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise AutoMergeGateError(f"{label} contains malformed JSON-LD") from exc
    nodes = data if isinstance(data, list) else [data]
    allowed_types = {
        ARTIFACT_SIGNAL_HTML: {"TechArticle", "Article"},
        ARTIFACT_SIGNALS_INDEX_HTML: {"Organization"},
    }.get(artifact_class, set())
    if not allowed_types:
        raise AutoMergeGateError(f"{label} is not allowed to contain JSON-LD")
    for node in nodes:
        if not isinstance(node, dict):
            raise AutoMergeGateError(f"{label} JSON-LD nodes must be objects")
        raw_type = node.get("@type")
        node_types = set(raw_type if isinstance(raw_type, list) else [raw_type])
        if not node_types.intersection(allowed_types):
            raise AutoMergeGateError(f"{label} JSON-LD type must be one of {sorted(allowed_types)}")
        payload = json.dumps(node, sort_keys=True)
        if "javascript:" in payload.lower() or INLINE_EVENT_PATTERN.search(payload):
            raise AutoMergeGateError(f"{label} JSON-LD contains unsafe script-like text")
        if PUBLIC_SEO_BASE_URL in payload:
            continue
        if any(str(value).startswith("http") for value in node.values() if isinstance(value, str)):
            # External source citations are allowed, but public page URLs must remain canonical.
            continue


def check_html_file(path: pathlib.Path, root: pathlib.Path, artifact_class: str) -> None:
    if not path.exists():
        raise AutoMergeGateError(f"changed public HTML file is missing: {path}")
    text = path.read_text(encoding="utf-8", errors="ignore")
    fail_if_forbidden_text(text, str(path))
    if INLINE_EVENT_PATTERN.search(text):
        raise AutoMergeGateError(f"{path} contains inline event handler")
    parser = PublicHtmlParser()
    parser.feed(text)
    if parser.iframe_tags:
        raise AutoMergeGateError(f"{path} contains iframe tag")
    if parser.inline_event_handlers:
        raise AutoMergeGateError(f"{path} contains inline event handler attribute")
    for script in parser.scripts:
        validate_json_ld_script(script, artifact_class, str(path))
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


def validate_robots(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    expected = f"User-agent: *\nAllow: /\nSitemap: {PUBLIC_SEO_BASE_URL}/sitemap.xml\n"
    fail_if_forbidden_text(text, str(path))
    if text != expected:
        raise AutoMergeGateError("robots.txt must only allow crawling and point to the production sitemap")


def validate_sitemap(path: pathlib.Path, launched_slugs: set[str]) -> None:
    text = path.read_text(encoding="utf-8")
    fail_if_forbidden_text(text, str(path))
    root = ET.fromstring(text)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    allowed_urls = {f"{PUBLIC_SEO_BASE_URL}/", f"{PUBLIC_SEO_BASE_URL}/signals/"}
    allowed_urls.update(f"{PUBLIC_SEO_BASE_URL}/signals/{slug}/" for slug in launched_slugs)
    found_urls: set[str] = set()
    for url_node in root.findall("sm:url", namespace):
        loc = (url_node.findtext("sm:loc", default="", namespaces=namespace) or "").strip()
        lastmod = (url_node.findtext("sm:lastmod", default="", namespaces=namespace) or "").strip()
        if loc not in allowed_urls:
            raise AutoMergeGateError(f"sitemap contains non-canonical or blocked URL: {loc}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lastmod):
            raise AutoMergeGateError(f"sitemap lastmod must be stable YYYY-MM-DD: {lastmod}")
        found_urls.add(loc)
    required = {f"{PUBLIC_SEO_BASE_URL}/", f"{PUBLIC_SEO_BASE_URL}/signals/"}
    if not required.issubset(found_urls):
        raise AutoMergeGateError("sitemap must include homepage and /signals/")


def validate_rss(path: pathlib.Path, entries: dict[str, dict[str, Any]]) -> None:
    text = path.read_text(encoding="utf-8")
    fail_if_forbidden_text(text, str(path))
    root = ET.fromstring(text)
    items = root.findall("./channel/item")
    if len(items) > 30:
        raise AutoMergeGateError("rss.xml must not include more than 30 items")
    summaries = {entry.get("summary", "") for entry in entries.values()}
    for item in items:
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        source = item.find("source")
        if not link.startswith(f"{PUBLIC_SEO_BASE_URL}/signals/"):
            raise AutoMergeGateError(f"rss.xml item link must be canonical public URL: {link}")
        if description not in summaries:
            raise AutoMergeGateError("rss.xml item description must match summary-only manifest content")
        if source is None or not (source.attrib.get("url") or "").startswith(("http://", "https://")):
            raise AutoMergeGateError("rss.xml item source attribution URL is missing")


def validate_json_feed(path: pathlib.Path, entries: dict[str, dict[str, Any]]) -> None:
    data = load_json_object(path, "feed.json")
    items = data.get("items")
    if not isinstance(items, list):
        raise AutoMergeGateError("feed.json items must be a list")
    if len(items) > 30:
        raise AutoMergeGateError("feed.json must not include more than 30 items")
    summaries = {entry.get("summary", "") for entry in entries.values()}
    for item in items:
        if not isinstance(item, dict):
            raise AutoMergeGateError("feed.json items must be objects")
        url = str(item.get("url") or "")
        content_text = str(item.get("content_text") or "")
        if not url.startswith(f"{PUBLIC_SEO_BASE_URL}/signals/"):
            raise AutoMergeGateError(f"feed.json item URL must be canonical public URL: {url}")
        if content_text not in summaries:
            raise AutoMergeGateError("feed.json content_text must match summary-only manifest content")
        external_url = str(item.get("external_url") or "")
        if external_url and not external_url.startswith(("http://", "https://")):
            raise AutoMergeGateError("feed.json external_url must be absolute http/https when present")


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


def validate_public_launch_manifest_raw_body_fields(manifest: dict[str, Any]) -> None:
    fail_if_raw_body_markers_in_values(manifest.get("launched", []), "public_launch_manifest.launched")


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
    return topic_off_topic_public_signal(entry)


def has_core_public_topic(entry: dict[str, Any]) -> bool:
    return topic_has_core_public_topic(entry)


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
    if not has_core_public_topic(entry):
        raise AutoMergeGateError(f"{slug} is missing a core DysonX public topic")


def load_artifact_manifest(root: pathlib.Path) -> dict[str, Any]:
    path = root / "signals" / "public_artifact_manifest.json"
    if not path.exists():
        raise AutoMergeGateError("signals/public_artifact_manifest.json is missing")
    data = load_json_object(path, "public artifact manifest", scan_raw_body=False)
    if data.get("contract_version") != PUBLIC_SIGNAL_CONTRACT_VERSION:
        raise AutoMergeGateError("public artifact manifest has unsupported contract_version")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        raise AutoMergeGateError("public artifact manifest artifacts must be a list")
    validate_artifact_manifest_raw_body_fields(data)
    return data


def validate_artifact_manifest_raw_body_fields(artifact_manifest: dict[str, Any]) -> None:
    for key, value in artifact_manifest.items():
        if key in ARTIFACT_MANIFEST_ALLOWED_TOP_LEVEL_RAW_VOCABULARY_FIELDS or key == "artifacts":
            continue
        fail_if_raw_body_markers_in_values(value, f"public_artifact_manifest.{key}")
    artifacts = artifact_manifest.get("artifacts", [])
    if not isinstance(artifacts, list):
        return
    for index, item in enumerate(artifacts):
        if not isinstance(item, dict):
            continue
        for key, value in item.items():
            if key not in ARTIFACT_MANIFEST_ALLOWED_ENTRY_FIELDS:
                fail_if_raw_body_markers_in_values(value, f"public_artifact_manifest.artifacts[{index}].{key}")
                continue
            if key in {"path", "slug", "material_signature"}:
                fail_if_raw_body_markers_in_values(value, f"public_artifact_manifest.artifacts[{index}].{key}")


def artifact_entries_by_path(artifact_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    for item in artifact_manifest.get("artifacts", []):
        if not isinstance(item, dict):
            raise AutoMergeGateError("artifact manifest entries must be objects")
        path = normalize_public_path(str(item.get("path") or ""))
        artifact_class = str(item.get("artifact_class") or "")
        if not path:
            raise AutoMergeGateError("artifact manifest entry missing path")
        if path in entries:
            raise AutoMergeGateError(f"artifact manifest declares duplicate path: {path}")
        if artifact_class not in ALLOWED_ARTIFACT_CLASSES:
            raise AutoMergeGateError(f"artifact manifest declares unknown artifact_class: {artifact_class}")
        expected_class = artifact_class_for_path(path)
        if expected_class != artifact_class:
            raise AutoMergeGateError(f"artifact manifest class/path mismatch for {path}: {artifact_class}")
        if item.get("contract_version") != PUBLIC_SIGNAL_CONTRACT_VERSION:
            raise AutoMergeGateError(f"artifact manifest entry has unsupported contract_version: {path}")
        declared_embeds = item.get("allowed_embeds")
        if declared_embeds != allowed_embeds_for_artifact_class(artifact_class):
            raise AutoMergeGateError(f"artifact manifest entry has wrong allowed_embeds: {path}")
        entries[path] = item
    return entries


def validate_changed_files_declared(changed_files: list[str], artifact_entries: dict[str, dict[str, Any]]) -> None:
    for changed_file in changed_files:
        if not is_allowed_changed_file(changed_file):
            raise AutoMergeGateError(f"changed file is outside allowed public Signals paths: {changed_file}")
        if changed_file not in artifact_entries:
            raise AutoMergeGateError(f"changed public artifact is not declared: {changed_file}")


def validate_public_artifact(path: str, root: pathlib.Path, artifact_class: str, entries: dict[str, dict[str, Any]]) -> None:
    full_path = root / path
    if not full_path.exists():
        raise AutoMergeGateError(f"changed public artifact is missing: {path}")
    if artifact_class in {ARTIFACT_SIGNAL_HTML, ARTIFACT_SIGNALS_INDEX_HTML}:
        check_html_file(full_path, root, artifact_class)
    elif artifact_class == ARTIFACT_ROBOTS_TXT:
        validate_robots(full_path)
    elif artifact_class == ARTIFACT_SITEMAP_XML:
        validate_sitemap(full_path, set(entries))
    elif artifact_class == ARTIFACT_RSS_XML:
        validate_rss(full_path, entries)
    elif artifact_class == ARTIFACT_JSON_FEED:
        validate_json_feed(full_path, entries)
    elif artifact_class == ARTIFACT_PUBLIC_LAUNCH_MANIFEST:
        manifest = load_json_object(full_path, path, scan_raw_body=False)
        validate_public_launch_manifest_raw_body_fields(manifest)
    elif artifact_class == ARTIFACT_PUBLIC_ARTIFACT_MANIFEST:
        artifact_manifest = load_json_object(full_path, path, scan_raw_body=False)
        validate_artifact_manifest_raw_body_fields(artifact_manifest)
    else:
        raise AutoMergeGateError(f"unsupported artifact class: {artifact_class}")


def run_gate(args: argparse.Namespace) -> None:
    manifest_path = pathlib.Path(args.manifest)
    root = manifest_path.parent.parent
    manifest = load_json_object(manifest_path, str(manifest_path), scan_raw_body=False)
    validate_public_launch_manifest_raw_body_fields(manifest)
    check_manifest_flags(manifest)
    artifact_manifest = load_artifact_manifest(root)
    artifact_entries = artifact_entries_by_path(artifact_manifest)

    changed_files = load_changed_files(args.changed_files_json)
    validate_changed_files_declared(changed_files, artifact_entries)

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

    paths_to_check = set(changed_files)
    if not changed_files:
        paths_to_check = {
            "signals/index.html",
            "signals/public_launch_manifest.json",
            "signals/public_artifact_manifest.json",
            "robots.txt",
            "sitemap.xml",
            "rss.xml",
            "feed.json",
            *[f"signals/{slug}/index.html" for slug in slugs_to_check],
        }
    for relative_path in sorted(paths_to_check):
        artifact = artifact_entries.get(relative_path)
        if not artifact:
            raise AutoMergeGateError(f"public artifact is not declared: {relative_path}")
        validate_public_artifact(relative_path, root, str(artifact["artifact_class"]), entries)


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
