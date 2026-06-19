# DysonX Signal Engine V1 Implementation Plan

Status: proposed planning document only

This document defines a limited V1 implementation plan for the DysonX Signal Engine. It does not implement production code, migrations, deployment, or live data changes.

## Governance Alignment

This plan follows the DysonX governing documents:

- DysonX remains an AI / AGI Intelligence OS focused on intelligence value, not commodity news publishing.
- Signal remains the primary content object.
- Monitored sources are managed in Notion, not permanently hardcoded.
- Raw collection is followed by LLM analysis as the first major interpretation step.
- English is canonical; Chinese is a localization layer.
- V1 prepares for, but does not implement, the full Knowledge Graph.
- V1 does not include prediction, enterprise, billing, subscriptions, marketplace, multi-tenant architecture, or advanced analytics.

## V1 Scope

Included:

- Notion-managed source database
- Source collector framework
- Raw source storage
- LLM analysis pipeline
- Signal schema
- Signal publishing workflow
- Signal page template
- Social post draft generation

Not included:

- Knowledge Graph implementation
- Prediction Engine
- Enterprise Features
- Subscription System
- Billing
- API Marketplace
- Multi-tenant Architecture
- Advanced Analytics

## Proposed V1 Architecture

V1 should be implemented as separable layers that match the canonical flow:

`Notion Sources -> Collectors -> Raw Items -> Normalization -> LLM Analysis -> Signal Candidate -> Quality Gate -> Published Signal -> Social Drafts`

### 1. Source Configuration Layer

Notion is the source of truth for monitored sources. The application syncs enabled source records into a local cache table for repeatable collector runs.

Responsibilities:

- Read source records from Notion.
- Validate required fields.
- Cache source configuration locally.
- Track sync status, errors, and timestamps.

V1 constraint:

- No permanent monitored source list may live in application code.
- Small test fixtures may exist only under tests.

### 2. Collection Layer

Collectors fetch raw content from configured sources without deciding publish value.

Initial V1 collector types:

- RSS feed collector
- Web page collector
- GitHub release/repository collector
- Manual URL collector

Deferred collector types:

- Social account collectors
- Government API collectors
- arXiv or paper API collector
- Conference/keynote collector

### 3. Raw Data Layer

Raw items are stored separately from Signals. Raw content is evidence and must remain available for audit.

Responsibilities:

- Store original URL, source ID, raw title, raw content/excerpt, author, published time, fetched time, content hash, fetch status, and errors.
- Prevent duplicate raw item creation through canonical URL and content hash checks.
- Preserve raw data even if LLM analysis later rejects publication.

### 4. Normalization Layer

Normalization prepares raw items for LLM analysis.

Responsibilities:

- Canonicalize URLs.
- Extract readable text.
- Remove obvious boilerplate.
- Normalize timestamps.
- Detect language.
- Compute content hash.
- Preserve attribution.

V1 constraint:

- Normalization must not rewrite raw items into publishable articles.

### 5. LLM Intelligence Layer

LLM analysis is the first major interpretation step after raw collection and normalization.

Required V1 analysis output:

- Summary
- Topic classification
- Entity candidates
- Event candidates
- AGI capability mapping
- Importance score
- Source authority reasoning
- Confidence score
- Duplicate hints
- Suggested Signal title
- Suggested DysonX Take
- Watch Next
- Suggested publish status
- Social post draft suggestions

All LLM runs should store:

- Provider
- Model name
- Prompt version
- Input raw item ID
- Request timestamp
- Response timestamp
- Parsed JSON output
- Parse/validation status
- Error state

### 6. Deduplication and Authority Layer

V1 deduplication should prevent obvious duplicate Signals while staying simple.

Signals may be grouped by:

- Canonical URL
- Content hash
- Source ID
- LLM duplicate hints
- Similar title/event time
- Related entity overlap

V1 authority scoring should combine:

- Notion source authority score
- Source type
- First-source status
- LLM authority reasoning
- Manual review override, when needed

### 7. Signal Candidate and Quality Gate Layer

LLM output creates a Signal candidate, not an automatically published page.

Quality gate must require:

- Original source URL
- Source attribution
- Source authority score
- Confidence score
- AGI impact score
- English title and summary
- DysonX Take
- Watch Next
- Related AGI capabilities
- Related entity candidates
- Duplicate check result
- SEO metadata
- At least one social draft
- No unsupported high-risk claims
- No copied long-form source text

### 8. Publishing Layer

Publishing converts approved Signal records into static or generated Signal pages.

V1 page requirements:

- English canonical route
- Chinese localized fields when available
- Signal title
- Summary
- Original source attribution
- Source type and authority score
- Confidence score
- AGI impact score
- Technical impact score
- Market impact score
- Related AGI capabilities
- Related entity candidates
- DysonX Take
- Watch Next
- SEO metadata
- Social sharing metadata

### 9. Social Distribution Layer

V1 generates social post drafts only. It must not auto-post to social platforms.

Initial draft targets:

- X
- LinkedIn
- Telegram
- Newsletter snippet

Each draft should reference the Signal and preserve source attribution.

### 10. Observability and Audit Layer

V1 should log enough state to explain decisions later.

Required audit surfaces:

- Source sync records
- Collection job records
- Raw item fetch status
- LLM job status
- Quality gate result
- Publish job status
- Manual review notes

## Proposed Database Schema

The schema below is proposed for V1. Table and column names can be adapted to the selected persistence layer, but the separation between raw items, LLM analysis, Signals, publishing, and social drafts should remain.

### source_configs

- id
- notion_page_id
- name
- source_type
- platform
- url
- feed_url
- api_url
- account_handle
- repository
- authority_score
- priority
- fetch_frequency_minutes
- language
- region
- topic_tags_json
- related_entities_json
- enabled
- last_fetched_at
- last_success_at
- last_error
- notes
- created_at
- updated_at

### source_sync_runs

- id
- started_at
- completed_at
- status
- sources_seen
- sources_created
- sources_updated
- sources_disabled
- error

### collection_jobs

- id
- source_config_id
- collector_type
- started_at
- completed_at
- status
- items_seen
- items_created
- items_skipped
- error

### raw_items

- id
- source_config_id
- collection_job_id
- original_url
- canonical_url
- raw_title
- raw_content
- raw_excerpt
- raw_author
- raw_published_at
- fetched_at
- detected_language
- content_hash
- fetch_status
- error
- created_at
- updated_at

### normalized_items

- id
- raw_item_id
- canonical_url
- normalized_title
- readable_text
- excerpt
- detected_language
- normalized_published_at
- content_hash
- normalization_version
- status
- error
- created_at

### llm_analysis_jobs

- id
- raw_item_id
- normalized_item_id
- provider
- model_name
- prompt_version
- started_at
- completed_at
- status
- output_json
- validation_errors_json
- confidence_score
- error

### signal_candidates

- id
- raw_item_id
- normalized_item_id
- llm_analysis_job_id
- suggested_title_en
- suggested_title_zh
- suggested_slug
- summary_en
- summary_zh
- source_authority_score
- confidence_score
- agi_impact_score
- market_impact_score
- technical_impact_score
- affected_capabilities_json
- related_entities_json
- dysonx_take_en
- dysonx_take_zh
- watch_next_en
- watch_next_zh
- duplicate_group_id
- suggested_publish_status
- review_status
- reviewer_notes
- created_at
- updated_at

### signals

- id
- signal_candidate_id
- signal_id
- title_en
- title_zh
- slug
- summary_en
- summary_zh
- original_source_url
- source_config_id
- source_type
- source_authority_score
- confidence_score
- agi_impact_score
- market_impact_score
- technical_impact_score
- affected_capabilities_json
- related_entities_json
- dysonx_take_en
- dysonx_take_zh
- watch_next_en
- watch_next_zh
- duplicate_group_id
- publish_status
- published_at
- created_at
- updated_at

### signal_quality_reviews

- id
- signal_candidate_id
- signal_id
- status
- has_source_attribution
- has_llm_summary
- has_authority_score
- has_confidence_score
- has_agi_impact_score
- has_entity_candidates
- duplicate_checked
- has_english_version
- has_seo_metadata
- has_social_draft
- unsupported_claims_flag
- copied_text_flag
- decision_value_score
- reviewer_notes
- reviewed_at

### signal_seo_metadata

- id
- signal_id
- canonical_path
- meta_title_en
- meta_description_en
- meta_title_zh
- meta_description_zh
- og_title
- og_description
- og_image
- twitter_title
- twitter_description
- structured_data_json
- created_at
- updated_at

### social_post_drafts

- id
- signal_id
- platform
- language
- draft_text
- status
- generated_by_llm_job_id
- reviewer_notes
- created_at
- updated_at

### publish_jobs

- id
- signal_id
- target
- started_at
- completed_at
- status
- output_path
- error

## Proposed Notion Schema

The V1 Notion database should be named `DysonX Sources`.

Required properties:

- Name: title
- Enabled: checkbox
- Source Type: select
- Platform: select
- URL: url
- Feed URL: url
- API URL: url
- Account Handle: text
- Repository: text
- Authority Score: number
- Priority: select
- Fetch Frequency Minutes: number
- Language: select
- Region: select
- Topic Tags: multi-select
- Related Entities: multi-select or relation
- First Source: checkbox
- Notes: rich text
- Last Fetched At: date
- Last Success At: date
- Last Error: rich text

Suggested Source Type values:

- Official Company Blog
- Research Lab
- Paper
- GitHub Repository
- Government
- Regulatory
- Product Changelog
- Key Person
- Conference
- High Authority Media
- Manual

Suggested Priority values:

- Critical
- High
- Medium
- Low

Suggested Language values:

- English
- Chinese
- Multilingual
- Other

V1 should treat Notion as editable source configuration only. Signal records may optionally be mirrored back to Notion later, but Notion should not be the canonical Signal datastore in V1 unless explicitly approved.

## Proposed GitHub Project Structure

This structure is proposed for the V1 implementation PRs. Exact filenames may be adjusted after implementation discovery.

```text
docs/
  DYSONX_SIGNAL_ENGINE_V1_IMPLEMENTATION_PLAN.md
  DYSONX_SIGNAL_SCHEMA.md

dysonx/
  __init__.py
  config.py
  database.py
  notion/
    __init__.py
    sources.py
    schema.py
  collectors/
    __init__.py
    base.py
    rss.py
    webpage.py
    github.py
    manual.py
  normalization/
    __init__.py
    normalize.py
  llm/
    __init__.py
    analyze.py
    prompts/
      signal_analysis_v1.md
    schemas.py
  signals/
    __init__.py
    candidates.py
    quality_gate.py
    publish.py
    seo.py
  social/
    __init__.py
    drafts.py
  audit/
    __init__.py
    events.py

scripts/
  dysonx_sync_sources.py
  dysonx_collect_sources.py
  dysonx_analyze_raw_items.py
  dysonx_review_candidates.py
  dysonx_publish_signals.py

templates/
  signals/
    signal.html

static/
  data/
    signals.json

tests/
  dysonx/
    test_notion_source_schema.py
    test_collectors.py
    test_raw_item_storage.py
    test_llm_signal_schema.py
    test_quality_gate.py
    test_signal_publishing.py
    test_social_drafts.py
```

## Development Phases

### Phase 0: Planning and Schema Lock

Deliverables:

- Approve V1 implementation plan.
- Approve database schema.
- Approve Notion source schema.
- Approve LLM output schema.
- Confirm storage choice and migration strategy.

Exit criteria:

- Planning-only PR reviewed.
- No production code merged from planning PR unless approved.

### Phase 1: Foundation and Local Persistence

Deliverables:

- Add DysonX module structure.
- Add local database initialization and migrations.
- Add core schema tests.
- Add raw item and Signal candidate models.

Exit criteria:

- Tests confirm schema separation between raw items and Signals.
- No hardcoded monitored source list exists.

### Phase 2: Notion Source Sync

Deliverables:

- Add Notion source schema adapter.
- Add source sync command.
- Add validation for required source fields.
- Add source sync audit records.

Exit criteria:

- Enabled Notion sources sync into local cache.
- Disabled sources are not collected.
- Tests cover missing or invalid Notion fields.

### Phase 3: Collector Framework and Raw Storage

Deliverables:

- Add collector interface.
- Add RSS collector.
- Add web page collector.
- Add GitHub collector.
- Add manual URL collector.
- Store raw items with source attribution and content hashes.

Exit criteria:

- Raw items are stored separately from Signal candidates.
- Collectors do not decide publish status.
- Duplicate raw item prevention is tested.

### Phase 4: Normalization

Deliverables:

- Add URL canonicalization.
- Add readable text extraction.
- Add language detection.
- Add content hash normalization.

Exit criteria:

- Normalized items preserve attribution.
- Normalization does not generate publishable articles.

### Phase 5: LLM Analysis Pipeline

Deliverables:

- Add prompt versioning.
- Add LLM analysis command.
- Add structured output validation.
- Store LLM job metadata and output JSON.

Exit criteria:

- LLM analysis output validates against schema.
- Invalid output is rejected and logged.
- Tests verify LLM analysis is required before Signal candidate creation.

### Phase 6: Signal Candidate and Quality Gate

Deliverables:

- Create Signal candidates from validated LLM output.
- Add V1 quality gate.
- Add manual review fields.
- Add duplicate group support.

Exit criteria:

- Low-value, unsupported, duplicate, or unattributed candidates are blocked.
- Approved candidates can become Signals.

### Phase 7: Signal Publishing Workflow and Page Template

Deliverables:

- Add Signal page template.
- Add static data export or page generation path.
- Add English canonical metadata.
- Add Chinese localized fields where available.
- Add structured data.

Exit criteria:

- Published Signals include required source attribution, scoring, DysonX Take, Watch Next, SEO metadata, and social metadata.
- Existing site routes are not unexpectedly broken.

### Phase 8: Social Draft Generation

Deliverables:

- Generate draft posts for X, LinkedIn, Telegram, and newsletter.
- Store drafts linked to Signals.
- Keep drafts review-only.

Exit criteria:

- No automatic social publishing occurs.
- Drafts preserve source attribution and link back to Signal pages.

### Phase 9: Integration Guards and PR Readiness

Deliverables:

- Add tests for source configuration, LLM schema, quality gate, publishing, SEO metadata, and social drafts.
- Run constitution guard.
- Run architecture guard.
- Run build checks.

Exit criteria:

- Draft PR documents tests and known limitations.
- No merge or deployment is performed by the agent.

## Risks

### Architecture Drift

Risk: V1 could accidentally recreate the existing aggregator pattern.

Mitigation:

- Keep raw items, LLM analysis, Signal candidates, and published Signals as separate records.
- Add tests that raw items cannot publish directly.

### Notion Schema Drift

Risk: Notion properties may be renamed or removed.

Mitigation:

- Validate required properties at sync time.
- Fail source sync with actionable errors.
- Keep the expected Notion schema documented.

### LLM Output Instability

Risk: LLM responses may be invalid, thin, or inconsistent.

Mitigation:

- Use versioned prompts.
- Validate structured JSON.
- Store raw output and validation errors.
- Require quality gate review before publication.

### Source Attribution Weakness

Risk: Signals may be created without sufficient source evidence.

Mitigation:

- Make original source URL and source authority score mandatory.
- Block candidates without attribution.

### Duplicate Signal Creation

Risk: Multiple raw items about the same event may become duplicate Signals.

Mitigation:

- Use canonical URL, content hash, LLM duplicate hints, source ID, title similarity, and entity overlap.
- Keep duplicate group ID on candidates and Signals.

### Copyright and Copying Risk

Risk: Published pages may copy too much source text.

Mitigation:

- Store raw content privately for evidence.
- Publish original interpretation and short attributed excerpts only.
- Add copied-text quality gate flag.

### Premature Knowledge Graph Complexity

Risk: Implementing graph infrastructure in V1 could expand scope.

Mitigation:

- Store related entity candidates and capability mappings as structured JSON in V1.
- Defer graph tables and relationship engine to the Knowledge Graph phase.

### Production Deployment Risk

Risk: Automation may accidentally publish or deploy.

Mitigation:

- Keep V1 implementation behind draft PRs.
- Do not change production secrets.
- Do not merge or deploy from agent tasks.

## Estimated Implementation Order

1. Approve this V1 implementation plan.
2. Add schema documentation and choose local persistence/migration approach.
3. Implement database tables and tests.
4. Implement Notion source sync.
5. Implement collector interface and first collectors.
6. Implement raw item storage and deduplication basics.
7. Implement normalization.
8. Implement LLM analysis schema, prompt versioning, and validation.
9. Implement Signal candidate creation.
10. Implement quality gate.
11. Implement Signal publishing workflow and page template.
12. Implement SEO metadata and structured data export.
13. Implement social draft generation.
14. Add integration tests and governance guard coverage.
15. Open implementation draft PRs in small, reviewable increments.

## Recommended PR Breakdown

1. `docs`: V1 plan and schema docs.
2. `feature`: local persistence and core models.
3. `feature`: Notion source sync.
4. `feature`: collectors and raw storage.
5. `feature`: LLM analysis pipeline.
6. `feature`: Signal candidate and quality gate.
7. `feature`: Signal publishing and page template.
8. `feature`: social draft generation.

Each implementation PR should remain draft until checks pass and human review confirms constitution alignment.
