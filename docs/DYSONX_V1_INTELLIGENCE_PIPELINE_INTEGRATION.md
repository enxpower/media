# DysonX V1 Intelligence Pipeline Integration

Status: V1 end-to-end integration path with fake default and gated real-provider mode

## Purpose

This integration composes existing DysonX V1 modules into one audit path from
Source store fixture through publish-package metadata.

The default provider remains `fake`. A real OpenAI path can be invoked only
through the already-approved gated provider implementation and explicit
orchestrator flags.

Required flow:

```text
Source store / fixture
-> Collector Foundation
-> RawItem store
-> Signal Candidate Pipeline
-> Gated LLM Provider
-> IntelligenceSignal Audit
-> Signal Ranking
-> Quality Review
-> Publish Package metadata
-> End-to-end audit report
```

## Script

```text
scripts/dysonx_v1_intelligence_pipeline.py
```

Command:

```bash
python3 scripts/dysonx_v1_intelligence_pipeline.py \
  --source-store tests/fixtures/source_sync_store_v1.json \
  --output-dir tmp/dysonx_v1_intelligence_pipeline
```

Real-provider mode is manual and gate-protected:

```bash
python3 scripts/dysonx_v1_intelligence_pipeline.py \
  --source-store tests/fixtures/source_sync_store_v1.json \
  --output-dir tmp/dysonx_v1_intelligence_pipeline \
  --provider openai \
  --allow-real-llm \
  --max-items 1
```

The OpenAI path runs only when all of these are true:

- `--provider openai`
- `--allow-real-llm`
- `OPENAI_API_KEY` is present
- `--max-items` is specified and accepted by the gated provider

Missing gate conditions fail closed before the provider can run.

## Reports Written

The script writes JSON audit artifacts only:

- `collector_report.json`
- `raw_items_store.json`
- `signal_candidate_report.json`
- `llm_audit_report.json`
- `signal_ranking_report.json`
- `quality_review_report.json`
- `publish_package_report.json`
- `v1_intelligence_pipeline_report.json`

It does not write website pages, public content files, social posts, graph data,
prediction data, production data, or deployment artifacts.

## Module Reuse

The integration composes existing modules:

- `dysonx_collector_foundation.run_collection`
- `dysonx_rawitem_signal_pipeline.run_integration`
- `dysonx_real_llm_provider.run_provider`
- `dysonx_signal_ranking.rank_signals`
- `dysonx_publish_eligibility.run_quality_review`
- `dysonx_publish_package.run_publish_package`

It does not duplicate collector, SignalCandidate, provider adapter, provider
gate, output validation, IntelligenceSignal creation, ranking, quality review,
or publish-package logic.

The orchestrator contains only a downstream compatibility projection that maps
validated provider signals and candidate metadata into the existing V1 ranking
input shape. It does not create a second OpenAI adapter or a second
IntelligenceSignal validation path.

## Layer Boundaries

The final audit report confirms:

- RawItem remains separate from SignalCandidate
- SignalCandidate remains separate from IntelligenceSignal
- IntelligenceSignal remains separate from PublishPackage
- Collector Foundation stops at RawItem persistence

## Final Audit Report

The final audit report includes:

- `sources_seen`
- `raw_items_created`
- `signal_candidates_created`
- `llm_jobs_created`
- `intelligence_signals_created`
- `signals_ranked`
- `publish_ready`
- `packages_created`
- `publish_package_created`
- `provider`
- `items_requested`
- `items_processed`
- `prompt_version`
- `rejected_or_skipped`
- `module_reuse`
- `layer_boundaries`
- safety flags

## Safety Flags

Required safety flags remain false in fake mode:

- `notion_write_operations_performed`
- `live_github_api_used`
- `real_llm_api_used`
- `llm_api_calls_performed`
- `publishing_performed`
- `website_pages_written`
- `public_content_files_written`
- `social_posting_performed`
- `article_body_scraping_performed`
- `deployment_performed`

In `provider=openai` mode, `real_llm_api_used` and
`llm_api_calls_performed` may be true only after the manual gate succeeds.
Publishing, website writing, public content writing, social posting, Notion
mutation, live GitHub API usage, article body scraping, and deployment must
remain false in every provider mode.

## What Is Not Implemented

This integration does not implement:

- Claude, Gemini, or other provider calls
- real LLM provider SDKs
- website page generation
- public content file writing
- social posting
- Knowledge Graph writes
- Prediction Engine
- dashboard, billing, enterprise, or multi-tenant features
- scheduled workflows
- deployment
- Notion mutation
- live GitHub API access
- article body scraping
- broad refactors

## Next Step

The next reviewed PR should evaluate the quality of manually gated OpenAI
outputs through audit artifacts before any broader run. Any future real-provider
expansion must remain separate from publishing and must keep quality gates
blocking public output.
