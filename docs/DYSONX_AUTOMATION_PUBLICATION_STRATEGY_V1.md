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

## 5. Functional Publishing Before Aesthetic Polish

Current strategic priority is to complete the safe, controllable, verifiable public publishing path.

Core rule:

```text
Functional publishing before aesthetic polish;
quality and safety gates before public release.
```

Current mainline:

```text
Owner Review Wizard
-> Publish Readiness Gate
-> Public Signal Page Generator
-> Public Signals Index
-> Local Public Preview
-> Manual Publish Approval
-> media.energizeos.com
```

Owner Console and Owner Review Wizard UI can be improved later in a dedicated UI/UX sprint. The current Wizard is acceptable for this stage if it is usable enough for the Owner to complete internal review.

Public Signal page visual polish can also be improved later in a dedicated UI/UX sprint. V1 public pages may be visually simple, but they must be credible, clear, structured, source-attributed, copyright-safe, previewable, quality-gated, and not misleadingly published.

Do not let Owner Console UI/UX polish block Publish Readiness Gate V1 or Public Signal Page Generator V1 unless the Owner workflow becomes unusable.

Do not let Public Page visual polish block the publication mainline unless it blocks trust, safety, attribution, basic readability, or publication clarity.

Speed means moving through the governed publication pipeline, not skipping gates.

This priority does not weaken:

- Publish Readiness Gate
- source attribution
- copyright safety
- quality score requirements
- risk blockers
- public metadata requirements
- manual publish approval before production release

## 6. Publish Readiness Gate Requirement

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

## 7. Speed With Safety

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

Step 2 of the strict 5-Step Final Launch Plan is `docs/DYSONX_PUBLIC_SIGNAL_PAGE_GENERATOR_V1.md`: Public Signal Page Generator V1, Public Signals Index V1, and Local Public Preview V1. This step creates static draft preview artifacts only; generated drafts and local preview are not publication, do not replace Manual Publish Approval V1, and must remain visually simple while preserving credibility, readability, attribution, copyright safety, and gate approval.

Step 3 of the strict 5-Step Final Launch Plan is `docs/DYSONX_MANUAL_PUBLISH_APPROVAL_V1.md`: Manual Publish Approval V1. This step consumes the Step 2 generator manifest plus explicit Owner approval input and emits an approval report for Step 4 Production Publish Pack. It does not publish, deploy, dispatch workflows, call OpenAI, or modify generated public HTML. `approved_for_production_pack` is not `published`; production release still requires Step 4 and Step 5.

Step 4 of the strict 5-Step Final Launch Plan is `docs/DYSONX_PRODUCTION_PUBLISH_PACK_V1.md`: Production Publish Pack V1 and Release Guard Integration V1. This step consumes Step 2 generated public pages and Step 3 manual approval, packages only approved pages, and emits release guard evidence for Step 5. It does not publish to production, deploy, dispatch workflows, call OpenAI, write to `media.energizeos.com`, or mark `published` or `production_publish_performed` true. Step 5 explicit Owner launch authorization remains required.

Step 5 of the strict 5-Step Final Launch Plan is `docs/DYSONX_FIRST_PUBLIC_LAUNCH_V1.md`: First Public Launch V1. This step consumes the Step 4 production publish pack and release guard report, requires explicit Owner launch authorization, and copies only approved static Signal pages into the repository public static output path. It may mark launched pages `published: true` and `production_publish_performed: true` only inside public-safe launch metadata. It does not call OpenAI, scrape, manually dispatch workflows, add backend/database systems, perform social/newsletter distribution, or create Step 6.

## 8. Owner Role

Owner is a strategic decision-maker, not a daily manual editor.

Owner should mostly see:

- items requiring strategic judgment
- high-value candidates
- ambiguous exceptions
- safety-sensitive decisions
- override opportunities

Owner should not be required to review every auto-rejected, auto-held, or clearly incomplete Signal.

The Owner Console should remain the place for exception handling, strategic judgment, and review-session capture, not a manual queue for every low-value item.

## 9. Required Future Prompt Language

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
- Functional publishing before aesthetic polish
- Quality and safety gates before public release
- Owner Wizard UI polish is a later sprint
- Public page visual polish is a later sprint
- current mainline is Owner Review Wizard -> Publish Readiness Gate -> Public Signal Page Generator -> Public Signals Index -> Local Public Preview -> Manual Publish Approval -> media.energizeos.com
- do not continue polishing internal UI unless it blocks usability
- do not continue polishing public UI unless it blocks trust, safety, attribution, basic readability, or publication clarity
- Publish Readiness Gate is mandatory before publication
- quality and safety remain prerequisites

## 10. Non-Goals

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
