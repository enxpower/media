#!/usr/bin/env python3
"""DysonX Source Intake V1.

Reads Notion-shaped source records from a local fixture or a disabled real
Notion read-only adapter skeleton, validates them, converts eligible records to
Source objects, and writes an audit report. It does not collect article content,
call LLM APIs, publish pages, write to Notion, or implement graph features.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from dysonx_notion_readonly_adapter import (
    FakeNotionSourceClient,
    NotionReadOnlyAdapterNotConfigured,
    NotionReadOnlySourceClient,
)
from dysonx_source_config_loader import SourceConfigLoadResult, load_sources_from_records


def build_audit_report(records: list[dict[str, Any]], result: SourceConfigLoadResult, mode: str, dry_run: bool) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "dry_run": dry_run,
        "total_records": len(records),
        "eligible_source_count": len(result.sources),
        "rejected_record_count": len(result.rejected_records),
        "eligible_sources": [asdict(source) for source in result.sources],
        "validation_errors": {name: list(errors) for name, errors in result.validation_errors.items()},
        "write_operations_performed": False,
        "collection_performed": False,
        "llm_analysis_performed": False,
        "publishing_performed": False,
    }


def write_report(report: dict[str, Any], output_path: str | pathlib.Path) -> None:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_fixture_intake(fixture_path: str | pathlib.Path, dry_run: bool) -> dict[str, Any]:
    adapter = FakeNotionSourceClient(fixture_path)
    records = adapter.list_source_records()
    result = load_sources_from_records(records)
    return build_audit_report(records, result, mode="fixture", dry_run=dry_run)


def run_notion_readonly_intake(dry_run: bool) -> dict[str, Any]:
    adapter = NotionReadOnlySourceClient.from_env()
    records = adapter.list_source_records()
    result = load_sources_from_records(records)
    return build_audit_report(records, result, mode="notion-readonly", dry_run=dry_run)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Source Intake V1.")
    source_mode = parser.add_mutually_exclusive_group(required=True)
    source_mode.add_argument("--fixture", help="Path to local Notion-shaped source fixture JSON.")
    source_mode.add_argument("--notion-readonly", action="store_true", help="Use real Notion read-only adapter skeleton.")
    parser.add_argument("--dry-run", action="store_true", help="Write an audit report without side effects.")
    parser.add_argument("--output", required=True, help="Path to write source intake audit report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        if args.fixture:
            report = run_fixture_intake(args.fixture, dry_run=args.dry_run)
        else:
            report = run_notion_readonly_intake(dry_run=args.dry_run)
    except NotionReadOnlyAdapterNotConfigured as exc:
        print(f"[source-intake] ERROR: {exc}", file=sys.stderr)
        return 2

    write_report(report, args.output)
    print(
        "[source-intake] wrote report: "
        f"{args.output} eligible={report['eligible_source_count']} rejected={report['rejected_record_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
