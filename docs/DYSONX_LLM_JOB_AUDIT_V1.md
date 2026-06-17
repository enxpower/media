# DysonX LLM Job & Audit Foundation V1

This document defines the provider-neutral LLM execution and audit foundation
for DysonX V1.

This is not real provider integration. V1 remains fake-provider only and
performs no network requests.

## Target Flow

```text
Signal Candidate
-> LLM Job
-> Prompt Template
-> Model Run
-> Output Validation
-> Intelligence Signal
-> Audit Report
```

## Scope

Allowed in V1:

- Create provider-neutral LLM job records.
- Use versioned prompt templates from a central registry.
- Execute deterministic fake-provider model runs.
- Validate structured model output before creating Intelligence Signals.
- Preserve audit records tying jobs, runs, validations, and output together.
- Generate an audit report with counts and distributions.

Not included in V1:

- OpenAI API calls.
- Anthropic API calls.
- Gemini API calls.
- Local model runtime calls.
- Provider credentials or secrets.
- Publishing.
- Social posting.
- Knowledge Graph writes.
- Prediction Engine behavior.
- Dashboard, billing, enterprise, or multi-tenant features.

## V1 Structures

### LLMJobV1

- `job_id`
- `candidate_id`
- `provider`
- `model`
- `prompt_template_version`
- `status`
- `created_at`

### PromptTemplateV1

- `template_id`
- `template_version`
- `purpose`
- `template_text`

### ModelRunV1

- `run_id`
- `job_id`
- `provider`
- `model`
- `latency_ms`
- `token_counts`
- `status`

### OutputValidationV1

- `validation_id`
- `run_id`
- `passed`
- `warnings`
- `validation_rules`

### AuditRecordV1

- `audit_id`
- `job_id`
- `run_id`
- `validation_id`
- `created_at`

## Prompt Registry

Prompts are registered by `template_id` and `template_version`.

Prompt text must live in the prompt registry, not scattered through provider
execution code. Future real provider integrations should reference a registered
template version and record it in the LLM job.

## Output Validation

V1 validation checks:

- Required fields are present.
- Confidence is in the `0..1` range.
- Importance is one of `low`, `medium`, or `high`.
- Summary is present and non-empty.

Malformed output must be captured as validation failure rather than silently
converted into an Intelligence Signal.

## Audit Report

The V1 audit report includes:

- Jobs created
- Runs completed
- Validations passed
- Validations failed
- Provider distribution
- Prompt versions used
- Job, run, validation, audit record, and signal details
- Confirmation that no real LLM API, network request, or publishing occurred

## Governance Notes

This PR strengthens governance and observability before real model integration.
It keeps the LLM layer provider-neutral, fake-only, and auditable.

No publishing or public distribution path is introduced.
