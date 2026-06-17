# DysonX V1 Dry-Run Milestone Review

Date: 2026-06-17

Branch: `audit/dysonx-v1-dry-run-milestone-review`

Base: `feature/dysonx-v1-pipeline-orchestrator`

Status: Documentation-only milestone review. No product code, provider
integration, collector, publishing, social posting, Knowledge Graph,
deployment, or merge work is included.

## Governance Inputs Reviewed

Governance documents reviewed before this audit:

- `AGENTS.md`
- `docs/DYSONX_OWNER_INTENT.md`
- `docs/DYSONX_PROJECT_CONTEXT.md`
- `docs/DYSONX_PRODUCT_CONSTITUTION.md`
- `docs/DYSONX_SYSTEM_ARCHITECTURE.md`
- `docs/DYSONX_ENGINEERING_GOVERNANCE.md`

PR stack reviewed:

- PR #22: Source Intake V1
- PR #23: Signal Candidate Pipeline V1
- PR #24: LLM Intelligence Layer V1
- PR #25: Governance & Architecture Audit
- PR #26: LLM Job & Audit Foundation V1
- PR #27: Signal Scoring & Ranking Engine V1
- PR #28: Quality Review Gate V1
- PR #29: Publish Package V1
- PR #30: V1 Pipeline Orchestrator

At review time, PRs #22 through #30 were open draft PRs with clean merge
status.

## Executive Summary

The DysonX V1 dry-run milestone is complete enough to proceed to the first
carefully scoped real-integration PR.

The end-to-end dry-run flow works:

```text
Raw Items Fixture
-> Signal Candidate
-> LLM Job / Audit
-> Intelligence Signal
-> Scoring / Ranking
-> Quality Review
-> Publish Package
-> Pipeline Summary
```

The pipeline remains fixture-based and dry-run only. It does not call real LLM
providers, fetch live sources, write website pages, post to social platforms,
write Knowledge Graph data, merge, or deploy.

## Scores

Milestone maturity score: **86 / 100**

Architecture compliance score: **93 / 100**

Governance compliance score: **95 / 100**

Score rationale:

- Strong: object boundaries are clear across raw item, candidate, LLM job,
  intelligence signal, score, review, package, and pipeline summary.
- Strong: all work remains draft-PR based, dry-run safe, and non-deploying.
- Strong: tests cover the core V1 data flow and negative guard cases.
- Remaining gap: real integrations still need fail-closed adapters, secrets
  policy enforcement, retry/error handling, and stronger source authority data.
- Remaining gap: legacy pre-DysonX aggregator scripts still exist and should
  remain quarantined from the V1 path.

## Flow Verification

Verified V1 dry-run flow:

1. `Raw Items Fixture`

   Local fixture records in `tests/fixtures/raw_items_v1.json` are the only raw
   content input for the orchestrated dry run.

2. `Signal Candidate`

   `scripts/dysonx_signal_candidate_pipeline.py` creates deterministic
   `SignalCandidate` records from valid raw items and rejects invalid raw items
   without crashing.

3. `LLM Job / Audit`

   `scripts/dysonx_llm_audit.py` creates provider-neutral LLM job, run,
   validation, audit, and Intelligence Signal output using only
   `FakeLLMProvider`.

4. `Intelligence Signal`

   Fake-provider output becomes structured Intelligence Signals. No article body
   or publishable page is generated.

5. `Scoring / Ranking`

   `scripts/dysonx_signal_ranking.py` scores and ranks Intelligence Signals by
   deterministic decision-priority rules.

6. `Quality Review`

   `scripts/dysonx_publish_eligibility.py` classifies ranked signals as
   `publish_ready`, `needs_review`, or `rejected`.

7. `Publish Package`

   `scripts/dysonx_publish_package.py` converts only `publish_ready` signals
   into structured package metadata. It does not write public content files.

8. `Pipeline Summary`

   `scripts/dysonx_v1_pipeline.py` writes the final dry-run summary and stage
   reports under `tmp/dysonx_v1_pipeline`.

## Governance Compliance

### Signal-First

Pass.

- The dry-run path uses Signal-oriented objects throughout.
- `Article` is not introduced as the primary object.
- Publish packages wrap Intelligence Signals rather than generic articles.

### English Canonical

Pass.

- Publish Package V1 uses `canonical_language = en`.
- Chinese is represented only as optional localization metadata.
- No Chinese canonical identifiers or duplicate localized Signals are created.

### Notion Source Rule

Pass for V1 scope.

- Notion remains the planned source-of-truth.
- Current dry run uses local fixtures only and does not hardcode production
  monitored sources.
- Real Notion access is still intentionally blocked until a read-only adapter
  integration PR.

### LLM-First After Collection

Pass for current V1.

- Candidate normalization is documented as pre-LLM scaffolding.
- Interpretation happens through the LLM job/audit and fake provider layer.
- Ranking and quality review operate downstream of Intelligence Signals.

### No Generic Article Path

Pass for V1 path.

- No dry-run stage writes article bodies, news pages, or SEO posts.
- Legacy article/news scripts remain outside the V1 path and should stay
  quarantined.

### No Publishing Bypass

Pass.

- Quality Review Gate precedes Publish Package generation.
- Publish Package V1 emits metadata only.
- No website pages, public content files, or social posts are written.

### No Production Deployment

Pass.

- Work remains branch and draft-PR based.
- No merge, deployment, production file modification, or production secret
  change was performed.

## Test Coverage Summary

Current test suite after PR #30:

- Source schema and source config loading tests.
- Read-only adapter and source intake tests.
- Schema separation tests for RawItem, SignalCandidate, Signal, SocialDraft.
- Signal candidate pipeline tests.
- LLM intelligence layer tests.
- LLM job/audit tests.
- Signal scoring/ranking tests.
- Quality review gate tests.
- Publish package tests.
- Full dry-run orchestrator tests.

Validation command result during this review:

- `python3 scripts/constitution_guard.py`: pass
- `python3 scripts/architecture_guard.py`: pass
- `python3 scripts/release_guard.py`: pass
- `python3 -m py_compile scripts/*.py`: pass
- `python3 -m unittest discover -s tests`: pass
- `python3 scripts/dysonx_v1_pipeline.py --raw-fixture tests/fixtures/raw_items_v1.json --output-dir tmp/dysonx_v1_pipeline --dry-run`: pass
- `git diff --check`: pass

Dry-run sample summary:

- `raw_items_seen`: 5
- `candidates_created`: 4
- `signals_generated`: 4
- `signals_ranked`: 4
- `publish_ready`: 4
- `packages_created`: 4
- `rejected`: 0
- `warnings`: []
- `real_llm_api_used`: false
- `publishing_performed`: false
- `social_posting_performed`: false
- `network_requests_performed`: false
- `dry_run`: true

## Remaining Blockers Before Real Integrations

### Real Notion API Read-Only Use

Blockers:

- Need a read-only client implementation with explicit timeout/error handling.
- Need env var checks that fail closed without logging secrets.
- Need tests that mock Notion responses and verify no writes are possible.
- Need audit fields for source sync attempts and last-error capture.

### Real LLM Provider Integration

Blockers:

- Need provider adapter interface around the existing LLM job/audit structures.
- Need prompt version pinning and output schema validation before accepting
  provider output.
- Need rate-limit, retry, timeout, malformed-output, and provider-error
  classification.
- Need secret handling tests that ensure tokens are not printed or committed.
- Need fixture/mocked provider tests before any live provider smoke path.

### Real RSS / Manual Collector

Blockers:

- Need collector interface that preserves raw evidence without judging final
  importance.
- Need source attribution, content hash, fetch status, and error state.
- Need fixture-only tests before live fetch.
- Need copyright-safe raw content retention policy.
- Need explicit separation from publishing and ranking.

### Website Publishing

Blockers:

- Need final Signal schema compatibility review.
- Need manual/human approval workflow for `publish_ready` packages.
- Need quality review persistence and audit replay.
- Need route/localization design for English canonical and Chinese optional
  localized fields.
- Need publish job dry-run and preview-only implementation before any public
  output.

## Known Technical Debt

- Legacy `scripts/aggregator.py` and `scripts/openai_summary.py` still exist
  from the pre-DysonX project. They are not part of the V1 dry-run path and
  should be explicitly deprecated or quarantined.
- Authority scoring is currently conservative and pattern-based. Real authority
  scoring should use source configuration history from Notion.
- Publish Package V1 currently has empty source URLs because upstream
  Intelligence Signal V1 does not carry original URLs all the way through the
  pipeline. This should be corrected before website publishing work.
- The dry-run orchestrator writes JSON files but does not persist state in a
  database. That is appropriate for V1 dry-run but not for production.
- Quality Review V1 is deterministic and automated only. Human review workflow
  is still missing.
- Deduplication is not implemented beyond warning handling. Real duplicate
  detection must be introduced before publishing.

## Recommended Merge Order

Recommended merge order for the V1 dry-run stack:

1. PR #22: Source Intake V1
2. PR #23: Signal Candidate Pipeline V1
3. PR #24: LLM Intelligence Layer V1
4. PR #26: LLM Job & Audit Foundation V1
5. PR #27: Signal Scoring & Ranking Engine V1
6. PR #28: Quality Review Gate V1
7. PR #29: Publish Package V1
8. PR #30: V1 Pipeline Orchestrator
9. PR #25: Governance & Architecture Audit can merge before or after the stack,
   but it is not a runtime dependency.

Do not merge any PR in this stack directly to `main` without the repository's
normal review path.

## Recommended Next Real-Integration PR

Recommended next PR:

`feature/dysonx-v1-notion-readonly-live-adapter`

Purpose:

- Implement the first real read-only Notion adapter behind the existing source
  intake interface.
- Require `NOTION_TOKEN` and `DYSONX_NOTION_SOURCES_DATABASE_ID`.
- Fail closed when env vars are absent.
- Never write to Notion.
- Mock Notion API responses in tests.
- Preserve audit errors without crashing the full intake.

Reasoning:

Notion source configuration is the safest first external integration because it
does not analyze, publish, or distribute content. It also strengthens the
governance requirement that monitored sources remain Notion-managed rather than
hardcoded.

## Go / No-Go Recommendation

Recommendation: **GO for the next controlled real-integration PR, Notion
read-only source sync only.**

Recommendation: **NO-GO for real LLM provider integration, collectors, website
publishing, social posting, Knowledge Graph writes, or Prediction Engine work
until the Notion read-only integration and legacy-script quarantine are handled.**

## Final Conclusion

The DysonX V1 dry-run milestone is aligned with the Constitution and ready for
the next narrow integration step. The pipeline proves the architecture can move
from raw fixture evidence to structured, ranked, quality-reviewed, packageable
Signals without becoming a generic article pipeline or publishing system.

No merge or production deployment was performed.
