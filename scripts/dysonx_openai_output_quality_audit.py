#!/usr/bin/env python3
"""DysonX OpenAI Output Quality Audit V1.

Reads already-generated safe JSON reports and scores IntelligenceSignal output
against the DysonX Signal Quality Framework. This script is deterministic and
offline: it does not call OpenAI, dispatch workflows, publish, scrape, mutate
Notion, call GitHub, write Knowledge Graph records, run Prediction Engine work,
or deploy.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Any


AUDIT_VERSION = "openai_output_quality_audit_v1"
FRAMEWORK_REFERENCE = "docs/DYSONX_SIGNAL_QUALITY_FRAMEWORK_V1.md"
MILESTONE_REFERENCE = "docs/DYSONX_V1_OPENAI_ORCHESTRATOR_SMOKE_MILESTONE.md"

QUALITY_DIMENSIONS = (
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

GENERIC_PHRASES = (
    "this is important",
    "important development",
    "stay tuned",
    "in today's fast-paced",
    "game changer",
    "revolutionary",
    "cutting-edge",
    "could change everything",
    "ai is transforming",
    "should be reviewed before publication",
    "verify the original source",
)

ARTICLE_LIKE_PHRASES = (
    "in this article",
    "this article",
    "read on",
    "we will explore",
    "breaking news",
    "latest news",
    "according to reports",
)

SEO_LIKE_PHRASES = (
    "ultimate guide",
    "top ",
    "best ",
    "you need to know",
    "everything you need",
)


class AuditInputError(ValueError):
    """Raised when a report cannot be audited safely."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    report_path = pathlib.Path(path)
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI should fail closed on malformed JSON.
        raise AuditInputError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AuditInputError(f"{label} must be a JSON object")
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


def word_count(*values: Any) -> int:
    text = " ".join(normalize_text(value) for value in values)
    return len(re.findall(r"[A-Za-z0-9_]+", text))


def has_url(value: Any) -> bool:
    text = normalize_text(value)
    return text.startswith("http://") or text.startswith("https://")


def lower_blob(signal: dict[str, Any]) -> str:
    fields = (
        signal.get("title"),
        signal.get("summary"),
        signal.get("why_it_matters"),
        signal.get("watch_next"),
        signal.get("agi_capability"),
    )
    return " ".join(normalize_text(field).lower() for field in fields)


def contains_phrase(blob: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in blob for phrase in phrases)


def recursively_contains_raw_provider_response(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in {"raw_provider_response", "raw_provider_responses"}:
                return True
            if key_text == "raw_provider_response_stored" and bool(item):
                return True
            if recursively_contains_raw_provider_response(item):
                return True
    elif isinstance(value, list):
        return any(recursively_contains_raw_provider_response(item) for item in value)
    return False


def report_indicates_prohibited_operation(*reports: dict[str, Any]) -> bool:
    prohibited_flags = (
        "publishing_performed",
        "website_pages_written",
        "public_content_files_written",
        "social_posting_performed",
        "deployment_performed",
        "notion_write_operations_performed",
        "notion_mutation_performed",
        "live_github_api_used",
        "article_body_scraping_performed",
        "knowledge_graph_write_performed",
        "prediction_engine_performed",
        "workflow_dispatched",
    )
    for report in reports:
        for flag in prohibited_flags:
            if bool(report.get(flag)):
                return True
    return False


def load_signals(llm_audit_report: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("intelligence_signals", "signals"):
        signals = llm_audit_report.get(key)
        if isinstance(signals, list) and all(isinstance(signal, dict) for signal in signals):
            return list(signals)
    raise AuditInputError("LLM audit report must contain intelligence_signals or signals list")


def load_candidates(signal_candidate_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    candidates = signal_candidate_report.get("candidates")
    if not isinstance(candidates, list) or not all(isinstance(candidate, dict) for candidate in candidates):
        raise AuditInputError("SignalCandidate report must contain candidates list")
    return {
        normalize_text(candidate.get("candidate_id")): candidate
        for candidate in candidates
        if normalize_text(candidate.get("candidate_id"))
    }


def provider_for_signal(signal: dict[str, Any], llm_audit_report: dict[str, Any]) -> str:
    provider = normalize_text(signal.get("provider") or llm_audit_report.get("provider"))
    if provider:
        return provider
    distribution = llm_audit_report.get("provider_distribution")
    if isinstance(distribution, dict) and distribution:
        return sorted(str(key) for key in distribution.keys())[0]
    return "unknown"


def prompt_version_for_signal(signal: dict[str, Any], llm_audit_report: dict[str, Any]) -> str:
    prompt_version = normalize_text(
        signal.get("prompt_version")
        or signal.get("prompt_template_version")
        or llm_audit_report.get("prompt_version")
    )
    if prompt_version:
        return prompt_version
    prompt_versions = llm_audit_report.get("prompt_versions_used")
    if isinstance(prompt_versions, dict) and prompt_versions:
        return sorted(str(key) for key in prompt_versions.keys())[0]
    prompt_template = llm_audit_report.get("prompt_template")
    if isinstance(prompt_template, dict):
        return normalize_text(prompt_template.get("template_version"))
    return ""


def source_url_for_signal(signal: dict[str, Any], candidate: dict[str, Any]) -> str:
    return normalize_text(signal.get("source_url") or candidate.get("url") or candidate.get("source_url"))


def agi_capability_for_signal(signal: dict[str, Any]) -> str:
    return normalize_text(signal.get("agi_capability") or signal.get("signal_type"))


def entities_for_signal(signal: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    return (
        normalize_list(signal.get("related_entities"))
        or normalize_list(signal.get("affected_entities"))
        or normalize_list(candidate.get("entities"))
    )


def watch_next_for_signal(signal: dict[str, Any]) -> str:
    watch_next = normalize_text(signal.get("watch_next"))
    if watch_next:
        return watch_next
    key_points = normalize_list(signal.get("key_points"))
    if len(key_points) > 1:
        return key_points[-1]
    return ""


def why_it_matters_for_signal(signal: dict[str, Any]) -> str:
    why = normalize_text(signal.get("why_it_matters"))
    if why:
        return why
    key_points = normalize_list(signal.get("key_points"))
    if key_points:
        return key_points[0]
    return ""


def signal_missing_fields(signal: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if not normalize_text(signal.get("title")):
        missing.append("title")
    if not normalize_text(signal.get("summary")):
        missing.append("summary")
    if not source_url_for_signal(signal, candidate):
        missing.append("source_url")
    if not why_it_matters_for_signal(signal):
        missing.append("why_it_matters")
    if not agi_capability_for_signal(signal):
        missing.append("agi_capability")
    if not entities_for_signal(signal, candidate):
        missing.append("related_entities")
    if signal.get("confidence") in (None, ""):
        missing.append("confidence")
    if not watch_next_for_signal(signal):
        missing.append("watch_next")
    return missing


def score_information_density(signal: dict[str, Any]) -> int:
    count = word_count(signal.get("title"), signal.get("summary"), why_it_matters_for_signal(signal))
    if count >= 70:
        return 5
    if count >= 45:
        return 4
    if count >= 28:
        return 3
    if count >= 14:
        return 2
    if count > 0:
        return 1
    return 0


def score_source_attribution(signal: dict[str, Any], candidate: dict[str, Any]) -> int:
    source_url = source_url_for_signal(signal, candidate)
    source_name = normalize_text(signal.get("source_name") or candidate.get("source_name"))
    if has_url(source_url) and source_name:
        return 5
    if has_url(source_url):
        return 4
    if source_url:
        return 2
    return 0


def score_source_authority(signal: dict[str, Any], candidate: dict[str, Any]) -> int:
    source_name = normalize_text(signal.get("source_name") or candidate.get("source_name"))
    provider = normalize_text(signal.get("provider"))
    if source_name and provider:
        return 4
    if source_name:
        return 3
    return 1 if source_url_for_signal(signal, candidate) else 0


def score_reasoning_depth(signal: dict[str, Any]) -> int:
    why = why_it_matters_for_signal(signal)
    if word_count(why) >= 35 and any(word in why.lower() for word in ("because", "therefore", "signals", "affects", "changes")):
        return 5
    if word_count(why) >= 24:
        return 4
    if word_count(why) >= 12:
        return 3
    if why:
        return 1
    return 0


def score_novelty(signal: dict[str, Any]) -> int:
    blob = lower_blob(signal)
    if any(word in blob for word in ("new", "first", "release", "launch", "milestone", "update", "shift", "change")):
        return 4
    if word_count(signal.get("title"), signal.get("summary")) >= 20:
        return 2
    return 1 if normalize_text(signal.get("summary")) else 0


def score_agi_capability(signal: dict[str, Any]) -> int:
    capability = agi_capability_for_signal(signal)
    if not capability:
        return 0
    if capability.lower() in {
        "reasoning",
        "planning",
        "memory",
        "world model",
        "agents",
        "robotics",
        "multimodal",
        "tool use",
        "ai safety",
        "compute",
        "data",
        "open source",
        "policy",
        "infrastructure",
        "evaluation",
        "alignment",
    }:
        return 5
    return 3


def score_entities(signal: dict[str, Any], candidate: dict[str, Any]) -> int:
    entity_count = len(entities_for_signal(signal, candidate))
    if entity_count >= 3:
        return 5
    if entity_count == 2:
        return 4
    if entity_count == 1:
        return 3
    return 0


def score_tracker_reuse(signal: dict[str, Any], candidate: dict[str, Any]) -> int:
    entities = entities_for_signal(signal, candidate)
    capability = agi_capability_for_signal(signal)
    if entities and capability and why_it_matters_for_signal(signal):
        return 4
    if entities and capability:
        return 3
    if entities or capability:
        return 2
    return 0


def score_actionability(signal: dict[str, Any]) -> int:
    text = " ".join((why_it_matters_for_signal(signal), watch_next_for_signal(signal))).lower()
    if any(word in text for word in ("monitor", "track", "compare", "verify", "watch", "evaluate")) and word_count(text) >= 20:
        return 5
    if any(word in text for word in ("monitor", "track", "verify", "watch")):
        return 4
    if watch_next_for_signal(signal):
        return 3
    return 0


def score_watch_next(signal: dict[str, Any]) -> int:
    watch = watch_next_for_signal(signal)
    if word_count(watch) >= 18 and any(word in watch.lower() for word in ("track", "monitor", "verify", "watch", "compare")):
        return 5
    if word_count(watch) >= 10:
        return 4
    if watch:
        return 2
    return 0


def score_prediction_value(signal: dict[str, Any]) -> int:
    text = " ".join((normalize_text(signal.get("summary")), why_it_matters_for_signal(signal), watch_next_for_signal(signal))).lower()
    if any(word in text for word in ("next", "follow-up", "benchmark", "milestone", "release", "commitment", "verify", "track")):
        return 4
    if watch_next_for_signal(signal):
        return 2
    return 0


def score_confidence_support(signal: dict[str, Any], candidate: dict[str, Any]) -> int:
    confidence = signal.get("confidence")
    if not isinstance(confidence, int | float):
        return 0
    score = 2
    if has_url(source_url_for_signal(signal, candidate)):
        score += 1
    if why_it_matters_for_signal(signal):
        score += 1
    if "uncertain" in lower_blob(signal) or "verify" in lower_blob(signal):
        score += 1
    return min(score, 5)


def score_anti_garbage(signal: dict[str, Any]) -> int:
    blob = lower_blob(signal)
    score = 5
    if contains_phrase(blob, GENERIC_PHRASES):
        score -= 2
    if contains_phrase(blob, ARTICLE_LIKE_PHRASES):
        score -= 3
    if contains_phrase(blob, SEO_LIKE_PHRASES):
        score -= 2
    if word_count(signal.get("summary")) < 8:
        score -= 1
    return max(0, score)


def score_signal(signal: dict[str, Any], candidate: dict[str, Any]) -> dict[str, int]:
    return {
        "Information Density": score_information_density(signal),
        "Source Attribution": score_source_attribution(signal, candidate),
        "Source Authority": score_source_authority(signal, candidate),
        "Reasoning Depth": score_reasoning_depth(signal),
        "Novelty": score_novelty(signal),
        "AGI Capability Relevance": score_agi_capability(signal),
        "Entity / Relationship Value": score_entities(signal, candidate),
        "Tracker Reuse Value": score_tracker_reuse(signal, candidate),
        "Actionability": score_actionability(signal),
        "Watch Next Specificity": score_watch_next(signal),
        "Prediction / Future Review Value": score_prediction_value(signal),
        "Confidence Support": score_confidence_support(signal, candidate),
        "Anti-Garbage Risk": score_anti_garbage(signal),
    }


def risk_flags_for_signal(
    signal: dict[str, Any],
    candidate: dict[str, Any],
    raw_provider_response_present: bool,
    prohibited_operation_attempted: bool,
) -> list[str]:
    flags: list[str] = []
    blob = lower_blob(signal)
    if not source_url_for_signal(signal, candidate):
        flags.append("missing_source_url")
    if not why_it_matters_for_signal(signal):
        flags.append("missing_why_it_matters")
    if not watch_next_for_signal(signal):
        flags.append("missing_watch_next")
    if not agi_capability_for_signal(signal):
        flags.append("missing_agi_capability")
    if normalize_text(signal.get("publish_status")).lower() in {"publish_ready", "published"}:
        flags.append("unsupported_publish_readiness")
    if contains_phrase(blob, ARTICLE_LIKE_PHRASES):
        flags.append("article_like_output")
    if contains_phrase(blob, GENERIC_PHRASES) or word_count(signal.get("summary")) < 8:
        flags.append("generic_summary")
    if raw_provider_response_present:
        flags.append("raw_provider_response_present")
    if prohibited_operation_attempted:
        flags.append("network_or_live_operation_attempted")
    return sorted(set(flags))


def quality_tier(total_score: int, risk_flags: list[str]) -> str:
    has_critical = bool(CRITICAL_RISK_FLAGS.intersection(risk_flags))
    if total_score >= 52 and not has_critical:
        return "Tier A: Decision-grade Signal"
    if total_score >= 40 and not has_critical:
        return "Tier B: Useful Signal"
    if total_score >= 28:
        return "Tier C: Needs Review"
    return "Tier D: Reject / Low-value"


def recommended_action_for_tier(tier: str, risk_flags: list[str]) -> str:
    if risk_flags:
        return "Fix critical risks before any publish-readiness consideration."
    if tier.startswith("Tier A"):
        return "Eligible for future human review as a publish-readiness candidate."
    if tier.startswith("Tier B"):
        return "Useful signal; validate correlation and confidence before approval."
    if tier.startswith("Tier C"):
        return "Needs stronger analysis, attribution, or capability mapping."
    return "Reject or regenerate; do not move toward publishing."


def confidence_notes(signal: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    confidence = signal.get("confidence")
    if isinstance(confidence, int | float):
        notes.append(f"model_confidence={confidence}")
    else:
        notes.append("model_confidence_missing")
    if has_url(source_url_for_signal(signal, candidate)):
        notes.append("source_url_present")
    if "verify" in lower_blob(signal) or "uncertain" in lower_blob(signal):
        notes.append("uncertainty_or_verification_language_present")
    else:
        notes.append("explicit_uncertainty_limited")
    return notes


def strengths_for_scores(scores: dict[str, int]) -> list[str]:
    return [dimension for dimension, score in scores.items() if score >= 4]


def weaknesses_for_scores(scores: dict[str, int]) -> list[str]:
    return [dimension for dimension, score in scores.items() if score <= 2]


def review_signal(
    signal: dict[str, Any],
    candidate: dict[str, Any],
    llm_audit_report: dict[str, Any],
    raw_provider_response_present: bool,
    prohibited_operation_attempted: bool,
) -> dict[str, Any]:
    scores = score_signal(signal, candidate)
    risk_flags = risk_flags_for_signal(
        signal,
        candidate,
        raw_provider_response_present=raw_provider_response_present,
        prohibited_operation_attempted=prohibited_operation_attempted,
    )
    total_score = sum(scores.values())
    tier = quality_tier(total_score, risk_flags)
    candidate_id = normalize_text(signal.get("candidate_id") or candidate.get("candidate_id"))
    return {
        "signal_id": normalize_text(signal.get("signal_id")) or candidate_id,
        "candidate_id": candidate_id,
        "title": normalize_text(signal.get("title")),
        "source_url": source_url_for_signal(signal, candidate),
        "provider": provider_for_signal(signal, llm_audit_report),
        "prompt_version": prompt_version_for_signal(signal, llm_audit_report),
        "quality_scores": scores,
        "total_score": total_score,
        "quality_tier": tier,
        "pass_publish_readiness_candidate": tier.startswith("Tier A") and not risk_flags,
        "strengths": strengths_for_scores(scores),
        "weaknesses": weaknesses_for_scores(scores),
        "missing_fields": signal_missing_fields(signal, candidate),
        "risk_flags": risk_flags,
        "confidence_notes": confidence_notes(signal, candidate),
        "recommended_action": recommended_action_for_tier(tier, risk_flags),
    }


def summarize_tiers(signal_reviews: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "Tier A: Decision-grade Signal": 0,
        "Tier B: Useful Signal": 0,
        "Tier C: Needs Review": 0,
        "Tier D: Reject / Low-value": 0,
    }
    for review in signal_reviews:
        tier = str(review.get("quality_tier"))
        counts[tier] = counts.get(tier, 0) + 1
    return counts


def build_findings(signal_reviews: list[dict[str, Any]]) -> list[str]:
    if not signal_reviews:
        return ["No IntelligenceSignals were available for review."]
    findings: list[str] = []
    risky = [review for review in signal_reviews if review.get("risk_flags")]
    tier_counts = summarize_tiers(signal_reviews)
    findings.append(f"Reviewed {len(signal_reviews)} IntelligenceSignals against Signal Quality Framework V1.")
    findings.append(
        "Tier distribution: "
        + ", ".join(f"{tier}={count}" for tier, count in tier_counts.items())
    )
    if risky:
        findings.append(f"{len(risky)} signals contain risk flags requiring review before publish readiness.")
    else:
        findings.append("No critical risk flags were detected by the deterministic V1 audit.")
    return findings


def recommended_next_actions(signal_reviews: list[dict[str, Any]]) -> list[str]:
    actions = [
        "Review Tier C and Tier D outputs before expanding real-provider usage.",
        "Use audit results to design SignalQualityScore V1 integration.",
        "Do not proceed to publishing until human approval and publish-readiness gates exist.",
    ]
    if any(review.get("risk_flags") for review in signal_reviews):
        actions.insert(0, "Fix or regenerate signals with critical risk flags.")
    return actions


def run_audit(
    llm_audit_report_path: str | pathlib.Path,
    signal_candidate_report_path: str | pathlib.Path,
    pipeline_report_path: str | pathlib.Path,
    output_path: str | pathlib.Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    llm_audit_report = read_json_object(llm_audit_report_path, "LLM audit report")
    signal_candidate_report = read_json_object(signal_candidate_report_path, "SignalCandidate report")
    pipeline_report = read_json_object(pipeline_report_path, "Pipeline report")

    signals = load_signals(llm_audit_report)
    candidates = load_candidates(signal_candidate_report)
    raw_provider_response_present = any(
        recursively_contains_raw_provider_response(report)
        for report in (llm_audit_report, signal_candidate_report, pipeline_report)
    )
    prohibited_operation_attempted = report_indicates_prohibited_operation(
        llm_audit_report,
        signal_candidate_report,
        pipeline_report,
    )

    signal_reviews = [
        review_signal(
            signal,
            candidates.get(normalize_text(signal.get("candidate_id")), {}),
            llm_audit_report,
            raw_provider_response_present=raw_provider_response_present,
            prohibited_operation_attempted=prohibited_operation_attempted,
        )
        for signal in signals
        if isinstance(signal, dict)
    ]
    report = {
        "audit_version": AUDIT_VERSION,
        "created_at": created_at or utc_now(),
        "input_paths": {
            "llm_audit_report": str(llm_audit_report_path),
            "signal_candidate_report": str(signal_candidate_report_path),
            "pipeline_report": str(pipeline_report_path),
        },
        "signals_reviewed": len(signal_reviews),
        "framework_reference": FRAMEWORK_REFERENCE,
        "milestone_reference": MILESTONE_REFERENCE,
        "quality_dimensions": list(QUALITY_DIMENSIONS),
        "signal_reviews": signal_reviews,
        "tier_counts": summarize_tiers(signal_reviews),
        "findings": build_findings(signal_reviews),
        "recommended_next_actions": recommended_next_actions(signal_reviews),
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
    parser = argparse.ArgumentParser(description="Run DysonX OpenAI Output Quality Audit V1.")
    parser.add_argument("--llm-audit-report", required=True, help="Path to existing LLM audit report JSON.")
    parser.add_argument("--signal-candidate-report", required=True, help="Path to existing SignalCandidate report JSON.")
    parser.add_argument("--pipeline-report", required=True, help="Path to existing final pipeline report JSON.")
    parser.add_argument("--output", required=True, help="Path to write output quality audit report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_audit(
            llm_audit_report_path=args.llm_audit_report,
            signal_candidate_report_path=args.signal_candidate_report,
            pipeline_report_path=args.pipeline_report,
            output_path=args.output,
        )
    except AuditInputError as exc:
        print(f"[openai-output-quality-audit] failed: {exc}")
        return 1

    print(
        "[openai-output-quality-audit] wrote report: "
        f"{args.output} signals_reviewed={report['signals_reviewed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
