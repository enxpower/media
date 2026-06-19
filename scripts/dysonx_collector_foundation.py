#!/usr/bin/env python3
"""DysonX Collector Foundation V1.

Collects fixture-safe Source records into RawItem JSON records. This script does
not mutate Notion, call live GitHub APIs, scrape article bodies, call LLM APIs,
publish pages, post to social platforms, or deploy anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from dysonx_raw_item_storage import STORE_VERSION, write_raw_item_store


DEFAULT_REPORT_PATH = pathlib.Path("tmp/dysonx_collector_report.json")
DEFAULT_RAW_STORE_PATH = pathlib.Path("tmp/dysonx_raw_items_store.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: str | pathlib.Path, data: dict[str, Any]) -> None:
    output_path = pathlib.Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_source_store(path: str | pathlib.Path) -> list[dict[str, Any]]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Source store must be a JSON object")
    sources = data.get("sources")
    if not isinstance(sources, list) or not all(isinstance(source, dict) for source in sources):
        raise ValueError("Source store must contain a sources list")
    return sources


def fixture_path(value: str, base_dir: pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(value)
    if not path.is_absolute():
        path = base_dir / path
    return path


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def canonicalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = re.sub(r"/+", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, "", ""))


def raw_item_id(source_id: str, canonical_url: str, title: str) -> str:
    digest = hashlib.sha256(f"{source_id}|{canonical_url}|{title}".encode("utf-8")).hexdigest()[:16]
    return f"raw_{digest}"


def source_fixture(source: dict[str, Any], base_dir: pathlib.Path) -> pathlib.Path | None:
    fixture = source.get("collector_fixture") or source.get("fixture_path")
    if fixture:
        return fixture_path(str(fixture), base_dir)
    url = str(source.get("url") or "")
    if url and not url.startswith(("http://", "https://")):
        return fixture_path(url, base_dir)
    return None


def select_collector(source: dict[str, Any]) -> str:
    source_type = str(source.get("source_type") or "").lower()
    platform = str(source.get("platform") or "").lower()
    url = str(source.get("url") or "").lower()

    if "github" in platform or "github" in source_type or source.get("github_releases_fixture"):
        return "github_release_fixture"
    if "manual" in platform or "manual" in source_type:
        return "manual_url"
    if "rss" in platform or "rss" in source_type or url.endswith((".rss", ".xml")):
        return "rss"
    return "manual_url"


def normalize_raw_item(source: dict[str, Any], item: dict[str, Any], collected_at: str) -> dict[str, Any]:
    title = normalize_space(str(item.get("raw_title") or item.get("title") or ""))
    original_url = str(item.get("original_url") or item.get("url") or source.get("url") or "")
    canonical_url = canonicalize_url(original_url)
    source_id = str(source["id"])
    raw_content = item.get("raw_content")
    raw_excerpt = item.get("raw_excerpt")
    content_hash = hashlib.sha256(
        f"{title}|{canonical_url}|{raw_content or raw_excerpt or ''}".encode("utf-8")
    ).hexdigest()
    return {
        "id": raw_item_id(source_id, canonical_url, title),
        "source_id": source_id,
        "source_name": str(source.get("name") or ""),
        "source_type": str(source.get("source_type") or ""),
        "original_url": original_url,
        "canonical_url": canonical_url,
        "raw_title": title,
        "raw_content": raw_content,
        "raw_excerpt": raw_excerpt,
        "raw_author": item.get("raw_author"),
        "raw_published_at": item.get("raw_published_at"),
        "fetched_at": collected_at,
        "content_hash": content_hash,
        "fetch_status": str(item.get("fetch_status") or "collected"),
        "detected_language": item.get("detected_language") or source.get("language") or "English",
        "error": item.get("error"),
        "metadata": dict(item.get("metadata") or {}),
    }


def collect_rss(source: dict[str, Any], base_dir: pathlib.Path) -> list[dict[str, Any]]:
    path = source_fixture(source, base_dir)
    if path is None:
        return [
            {
                "title": "",
                "url": str(source.get("url") or ""),
                "fetch_status": "skipped",
                "error": "RSS collector V1 requires a local fixture path",
            }
        ]
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    items: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        title = item.findtext("title") or ""
        link = item.findtext("link") or ""
        description = item.findtext("description") or ""
        published = item.findtext("pubDate") or item.findtext("published") or ""
        items.append(
            {
                "title": title,
                "url": link,
                "raw_excerpt": normalize_space(description),
                "raw_published_at": published,
                "metadata": {"collector": "rss", "fixture_path": str(path)},
            }
        )
    return items


def collect_manual_url(source: dict[str, Any], _base_dir: pathlib.Path) -> list[dict[str, Any]]:
    title = f"Manual URL placeholder: {source.get('name')}"
    return [
        {
            "title": title,
            "url": str(source.get("url") or ""),
            "raw_excerpt": "",
            "raw_content": None,
            "raw_published_at": None,
            "metadata": {"collector": "manual_url", "metadata_only": True},
        }
    ]


def collect_github_release_fixture(source: dict[str, Any], base_dir: pathlib.Path) -> list[dict[str, Any]]:
    fixture = source.get("github_releases_fixture") or source.get("collector_fixture")
    if not fixture:
        return [
            {
                "title": "",
                "url": str(source.get("url") or ""),
                "fetch_status": "skipped",
                "error": "GitHub release collector V1 requires fixture data",
            }
        ]
    path = fixture_path(str(fixture), base_dir)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("GitHub release fixture must contain a list")
    items: list[dict[str, Any]] = []
    for release in data:
        if not isinstance(release, dict):
            continue
        items.append(
            {
                "title": str(release.get("name") or release.get("tag_name") or ""),
                "url": str(release.get("html_url") or source.get("url") or ""),
                "raw_excerpt": normalize_space(str(release.get("body") or "")),
                "raw_published_at": release.get("published_at"),
                "metadata": {
                    "collector": "github_release_fixture",
                    "tag_name": release.get("tag_name"),
                    "fixture_path": str(path),
                },
            }
        )
    return items


COLLECTORS = {
    "rss": collect_rss,
    "manual_url": collect_manual_url,
    "github_release_fixture": collect_github_release_fixture,
}


def deduplicate_raw_items(raw_items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seen: dict[tuple[str, str, str], dict[str, Any]] = {}
    unique_items: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    for item in raw_items:
        key = (
            str(item["source_id"]),
            str(item["canonical_url"]),
            str(item["raw_title"]).lower(),
        )
        if key in seen:
            results.append(
                {
                    "status": "duplicate",
                    "raw_item_id": item["id"],
                    "duplicate_of": seen[key]["id"],
                    "canonical_url": item["canonical_url"],
                    "source_id": item["source_id"],
                }
            )
            continue
        seen[key] = item
        unique_items.append(item)
        results.append(
            {
                "status": "unique",
                "raw_item_id": item["id"],
                "canonical_url": item["canonical_url"],
                "source_id": item["source_id"],
            }
        )
    return unique_items, results


def run_collection(
    source_store_path: str | pathlib.Path,
    report_path: str | pathlib.Path = DEFAULT_REPORT_PATH,
    raw_store_path: str | pathlib.Path = DEFAULT_RAW_STORE_PATH,
) -> dict[str, Any]:
    collected_at = utc_now()
    base_dir = pathlib.Path(source_store_path).resolve().parents[2]
    sources = load_source_store(source_store_path)
    raw_items: list[dict[str, Any]] = []
    source_results: list[dict[str, Any]] = []

    for source in sources:
        if source.get("enabled") is False:
            source_results.append(
                {
                    "source_id": source.get("id"),
                    "source_name": source.get("name"),
                    "collector": "none",
                    "status": "skipped",
                    "items_collected": 0,
                    "error": "source disabled",
                }
            )
            continue
        collector_name = select_collector(source)
        collector = COLLECTORS[collector_name]
        try:
            collected = collector(source, base_dir)
            normalized = [normalize_raw_item(source, item, collected_at) for item in collected]
            raw_items.extend(normalized)
            source_results.append(
                {
                    "source_id": source.get("id"),
                    "source_name": source.get("name"),
                    "collector": collector_name,
                    "status": "collected",
                    "items_collected": len(normalized),
                    "error": None,
                }
            )
        except Exception as exc:  # pragma: no cover - exercised by integration failures
            source_results.append(
                {
                    "source_id": source.get("id"),
                    "source_name": source.get("name"),
                    "collector": collector_name,
                    "status": "failed",
                    "items_collected": 0,
                    "error": str(exc),
                }
            )

    unique_items, deduplication_results = deduplicate_raw_items(raw_items)
    collection_metadata = {
        "store_version": STORE_VERSION,
        "collected_at": collected_at,
        "total_sources": len(sources),
        "total_raw_items_before_deduplication": len(raw_items),
        "total_raw_items": len(unique_items),
        "duplicates_removed": len(raw_items) - len(unique_items),
    }
    store_document = write_raw_item_store(
        raw_store_path,
        raw_items=unique_items,
        collection_metadata=collection_metadata,
        deduplication_results=deduplication_results,
    )
    report = {
        **collection_metadata,
        "source_results": source_results,
        "raw_store_path": str(raw_store_path),
        "stored_raw_item_count": len(store_document["raw_items"]),
        "notion_write_operations_performed": False,
        "live_github_api_used": False,
        "llm_api_calls_performed": False,
        "publishing_performed": False,
        "social_posting_performed": False,
        "article_body_scraping_performed": False,
    }
    write_json(report_path, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Collector Foundation V1.")
    parser.add_argument("--source-store", required=True, help="Path to source sync store JSON.")
    parser.add_argument("--output", default=str(DEFAULT_REPORT_PATH), help="Path to collector audit report JSON.")
    parser.add_argument("--raw-store", default=str(DEFAULT_RAW_STORE_PATH), help="Path to raw item JSON store.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = run_collection(args.source_store, report_path=args.output, raw_store_path=args.raw_store)
    print(
        "[collector-foundation] wrote report: "
        f"{args.output} sources={report['total_sources']} raw_items={report['total_raw_items']} "
        f"duplicates_removed={report['duplicates_removed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
