# DysonX LLM Intelligence Layer V1

This document defines the first DysonX Intelligence Signal generation layer.

V1 transforms `SignalCandidate` objects into structured `IntelligenceSignal`
records through an LLM provider abstraction. This is intelligence extraction,
not article generation.

## Scope

Allowed in V1:

- Read existing `SignalCandidate` records.
- Analyze candidates through a provider abstraction.
- Use `FakeLLMProvider` for deterministic local tests.
- Produce structured `IntelligenceSignal` records.
- Produce an audit report with processing counts and distributions.

Not included in V1:

- Real OpenAI, Anthropic, Gemini, or local model calls.
- Provider credentials or environment variables.
- Website publishing.
- Social posting.
- Knowledge Graph writes.
- Prediction Engine behavior.
- Dashboard, billing, subscription, enterprise, API platform, or multi-tenant features.

## Target Flow

```text
SignalCandidate
-> LLM Analysis abstraction
-> IntelligenceSignal
-> Audit Report
```

V1 uses a fake provider behind the same interface that future providers can
implement. This preserves the LLM-first architecture without introducing real
network calls in this foundation PR.

## IntelligenceSignal V1 Fields

- `signal_id`
- `title`
- `source_id`
- `source_name`
- `signal_type`
- `importance`
- `confidence`
- `summary`
- `key_points`
- `affected_entities`
- `impact_horizon`
- `tags`
- `created_at`

## Provider Abstraction

The LLM provider interface accepts one `SignalCandidate` and returns structured
analysis fields used to create an `IntelligenceSignal`.

Future provider families are intentionally provider-neutral:

- OpenAI
- Anthropic
- Gemini
- Local models

V1 implements only `FakeLLMProvider`. It is deterministic, has no credentials,
and performs no network requests.

## Audit Report

The audit report records:

- Candidates processed
- Signals generated
- Confidence distribution
- Importance distribution
- Processing warnings
- Provider mode
- Whether real LLM APIs, network requests, or publishing occurred

## Governance Notes

This layer supports the DysonX constitution by making LLM analysis the first
major interpretation layer after pre-LLM candidate preparation. It does not
generate articles, publish pages, or optimize for content volume.
