#!/usr/bin/env python3
"""DysonX Quality Review Gate V1."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


VALID_IMPORTANCE_VALUES = frozenset({"low", "medium", "high"})
QUALITY_GATE_VERSION = "dysonx-quality-review-v1"


@dataclass(frozen=True)
class QualityReviewV1:
    review_id: str
    signal_id: str
    ranking_id: str
    status: str
    decision: str
    reasons: tuple[str, ...]
    required_fields_checked: tuple[str, ...]
    failed_checks: tuple[str, ...]
    reviewer_type: str
    created_at: str


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:16]}"


def has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def warnings_for_ranked_signal(ranked_signal: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    signal = ranked_signal.get("signal", {})
    score = ranked_signal.get("score", {})

    for source in (signal, score, ranked_signal):
        raw_warnings = source.get("warnings")
        if isinstance(raw_warnings, list):
            warnings.extend(str(warning).lower() for warning in raw_warnings)

    return warnings


def review_ranked_signal(
    ranked_signal: dict[str, Any],
    ranking_id: str,
    created_at: str | None = None,
) -> QualityReviewV1:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    signal = ranked_signal.get("signal", {})
    score = ranked_signal.get("score", {})

    signal_id = str(signal.get("signal_id") or score.get("signal_id") or "unknown_signal")
    confidence_score = score.get("confidence_score", signal.get("confidence"))
    composite_score = score.get("composite_score")
    importance = str(signal.get("importance", "")).lower()
    warnings = warnings_for_ranked_signal(ranked_signal)

    required_fields = (
        "source_id",
        "source_name",
        "title",
        "summary",
        "confidence_score",
        "composite_score",
        "importance",
    )

    failed_checks: list[str] = []
    reasons: list[str] = []

    if not has_text(signal.get("source_id")):
        failed_checks.append("source_id")
        reasons.append("missing source attribution")
    if not has_text(signal.get("source_name")):
        failed_checks.append("source_name")
        reasons.append("missing source attribution")
    if not has_text(signal.get("title")):
        failed_checks.append("title")
        reasons.append("missing title")
    if not has_text(signal.get("summary")):
        failed_checks.append("summary")
        reasons.append("missing summary")

    if not isinstance(confidence_score, int | float):
        failed_checks.append("confidence_score")
        reasons.append("confidence score missing or invalid")
        confidence_value = 0.0
    else:
        confidence_value = float(confidence_score)

    if not isinstance(composite_score, int | float):
        failed_checks.append("composite_score")
        reasons.append("composite score missing or invalid")
        composite_value = 0.0
    else:
        composite_value = float(composite_score)

    if importance not in VALID_IMPORTANCE_VALUES:
        failed_checks.append("importance")
        reasons.append("importance missing or invalid")

    validation_failed = any("validation failed" in warning for warning in warnings)
    unsupported_claim = any("unsupported_claim" in warning or "unsupported claim" in warning for warning in warnings)
    duplicate_warning = any("duplicate" in warning for warning in warnings)
    duplicate_fatal = any("duplicate fatal" in warning or "fatal duplicate" in warning for warning in warnings)

    if validation_failed:
        failed_checks.append("validation")
        reasons.append("validation failed")
    if unsupported_claim:
        failed_checks.append("unsupported_claim")
        reasons.append("unsupported claim warning")
    if duplicate_warning:
        reasons.append("duplicate warning")
    if duplicate_fatal:
        failed_checks.append("duplicate")
        reasons.append("duplicate warning is fatal")

    fatal_failure = (
        "source_id" in failed_checks
        or "source_name" in failed_checks
        or "summary" in failed_checks
        or confidence_value < 0.50
        or composite_value < 0.50
        or validation_failed
        or duplicate_fatal
    )

    if confidence_value < 0.50:
        reasons.append("confidence below rejection threshold")
    if composite_value < 0.50:
        reasons.append("composite score below rejection threshold")

    if fatal_failure:
        status = "rejected"
        decision = "rejected"
    elif confidence_value >= 0.70 and composite_value >= 0.70 and not unsupported_claim and not duplicate_warning:
        status = "publish_ready"
        decision = "publish_ready"
        reasons.append("passed deterministic publish readiness checks")
    else:
        status = "needs_review"
        decision = "needs_review"
        if 0.50 <= confidence_value < 0.70:
            reasons.append("confidence requires manual review")
        if 0.50 <= composite_value < 0.70:
            reasons.append("composite score requires manual review")
        if unsupported_claim or duplicate_warning:
            reasons.append("non-fatal warning requires manual review")
        if not reasons:
            reasons.append("important fields present but weak")

    return QualityReviewV1(
        review_id=stable_id("quality_review", ranking_id, signal_id, timestamp),
        signal_id=signal_id,
        ranking_id=ranking_id,
        status=status,
        decision=decision,
        reasons=tuple(dict.fromkeys(reasons)),
        required_fields_checked=required_fields,
        failed_checks=tuple(dict.fromkeys(failed_checks)),
        reviewer_type="deterministic_v1",
        created_at=timestamp,
    )


def serialize_review(review: QualityReviewV1) -> dict[str, Any]:
    data = asdict(review)
    data["reasons"] = list(review.reasons)
    data["required_fields_checked"] = list(review.required_fields_checked)
    data["failed_checks"] = list(review.failed_checks)
    return data
