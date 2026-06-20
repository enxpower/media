#!/usr/bin/env python3
"""DysonX Owner Review Feedback V1.

Captures Owner decisions on Internal Intelligence Brief V1 review items as a
structured offline JSON report. This script is deterministic. It does not call
OpenAI, dispatch workflows, publish, write public content, mutate Notion, call
live GitHub APIs, scrape article bodies, store raw provider responses, write
Knowledge Graph records, run Prediction Engine work, perform confidence
calibration or correlation, enable publish readiness, or deploy.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any


FEEDBACK_VERSION = "owner_review_feedback_v1"
BRIEF_VERSION = "internal_intelligence_brief_v1"

ALLOWED_OWNER_DECISIONS = (
    "approve_for_future_publish_readiness_review",
    "request_more_sources",
    "request_regeneration",
    "reject",
    "hold",
)

ALLOWED_PRIORITIES = ("high", "medium", "low")

RESULTING_STATUS_BY_DECISION = {
    "approve_for_future_publish_readiness_review": "owner_approved_for_later_publish_readiness_review_only",
    "request_more_sources": "needs_more_sources",
    "request_regeneration": "needs_regeneration",
    "reject": "owner_rejected",
    "hold": "owner_hold",
}

NEXT_ACTION_BY_DECISION = {
    "approve_for_future_publish_readiness_review": "later_publish_readiness_review_required",
    "request_more_sources": "collect_or_attach_more_sources",
    "request_regeneration": "regenerate_or_improve_signal_analysis",
    "reject": "remove_from_current_review_queue",
    "hold": "keep_for_later_review",
}

SAFETY_FLAGS = {
    "openai_call_performed": False,
    "workflow_dispatched": False,
    "publishing_performed": False,
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


class FeedbackInputError(ValueError):
    """Raised when owner feedback cannot safely produce a report."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    input_path = pathlib.Path(path)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should fail closed on malformed JSON.
        raise FeedbackInputError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise FeedbackInputError(f"{label} must be a JSON object")
    return data


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def require_brief_fields(brief: dict[str, Any]) -> None:
    required_fields = (
        "brief_version",
        "source_score_report",
        "signals_reviewed",
        "owner_review_queue",
        "safety_flags",
    )
    missing = [field for field in required_fields if field not in brief]
    if missing:
        raise FeedbackInputError(f"Internal Intelligence Brief missing required fields: {', '.join(missing)}")
    if brief.get("brief_version") != BRIEF_VERSION:
        raise FeedbackInputError("Brief report must be Internal Intelligence Brief V1")
    queue = brief.get("owner_review_queue")
    if not isinstance(queue, list) or not queue or not all(isinstance(item, dict) for item in queue):
        raise FeedbackInputError("Brief owner_review_queue must be a non-empty list of objects")


def require_queue_item_fields(item: dict[str, Any], index: int) -> None:
    required_fields = ("signal_id", "title", "tier", "action")
    missing = [field for field in required_fields if field not in item]
    if missing:
        raise FeedbackInputError(f"Brief owner_review_queue item {index} missing required fields: {', '.join(missing)}")
    if not normalize_text(item.get("signal_id")):
        raise FeedbackInputError(f"Brief owner_review_queue item {index} signal_id is required")


def owner_review_items_by_signal_id(brief: dict[str, Any]) -> dict[str, dict[str, Any]]:
    require_brief_fields(brief)
    items: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(brief["owner_review_queue"]):
        require_queue_item_fields(item, index)
        signal_id = normalize_text(item.get("signal_id"))
        if signal_id in items:
            raise FeedbackInputError(f"Brief owner_review_queue contains duplicate signal_id: {signal_id}")
        items[signal_id] = item
    return items


def require_feedback_fields(feedback: dict[str, Any], brief: dict[str, Any], brief_path: str | pathlib.Path) -> None:
    required_fields = (
        "reviewer",
        "review_session_id",
        "reviewed_at",
        "brief_version",
        "brief_source",
        "decisions",
    )
    missing = [field for field in required_fields if field not in feedback]
    if missing:
        raise FeedbackInputError(f"Owner feedback input missing required fields: {', '.join(missing)}")
    for field in ("reviewer", "review_session_id", "reviewed_at", "brief_version", "brief_source"):
        if not normalize_text(feedback.get(field)):
            raise FeedbackInputError(f"Owner feedback input field {field} is required")
    if feedback.get("brief_version") != brief.get("brief_version"):
        raise FeedbackInputError("Owner feedback input brief_version must match the brief JSON brief_version")
    brief_source = normalize_text(feedback.get("brief_source"))
    valid_sources = {str(brief_path), pathlib.Path(brief_path).name}
    if brief_source not in valid_sources and brief_source != normalize_text(brief.get("source_score_report")):
        raise FeedbackInputError("Owner feedback input brief_source must match or reference the source brief path")
    decisions = feedback.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        raise FeedbackInputError("Owner feedback input decisions must be a non-empty list")
    if not all(isinstance(decision, dict) for decision in decisions):
        raise FeedbackInputError("Owner feedback input decisions must be objects")


def validate_decision(decision: dict[str, Any], index: int, known_signal_ids: set[str]) -> None:
    required_fields = (
        "signal_id",
        "owner_decision",
        "owner_comment",
        "priority",
        "follow_up_required",
        "follow_up_note",
    )
    missing = [field for field in required_fields if field not in decision]
    if missing:
        raise FeedbackInputError(f"Owner feedback decision {index} missing required fields: {', '.join(missing)}")
    signal_id = normalize_text(decision.get("signal_id"))
    if signal_id not in known_signal_ids:
        raise FeedbackInputError(f"Owner feedback decision {index} references unknown signal_id: {signal_id}")
    owner_decision = normalize_text(decision.get("owner_decision"))
    if owner_decision not in ALLOWED_OWNER_DECISIONS:
        raise FeedbackInputError(f"Owner feedback decision {index} has unsupported owner_decision: {owner_decision}")
    priority = normalize_text(decision.get("priority"))
    if priority not in ALLOWED_PRIORITIES:
        raise FeedbackInputError(f"Owner feedback decision {index} has unsupported priority: {priority}")
    if not isinstance(decision.get("follow_up_required"), bool):
        raise FeedbackInputError(f"Owner feedback decision {index} follow_up_required must be boolean")
    if not isinstance(decision.get("owner_comment"), str):
        raise FeedbackInputError(f"Owner feedback decision {index} owner_comment must be a string")
    if not isinstance(decision.get("follow_up_note"), str):
        raise FeedbackInputError(f"Owner feedback decision {index} follow_up_note must be a string")


def validate_decisions(feedback: dict[str, Any], known_signal_ids: set[str]) -> None:
    seen: set[str] = set()
    for index, decision in enumerate(feedback["decisions"]):
        validate_decision(decision, index, known_signal_ids)
        signal_id = normalize_text(decision.get("signal_id"))
        if signal_id in seen:
            raise FeedbackInputError(f"Owner feedback input contains duplicate decision for signal_id: {signal_id}")
        seen.add(signal_id)


def build_feedback_record(decision: dict[str, Any], brief_item: dict[str, Any]) -> dict[str, Any]:
    owner_decision = normalize_text(decision.get("owner_decision"))
    return {
        "signal_id": normalize_text(decision.get("signal_id")),
        "title": normalize_text(brief_item.get("title")),
        "original_tier": normalize_text(brief_item.get("tier")),
        "original_recommended_action": normalize_text(brief_item.get("action")),
        "owner_decision": owner_decision,
        "owner_comment": decision.get("owner_comment", ""),
        "priority": normalize_text(decision.get("priority")),
        "follow_up_required": bool(decision.get("follow_up_required")),
        "follow_up_note": decision.get("follow_up_note", ""),
        "resulting_status": RESULTING_STATUS_BY_DECISION[owner_decision],
        "next_action": NEXT_ACTION_BY_DECISION[owner_decision],
    }


def decision_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts = {decision: 0 for decision in ALLOWED_OWNER_DECISIONS}
    for record in records:
        counts[record["owner_decision"]] += 1
    return counts


def recommended_next_actions(records: list[dict[str, Any]]) -> list[str]:
    decisions = {record["owner_decision"] for record in records}
    actions: list[str] = []
    if "request_more_sources" in decisions:
        actions.append("Prepare better source evidence for Signals marked request_more_sources.")
    if "request_regeneration" in decisions:
        actions.append("Improve Signal analysis prompt or regenerate selected Signals offline.")
    if "hold" in decisions:
        actions.append("Keep held Signals in the next internal brief or owner review queue.")
    if "approve_for_future_publish_readiness_review" in decisions:
        actions.append("Future publish-readiness review is required; do not publish automatically.")
    if "reject" in decisions:
        actions.append("Remove rejected Signals from the current owner review queue.")
    actions.append("Do not publish yet.")
    return actions


def build_feedback_report(
    brief_json_path: str | pathlib.Path,
    feedback_input_path: str | pathlib.Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    brief = read_json_object(brief_json_path, "Internal Intelligence Brief V1 report")
    feedback = read_json_object(feedback_input_path, "Owner feedback input")
    review_items = owner_review_items_by_signal_id(brief)
    require_feedback_fields(feedback, brief, brief_json_path)
    validate_decisions(feedback, set(review_items.keys()))
    records = [
        build_feedback_record(decision, review_items[normalize_text(decision.get("signal_id"))])
        for decision in feedback["decisions"]
    ]
    return {
        "feedback_version": FEEDBACK_VERSION,
        "created_at": created_at or utc_now(),
        "reviewer": normalize_text(feedback.get("reviewer")),
        "review_session_id": normalize_text(feedback.get("review_session_id")),
        "reviewed_at": normalize_text(feedback.get("reviewed_at")),
        "source_brief": str(brief_json_path),
        "brief_version": brief.get("brief_version"),
        "signals_reviewed": int(brief.get("signals_reviewed", len(review_items))),
        "decisions_recorded": len(records),
        "decision_counts": decision_counts(records),
        "follow_up_required_count": sum(1 for record in records if record["follow_up_required"]),
        "feedback_records": records,
        "recommended_next_actions": recommended_next_actions(records),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def write_json(path: str | pathlib.Path, content: dict[str, Any]) -> None:
    output_path = pathlib.Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_feedback(
    brief_json_path: str | pathlib.Path,
    feedback_input_path: str | pathlib.Path,
    output_path: str | pathlib.Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    report = build_feedback_report(brief_json_path, feedback_input_path, created_at=created_at)
    write_json(output_path, report)
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Owner Review Feedback V1.")
    parser.add_argument("--brief-json", required=True, help="Path to Internal Intelligence Brief V1 JSON.")
    parser.add_argument("--feedback-input", required=True, help="Path to Owner feedback input JSON.")
    parser.add_argument("--output", required=True, help="Path to write Owner Review Feedback V1 JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_feedback(args.brief_json, args.feedback_input, args.output)
    except FeedbackInputError as exc:
        print(f"[owner-review-feedback] failed: {exc}")
        return 1
    print(
        "[owner-review-feedback] wrote report: "
        f"{args.output} decisions_recorded={report['decisions_recorded']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
