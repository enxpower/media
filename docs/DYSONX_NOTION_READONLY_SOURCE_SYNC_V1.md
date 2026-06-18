# DysonX Notion Read-Only Source Sync V1

Status: first real external integration boundary

This document defines the V1 read-only Notion source sync. The feature syncs
source configuration only. It does not collect source content, run RSS/web/GitHub
collectors, call LLM providers, write public pages, post to social platforms,
write Knowledge Graph records, create predictions, deploy, or modify Notion.

## Architecture

The vertical slice is:

```text
Notion Sources Database
-> Read-Only Fetch
-> Schema Validation
-> Source Conversion
-> Audit Report
-> JSON Source Sync Store
```

This belongs to the Source Configuration Layer. It prepares monitored source
records for later collection work while preserving the broader DysonX path:

```text
Source -> Signal -> LLM -> Ranking -> Review -> Publish
```

## Environment Variables

Required for real Notion sync:

- `NOTION_TOKEN`
- `DYSONX_NOTION_SOURCES_DATABASE_ID`

If either value is missing, the client fails closed before a network request and
does not write a report or store file.

## Read-Only Client

The real client queries:

```text
POST https://api.notion.com/v1/databases/{database_id}/query
```

It uses the official Notion database query API shape and paginates with
`next_cursor` when `has_more` is true.

The client exposes only `list_source_records()`. It has no create, update,
delete, patch, archive, or mutation methods.

## Validation Behavior

Fetched Notion pages are converted into the existing DysonX source schema fields:

- `Name`
- `Source Type`
- `URL`
- `Platform`
- `Priority`
- `Authority Score`
- `Language`
- `Region`
- `Topic Tags`
- `Related Entities`
- `Enabled`
- `Fetch Frequency`
- `Last Fetched At`
- `Last Success At`
- `Last Error`
- `Notes`

Each record is validated by `validate_notion_source_record()`.

Validation outcomes:

- Valid and enabled records become `Source` objects.
- Schema-invalid records are reported as invalid and do not stop the sync.
- Schema-valid disabled records are reported as skipped.

## Persistence

V1 uses JSON persistence because it is the smallest useful storage layer for the
current boundary. It is deterministic, easy to inspect in PRs, and does not add a
database migration surface before collection, LLM analysis, and publishing are
ready.

Default store path:

```text
tmp/dysonx_source_sync_store.json
```

The store contains:

- `sources`
- `sync_metadata`
- `validation_results`

Those are the only top-level persisted JSON keys. Store version metadata lives
inside `sync_metadata`.

The store explicitly does not contain:

- raw articles
- LLM outputs
- publish packages
- social posts
- graph records
- prediction records

## Audit Output

Default report path:

```text
tmp/dysonx_source_sync_report.json
```

The report includes:

- total records
- valid records
- invalid records
- skipped records
- sync duration
- sync timestamp
- Notion write operations performed: always `false`
- storage write operations performed
- validation details
- converted source records

## Failure Modes

- Missing `NOTION_TOKEN`: fail closed.
- Missing `DYSONX_NOTION_SOURCES_DATABASE_ID`: fail closed.
- Notion query transport error: fail without partial storage.
- Malformed Notion response: fail without partial storage.
- Invalid individual record: audit and continue.
- Disabled individual record: skip and continue.

## CLI

Real read-only sync:

```bash
python3 scripts/dysonx_notion_source_sync.py --notion-readonly
```

Fixture-backed local sync for tests and review:

```bash
python3 scripts/dysonx_notion_source_sync.py \
  --fixture tests/fixtures/notion_sources_v1.json \
  --output tmp/dysonx_source_sync_report.json \
  --storage tmp/dysonx_source_sync_store.json
```

## Governance Boundary

This PR is intentionally limited to source configuration sync.

Out of scope:

- Article collection.
- RSS collector.
- GitHub collector.
- Web scraping.
- Real LLM provider calls.
- Publishing.
- Social posting.
- Knowledge Graph implementation.
- Prediction Engine.
- Dashboard, enterprise, billing, or multi-tenant features.
- Deployment.
