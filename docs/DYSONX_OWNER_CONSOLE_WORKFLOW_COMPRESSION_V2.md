# DysonX Owner Console Workflow Compression V2

## Purpose

Owner Console Workflow Compression V2 turns the internal Owner Console from a long report into an auto-decision control desk. The Owner should quickly see what needs attention, what the system already handled, where an override may be useful, and how to export structured feedback.

The goal is the ten-second rule: for each Signal, the Owner should be able to answer whether it needs attention, what the system decided, why, what should happen next, and whether an override is needed within roughly 10 seconds.

## Why The Previous Console Was Too Report-Like

The previous console displayed the right fields but expanded too much content by default. Five Signals could feel like a long printed report. Low-value and blocked items received too much visual weight, and Reviewed / Pending status was confusing because Auto Decision already applied system defaults before Owner review.

## Owner Work Summary Model

The first screen now emphasizes Owner work rather than raw report metadata:

* Needs Owner Attention
* Auto-handled
* Candidates
* More Sources
* Regenerate
* Hold
* Rejected
* Overrides
* Ready to export feedback

These counts are derived from the loaded Internal Intelligence Brief fixture and Auto Decision fields.

## System-Decided / Owner-Overridden Status Model

The console uses an automation-aware model:

* System-decided: Signals with a system default Owner decision.
* Owner-overridden: Signals where the Owner changed the default decision.
* Needs Owner attention: Signals worth immediate inspection.
* Total Signals: Signals in the loaded review queue.

The console does not treat every default decision as a manual review.

## Signal Grouping Model

Signals are grouped by work category:

* Needs Owner Attention: high-value candidates and Signals needing more evidence.
* Auto-handled: held or regeneration-needed Signals that do not require immediate Owner inspection.
* Blocked / Low-value: rejected or low-quality Signals shown as compact summaries.

A Signal should not appear with full detail in multiple places.

## Compact Card Default Behavior

Signal cards are compact by default. The visible card shows:

* title
* Auto Decision
* score
* tier
* risk summary
* missing fields
* short why_it_matters
* short watch_next
* Owner decision control
* priority control
* override status

The compact card is intended for fast comparison, not exhaustive reading.

## Expanded Details Behavior

Full technical details live behind an expandable details control. Expanded details may include Signal ID, source URL, source authority, AGI capability, entities, full why_it_matters, full watch_next, and raw internal action values.

Raw technical fields must not dominate the first screen.

## Feedback JSON Behavior

Feedback JSON includes system defaults and Owner overrides. If the Owner changes nothing, the export still records default system decisions for every Signal.

Each record includes:

* auto_decision
* system_default_owner_decision
* selected_owner_decision
* owner_overridden
* priority
* owner_comment
* follow_up_required
* follow_up_note
* publication_approved: false
* publish_readiness_candidate when present

The export states that feedback is not publication approval.

## Safety Boundary

Workflow Compression V2 does not publish, approve publication, generate public pages, write Knowledge Graph records, run Prediction Engine work, perform Confidence Calibration, perform Multi-source Correlation, mutate Notion, use live GitHub APIs, scrape article bodies, call OpenAI, dispatch workflows, deploy, or change production.

Auto Decision remains internal handling guidance only. Publish readiness still requires a future explicit Publish Readiness Gate.

## Non-Goals

This change does not implement:

* persistence
* backend APIs
* public publishing
* public website generation
* Publish Readiness Gate
* OpenAI calls
* workflow dispatch
* deployment
* production changes

## How To Run Locally

From the repository root:

```bash
python3 -m http.server 8090
```

Then open:

```text
http://127.0.0.1:8090/internal/dysonx-owner-intelligence-preview/?v=workflow-compression-v2
```

If port 8090 is busy, use 8091 and adjust the URL.

## Recommended Next Step

If the compressed workflow is usable, the next practical step is Review Session Save V1 / Local Persistence V1 so Owner feedback can be saved without copy/paste friction.

If the console is still too slow to use, do Owner Console Usability Fix V3 before adding persistence.
