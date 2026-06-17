#!/usr/bin/env python3
"""DysonX V1 Pipeline Orchestrator.

Runs the fixture-based V1 pipeline as a safe dry run. It writes only JSON audit
reports into the requested output directory and performs no real provider calls,
network requests, website publishing, public content file writes, or social
posting.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

import dysonx_llm_audit as llm_audit
import dysonx_publish_eligibility as publish_eligibility
import dysonx_publish_package as publish_package
import dysonx_signal_candidate_pipeline as candidate_pipeline
import dysonx_signal_ranking as signal_ranking


def write_json_report(report: dict[str, Any], output_path: pathlib.Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def summarize_pipeline(
    raw_records: list[dict[str, Any]],
    candidate_report: dict[str, Any],
    llm_audit_report: dict[str, Any],
    ranking_report: dict[str, Any],
    quality_report: dict[str, Any],
    package_report: dict[str, Any],
    dry_run: bool,
    generated_at: str,
) -> dict[str, Any]:
    warnings: list[str] = []
    warnings.extend(str(warning) for warning in candidate_report.get("processing_warnings", []))
    warnings.extend(str(item) for item in ranking_report.get("audit_summary", {}).get("warnings", []))
    warnings.extend(str(item) for item in package_report.get("skipped", []))

    return {
        "generated_at": generated_at,
        "raw_items_seen": len(raw_records),
        "candidates_created": int(candidate_report.get("candidates_created", 0)),
        "signals_generated": int(llm_audit_report.get("signals_generated", 0)),
        "signals_ranked": int(ranking_report.get("audit_summary", {}).get("signals_ranked", 0)),
        "publish_ready": int(quality_report.get("status_counts", {}).get("publish_ready", 0)),
        "packages_created": int(package_report.get("packages_created", 0)),
        "rejected": int(quality_report.get("status_counts", {}).get("rejected", 0)),
        "warnings": warnings,
        "real_llm_api_used": False,
        "publishing_performed": False,
        "social_posting_performed": False,
        "network_requests_performed": False,
        "dry_run": dry_run,
    }


def run_pipeline(raw_fixture: str | pathlib.Path, output_dir: str | pathlib.Path, dry_run: bool) -> dict[str, Any]:
    if not dry_run:
        raise ValueError("DysonX V1 pipeline orchestrator only supports --dry-run")

    generated_at = datetime.now(timezone.utc).isoformat()
    output_path = pathlib.Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    raw_records = candidate_pipeline.load_raw_item_records(raw_fixture)
    candidate_report = candidate_pipeline.run_pipeline(raw_records, created_at=generated_at)

    candidate_records = list(candidate_report["candidates"])
    llm_audit_report = llm_audit.run_llm_audit(candidate_records, created_at=generated_at)
    write_json_report(llm_audit_report, output_path / "llm_audit_report.json")

    ranking_result = signal_ranking.rank_signals(llm_audit_report["signals"], top_n=10, created_at=generated_at)
    ranking_report = signal_ranking.ranking_result_to_report(ranking_result)
    write_json_report(ranking_report, output_path / "signal_ranking_report.json")

    quality_report = publish_eligibility.run_quality_review(ranking_report, created_at=generated_at)
    write_json_report(quality_report, output_path / "quality_review_report.json")

    package_report = publish_package.run_publish_package(quality_report, created_at=generated_at)
    write_json_report(package_report, output_path / "publish_package_report.json")

    summary = summarize_pipeline(
        raw_records=raw_records,
        candidate_report=candidate_report,
        llm_audit_report=llm_audit_report,
        ranking_report=ranking_report,
        quality_report=quality_report,
        package_report=package_report,
        dry_run=dry_run,
        generated_at=generated_at,
    )
    write_json_report(summary, output_path / "pipeline_summary.json")
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the DysonX V1 fixture pipeline as a dry run.")
    parser.add_argument("--raw-fixture", required=True, help="Path to RawItem fixture JSON.")
    parser.add_argument("--output-dir", required=True, help="Directory to write V1 pipeline reports.")
    parser.add_argument("--dry-run", action="store_true", required=True, help="Required safety flag.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run_pipeline(raw_fixture=args.raw_fixture, output_dir=args.output_dir, dry_run=args.dry_run)
    print(
        "[v1-pipeline] wrote reports: "
        f"{args.output_dir} raw_items={summary['raw_items_seen']} "
        f"signals={summary['signals_generated']} packages={summary['packages_created']} dry_run={summary['dry_run']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
