# DysonX Real LLM Provider Gated V1

Status: gated implementation PR documentation

## Purpose

DysonX Real LLM Provider Gated V1 introduces the first narrow real-provider
boundary after the V1 offline intelligence pipeline milestone.

The goal is to process existing SignalCandidate inputs into validated
IntelligenceSignal outputs while keeping the system manual-only, audit-heavy,
and publishing-blocked.

This is not a publishing PR. It does not write website pages, public content
files, social posts, Knowledge Graph records, prediction records, dashboards, or
deployment artifacts.

## Architecture

Required flow:

```text
SignalCandidate report
-> Provider gate
-> OpenAI provider adapter
-> Prompt registry
-> Strict JSON output validation
-> LLM job / audit report
-> IntelligenceSignal report
```

The implementation lives in:

```text
scripts/dysonx_real_llm_provider.py
```

The CLI reads a SignalCandidate report and writes a JSON audit report. It does
not call collectors, mutate Notion, call live GitHub APIs, scrape article
bodies, publish, post socially, schedule work, or deploy.

## Provider Choice

V1 supports:

- `fake`
- `openai`

The default provider is `fake`.

OpenAI is the only real provider accepted by V1. Claude, Gemini, and other
providers are intentionally not implemented in this PR.

## Dependency Decision

No OpenAI SDK dependency is added.

The OpenAI adapter uses Python standard library HTTP support through
`http.client`. This keeps the integration narrow, avoids dependency churn, and
makes the provider boundary easy to audit. The adapter targets the OpenAI
Responses API and requests strict JSON output.

The implementation was checked against the official OpenAI Responses API
reference during development. The PR does not run a real API call during
validation.

## Environment Variables

The OpenAI real-provider path requires:

```text
OPENAI_API_KEY
```

The key must be supplied by the runtime environment. It must never be printed,
stored in reports, committed, or included in artifacts.

Missing `OPENAI_API_KEY` fails closed when `--provider openai` is selected.

## Provider Gate

The real OpenAI provider runs only when all of these are true:

- `--provider openai`
- `--allow-real-llm`
- `OPENAI_API_KEY` is present
- `--max-items` is set to a small positive integer

The current maximum is intentionally capped at `5` items.

If any condition is missing, the CLI exits through the provider gate without
creating an output report.

Fake-provider mode does not require `--allow-real-llm`, `OPENAI_API_KEY`, or
`--max-items`.

## CLI

Offline fake-provider validation:

```bash
python3 scripts/dysonx_real_llm_provider.py \
  --signal-candidates tmp/dysonx_v1_intelligence_pipeline/signal_candidates_report.json \
  --provider fake \
  --output tmp/dysonx_real_llm_report.json
```

Manual real-provider shape:

```bash
python3 scripts/dysonx_real_llm_provider.py \
  --signal-candidates tmp/dysonx_v1_intelligence_pipeline/signal_candidates_report.json \
  --provider openai \
  --allow-real-llm \
  --max-items 1 \
  --output tmp/dysonx_real_llm_report.json
```

The real-provider command must remain manual. No scheduled workflow is added.

## Prompt Registry

The V1 provider prompt version is:

```text
real_llm_provider_gated_v1
```

The prompt instructs the provider to transform one SignalCandidate into one
structured IntelligenceSignal and return only strict JSON.

The prompt explicitly says:

- do not write an article
- do not publish

## Strict Output Validation

Required IntelligenceSignal output fields:

- `title`
- `summary`
- `why_it_matters`
- `agi_capability`
- `related_entities`
- `confidence`
- `watch_next`
- `source_url`

Validation rejects malformed output when:

- a required field is missing
- required string fields are empty
- `related_entities` is not a list of strings
- `confidence` is not a number from `0` to `1`

Invalid provider output is captured in validation/audit records and does not
become an IntelligenceSignal.

## Audit Report

The output report includes:

- `provider`
- `model`
- `prompt_version`
- `items_requested`
- `items_processed`
- `items_skipped`
- `jobs_created`
- `validations_passed`
- `validations_failed`
- `intelligence_signals_created`
- `estimated_token_usage`
- `jobs`
- `validations`
- `audit_records`
- `intelligence_signals`
- safety flags

The report does not store raw unredacted provider responses by default.

## Required Safety Flags

The report includes:

- `real_llm_api_used`
- `llm_api_calls_performed`
- `publishing_performed`
- `website_pages_written`
- `public_content_files_written`
- `social_posting_performed`
- `deployment_performed`
- `notion_write_operations_performed`
- `live_github_api_used`
- `article_body_scraping_performed`
- `raw_provider_response_stored`

In fake-provider mode:

- `real_llm_api_used`: false
- `llm_api_calls_performed`: false

For the real OpenAI path:

- `real_llm_api_used`: true only after the provider gate is satisfied
- `llm_api_calls_performed`: true only after the provider gate is satisfied
- all publishing, website, social, deployment, Notion, GitHub, article scraping,
  and raw-response storage flags remain false

## What Is Not Implemented

This PR does not implement:

- scheduled workflow
- automatic real LLM run
- website page generation
- public content file writing
- publishing
- social posting
- Knowledge Graph implementation
- Prediction Engine
- dashboard
- billing
- enterprise features
- multi-tenant features
- deployment
- Notion mutation
- live GitHub API integration
- article body scraping
- raw unredacted provider response storage by default

## Validation Expectations

PR creation validation must remain offline:

```bash
python3 scripts/constitution_guard.py
python3 scripts/architecture_guard.py
python3 scripts/release_guard.py
python3 -m py_compile scripts/*.py
python3 -m unittest discover -s tests
python3 scripts/dysonx_static_preview_check.py
python3 scripts/dysonx_v1_intelligence_pipeline.py \
  --source-store tests/fixtures/source_sync_store_v1.json \
  --output-dir tmp/dysonx_v1_intelligence_pipeline
python3 scripts/dysonx_real_llm_provider.py \
  --signal-candidates tmp/dysonx_v1_intelligence_pipeline/signal_candidates_report.json \
  --provider fake \
  --output tmp/dysonx_real_llm_report.json
git diff --check
```

Do not run real OpenAI during PR creation.

## Governance Position

This PR preserves the DysonX architecture:

- Source configuration remains Notion-managed.
- Collection remains separate from RawItem persistence.
- SignalCandidate remains the handoff into the intelligence layer.
- LLM analysis is the first major interpretation step after collection.
- Quality Review and publishing remain downstream and blocked.
- No public output is created.
- DysonX remains Signal-first, not Article-first.

The next review should verify the OpenAI gate before any manual real-provider
smoke test is authorized.
