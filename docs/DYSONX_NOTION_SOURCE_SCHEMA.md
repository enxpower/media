# DysonX Notion Source Schema

Status: V1 source schema foundation only

This document defines the Notion source database fields required for DysonX Signal Engine V1. It does not connect to the Notion API, fetch live Notion data, add collectors, call LLM APIs, publish pages, or implement Knowledge Graph features.

## Purpose

Notion is the source of truth for monitored source configuration. V1 code may later sync these records into local schema objects, but the API connection and sync workflow are out of scope for this schema foundation.

## Database

Recommended Notion database name:

`DysonX Sources`

## Required Fields

The V1 Notion source database must define these properties:

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

## Field Definitions

### Name

- Notion type: `title`
- Required: yes
- Purpose: Human-readable source name.

### Source Type

- Notion type: `select`
- Required: yes
- Purpose: Identifies the kind of source so future collection logic can choose the correct collector.
- V1 allowed values:
  - `Official Company Blog`
  - `Research Lab`
  - `Paper`
  - `GitHub Repository`
  - `Government`
  - `Regulatory`
  - `Product Changelog`
  - `Key Person`
  - `Conference`
  - `High Authority Media`
  - `Manual`

### URL

- Notion type: `url`
- Required: yes
- Purpose: Canonical source URL or entry point.

### Platform

- Notion type: `select`
- Required: yes
- Purpose: Identifies where the source lives.
- V1 allowed values:
  - `Website`
  - `RSS`
  - `GitHub`
  - `Paper Repository`
  - `Government Site`
  - `Social`
  - `Manual`

### Priority

- Notion type: `select`
- Required: yes
- Purpose: Collection priority for future sync and collection scheduling.
- V1 allowed values:
  - `Critical`
  - `High`
  - `Medium`
  - `Low`

### Authority Score

- Notion type: `number`
- Required: yes
- Purpose: Source authority score used by later Signal analysis and quality gates.
- Valid range: `0` to `100`, inclusive.

### Language

- Notion type: `select`
- Required: yes
- Purpose: Default language for source material.
- V1 allowed values:
  - `English`
  - `Chinese`
  - `Multilingual`
  - `Other`

### Region

- Notion type: `select`
- Required: yes
- Purpose: Geographic or policy region for the source.
- V1 allowed values:
  - `Global`
  - `US`
  - `China`
  - `EU`
  - `UK`
  - `Japan`
  - `Other`

### Topic Tags

- Notion type: `multi_select`
- Required: no
- Purpose: Lightweight source categorization before LLM interpretation.
- These tags do not replace LLM analysis.

### Related Entities

- Notion type: `multi_select`
- Required: no
- Purpose: Optional source-level entity hints.
- Entity hints are not a Knowledge Graph implementation.

### Enabled

- Notion type: `checkbox`
- Required: yes
- Purpose: Determines whether the source is eligible for future collection.
- A source must not be considered collection-eligible unless `Enabled` is true.

### Fetch Frequency

- Notion type: `number`
- Required: yes
- Purpose: Future collection cadence in minutes.
- Valid range: `15` to `10080`, inclusive.

### Last Fetched At

- Notion type: `date`
- Required: no
- Purpose: Future sync state written after collection attempts.

### Last Success At

- Notion type: `date`
- Required: no
- Purpose: Future sync state written after successful collection.

### Last Error

- Notion type: `rich_text`
- Required: no
- Purpose: Future sync state for the latest collection or validation error.

### Notes

- Notion type: `rich_text`
- Required: no
- Purpose: Human review notes for source management.

## Collection Eligibility

A source is eligible for future collection only when:

- `Enabled` is true.
- `Name` is present.
- `Source Type` is present and valid.
- `URL` is present.
- `Platform` is present and valid.
- `Priority` is present and valid.
- `Authority Score` is present and within range.
- `Language` is present and valid.
- `Region` is present and valid.
- `Fetch Frequency` is present and within range.

Eligibility does not fetch anything. It only validates that the source record is ready for future collector work.

## Local Fixture Loader

Before real read-only Notion integration, V1 may use a local JSON fixture to exercise schema validation and conversion into local `Source` objects.

The local fixture loader is allowed to:

- Read local JSON records.
- Validate records against this schema.
- Convert valid enabled records into local `Source` objects.
- Preserve validation errors for audit and debugging.

The local fixture loader must not:

- Connect to Notion API.
- Fetch real Notion data.
- Perform network requests.
- Run collectors.
- Call LLM APIs.
- Publish pages.

## Read-Only Adapter Interface

Before real Notion integration, V1 may define a read-only adapter interface whose only responsibility is returning source records in this schema shape.

The initial adapter implementation may be fixture-backed for tests. It must not:

- Connect to the real Notion API.
- Require real Notion credentials.
- Read Notion tokens from environment variables.
- Write, update, or delete Notion records.
- Perform network requests.

## V1 Non-Goals

This schema foundation must not:

- Connect to Notion API.
- Fetch real Notion data.
- Add collectors.
- Call LLM APIs.
- Publish pages.
- Implement Knowledge Graph tables or relationships.
- Implement Prediction Engine, billing, subscriptions, dashboards, API platform, enterprise, or multi-tenant features.
