#!/usr/bin/env python3
"""DysonX V1 Intelligence Pipeline Integration.

Runs the V1 pipeline from Source store through publish-package metadata.
It composes existing modules and writes JSON audit reports only. The default
provider remains fake. The OpenAI provider path is available only through the
existing gated provider implementation and explicit CLI gates.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any

import dysonx_collector_foundation
import dysonx_publish_eligibility
import dysonx_publish_package
import dysonx_rawitem_signal_pipeline
import dysonx_real_llm_provider
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


def signal_type_for_candidate(candidate: dict[str, Any]) -> str:
    candidate_type = str(candidate.get("candidate_type") or "").strip()
    return candidate_type or "general_signal"


def importance_for_signal(signal: dict[str, Any]) -> str:
    confidence = signal.get("confidence")
    if isinstance(confidence, int | float):
        if confidence >= 0.75:
            return "high"
        if confidence >= 0.55:
            return "medium"
    return "low"


def build_downstream_signal(signal: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Project provider output into the existing downstream V1 signal shape."""
    related_entities = signal.get("related_entities") or []
    return {
        **signal,
        "source_id": str(candidate.get("source_id") or ""),
        "source_name": str(candidate.get("source_name") or ""),
        "signal_type": signal_type_for_candidate(candidate),
        "importance": importance_for_signal(signal),
        "key_points": [
            str(signal.get("why_it_matters") or ""),
            str(signal.get("watch_next") or ""),
        ],
        "affected_entities": [str(entity) for entity in related_entities],
        "tags": [str(tag) for tag in candidate.get("tags") or []],
    }


def prepare_provider_report_for_downstream(
    provider_report: dict[str, Any],
    candidate_report: dict[str, Any],
) -> dict[str, Any]:
    candidates = {
        str(candidate.get("candidate_id")): candidate
        for candidate in candidate_report.get("candidates", [])
        if isinstance(candidate, dict)
    }
    signals = [
        build_downstream_signal(signal, candidates.get(str(signal.get("candidate_id")), {}))
        for signal in provider_report.get("intelligence_signals", [])
        if isinstance(signal, dict)
    ]
    provider_report["signals"] = signals
    provider_report["signals_generated"] = len(signals)
    provider_report["provider_distribution"] = {
        str(provider_report.get("provider")): int(provider_report.get("jobs_created", 0))
    }
    provider_report["prompt_versions_used"] = {
        str(provider_report.get("prompt_version")): int(provider_report.get("jobs_created", 0))
    }
    return provider_report


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
        "real_llm_provider_reused": True,
        "duplicate_provider_logic_introduced": False,
        "fake_provider_default_available": True,
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
        "publish_package_created": int(package_report.get("packages_created", 0)) > 0,
        "provider": str(llm_audit_report.get("provider") or "fake"),
        "items_requested": int(llm_audit_report.get("items_requested", 0)),
        "items_processed": int(llm_audit_report.get("items_processed", 0)),
        "prompt_version": str(llm_audit_report.get("prompt_version") or ""),
        "rejected_or_skipped": rejected_or_skipped_counts(
            candidate_report,
            llm_audit_report,
            quality_report,
            package_report,
        ),
        "module_reuse": module_reuse,
        "layer_boundaries": layer_boundaries,
        **{
            **SAFETY_FLAGS,
            "real_llm_api_used": bool(llm_audit_report.get("real_llm_api_used", False)),
            "llm_api_calls_performed": bool(llm_audit_report.get("llm_api_calls_performed", False)),
            "raw_provider_response_stored": bool(llm_audit_report.get("raw_provider_response_stored", False)),
        },
    }


def run_pipeline(
    source_store: str | pathlib.Path,
    output_dir: str | pathlib.Path,
    provider: str = "fake",
    allow_real_llm: bool = False,
    max_items: int | None = None,
) -> dict[str, Any]:
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
    llm_audit_report = dysonx_real_llm_provider.run_provider(
        paths["signal_candidates"],
        provider=provider,
        allow_real_llm=allow_real_llm,
        max_items=max_items,
        output_path=paths["llm_audit"],
        created_at=generated_at,
    )
    llm_audit_report = prepare_provider_report_for_downstream(llm_audit_report, candidate_report)
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
    parser = argparse.ArgumentParser(description="Run DysonX V1 Intelligence Pipeline Integration.")
    parser.add_argument("--source-store", required=True, help="Path to Source sync store JSON.")
    parser.add_argument("--output-dir", required=True, help="Directory to write V1 intelligence pipeline reports.")
    parser.add_argument("--provider", choices=("fake", "openai"), default="fake", help="LLM provider mode.")
    parser.add_argument("--allow-real-llm", action="store_true", help="Required to allow the OpenAI provider path.")
    parser.add_argument("--max-items", type=int, help="Required small positive item limit for the OpenAI provider path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_pipeline(
            args.source_store,
            args.output_dir,
            provider=args.provider,
            allow_real_llm=args.allow_real_llm,
            max_items=args.max_items,
        )
    except dysonx_real_llm_provider.ProviderGateError as exc:
        print(f"[v1-intelligence-pipeline] provider gate blocked run: {exc}")
        return 2
    print(
        "[v1-intelligence-pipeline] wrote reports: "
        f"{args.output_dir} sources={report['sources_seen']} raw_items={report['raw_items_created']} "
        f"provider={report['provider']} signals={report['intelligence_signals_created']} "
        f"packages={report['packages_created']} real_llm_api_used={report['real_llm_api_used']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
