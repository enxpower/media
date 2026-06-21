#!/usr/bin/env python3
"""DysonX Auto Decision Engine V1.

Classifies SignalQualityScore V1 records into conservative internal handling
decisions. This script is offline and deterministic. It does not call OpenAI,
dispatch workflows, publish content, generate public pages, mutate Notion, call
live GitHub APIs, scrape article bodies, write Knowledge Graph records, run
Prediction Engine work, perform confidence calibration or correlation, enable
publish readiness, approve publication, or deploy.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any


AUTO_DECISION_VERSION = "auto_decision_engine_v1"
SCORE_VERSION = "signal_quality_score_v1"

QUALITY_SCORE_MAX = 65

AUTO_DECISIONS = (
    "auto_reject",
    "needs_more_sources",
    "needs_regeneration",
    "hold",
    "candidate_for_publish_readiness_review",
)

DECISION_LABELS = {
    "auto_reject": "Reject automatically",
    "needs_more_sources": "Need more sources",
    "needs_regeneration": "Regenerate analysis",
    "hold": "Hold",
    "candidate_for_publish_readiness_review": "Candidate for later readiness review",
}

NEXT_ACTION_BY_DECISION = {
    "auto_reject": "remove_from_current_review_queue",
    "needs_more_sources": "collect_or_attach_more_sources",
    "needs_regeneration": "regenerate_or_improve_signal_analysis",
    "hold": "keep_for_later_review",
    "candidate_for_publish_readiness_review": "later_publish_readiness_review_required",
}

SAFETY_FLAGS = {
    "openai_call_performed": False,
    "workflow_dispatched": False,
    "publishing_performed": False,
    "publication_approved": False,
    "publish_readiness_enabled": False,
    "public_content_generated": False,
    "website_pages_written": False,
    "social_posting_performed": False,
    "notion_mutation_performed": False,
    "live_github_api_used": False,
    "article_body_scraping_performed": False,
    "raw_provider_response_stored": False,
    "knowledge_graph_write_performed": False,
    "prediction_engine_performed": False,
    "confidence_calibration_performed": False,
    "correlation_performed": False,
    "deployment_performed": False,
}

CRITICAL_AUTO_REJECT_FLAGS = {"generic_summary", "missing_source_url"}
REGENERATION_MISSING_FIELDS = {
    "why_it_matters",
    "watch_next",
    "agi_capability",
    "owner_decision_implication",
}
SOURCE_MISSING_FIELDS = {"first_source_url", "source_url", "source_authority_reasoning"}
WEAK_SOURCE_MARKERS = (
    "weak",
    "secondhand",
    "not independently verified",
    "not yet independently verified",
    "vague sourcing",
    "incomplete",
    "insufficient",
    "promotional",
)


class AutoDecisionInputError(ValueError):
    """Raised when a score report cannot safely produce auto decisions."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    input_path = pathlib.Path(path)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should fail closed on malformed JSON.
        raise AutoDecisionInputError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AutoDecisionInputError(f"{label} must be a JSON object")
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


def require_report_fields(report: dict[str, Any]) -> None:
    required_fields = (
        "score_version",
        "signals_scored",
        "score_records",
        "tier_counts",
        "safety_flags",
    )
    missing = [field for field in required_fields if field not in report]
    if missing:
        raise AutoDecisionInputError(f"SignalQualityScore report missing required fields: {', '.join(missing)}")
    if report.get("score_version") != SCORE_VERSION:
        raise AutoDecisionInputError("Input report must be SignalQualityScore V1")
    records = report.get("score_records")
    if not isinstance(records, list) or not records or not all(isinstance(record, dict) for record in records):
        raise AutoDecisionInputError("SignalQualityScore score_records must be a non-empty list of objects")


def require_record_fields(record: dict[str, Any], index: int) -> None:
    required_fields = (
        "signal_id",
        "title",
        "source_url",
        "quality_score_total",
        "quality_score_max",
        "quality_tier",
        "critical_risk_flags",
        "noncritical_risk_flags",
        "missing_fields",
        "recommended_action",
    )
    missing = [field for field in required_fields if field not in record]
    if missing:
        raise AutoDecisionInputError(f"Score record {index} missing required fields: {', '.join(missing)}")
    if not normalize_text(record.get("signal_id")):
        raise AutoDecisionInputError(f"Score record {index} signal_id is required")
    total = record.get("quality_score_total")
    max_score = record.get("quality_score_max")
    if not isinstance(total, int) or total < 0 or total > QUALITY_SCORE_MAX:
        raise AutoDecisionInputError(f"Score record {index} quality_score_total must be 0..{QUALITY_SCORE_MAX}")
    if not isinstance(max_score, int) or max_score != QUALITY_SCORE_MAX:
        raise AutoDecisionInputError(f"Score record {index} quality_score_max must be {QUALITY_SCORE_MAX}")


def lower_values(values: list[str]) -> set[str]:
    return {value.lower() for value in values}


def dimension_score(record: dict[str, Any], dimension: str) -> int | None:
    scores = record.get("dimension_scores")
    if not isinstance(scores, dict):
        return None
    value = scores.get(dimension)
    return value if isinstance(value, int) else None


def tier_contains(record: dict[str, Any], marker: str) -> bool:
    return marker.lower() in normalize_text(record.get("quality_tier")).lower()


def text_contains_any(value: str, markers: tuple[str, ...] | set[str]) -> bool:
    lowered = value.lower()
    return any(marker.lower() in lowered for marker in markers)


def source_authority(record: dict[str, Any]) -> str:
    return normalize_text(record.get("source_authority"))


def agi_capability(record: dict[str, Any]) -> str:
    return normalize_text(record.get("agi_capability"))


def why_it_matters(record: dict[str, Any]) -> str:
    return normalize_text(record.get("why_it_matters"))


def watch_next(record: dict[str, Any]) -> str:
    return normalize_text(record.get("watch_next"))


def risk_summary(record: dict[str, Any]) -> str:
    summary = normalize_text(record.get("risk_summary"))
    if summary:
        return summary
    risks = normalize_list(record.get("critical_risk_flags")) + normalize_list(record.get("noncritical_risk_flags"))
    return ", ".join(risks)


def combined_risk_flags(record: dict[str, Any]) -> list[str]:
    return normalize_list(record.get("critical_risk_flags")) + normalize_list(record.get("noncritical_risk_flags"))


def is_too_generic(record: dict[str, Any]) -> bool:
    title = normalize_text(record.get("title")).lower()
    generic_titles = {
        "several companies say ai demand remains strong",
        "ai changes everything",
        "new ai news roundup",
    }
    return title in generic_titles or "generic" in risk_summary(record).lower()


def should_auto_reject(record: dict[str, Any]) -> tuple[bool, list[str]]:
    total = int(record.get("quality_score_total", 0))
    critical_flags = lower_values(normalize_list(record.get("critical_risk_flags")))
    reasons: list[str] = []
    if tier_contains(record, "Tier D") or tier_contains(record, "Reject") or tier_contains(record, "blocked"):
        reasons.append("quality tier is reject or blocked")
    if total < 28:
        reasons.append("quality score is below 28")
    for flag in sorted(CRITICAL_AUTO_REJECT_FLAGS.intersection(critical_flags)):
        reasons.append(f"critical risk flag: {flag}")
    if not normalize_text(record.get("source_url")):
        reasons.append("source URL is missing")
    anti_garbage = dimension_score(record, "Anti-Garbage Risk")
    if anti_garbage is not None and anti_garbage <= 1:
        reasons.append("Anti-Garbage Risk score is very low")
    if is_too_generic(record):
        reasons.append("Signal is too generic to support Owner decision")
    return bool(reasons), reasons


def should_regenerate(record: dict[str, Any]) -> tuple[bool, list[str]]:
    missing = lower_values(normalize_list(record.get("missing_fields")))
    reasons: list[str] = []
    if tier_contains(record, "Tier C") or tier_contains(record, "Needs work"):
        reasons.append("quality tier needs review")
    for field in sorted(REGENERATION_MISSING_FIELDS.intersection(missing)):
        reasons.append(f"missing field: {field}")
    if normalize_text(record.get("recommended_action")) == "improve_or_regenerate":
        reasons.append("recommended action is improve_or_regenerate")
    if "thin" in risk_summary(record).lower() and normalize_text(record.get("source_url")):
        reasons.append("analysis is thin but source exists")
    return bool(reasons), reasons


def should_need_more_sources(record: dict[str, Any]) -> tuple[bool, list[str]]:
    missing = lower_values(normalize_list(record.get("missing_fields")))
    risks = lower_values(combined_risk_flags(record))
    summary = risk_summary(record).lower()
    recommended = normalize_text(record.get("recommended_action")).lower()
    authority = source_authority(record).lower()
    total = int(record.get("quality_score_total", 0))
    reasons: list[str] = []
    if normalize_text(record.get("source_url")) and text_contains_any(authority, WEAK_SOURCE_MARKERS):
        reasons.append("source exists but source authority is weak or incomplete")
    for field in sorted(SOURCE_MISSING_FIELDS.intersection(missing)):
        reasons.append(f"missing source evidence field: {field}")
    if any("weak" in flag and "attribution" in flag for flag in risks):
        reasons.append("risk flags suggest weak attribution")
    if "more source" in summary or "more evidence" in summary or "source support" in summary:
        reasons.append("risk summary indicates more source support is needed")
    if "more evidence" in recommended or "more source" in recommended:
        reasons.append("recommended action indicates more evidence is needed")
    if total >= 38 and ("evidence is incomplete" in summary or "source support" in summary):
        reasons.append("score is useful but evidence is incomplete")
    return bool(reasons), reasons


def should_candidate(record: dict[str, Any]) -> tuple[bool, list[str]]:
    total = int(record.get("quality_score_total", 0))
    critical = normalize_list(record.get("critical_risk_flags"))
    summary = risk_summary(record).lower()
    required = {
        "source_url": normalize_text(record.get("source_url")),
        "why_it_matters": why_it_matters(record),
        "watch_next": watch_next(record),
        "agi_capability": agi_capability(record),
    }
    reasons: list[str] = []
    if not (tier_contains(record, "Tier A") or tier_contains(record, "Decision-grade")):
        return False, []
    if total < 52:
        return False, []
    if critical:
        return False, []
    if any(not value for value in required.values()):
        return False, []
    critical_gap_markers = ("unresolved critical evidence gap", "open critical evidence gap", "critical evidence gap remains")
    if text_contains_any(summary, critical_gap_markers) or "unresolved critical" in summary:
        return False, []
    reasons.append("Tier A score is at least 52 with no critical risks")
    reasons.append("source, why_it_matters, watch_next, and agi_capability are present")
    return True, reasons


def choose_decision(record: dict[str, Any]) -> tuple[str, str, list[str], list[str]]:
    reject, reject_reasons = should_auto_reject(record)
    if reject:
        return "auto_reject", "high", reject_reasons, reject_reasons
    regenerate, regenerate_reasons = should_regenerate(record)
    if regenerate:
        return "needs_regeneration", "high", regenerate_reasons, []
    candidate, candidate_reasons = should_candidate(record)
    if candidate:
        return "candidate_for_publish_readiness_review", "high", candidate_reasons, []
    more_sources, source_reasons = should_need_more_sources(record)
    if more_sources:
        confidence = "medium" if int(record.get("quality_score_total", 0)) >= 38 else "low"
        return "needs_more_sources", confidence, source_reasons, []
    return "hold", "medium", ["No blocking issue, regeneration trigger, or readiness candidate rule matched."], []


def build_auto_decision_record(record: dict[str, Any], index: int) -> dict[str, Any]:
    require_record_fields(record, index)
    auto_decision, confidence, reasons, blocking_reasons = choose_decision(record)
    publish_candidate = auto_decision == "candidate_for_publish_readiness_review"
    return {
        "signal_id": normalize_text(record.get("signal_id")),
        "title": normalize_text(record.get("title")),
        "quality_tier": normalize_text(record.get("quality_tier")),
        "quality_score_total": int(record.get("quality_score_total")),
        "quality_score_max": int(record.get("quality_score_max")),
        "source_url": normalize_text(record.get("source_url")),
        "source_authority": source_authority(record),
        "agi_capability": agi_capability(record),
        "auto_decision": auto_decision,
        "decision_label": DECISION_LABELS[auto_decision],
        "decision_confidence": confidence,
        "decision_reasons": reasons,
        "blocking_reasons": blocking_reasons,
        "missing_fields": normalize_list(record.get("missing_fields")),
        "risk_flags": combined_risk_flags(record),
        "recommended_next_action": NEXT_ACTION_BY_DECISION[auto_decision],
        "owner_override_allowed": True,
        "publish_readiness_candidate": publish_candidate,
        "publication_approved": False,
    }


def decision_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = {decision: 0 for decision in AUTO_DECISIONS}
    for record in records:
        counts[record["auto_decision"]] += 1
    return counts


def needs_owner_attention(record: dict[str, Any]) -> tuple[bool, str, str]:
    decision = normalize_text(record.get("auto_decision"))
    total = int(record.get("quality_score_total", 0))
    if decision == "candidate_for_publish_readiness_review":
        return True, "High-value candidate requires Owner inspection before any later readiness review.", "inspect candidate and confirm or override"
    if decision == "needs_more_sources" and total >= 38:
        return True, "Useful Signal needs better evidence before it can move forward.", "request stronger source evidence or hold"
    if total >= 48 and record.get("missing_fields"):
        return True, "High-score Signal is missing evidence fields that may change the next action.", "inspect missing fields and override if needed"
    return False, "", ""


def exception_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    exceptions: list[dict[str, Any]] = []
    for record in records:
        include, reason, action = needs_owner_attention(record)
        if include:
            exceptions.append(
                {
                    "signal_id": record["signal_id"],
                    "title": record["title"],
                    "auto_decision": record["auto_decision"],
                    "decision_label": record["decision_label"],
                    "reason_owner_attention_needed": reason,
                    "suggested_owner_action": action,
                }
            )
    return exceptions


def recommended_owner_attention(records: list[dict[str, Any]], exceptions: list[dict[str, Any]]) -> dict[str, Any]:
    counts = decision_counts(records)
    inspect_first = [record["signal_id"] for record in exceptions[:5]]
    return {
        "signals_can_be_ignored": counts["auto_reject"],
        "signals_need_regeneration": counts["needs_regeneration"],
        "signals_need_more_evidence": counts["needs_more_sources"],
        "signals_candidate_for_later_publish_readiness_review": counts["candidate_for_publish_readiness_review"],
        "signals_on_hold": counts["hold"],
        "inspect_first_signal_ids": inspect_first,
        "summary": (
            f"{counts['auto_reject']} can be ignored, {counts['needs_regeneration']} need regeneration, "
            f"{counts['needs_more_sources']} need more evidence, "
            f"{counts['candidate_for_publish_readiness_review']} are candidates for later readiness review, "
            f"and {counts['hold']} can be held."
        ),
    }


def build_auto_decision_report(
    score_report_path: str | pathlib.Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    score_report = read_json_object(score_report_path, "SignalQualityScore V1 report")
    require_report_fields(score_report)
    records = [
        build_auto_decision_record(record, index)
        for index, record in enumerate(score_report["score_records"])
    ]
    exceptions = exception_records(records)
    return {
        "auto_decision_version": AUTO_DECISION_VERSION,
        "created_at": created_at or utc_now(),
        "source_score_report": str(score_report_path),
        "signals_evaluated": len(records),
        "decision_counts": decision_counts(records),
        "auto_decision_records": records,
        "exception_records": exceptions,
        "recommended_owner_attention": recommended_owner_attention(records, exceptions),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def write_json(path: str | pathlib.Path, content: dict[str, Any]) -> None:
    output_path = pathlib.Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_auto_decision(
    score_report_path: str | pathlib.Path,
    output_path: str | pathlib.Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    report = build_auto_decision_report(score_report_path, created_at=created_at)
    write_json(output_path, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Auto Decision Engine V1.")
    parser.add_argument("--score-report", required=True, help="Path to SignalQualityScore V1 JSON.")
    parser.add_argument("--output", required=True, help="Path to write Auto Decision Engine V1 JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_auto_decision(args.score_report, args.output)
    except AutoDecisionInputError as exc:
        print(f"[auto-decision-engine] failed: {exc}")
        return 1
    print(
        "[auto-decision-engine] wrote report: "
        f"{args.output} signals_evaluated={report['signals_evaluated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
