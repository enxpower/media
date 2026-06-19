# DysonX V1 OpenAI Orchestrator Smoke Test

Status: manual full-orchestrator smoke-test documentation

## Purpose

The DysonX V1 OpenAI Orchestrator Smoke Test verifies that the full V1
Intelligence Pipeline orchestrator can run with the already-gated OpenAI
provider.

This is not a publishing workflow. It exists only to confirm that the full V1
pipeline can carry one manually gated OpenAI IntelligenceSignal through ranking,
quality review, publish-package metadata, and final audit reporting.

## Workflow

Workflow file:

```text
.github/workflows/dysonx-v1-openai-orchestrator-smoke.yml
```

Trigger:

```text
workflow_dispatch only
```

There is no schedule trigger, push trigger, pull request trigger, deployment
trigger, or automatic production run.

## Required Secret

The workflow requires this GitHub Secret:

```text
OPENAI_API_KEY
```

The workflow passes the secret to the existing gated provider path through the
orchestrator process environment. It must not be printed, echoed, uploaded, or
written to artifacts.

## Full Orchestrator Path Tested

The workflow runs this full path:

```text
Source store fixture
-> Collector
-> RawItem
-> SignalCandidate
-> OpenAI IntelligenceSignal
-> Ranking
-> QualityReview
-> PublishPackage metadata
-> Final audit report
```

The orchestrator command is:

```bash
python3 scripts/dysonx_v1_intelligence_pipeline.py \
  --source-store tests/fixtures/source_sync_store_v1.json \
  --output-dir tmp/dysonx_v1_openai_orchestrator_smoke \
  --provider openai \
  --allow-real-llm \
  --max-items 1
```

## Cost Boundary

The workflow uses:

```text
--max-items 1
```

This keeps the smoke test to at most one SignalCandidate. The final audit report
must show:

- `items_requested` less than or equal to `1`
- `items_processed` less than or equal to `1`

The run still invokes the real OpenAI provider when manually dispatched, so it
can incur a small API cost. It must remain manual until a separate scheduling
and cost-control review is approved.

## Safety Assertions

The workflow fails unless the final orchestrator audit report confirms:

- `provider`: `openai`
- `real_llm_api_used`: true
- `llm_api_calls_performed`: true
- `items_requested` less than or equal to `1`
- `items_processed` less than or equal to `1`
- `publishing_performed`: false
- `website_pages_written`: false
- `public_content_files_written`: false
- `social_posting_performed`: false
- `deployment_performed`: false
- `notion_write_operations_performed`: false
- `live_github_api_used`: false
- `article_body_scraping_performed`: false
- `raw_provider_response_stored`: false

## Safe Artifacts

The workflow uploads only:

- `tmp/dysonx_v1_openai_orchestrator_smoke/v1_intelligence_pipeline_report.json`
- `tmp/dysonx_v1_openai_orchestrator_smoke/llm_audit_report.json`
- `tmp/dysonx_v1_openai_orchestrator_smoke/signal_candidate_report.json`

The workflow does not upload:

- raw provider responses
- secrets
- RawItem stores
- publish packages
- website pages
- public content files

## Difference From PR #50 Provider Smoke

PR #50 added a provider-boundary smoke test. That workflow first creates a
SignalCandidate fixture output, then calls `dysonx_real_llm_provider.py`
directly.

This workflow tests the larger orchestrator boundary. It calls
`dysonx_v1_intelligence_pipeline.py` once and verifies the full chain from
Source store fixture through final V1 audit report.

## How To Read Success

A successful run means:

- GitHub Actions could invoke the full V1 orchestrator manually.
- The orchestrator reused the gated OpenAI provider path.
- The run was limited to at most one SignalCandidate.
- Ranking, QualityReview, and PublishPackage metadata stages completed.
- Final safety assertions passed.
- No publishing, website writing, social posting, deployment, Notion mutation,
  live GitHub API usage, article body scraping, or raw provider response storage
  occurred.

## How To Read Failure

A failure may mean:

- `OPENAI_API_KEY` is missing or invalid.
- The provider API returned an error.
- The provider output failed strict JSON validation.
- The downstream ranking, quality review, or publish-package metadata stage
  rejected or could not process the generated IntelligenceSignal.
- The final audit report safety flags did not match the required boundary.
- More than one item was requested or processed.
- Expected safe artifacts were not created.

Failure does not publish content. It should be treated as an integration signal
for the orchestrator boundary only.

## What This Does Not Validate

This smoke test does not validate:

- production publishing
- website page generation
- public content writing
- social posting
- Knowledge Graph writes
- Prediction Engine behavior
- dashboard, billing, enterprise, or multi-tenant features
- scheduled operation
- production deployment
- live Notion mutation
- live GitHub API usage
- article body scraping
- large-volume cost behavior
- final editorial quality for public release

## Next Step After Success

After one successful manual orchestrator smoke test, the next recommended PR
should document the result and review the real-provider output quality across
the final orchestrator audit report.

Do not proceed directly to publishing, social distribution, Knowledge Graph
writes, scheduled LLM runs, or deployment from this smoke-test milestone.
