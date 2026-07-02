#!/usr/bin/env python3
"""Reusable topic policy for DysonX Public Signals."""

from __future__ import annotations

from typing import Any


CORE_PUBLIC_TOPIC_TERMS = (
    "agentic workflow",
    "agentic workflows",
    "agi governance",
    "agi safety",
    "ai agent",
    "ai agents",
    "ai governance",
    "ai infrastructure",
    "ai regulation",
    "ai safety",
    "autonomous ai agent",
    "autonomous ai agents",
    "benchmark",
    "benchmarks",
    "code agent",
    "code agents",
    "coding agent",
    "coding agents",
    "developer tool",
    "developer tools",
    "formal verification",
    "frontier model",
    "frontier models",
    "frontier model operations",
    "llm agent",
    "llm agents",
    "llm judge",
    "llm judges",
    "model evaluation",
    "model evaluations",
)

DOMAIN_RISK_GROUPS = {
    "child_online_safety": ("child online safety", "online safety", "social media ban", "social media bans"),
    "medical": (
        "biomedical",
        "cancer",
        "clinical",
        "drug",
        "drug drug interaction",
        "drug-drug interaction",
        "healthcare diagnosis",
        "laparoscopic",
        "medical",
        "medical imaging",
        "medicine",
        "prostate",
        "surgical",
        "ultrasound",
    ),
    "biological_lab": ("biology", "lab agent", "lab agents", "laboratory agent", "laboratory agents"),
    "legal": ("law", "legal deliberation", "legal domain", "legal-domain"),
    "agriculture": ("agriculture", "agricultural", "cattle", "dairy", "methane"),
    "oceanography": ("oceanography",),
    "poetry": ("eclipse", "eclipses", "poetry"),
    "generic_news": ("electoral politics", "general news", "general science", "generic policy news", "politics"),
    "household_robotics": ("robot vacuum", "vacuum cleaner"),
    "generic_robotics": ("generic indoor robotics", "household robotics", "indoor robotics"),
}

DOMAIN_RISK_CLEAR_FRAMING_TERMS = (
    "agent audit",
    "agent transparency",
    "agi governance",
    "agi safety",
    "ai agent governance",
    "ai governance",
    "ai regulation",
    "ai safety",
    "ai safety evaluation",
    "autonomous capability tracking",
    "embodied ai",
    "formal verification of ai behavior",
    "foundation model",
    "frontier ai safety",
    "frontier model evaluation",
    "frontier model governance",
    "frontier model safety",
    "model evaluation",
    "multi-agent planning",
    "vla capability evaluation",
)

MULTI_AGENT_TERMS = ("multi-agent", "multi agent")
MULTI_AGENT_CONTEXT_TERMS = ("ai", "agent", "capability", "safety", "evaluation", "governance", "coordination", "planning")
AGENT_CONTEXT_TERMS = ("audit", "capability", "control", "evaluation", "governance", "reliability", "safety", "transparency", "workflow")
AUTONOMY_TERMS = ("autonomy", "autonomous systems")
AUTONOMY_CONTEXT_TERMS = ("ai", "agent", "capability", "safety", "evaluation", "control")
VLA_TERMS = ("vla", "vision-language-action", "vision language action")
VLA_CONTEXT_TERMS = (
    "agent capability",
    "embodied agent",
    "embodied ai",
    "foundation model",
    "robotics agent",
    "robotics foundation model",
)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def field(record: dict[str, Any], *names: str) -> Any:
    lowered = {key.lower(): value for key, value in record.items()}
    for name in names:
        if name in record:
            return record[name]
        value = lowered.get(name.lower())
        if value is not None:
            return value
    return None


def topic_haystack(record: dict[str, Any]) -> str:
    values = [
        field(record, "Signal Title", "Title", "Name", "signal_title", "title"),
        field(record, "Summary", "Public Summary", "summary"),
        field(record, "Why This Matters", "why_this_matters"),
        field(record, "Risk Notes", "Safety Notes", "risk_notes"),
        field(record, "Watch Next", "watch_next"),
        field(record, "Category", "Categories", "Tag", "Tags", "tags"),
        field(record, "Source Label", "Source Name", "Source", "source_label", "source_name"),
        field(record, "AGI Relevance", "agi_relevance"),
    ]
    flattened: list[str] = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(normalize_text(item) for item in value)
        else:
            flattened.append(normalize_text(value))
    return " ".join(flattened).lower()


def matched_terms(haystack: str, terms: tuple[str, ...]) -> list[str]:
    return [term for term in terms if term in haystack]


def core_topic_matches(haystack: str) -> list[str]:
    matches = matched_terms(haystack, CORE_PUBLIC_TOPIC_TERMS)
    if "agent" in haystack and any(term in haystack for term in AGENT_CONTEXT_TERMS):
        matches.append("agent_context")
    if any(term in haystack for term in MULTI_AGENT_TERMS) and any(term in haystack for term in MULTI_AGENT_CONTEXT_TERMS):
        matches.append("multi_agent_context")
    if any(term in haystack for term in AUTONOMY_TERMS) and any(term in haystack for term in AUTONOMY_CONTEXT_TERMS):
        matches.append("autonomy_context")
    if any(term in haystack for term in VLA_TERMS) and any(term in haystack for term in VLA_CONTEXT_TERMS):
        matches.append("vla_context")
    return sorted(set(matches))


def domain_risk_matches(haystack: str) -> dict[str, list[str]]:
    return {
        group: matched
        for group, terms in DOMAIN_RISK_GROUPS.items()
        if (matched := matched_terms(haystack, terms))
    }


def public_topic_decision(record: dict[str, Any]) -> dict[str, Any]:
    haystack = topic_haystack(record)
    core_matches = core_topic_matches(haystack)
    risk_matches = domain_risk_matches(haystack)
    clear_framing = matched_terms(haystack, DOMAIN_RISK_CLEAR_FRAMING_TERMS)
    has_core = bool(core_matches)
    has_domain_risk = bool(risk_matches)
    allowed_domain_risk = has_domain_risk and has_core and bool(clear_framing)
    off_topic = has_domain_risk and not allowed_domain_risk
    reasons: list[str] = []
    if off_topic:
        reasons.append("off_topic_public_signal")
    if not has_core:
        reasons.append("missing_core_public_topic")
    return {
        "has_core_public_topic": has_core,
        "domain_risk_detected": has_domain_risk,
        "allowed_domain_risk": allowed_domain_risk,
        "off_topic_public_signal": off_topic,
        "matched_core_topics": core_matches,
        "matched_domain_risks": risk_matches,
        "matched_domain_risk_framing": sorted(set(clear_framing)),
        "reasons": reasons,
    }


def off_topic_public_signal(record: dict[str, Any]) -> bool:
    return bool(public_topic_decision(record)["off_topic_public_signal"])


def has_core_public_topic(record: dict[str, Any]) -> bool:
    return bool(public_topic_decision(record)["has_core_public_topic"])
