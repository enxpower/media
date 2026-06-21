# DysonX Auto Decision Engine V1

## 1. Purpose

Owner should not manually decide every Signal every day.

Auto Decision Engine V1 converts an existing SignalQualityScore V1 report into conservative internal handling decisions so the Owner can focus on exceptions, high-value candidates, overrides, and structured feedback.

The goal is workload reduction inside the minimal usable Owner intelligence loop. This is not publishing automation.

## 2. Relationship To Existing System

Auto Decision Engine V1 sits after SignalQualityScore V1:

```text
SignalQualityScore
-> Auto Decision Engine
-> Internal Intelligence Brief
-> Owner Console
-> Owner Review Feedback
```

Relationship to existing artifacts:

- SignalQualityScore V1 provides scored records, tiers, risks, missing fields, and recommended actions.
- Internal Intelligence Brief V1 remains the Owner-readable brief surface.
- Owner Review Feedback V1 remains the structured feedback artifact.
- Owner Console MVP uses Auto Decision values to default the Owner workflow and reduce manual choices.

Auto Decision Engine V1 does not rescore Signals and does not replace Owner judgment.

## 3. Auto Decision Rules

The engine assigns exactly one internal decision per Signal:

- `auto_reject`
- `needs_more_sources`
- `needs_regeneration`
- `hold`
- `candidate_for_publish_readiness_review`

Rules are deterministic and conservative. The engine does not call an LLM, does not invent probabilistic confidence, and does not perform live research.

### auto_reject

Applied when a Signal is too weak or unsafe for Owner review, including:

- Tier D or reject / blocked tier
- total score below 28
- critical `generic_summary`
- critical `missing_source_url`
- missing source URL
- very low Anti-Garbage Risk score
- clearly generic content that cannot support an Owner decision

Recommended next action:

```text
remove_from_current_review_queue
```

Decision label:

```text
Reject automatically
```

### needs_regeneration

Applied when the source may be usable but the analysis is too thin, including:

- Tier C / needs-review quality
- missing `why_it_matters`
- missing `watch_next`
- missing `agi_capability`
- missing `owner_decision_implication`
- `recommended_action` is `improve_or_regenerate`

Recommended next action:

```text
regenerate_or_improve_signal_analysis
```

Decision label:

```text
Regenerate analysis
```

### needs_more_sources

Applied when the Signal is useful but evidence support is incomplete, including:

- weak or secondhand source authority
- missing first-source evidence
- weak attribution risk flags
- risk summary says more evidence or more source support is needed
- useful score with incomplete evidence or correlation context

Recommended next action:

```text
collect_or_attach_more_sources
```

Decision label:

```text
Need more sources
```

### candidate_for_publish_readiness_review

Applied only when all are true:

- Tier A / decision-grade
- total score is at least 52
- no critical risk flags
- source URL exists
- `why_it_matters` exists
- `watch_next` exists
- `agi_capability` exists
- no unresolved critical evidence gap appears in the risk summary

Recommended next action:

```text
later_publish_readiness_review_required
```

Decision label:

```text
Candidate for later readiness review
```

### hold

Applied when no stronger action is triggered.

Typical cases:

- Tier B useful but not urgent
- useful but not sufficiently supported for readiness review
- requires later correlation
- not immediately actionable

Recommended next action:

```text
keep_for_later_review
```

Decision label:

```text
Hold
```

## 4. Why Auto Decision Is Not Auto Publishing

Auto Decision V1 is not Auto Publishing.

`candidate_for_publish_readiness_review` means only that a Signal may later enter a separate reviewed publish-readiness process.

In V1:

- `publication_approved` is always `false`
- `publish_readiness_enabled` is always `false`
- no public content is generated
- no Signal becomes publish-ready
- no publishing workflow exists

The strongest allowed automated outcome is:

```text
candidate_for_publish_readiness_review
```

That means later review only.

## 5. Exception Handling

`exception_records` identify Signals that still need Owner attention:

- candidates for later publish-readiness review
- useful Signals that need more evidence
- high-value ambiguous Signals where missing evidence could change the decision
- items where Owner override may materially change the next action

`recommended_owner_attention` summarizes:

- how many Signals can be ignored
- how many need regeneration
- how many need more evidence
- how many are candidates for later publish-readiness review
- which Signals the Owner should inspect first

## 6. Owner Override

The Owner can override every automated decision.

Every auto decision record includes:

```text
owner_override_allowed: true
```

Owner Review Feedback V1 remains the source for the Owner's final review decision.

## 7. Console Behavior

The Owner Console displays Auto Decision values near the top of each review card and defaults decision controls from the automated decision:

- `auto_reject` -> `reject`
- `needs_more_sources` -> `request_more_sources`
- `needs_regeneration` -> `request_regeneration`
- `hold` -> `hold`
- `candidate_for_publish_readiness_review` -> `approve_for_future_publish_readiness_review`

The UI uses human-readable labels such as:

- Reject automatically
- Need more sources
- Regenerate analysis
- Hold
- Candidate for later readiness review

The console keeps the Owner override path visible. Defaults reduce workload; they do not remove Owner control.

## 8. Safety Boundaries

Auto Decision Engine V1 must not:

- call OpenAI
- require `OPENAI_API_KEY`
- dispatch workflows
- publish content
- approve publication
- enable publish readiness
- generate public website pages
- generate social posts
- mutate Notion
- use live GitHub API collection
- scrape article bodies
- store raw provider responses
- write Knowledge Graph records
- run Prediction Engine work
- perform Confidence Calibration
- perform Multi-source Correlation
- deploy
- modify production secrets
- modify production server files

All safety flags remain false.

## 9. Non-Goals

This PR does not implement:

- public publishing
- Publish Readiness Gate
- social posting
- Knowledge Graph writes
- Prediction Engine
- Confidence Calibration
- Multi-source Correlation
- Notion mutation
- live GitHub API collection
- article scraping
- OpenAI calls
- deployment
- persistence

## 10. How To Run Locally

Run the Auto Decision Engine against the fixture:

```bash
python3 scripts/dysonx_auto_decision_engine.py \
  --score-report tests/fixtures/auto_decision_engine_v1/signal_quality_score.json \
  --output tmp/dysonx_auto_decision_engine.json
```

Open the Owner Console locally:

```bash
python3 -m http.server 8090
```

Then open:

```text
http://127.0.0.1:8090/internal/dysonx-owner-intelligence-preview/
```

## 11. Recommended Next Step

After the Owner tests this:

- if console decisions are still slow, do Owner Console Usability Fix V2
- if workflow is usable, do Review Session Save V1 / Internal Frontend Persistence V1
- only later consider Publish Readiness Gate V1

No production deployment was performed.
