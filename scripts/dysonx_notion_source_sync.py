#!/usr/bin/env python3
"""DysonX Notion read-only source sync V1.

Fetches Notion source records, validates them, converts valid enabled records to
Source objects, writes a lightweight JSON store, and emits an audit report.
This does not collect content, call LLM APIs, publish pages, post to social
platforms, write Notion records, implement graph writes, or create predictions.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from dysonx_notion_readonly_adapter import (
    FakeNotionSourceClient,
    NotionReadOnlyAdapterNotConfigured,
    NotionReadOnlySourceClient,
    ReadOnlyNotionSourceAdapter,
)
from dysonx_notion_source_schema import validate_notion_source_record
from dysonx_source_config_loader import notion_record_to_source
from dysonx_source_sync_storage import write_source_sync_store


DEFAULT_REPORT_PATH = pathlib.Path("tmp/dysonx_source_sync_report.json")
DEFAULT_STORE_PATH = pathlib.Path("tmp/dysonx_source_sync_store.json")


def _record_name(record: dict[str, Any], index: int) -> str:
    return str(record.get("Name") or record.get("_notion_page_id") or f"record_{index}")


def classify_source_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    valid_sources: list[dict[str, Any]] = []
    invalid_records: list[dict[str, Any]] = []
    skipped_records: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        name = _record_name(record, index)
        errors = validate_notion_source_record(record)
        if errors:
            invalid_records.append(
                {
                    "record_name": name,
                    "notion_page_id": str(record.get("_notion_page_id") or ""),
                    "errors": errors,
                }
            )
            continue

        if record.get("Enabled") is not True:
            skipped_records.append(
                {
                    "record_name": name,
                    "notion_page_id": str(record.get("_notion_page_id") or ""),
                    "reason": "Enabled is false",
                }
            )
            continue

        valid_sources.append(asdict(notion_record_to_source(record, index)))

    return valid_sources, invalid_records, skipped_records


def build_validation_results(
    valid_sources: list[dict[str, Any]],
    invalid_records: list[dict[str, Any]],
    skipped_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    results.extend(
        {
            "record_name": source["name"],
            "notion_page_id": source["notion_page_id"],
            "status": "valid",
            "errors": [],
        }
        for source in valid_sources
    )
    results.extend({**record, "status": "invalid"} for record in invalid_records)
    results.extend({**record, "status": "skipped", "errors": []} for record in skipped_records)
    return results


def write_json(path: str | pathlib.Path, data: dict[str, Any]) -> None:
    output_path = pathlib.Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sync_sources(
    adapter: ReadOnlyNotionSourceAdapter,
    storage_path: str | pathlib.Path = DEFAULT_STORE_PATH,
    report_path: str | pathlib.Path = DEFAULT_REPORT_PATH,
    mode: str = "notion-readonly",
) -> dict[str, Any]:
    started = perf_counter()
    sync_timestamp = datetime.now(timezone.utc).isoformat()
    records = adapter.list_source_records()
    valid_sources, invalid_records, skipped_records = classify_source_records(records)
    validation_results = build_validation_results(valid_sources, invalid_records, skipped_records)
    duration = perf_counter() - started

    sync_metadata = {
        "mode": mode,
        "sync_timestamp": sync_timestamp,
        "sync_duration_seconds": round(duration, 6),
        "total_records": len(records),
        "valid_records": len(valid_sources),
        "invalid_records": len(invalid_records),
        "skipped_records": len(skipped_records),
        "notion_write_operations_performed": False,
        "collection_performed": False,
        "llm_api_calls_performed": False,
        "publishing_performed": False,
        "social_posting_performed": False,
    }
    store_document = write_source_sync_store(
        storage_path,
        sources=valid_sources,
        sync_metadata=sync_metadata,
        validation_results=validation_results,
    )
    report = {
        **sync_metadata,
        "write_operations_performed": False,
        "storage_write_operations_performed": True,
        "storage_path": str(storage_path),
        "stored_source_count": len(store_document["sources"]),
        "valid_sources": valid_sources,
        "invalid_record_details": invalid_records,
        "skipped_record_details": skipped_records,
        "validation_results": validation_results,
        "raw_articles_stored": False,
        "llm_outputs_stored": False,
        "publish_packages_stored": False,
    }
    write_json(report_path, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Notion read-only source sync V1.")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--fixture", help="Path to local Notion-shaped source fixture JSON for dry-run testing.")
    source.add_argument("--notion-readonly", action="store_true", help="Fetch from the configured Notion database.")
    parser.add_argument("--output", default=str(DEFAULT_REPORT_PATH), help="Path to write source sync audit report JSON.")
    parser.add_argument("--storage", default=str(DEFAULT_STORE_PATH), help="Path to write source sync JSON store.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.fixture:
            report = sync_sources(
                FakeNotionSourceClient(args.fixture),
                storage_path=args.storage,
                report_path=args.output,
                mode="fixture",
            )
        else:
            report = sync_sources(
                NotionReadOnlySourceClient.from_env(),
                storage_path=args.storage,
                report_path=args.output,
                mode="notion-readonly",
            )
    except NotionReadOnlyAdapterNotConfigured as exc:
        print(f"[source-sync] ERROR: {exc}", file=sys.stderr)
        return 2

    print(
        "[source-sync] wrote report: "
        f"{args.output} total={report['total_records']} valid={report['valid_records']} "
        f"invalid={report['invalid_records']} skipped={report['skipped_records']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
