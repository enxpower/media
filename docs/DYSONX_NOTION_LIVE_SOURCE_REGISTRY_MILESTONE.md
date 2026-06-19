# DysonX Notion Live Source Registry Milestone

Status: milestone documentation after successful live smoke test on `main`

## Milestone Summary

DysonX now has a confirmed live read-only Source Registry path from GitHub
Actions to Notion and back into the V1 source-sync audit and JSON persistence
layer.

The manual GitHub Actions workflow `DysonX Notion Read-Only Smoke Test` was run
on `main` after seed sources were added to the configured Notion source
database.

Smoke test result:

- `total_records`: 2
- `valid_records`: 2
- `invalid_records`: 0
- `skipped_records`: 0
- Notion writes: false
- collection: false
- LLM calls: false
- publishing: false
- social posting: false

Confirmed live chain:

```text
GitHub Actions
-> GitHub Secrets
-> Notion API
-> DysonX Sources
-> Validation
-> JSON Store
-> Audit Report
```

## What Is Now Confirmed

- The repository governance foundation, DysonX identity shell, hygiene cleanup,
  Notion read-only source sync, and manual smoke-test workflow have been merged.
- `main` can run the manual Notion smoke workflow through `workflow_dispatch`.
- GitHub Secrets can provide `NOTION_TOKEN` and
  `DYSONX_NOTION_SOURCES_DATABASE_ID` to the read-only sync command.
- The configured Notion database can be read by the DysonX source sync client.
- Seed Notion records can be validated and converted into DysonX Source objects.
- The sync path can write the expected JSON source store.
- The sync path can write the expected audit report.
- Invalid and skipped record counters are surfaced in the audit output.
- The smoke-test boundary confirms no Notion writes, collection, LLM calls,
  publishing, or social posting.

## What Remains Intentionally Not Implemented

This milestone does not implement:

- collector layer
- RSS collection
- GitHub collection
- web scraping
- raw article storage
- real LLM provider calls
- LLM interpretation of collected raw items
- Signal publishing
- social posting
- Knowledge Graph implementation
- Prediction Engine
- dashboard
- billing
- enterprise features
- deployment automation

The live Source Registry is configuration infrastructure only. It does not
collect external content, analyze content, publish pages, or distribute content.

## Operational Notes

- The smoke workflow is manual-only and should remain `workflow_dispatch` until
  a separate scheduling review is approved.
- Notion remains the source of truth for monitored sources.
- The JSON store is a cache and audit artifact, not a production knowledge graph.
- Smoke-test artifacts may contain source registry metadata such as source names,
  URLs, validation results, and sync metadata. They must not contain secrets.
- The smoke-test report should continue to assert that Notion writes,
  collection, LLM calls, publishing, and social posting remain false.
- Future source schema changes should update validation tests, documentation, and
  smoke-test expectations in the same PR.

## Governance Position

This milestone preserves the DysonX architecture boundary:

```text
Source Configuration
-> Collection
-> Raw Data
-> LLM Intelligence
-> Structured Knowledge
-> Signal / Tracker / Report / Distribution
```

Only the Source Configuration layer has moved from dry-run fixture confidence to
live read-only Notion confidence. Downstream layers remain blocked until each is
implemented and reviewed in sequence.

## Next Recommended Product PR

Next recommended product PR:

```text
feature/dysonx-collector-foundation-v1
```

Recommended scope:

- define the collector boundary
- introduce fixture-backed collector interfaces
- preserve raw item separation from interpreted Signals
- add audit output for collection attempts
- keep LLM calls disabled
- keep publishing disabled
- keep social posting disabled

The next PR should not start broad collection or production publishing. It
should establish the collector foundation with governance checks before any live
collector is enabled.
