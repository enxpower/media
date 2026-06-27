#!/usr/bin/env python3
"""DysonX Publish Readiness Gate V1.

Evaluates internally reviewed Signals for future public generation readiness.
This script is deterministic, offline, and standard-library only. It does not
publish, generate public pages, call OpenAI, dispatch workflows, fetch URLs,
scrape sources, write Knowledge Graph records, run Prediction Engine work,
perform confidence calibration or correlation, deploy, or change production.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse


GATE_VERSION = "publish_readiness_gate_v1"
DEFAULT_SCORE_MAX = 65
PASS_SCORE_THRESHOLD = 55
REVIEW_SCORE_THRESHOLD = 45

APPROVE_DECISIONS = {
    "approve_for_future_publish_readiness_review",
    "candidate_for_publish_readiness_review",
    "owner_approved_for_later_publish_readiness_review_only",
}

BLOCKED_DECISION_BY_STATUS = {
    "needs_more_sources": "blocked_needs_more_sources",
    "request_more_sources": "blocked_needs_more_sources",
    "needs_regeneration": "blocked_needs_regeneration",
    "request_regeneration": "blocked_needs_regeneration",
    "hold": "blocked_hold",
    "owner_hold": "blocked_hold",
    "reject": "blocked_rejected",
    "auto_reject": "blocked_rejected",
    "owner_rejected": "blocked_rejected",
}

PUBLIC_CONTENT_FIELDS = (
    "public_title",
    "public_slug",
    "public_summary",
    "public_why_it_matters",
    "public_watch_next",
    "public_capability_area",
    "public_source_label",
    "public_attribution",
)

RAW_CONTENT_FIELDS = (
    "raw_body",
    "article_body",
    "scraped_text",
    "full_text",
    "provider_response",
    "raw_provider_response",
    "raw_copyrighted_article_text",
)

CRITICAL_RISK_FLAGS = {
    "copyright_risk",
    "source_risk",
    "hallucination_risk",
    "weak_attribution",
    "weak_source_attribution",
    "generic_summary",
    "safety_sensitive_without_context",
    "missing_source",
    "missing_source_url",
    "raw_source_text_present",
    "raw_provider_response_present",
}

SAFETY_TRUE_FIELDS = (
    "auto_decision_is_not_publication_approval",
    "owner_feedback_is_not_publication_approval",
    "review_session_is_not_publication_approval",
)


class GateInputError(ValueError):
    """Raised when the gate cannot safely read or validate inputs."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    input_path = pathlib.Path(path)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI fails closed on malformed JSON.
        raise GateInputError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise GateInputError(f"{label} must be a JSON object")
    return data


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def first_present(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, "", []):
            return value
    return None


def bool_value(record: dict[str, Any], key: str) -> bool:
    return bool(record.get(key))


def signal_id_from(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "signal_id", "canonical_signal_id", "id"))


def merge_record(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in update.items():
        if value not in (None, "", []):
            merged[key] = value
    return merged


def owner_records(owner_feedback: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(owner_feedback.get("records"), list):
        return [item for item in owner_feedback["records"] if isinstance(item, dict)]
    if isinstance(owner_feedback.get("feedback_records"), list):
        return [item for item in owner_feedback["feedback_records"] if isinstance(item, dict)]
    decisions = owner_feedback.get("decisions")
    if isinstance(decisions, list):
        return [item for item in decisions if isinstance(item, dict)]
    raise GateInputError("Owner feedback must include records, feedback_records, or decisions")


def brief_records(brief: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not brief:
        return {}
    sections = (
        "decision_grade_candidates",
        "useful_review_queue",
        "blocked_or_low_value",
        "owner_review_queue",
    )
    records: dict[str, dict[str, Any]] = {}
    for section in sections:
        for item in as_list(brief.get(section)):
            if not isinstance(item, dict):
                continue
            signal_id = signal_id_from(item)
            if signal_id:
                records[signal_id] = merge_record(records.get(signal_id, {}), item)
    return records


def score_records(score_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not score_report:
        return {}
    records: dict[str, dict[str, Any]] = {}
    for item in as_list(score_report.get("score_records")):
        if not isinstance(item, dict):
            continue
        signal_id = signal_id_from(item)
        if signal_id:
            records[signal_id] = item
    return records


def build_signal_contexts(
    owner_feedback: dict[str, Any],
    brief: dict[str, Any] | None,
    score_report: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    by_brief = brief_records(brief)
    by_score = score_records(score_report)
    contexts: list[dict[str, Any]] = []
    for owner_record in owner_records(owner_feedback):
        signal_id = signal_id_from(owner_record)
        if not signal_id:
            continue
        context: dict[str, Any] = {}
        context = merge_record(context, by_score.get(signal_id, {}))
        context = merge_record(context, by_brief.get(signal_id, {}))
        context = merge_record(context, owner_record)
        context["signal_id"] = signal_id
        contexts.append(context)
    return contexts


def source_url(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "source_url", "first_source_url", "original_source_url"))


def source_hostname(url: str) -> str:
    try:
        return urlparse(url).hostname or ""
    except ValueError:
        return ""


def has_unknown_source(record: dict[str, Any]) -> bool:
    values = [
        source_url(record),
        normalize_text(first_present(record, "source_authority", "source_authority_reasoning")),
        normalize_text(first_present(record, "public_source_label", "source_title", "source_reference")),
    ]
    return any(value.lower() in {"unknown", "missing", "none", "n/a"} for value in values if value)


def numeric_score(record: dict[str, Any]) -> tuple[float | None, float | None, bool]:
    score_value = first_present(record, "score", "quality_score_total", "total_score")
    max_value = first_present(record, "max_score", "quality_score_max", "score_max")
    try:
        score = float(score_value)
    except (TypeError, ValueError):
        return None, None, True
    if max_value in (None, ""):
        return score, float(DEFAULT_SCORE_MAX), False
    try:
        max_score = float(max_value)
    except (TypeError, ValueError):
        return score, None, True
    if max_score <= 0:
        return score, None, True
    return score, max_score, False


def normalized_score_65(record: dict[str, Any]) -> tuple[float | None, bool]:
    score, max_score, unknown = numeric_score(record)
    if score is None or max_score is None or unknown:
        return None, True
    return score * DEFAULT_SCORE_MAX / max_score, False


def risk_flags(record: dict[str, Any]) -> set[str]:
    flags: set[str] = set()
    for key in ("risk_flags", "critical_risk_flags", "noncritical_risk_flags"):
        for flag in as_list(record.get(key)):
            if isinstance(flag, str) and flag.strip():
                flags.add(flag.strip())
    if bool_value(record, "generic_summary_risk"):
        flags.add("generic_summary")
    if bool_value(record, "weak_attribution_risk"):
        flags.add("weak_attribution")
    if bool_value(record, "copyright_risk"):
        flags.add("copyright_risk")
    return flags


def add_block(blockers: list[str], actions: list[str], blocker: str, action: str) -> None:
    if blocker not in blockers:
        blockers.append(blocker)
    if action not in actions:
        actions.append(action)


def candidate_status(record: dict[str, Any]) -> set[str]:
    values = {
        normalize_text(first_present(record, "auto_decision")),
        normalize_text(first_present(record, "selected_owner_decision", "owner_decision")),
        normalize_text(first_present(record, "resulting_status")),
        normalize_text(first_present(record, "recommended_action", "action")),
    }
    if bool_value(record, "publish_readiness_candidate"):
        values.add("candidate_for_publish_readiness_review")
    return {value for value in values if value}


def infer_owner_review_status(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "owner_review_status", "resulting_status")) or "inferred_from_owner_feedback"


def evaluate_signal(
    record: dict[str, Any],
    owner_feedback: dict[str, Any],
    now: str,
) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    required_next_actions: list[str] = []
    signal_id = signal_id_from(record)

    review_session_id = normalize_text(first_present(owner_feedback, "review_session_id", "wizard_session_id"))
    owner_review_source = normalize_text(first_present(owner_feedback, "reviewer", "owner_review_wizard_version", "feedback_version"))
    if not review_session_id:
        add_block(blockers, required_next_actions, "missing_review_session_id", "provide_review_session_id_or_wizard_session_id")
    if not owner_review_source:
        add_block(blockers, required_next_actions, "missing_owner_review_source", "provide_reviewer_or_owner_review_source")

    selected_decision = normalize_text(first_present(record, "selected_owner_decision", "owner_decision"))
    if not selected_decision:
        add_block(blockers, required_next_actions, "missing_selected_owner_decision", "record_selected_owner_decision")
    owner_review_status = infer_owner_review_status(record)

    if record.get("publication_approved") is True or owner_feedback.get("publication_approved") is True:
        add_block(blockers, required_next_actions, "publication_approved_true_without_gate_logic", "reset_publication_approved_false_and_recheck")

    for field in SAFETY_TRUE_FIELDS:
        if owner_feedback.get(field) is not True:
            warnings.append(f"missing_or_false_{field}")
            add_block(blockers, required_next_actions, f"missing_safety_statement_{field}", "include_owner_feedback_safety_statements")

    statuses = candidate_status(record)
    blocked_status_decision = next((BLOCKED_DECISION_BY_STATUS[value] for value in statuses if value in BLOCKED_DECISION_BY_STATUS), None)
    if blocked_status_decision:
        add_block(blockers, required_next_actions, blocked_status_decision, "resolve_internal_review_decision_before_public_generation")
    if not statuses.intersection(APPROVE_DECISIONS):
        add_block(blockers, required_next_actions, "not_publish_readiness_candidate", "route_only_approved_candidates_to_publish_readiness_gate")

    url = source_url(record)
    if not url:
        add_block(blockers, required_next_actions, "missing_source_url", "attach_first_source_url")
    else:
        hostname = source_hostname(url)
        if hostname in {"example.org", "example.com", "example.net"}:
            if record.get("fixture_mode") is True:
                warnings.append("fixture_only_not_publishable")
                add_block(blockers, required_next_actions, "fixture_only_not_publishable", "replace_fixture_source_with_real_source_before_public_generation")
            else:
                add_block(blockers, required_next_actions, "example_source_without_fixture_mode", "replace_example_source_or_mark_fixture_mode")
    if not normalize_text(first_present(record, "source_authority", "source_authority_reasoning")):
        add_block(blockers, required_next_actions, "missing_source_authority", "add_source_authority_reasoning")
    if not normalize_text(first_present(record, "source_title", "source_reference", "public_source_label")):
        add_block(blockers, required_next_actions, "missing_source_reference", "add_source_title_or_public_source_label")
    if has_unknown_source(record):
        add_block(blockers, required_next_actions, "unknown_source", "replace_unknown_source_with_attributed_source")

    for field in RAW_CONTENT_FIELDS:
        if record.get(field):
            add_block(blockers, required_next_actions, "raw_source_content_present", "remove_raw_source_or_provider_content")
            break

    missing_public_fields = [field for field in PUBLIC_CONTENT_FIELDS if not normalize_text(record.get(field))]
    for field in missing_public_fields:
        add_block(blockers, required_next_actions, f"missing_{field}", "add_required_public_content_fields")

    capability = normalize_text(first_present(record, "specific_agi_capability", "agi_capability_affected", "agi_capability", "public_capability_area"))
    if not capability:
        add_block(blockers, required_next_actions, "missing_specific_agi_capability", "map_signal_to_specific_agi_capability")
    if not normalize_text(first_present(record, "why_it_matters", "public_why_it_matters")):
        add_block(blockers, required_next_actions, "missing_why_it_matters", "add_why_it_matters")
    if not normalize_text(first_present(record, "watch_next", "public_watch_next")):
        add_block(blockers, required_next_actions, "missing_watch_next", "add_watch_next")
    if not first_present(record, "entities", "key_entities"):
        add_block(blockers, required_next_actions, "missing_entities", "add_relevant_entities")
    if bool_value(record, "generic_summary_risk"):
        add_block(blockers, required_next_actions, "generic_summary_risk", "regenerate_as_structured_signal")
    if bool_value(record, "weak_attribution_risk"):
        add_block(blockers, required_next_actions, "weak_attribution_risk", "strengthen_source_attribution")
    if bool_value(record, "concrete_decision_value") is False and "concrete_decision_value" in record:
        add_block(blockers, required_next_actions, "missing_concrete_decision_value", "add_decision_usefulness_or_block")

    score_65, scale_unknown = normalized_score_65(record)
    if scale_unknown:
        add_block(blockers, required_next_actions, "score_scale_unknown", "provide_score_and_max_score")
    elif score_65 is not None and score_65 < PASS_SCORE_THRESHOLD:
        if score_65 >= REVIEW_SCORE_THRESHOLD:
            add_block(blockers, required_next_actions, "quality_requires_additional_review", "add_sources_or_owner_review_before_public_generation")
        else:
            add_block(blockers, required_next_actions, "quality_below_threshold", "improve_signal_quality_before_public_generation")
    if not normalize_text(first_present(record, "quality_tier", "tier")):
        add_block(blockers, required_next_actions, "missing_quality_tier", "include_quality_tier")

    critical_flags = sorted(flag for flag in risk_flags(record) if flag in CRITICAL_RISK_FLAGS)
    for flag in critical_flags:
        add_block(blockers, required_next_actions, f"critical_risk_{flag}", "resolve_critical_risk_flags")

    if not normalize_text(record.get("public_slug")):
        add_block(blockers, required_next_actions, "missing_public_slug", "add_public_slug")
    if not normalize_text(first_present(record, "canonical_signal_id", "signal_id")):
        add_block(blockers, required_next_actions, "missing_canonical_signal_id", "add_canonical_signal_id")
    if not normalize_text(record.get("publication_candidate_id")):
        add_block(blockers, required_next_actions, "missing_publication_candidate_id", "add_publication_candidate_id")
    if not normalize_text(record.get("public_surface_target")):
        add_block(blockers, required_next_actions, "missing_public_surface_target", "set_public_surface_target")

    gate_decision = choose_gate_decision(blockers)
    passed = not blockers
    return {
        "signal_id": signal_id,
        "canonical_signal_id": normalize_text(first_present(record, "canonical_signal_id", "signal_id")),
        "publication_candidate_id": normalize_text(record.get("publication_candidate_id")),
        "title": normalize_text(record.get("title")),
        "owner_review_status": owner_review_status,
        "selected_owner_decision": selected_decision,
        "source_url": url,
        "score_normalized_to_65": score_65,
        "quality_tier": normalize_text(first_present(record, "quality_tier", "tier")),
        "publish_readiness_gate_passed": passed,
        "ready_for_public_generation": passed,
        "public_generation_blocked": not passed,
        "public_generation_blockers": blockers,
        "gate_decision": gate_decision,
        "blockers": blockers,
        "warnings": warnings,
        "required_next_actions": required_next_actions,
        "fixture_only_not_publishable": "fixture_only_not_publishable" in blockers,
        "public_surface_target": normalize_text(record.get("public_surface_target")),
        "gate_version": GATE_VERSION,
        "gate_checked_at": now,
        "published": False,
        "publication_approved": False,
    }


def choose_gate_decision(blockers: list[str]) -> str:
    if not blockers:
        return "ready_for_public_generation"
    priority = (
        ("raw_source_content_present", "blocked_raw_source_content"),
        ("fixture_only_not_publishable", "blocked_fixture_only"),
        ("example_source_without_fixture_mode", "blocked_missing_source"),
        ("missing_source_url", "blocked_missing_source"),
        ("unknown_source", "blocked_missing_source"),
        ("blocked_needs_more_sources", "blocked_needs_more_sources"),
        ("blocked_needs_regeneration", "blocked_needs_regeneration"),
        ("blocked_hold", "blocked_hold"),
        ("blocked_rejected", "blocked_rejected"),
        ("quality_below_threshold", "blocked_quality_threshold"),
        ("quality_requires_additional_review", "blocked_quality_threshold"),
        ("generic_summary_risk", "blocked_risk_flags"),
        ("weak_attribution_risk", "blocked_risk_flags"),
    )
    for blocker, decision in priority:
        if blocker in blockers:
            return decision
    if any(blocker.startswith("critical_risk_") for blocker in blockers):
        return "blocked_risk_flags"
    if any(blocker.startswith("missing_public_") for blocker in blockers) or "missing_public_slug" in blockers:
        return "blocked_missing_public_fields"
    if any(blocker.startswith("missing_") for blocker in blockers):
        return "insufficient_input"
    return "insufficient_input"


def build_report(
    owner_feedback: dict[str, Any],
    owner_feedback_path: pathlib.Path,
    brief: dict[str, Any] | None,
    brief_path: pathlib.Path | None,
    score_report: dict[str, Any] | None,
    score_report_path: pathlib.Path | None,
) -> dict[str, Any]:
    now = utc_now()
    contexts = build_signal_contexts(owner_feedback, brief, score_report)
    evaluations = [evaluate_signal(context, owner_feedback, now) for context in contexts]
    ready_count = sum(1 for item in evaluations if item["ready_for_public_generation"])
    blocked_count = sum(1 for item in evaluations if item["public_generation_blocked"])
    warning_count = sum(len(item["warnings"]) for item in evaluations)
    return {
        "gate_version": GATE_VERSION,
        "created_at": now,
        "input_files": {
            "owner_feedback": str(owner_feedback_path),
            "brief": str(brief_path) if brief_path else None,
            "score_report": str(score_report_path) if score_report_path else None,
        },
        "signals_evaluated": len(evaluations),
        "ready_count": ready_count,
        "blocked_count": blocked_count,
        "warning_count": warning_count,
        "evaluations": evaluations,
        "no_public_publishing_performed": True,
        "no_deployment_performed": True,
        "no_openai_call_performed": True,
        "no_workflow_dispatch_performed": True,
        "public_pages_generated": False,
        "knowledge_graph_write_performed": False,
        "prediction_engine_performed": False,
        "confidence_calibration_performed": False,
        "multi_source_correlation_performed": False,
    }


def write_report(report: dict[str, Any], output_path: str | pathlib.Path) -> pathlib.Path:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate DysonX Signals with Publish Readiness Gate V1.")
    parser.add_argument("--owner-feedback", required=True, help="Owner Feedback JSON or Wizard Feedback JSON input.")
    parser.add_argument("--brief", help="Optional Internal Intelligence Brief JSON input.")
    parser.add_argument("--score-report", help="Optional SignalQualityScore report JSON input.")
    parser.add_argument("--output", required=True, help="Output Publish Readiness Gate report JSON path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    owner_feedback_path = pathlib.Path(args.owner_feedback)
    brief_path = pathlib.Path(args.brief) if args.brief else None
    score_report_path = pathlib.Path(args.score_report) if args.score_report else None
    try:
        owner_feedback = read_json_object(owner_feedback_path, "Owner feedback")
        brief = read_json_object(brief_path, "Internal brief") if brief_path else None
        score_report = read_json_object(score_report_path, "Signal quality score report") if score_report_path else None
        report = build_report(owner_feedback, owner_feedback_path, brief, brief_path, score_report, score_report_path)
        output_path = write_report(report, args.output)
    except GateInputError as exc:
        print(f"[publish-readiness-gate] failed: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[publish-readiness-gate] failed: {exc}", file=sys.stderr)
        return 2
    print(
        "[publish-readiness-gate] wrote report: "
        f"{output_path} signals_evaluated={report['signals_evaluated']} "
        f"ready={report['ready_count']} blocked={report['blocked_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
