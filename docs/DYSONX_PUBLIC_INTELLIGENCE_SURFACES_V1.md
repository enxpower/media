# DysonX Public Intelligence Surfaces V1

## 1. Purpose

DysonX backend processing creates intelligence-grade Signal objects.

The Owner Console is an internal decision and exception-handling workbench.

The public website is not a mirror of all collected information.

The public website displays only published AGI intelligence assets that passed quality and publish readiness gates.

The core purpose is to convert AI / AGI information overload into structured, trusted, high-value public intelligence assets.

## 2. One-Sentence Definition

DysonX public surfaces publish selected, verified, structured AGI Signals, Trackers, AGI Maps, and Reports after internal scoring, automatic decisioning, Owner exception handling, and publish readiness validation.

## 3. Core System Chain

Canonical chain:

```text
Source Collection
-> RawItem
-> SignalCandidate
-> IntelligenceSignal
-> QualityAudit
-> SignalQualityScore
-> AutoDecision
-> Internal Intelligence Brief
-> Owner Console
-> Publish Readiness Gate
-> Public Intelligence Surface
```

Earlier stages are internal. They are evidence, analysis, scoring, judgment, and review layers. They must not be made directly public.

Only the final Public Intelligence Surface may be public, and only after the Publish Readiness Gate exists and passes.

## 4. Backend Responsibility

Backend is the intelligence factory and judgment engine.

Backend owns:

- source collection
- safe artifact storage
- LLM understanding after collection
- SignalCandidate generation
- IntelligenceSignal generation
- quality audit
- SignalQualityScore
- AutoDecision
- Internal Intelligence Brief generation
- future Publish Readiness Gate checks
- future public artifact generation only after readiness gates

Backend must answer:

- What happened?
- Which source proves it?
- Which entity is involved?
- Which AGI capability is affected?
- Why does it matter?
- What should be watched next?
- What is the quality score?
- What is the automatic decision?
- What blocks publication?

Backend must not become an RSS mirror, article scraper, generic summary generator, or public spam engine.

## 5. Owner Console Responsibility

Owner Console is internal.

Owner Console owns:

- high-value candidate review
- exception handling
- Owner override
- strategic judgment
- feedback capture
- review session output
- deciding whether something may enter Publish Readiness Gate

Owner is not supposed to manually decide every Signal every day.

The system should automatically handle most Signals.

Owner should mainly inspect:

- high-value candidates
- ambiguous exceptions
- strategically important Signals
- cases where system decision should be overridden

Owner Console must not be publicly exposed without access control.

## 6. Publish Readiness Gate Responsibility

Publish Readiness Gate is the required boundary between internal judgment and public publication.

A Signal must not become public merely because:

- it has a good score
- AutoDecision marks it as `candidate_for_publish_readiness_review`
- Owner marked it `approve_for_future_publish_readiness_review`

Those statuses mean later review only.

Publish Readiness Gate must verify:

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

Only after Publish Readiness Gate may an item become Ready to Publish.

Public Signal Page Generator V1 must only consume Signals that pass `docs/DYSONX_PUBLISH_READINESS_GATE_V1.md`. Passing that gate means ready for future public generation; it does not mean published.

Public Signal Page Generator V1 is governed by `docs/DYSONX_PUBLIC_SIGNAL_PAGE_GENERATOR_V1.md`. It creates static draft / local preview artifacts only. Generated page drafts and local preview are not publication, and Manual Publish Approval V1 remains required before production release.

Manual Publish Approval V1 is governed by `docs/DYSONX_MANUAL_PUBLISH_APPROVAL_V1.md`. It creates an offline approval report for Step 4 Production Publish Pack only; it does not publish, deploy, dispatch workflows, call OpenAI, or modify generated public HTML. `approved_for_production_pack` must not be treated as `published`.

Production Publish Pack V1 is governed by `docs/DYSONX_PRODUCTION_PUBLISH_PACK_V1.md`. It creates production-ready artifacts for Step 5 only. It does not write to `media.energizeos.com`, deploy, publish, dispatch workflows, call OpenAI, or mark `published` true. Step 5 explicit Owner launch authorization remains required.

First Public Launch V1 is governed by `docs/DYSONX_FIRST_PUBLIC_LAUNCH_V1.md`. It may copy only approved, release-guarded static Signal pages into the repository public static output path after explicit Owner launch authorization. It does not call OpenAI, scrape, manually dispatch workflows, perform social/newsletter distribution, add backend/database systems, or create a Step 6.

## 7. Public Website Responsibility

Public website is the external product surface.

It should display:

- Published Signals
- Trackers
- AGI Capability Map
- Reports
- About / methodology pages

It must not display:

- raw backend JSON
- raw provider responses
- unreviewed SignalCandidates
- Owner Console decisions
- internal review states
- draft feedback JSON
- unpublished Signals
- scraped article bodies
- weak-source summaries
- generic AI news lists
- internal safety flags
- internal queue state

The public website is not the intelligence factory.

It is the presentation layer for already-qualified public intelligence assets.

## 8. Functional Public Surface V1 Priority

Public surface V1 should prioritize safe and credible publication structure before final visual polish.

Public UI/UX refinement is a later dedicated sprint. V1 public pages may be simple, but they must still satisfy:

- source attribution
- copyright safety
- public metadata
- quality-gate requirements
- basic readability
- no exposure of internal state
- no misleading publication status

## 9. Public Surface Types

### A. Signals

A public Signal is a short, structured intelligence card or page.

It should include:

- title
- public summary
- source attribution
- source authority
- why it matters
- affected AGI capability
- entities
- DysonX take
- watch next
- related Signals
- related Trackers
- published time
- updated time

A Signal is not a generic article.

A Signal should be concise, evidence-linked, and judgment-oriented.

### B. Trackers

Trackers are long-term intelligence assets.

Examples:

- OpenAI Tracker
- Anthropic Tracker
- Google DeepMind Tracker
- Nvidia AI Infrastructure Tracker
- Agent Infrastructure Tracker
- Robotics Foundation Model Tracker
- AI Safety Policy Tracker
- Open Source Model Tracker

Trackers should include:

- recent published Signals
- timeline
- capability movement
- entity movement
- DysonX interpretation
- watch next
- related reports
- risk / uncertainty notes

Trackers are not company profile pages.

They are living intelligence views.

### C. AGI Capability Map

The AGI Map organizes public intelligence by capability, not news category.

Examples:

- Reasoning
- Planning
- Memory
- World Models
- Agents
- Tool Use
- Robotics
- Multimodal
- Self-Improvement
- AI Safety
- Compute
- Data
- Open Source
- Policy
- Infrastructure
- Evaluation
- Alignment

Each capability page should show:

- recent Signals
- relevant entities
- capability movement
- key evidence
- DysonX interpretation
- watch next

### D. Reports

Reports synthesize multiple Signals.

Examples:

- Daily AGI Signal Brief
- Weekly AGI Intelligence Report
- Monthly AGI Capability Map Update
- Company Strategy Brief
- Research-to-Business Translation
- Policy Impact Brief

Reports should answer:

- What changed?
- Which Signals mattered?
- Which capabilities moved?
- Which entities changed direction?
- What was noise?
- What should be watched next?

Reports are the most commercializable public asset.

## 10. Recommended Public Routes

Recommended public routes:

- `/`
- `/signals/`
- `/signals/<slug>/`
- `/trackers/`
- `/trackers/openai/`
- `/trackers/anthropic/`
- `/trackers/google-deepmind/`
- `/trackers/nvidia-ai-infrastructure/`
- `/agi-map/`
- `/agi-map/agents/`
- `/agi-map/tool-use/`
- `/agi-map/robotics/`
- `/reports/`
- `/reports/weekly-agi-intelligence-YYYY-MM-DD/`
- `/about/`
- `/methodology/`

Internal routes:

- `/internal/owner-console/`
- `/internal/review/`
- `/internal/briefs/`

Internal routes must require access control before any public deployment.

## 11. Public Publication State Machine

Canonical state machine:

```text
Raw Signal
-> Scored
-> Auto Decision
-> Internal Brief
-> Owner Reviewed or Auto Handled
-> Publish Readiness Candidate
-> Publish Readiness Gate
-> Ready to Publish
-> Published
```

Only Published items appear on public surfaces.

`candidate_for_publish_readiness_review` is not publication approval.

`approve_for_future_publish_readiness_review` is not publication approval.

`publication_approved` must remain false until a future explicit Publish Readiness Gate exists and passes.

## 12. Public Signal Page Template

A public Signal page should include:

- Title
- Signal Summary
- Source
- Why It Matters
- AGI Capability Impact
- Entities
- DysonX Take
- Watch Next
- Related Signals
- Related Trackers
- Published / Updated Time

Public Signal pages should be short, dense, structured, and evidence-linked.

They should not become long generic AI blog posts.

## 13. Tracker Page Template

A Tracker page should include:

- Tracker name
- Current direction
- Recent Signals
- Capability movement
- Entity movement
- Timeline
- Watch next
- Risks / uncertainties
- Related reports

## 14. Report Page Template

A Report page should include:

- Executive Summary
- Top Signals
- Capability Map Changes
- Company / Entity Movements
- Research Signals
- Policy / Safety Signals
- What Was Noise
- Watch Next
- Related Signals and Trackers

## 15. Owner Role In The Public Loop

Owner is not a daily manual editor.

Owner is a strategic decision-maker.

Owner should inspect high-value candidates and exceptions, not all Signals.

System should automatically handle 80-90% of low-value, incomplete, or blocked Signals.

Owner should mainly decide:

- whether a high-value candidate should proceed
- whether an exception deserves more sources
- whether a system decision should be overridden
- whether a Signal belongs in a report or tracker

## 16. Public Launch Sequence

Recommended sequence:

1. Auto Decision Engine V1
2. Owner Console Auto Decision Workflow
3. Review Session Save / Local Persistence V1
4. Publish Readiness Gate V1
5. Public Signal Page Generator V1
6. `/signals/` public index
7. Tracker index
8. AGI Capability Map
9. Weekly Report
10. Controlled limited auto-publish only after gates prove stable

Do not skip Publish Readiness Gate.

## 17. Forbidden Drift

Explicitly forbidden:

- public RSS mirror
- AI news blog
- generic article summaries
- SEO spam
- raw scraped article publishing
- public posting from unreviewed SignalCandidates
- exposing Owner Console publicly without access control
- publishing based only on score
- publishing based only on Owner preliminary approval
- publishing without source attribution
- publishing without AGI capability mapping
- publishing without `why_it_matters`
- publishing without `watch_next`
- volume-over-value publishing

## 18. Prompt Requirement

All future Codex prompts that touch DysonX public website, public publishing, Signals, Trackers, AGI Map, Reports, Owner Console, AutoDecision, Publish Readiness Gate, or public content generation must include this document in the mandatory reading list:

```text
docs/DYSONX_PUBLIC_INTELLIGENCE_SURFACES_V1.md
```

This document must be read together with:

- `docs/DYSONX_PRODUCT_CONSTITUTION.md`
- `docs/DYSONX_SYSTEM_ARCHITECTURE.md`
- `docs/DYSONX_ENGINEERING_GOVERNANCE.md`
- `docs/DYSONX_OWNER_USABILITY_GOVERNANCE.md`
- `docs/DYSONX_AUTO_DECISION_ENGINE_V1.md`
- `docs/DYSONX_AUTOMATION_PUBLICATION_STRATEGY_V1.md`

Automation and public publication strategy is governed by:

```text
docs/DYSONX_AUTOMATION_PUBLICATION_STRATEGY_V1.md
```

## 19. Non-Goals

This document does not authorize implementation of:

- public publishing
- automatic publishing
- Publish Readiness Gate implementation
- public website generation
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

This document is architecture / governance only.
