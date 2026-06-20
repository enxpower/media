#!/usr/bin/env python3
"""DysonX Internal Intelligence Brief V1.

Builds internal owner-review Markdown and JSON briefs from an existing
SignalQualityScore V1 report. This script is offline and deterministic. It
does not call OpenAI, dispatch workflows, publish, write website pages, mutate
Notion, call live GitHub APIs, scrape article bodies, write Knowledge Graph
records, run Prediction Engine work, enable publish readiness, or deploy.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Any


BRIEF_VERSION = "internal_intelligence_brief_v1"
GENERATED_FOR = "internal_owner_review"
SCORE_VERSION = "signal_quality_score_v1"

OWNER_DECISION_PLACEHOLDERS = (
    "approve_for_future_publish_readiness_review",
    "request_more_sources",
    "request_regeneration",
    "reject",
    "hold",
)

SAFETY_FLAGS = {
    "openai_call_performed": False,
    "workflow_dispatched": False,
    "publishing_performed": False,
    "public_content_generated": False,
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


class BriefInputError(ValueError):
    """Raised when a score report cannot safely produce a brief."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    report_path = pathlib.Path(path)
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should fail closed on malformed JSON.
        raise BriefInputError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise BriefInputError(f"{label} must be a JSON object")
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
        "created_at",
        "input_audit_report",
        "signals_scored",
        "score_records",
        "tier_counts",
        "recommended_next_actions",
        "safety_flags",
    )
    missing = [field for field in required_fields if field not in report]
    if missing:
        raise BriefInputError(f"Score report missing required fields: {', '.join(missing)}")
    if report.get("score_version") != SCORE_VERSION:
        raise BriefInputError("Score report must be SignalQualityScore V1")
    if not isinstance(report.get("score_records"), list) or not all(
        isinstance(record, dict) for record in report.get("score_records", [])
    ):
        raise BriefInputError("Score report score_records must be a list of objects")
    if not isinstance(report.get("tier_counts"), dict):
        raise BriefInputError("Score report tier_counts must be an object")


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
        "requires_human_review",
        "correlation_recommended",
    )
    missing = [field for field in required_fields if field not in record]
    if missing:
        raise BriefInputError(f"Score record {index} missing required fields: {', '.join(missing)}")
    if not isinstance(record.get("quality_score_total"), int):
        raise BriefInputError(f"Score record {index} quality_score_total must be an integer")
    if not isinstance(record.get("quality_score_max"), int):
        raise BriefInputError(f"Score record {index} quality_score_max must be an integer")
    if not isinstance(record.get("requires_human_review"), bool):
        raise BriefInputError(f"Score record {index} requires_human_review must be boolean")
    if not isinstance(record.get("correlation_recommended"), bool):
        raise BriefInputError(f"Score record {index} correlation_recommended must be boolean")


def validated_records(report: dict[str, Any]) -> list[dict[str, Any]]:
    require_report_fields(report)
    records = report["score_records"]
    for index, record in enumerate(records):
        require_record_fields(record, index)
    return records


def is_tier_a(record: dict[str, Any]) -> bool:
    return normalize_text(record.get("quality_tier")).startswith("Tier A")


def is_tier_b(record: dict[str, Any]) -> bool:
    return normalize_text(record.get("quality_tier")).startswith("Tier B")


def is_blocked_or_low_value(record: dict[str, Any]) -> bool:
    tier = normalize_text(record.get("quality_tier"))
    critical = normalize_list(record.get("critical_risk_flags"))
    return bool(critical) or tier.startswith("Tier C") or tier.startswith("Tier D")


def compact_record(record: dict[str, Any]) -> dict[str, Any]:
    critical = normalize_list(record.get("critical_risk_flags"))
    noncritical = normalize_list(record.get("noncritical_risk_flags"))
    return {
        "signal_id": normalize_text(record.get("signal_id")),
        "title": normalize_text(record.get("title")),
        "source_url": normalize_text(record.get("source_url")),
        "quality_score_total": int(record.get("quality_score_total", 0)),
        "quality_score_max": int(record.get("quality_score_max", 0)),
        "quality_tier": normalize_text(record.get("quality_tier")),
        "recommended_action": normalize_text(record.get("recommended_action")),
        "missing_fields": normalize_list(record.get("missing_fields")),
        "critical_risk_flags": critical,
        "noncritical_risk_flags": noncritical,
        "risk_flags": sorted(set(critical + noncritical)),
        "why_it_matters": normalize_text(record.get("why_it_matters")),
        "watch_next": normalize_text(record.get("watch_next")),
        "score_explanation": normalize_text(record.get("score_explanation")),
    }


def owner_review_item(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "signal_id": normalize_text(record.get("signal_id")),
        "title": normalize_text(record.get("title")),
        "tier": normalize_text(record.get("quality_tier")),
        "action": normalize_text(record.get("recommended_action")),
        "owner_decision_placeholder": list(OWNER_DECISION_PLACEHOLDERS),
    }


def overall_recommendation(records: list[dict[str, Any]]) -> str:
    decision_grade = [record for record in records if is_tier_a(record) and not normalize_list(record.get("critical_risk_flags"))]
    useful = [record for record in records if is_tier_b(record)]
    blocked = [record for record in records if is_blocked_or_low_value(record)]
    if decision_grade:
        return "Review Tier A candidates internally, but do not publish yet."
    if useful:
        return "Review useful Tier B signals and improve confidence or correlation before any approval path."
    if blocked:
        return "Improve, regenerate, or reject blocked and low-value signals before owner approval."
    return "No usable Signals are ready for owner review yet; do not publish yet."


def default_next_actions(score_report: dict[str, Any]) -> list[str]:
    actions = [
        "Review Tier A and Tier B Signals internally.",
        "Regenerate or improve Tier C and Tier D Signals.",
        "Run confidence calibration later.",
        "Run correlation later.",
        "Do not publish yet.",
    ]
    for action in normalize_list(score_report.get("recommended_next_actions")):
        if action not in actions:
            actions.append(action)
    return actions


def build_brief(
    score_report_path: str | pathlib.Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    score_report = read_json_object(score_report_path, "SignalQualityScore V1 report")
    records = validated_records(score_report)
    decision_grade = [
        compact_record(record)
        for record in records
        if is_tier_a(record) and not normalize_list(record.get("critical_risk_flags"))
    ]
    useful = [compact_record(record) for record in records if is_tier_b(record)]
    blocked = [compact_record(record) for record in records if is_blocked_or_low_value(record)]
    review_queue = [owner_review_item(record) for record in records]
    return {
        "brief_version": BRIEF_VERSION,
        "created_at": created_at or utc_now(),
        "source_score_report": str(score_report_path),
        "generated_for": GENERATED_FOR,
        "signals_reviewed": int(score_report.get("signals_scored", len(records))),
        "tier_counts": dict(score_report.get("tier_counts", {})),
        "blocked_count": len(blocked),
        "human_review_count": sum(1 for record in records if bool(record.get("requires_human_review"))),
        "correlation_recommended_count": sum(1 for record in records if bool(record.get("correlation_recommended"))),
        "overall_recommendation": overall_recommendation(records),
        "decision_grade_candidates": decision_grade,
        "useful_review_queue": useful,
        "blocked_or_low_value": blocked,
        "owner_review_queue": review_queue,
        "recommended_next_actions": default_next_actions(score_report),
        "safety_flags": dict(SAFETY_FLAGS),
    }


def bullet_list(values: list[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def score_text(record: dict[str, Any]) -> str:
    return f"{record['quality_score_total']} / {record['quality_score_max']}"


def render_record(record: dict[str, Any], include_owner_review: bool = False) -> list[str]:
    lines = [
        f"### {record['title'] or '(untitled signal)'}",
        f"- source_url: {record['source_url'] or 'missing'}",
        f"- score: {score_text(record)}",
        f"- quality_tier: {record['quality_tier']}",
        f"- recommended_action: {record['recommended_action']}",
    ]
    if record.get("why_it_matters"):
        lines.append(f"- why_it_matters: {record['why_it_matters']}")
    if record.get("watch_next"):
        lines.append(f"- watch_next: {record['watch_next']}")
    lines.append(f"- risk_flags: {bullet_list(record.get('risk_flags', []))}")
    if include_owner_review:
        missing = bullet_list(record.get("missing_fields", []))
        lines.append(f"- missing_fields: {missing}")
        lines.append("- what_owner_should_review: source support, confidence, correlation need, and whether to improve or reject.")
    return lines


def render_markdown(brief: dict[str, Any]) -> str:
    lines = [
        "# DysonX Internal Intelligence Brief V1",
        "",
        "## Brief Metadata",
        f"- brief_version: {brief['brief_version']}",
        f"- created_at: {brief['created_at']}",
        f"- source_score_report: {brief['source_score_report']}",
        f"- signals_reviewed: {brief['signals_reviewed']}",
        f"- generated_for: {brief['generated_for']}",
        "",
        "## Executive Summary",
        f"- Signals reviewed: {brief['signals_reviewed']}",
        f"- Tier counts: {json.dumps(brief['tier_counts'], sort_keys=True)}",
        f"- Blocked by critical risks or low-value tier: {brief['blocked_count']}",
        f"- Requiring human review: {brief['human_review_count']}",
        f"- Recommended for correlation: {brief['correlation_recommended_count']}",
        f"- Overall recommendation: {brief['overall_recommendation']}",
        "",
        "## Decision-Grade Candidates",
    ]
    if brief["decision_grade_candidates"]:
        for record in brief["decision_grade_candidates"]:
            lines.extend(render_record(record))
            lines.append("")
    else:
        lines.append("No decision-grade candidates yet.")
        lines.append("")
    lines.append("## Useful Signals Requiring Review")
    if brief["useful_review_queue"]:
        for record in brief["useful_review_queue"]:
            lines.extend(render_record(record, include_owner_review=True))
            lines.append("")
    else:
        lines.append("No useful Tier B Signals requiring review.")
        lines.append("")
    lines.append("## Blocked / Low-Value Signals")
    if brief["blocked_or_low_value"]:
        for record in brief["blocked_or_low_value"]:
            lines.extend(
                [
                    f"### {record['title'] or '(untitled signal)'}",
                    f"- tier: {record['quality_tier']}",
                    f"- critical_risk_flags: {bullet_list(record['critical_risk_flags'])}",
                    f"- recommended_action: {record['recommended_action']}",
                    f"- reason_for_block: {record['score_explanation'] or bullet_list(record['critical_risk_flags']) or 'Tier requires improvement before review.'}",
                ]
            )
            lines.append("")
    else:
        lines.append("No blocked or low-value Signals.")
        lines.append("")
    lines.extend(
        [
            "## Owner Review Queue",
            "| signal_id | title | tier | action | owner_decision_placeholder |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in brief["owner_review_queue"]:
        placeholders = "<br>".join(item["owner_decision_placeholder"])
        lines.append(
            f"| {item['signal_id']} | {item['title']} | {item['tier']} | {item['action']} | {placeholders} |"
        )
    lines.extend(["", "## Next Actions"])
    for action in brief["recommended_next_actions"]:
        lines.append(f"- {action}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "- No publishing performed",
            "- No public content generated",
            "- No website pages written",
            "- No social posts generated",
            "- No OpenAI call performed",
            "- No workflow dispatched",
            "- No Notion mutation",
            "- No live GitHub API used",
            "- No Knowledge Graph writes",
            "- No Prediction Engine work",
            "- No deployment performed",
            "",
        ]
    )
    return "\n".join(lines)


def write_text(path: str | pathlib.Path, content: str) -> None:
    output_path = pathlib.Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def write_json(path: str | pathlib.Path, content: dict[str, Any]) -> None:
    output_path = pathlib.Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_brief(
    score_report_path: str | pathlib.Path,
    output_md_path: str | pathlib.Path,
    output_json_path: str | pathlib.Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    brief = build_brief(score_report_path, created_at=created_at)
    write_text(output_md_path, render_markdown(brief))
    write_json(output_json_path, brief)
    return brief


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Internal Intelligence Brief V1.")
    parser.add_argument("--score-report", required=True, help="Path to SignalQualityScore V1 JSON.")
    parser.add_argument("--output-md", required=True, help="Path to write Markdown internal brief.")
    parser.add_argument("--output-json", required=True, help="Path to write JSON brief report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        brief = run_brief(args.score_report, args.output_md, args.output_json)
    except BriefInputError as exc:
        print(f"[internal-intelligence-brief] failed: {exc}")
        return 1
    print(
        "[internal-intelligence-brief] wrote brief: "
        f"{args.output_md} {args.output_json} signals_reviewed={brief['signals_reviewed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
