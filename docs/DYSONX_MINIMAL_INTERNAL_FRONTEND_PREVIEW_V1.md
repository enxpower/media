# DysonX Minimal Internal Frontend Preview V1

## Purpose

Minimal Internal Frontend Preview V1 is the first local Owner-facing preview for the DysonX internal intelligence loop.

It lets the Owner open a local preview, load an Internal Intelligence Brief V1 JSON fixture, review Signals, choose Owner decisions, enter comments, set priority and follow-up fields, and export Owner Review Feedback V1 JSON.

This is an internal preview only. It is not public publishing, public website generation, social distribution, Knowledge Graph writing, Prediction Engine work, Confidence Calibration, Correlation, workflow automation, or deployment.

## Why This Follows Owner Review Feedback V1

Owner Review Feedback V1 created a structured JSON artifact for Owner decisions.

The next usability gap is that writing feedback JSON by hand is not a realistic Owner workflow. This preview creates a minimal local interface for the same schema so the Owner can test whether the review loop is understandable before DysonX adds persistence or a fuller internal frontend.

The purpose is usability validation, not backend expansion.

## Relationship To Internal Intelligence Brief V1

The preview consumes Internal Intelligence Brief V1 JSON.

It displays:

- brief metadata
- executive summary
- decision-grade candidates
- useful Signals requiring review
- blocked / low-value Signals
- owner review queue
- safety boundary

The preview reads a local fixture at:

`internal/dysonx-owner-intelligence-preview/brief_fixture.json`

It can also load another local JSON file through the browser file picker.

## Relationship To Owner Review Feedback V1

The preview exports JSON matching the Owner Review Feedback V1 schema.

Generated feedback includes:

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

Each feedback record includes:

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

`approve_for_future_publish_readiness_review` remains only later review eligibility. It does not enable publishing or publish readiness.

## How To Run Or Open Locally

From the repository root, run a local static server:

```bash
python3 -m http.server 8080
```

Then open:

```text
http://127.0.0.1:8080/internal/dysonx-owner-intelligence-preview/
```

The page attempts to load the included fixture automatically when served through a local server.

If opening the HTML file directly, use the JSON file picker because some browsers block `file://` fixture fetches.

## What The Owner Can Review

The Owner can review:

- Signal title
- `signal_id`
- tier
- recommended action
- source URL when available
- risk flags when available
- missing fields when available
- safety boundary

For each queue item, the Owner can choose:

- `approve_for_future_publish_readiness_review`
- `request_more_sources`
- `request_regeneration`
- `reject`
- `hold`

The Owner can also enter:

- owner comment
- priority: `high`, `medium`, or `low`
- follow-up required checkbox
- follow-up note

## How Feedback JSON Is Produced

The preview generates JSON in a textarea and enables a local download.

The browser creates the JSON locally. It does not write to production data stores, call APIs, mutate Notion, or dispatch workflows.

The generated JSON should be treated as an internal artifact for review and future iteration.

## Safety Boundaries

The preview explicitly states:

- Internal preview only
- Not publish-ready
- No public publishing
- No website/public content generation
- No social distribution
- No Knowledge Graph writes
- No Prediction Engine work
- No Confidence Calibration
- No Correlation
- No OpenAI call
- No workflow dispatch
- No deployment

The preview does not require `OPENAI_API_KEY`.

It does not expose secrets or require environment variables.

## Non-Goals

This PR does not:

- call OpenAI
- require `OPENAI_API_KEY`
- dispatch workflows
- change workflows
- deploy
- publish content
- generate public website pages
- generate SEO metadata
- generate social post drafts
- mutate Notion
- use live GitHub API collection
- scrape article bodies
- write Knowledge Graph records
- implement Prediction Engine work
- implement Confidence Calibration
- implement Multi-source Correlation
- implement Human Approval Gate
- implement Publish Readiness Gate
- persist feedback in a database
- merge itself

## Known Limitations

- This is a local static preview, not a production application.
- Feedback is generated in the browser and must be downloaded or copied.
- There is no authentication or multi-user review state.
- There is no database persistence.
- Brief field completeness is not improved in this PR.
- The default fixture is a representative local sample, not live production intelligence.

## Recommended Next Step

After usability testing:

- Do Brief Field Completeness V1 if the Owner cannot judge Signals because the brief content is too thin.
- Otherwise do Internal Frontend Persistence V1 or Review Session Save V1 so review sessions can be saved and resumed.

Do not add complex Confidence Calibration, Correlation, Knowledge Graph writes, Prediction Engine work, public publishing, social distribution, or deployment automation until actual Owner review shows those are needed.
