# DysonX Owner Guided Review Workflow V1

## 1. Purpose

Owner Guided Review Workflow V1 turns the internal DysonX Owner Console from a passive control panel into a guided operating workflow. The Owner should always know the current step, what to click now, what is complete, what is locked, and what final export action remains.

This improves internal review usability without implementing public publishing, Publish Readiness Gate, backend APIs, database storage, OpenAI calls, workflow dispatch, deployment, or production changes.

## 2. Why Button Existence Was Not Enough

The previous console exposed the right controls, but the Owner still had to infer the operating sequence. A console can be technically functional and still fail if the Owner has to ask which button to press next.

Guided review makes the workflow explicit:

1. Review attention items.
2. Confirm auto-handled items.
3. Save the review session.
4. Generate Owner Feedback JSON.
5. Download or copy outputs.

## 3. Owner Guided Workflow Model

The primary workflow is:

```text
Review Attention Items
-> Confirm Auto-handled
-> Save Session
-> Generate Feedback
-> Download / Copy
```

The workflow highlights the current action, marks completed steps, and locks future steps until prerequisites are complete.

The guided workflow must behave as a single active action console. Multiple competing highlighted actions, expanded completed cards, or unexplained disabled buttons are product failures.

## 4. Stepper States

Each step has one visible state:

- `active`: current step
- `complete`: finished step
- `locked`: future step unavailable until prerequisites complete

The UI uses text labels and class names, not color alone.

## 5. Current Action Banner

The current action banner tells the Owner what to do next.

Examples:

- Current action: Review the highlighted Signal.
- Current action: Confirm auto-handled Signals.
- Current action: Save the review session.
- Current action: Generate Owner Feedback JSON.
- Current action: Download or copy outputs.
- Complete: Internal review saved and feedback generated. No publication occurred.

## 6. Active Item Highlighting

During Review Attention Items, the active Needs Owner Attention card is highlighted. Completed attention cards show `Done`. Future attention cards show `Next` and stay visually secondary until active.

Only one attention card should be strongly highlighted at a time.

## 7. Per-Card Actions

Each Needs Owner Attention card includes:

- Accept system decision
- Override decision
- Mark done

Accept system decision resets the selected Owner decision to the system default, clears override state, marks the Signal done, and advances the workflow.

Override decision focuses the Owner decision control but does not mark the Signal done. The Owner must choose the decision and click Mark done.

Mark done completes the current Signal and advances to the next attention item.

## 8. Auto-Handled Confirmation

Auto-handled Signals already have system decisions. The Owner should not manually review every auto-rejected, held, or regeneration-needed Signal.

The guided workflow provides:

- Accept all auto-handled system decisions
- Review auto-handled details

The default path is to accept all auto-handled decisions unless the Owner disagrees.

## 9. Save / Generate / Download Gating

Save Session remains locked until attention items and auto-handled confirmation are complete.

Generate Owner Feedback JSON remains locked until the review session is saved.

Download and copy actions remain locked until Owner Feedback JSON exists.

Restored sessions may unlock later steps when their persisted workflow state shows prerequisites are complete.

## 10. Workflow Persistence

The workflow persists locally through the existing key:

```text
dysonx.ownerConsole.reviewSession.v1
```

Persisted workflow fields include:

- `active_step`
- `completed_steps`
- `attention_item_statuses`
- `auto_handled_confirmed`
- `session_saved`
- `feedback_generated`
- `outputs_ready`

Clear Saved Session resets the workflow to Step 1.

## 11. Completion State

After feedback generation, the console shows a completion panel:

- Internal review complete.
- Owner Feedback JSON generated.
- Review Session JSON generated.
- No public publishing occurred.
- No publication approval occurred.
- Next future stage is Publish Readiness Gate V1.

A completed guided review is not publication approval.

## 12. Safety Boundaries

Owner Guided Review Workflow V1 does not:

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

## 13. Non-Goals

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

## 14. How To Run Locally

From the repository root:

```bash
python3 -m http.server 8090
```

Then open:

```text
http://127.0.0.1:8090/internal/dysonx-owner-intelligence-preview/?v=guided-review-workflow-v1
```

If port 8090 is busy, use 8091 and adjust the URL.

## 15. Recommended Next Step

Owner tests guided workflow locally.

If Owner can complete a review without external explanation, proceed to Publish Readiness Gate V1.

If not, do not proceed to Publish Readiness Gate. Do another Owner Console usability fix first.
