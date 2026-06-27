# DysonX

DysonX is an AI / AGI Intelligence OS for tracking the signals shaping AGI.

It is an AGI signal tracker and first-source AI intelligence platform. The core
object is the Signal, not the Article. DysonX is designed to turn high-authority
AI and AGI source material into structured intelligence, rankings, quality
review decisions, and decision-ready context.

## Product Principles

- Signal-first: Signals are the operating unit for intelligence value.
- English-default: English is canonical for routes, metadata, and structured
  output.
- Chinese-switchable: Chinese is a future localization layer, not a separate
  canonical product.
- Notion-managed sources: monitored source configuration belongs in Notion, not
  permanent hardcoded lists.
- LLM-first interpretation: after collection, the first major interpretation
  step is provider-neutral LLM analysis with audit records.
- Quality-gated output: publishing must stay behind validation and review gates.

## Current V1 Status

The V1 dry-run pipeline is available and fixture-based.

Current dry-run flow:

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

The dry-run pipeline writes JSON audit reports under `tmp/` and does not publish
website pages, post to social platforms, call real model providers, or fetch
live Notion data.

## DysonX Public Intelligence Pipeline

The completed public intelligence automation chain is:

```text
DysonX Sources
-> Source Collector V1
-> DysonX Signal Intake
-> Public Signals Sync PR
-> Public Signals Auto-Merge Gate
-> automatic squash merge when DYSONX_PUBLIC_SIGNALS_AUTO_MERGE=true
-> public page update
```

Workflows:

- `DysonX Source Collector V1` reads DysonX Sources, writes safe candidates to
  Signal Intake, and does not write public pages.
- `DysonX Notion Public Signals Sync` reads Signal Intake, generates public
  Signals static output, and opens a content PR.
- `DysonX Public Signals Auto-Merge V1` gates only public Signals sync PRs,
  requires strict quality and safety checks, and auto-merges only when
  `DYSONX_PUBLIC_SIGNALS_AUTO_MERGE=true`.

Safety gates require Critical source priority, `Quality Hint >= 92`,
`Attribution Status = Complete`, `Copyright Status = Safe Summary Only`,
`Ready for Pipeline = true`, `Published = true`, all non-excluded GitHub checks
green, no OpenAI call, no source-page body scraping, no raw article body
copying, no manual deployment, no hardcoded deployment domain, and changed files
restricted to `signals/` public output.

Kill switch:

- Repository variable: `DYSONX_PUBLIC_SIGNALS_AUTO_MERGE`
- `true` enables automatic merge.
- Missing or `false` means the gate may run, but no merge occurs.

Detailed docs:

- `docs/DYSONX_SOURCE_COLLECTOR_V1.md`
- `docs/DYSONX_NOTION_PUBLIC_SIGNALS_SYNC_V1.md`
- `docs/DYSONX_PUBLIC_SIGNALS_AUTO_MERGE_V1.md`

Run the V1 dry-run pipeline:

```bash
python3 scripts/dysonx_v1_pipeline.py \
  --raw-fixture tests/fixtures/raw_items_v1.json \
  --output-dir tmp/dysonx_v1_pipeline \
  --dry-run
```

## Active Architecture

Key V1 layers already present:

- Notion source schema foundation
- Local source fixture loader
- Read-only Notion adapter interface
- Source intake dry run
- Raw Item to Signal Candidate pipeline
- Provider-neutral LLM job and audit layer with fake provider
- Intelligence Signal generation
- Deterministic scoring and ranking
- Quality review gate
- Publish package metadata generation
- Full V1 dry-run orchestrator

## Governance

Every task must read:

- `AGENTS.md`
- `docs/DYSONX_OWNER_INTENT.md`
- `docs/DYSONX_PROJECT_CONTEXT.md`
- `docs/DYSONX_PRODUCT_CONSTITUTION.md`
- `docs/DYSONX_SYSTEM_ARCHITECTURE.md`
- `docs/DYSONX_ENGINEERING_GOVERNANCE.md`

Development is GitHub-first through branches and draft pull requests. No merge
or production deployment should happen without explicit owner approval.

## Validation

Recommended checks:

```bash
python3 scripts/constitution_guard.py
python3 scripts/architecture_guard.py
python3 scripts/release_guard.py
python3 -m py_compile scripts/*.py
python3 -m unittest discover -s tests
python3 scripts/dysonx_v1_pipeline.py \
  --raw-fixture tests/fixtures/raw_items_v1.json \
  --output-dir tmp/dysonx_v1_pipeline \
  --dry-run
git diff --check
```

## Legacy Decommission

The old generated content path has been decommissioned in stages:

- legacy automation disabled
- old aggregation scripts removed
- hardcoded feed configuration removed
- generated legacy pages and old sitemap removed

Remaining cleanup is tracked in
`docs/DYSONX_LEGACY_AGGREGATOR_DECOMMISSION_PLAN.md`.
