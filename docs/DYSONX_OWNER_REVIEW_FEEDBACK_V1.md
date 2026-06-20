# DysonX Owner Review Feedback V1

## Purpose

Owner Review Feedback V1 captures Owner decisions on Internal Intelligence Brief V1 items as a structured JSON report.

It is an offline deterministic review artifact. It helps DysonX close the minimal usable Owner intelligence loop:

```text
SignalQualityScore
-> Internal Intelligence Brief
-> Owner Review
-> Owner Feedback
-> Improved Brief / Usable Internal Frontend
```

This is internal only. It is not publishing, public content generation, website generation, social distribution, Knowledge Graph writing, Prediction Engine work, Confidence Calibration, Correlation, workflow automation, or deployment.

## Why This Exists Now

Internal Intelligence Brief V1 made scored Signals readable by the Owner.

The Phase 2 Usability Milestone Review identified the next practical missing piece: the Owner can read and judge a brief, but feedback is not yet saved as structured data.

Owner Review Feedback V1 creates that first persistent feedback artifact. It lets the Owner record whether each brief item should be held, rejected, regenerated, supported by more sources, or considered later for a future publish-readiness review.

The goal is product usefulness, not backend layer expansion.

## Relationship To SignalQualityScore V1

SignalQualityScore V1 creates quality score records and tier/action mappings from an existing OpenAI Output Quality Audit V1 report.

Owner Review Feedback V1 does not rescore Signals. It does not change score records. It consumes the downstream Internal Intelligence Brief V1 queue that was derived from SignalQualityScore V1.

An Owner decision can disagree with or refine a score-driven recommendation, but it does not alter the original score report.

## Relationship To Internal Intelligence Brief V1

Internal Intelligence Brief V1 creates an owner-readable brief and an `owner_review_queue`.

Owner Review Feedback V1 reads that existing brief JSON and validates every Owner decision against the brief's `owner_review_queue`.

Every decision `signal_id` must exist in the brief. Unknown Signals fail closed.

## Input Brief JSON

CLI:

```bash
python3 scripts/dysonx_owner_review_feedback.py \
  --brief-json tmp/dysonx_internal_intelligence_brief.json \
  --feedback-input tmp/owner_feedback_input.json \
  --output tmp/dysonx_owner_review_feedback.json
```

The brief input must be an existing Internal Intelligence Brief V1 JSON report with:

- `brief_version`
- `source_score_report`
- `signals_reviewed`
- `owner_review_queue`
- `safety_flags`

The script reads the brief JSON only from the explicit `--brief-json` path.

## Input Owner Feedback JSON

The Owner feedback input contains:

- `reviewer`
- `review_session_id`
- `reviewed_at`
- `brief_version`
- `brief_source`
- `decisions`

Each decision contains:

- `signal_id`
- `owner_decision`
- `owner_comment`
- `priority`
- `follow_up_required`
- `follow_up_note`

Validation rules:

- `reviewer` is required.
- `review_session_id` is required.
- `reviewed_at` is required.
- `brief_version` must match the brief JSON `brief_version`.
- `brief_source` must match or reference the source brief path.
- `decisions` must be a non-empty list.
- Every decision `signal_id` must exist in the brief `owner_review_queue`.
- `owner_decision` must be an allowed value.
- `priority` must be an allowed value.
- `owner_comment` may be empty but must exist.
- `follow_up_required` must be boolean.
- `follow_up_note` may be empty but must exist.

Malformed or incomplete input fails closed.

## Output Feedback Report Schema

The output JSON contains:

- `feedback_version`
- `created_at`
- `reviewer`
- `review_session_id`
- `reviewed_at`
- `source_brief`
- `brief_version`
- `signals_reviewed`
- `decisions_recorded`
- `decision_counts`
- `follow_up_required_count`
- `feedback_records`
- `recommended_next_actions`
- `safety_flags`

Each feedback record contains:

- `signal_id`
- `title`
- `original_tier`
- `original_recommended_action`
- `owner_decision`
- `owner_comment`
- `priority`
- `follow_up_required`
- `follow_up_note`
- `resulting_status`
- `next_action`

## Allowed Decisions

Allowed `owner_decision` values:

- `approve_for_future_publish_readiness_review`
- `request_more_sources`
- `request_regeneration`
- `reject`
- `hold`

Allowed `priority` values:

- `high`
- `medium`
- `low`

No decision is treated as publication permission.

`approve_for_future_publish_readiness_review` means only that the Signal may later enter a separate reviewed publish-readiness process after missing gates exist. It does not make the Signal publish-ready.

## Resulting Status Mapping

- `approve_for_future_publish_readiness_review` -> `owner_approved_for_later_publish_readiness_review_only`
- `request_more_sources` -> `needs_more_sources`
- `request_regeneration` -> `needs_regeneration`
- `reject` -> `owner_rejected`
- `hold` -> `owner_hold`

## Next Action Mapping

- `approve_for_future_publish_readiness_review` -> `later_publish_readiness_review_required`
- `request_more_sources` -> `collect_or_attach_more_sources`
- `request_regeneration` -> `regenerate_or_improve_signal_analysis`
- `reject` -> `remove_from_current_review_queue`
- `hold` -> `keep_for_later_review`

## Safety Boundaries

The output safety flags are all false:

- `openai_call_performed`
- `workflow_dispatched`
- `publishing_performed`
- `publish_readiness_enabled`
- `public_content_generated`
- `website_pages_written`
- `social_posting_performed`
- `notion_mutation_performed`
- `live_github_api_used`
- `article_body_scraping_performed`
- `raw_provider_response_stored`
- `knowledge_graph_write_performed`
- `prediction_engine_performed`
- `confidence_calibration_performed`
- `correlation_performed`
- `deployment_performed`

The tool does not require `OPENAI_API_KEY`.

It reads only explicit local JSON inputs and writes only the requested output JSON report.

## Non-Goals

This PR does not:

- call OpenAI
- require `OPENAI_API_KEY`
- dispatch workflows
- change workflows
- publish content
- enable publish readiness
- generate public content
- generate website pages
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
- deploy
- merge itself

## How To Run Locally

Run the tool against fixture inputs:

```bash
python3 scripts/dysonx_owner_review_feedback.py \
  --brief-json tests/fixtures/owner_review_feedback_v1/internal_intelligence_brief.json \
  --feedback-input tests/fixtures/owner_review_feedback_v1/owner_feedback_input.json \
  --output tmp/dysonx_owner_review_feedback.json
```

The output is a local internal JSON report for audit and reuse.

## Next Recommended Step

After reviewing Owner Review Feedback V1 output, choose the next practical PR based on actual usefulness:

- Brief Field Completeness V1 if the brief is too thin for good Owner decisions.
- Minimal Internal Frontend Preview V1 if the brief and feedback artifacts are sufficient and the next bottleneck is usability.

Default recommendation: Brief Field Completeness V1 if the Owner cannot judge Signals from the current brief; otherwise Minimal Internal Frontend Preview V1.

Publishing, correlation, confidence calibration, Knowledge Graph writes, Prediction Engine work, and deployment remain blocked unless separately authorized.
