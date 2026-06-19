#!/usr/bin/env python3
"""DysonX RawItem to SignalCandidate Integration V1.

Connects Collector Foundation V1 RawItem JSON output to the existing Signal
Candidate Pipeline. This script does not call LLM APIs, publish pages, post to
social platforms, mutate Notion, call live GitHub APIs, scrape article bodies,
implement graph writes, schedule collectors, or deploy anything.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Any

import dysonx_collector_foundation
import dysonx_signal_candidate_pipeline


DEFAULT_SIGNAL_OUTPUT = pathlib.Path("tmp/dysonx_signal_candidates_report.json")


SAFETY_FLAGS = {
    "notion_write_operations_performed": False,
    "live_github_api_used": False,
    "llm_api_calls_performed": False,
    "publishing_performed": False,
    "social_posting_performed": False,
    "article_body_scraping_performed": False,
}


def write_json(path: str | pathlib.Path, data: dict[str, Any]) -> None:
    output_path = pathlib.Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_raw_store(
    source_store_path: str | pathlib.Path,
    raw_store_path: str | pathlib.Path,
    collector_report_path: str | pathlib.Path,
) -> dict[str, Any]:
    raw_path = pathlib.Path(raw_store_path)
    if raw_path.exists():
        return {
            "collector_ran": False,
            "collector_report_path": str(collector_report_path),
            "raw_store_path": str(raw_store_path),
        }
    report = dysonx_collector_foundation.run_collection(
        source_store_path,
        report_path=collector_report_path,
        raw_store_path=raw_store_path,
    )
    return {
        "collector_ran": True,
        "collector_report_path": str(collector_report_path),
        "raw_store_path": str(raw_store_path),
        "collector_report": report,
    }


def load_raw_item_store(path: str | pathlib.Path) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("RawItem store must be a JSON object")
    if set(data) != {"raw_items", "collection_metadata", "deduplication_results"}:
        raise ValueError("RawItem store must contain raw_items, collection_metadata, and deduplication_results")
    raw_items = data.get("raw_items")
    if not isinstance(raw_items, list) or not all(isinstance(item, dict) for item in raw_items):
        raise ValueError("RawItem store raw_items must be a list of objects")
    return data


def raw_store_item_to_pipeline_record(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": item.get("source_id"),
        "source_name": item.get("source_name"),
        "title": item.get("raw_title"),
        "url": item.get("canonical_url") or item.get("original_url"),
        "published_at": item.get("raw_published_at") or "",
        "language": item.get("detected_language") or "English",
        "collected_at": item.get("fetched_at"),
        "raw_content": item.get("raw_content") or item.get("raw_excerpt") or "",
        "metadata": {
            **dict(item.get("metadata") or {}),
            "raw_item_id": item.get("id"),
            "original_url": item.get("original_url"),
            "content_hash": item.get("content_hash"),
            "source_type": item.get("source_type"),
        },
    }


def raw_store_to_pipeline_records(raw_store: dict[str, Any]) -> list[dict[str, Any]]:
    return [raw_store_item_to_pipeline_record(item) for item in raw_store["raw_items"]]


def run_integration(
    source_store_path: str | pathlib.Path,
    raw_store_path: str | pathlib.Path,
    collector_report_path: str | pathlib.Path,
    signal_output_path: str | pathlib.Path = DEFAULT_SIGNAL_OUTPUT,
) -> dict[str, Any]:
    collector_context = ensure_raw_store(source_store_path, raw_store_path, collector_report_path)
    raw_store = load_raw_item_store(raw_store_path)
    records = raw_store_to_pipeline_records(raw_store)
    candidate_report = dysonx_signal_candidate_pipeline.run_pipeline(records)
    report = {
        **candidate_report,
        "integration": {
            "source_store_path": str(source_store_path),
            "raw_store_path": str(raw_store_path),
            "collector_report_path": str(collector_report_path),
            "collector_ran": collector_context["collector_ran"],
            "raw_items_read": len(records),
            "signal_candidate_pipeline_reused": True,
            "signal_candidate_layer_bypassed": False,
        },
        **SAFETY_FLAGS,
    }
    write_json(signal_output_path, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX RawItem to SignalCandidate Integration V1.")
    parser.add_argument("--source-store", required=True, help="Path to source sync store JSON.")
    parser.add_argument("--raw-store", required=True, help="Path to RawItem store JSON.")
    parser.add_argument("--collector-report", required=True, help="Path to collector audit report JSON.")
    parser.add_argument("--signal-output", default=str(DEFAULT_SIGNAL_OUTPUT), help="Path to SignalCandidate report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = run_integration(
        args.source_store,
        raw_store_path=args.raw_store,
        collector_report_path=args.collector_report,
        signal_output_path=args.signal_output,
    )
    print(
        "[rawitem-signal-pipeline] wrote report: "
        f"{args.signal_output} raw_items={report['integration']['raw_items_read']} "
        f"candidates={report['candidates_created']} rejected={len(report['rejected_items'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
