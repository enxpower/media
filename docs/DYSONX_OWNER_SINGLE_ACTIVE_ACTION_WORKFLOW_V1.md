# DysonX Owner Single Active Action Workflow V1

## 1. Purpose

Owner Single Active Action Workflow V1 fixes the Owner Console usability failure where too many buttons, highlighted sections, expanded cards, and export controls competed for attention.

The console must behave like an internal operating panel: one current task, one primary action, clear completed state, clear locked state, and a final output action.

This is an Owner Console usability fix only. It does not implement public publishing, Publish Readiness Gate, backend APIs, database storage, OpenAI calls, workflow dispatch, deployment, or production changes.

## 2. Why The Previous Guided Workflow Still Failed

Owner Guided Review Workflow V1 added a stepper and gated actions, but the page could still feel ambiguous:

- multiple actions looked important at once
- completed cards remained visually prominent
- disabled buttons looked broken instead of intentionally locked
- future cards were too visible
- export actions appeared in multiple places
- review-complete state could compete with incomplete-looking controls

The problem was not missing explanatory text. The problem was interaction state.

## 3. Single Active Action Rule

At any moment, the Owner Console must expose exactly one primary action.

Secondary actions may exist only when they support the current task and must be visually subordinate.

The current primary action must be obvious within three seconds.

## 4. Active Task Header

The Active Task Header is the primary operating surface. It shows:

- step number
- current task title
- one sentence instruction
- one primary action
- optional secondary action
- progress text

The rest of the page supports the active task; it must not compete with it.

## 5. One Primary Action Rule

The UI must maintain one primary action marker, such as:

```text
data-primary-action="true"
```

Examples:

- review attention item: Accept system decision and mark done
- override mode: Mark done
- auto-handled step: Accept all auto-handled system decisions
- save step: Save review session locally
- feedback step: Generate Owner Feedback JSON
- output step: Download Owner Feedback JSON

## 6. Collapsed Completed Cards

Completed attention cards collapse to a short summary:

```text
Done -- title -- selected decision -- Edit
```

Completed cards must not keep full forms, full details, or strong highlights visible.

## 7. Collapsed Future Cards

Future attention cards collapse to:

```text
Next -- title -- system suggested decision -- locked until previous item complete
```

Future cards must not expose active controls before they become current.

## 8. Active Card Behavior

Only the active attention card shows the full compact review controls:

- Auto Decision
- score
- tier
- risk summary
- missing fields
- why it matters
- watch next
- Owner decision dropdown
- priority
- comment
- follow-up fields
- active review actions

Only one attention card should be strongly highlighted.

## 9. Auto-Handled Confirmation Behavior

Auto-handled Signals remain collapsed and muted until their step.

During the auto-handled step, the console should show a concise confirmation panel:

```text
These Signals are already system-decided. Accept all unless you disagree.
```

The default primary action is:

```text
Accept all auto-handled system decisions
```

Reviewing details is secondary.

## 10. Save / Feedback / Output Gating

Save, feedback, and output actions must be gated by workflow progress:

- save unlocks after attention and auto-handled steps are complete
- feedback unlocks after session save
- download/copy unlock after feedback generation
- final completion appears only after the output step completes

Locked actions should be explained with text, not shown as unexplained broken buttons.

## 11. Final Completion State

The final state says:

```text
Internal review complete.
No public publishing occurred.
Next future stage: Publish Readiness Gate V1.
```

A completed single-action review is not publication approval.

## 12. Reset / Clear Behavior

Clear saved review must be secondary and labeled for local testing, such as:

```text
Reset local test state
```

It must not sit in the primary path where the Owner may click it accidentally.

## 13. Responsive Usability Requirement

The single active action panel must remain readable on narrow screens.

Metric cards, stepper labels, collapsed summaries, and primary action buttons must not wrap into unreadable fragments.

## 14. Persistence State

The workflow continues to use:

```text
dysonx.ownerConsole.reviewSession.v1
```

Persisted workflow state includes existing Review Session Save fields plus:

- `active_attention_index`
- `override_mode_for_active_item`
- `output_downloaded`
- `output_step_complete`
- `active_primary_action`

Reloading a saved session must restore the correct active task.

## 15. Safety Boundaries

Single Active Action Workflow V1 does not:

- publish content
- approve publication
- generate public website pages
- implement Publish Readiness Gate
- write Knowledge Graph records
- run Prediction Engine work
- perform Confidence Calibration
- perform Multi-source Correlation
- mutate Notion
- use live GitHub APIs
- scrape article bodies
- call OpenAI
- require `OPENAI_API_KEY`
- dispatch workflows
- deploy
- change production

`publication_approved` remains `false`.

## 16. Non-Goals

This PR does not implement:

- backend API
- database
- server persistence
- public publishing
- public website generation
- Publish Readiness Gate implementation
- OpenAI call
- workflow dispatch
- deployment
- production changes

## 17. How To Run Locally

From the repository root:

```bash
python3 -m http.server 8090
```

Then open:

```text
http://127.0.0.1:8090/internal/dysonx-owner-intelligence-preview/?v=single-active-action-v1
```

If port 8090 is busy, use 8091 and adjust the URL.

## 18. Recommended Next Step

Owner tests single active action workflow locally.

If Owner can complete internal review without asking what to click next, proceed to Publish Readiness Gate V1.

If not, fix Owner Console again before Publish Readiness Gate.
