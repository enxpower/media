# DysonX Source Collector V1

DysonX Source Collector V1 connects the Notion-managed `DysonX Sources` database to the Notion `DysonX Signal Intake` database.

It is not a launch step and does not create Step 6. It does not write public pages. Public page generation remains owned by the Notion public Signals sync workflow introduced after PR #82.

## Purpose

The collector reads enabled sources, collects recent public metadata/items, converts them into safe candidate Signals, and writes those candidates into Signal Intake.

It supports:

- RSS and Atom feeds.
- arXiv RSS-style metadata feeds.
- Official website pages with title, canonical URL, and meta description extraction.
- Government and policy pages with metadata extraction.
- Manual source URLs.

## Required Secrets

The workflow requires:

- `NOTION_TOKEN`
- `DYSONX_NOTION_SOURCES_DATABASE_ID`
- `NOTION_SIGNAL_INTAKE_DATABASE_ID`

## Source Eligibility

A source can be collected only when:

- `Enabled` is checked.
- `Priority` is `Critical`, `High`, or `Medium`.
- `URL` exists.
- `Source Type` or `Platform` is supported.
- `Fetch Frequency` allows a new run when `Last Fetched At` exists.

The live collector may update `Last Fetched At`, `Last Success At`, and `Last Error` when source-page status tracking is available in Notion.

## Metadata Collection Rules

For RSS and Atom feeds, V1 extracts:

- title
- link
- published date when available
- summary or description when available

For non-feed pages, V1 extracts only:

- page title
- canonical URL
- meta description

The collector does not scrape article bodies and does not copy full page text.

For arXiv sources, V1 prefers RSS/Atom metadata and may use abstract summary metadata available in the feed. It does not copy full paper text.

## Candidate Signal Fields

Each candidate includes:

- Signal Title
- Slug
- Source Name
- Source URL
- Published Date when available
- Category
- AGI Relevance
- Summary
- Why It Matters
- Evidence
- Risk / Safety Notes
- Attribution Status
- Copyright Status
- Quality Hint
- Status
- Ready for Pipeline
- Published

## Auto-Publish Eligibility

The collector may mark a candidate `Ready for Pipeline` and `Published` only when all conditions are true:

- Source priority is `Critical` or `High`.
- Source authority score is at least `85`.
- Attribution is complete.
- Source URL is present.
- Summary is short and summary-only.
- No raw article body is included.
- The item is clearly AI, AGI, agent, model, evaluation, compute, safety, or policy relevant.
- Quality Hint is at least `85`.
- Copyright Status is `Safe Summary Only`.

Otherwise, the candidate remains not ready and not published, with status such as `Needs Owner Review` or `Needs More Sources`.

## Deduplication

Before creating a Signal Intake row, V1 checks existing Signal Intake records by:

- Source URL
- normalized Signal title

Duplicates are skipped. V1 does not create duplicate public Signals.

## Safety Rules

Source Collector V1 must not:

- Call OpenAI.
- Use LLM-generated claims.
- Copy raw article bodies.
- Scrape full source-page bodies.
- Publish unknown-source content.
- Publish missing-attribution content.
- Publish low-relevance content directly.
- Write public static pages.
- Hardcode a deployment domain.
- Deploy.
- Auto-merge.

V1 uses deterministic rule-based scoring only.

## Workflow

`.github/workflows/dysonx-source-collector-v1.yml` runs every six hours, offset from the public Signals sync workflow, and supports manual `workflow_dispatch`.

The workflow does only:

`DysonX Sources -> DysonX Signal Intake`

It does not modify `signals/`, does not commit public files, and does not open public content PRs.

The existing Notion public Signals sync workflow remains responsible for:

`DysonX Signal Intake -> Public Signals static pages -> content PR`

No production deployment is performed by Source Collector V1.
