# DysonX Owner Review Wizard V1

## 1. Why Previous Owner Console Attempts Failed

Previous Owner Console iterations exposed the right controls but still required the Owner to infer the workflow. The Owner could complete steps by clicking around without understanding the sequence, which is a product failure.

The failure was interaction design, not missing backend logic.

## 2. Why Wizard Mode Is Required

Wizard mode is required because the Owner review path must behave as one screen, one task, and one primary action. The Owner should not see dense console panels, raw JSON, expanded completed cards, or competing export controls during review.

The advanced console may remain available for inspection, but the primary Owner acceptance path is the wizard.

## 3. One Screen / One Task / One Primary Action Rule

Every wizard screen has exactly one primary action. Secondary actions are visually weaker and support the current task only.

The screen must answer:

- what to do now
- what will happen after clicking
- what did not happen, especially publication

## 4. Wizard Screens

The V1 flow is:

1. Start or resume.
2. Review attention item 1.
3. Review attention item 2.
4. Accept system-handled Signals.
5. Save internal review.
6. Generate Owner Feedback JSON.
7. Download outputs.
8. Complete.

The progress indicator is passive and not clickable.

## 5. Attention Item Review

The Owner sees one attention Signal at a time. Each attention screen shows only the Signal title, short why-it-matters text, system recommendation, score / tier, risk summary, and missing fields.

The primary path is to accept the system recommendation. The Owner may change the decision, add a priority, comment, and follow-up fields, or skip for later.

Skipped attention items remain internal review records. They default to the system decision, set follow-up required, and do not approve publication.

## 6. Auto-Handled Confirmation

The system-handled screen summarizes Signals already handled by deterministic automation, such as hold, regeneration, and rejection.

The Owner is not expected to inspect every auto-handled Signal. The primary action accepts system-handled Signals in one step, while details remain compact and optional.

## 7. Save / Generate / Download Flow

The wizard separates durable review capture from output generation:

- Save Internal Review records the browser-local review state.
- Generate Owner Feedback JSON creates the internal downstream artifact.
- Download Owner Feedback JSON exports the primary output.

Raw JSON is not shown inside the main wizard flow.

## 8. Local Persistence

The wizard uses the localStorage key:

```text
dysonx.ownerReviewWizard.v1
```

It persists:

- `wizard_session_id`
- `current_screen`
- `attention_index`
- `attention_item_statuses`
- `selected_owner_decisions`
- `priority_values`
- `owner_comments`
- `follow_up_required`
- `follow_up_notes`
- `owner_overridden`
- `auto_handled_accepted`
- `internal_review_saved`
- `feedback_generated`
- `feedback_downloaded`
- `session_created_at`
- `session_updated_at`

Starting a new review clears only this wizard key.

## 9. Feedback JSON

Owner Feedback JSON includes:

- `wizard_session_id`
- `owner_review_wizard_version: "v1"`
- `internal_review_complete`
- `auto_handled_accepted`
- `records`
- `publication_approved: false`
- `auto_decision_is_not_publication_approval: true`
- `owner_feedback_is_not_publication_approval: true`
- `review_session_is_not_publication_approval: true`
- `wizard_review_is_not_publication_approval: true`

Each record preserves system defaults, selected Owner decision, override status, priority, comments, follow-up fields, skipped status when applicable, and publish-readiness candidate markers.

## 10. Safety Boundaries

The wizard is local browser review only.

It does not implement:

- Publish Readiness Gate
- public publishing
- automatic publishing
- public website generation
- backend API
- database
- server persistence
- OpenAI call
- workflow dispatch
- deployment
- production changes
- Knowledge Graph writes
- Prediction Engine
- Confidence Calibration
- Multi-source Correlation

Saved wizard review is not publication approval. `publication_approved` remains `false`.

## 11. Non-Goals

This document and PR do not authorize public output, server persistence, backend API work, publish-readiness implementation, public page generation, automation dispatch, OpenAI calls, deployment, or production changes.

## 12. How To Run Locally

From the repository root:

```bash
python3 -m http.server 8093
```

Open:

```text
http://127.0.0.1:8093/internal/dysonx-owner-review-wizard/?v=owner-review-wizard-v1
```

Use a private browser window or clear `dysonx.ownerReviewWizard.v1` to test a clean first-run state.

## 13. Owner Acceptance Criteria

The wizard is acceptable only if the Owner can complete review without asking what to click next.

Acceptance requires:

- one current screen
- one current task
- one primary action
- no raw JSON in the review path
- no completed-step controls
- no future-step controls
- no public publishing implication
- clear completion state

## 14. Recommended Next Step

Owner tests the Wizard.

If Owner can complete the review without asking what to click next, then merge Wizard and proceed to Publish Readiness Gate V1.

If not, keep fixing Wizard.
