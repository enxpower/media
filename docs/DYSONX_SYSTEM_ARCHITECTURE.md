# DysonX System Architecture v1.0

DysonX is an AI / AGI Intelligence OS whose architecture must protect long-term value.

Canonical flow:

`Source -> LLM Understanding -> Structured Knowledge -> Signal / Tracker / Report / Distribution`

Forbidden flow:

`Source -> RSS mirror -> generic article -> SEO spam`

## Layers

1. Source Configuration Layer
2. Collection Layer
3. Raw Data Layer
4. Normalization Layer
5. LLM Intelligence Layer
6. Deduplication and Authority Layer
7. Knowledge Graph Layer
8. Publishing Layer
9. Social Distribution Layer
10. Reporting Layer
11. Observability and Audit Layer
12. Governance Layer

Each layer must be separable, testable, and replaceable.

## Source Configuration Layer

All monitored sources must be stored in Notion, not hardcoded into application logic.

Source records should include name, source type, URL/feed/API/account/repository, platform, authority score, priority, fetch frequency, language, region, topic tags, related entities, enabled status, last fetched time, last success time, last error, and notes.

## Collection Layer

Collectors fetch raw content from configured sources. Supported collectors may include RSS, websites, GitHub, arXiv/papers, government pages, social accounts, APIs, and manual ingestion.

Collectors must preserve original URL, source ID, timestamps, raw title, raw content/excerpt, content hash, and error state.

Collectors must not decide final importance, AGI relevance, or publish status by themselves.

## Raw Data Layer

Raw data must be stored separately from interpreted Signals.

Minimum raw item fields:

- Raw item ID
- Source ID
- Original URL
- Raw title
- Raw content or excerpt
- Raw author, when available
- Raw published time, when available
- Fetched time
- Content hash
- Fetch status
- Error state

Raw data is evidence. It must not be overwritten by LLM interpretation.

## Normalization Layer

Normalization cleans markup, extracts readable text, detects language, normalizes dates and URLs, creates content hash, removes obvious boilerplate, and preserves original attribution.

Normalization must not rewrite content into a published article.

## LLM Intelligence Layer

LLM analysis is the first major interpretation step.

Required outputs:

- Summary
- Topic classification
- Entity extraction
- Event extraction
- AGI capability mapping
- Importance score
- Authority reasoning
- Confidence score
- Duplicate hints
- Suggested Signal title
- Suggested DysonX Take
- Watch Next
- Suggested social posts
- Suggested publish status

Every LLM output should store model provider, model name, prompt version, timestamp, input raw item ID, output JSON, and confidence fields where practical.

## Deduplication and Authority Layer

Repeated coverage of the same event must become one Signal.

Deduplication should use URL canonicalization, content hash, semantic similarity, entity overlap, event time, and LLM duplicate hints.

Authority scoring should prefer first-source evidence over secondhand reporting.

## Knowledge Graph Layer

The knowledge graph is the long-term asset.

Core models:

- sources
- raw_items
- signals
- entities
- entity_relationships
- topics
- agi_capabilities
- trackers
- predictions
- reports
- social_posts
- publish_jobs
- quality_reviews

Entity types include Company, Person, Organization, Government body, Product, Model, Paper, GitHub project, Policy, Technology topic, AGI capability, Event, Signal, Prediction, and Report.

Relationships must be explicit and queryable.

## Publishing Layer

A Signal may be published only after passing the quality gate.

Published Signal pages should include title, summary, source attribution, authority score, confidence score, AGI impact score, related entities, related capabilities, DysonX Take, Watch Next, internal links to trackers, English default content, Chinese localized content when available, structured data, and SEO metadata.

Public-facing surfaces are governed by `docs/DYSONX_PUBLIC_INTELLIGENCE_SURFACES_V1.md`.

Public Signal Page Generator V1 is the Step 2 static draft generator governed by `docs/DYSONX_PUBLIC_SIGNAL_PAGE_GENERATOR_V1.md`. It may generate local preview HTML only after Publish Readiness Gate V1 passes, and those draft pages are not publication, production approval, deployment, or public release.

Manual Publish Approval V1 is the Step 3 offline approval report governed by `docs/DYSONX_MANUAL_PUBLISH_APPROVAL_V1.md`. It consumes the Step 2 manifest and explicit Owner approval input for the future Production Publish Pack. `approved_for_production_pack` is not publication, does not modify generated HTML, and does not deploy.

Production Publish Pack V1 is the Step 4 offline artifact pack governed by `docs/DYSONX_PRODUCTION_PUBLISH_PACK_V1.md`. It consumes Step 2 generated pages and Step 3 approval, packages only approved pages for Step 5, emits release guard evidence, and does not publish, deploy, dispatch workflows, call OpenAI, write to `media.energizeos.com`, or mark `published` true.

First Public Launch V1 is the Step 5 launch guard governed by `docs/DYSONX_FIRST_PUBLIC_LAUNCH_V1.md`. It requires explicit Owner launch authorization and passed Step 4 release guard evidence before copying approved static Signal pages into the repository public static output path. It does not call OpenAI, scrape, add backend/database systems, manually dispatch workflows, or perform social/newsletter distribution.

## Tracker Layer

Trackers are persistent intelligence surfaces for companies, people, topics, capabilities, models, papers, policies, and GitHub projects.

Trackers should be updated from Signals and relationships, not manually rewritten each time.

## Report Layer

Reports synthesize multiple Signals. They must not merely concatenate articles.

Report types include Daily AI / AGI Brief, Weekly AGI Intelligence Report, Monthly Capability Map Update, Company Strategy Brief, Research-to-Business Translation, and Policy Impact Brief.

## Social Distribution Layer

Each published Signal or Report can generate platform-specific drafts for X, LinkedIn, Telegram, Threads, and Newsletter.

Social posts must link back to DysonX and must not blindly duplicate website copy.

## Localization Layer

English is canonical. Chinese is localization.

Chinese translation must not create separate duplicate Signals unless the underlying event is different.

## Quality Gate Layer

Before publishing, every Signal must pass checks for source, original URL, LLM summary, authority score, confidence score, AGI impact, entity extraction, duplicate check, English version, SEO metadata, social draft, unsupported claims, copyright copying, and decision value.

## Observability and Audit Layer

Required logs include source sync, fetch jobs, LLM jobs, deduplication decisions, authority scores, publishing jobs, social distribution, failed jobs, and manual overrides.

The system must allow future review of why a Signal was published, rejected, or scored a certain way.

## Deployment Architecture

Recommended environments:

- Local development
- Preview / PR environment
- Staging
- Production

Production must never be modified directly by Codex or Claude Code.

## Forbidden Architecture Drift

Forbidden:

- Permanent hardcoded source lists
- Making Article primary instead of Signal
- Bypassing LLM interpretation
- Publishing raw RSS summaries directly
- Breaking English-default architecture
- Removing Chinese switchability
- Mixing collection, analysis, publishing, and UI into one tangled script
- Treating website pages as the only data store
- Generating SEO pages without intelligence value
- Deploying directly to production without review

## Architecture Success Standard

The architecture succeeds if DysonX can answer:

- What happened?
- Who was involved?
- What capability did it affect?
- Which source proved it?
- How did this change over time?
- What did DysonX previously predict?
- Was the prediction correct?
- What should a decision-maker watch next?

If the architecture can only display news articles, it has failed.
