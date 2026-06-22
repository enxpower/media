# DysonX Publish Readiness Gate V1

## 1. Purpose

Publish Readiness Gate V1 evaluates whether an internally reviewed DysonX Signal is ready for future public Signal page generation.

It is a deterministic, offline, local CLI. It consumes structured internal review output and source Signal data, then emits a Publish Readiness Gate report with ready or blocked decisions.

It answers:

```text
Can this Signal safely move to Public Signal Page Generator V1?
```

If not, it records why not.

## 2. Why This Gate Is Required Before Public Publishing

AutoDecision, Owner review, Review Session Save, and Owner Review Wizard completion are not publication approval.

Public generation requires a separate gate because public surfaces must not expose weak, unsourced, generic, copyrighted, fixture-only, or internally incomplete Signals.

Publish Readiness Gate V1 is the first explicit boundary between internal review artifacts and future public generation.

## 3. Inputs

Required V1 input:

- Owner Feedback JSON or Owner Review Wizard Feedback JSON

Optional inputs:

- Internal Intelligence Brief JSON
- SignalQualityScore report JSON
- Auto Decision report JSON in a future version

If only Owner Feedback JSON is provided, the gate evaluates the fields available and marks missing dependencies clearly.

The gate reads local JSON only.

## 4. Outputs

The gate writes a JSON report containing:

- `gate_version`
- `created_at`
- `input_files`
- `signals_evaluated`
- `ready_count`
- `blocked_count`
- `warning_count`
- `evaluations`
- safety fields proving no publication, deployment, OpenAI call, or workflow dispatch occurred

Each evaluation contains:

- `publish_readiness_gate_passed`
- `ready_for_public_generation`
- `public_generation_blocked`
- `public_generation_blockers`
- `gate_decision`
- `blockers`
- `warnings`
- `required_next_actions`
- `published: false`
- `publication_approved: false`

## 5. Gate Checks

Publish Readiness Gate V1 checks:

1. Review / decision trail.
2. Candidate status.
3. Source and attribution.
4. Copyright and raw content safety.
5. Public content fields.
6. AGI intelligence value.
7. Quality score threshold.
8. Critical risk flags.
9. Public metadata.
10. Final ready / blocked decision.

## 6. Decision States

Allowed gate decisions:

- `ready_for_public_generation`
- `blocked_missing_public_fields`
- `blocked_missing_source`
- `blocked_needs_more_sources`
- `blocked_needs_regeneration`
- `blocked_hold`
- `blocked_rejected`
- `blocked_quality_threshold`
- `blocked_risk_flags`
- `blocked_fixture_only`
- `blocked_raw_source_content`
- `insufficient_input`

## 7. Blocker Taxonomy

Blockers include:

- missing review session ID
- missing Owner review source
- missing selected Owner decision
- missing or false safety statement
- `publication_approved` true before gate logic
- non-candidate internal status
- missing source URL
- example source without fixture mode
- fixture-only source
- missing source authority
- unknown source
- raw source content present
- missing public content fields
- missing AGI capability
- missing `why_it_matters`
- missing `watch_next`
- missing entities
- generic summary risk
- weak attribution risk
- quality below threshold
- critical risk flags

## 8. Ready-For-Public-Generation Meaning

`ready_for_public_generation: true` means only that the Signal may be consumed by a future Public Signal Page Generator V1.

It does not mean:

- public page generated
- public page published
- social post sent
- newsletter sent
- Knowledge Graph written
- deployment performed

The gate output uses explicit fields:

- `publish_readiness_gate_passed`
- `ready_for_public_generation`
- `public_generation_blocked`
- `public_generation_blockers`

It does not use ambiguous publication wording.

## 9. Why This Is Not Publishing

Publish Readiness Gate V1 writes only a local JSON report.

It does not write HTML, Markdown public pages, static site files, feeds, sitemaps, social drafts, newsletters, deployment files, or production data.

Even a passing Signal has:

```json
{
  "published": false,
  "publication_approved": false
}
```

## 10. Source And Attribution Rules

Required source fields:

- `source_url` or `first_source_url`
- `source_authority` or `source_authority_reasoning`
- source title, source reference, or public source label

The source must not be missing or unknown.

Fixture URLs such as `example.org`, `example.com`, and `example.net` are allowed only for fixture evaluation. They are blocked from future public generation with `fixture_only_not_publishable`.

## 11. Copyright / Raw Content Safety Rules

The gate blocks public generation when raw source or provider fields are present, including:

- `raw_body`
- `article_body`
- `scraped_text`
- `full_text`
- `provider_response`
- `raw_provider_response`
- `raw_copyrighted_article_text`

The blocker is:

```text
raw_source_content_present
```

## 12. Public Content Field Requirements

Required fields for future public generation:

- `public_title`
- `public_slug`
- `public_summary`
- `public_why_it_matters`
- `public_watch_next`
- `public_capability_area`
- `public_source_label`
- `public_attribution`

V1 is strict. Missing any required public content field blocks the gate.

## 13. Quality Score Thresholds

V1 normalizes scores to a 65-point scale.

Suggested thresholds:

- `score >= 55 / 65`: may pass quality threshold
- `score 45-54 / 65`: blocked for additional review or source support
- `score < 45 / 65`: blocked by quality threshold

Unknown score scale blocks public generation.

## 14. Risk Flag Handling

Critical risk flags block public generation.

Critical risks include:

- copyright risk
- source risk
- hallucination risk
- weak attribution
- generic summary
- safety-sensitive item without sufficient context
- missing source
- raw source text present

## 15. Fixture Mode

Fixture mode exists only for deterministic tests.

If a Signal uses an example source and `fixture_mode: true`, the gate can evaluate the item but must block future public generation with:

```text
fixture_only_not_publishable
```

Fixture mode does not make a Signal publishable.

## 16. CLI Usage

```bash
python3 scripts/dysonx_publish_readiness_gate.py \
  --owner-feedback tests/fixtures/publish_readiness_gate_v1/owner_feedback.json \
  --brief tests/fixtures/publish_readiness_gate_v1/internal_brief.json \
  --score-report tests/fixtures/publish_readiness_gate_v1/signal_quality_score.json \
  --output tmp/dysonx_publish_readiness_gate.json
```

The CLI exits `0` when a valid report is generated, even if every Signal is blocked.

It exits nonzero only for invalid CLI usage, unreadable files, invalid JSON, or write failure.

## 17. Example Output

Example stdout:

```text
[publish-readiness-gate] wrote report: tmp/dysonx_publish_readiness_gate.json signals_evaluated=6 ready=1 blocked=5
```

Example ready evaluation:

```json
{
  "publish_readiness_gate_passed": true,
  "ready_for_public_generation": true,
  "public_generation_blocked": false,
  "gate_decision": "ready_for_public_generation",
  "published": false,
  "publication_approved": false
}
```

## 18. Non-Goals

This PR does not implement:

- public publishing
- automatic publishing
- public website generation
- deployment
- workflow dispatch
- OpenAI call
- web scraping
- source fetching
- Knowledge Graph writes
- Prediction Engine
- Confidence Calibration
- Multi-source Correlation

## 19. How To Test Locally

Run:

```bash
python3 -m unittest tests.test_dysonx_publish_readiness_gate
```

Run the manual fixture command:

```bash
mkdir -p tmp
python3 scripts/dysonx_publish_readiness_gate.py \
  --owner-feedback tests/fixtures/publish_readiness_gate_v1/owner_feedback.json \
  --brief tests/fixtures/publish_readiness_gate_v1/internal_brief.json \
  --score-report tests/fixtures/publish_readiness_gate_v1/signal_quality_score.json \
  --output tmp/dysonx_publish_readiness_gate.json
```

## 20. Recommended Next Step

Public Signal Page Generator V1 after Owner verifies the gate report.
