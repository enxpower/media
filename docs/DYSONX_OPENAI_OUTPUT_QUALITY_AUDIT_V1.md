# DysonX OpenAI Output Quality Audit V1

## Purpose

DysonX OpenAI Output Quality Audit V1 is the first offline implementation step after the Signal Quality Framework V1.

It reviews already-generated safe JSON reports from the V1 Intelligence Pipeline and produces a deterministic quality audit report for IntelligenceSignal output. It exists to identify whether OpenAI-generated Signals are dense, attributed, source-aware, AGI-relevant, reusable, and safe enough to proceed toward future scoring and human review work.

This audit does not call OpenAI. It does not dispatch workflows. It does not publish content. It does not write website pages. It does not mutate Notion. It does not use the live GitHub API. It does not scrape article bodies. It does not write Knowledge Graph records. It does not implement Prediction Engine work. It does not deploy.

## Relationship to Signal Quality Framework V1

This audit implements the first deterministic review tool aligned with:

`docs/DYSONX_SIGNAL_QUALITY_FRAMEWORK_V1.md`

The framework defines what makes a DysonX Signal high quality. This audit converts those standards into conservative V1 checks over existing IntelligenceSignal JSON.

The audit is intentionally not a final SignalQualityScore implementation. It is a review layer that helps validate whether the quality dimensions, risk flags, and tier thresholds are useful before they become part of a deeper scoring or approval system.

## Input Reports

The script accepts these CLI arguments:

```bash
python3 scripts/dysonx_openai_output_quality_audit.py \
  --llm-audit-report tmp/dysonx_v1_intelligence_pipeline/llm_audit_report.json \
  --signal-candidate-report tmp/dysonx_v1_intelligence_pipeline/signal_candidate_report.json \
  --pipeline-report tmp/dysonx_v1_intelligence_pipeline/v1_intelligence_pipeline_report.json \
  --output tmp/dysonx_openai_output_quality_audit.json
```

Inputs are safe local JSON reports only:

- LLM audit report, containing `intelligence_signals` or `signals`
- SignalCandidate report, containing `candidates`
- final pipeline report, containing high-level pipeline and safety status

The audit does not require `OPENAI_API_KEY`. It must remain valid when that environment variable is absent.

## Output Schema

The audit writes a JSON object containing:

- `audit_version`
- `created_at`
- `input_paths`
- `signals_reviewed`
- `framework_reference`
- `milestone_reference`
- `quality_dimensions`
- `signal_reviews`
- `tier_counts`
- `findings`
- `recommended_next_actions`
- `safety_flags`

Each `signal_reviews` item contains:

- `signal_id`
- `candidate_id`
- `title`
- `source_url`
- `provider`
- `prompt_version`
- `quality_scores`
- `total_score`
- `quality_tier`
- `pass_publish_readiness_candidate`
- `strengths`
- `weaknesses`
- `missing_fields`
- `risk_flags`
- `confidence_notes`
- `recommended_action`

## Quality Dimensions

The audit uses the Signal Quality Framework V1 dimensions:

- Information Density
- Source Attribution
- Source Authority
- Reasoning Depth
- Novelty
- AGI Capability Relevance
- Entity / Relationship Value
- Tracker Reuse Value
- Actionability
- Watch Next Specificity
- Prediction / Future Review Value
- Confidence Support
- Anti-Garbage Risk

Each dimension is scored from 0 to 5. The maximum score is 65.

## Tiering Logic

V1 tiering is conservative:

- Tier A: Decision-grade Signal, `total_score >= 52` and no critical risk flags
- Tier B: Useful Signal, `total_score >= 40` and no critical risk flags
- Tier C: Needs Review, `total_score >= 28`
- Tier D: Reject / Low-value, below 28 or too thin/generic to use

Tier A is intentionally hard to reach. Tier B is useful but not automatically publish-ready. Tier C requires improved analysis or human review. Tier D should be rejected or regenerated.

Critical risk flags include:

- `missing_source_url`
- `missing_why_it_matters`
- `missing_watch_next`
- `missing_agi_capability`
- `unsupported_publish_readiness`
- `article_like_output`
- `generic_summary`
- `raw_provider_response_present`
- `network_or_live_operation_attempted`

Critical risk flags prevent `pass_publish_readiness_candidate` from becoming true.

## Safety Boundaries

The audit output includes these safety flags, all false:

- `openai_call_performed`
- `workflow_dispatched`
- `publishing_performed`
- `website_pages_written`
- `social_posting_performed`
- `notion_mutation_performed`
- `live_github_api_used`
- `article_body_scraping_performed`
- `raw_provider_response_stored`
- `knowledge_graph_write_performed`
- `prediction_engine_performed`
- `deployment_performed`

The audit reads only existing report JSON. It does not import provider adapters or HTTP libraries.

## Non-Goals

This PR does not:

- call OpenAI
- require `OPENAI_API_KEY`
- dispatch workflows
- change workflows
- publish content
- generate website pages
- write public content files
- social post
- mutate Notion
- use live GitHub API collection
- scrape article bodies
- store raw provider responses
- write Knowledge Graph records
- implement Prediction Engine work
- implement final SignalQualityScore
- implement Confidence Calibration
- implement Multi-source Correlation
- implement Human Approval Gate
- implement Publish Readiness Gate
- deploy
- merge itself

## How To Run Locally

Run the V1 intelligence pipeline in fake mode to generate safe fixture-style reports:

```bash
python3 scripts/dysonx_v1_intelligence_pipeline.py \
  --source-store tests/fixtures/source_sync_store_v1.json \
  --output-dir tmp/dysonx_v1_intelligence_pipeline
```

Then run the output quality audit:

```bash
python3 scripts/dysonx_openai_output_quality_audit.py \
  --llm-audit-report tmp/dysonx_v1_intelligence_pipeline/llm_audit_report.json \
  --signal-candidate-report tmp/dysonx_v1_intelligence_pipeline/signal_candidate_report.json \
  --pipeline-report tmp/dysonx_v1_intelligence_pipeline/v1_intelligence_pipeline_report.json \
  --output tmp/dysonx_openai_output_quality_audit.json
```

The same audit can review reports from a manually gated OpenAI run after those reports already exist locally or as safe artifacts. The audit itself never initiates a provider call.

## Next Recommended PR

The next recommended PR is:

`feat: add SignalQualityScore V1`

That PR should integrate validated audit results into a first-class score object only after this audit's output shape, risk flags, and tier thresholds have been reviewed against real and fixture outputs.

Publishing should remain blocked until SignalQualityScore V1, Confidence Calibration V1, Multi-source Correlation V1, Human Approval Gate V1, and Publish Readiness Gate V1 are stable.
