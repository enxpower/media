# DysonX V1 Offline Intelligence Pipeline Milestone Review

Status: milestone audit after PR47 on `main`

## Purpose

This review documents the repository state after the DysonX V1 offline
intelligence pipeline integration landed on `main`.

The goal is to determine whether DysonX is ready for the next controlled step:
a gated real LLM provider integration PR.

This document is an audit artifact only. It does not introduce code, workflows,
provider credentials, collection schedules, publishing, social distribution,
Knowledge Graph writes, or deployment behavior.

## Current Architecture State

DysonX now has a governed V1 path that separates source configuration,
collection, raw evidence, SignalCandidate creation, fake-provider LLM audit,
ranking, quality review, publish-package metadata, and end-to-end audit output.

Current V1 flow:

```text
Notion Source Registry / Source store
-> Source validation
-> JSON source persistence
-> Collector Foundation
-> RawItem persistence
-> RawItem to SignalCandidate integration
-> Fake-provider LLM Job / Audit
-> IntelligenceSignal output
-> Ranking
-> Quality Review
-> Publish Package metadata
-> V1 Intelligence Pipeline audit report
```

This remains aligned with the DysonX architecture:

- Source configuration remains managed by Notion.
- RawItems remain separate from interpreted Signals.
- SignalCandidate is the handoff into the intelligence layer.
- LLM analysis remains the first major interpretation step after collection.
- Quality review remains before publish-package metadata.
- Publish packages remain metadata only and do not create public pages.
- The system remains Signal-first, not Article-first.

## Confirmed Live Systems

### Notion Source Registry

The live Notion Source Registry is confirmed as the source-of-truth
configuration layer for monitored sources.

Confirmed properties:

- `NOTION_TOKEN` and `DYSONX_NOTION_SOURCES_DATABASE_ID` are consumed through
  controlled runtime configuration.
- The Notion sync path is read-only.
- Missing configuration fails closed.
- Source records are validated before conversion into DysonX Source objects.
- Invalid records are reported without stopping valid records from syncing.
- Notion write operations remain false in audit output.

### GitHub Actions Smoke Test

The manual GitHub Actions smoke workflow is confirmed.

Confirmed properties:

- Trigger is manual-only through `workflow_dispatch`.
- No schedule trigger is enabled.
- GitHub Secrets provide the Notion token and database ID.
- The workflow runs the read-only Notion source sync path.
- Sync artifacts are audit outputs, not production content.
- The workflow does not collect articles, call LLMs, publish, social post, or
  deploy.

### Source Validation

The source schema and validation layer are confirmed.

Confirmed properties:

- Valid Notion records become DysonX Source objects.
- Invalid records are counted and audited.
- Source validation protects the downstream collector boundary.
- Monitored source configuration is not permanently hardcoded.

### JSON Source Persistence

The JSON source store is confirmed as a lightweight V1 persistence layer.

Confirmed top-level storage shape:

- `sources`
- `sync_metadata`
- `validation_results`

The source store does not persist raw articles, LLM outputs, or publish
packages.

## Confirmed Offline Systems

### Collector Foundation

The Collector Foundation is confirmed as the first controlled collection layer.

Confirmed properties:

- Collector behavior is selected from Source objects.
- RSS parsing is fixture/local XML based where tested.
- Manual URL collection is metadata-only and does not scrape article bodies.
- GitHub release collection uses fixture JSON only.
- Live GitHub API usage remains false.
- Notion mutation remains false.

### RawItem Persistence

RawItem JSON persistence is confirmed.

Confirmed top-level storage shape:

- `raw_items`
- `collection_metadata`
- `deduplication_results`

RawItems remain evidence records and are not published directly.

### RawItem to SignalCandidate Integration

The RawItem to SignalCandidate integration is confirmed as a thin bridge from
collection output into the existing Signal Candidate Pipeline.

Confirmed properties:

- RawItem store is read as input.
- Existing Signal Candidate Pipeline logic is reused.
- SignalCandidate logic is not duplicated in the bridge.
- `signal_candidate_layer_bypassed` remains false.
- Collector Foundation still stops at RawItem persistence.

### Fake-Provider LLM Audit

The fake-provider LLM layer is confirmed as the current intelligence-layer
boundary.

Confirmed properties:

- LLM jobs and audit records are created offline.
- Fake provider is the only active provider.
- No real OpenAI, Claude, Gemini, or other provider API is called.
- No real provider SDK is introduced by the offline pipeline.
- The audit path records provider, model, prompt version, output validation,
  and safety flags.

### Ranking

Signal ranking is confirmed as a reusable downstream module after fake-provider
intelligence output.

Confirmed properties:

- IntelligenceSignals are ranked after LLM audit.
- Ranking does not replace collection, SignalCandidate creation, or LLM audit.
- Ranking remains separate from quality review and publish-package metadata.

### Quality Review

Quality Review is confirmed as the gate before publish-package metadata.

Confirmed properties:

- Signals can be blocked or marked for review before publish package creation.
- Quality Review remains separate from ranking.
- Quality Review prevents low-confidence output from becoming public content.

### Publish Package Metadata

Publish Package metadata is confirmed as an offline packaging layer.

Confirmed properties:

- Publish packages are metadata artifacts only.
- Website pages are not generated.
- Public content files are not written.
- Social posts are not sent.
- Publishing remains blocked by Quality Review.

### V1 Intelligence Pipeline Orchestrator

The V1 Intelligence Pipeline orchestrator is confirmed as the current offline
end-to-end audit path.

Confirmed properties:

- Existing modules are composed rather than duplicated.
- Intermediate audit reports are written under the selected output directory.
- Final audit report includes counts, module reuse confirmations, layer
  boundary confirmations, rejected/skipped counts, and safety flags.
- The orchestrator does not add scheduling, deployment, web publishing, social
  distribution, live provider calls, live GitHub calls, or Notion mutation.

## What Remains Intentionally Not Implemented

The following capabilities remain intentionally out of scope:

- real LLM provider integration
- real website publishing
- social posting
- Knowledge Graph implementation
- Prediction Engine
- dashboard
- billing
- enterprise features
- multi-tenant features
- scheduled collection
- scheduled LLM runs
- production deployment

These exclusions are deliberate. The current milestone establishes confidence in
the offline architecture before introducing external model risk.

## Risks Before Real LLM Provider Integration

### Prompt Schema Drift

The fake-provider output shape may not perfectly represent real provider
behavior. A real provider PR must lock prompt versions, expected JSON schema,
validation behavior, and failure reporting before any output can proceed
downstream.

### Secret Handling

Provider API keys introduce new secret risk. The next PR must keep secrets out
of logs, artifacts, reports, tests, docs examples, and PR summaries. Missing
secrets must fail closed.

### Output Validation

Real model output can be malformed, partial, overlong, or non-JSON. The next PR
must validate output strictly and route invalid output to audit/rejection
without fabricating fallback intelligence.

### Cost Control

Real provider calls introduce spend risk. The next PR must be manual-only,
bounded by fixture or explicit input limits, and must report attempted calls,
successful calls, failed calls, and skipped calls.

### Hallucination / Unsupported Claims

Real model output can invent unsupported entities, impact claims, or source
interpretations. The next PR must preserve original source attribution and keep
unsupported or low-confidence outputs blocked by Quality Review.

### Quality Gate Tightening

The existing Quality Review gate should be reviewed before public publishing is
introduced. Real provider output must not lower the bar for publish readiness.

## Go / No-Go Recommendation

Recommendation for the next PR:

```text
GO: feature/dysonx-real-llm-provider-gated-v1
```

This is a limited go only for a gated, manual, non-publishing provider
integration. The repository is ready to test one real provider boundary because:

- Source Registry is live and read-only.
- Collector Foundation is separated from interpretation.
- RawItem and SignalCandidate boundaries are established.
- Fake-provider LLM audit exists.
- Ranking, Quality Review, and publish-package metadata are downstream and
  testable.
- The V1 orchestrator can provide end-to-end audit evidence.

This is not a go for publishing, scheduling, social distribution, Knowledge
Graph writes, prediction features, dashboards, or deployment.

## Exact Boundaries for the Next Real LLM PR

Recommended branch:

```text
feature/dysonx-real-llm-provider-gated-v1
```

Required boundaries:

- provider abstraction only
- choose one provider only: OpenAI or Claude
- manual CLI or manual workflow only
- no scheduled runs
- no publishing
- no social posting
- no website page writing
- no public content file writing
- no Knowledge Graph implementation
- no Prediction Engine
- no dashboard, billing, enterprise, or multi-tenant feature
- no production deployment
- no Notion mutation
- no live GitHub API expansion
- no article body scraping expansion

Required safety behavior:

- fail closed when provider secrets are missing
- never print provider secrets
- cap input size and record skipped items
- record attempted, completed, failed, and skipped model calls
- preserve fake provider tests
- validate model output before downstream conversion
- keep invalid output in audit/rejection paths
- keep Quality Review blocking public output

## Milestone Decision

DysonX V1 has reached an offline intelligence pipeline milestone.

The system is not production publishing-ready, but it is ready for a carefully
bounded real LLM provider integration that remains manual, audited, and
non-publishing.

The next PR should prove provider plumbing and output validation only. It should
not broaden into publishing, distribution, Knowledge Graph construction,
Prediction Engine, dashboard work, or deployment.
