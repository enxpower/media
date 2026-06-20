# DysonX Internal Intelligence Brief V1

## Purpose

Internal Intelligence Brief V1 turns an existing SignalQualityScore V1 report into an owner-readable internal brief.

It produces:

- a Markdown brief for human review
- a JSON brief report for audit and reuse

This brief is internal owner-review output only. It is not publishing, public content, a website page, social distribution, Knowledge Graph writing, Prediction Engine work, workflow automation, or deployment.

## Why This Exists Now

DysonX has added the first quality layers after the V1 OpenAI orchestrator smoke milestone:

- Signal Quality Framework V1
- OpenAI Output Quality Audit V1
- SignalQualityScore V1

Those layers are useful only if the owner can read the resulting intelligence and judge what is worth improving, correlating, rejecting, or eventually routing into a future approval path.

Internal Intelligence Brief V1 is the first owner-usable internal review surface. It keeps DysonX from accumulating internal scores without producing decision value.

## Relationship To Signal Quality Framework V1

The brief uses the quality tiers and quality intent defined by:

`docs/DYSONX_SIGNAL_QUALITY_FRAMEWORK_V1.md`

It does not redefine quality dimensions. It summarizes scored Signals so the owner can review decision-grade candidates, useful Signals requiring review, and blocked or low-value Signals.

## Relationship To OpenAI Output Quality Audit V1

The brief does not read OpenAI outputs directly.

OpenAI Output Quality Audit V1 remains the deterministic audit layer over already-generated safe reports. Internal Intelligence Brief V1 consumes only the downstream SignalQualityScore V1 report.

It does not call OpenAI, require `OPENAI_API_KEY`, read raw provider responses, scrape articles, or inspect workflow logs.

## Relationship To SignalQualityScore V1

The brief consumes:

`docs/DYSONX_SIGNAL_QUALITY_SCORE_V1.md`

SignalQualityScore V1 creates the first-class score records. Internal Intelligence Brief V1 converts those records into an owner review queue.

The brief preserves the boundary that `publish_readiness_candidate` is not publication permission. It does not approve Signals and does not enable publish readiness.

## Input Score Report

CLI:

```bash
python3 scripts/dysonx_internal_intelligence_brief.py \
  --score-report tmp/dysonx_signal_quality_score.json \
  --output-md tmp/dysonx_internal_intelligence_brief.md \
  --output-json tmp/dysonx_internal_intelligence_brief.json
```

The input must be an existing SignalQualityScore V1 JSON report containing:

- `score_version`
- `created_at`
- `input_audit_report`
- `signals_scored`
- `score_records`
- `tier_counts`
- `recommended_next_actions`
- `safety_flags`

Malformed or incomplete input fails closed.

## Markdown Output Structure

The Markdown brief includes:

1. Brief Metadata
2. Executive Summary
3. Decision-Grade Candidates
4. Useful Signals Requiring Review
5. Blocked / Low-Value Signals
6. Owner Review Queue
7. Next Actions
8. Safety Boundary

The Markdown brief is written only to the explicit `--output-md` path provided by the caller.

It must not be placed under public website content directories by default. It does not generate SEO metadata, social drafts, or public pages.

## JSON Output Schema

The JSON brief contains:

- `brief_version`
- `created_at`
- `source_score_report`
- `generated_for`
- `signals_reviewed`
- `tier_counts`
- `blocked_count`
- `human_review_count`
- `correlation_recommended_count`
- `overall_recommendation`
- `decision_grade_candidates`
- `useful_review_queue`
- `blocked_or_low_value`
- `owner_review_queue`
- `recommended_next_actions`
- `safety_flags`

## Owner Review Queue

The owner review queue is a decision aid, not an approval system.

Each row includes:

- `signal_id`
- `title`
- `tier`
- `action`
- `owner_decision_placeholder`

Allowed placeholders:

- `approve_for_future_publish_readiness_review`
- `request_more_sources`
- `request_regeneration`
- `reject`
- `hold`

No Signal is auto-approved. The placeholder `approve_for_future_publish_readiness_review` means only that the owner may choose to route the Signal into a future reviewed publish-readiness workflow after missing gates exist.

## Safety Boundaries

The output safety flags are all false:

- `openai_call_performed`
- `workflow_dispatched`
- `publishing_performed`
- `public_content_generated`
- `website_pages_written`
- `social_posting_performed`
- `notion_mutation_performed`
- `live_github_api_used`
- `article_body_scraping_performed`
- `raw_provider_response_stored`
- `knowledge_graph_write_performed`
- `prediction_engine_performed`
- `deployment_performed`

The Markdown brief explicitly states:

- No publishing performed
- No public content generated
- No website pages written
- No social posts generated
- No OpenAI call performed
- No workflow dispatched
- No Notion mutation
- No live GitHub API used
- No Knowledge Graph writes
- No Prediction Engine work
- No deployment performed

## Non-Goals

This PR does not:

- call OpenAI
- require `OPENAI_API_KEY`
- dispatch workflows
- change workflows
- publish content
- enable publish readiness
- generate public website pages
- generate SEO metadata
- generate social post drafts
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
- auto-approve any Signal
- deploy
- merge itself

## How To Run Locally

Generate a SignalQualityScore V1 report from an existing safe audit report:

```bash
python3 scripts/dysonx_signal_quality_score.py \
  --audit-report tests/fixtures/signal_quality_score_v1/openai_output_quality_audit.json \
  --output tmp/dysonx_signal_quality_score.json
```

Generate the internal brief:

```bash
python3 scripts/dysonx_internal_intelligence_brief.py \
  --score-report tmp/dysonx_signal_quality_score.json \
  --output-md tmp/dysonx_internal_intelligence_brief.md \
  --output-json tmp/dysonx_internal_intelligence_brief.json
```

## Next Recommended Step

The next recommended step should be selected after reviewing whether the brief is actually useful to the owner:

- Owner Review Feedback V1 if the brief successfully helps the owner make review decisions.
- Lightweight Confidence Notes V1 if the brief shows that confidence context is too thin for useful owner judgment.

Publishing should remain blocked until Confidence Calibration, Multi-source Correlation, Human Approval Gate, and Publish Readiness Gate work exists and is reviewed separately.
