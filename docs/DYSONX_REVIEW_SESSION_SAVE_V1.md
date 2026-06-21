# DysonX Review Session Save V1

## Purpose

Review Session Save V1 adds local browser persistence to the internal DysonX Owner Console. It lets the Owner save, restore, clear, download, and resume a review session after changing decisions, priorities, comments, follow-up flags, or follow-up notes.

This creates a local decision trail for future Publish Readiness Gate work without publishing, approving publication, writing to a server, or using a database.

## Why Local Review Persistence Is Needed Before Daily Use

The Owner Console now supports Auto Decision and a compressed decision workflow, but review work is not durable if the page refreshes. Daily use requires the Owner to safely resume review state without manually rebuilding decisions or comments.

Local persistence removes that friction while keeping the feature internal and browser-only.

## Relationship To Auto Decision Engine V1

Auto Decision Engine V1 supplies conservative system defaults such as `auto_reject`, `needs_more_sources`, `needs_regeneration`, `hold`, and `candidate_for_publish_readiness_review`.

Review Session Save V1 preserves the Owner's selected decision alongside the system default so later review can see where the Owner accepted or overrode automation.

## Relationship To Owner Console Workflow Compression V2

Workflow Compression V2 made the console usable as an auto-decision control desk. Review Session Save V1 makes that control desk resumable by saving compact-card form values and override status in local browser storage.

Review Session Save must be embedded in a guided workflow. The Owner should not have to infer which button to press next.

## Relationship To Owner Feedback JSON

Owner Feedback JSON remains the exportable structured feedback artifact. Review Session Save V1 integrates with it by preserving the same selected/default decision state and including review session metadata in generated feedback JSON.

## Relationship To Future Publish Readiness Gate

A future Publish Readiness Gate will need a decision trail showing system defaults, Owner overrides, comments, follow-up requirements, and session metadata.

Review Session Save V1 creates that trail locally. It does not implement the Publish Readiness Gate.

## Why Saved Sessions Are Not Publication Approval

A saved review session is not publication approval.

A saved review session does not publish, does not approve publication, and does not generate public pages.

In V1:

- `publication_approved` remains `false`
- `auto_decision_is_not_publication_approval` is `true`
- `owner_feedback_is_not_publication_approval` is `true`
- `review_session_is_not_publication_approval` is `true`

The strongest allowed meaning remains later review only.

## Review Session Schema

The saved session contains:

- `review_session_version`
- `review_session`
- `last_saved_at`
- `source_brief`
- `records`
- `generated_feedback_json`
- safety statements

The `review_session` metadata includes:

- `review_session_id`
- `created_at`
- `updated_at`
- `console_version`
- `brief_id`
- `source_brief_title`
- `source_fixture`
- `total_signals`
- `system_decided_count`
- `owner_overridden_count`
- `needs_owner_attention_count`
- `saved_locally`
- `publication_approved`

Each record includes the Signal ID, system default decision, selected Owner decision, override status, priority, Owner comment, follow-up values, publish-readiness candidate marker, and `publication_approved: false`.

## LocalStorage Behavior

The console uses this namespaced key:

```text
dysonx.ownerConsole.reviewSession.v1
```

The browser stores only local review state. It must not store secrets, API keys, raw provider responses, article bodies, or production data.

## Auto-Save Behavior

The console auto-saves when the Owner changes:

- decision dropdown
- priority
- Owner comment
- follow-up required
- follow-up note

The UI shows a saved/restored status and last saved timestamp.

## Save / Load / Clear / Download Controls

Review Session Save V1 adds:

- Save Review Session
- Load Saved Session
- Clear Saved Session
- Download Session JSON

Clear Saved Session removes only this console's localStorage state and restores system defaults. It does not change fixtures, code, server data, or public content.

## Safety Boundaries

This feature is local-only and browser-only. It does not call OpenAI, require `OPENAI_API_KEY`, dispatch workflows, publish content, approve publication, generate public pages, write Knowledge Graph records, run Prediction Engine work, mutate Notion, use live GitHub APIs, scrape article bodies, deploy, or change production.

## Non-Goals

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

## How To Run Locally

From the repository root:

```bash
python3 -m http.server 8090
```

Then open:

```text
http://127.0.0.1:8090/internal/dysonx-owner-intelligence-preview/?v=review-session-save-v1
```

If port 8090 is busy, use 8091 and adjust the URL.

## Recommended Next Step

If the Owner confirms saved sessions are usable, the next practical step is Publish Readiness Gate V1.

If local persistence creates confusion, do Owner Console Usability Fix V3 before adding publish-readiness logic.
