# DysonX Signal Engine V1 Schema

Status: V1 schema foundation only

This document defines the first implementation boundary for the DysonX Signal Engine V1. It is not a database migration, Notion integration, collector implementation, LLM integration, publishing system, or deployment change.

## Scope

V1 schema foundation includes only these entities:

- Source
- RawItem
- LLMAnalysisJob
- SignalCandidate
- Signal
- QualityReview
- PublishJob
- SocialDraft

V1 schema foundation explicitly excludes:

- Knowledge Graph tables
- Entity relationship tables
- Prediction Engine tables
- Subscription, billing, dashboard, enterprise, API marketplace, and multi-tenant tables
- Notion API connection
- Collector execution
- LLM API calls
- Page publishing
- Social platform posting

## Layer Separation

The schema keeps the first Signal Engine path explicit:

`Source -> RawItem -> LLMAnalysisJob -> SignalCandidate -> QualityReview -> Signal -> PublishJob -> SocialDraft`

The boundaries are intentional:

- `RawItem` is collected evidence, not a published Signal.
- `LLMAnalysisJob` records model interpretation output, not editorial approval.
- `SignalCandidate` is a proposed Signal, not a published Signal.
- `Signal` is the approved Signal object.
- `SocialDraft` is review-only text and does not represent platform posting.

## Entity Definitions

### Source

Represents a monitored source configured outside runtime code. In V1, this mirrors the minimum shape needed for a future Notion-managed source sync.

Required fields:

- `id`
- `notion_page_id`
- `name`
- `source_type`
- `url`
- `authority_score`
- `enabled`

Optional fields:

- `platform`
- `feed_url`
- `language`
- `region`
- `priority`
- `notes`

### RawItem

Represents raw collected evidence from a Source.

Required fields:

- `id`
- `source_id`
- `original_url`
- `raw_title`
- `fetched_at`
- `content_hash`
- `fetch_status`

Optional fields:

- `canonical_url`
- `raw_content`
- `raw_excerpt`
- `raw_author`
- `raw_published_at`
- `detected_language`
- `error`

### LLMAnalysisJob

Represents a versioned LLM analysis attempt for a RawItem.

Required fields:

- `id`
- `raw_item_id`
- `provider`
- `model_name`
- `prompt_version`
- `status`
- `started_at`

Optional fields:

- `completed_at`
- `output_json`
- `validation_errors_json`
- `confidence_score`
- `error`

### SignalCandidate

Represents a structured Signal proposal created from an LLMAnalysisJob.

Required fields:

- `id`
- `raw_item_id`
- `llm_analysis_job_id`
- `suggested_title_en`
- `summary_en`
- `source_authority_score`
- `confidence_score`
- `agi_impact_score`
- `suggested_publish_status`
- `review_status`

Optional fields:

- `suggested_title_zh`
- `suggested_slug`
- `summary_zh`
- `market_impact_score`
- `technical_impact_score`
- `affected_capabilities`
- `related_entities`
- `dysonx_take_en`
- `dysonx_take_zh`
- `watch_next_en`
- `watch_next_zh`
- `duplicate_group_id`
- `reviewer_notes`

### Signal

Represents an approved Signal. It is separate from both raw evidence and SignalCandidate review state.

Required fields:

- `id`
- `signal_candidate_id`
- `signal_id`
- `title_en`
- `slug`
- `summary_en`
- `original_source_url`
- `source_id`
- `source_type`
- `source_authority_score`
- `confidence_score`
- `agi_impact_score`
- `publish_status`

Optional fields:

- `title_zh`
- `summary_zh`
- `market_impact_score`
- `technical_impact_score`
- `affected_capabilities`
- `related_entities`
- `dysonx_take_en`
- `dysonx_take_zh`
- `watch_next_en`
- `watch_next_zh`
- `duplicate_group_id`
- `published_at`

### QualityReview

Represents the quality gate result for a SignalCandidate or Signal.

Required fields:

- `id`
- `signal_candidate_id`
- `status`
- `has_source_attribution`
- `has_llm_summary`
- `has_authority_score`
- `has_confidence_score`
- `has_agi_impact_score`
- `duplicate_checked`
- `has_english_version`
- `has_social_draft`
- `unsupported_claims_flag`
- `copied_text_flag`

Optional fields:

- `signal_id`
- `has_entity_candidates`
- `has_seo_metadata`
- `decision_value_score`
- `reviewer_notes`
- `reviewed_at`

### PublishJob

Represents a publish workflow attempt for an approved Signal.

Required fields:

- `id`
- `signal_id`
- `target`
- `status`
- `started_at`

Optional fields:

- `completed_at`
- `output_path`
- `error`

### SocialDraft

Represents a generated draft for later human review. It is not a posted social update.

Required fields:

- `id`
- `signal_id`
- `platform`
- `language`
- `draft_text`
- `status`

Optional fields:

- `generated_by_llm_job_id`
- `reviewer_notes`
- `created_at`
- `updated_at`

V1 status values should include `draft`, `approved`, and `rejected`. V1 must not include `posted` because platform posting is out of scope.

## V1 Non-Goals

The following tables or models must not be introduced in this V1 schema foundation:

- Entity
- EntityRelationship
- Topic
- Tracker
- Prediction
- Report
- Account
- Organization
- Tenant
- Subscription
- Invoice
- ApiKey
- Dashboard

Entity names may appear only as candidate strings inside `SignalCandidate.related_entities` or `Signal.related_entities`. That is not a Knowledge Graph implementation.

## Validation Expectations

Tests should verify:

- RawItem is separate from Signal.
- LLMAnalysisJob is separate from SignalCandidate.
- SignalCandidate is separate from Signal.
- SocialDraft remains draft-only.
- No Knowledge Graph, prediction, billing, subscription, API platform, dashboard, enterprise, or multi-tenant schema classes are implemented in V1.
