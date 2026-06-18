# DysonX Notion Live Smoke Test

Status: manual GitHub Actions smoke test for read-only source sync

This document describes the safe live Notion smoke test workflow:

```text
.github/workflows/dysonx-notion-smoke-test.yml
```

## Purpose

The workflow verifies that the configured Notion source database can be read by
the DysonX read-only source sync without adding any downstream product behavior.

It tests only:

```text
Notion Source Registry
-> Read-Only Fetch
-> Validation
-> Source Conversion
-> Audit Report
-> JSON Source Persistence
```

## Trigger

The workflow uses `workflow_dispatch` only.

There is no schedule, push trigger, pull request trigger, production deployment
trigger, or automatic run path.

## Secrets

The workflow reads these GitHub Secrets:

- `NOTION_TOKEN`
- `DYSONX_NOTION_SOURCES_DATABASE_ID`

The sync client fails closed if either value is missing.

## Command

The workflow runs:

```bash
python3 scripts/dysonx_notion_source_sync.py \
  --notion-readonly \
  --output tmp/dysonx_source_sync_report.json \
  --storage tmp/dysonx_source_sync_store.json
```

## Safety Assertions

After the sync command, the workflow checks the report and store to confirm:

- no Notion writes
- no collection
- no LLM calls
- no publishing
- no social posting
- no raw article storage
- no LLM output storage
- no publish package storage
- persisted store top-level keys are only `sources`, `sync_metadata`, and
  `validation_results`

## Artifacts

The workflow uploads:

- `tmp/dysonx_source_sync_report.json`
- `tmp/dysonx_source_sync_store.json`

These artifacts exist for manual review of source sync health. They are not
published pages and are not deployed.

## Out of Scope

This smoke test does not add:

- scheduled source sync
- collector layer
- RSS collector
- GitHub collector
- web scraping
- real LLM provider calls
- publishing
- social posting
- Knowledge Graph implementation
- Prediction Engine
- dashboard
- deployment
- merge automation
