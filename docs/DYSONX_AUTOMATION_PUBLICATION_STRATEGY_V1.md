# DysonX Automation and Public Publication Strategy V1

## 1. Purpose

DysonX must move from internal review tooling toward public AGI intelligence surfaces as quickly as quality and safety allow.

The system should automate the majority of Signal handling.

Owner should not become a daily manual editor.

Public publication is the current strategic objective, but it must not bypass quality and safety gates.

This document locks the current direction:

- maximize safe automation
- minimize unnecessary Owner review
- reserve Owner attention for high-value, ambiguous, safety-sensitive, or strategic exceptions
- prevent a few pending Owner-review items from blocking other qualified Signals
- move quickly toward public web publication
- require quality, attribution, safety, and Publish Readiness Gate validation before publication

## 2. Automation Principle

DysonX should automatically handle as many Signals as possible.

The system should auto-classify Signals into:

- `auto_reject`
- `needs_more_sources`
- `needs_regeneration`
- `hold`
- `candidate_for_publish_readiness_review`

The system should auto-handle low-risk cases:

- low-quality rejects
- generic summaries
- missing-source items
- clear regeneration cases
- non-urgent holds
- source-completion requests where deterministic rules apply

Owner review should be reserved for:

- high-value candidates
- ambiguous exceptions
- safety-sensitive items
- strategic judgment calls
- overrides

Automation should reduce repetitive review work. It must not remove the Owner's ability to inspect, override, or reject system decisions.

## 3. Non-Blocking Review Principle

A small number of Signals waiting for Owner review must not block other qualified Signals from progressing.

The pipeline should support parallel states:

- some Signals can wait for Owner review
- some can be rejected
- some can be regenerated
- some can collect more sources
- some can advance to Publish Readiness Candidate
- future approved items can move to Publish Readiness Gate

Do not design the system so all publication progress halts until every item is manually reviewed.

## 4. Public Publication Strategic Objective

Public web publication is the current stage goal.

Target public destination:

- `media.energizeos.com/signals/`
- `media.energizeos.com/signals/<slug>/`
- `media.energizeos.com/trackers/`
- `media.energizeos.com/agi-map/`
- `media.energizeos.com/reports/`

The system should move toward:

```text
Review Session Save
-> Publish Readiness Gate
-> Public Signal Page Generator
-> Public Signals Index
-> Trackers
-> AGI Map
-> Reports
```

Public publication is the strategic target, but the next public-facing implementation must still pass through an explicit Publish Readiness Gate.

## 5. Publish Readiness Gate Requirement

No Signal may be published merely because:

- AutoDecision says `candidate_for_publish_readiness_review`
- Owner says `approve_for_future_publish_readiness_review`
- Review Session was saved
- score is high

Publish Readiness Gate must still verify:

- `source_url` exists
- source attribution is clear
- no copied article body is used
- no raw copyrighted article text is published
- `why_it_matters` exists
- `watch_next` exists
- AGI capability exists
- entities exist
- quality score is sufficient
- no critical risk flags
- no generic summary drift
- public title exists
- public summary exists
- public slug exists
- public metadata exists
- publication history / approval trail exists
- safety flags do not block release

Until that gate exists and passes, `publication_approved` must remain `false`.

## 6. Speed With Safety

DysonX should move quickly.

Speed means reducing unnecessary manual bottlenecks, not bypassing quality gates.

Quality and safety are prerequisites for public credibility.

Speed must not override:

- source attribution
- copyright safety
- Signal quality
- AGI capability mapping
- `why_it_matters`
- `watch_next`
- publication trail
- Publish Readiness Gate

Fast progress should come from deterministic automation, concise Owner exception workflows, and clean handoffs between internal review and future public publication gates.

Fast publication progress also means automating blockers and readiness checks through `docs/DYSONX_PUBLISH_READINESS_GATE_V1.md`, not bypassing the gate.

## 7. Owner Role

Owner is a strategic decision-maker, not a daily manual editor.

Owner should mostly see:

- items requiring strategic judgment
- high-value candidates
- ambiguous exceptions
- safety-sensitive decisions
- override opportunities

Owner should not be required to review every auto-rejected, auto-held, or clearly incomplete Signal.

The Owner Console should remain the place for exception handling, strategic judgment, and review-session capture, not a manual queue for every low-value item.

## 8. Required Future Prompt Language

All future Codex prompts touching DysonX must include this document:

```text
docs/DYSONX_AUTOMATION_PUBLICATION_STRATEGY_V1.md
```

They must also include:

- `docs/DYSONX_PRODUCT_CONSTITUTION.md`
- `docs/DYSONX_SYSTEM_ARCHITECTURE.md`
- `docs/DYSONX_ENGINEERING_GOVERNANCE.md`
- `docs/DYSONX_OWNER_USABILITY_GOVERNANCE.md`
- `docs/DYSONX_PUBLIC_INTELLIGENCE_SURFACES_V1.md`
- `docs/DYSONX_AUTO_DECISION_ENGINE_V1.md`
- `docs/DYSONX_REVIEW_SESSION_SAVE_V1.md`

Future prompts must restate:

- maximize safe automation
- minimize unnecessary Owner review
- do not block all progress on pending Owner review
- public publication is the strategic target
- Publish Readiness Gate is mandatory before publication
- quality and safety remain prerequisites

## 9. Non-Goals

This document does not authorize immediate implementation of:

- public publishing
- automatic publishing
- public website generation
- Publish Readiness Gate implementation
- social posting
- newsletter sending
- Knowledge Graph writes
- Prediction Engine
- Confidence Calibration
- Multi-source Correlation
- OpenAI calls
- workflow dispatch
- deployment
- production changes

This document is governance / strategy only.
