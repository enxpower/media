# DysonX Signal Scoring & Ranking Engine V1

This document defines the V1 ranking layer for DysonX Intelligence Signals.

The purpose is decision priority, not content volume. This layer supports the
DysonX principle:

```text
Decision > Content
```

## Target Flow

```text
Intelligence Signal
-> Scoring
-> Ranking
-> Top Signals
-> Audit Report
```

## Scope

Allowed in V1:

- Read existing fake-provider IntelligenceSignal audit reports.
- Score each IntelligenceSignal deterministically.
- Rank signals by decision-priority composite score.
- Return top signals.
- Produce an audit report with scoring reasons and scope flags.

Not included in V1:

- Real LLM provider calls.
- Publishing.
- Social posting.
- Knowledge Graph writes.
- Prediction Engine behavior.
- Dashboard, billing, enterprise, or multi-tenant features.

## SignalScoreV1

- `signal_id`
- `importance_score`
- `confidence_score`
- `authority_score`
- `freshness_score`
- `impact_score`
- `composite_score`
- `scoring_version`
- `scoring_reasons`
- `created_at`

## RankingResultV1

- `ranking_id`
- `ranked_signals`
- `top_n`
- `scoring_version`
- `created_at`
- `audit_summary`

## Deterministic Scoring

V1 scoring is deterministic and does not call LLM APIs.

Weighted composite score:

- `importance_score`: 30%
- `authority_score`: 25%
- `impact_score`: 20%
- `confidence_score`: 15%
- `freshness_score`: 10%

Importance, authority, impact, confidence, and freshness each normalize to a
`0..1` range. Missing or invalid fields receive conservative scores and are
captured in scoring reasons instead of crashing the ranking run.

## Stable Ranking

Signals are sorted by:

1. Composite score descending
2. Importance score descending
3. Confidence score descending
4. Signal ID ascending

This keeps equal-score ranking stable and auditable.

## Audit Report

The ranking audit report includes:

- Signals seen
- Signals ranked
- Top N requested
- Top N returned
- Scoring version
- Ranked signal entries with component scores
- Scoring reasons
- Confirmation that no LLM API, publishing, or social posting occurred

## Governance Notes

This layer is downstream of LLM Intelligence and LLM Job Audit. It does not
bypass LLM interpretation; it ranks already-structured Intelligence Signals for
decision priority.
