# DysonX Quality Review Gate V1

This document defines the deterministic V1 quality gate for ranked DysonX
Intelligence Signals.

This is pre-publishing. It does not publish pages or post to social platforms.

## Target Flow

```text
Ranked Intelligence Signal
-> Quality Review Gate
-> Publish Eligibility Decision
-> Audit Report
```

## Scope

Allowed in V1:

- Read ranking reports from Signal Ranking Engine V1.
- Evaluate each ranked Intelligence Signal with deterministic checks.
- Classify each signal as `publish_ready`, `needs_review`, or `rejected`.
- Produce publish eligibility records.
- Produce an audit report.

Not included in V1:

- Page publishing.
- Social posting.
- Real LLM provider calls.
- Knowledge Graph writes.
- Prediction Engine behavior.
- Dashboard, billing, enterprise, or multi-tenant features.

## QualityReviewV1

- `review_id`
- `signal_id`
- `ranking_id`
- `status`
- `decision`
- `reasons`
- `required_fields_checked`
- `failed_checks`
- `reviewer_type`
- `created_at`

## PublishEligibilityV1

- `signal_id`
- `eligible`
- `eligibility_status`
- `reasons`
- `required_manual_review`
- `created_at`

## Deterministic Rules

A signal can be `publish_ready` only if:

- `source_id` exists.
- `source_name` exists.
- `title` exists.
- `summary` exists.
- `confidence_score >= 0.70`.
- `composite_score >= 0.70`.
- Importance is valid.
- No validation failure exists.
- No unsupported-claim warning exists.
- No duplicate warning exists.

A signal must be `needs_review` if:

- Confidence is between `0.50` and `0.70`.
- Composite score is between `0.50` and `0.70`.
- Important fields are present but weak.
- Warnings exist but are not fatal.

A signal must be `rejected` if:

- Source attribution is missing.
- Summary is missing.
- Confidence is below `0.50`.
- Composite score is below `0.50`.
- Validation failed.
- Duplicate warning is fatal.

## Audit Report

The quality review report includes:

- Ranking ID.
- Signals reviewed.
- Status counts.
- Quality review records.
- Publish eligibility records.
- Confirmation that no publishing, social posting, real LLM API call, or network
  request occurred.

## Governance Notes

This gate protects DysonX from publishing thin, unsupported, duplicated, or
low-confidence content. It strengthens the Quality Gate layer while remaining
pre-publishing and deterministic.
