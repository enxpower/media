# DysonX Collector Foundation V1

Status: first collection-layer foundation after the live Notion Source Registry milestone

## Purpose

Collector Foundation V1 establishes the first controlled path from DysonX Source
objects to persisted RawItem records.

It implements this vertical slice:

```text
Source Registry / Source objects
-> Collector selection
-> RSS collector
-> Manual URL collector skeleton
-> GitHub release collector skeleton
-> RawItem creation
-> Normalization
-> Deduplication
-> RawItem JSON persistence
-> Audit report
```

## Architecture Boundary

This PR introduces the Collection and Raw Data foundation only. It does not
advance collected RawItems into SignalCandidates, LLM jobs, Signals, publishing,
social distribution, trackers, or the Knowledge Graph.

The protected architecture remains:

```text
Source
-> RawItem
-> SignalCandidate
-> LLM Intelligence
-> Ranking
-> Review
-> Publish Package
```

Collector Foundation V1 stops at RawItem persistence.

## Collector Behavior

Collector selection is based on Source fields from the source sync store:

- RSS sources use the RSS collector.
- Manual URL sources use a metadata-only manual collector skeleton.
- GitHub release sources use a fixture-only GitHub release collector skeleton.
- Unknown sources fall back to the manual URL skeleton.

### RSS Collector

The RSS collector parses local XML fixture data with Python standard library XML
parsing. It extracts item title, link, description, publication date, and source
metadata into RawItem candidates.

This foundation does not schedule RSS collection and does not publish RSS-derived
items.

### Manual URL Skeleton

The manual URL collector creates RawItem metadata only. It preserves source URL
and source attribution but does not scrape article bodies.

### GitHub Release Skeleton

The GitHub release collector parses fixture JSON only. It does not call the live
GitHub API.

## Normalization

Normalization:

- trims repeated title whitespace
- canonicalizes URL scheme and host casing
- strips query strings and fragments
- creates deterministic RawItem IDs from source, canonical URL, and title
- computes content hashes
- preserves source attribution
- preserves raw excerpt separately from raw content

Normalization must not rewrite source material into a publishable article.

## Deduplication

Deduplication is deterministic and local to the collection run.

RawItems are considered duplicates when they share:

- source ID
- canonical URL
- normalized lower-case title

Duplicate records are reported in `deduplication_results` and excluded from the
persisted `raw_items` list.

## RawItem Persistence Shape

RawItems are stored in JSON with exactly these top-level keys:

```text
raw_items
collection_metadata
deduplication_results
```

The store is a raw-data cache and audit artifact. It is not a Knowledge Graph,
not a publish package, and not a website data store.

## Audit Report

The collector audit report includes:

- collection timestamp
- source count
- raw item count before deduplication
- persisted raw item count
- duplicates removed
- per-source collector results
- raw store path
- safety flags

Required safety flags are always false:

- `notion_write_operations_performed`
- `live_github_api_used`
- `llm_api_calls_performed`
- `publishing_performed`
- `social_posting_performed`
- `article_body_scraping_performed`

## What Is Not Implemented

Collector Foundation V1 does not implement:

- scheduled collectors
- live GitHub API access
- full article scraping
- Notion mutation or writeback
- LLM provider calls
- SignalCandidate generation from collected data
- Signal publishing
- social posting
- Knowledge Graph writes
- Prediction Engine
- dashboard, billing, enterprise, or multi-tenant features
- deployment

## Command

Fixture-safe command:

```bash
python3 scripts/dysonx_collector_foundation.py \
  --source-store tests/fixtures/source_sync_store_v1.json \
  --output tmp/dysonx_collector_report.json \
  --raw-store tmp/dysonx_raw_items_store.json
```

## Next Step

The next product step after this foundation should be a separate reviewed PR for
converting RawItems into SignalCandidates without bypassing the LLM-first
interpretation architecture.
