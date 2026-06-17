#!/usr/bin/env python3
"""Lightweight DysonX Signal Engine V1 schema definitions.

This module defines schema-level data objects only. It does not connect to
Notion, collect sources, call LLM APIs, publish pages, or post to social media.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar, Literal


SchemaEntity = Literal[
    "Source",
    "RawItem",
    "LLMAnalysisJob",
    "SignalCandidate",
    "Signal",
    "QualityReview",
    "PublishJob",
    "SocialDraft",
]


V1_SCHEMA_ENTITIES: tuple[SchemaEntity, ...] = (
    "Source",
    "RawItem",
    "LLMAnalysisJob",
    "SignalCandidate",
    "Signal",
    "QualityReview",
    "PublishJob",
    "SocialDraft",
)


OUT_OF_SCOPE_SCHEMA_ENTITIES: frozenset[str] = frozenset(
    {
        "Entity",
        "EntityRelationship",
        "Topic",
        "Tracker",
        "Prediction",
        "Report",
        "Account",
        "Organization",
        "Tenant",
        "Subscription",
        "Invoice",
        "ApiKey",
        "Dashboard",
    }
)


@dataclass(frozen=True)
class Source:
    id: str
    notion_page_id: str
    name: str
    source_type: str
    url: str
    authority_score: float
    enabled: bool
    platform: str | None = None
    feed_url: str | None = None
    language: str = "English"
    region: str | None = None
    priority: str = "Medium"
    notes: str | None = None


@dataclass(frozen=True)
class RawItem:
    id: str
    source_id: str
    original_url: str
    raw_title: str
    fetched_at: datetime
    content_hash: str
    fetch_status: str
    canonical_url: str | None = None
    raw_content: str | None = None
    raw_excerpt: str | None = None
    raw_author: str | None = None
    raw_published_at: datetime | None = None
    detected_language: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class LLMAnalysisJob:
    id: str
    raw_item_id: str
    provider: str
    model_name: str
    prompt_version: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    output_json: dict[str, Any] = field(default_factory=dict)
    validation_errors_json: list[str] = field(default_factory=list)
    confidence_score: float | None = None
    error: str | None = None


@dataclass(frozen=True)
class SignalCandidate:
    id: str
    raw_item_id: str
    llm_analysis_job_id: str
    suggested_title_en: str
    summary_en: str
    source_authority_score: float
    confidence_score: float
    agi_impact_score: float
    suggested_publish_status: str
    review_status: str
    suggested_title_zh: str | None = None
    suggested_slug: str | None = None
    summary_zh: str | None = None
    market_impact_score: float | None = None
    technical_impact_score: float | None = None
    affected_capabilities: tuple[str, ...] = ()
    related_entities: tuple[str, ...] = ()
    dysonx_take_en: str | None = None
    dysonx_take_zh: str | None = None
    watch_next_en: str | None = None
    watch_next_zh: str | None = None
    duplicate_group_id: str | None = None
    reviewer_notes: str | None = None


@dataclass(frozen=True)
class Signal:
    id: str
    signal_candidate_id: str
    signal_id: str
    title_en: str
    slug: str
    summary_en: str
    original_source_url: str
    source_id: str
    source_type: str
    source_authority_score: float
    confidence_score: float
    agi_impact_score: float
    publish_status: str
    title_zh: str | None = None
    summary_zh: str | None = None
    market_impact_score: float | None = None
    technical_impact_score: float | None = None
    affected_capabilities: tuple[str, ...] = ()
    related_entities: tuple[str, ...] = ()
    dysonx_take_en: str | None = None
    dysonx_take_zh: str | None = None
    watch_next_en: str | None = None
    watch_next_zh: str | None = None
    duplicate_group_id: str | None = None
    published_at: datetime | None = None


@dataclass(frozen=True)
class QualityReview:
    id: str
    signal_candidate_id: str
    status: str
    has_source_attribution: bool
    has_llm_summary: bool
    has_authority_score: bool
    has_confidence_score: bool
    has_agi_impact_score: bool
    duplicate_checked: bool
    has_english_version: bool
    has_social_draft: bool
    unsupported_claims_flag: bool
    copied_text_flag: bool
    signal_id: str | None = None
    has_entity_candidates: bool = False
    has_seo_metadata: bool = False
    decision_value_score: float | None = None
    reviewer_notes: str | None = None
    reviewed_at: datetime | None = None


@dataclass(frozen=True)
class PublishJob:
    id: str
    signal_id: str
    target: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    output_path: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class SocialDraft:
    DRAFT_ONLY_STATUSES: ClassVar[frozenset[str]] = frozenset({"draft", "approved", "rejected"})

    id: str
    signal_id: str
    platform: str
    language: str
    draft_text: str
    status: str
    generated_by_llm_job_id: str | None = None
    reviewer_notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.status not in self.DRAFT_ONLY_STATUSES:
            allowed = ", ".join(sorted(self.DRAFT_ONLY_STATUSES))
            raise ValueError(f"SocialDraft status must be draft-only: {allowed}")


def v1_schema_entity_names() -> tuple[str, ...]:
    return tuple(V1_SCHEMA_ENTITIES)


def out_of_scope_schema_entity_names() -> frozenset[str]:
    return OUT_OF_SCOPE_SCHEMA_ENTITIES
