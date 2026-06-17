#!/usr/bin/env python3
"""DysonX LLM output validation V1."""

from __future__ import annotations

from typing import Any


REQUIRED_INTELLIGENCE_FIELDS: tuple[str, ...] = (
    "title",
    "signal_type",
    "importance",
    "confidence",
    "summary",
    "key_points",
    "affected_entities",
    "impact_horizon",
    "tags",
)

VALID_IMPORTANCE_VALUES: frozenset[str] = frozenset({"low", "medium", "high"})

VALIDATION_RULES: tuple[str, ...] = (
    "required fields present",
    "confidence within range",
    "importance value valid",
    "summary not empty",
)


def validate_intelligence_output(output: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
    warnings: list[str] = []

    for field_name in REQUIRED_INTELLIGENCE_FIELDS:
        if field_name not in output:
            warnings.append(f"{field_name} is required")

    confidence = output.get("confidence")
    if not isinstance(confidence, int | float) or confidence < 0 or confidence > 1:
        warnings.append("confidence must be a number from 0 to 1")

    importance = output.get("importance")
    if importance not in VALID_IMPORTANCE_VALUES:
        allowed = ", ".join(sorted(VALID_IMPORTANCE_VALUES))
        warnings.append(f"importance must be one of: {allowed}")

    summary = output.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        warnings.append("summary must be present")

    return len(warnings) == 0, tuple(warnings)
