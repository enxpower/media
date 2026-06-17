# DysonX Signal Candidate Pipeline V1

Status: pre-LLM candidate pipeline foundation

This document describes the first deterministic Signal Candidate pipeline:

`Raw Item -> Normalizer -> Signal Candidate -> Audit Report`

This is intentionally pre-LLM. It does not call LLM APIs, fetch source content, run RSS/web/GitHub collectors, publish pages, post to social platforms, implement Knowledge Graph, or implement Prediction Engine.

## Purpose

The V1 Signal Candidate pipeline turns already-available raw item fixtures into structured Signal Candidates. It exists to prove object boundaries and audit behavior before LLM analysis is introduced.

## RawItem V1

Required fields:

- `source_id`
- `source_name`
- `title`
- `url`
- `published_at`
- `language`
- `collected_at`
- `raw_content`
- `metadata`

Raw Items are evidence inputs. They are not Signals and must not be published directly.

## SignalCandidate V1

Required fields:

- `candidate_id`
- `title`
- `source_id`
- `source_name`
- `url`
- `candidate_type`
- `entities`
- `tags`
- `status`
- `confidence`
- `created_at`

Signal Candidates are proposed Signals. They are not published Signals, tracker entries, Knowledge Graph nodes, or social posts.

## Deterministic Normalization

V1 uses a deterministic rule-based normalizer only:

- Titles containing `openai` and `release` map to `model_release`.
- Titles containing `anthropic` and `announce` map to `company_announcement`.
- Titles containing `ai act`, `regulation`, or `regulatory` map to `regulation`.
- Titles containing `deepmind`, `research`, or `paper` map to `research_update`.
- Otherwise, valid items map to `general_signal`.

These rules are scaffolding only. They do not replace future LLM analysis.

## Audit Report

The pipeline writes a JSON audit report with:

- `total_raw_items`
- `candidates_created`
- `candidate_types`
- `rejected_items`
- `processing_warnings`
- `llm_used`
- `network_requests_performed`
- `publishing_performed`

## Non-Goals

Signal Candidate Pipeline V1 must not:

- Call LLM APIs.
- Add RSS, web, GitHub, social, paper, or government collectors.
- Fetch article or webpage content.
- Publish pages.
- Post to social platforms.
- Implement Knowledge Graph.
- Implement Prediction Engine.
- Add dashboard, billing, API platform, enterprise, or multi-tenant features.
