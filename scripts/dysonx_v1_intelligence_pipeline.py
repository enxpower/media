#!/usr/bin/env python3
"""DysonX V1 Intelligence Pipeline Integration.

Runs the offline V1 pipeline from Source store through publish-package metadata.
It composes existing modules and writes JSON audit reports only. It does not
call real LLM APIs, mutate Notion, call live GitHub APIs, scrape article bodies,
write website pages, write public content files, post to social platforms,
schedule work, or deploy anything.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

import dysonx_collector_foundation
import dysonx_llm_audit
import dysonx_publish_eligibility
import dysonx_publish_package
import dysonx_rawitem_signal_pipeline
import dysonx_signal_ranking


SAFETY_FLAGS = {
    "notion_write_operations_performed": False,
    "live_github_api_used": False,
    "real_llm_api_used": False,
    "llm_api_calls_performed": False,
    "publishing_performed": False,
    "website_pages_written": False,
    "public_content_files_written": False,
    "social_posting_performed": False,
    "article_body_scraping_performed": False,
    "deployment_performed": False,
}


def write_json_report(report: dict[str, Any], output_path: pathlib.Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def report_paths(output_dir: str | pathlib.Path) -> dict[str, pathlib.Path]:
    output_path = pathlib.Path(output_dir)
    return {
        "collector": output_path / "collector_report.json",
        "raw_store": output_path / "raw_items_store.json",
        "signal_candidates": output_path / "signal_candidate_report.json",
        "llm_audit": output_path / "llm_audit_report.json",
        "ranking": output_path / "signal_ranking_report.json",
        "quality": output_path / "quality_review_report.json",
        "publish_package": output_path / "publish_package_report.json",
        "final": output_path / "v1_intelligence_pipeline_report.json",
    }


def rejected_or_skipped_counts(
    candidate_report: dict[str, Any],
    llm_audit_report: dict[str, Any],
    quality_report: dict[str, Any],
    package_report: dict[str, Any],
) -> dict[str, int]:
    status_counts = quality_report.get("status_counts", {})
    return {
        "candidate_rejected": len(candidate_report.get("rejected_items", [])),
        "llm_validations_failed": int(llm_audit_report.get("validations_failed", 0)),
        "quality_rejected": int(status_counts.get("rejected", 0)),
        "quality_needs_review": int(status_counts.get("needs_review", 0)),
        "publish_package_skipped": len(package_report.get("skipped", [])),
    }


def summarize_pipeline(
    source_store_path: str | pathlib.Path,
    output_dir: str | pathlib.Path,
    collector_report: dict[str, Any],
    raw_store: dict[str, Any],
    candidate_report: dict[str, Any],
    llm_audit_report: dict[str, Any],
    ranking_report: dict[str, Any],
    quality_report: dict[str, Any],
    package_report: dict[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    module_reuse = {
        "collector_foundation_reused": True,
        "rawitem_signal_pipeline_reused": True,
        "signal_candidate_pipeline_reused": bool(
            candidate_report.get("integration", {}).get("signal_candidate_pipeline_reused")
        ),
        "llm_audit_reused": True,
        "fake_provider_only": llm_audit_report.get("provider_distribution") == {"fake": llm_audit_report.get("jobs_created")},
        "signal_ranking_reused": True,
        "quality_review_reused": True,
        "publish_package_reused": True,
    }
    layer_boundaries = {
        "rawitem_separate_from_signal_candidate": True,
        "signal_candidate_separate_from_intelligence_signal": True,
        "intelligence_signal_separate_from_publish_package": True,
        "collector_stops_at_rawitem_persistence": True,
    }
    return {
        "generated_at": generated_at,
        "source_store_path": str(source_store_path),
        "output_dir": str(output_dir),
        "sources_seen": int(collector_report.get("total_sources", 0)),
        "raw_items_created": len(raw_store.get("raw_items", [])),
        "signal_candidates_created": int(candidate_report.get("candidates_created", 0)),
        "llm_jobs_created": int(llm_audit_report.get("jobs_created", 0)),
        "intelligence_signals_created": int(llm_audit_report.get("signals_generated", 0)),
        "signals_ranked": int(ranking_report.get("audit_summary", {}).get("signals_ranked", 0)),
        "publish_ready": int(quality_report.get("status_counts", {}).get("publish_ready", 0)),
        "packages_created": int(package_report.get("packages_created", 0)),
        "rejected_or_skipped": rejected_or_skipped_counts(
            candidate_report,
            llm_audit_report,
            quality_report,
            package_report,
        ),
        "module_reuse": module_reuse,
        "layer_boundaries": layer_boundaries,
        **SAFETY_FLAGS,
    }


def run_pipeline(source_store: str | pathlib.Path, output_dir: str | pathlib.Path) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    paths = report_paths(output_dir)
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    collector_report = dysonx_collector_foundation.run_collection(
        source_store,
        report_path=paths["collector"],
        raw_store_path=paths["raw_store"],
    )
    raw_store = json.loads(paths["raw_store"].read_text(encoding="utf-8"))

    candidate_report = dysonx_rawitem_signal_pipeline.run_integration(
        source_store,
        raw_store_path=paths["raw_store"],
        collector_report_path=paths["collector"],
        signal_output_path=paths["signal_candidates"],
    )

    candidate_records = list(candidate_report["candidates"])
    llm_audit_report = dysonx_llm_audit.run_llm_audit(candidate_records, created_at=generated_at)
    write_json_report(llm_audit_report, paths["llm_audit"])

    ranking_result = dysonx_signal_ranking.rank_signals(llm_audit_report["signals"], top_n=10, created_at=generated_at)
    ranking_report = dysonx_signal_ranking.ranking_result_to_report(ranking_result)
    write_json_report(ranking_report, paths["ranking"])

    quality_report = dysonx_publish_eligibility.run_quality_review(ranking_report, created_at=generated_at)
    write_json_report(quality_report, paths["quality"])

    package_report = dysonx_publish_package.run_publish_package(quality_report, created_at=generated_at)
    write_json_report(package_report, paths["publish_package"])

    final_report = summarize_pipeline(
        source_store_path=source_store,
        output_dir=output_dir,
        collector_report=collector_report,
        raw_store=raw_store,
        candidate_report=candidate_report,
        llm_audit_report=llm_audit_report,
        ranking_report=ranking_report,
        quality_report=quality_report,
        package_report=package_report,
        generated_at=generated_at,
    )
    write_json_report(final_report, paths["final"])
    return final_report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX V1 Intelligence Pipeline Integration offline.")
    parser.add_argument("--source-store", required=True, help="Path to Source sync store JSON.")
    parser.add_argument("--output-dir", required=True, help="Directory to write V1 intelligence pipeline reports.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = run_pipeline(args.source_store, args.output_dir)
    print(
        "[v1-intelligence-pipeline] wrote reports: "
        f"{args.output_dir} sources={report['sources_seen']} raw_items={report['raw_items_created']} "
        f"signals={report['intelligence_signals_created']} packages={report['packages_created']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
