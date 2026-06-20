#!/usr/bin/env python3
"""DysonX SignalQualityScore V1.

Builds first-class score records from an existing OpenAI Output Quality Audit
V1 report. This script is offline and deterministic. It does not call OpenAI,
dispatch workflows, publish, write website pages, mutate Notion, call GitHub,
scrape article bodies, write Knowledge Graph records, run Prediction Engine
work, enable publish readiness, or deploy.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any


SCORE_VERSION = "signal_quality_score_v1"
FRAMEWORK_REFERENCE = "docs/DYSONX_SIGNAL_QUALITY_FRAMEWORK_V1.md"
AUDIT_REFERENCE = "docs/DYSONX_OPENAI_OUTPUT_QUALITY_AUDIT_V1.md"
QUALITY_SCORE_MAX = 65

SCORE_DIMENSIONS = (
    "Information Density",
    "Source Attribution",
    "Source Authority",
    "Reasoning Depth",
    "Novelty",
    "AGI Capability Relevance",
    "Entity / Relationship Value",
    "Tracker Reuse Value",
    "Actionability",
    "Watch Next Specificity",
    "Prediction / Future Review Value",
    "Confidence Support",
    "Anti-Garbage Risk",
)

CRITICAL_RISK_FLAGS = {
    "missing_source_url",
    "missing_why_it_matters",
    "missing_watch_next",
    "missing_agi_capability",
    "unsupported_publish_readiness",
    "article_like_output",
    "generic_summary",
    "raw_provider_response_present",
    "network_or_live_operation_attempted",
}

SAFETY_FLAGS = {
    "openai_call_performed": False,
    "workflow_dispatched": False,
    "publishing_performed": False,
    "publish_readiness_enabled": False,
    "website_pages_written": False,
    "social_posting_performed": False,
    "notion_mutation_performed": False,
    "live_github_api_used": False,
    "article_body_scraping_performed": False,
    "raw_provider_response_stored": False,
    "knowledge_graph_write_performed": False,
    "prediction_engine_performed": False,
    "deployment_performed": False,
}


class ScoreInputError(ValueError):
    """Raised when an audit report cannot safely produce score records."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    report_path = pathlib.Path(path)
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should fail closed on malformed JSON.
        raise ScoreInputError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ScoreInputError(f"{label} must be a JSON object")
    return data


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def require_fields(report: dict[str, Any]) -> None:
    required_fields = (
        "audit_version",
        "framework_reference",
        "quality_dimensions",
        "signal_reviews",
        "tier_counts",
        "safety_flags",
    )
    missing = [field for field in required_fields if field not in report]
    if missing:
        raise ScoreInputError(f"Audit report missing required fields: {', '.join(missing)}")
    if report.get("audit_version") != "openai_output_quality_audit_v1":
        raise ScoreInputError("Audit report must be OpenAI Output Quality Audit V1")
    if report.get("quality_dimensions") != list(SCORE_DIMENSIONS):
        raise ScoreInputError("Audit quality dimensions do not match SignalQualityScore V1")
    signal_reviews = report.get("signal_reviews")
    if not isinstance(signal_reviews, list) or not all(isinstance(review, dict) for review in signal_reviews):
        raise ScoreInputError("Audit report signal_reviews must be a list of objects")


def critical_and_noncritical_risks(risk_flags: list[str]) -> tuple[list[str], list[str]]:
    critical = sorted(flag for flag in risk_flags if flag in CRITICAL_RISK_FLAGS)
    noncritical = sorted(flag for flag in risk_flags if flag not in CRITICAL_RISK_FLAGS)
    return critical, noncritical


def action_for_tier(quality_tier: str, critical_risk_flags: list[str]) -> str:
    if critical_risk_flags:
        return "blocked_by_quality_risk"
    if quality_tier.startswith("Tier A"):
        return "candidate_for_human_approval"
    if quality_tier.startswith("Tier B"):
        return "needs_human_review"
    if quality_tier.startswith("Tier C"):
        return "improve_or_regenerate"
    return "reject_or_regenerate"


def confidence_input_available(review: dict[str, Any]) -> bool:
    notes = normalize_list(review.get("confidence_notes"))
    if not notes:
        return False
    return any(note.startswith("model_confidence=") or note == "source_url_present" for note in notes)


def requires_human_review(quality_tier: str, critical_risk_flags: list[str]) -> bool:
    if critical_risk_flags:
        return True
    if quality_tier.startswith("Tier A"):
        return True
    if quality_tier.startswith("Tier B") or quality_tier.startswith("Tier C"):
        return True
    return False


def correlation_recommended(quality_tier: str, dimension_scores: dict[str, int]) -> bool:
    entity_score = int(dimension_scores.get("Entity / Relationship Value", 0))
    return quality_tier.startswith("Tier A") or quality_tier.startswith("Tier B") or entity_score >= 3


def score_explanation(total: int, tier: str, critical_risk_flags: list[str]) -> str:
    percent = total / QUALITY_SCORE_MAX
    if critical_risk_flags:
        return (
            f"Score {total}/{QUALITY_SCORE_MAX} ({percent:.2%}) is blocked by "
            f"critical risks: {', '.join(critical_risk_flags)}."
        )
    return f"Score {total}/{QUALITY_SCORE_MAX} ({percent:.2%}) maps to {tier}."


def validate_review(review: dict[str, Any], index: int) -> None:
    required_fields = (
        "signal_id",
        "candidate_id",
        "title",
        "source_url",
        "quality_scores",
        "total_score",
        "quality_tier",
        "risk_flags",
        "missing_fields",
    )
    missing = [field for field in required_fields if field not in review]
    if missing:
        raise ScoreInputError(f"Signal review {index} missing required fields: {', '.join(missing)}")
    scores = review.get("quality_scores")
    if not isinstance(scores, dict):
        raise ScoreInputError(f"Signal review {index} quality_scores must be an object")
    if set(scores.keys()) != set(SCORE_DIMENSIONS):
        raise ScoreInputError(f"Signal review {index} quality score dimensions do not match framework")
    for dimension, score in scores.items():
        if not isinstance(score, int) or score < 0 or score > 5:
            raise ScoreInputError(f"Signal review {index} dimension {dimension} must be an integer from 0 to 5")
    total = review.get("total_score")
    if not isinstance(total, int) or total < 0 or total > QUALITY_SCORE_MAX:
        raise ScoreInputError(f"Signal review {index} total_score must be an integer from 0 to {QUALITY_SCORE_MAX}")


def build_score_record(review: dict[str, Any], index: int) -> dict[str, Any]:
    validate_review(review, index)
    dimension_scores = {dimension: int(review["quality_scores"][dimension]) for dimension in SCORE_DIMENSIONS}
    total = int(review["total_score"])
    quality_tier = normalize_text(review.get("quality_tier"))
    risk_flags = normalize_list(review.get("risk_flags"))
    critical, noncritical = critical_and_noncritical_risks(risk_flags)
    action = action_for_tier(quality_tier, critical)
    publish_candidate = action == "candidate_for_human_approval" and not critical
    confidence_available = confidence_input_available(review)
    return {
        "signal_id": normalize_text(review.get("signal_id")),
        "candidate_id": normalize_text(review.get("candidate_id")),
        "title": normalize_text(review.get("title")),
        "source_url": normalize_text(review.get("source_url")),
        "quality_score_total": total,
        "quality_score_max": QUALITY_SCORE_MAX,
        "quality_score_percent": total / QUALITY_SCORE_MAX,
        "quality_tier": quality_tier,
        "dimension_scores": dimension_scores,
        "critical_risk_flags": critical,
        "noncritical_risk_flags": noncritical,
        "missing_fields": normalize_list(review.get("missing_fields")),
        "publish_readiness_candidate": publish_candidate,
        "recommended_action": action,
        "score_explanation": score_explanation(total, quality_tier, critical),
        "confidence_input_available": confidence_available,
        "requires_confidence_calibration": True,
        "requires_human_review": requires_human_review(quality_tier, critical),
        "correlation_recommended": correlation_recommended(quality_tier, dimension_scores),
        "score_source": "openai_output_quality_audit_v1",
    }


def summarize_tiers(score_records: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "Tier A: Decision-grade Signal": 0,
        "Tier B: Useful Signal": 0,
        "Tier C: Needs Review": 0,
        "Tier D: Reject / Low-value": 0,
    }
    for record in score_records:
        tier = str(record.get("quality_tier"))
        counts[tier] = counts.get(tier, 0) + 1
    return counts


def summarize_blocking_risks(score_records: list[dict[str, Any]]) -> dict[str, int]:
    counts = {flag: 0 for flag in sorted(CRITICAL_RISK_FLAGS)}
    for record in score_records:
        for flag in record.get("critical_risk_flags", []):
            counts[flag] = counts.get(flag, 0) + 1
    return {flag: count for flag, count in counts.items() if count > 0}


def recommended_next_actions(score_records: list[dict[str, Any]]) -> list[str]:
    actions = [
        "Review SignalQualityScore V1 output against real and fixture audit reports.",
        "Implement Confidence Calibration V1 before publish-readiness decisions.",
        "Implement Multi-source Correlation V1 for high-value or entity-rich signals.",
        "Keep publishing blocked until Human Approval Gate and Publish Readiness Gate exist.",
    ]
    if any(record.get("critical_risk_flags") for record in score_records):
        actions.insert(0, "Resolve records blocked by critical quality risks.")
    return actions


def run_score(
    audit_report_path: str | pathlib.Path,
    output_path: str | pathlib.Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    audit_report = read_json_object(audit_report_path, "OpenAI Output Quality Audit V1 report")
    require_fields(audit_report)
    score_records = [
        build_score_record(review, index)
        for index, review in enumerate(audit_report["signal_reviews"])
    ]
    report = {
        "score_version": SCORE_VERSION,
        "created_at": created_at or utc_now(),
        "input_audit_report": str(audit_report_path),
        "framework_reference": FRAMEWORK_REFERENCE,
        "audit_reference": AUDIT_REFERENCE,
        "signals_scored": len(score_records),
        "score_dimensions": list(SCORE_DIMENSIONS),
        "score_records": score_records,
        "tier_counts": summarize_tiers(score_records),
        "blocking_risk_counts": summarize_blocking_risks(score_records),
        "recommended_next_actions": recommended_next_actions(score_records),
        "safety_flags": dict(SAFETY_FLAGS),
    }
    if output_path is not None:
        write_report(report, output_path)
    return report


def write_report(report: dict[str, Any], output_path: str | pathlib.Path) -> None:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX SignalQualityScore V1.")
    parser.add_argument("--audit-report", required=True, help="Path to OpenAI Output Quality Audit V1 JSON.")
    parser.add_argument("--output", required=True, help="Path to write SignalQualityScore V1 report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_score(args.audit_report, output_path=args.output)
    except ScoreInputError as exc:
        print(f"[signal-quality-score] failed: {exc}")
        return 1
    print(
        "[signal-quality-score] wrote report: "
        f"{args.output} signals_scored={report['signals_scored']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
