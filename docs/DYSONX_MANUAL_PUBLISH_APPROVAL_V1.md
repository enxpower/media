# DysonX Manual Publish Approval V1

## 1. Purpose

Manual Publish Approval V1 is Step 3 of the strict 5-Step Final Launch Plan:

```text
Owner Review Wizard
-> Publish Readiness Gate
-> Public Signal Page Generator
-> Public Signals Index
-> Local Public Preview
-> Manual Publish Approval
-> current deployment host
```

It creates a deterministic offline approval report from Step 2 Public Signal Page Generator V1 manifest output and an explicit Owner approval input.

The report is an input for Step 4 Production Publish Pack. It is not publication.

## 2. Boundary

Manual Publish Approval V1 does not:

- publish
- deploy
- dispatch workflows
- call OpenAI
- scrape or fetch sources
- modify generated public HTML
- write production public pages
- mark any page as published
- perform production release

It may set:

```json
{
  "approved_for_production_pack": true
}
```

It must not set:

```json
{
  "published": true,
  "production_publish_performed": true,
  "deployed": true
}
```

`approved_for_production_pack` means only that Step 4 may include the approved draft page in a production publish pack candidate. Published remains false until Step 5 production launch.

Production Publish Pack V1 is governed by `docs/DYSONX_PRODUCTION_PUBLISH_PACK_V1.md`. It consumes the Step 2 generator output and this Step 3 approval report to create production-ready artifacts for Step 5. It does not publish, deploy, dispatch workflows, call OpenAI, write to `current deployment host`, or mark `published` true.

First Public Launch V1 is governed by `docs/DYSONX_FIRST_PUBLIC_LAUNCH_V1.md`. It is the only launch step allowed to mark launched pages `published: true`, and only after Step 4 release guard evidence plus explicit Owner launch authorization.

## 3. CLI

```bash
python3 scripts/dysonx_manual_publish_approval.py \
  --manifest tests/fixtures/manual_publish_approval_v1/public_signal_pages_manifest.json \
  --approval-input tests/fixtures/manual_publish_approval_v1/manual_publish_approval_input.json \
  --output tmp/manual_publish_approval_report.json
```

The CLI reads local JSON only and uses Python standard library modules.

## 4. Approval Input

The approval input must include:

- `approval_version`
- `owner.name`
- `owner.role`
- `approved_at`
- `decisions`

Allowed decisions:

- `approve_for_production_pack`
- `hold`
- `reject`

Only `approve_for_production_pack` can create an approved entry. `hold` and `reject` are recorded as blocked from Step 4 packaging.

## 5. Approval Rules

The tool approves only pages that:

- exist in the Step 2 manifest `pages` list
- were generated from Publish Readiness Gate-approved Signals
- are ready for public generation
- have `published` false or absent
- have no `production_publish_performed` marker
- come from a manifest where `manual_publish_approval_required` is true
- have source page and preview paths
- receive explicit Owner decision `approve_for_production_pack`
- include Owner identity and approval timestamp

The tool blocks:

- missing page entries
- generator-blocked Signals
- missing Owner identity
- missing approval timestamp
- missing or unsupported decisions
- `hold` and `reject`
- `published: true`
- `production_publish_performed: true`
- manifests that do not require manual publish approval

## 6. Output Report

The report includes:

- approval metadata
- input files
- Owner identity
- approved timestamp
- pages seen / approved / blocked counts
- approved entries
- blocked entries
- safety flags

Safety fields must state:

- `manual_publish_approval_completed: true`
- `no_public_publishing_performed: true`
- `no_deployment_performed: true`
- `no_openai_call_performed: true`
- `no_workflow_dispatch_performed: true`
- `production_publish_performed: false`
- `production_pack_required: true`

## 7. Functional Publishing Priority

This step supports:

```text
Functional publishing before aesthetic polish;
quality and safety gates before public release.
```

Manual approval is mandatory before production release. Public page visual polish remains a later sprint unless trust, safety, attribution, basic readability, or publication clarity is broken.

## 8. Non-Goals

This step does not implement:

- Production Publish Pack
- production deployment
- public release
- workflow dispatch
- OpenAI calls
- backend APIs
- database storage
- scraping
- Knowledge Graph writes
- Prediction Engine
- Confidence Calibration
- Multi-source Correlation
- social distribution
- final public visual polish

No production deployment is authorized by this document.
