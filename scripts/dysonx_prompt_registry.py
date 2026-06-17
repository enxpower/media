#!/usr/bin/env python3
"""DysonX versioned prompt registry V1."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplateV1:
    template_id: str
    template_version: str
    purpose: str
    template_text: str


_PROMPT_TEMPLATES: dict[tuple[str, str], PromptTemplateV1] = {
    (
        "intelligence_signal_extraction",
        "v1",
    ): PromptTemplateV1(
        template_id="intelligence_signal_extraction",
        template_version="v1",
        purpose="Transform one SignalCandidate into structured IntelligenceSignal fields.",
        template_text=(
            "Analyze the SignalCandidate as DysonX intelligence extraction. "
            "Return structured fields: title, signal_type, importance, confidence, "
            "summary, key_points, affected_entities, impact_horizon, and tags. "
            "Do not write an article. Do not publish."
        ),
    )
}


def get_prompt_template(template_id: str, template_version: str) -> PromptTemplateV1:
    key = (template_id, template_version)
    if key not in _PROMPT_TEMPLATES:
        raise KeyError(f"Unknown prompt template: {template_id}@{template_version}")
    return _PROMPT_TEMPLATES[key]


def list_prompt_templates() -> tuple[PromptTemplateV1, ...]:
    return tuple(_PROMPT_TEMPLATES.values())
