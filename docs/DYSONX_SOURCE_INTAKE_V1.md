# DysonX Source Intake V1

Status: V1 source intake foundation

This document describes the first vertical slice for source intake:

`Notion-shaped source records -> validation -> Source objects -> collection-ready source list -> audit report`

This is not content collection. It does not fetch article content, call LLM APIs, publish pages, write to Notion, implement Knowledge Graph, or implement Prediction Engine.

## Modes

### Fixture Mode

Fixture mode reads a local JSON file shaped like the V1 Notion source database:

```bash
python3 scripts/dysonx_source_intake.py \
  --fixture tests/fixtures/notion_sources_v1.json \
  --dry-run \
  --output tmp/dysonx_source_intake_report.json
```

Fixture mode:

- Reads local JSON only.
- Validates records against `dysonx_notion_source_schema.py`.
- Converts valid enabled records into `Source` objects.
- Rejects disabled or invalid records from collection eligibility.
- Preserves validation errors in the audit report.
- Performs no network requests.

### Dry-Run Mode

`--dry-run` records the intended intake result without side effects. V1 source intake always avoids writes, collection, LLM analysis, and publishing.

The audit report includes:

- Total source records seen
- Eligible source count
- Rejected record count
- Eligible source details
- Validation errors
- Confirmation that no write, collection, LLM, or publishing operation occurred

### Real Notion Read-Only Mode

Real Notion read-only mode is represented by a disabled adapter skeleton:

```bash
python3 scripts/dysonx_source_intake.py \
  --notion-readonly \
  --dry-run \
  --output tmp/dysonx_source_intake_report.json
```

It requires these environment variables before any future read attempt:

- `NOTION_TOKEN`
- `DYSONX_NOTION_SOURCES_DATABASE_ID`

If either variable is missing, the command fails closed with a clear error. The V1 skeleton does not implement the real Notion fetch yet and never writes to Notion.

## Non-Goals

Source Intake V1 must not:

- Add RSS, web, GitHub, social, paper, or government collectors.
- Fetch article or source content.
- Call LLM APIs.
- Publish pages.
- Write to Notion.
- Implement Knowledge Graph.
- Implement Prediction Engine.
- Add billing, dashboards, API platform, enterprise, or multi-tenant features.
