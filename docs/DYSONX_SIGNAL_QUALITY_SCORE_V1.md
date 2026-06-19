# DysonX SignalQualityScore V1

## Purpose

SignalQualityScore V1 turns DysonX OpenAI Output Quality Audit V1 results into a stable score report that future Confidence Calibration, Multi-source Correlation, Human Approval, and Publish Readiness Gate work can consume.

This is an offline score object derived from an existing audit report. It does not call OpenAI, dispatch workflows, publish content, write website pages, mutate Notion, use live GitHub API collection, scrape article bodies, write Knowledge Graph records, implement Prediction Engine work, deploy, or merge.

SignalQualityScore V1 does not enable publishing. It creates structured score records so DysonX can review quality consistently before any future approval or publish-readiness path exists.

## Relationship To Signal Quality Framework V1

SignalQualityScore V1 uses the 13 dimensions defined by:

`docs/DYSONX_SIGNAL_QUALITY_FRAMEWORK_V1.md`

The score dimensions are:

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

The score does not redefine these dimensions. It preserves the audit's dimension scores and normalizes them into a first-class score record.

## Relationship To OpenAI Output Quality Audit V1

SignalQualityScore V1 consumes:

`docs/DYSONX_OPENAI_OUTPUT_QUALITY_AUDIT_V1.md`

It reads only an existing OpenAI Output Quality Audit V1 JSON report. It does not read raw provider responses, raw articles, workflow logs, secrets, Notion data, live GitHub data, or website output.

V1 does not rescore raw text unless a future reviewed change requires it. The score is derived from audit output so audit behavior and score behavior remain separable.

## Input Audit Report

CLI:

```bash
python3 scripts/dysonx_signal_quality_score.py \
  --audit-report tmp/dysonx_openai_output_quality_audit.json \
  --output tmp/dysonx_signal_quality_score.json
```

The input audit report must include:

- `audit_version`
- `framework_reference`
- `quality_dimensions`
- `signal_reviews`
- `tier_counts`
- `safety_flags`

Malformed or incomplete input fails closed.

## Output Score Report Schema

The score report contains:

- `score_version`
- `created_at`
- `input_audit_report`
- `framework_reference`
- `audit_reference`
- `signals_scored`
- `score_dimensions`
- `score_records`
- `tier_counts`
- `blocking_risk_counts`
- `recommended_next_actions`
- `safety_flags`

Each score record contains:

- `signal_id`
- `candidate_id`
- `title`
- `source_url`
- `quality_score_total`
- `quality_score_max`
- `quality_score_percent`
- `quality_tier`
- `dimension_scores`
- `critical_risk_flags`
- `noncritical_risk_flags`
- `missing_fields`
- `publish_readiness_candidate`
- `recommended_action`
- `score_explanation`
- `confidence_input_available`
- `requires_confidence_calibration`
- `requires_human_review`
- `correlation_recommended`
- `score_source`

`quality_score_percent` is normalized as:

`quality_score_total / 65`

## Tier And Action Mapping

SignalQualityScore V1 preserves audit tiers when the audit report is valid.

Recommended action mapping:

- Tier A with no critical risk: `candidate_for_human_approval`
- Tier B with no critical risk: `needs_human_review`
- Tier C: `improve_or_regenerate`
- Tier D: `reject_or_regenerate`
- Any critical risk: `blocked_by_quality_risk`

Tier A can become a candidate for future human approval, but it is not publish-ready by itself. Tier B requires human review. Tier C requires improved analysis or regeneration. Tier D should be rejected or regenerated.

## Critical Risk Handling

Critical risks include:

- `missing_source_url`
- `missing_why_it_matters`
- `missing_watch_next`
- `missing_agi_capability`
- `unsupported_publish_readiness`
- `article_like_output`
- `generic_summary`
- `raw_provider_response_present`
- `network_or_live_operation_attempted`

Any critical risk blocks `publish_readiness_candidate`.

This PR does not implement a Publish Readiness Gate. The field is a future-facing score attribute only, and the output safety flag `publish_readiness_enabled` remains false.

## Confidence Calibration Boundary

SignalQualityScore V1 records whether confidence input is available from the audit report. It does not calibrate confidence.

`requires_confidence_calibration` is true by default because future calibration must consider source authority, evidence completeness, claim specificity, cross-source support, contradiction risk, uncertainty labeling, freshness, and whether claims are directly supported or inferred.

## Correlation Boundary

SignalQualityScore V1 may recommend future correlation for Tier A or Tier B signals, or for signals with strong entity / relationship value.

It does not perform correlation. It does not merge sources, compare evidence across sources, or create Knowledge Graph edges.

## Human Approval Boundary

SignalQualityScore V1 does not approve Signals.

Tier A still requires future human approval before any publish-readiness path. Tier B and Tier C require human review or improved analysis. Signals with critical risks are blocked until those risks are resolved.

## Publish-Readiness Boundary

This PR does not enable publish readiness.

Publishing remains blocked until Confidence Calibration V1, Multi-source Correlation V1, Human Approval Gate V1, and Publish Readiness Gate V1 are reviewed and stable.

## Safety Flags

The output safety flags are all false:

- `openai_call_performed`
- `workflow_dispatched`
- `publishing_performed`
- `publish_readiness_enabled`
- `website_pages_written`
- `social_posting_performed`
- `notion_mutation_performed`
- `live_github_api_used`
- `article_body_scraping_performed`
- `raw_provider_response_stored`
- `knowledge_graph_write_performed`
- `prediction_engine_performed`
- `deployment_performed`

## Non-Goals

This PR does not:

- call OpenAI
- require `OPENAI_API_KEY`
- dispatch workflows
- change workflows
- publish content
- enable publish readiness
- generate website pages
- write public content files
- social post
- mutate Notion
- use live GitHub API collection
- scrape article bodies
- require or store raw provider responses
- write Knowledge Graph records
- implement Prediction Engine work
- implement Confidence Calibration
- implement Multi-source Correlation
- implement Human Approval Gate
- implement Publish Readiness Gate
- deploy
- merge itself

## How To Run Locally

Generate the audit fixture from existing safe reports:

```bash
python3 scripts/dysonx_openai_output_quality_audit.py \
  --llm-audit-report tests/fixtures/openai_output_quality_audit_v1/llm_audit_report.json \
  --signal-candidate-report tests/fixtures/openai_output_quality_audit_v1/signal_candidate_report.json \
  --pipeline-report tests/fixtures/openai_output_quality_audit_v1/pipeline_report.json \
  --output tmp/dysonx_openai_output_quality_audit.json
```

Then generate SignalQualityScore V1:

```bash
python3 scripts/dysonx_signal_quality_score.py \
  --audit-report tmp/dysonx_openai_output_quality_audit.json \
  --output tmp/dysonx_signal_quality_score.json
```

## Next Recommended PR

The next recommended PR should be selected after review of score outputs:

- Confidence Calibration V1 if reviewers need better confidence support before using scores.
- Multi-source Correlation V1 if reviewers need cross-source evidence comparison for Tier A/B Signals.

Publishing should remain blocked until both the confidence and correlation boundaries are understood and a separate Human Approval Gate and Publish Readiness Gate exist.
