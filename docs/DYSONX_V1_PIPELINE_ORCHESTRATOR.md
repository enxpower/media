# DysonX V1 Pipeline Orchestrator

This document defines the dry-run V1 pipeline orchestrator.

The orchestrator is a local fixture workflow. It does not connect to real
providers, perform network requests, write website pages, write public content
files, post to social platforms, merge, or deploy.

## Target Flow

```text
Raw Items Fixture
-> Signal Candidate Pipeline
-> LLM Job & Audit
-> Signal Ranking
-> Quality Review
-> Publish Package
-> Final V1 Pipeline Report
```

## CLI

```bash
python3 scripts/dysonx_v1_pipeline.py \
  --raw-fixture tests/fixtures/raw_items_v1.json \
  --output-dir tmp/dysonx_v1_pipeline \
  --dry-run
```

The `--dry-run` flag is required. The orchestrator fails closed without it.

## Outputs

The orchestrator writes:

- `tmp/dysonx_v1_pipeline/llm_audit_report.json`
- `tmp/dysonx_v1_pipeline/signal_ranking_report.json`
- `tmp/dysonx_v1_pipeline/quality_review_report.json`
- `tmp/dysonx_v1_pipeline/publish_package_report.json`
- `tmp/dysonx_v1_pipeline/pipeline_summary.json`

## Pipeline Summary

`pipeline_summary.json` includes:

- `raw_items_seen`
- `candidates_created`
- `signals_generated`
- `signals_ranked`
- `publish_ready`
- `packages_created`
- `rejected`
- `warnings`
- `real_llm_api_used`
- `publishing_performed`
- `social_posting_performed`
- `network_requests_performed`
- `dry_run`

## Governance Notes

The orchestrator composes existing V1 modules instead of duplicating business
logic. It is useful for local auditability and PR validation, but it is not a
production job runner and does not publish anything.
