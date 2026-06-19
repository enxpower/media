# DysonX RawItem to SignalCandidate Integration V1

Status: first integration from Collector Foundation V1 output into the existing
Signal Candidate Pipeline

## Purpose

This integration connects collected RawItems to the existing deterministic Signal
Candidate Pipeline without adding LLM calls, publishing, social posting, graph
writes, deployment, scheduled collection, article body scraping, Notion
mutation, or live GitHub API access.

Required flow:

```text
Source Registry / Source store
-> Collector Foundation
-> RawItem store
-> Signal Candidate Pipeline
-> Signal Candidate audit report
```

## Architecture Boundary

This PR introduces a handoff between the Raw Data layer and the existing
SignalCandidate layer. It does not merge SignalCandidate generation into the
collector itself.

The collector still stops at RawItem persistence. The integration script reads
that RawItem store, adapts records into the existing pipeline input shape, and
then calls the existing `dysonx_signal_candidate_pipeline.run_pipeline` function.

## Script

Integration script:

```text
scripts/dysonx_rawitem_signal_pipeline.py
```

Command:

```bash
python3 scripts/dysonx_rawitem_signal_pipeline.py \
  --source-store tests/fixtures/source_sync_store_v1.json \
  --raw-store tmp/dysonx_raw_items_store.json \
  --collector-report tmp/dysonx_collector_report.json \
  --signal-output tmp/dysonx_signal_candidates_report.json
```

If `--raw-store` does not exist, the script runs Collector Foundation V1 first
with the provided fixture source store and writes the collector report.

## RawItem Store Input

The RawItem store must keep the Collector Foundation V1 shape:

```text
raw_items
collection_metadata
deduplication_results
```

Each persisted RawItem is adapted into the existing Signal Candidate Pipeline
fixture shape:

- `source_id`
- `source_name`
- `title`
- `url`
- `published_at`
- `language`
- `collected_at`
- `raw_content`
- `metadata`

The adapter preserves RawItem metadata, original URL, content hash, source type,
and RawItem ID in the pipeline metadata object.

## Signal Candidate Pipeline Reuse

The integration reuses:

```text
dysonx_signal_candidate_pipeline.run_pipeline
```

It does not add a new candidate classifier outside the existing pipeline and
does not bypass the SignalCandidate layer.

## Audit Report

The signal candidate audit report includes the existing candidate pipeline
fields plus an `integration` object:

- source store path
- raw store path
- collector report path
- whether Collector Foundation ran in this invocation
- RawItems read
- confirmation that the existing Signal Candidate Pipeline was reused
- confirmation that the SignalCandidate layer was not bypassed

Required safety flags remain false:

- `notion_write_operations_performed`
- `live_github_api_used`
- `llm_api_calls_performed`
- `publishing_performed`
- `social_posting_performed`
- `article_body_scraping_performed`

The existing candidate pipeline flags also remain false:

- `llm_used`
- `network_requests_performed`
- `publishing_performed`

## What Is Not Implemented

This integration does not implement:

- real LLM API calls
- publishing
- social posting
- Knowledge Graph writes
- Prediction Engine
- dashboard, billing, enterprise, or multi-tenant features
- deployment
- Notion mutation
- live GitHub API access
- scheduled collectors
- article body scraping

## Next Step

The next reviewed PR should move from deterministic SignalCandidate creation
toward the LLM Intelligence layer while preserving the rule that LLM analysis is
the first major interpretation step after collection.
