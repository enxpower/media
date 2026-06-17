#!/usr/bin/env python3
"""DysonX Signal Scoring Engine V1."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


SCORING_VERSION = "dysonx-signal-score-v1"

SCORING_WEIGHTS: dict[str, float] = {
    "importance_score": 0.30,
    "authority_score": 0.25,
    "impact_score": 0.20,
    "confidence_score": 0.15,
    "freshness_score": 0.10,
}

IMPORTANCE_VALUES: dict[str, float] = {
    "high": 1.0,
    "medium": 0.65,
    "low": 0.3,
}

SIGNAL_TYPE_IMPACT_VALUES: dict[str, float] = {
    "model_release": 0.9,
    "regulation": 0.9,
    "research_update": 0.75,
    "company_announcement": 0.65,
    "general_signal": 0.4,
}

HIGH_AUTHORITY_SOURCES = (
    "openai",
    "anthropic",
    "deepmind",
    "ai office",
    "government",
    "research",
)


@dataclass(frozen=True)
class SignalScoreV1:
    signal_id: str
    importance_score: float
    confidence_score: float
    authority_score: float
    freshness_score: float
    impact_score: float
    composite_score: float
    scoring_version: str
    scoring_reasons: tuple[str, ...]
    created_at: str


def clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def score_importance(signal: dict[str, Any]) -> tuple[float, str]:
    importance = str(signal.get("importance", "")).lower()
    if importance in IMPORTANCE_VALUES:
        return IMPORTANCE_VALUES[importance], f"importance={importance}"
    return 0.0, "importance missing or invalid"


def score_confidence(signal: dict[str, Any]) -> tuple[float, str]:
    confidence = signal.get("confidence")
    if isinstance(confidence, int | float):
        score = clamp_score(float(confidence))
        return score, f"confidence={score:.2f}"
    return 0.0, "confidence missing or invalid"


def score_authority(signal: dict[str, Any]) -> tuple[float, str]:
    source_text = f"{signal.get('source_id', '')} {signal.get('source_name', '')}".lower()
    if any(source in source_text for source in HIGH_AUTHORITY_SOURCES):
        return 0.9, "high-authority first-source pattern"
    if source_text.strip():
        return 0.55, "known source without high-authority pattern"
    return 0.0, "source missing"


def score_impact(signal: dict[str, Any]) -> tuple[float, str]:
    signal_type = str(signal.get("signal_type", "")).lower()
    base = SIGNAL_TYPE_IMPACT_VALUES.get(signal_type, 0.35)
    entities = signal.get("affected_entities")
    entity_bonus = 0.05 if isinstance(entities, list | tuple) and len(entities) > 0 else 0.0
    score = clamp_score(base + entity_bonus)
    return score, f"impact={signal_type or 'unknown'}"


def score_freshness(signal: dict[str, Any], reference_time: datetime | None) -> tuple[float, str]:
    created_at = parse_timestamp(signal.get("created_at"))
    if created_at is None or reference_time is None:
        return 0.5, "freshness timestamp missing or invalid"

    age_days = max(0.0, (reference_time - created_at).total_seconds() / 86400)
    if age_days <= 1:
        return 1.0, "freshness<=1d"
    if age_days <= 7:
        return 0.75, "freshness<=7d"
    if age_days <= 30:
        return 0.5, "freshness<=30d"
    return 0.2, "freshness>30d"


def calculate_composite_score(
    importance_score: float,
    authority_score: float,
    impact_score: float,
    confidence_score: float,
    freshness_score: float,
) -> float:
    composite = (
        importance_score * SCORING_WEIGHTS["importance_score"]
        + authority_score * SCORING_WEIGHTS["authority_score"]
        + impact_score * SCORING_WEIGHTS["impact_score"]
        + confidence_score * SCORING_WEIGHTS["confidence_score"]
        + freshness_score * SCORING_WEIGHTS["freshness_score"]
    )
    return round(composite, 4)


def score_signal(signal: dict[str, Any], reference_time: datetime | None = None, created_at: str | None = None) -> SignalScoreV1:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    signal_id = str(signal.get("signal_id") or "unknown_signal")

    importance_score, importance_reason = score_importance(signal)
    confidence_score, confidence_reason = score_confidence(signal)
    authority_score, authority_reason = score_authority(signal)
    freshness_score, freshness_reason = score_freshness(signal, reference_time)
    impact_score, impact_reason = score_impact(signal)
    composite_score = calculate_composite_score(
        importance_score=importance_score,
        authority_score=authority_score,
        impact_score=impact_score,
        confidence_score=confidence_score,
        freshness_score=freshness_score,
    )

    return SignalScoreV1(
        signal_id=signal_id,
        importance_score=importance_score,
        confidence_score=confidence_score,
        authority_score=authority_score,
        freshness_score=freshness_score,
        impact_score=impact_score,
        composite_score=composite_score,
        scoring_version=SCORING_VERSION,
        scoring_reasons=(
            importance_reason,
            authority_reason,
            impact_reason,
            confidence_reason,
            freshness_reason,
        ),
        created_at=timestamp,
    )


def serialize_score(score: SignalScoreV1) -> dict[str, Any]:
    data = asdict(score)
    data["scoring_reasons"] = list(score.scoring_reasons)
    return data
