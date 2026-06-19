# DysonX OpenAI Gated Smoke Test

Status: manual smoke-test workflow documentation

## Purpose

The DysonX OpenAI Gated Smoke Test verifies that the already merged gated
OpenAI provider path can be invoked manually with strict limits.

This smoke test is not a publishing workflow. It exists only to confirm that the
real provider boundary can process one existing SignalCandidate into a validated
IntelligenceSignal audit report.

## Workflow

Workflow file:

```text
.github/workflows/dysonx-openai-gated-smoke-test.yml
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

The workflow passes the secret as an environment variable to the gated provider
CLI. It must not be printed, echoed, uploaded, or written to artifacts.

## Smoke-Test Flow

The workflow performs these steps:

```text
Checkout repository
-> Set up Python
-> Run V1 intelligence pipeline against fixture source store
-> Run dysonx_real_llm_provider.py with OpenAI gate enabled
-> Assert safety flags and item limits
-> Upload safe JSON artifacts
```

The real provider command is:

```bash
python3 scripts/dysonx_real_llm_provider.py \
  --signal-candidates tmp/dysonx_v1_intelligence_pipeline/signal_candidates_report.json \
  --provider openai \
  --allow-real-llm \
  --max-items 1 \
  --output tmp/dysonx_openai_smoke_report.json
```

## Cost Boundary

The workflow uses:

```text
--max-items 1
```

This keeps the smoke test to a single candidate. The report should show:

- `items_requested` less than or equal to `1`
- `items_processed` less than or equal to `1`

The workflow is still a real provider call when run manually, so it can incur a
small OpenAI API cost. It must remain manual until a separate scheduling and
cost-control review is approved.

## Safety Assertions

The workflow fails unless the OpenAI smoke report confirms:

- `provider`: `openai`
- `items_requested` less than or equal to `1`
- `items_processed` less than or equal to `1`
- `real_llm_api_used`: true
- `llm_api_calls_performed`: true
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

- `tmp/dysonx_openai_smoke_report.json`
- `tmp/dysonx_v1_intelligence_pipeline/signal_candidates_report.json`

The workflow does not upload:

- raw provider responses
- secrets
- full raw article content
- RawItem stores
- publish packages
- website pages
- public content files

## How To Read Success

A successful run means:

- GitHub Actions could invoke the OpenAI-gated provider path manually.
- The provider gate accepted the explicit manual command.
- The run was limited to at most one SignalCandidate.
- The provider report passed strict safety assertions.
- No publishing, website writing, social posting, deployment, Notion mutation,
  live GitHub API usage, article body scraping, or raw provider response storage
  occurred.

## How To Read Failure

A failure may mean:

- `OPENAI_API_KEY` is missing or invalid.
- The provider API returned an error.
- The provider output failed strict JSON validation.
- The report safety flags did not match the required boundary.
- More than one item was requested or processed.
- Expected safe artifacts were not created.

Failure does not publish content. It should be treated as an integration signal
for the provider boundary only.

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
- full source collection
- live Notion mutation
- live GitHub API usage
- article body scraping
- large-volume cost behavior
- final editorial quality for public release

## Next Step After Successful Smoke Test

After one successful manual smoke test, the next recommended PR should document
the result and decide whether to add a narrow real-provider audit review step.

Do not proceed directly to publishing, social distribution, Knowledge Graph
writes, scheduled LLM runs, or deployment from this smoke-test milestone.
