# DysonX Public Signal Page Generator V1

## 1. Purpose

Public Signal Page Generator V1 is Step 2 of the strict 5-Step Final Launch Plan:

```text
Owner Review Wizard
-> Publish Readiness Gate
-> Public Signal Page Generator
-> Public Signals Index
-> Local Public Preview
-> Manual Publish Approval
-> media.energizeos.com
```

It generates static draft public Signal preview pages from Publish Readiness Gate-approved Signals.

This step supports functional publishing before aesthetic polish while preserving quality and safety gates before public release.

## 2. Boundary

Generated page draft is not publication.

Local preview is not publication.

`ready_for_public_generation: true` is not publication approval.

`publish_readiness_gate_passed: true` is not publication approval.

Manual Publish Approval V1 is still required before production release.

## 3. CLI

```bash
python3 scripts/dysonx_public_signal_page_generator.py \
  --gate-report tests/fixtures/public_signal_page_generator_v1/publish_readiness_gate_report.json \
  --output-dir tmp/public_signal_pages
```

The CLI reads a local Publish Readiness Gate report and writes static draft preview artifacts under:

```text
tmp/public_signal_pages/
```

It uses only Python standard library modules.

## 4. Input Rule

The generator may process only Signals where all are true:

- `publish_readiness_gate_passed` is `true`
- `ready_for_public_generation` is `true`
- `public_generation_blocked` is `false`
- `published` is `false` or absent
- `publication_approved` is `false` or absent

Any Signal outside that boundary is blocked from draft page generation.

## 5. Output Structure

Generated files:

```text
tmp/public_signal_pages/signals/<slug>/index.html
tmp/public_signal_pages/signals/index.html
tmp/public_signal_pages/public_signal_pages_manifest.json
tmp/public_signal_pages/README.md
```

The README contains local preview instructions:

```bash
python3 -m http.server --directory tmp/public_signal_pages 8080
```

Then visit:

```text
http://localhost:8080/signals/
```

## 6. Public Signal Draft Page Requirements

V1 pages may be visually simple. They must still be:

- credible
- clear
- source-attributed
- copyright-safe
- readable
- previewable
- gate-approved

Each generated Signal draft page includes:

- Signal title
- slug
- Draft Preview / Not Published status
- generated timestamp
- short summary
- why this matters
- AGI relevance
- source attribution
- source URLs or source references when available
- quality score / confidence summary
- risk / safety notes
- Manual Publish Approval V1 required notice
- link back to the Signals index

## 7. Forbidden Output

The generator must not include:

- raw article body
- internal Owner comments
- internal decision trail leakage
- private review state
- misleading published status
- ads
- tracking
- external runtime JavaScript dependency
- OpenAI calls
- network fetches

The generator must escape HTML content.

## 8. Manifest

The manifest records:

- generator version
- input file
- output directory
- generated pages
- blocked Signals
- safety flags
- Manual Publish Approval V1 requirement

Safety fields must state:

- `no_public_publishing_performed: true`
- `no_deployment_performed: true`
- `no_openai_call_performed: true`
- `no_workflow_dispatch_performed: true`
- `manual_publish_approval_required: true`
- `production_publish_performed: false`

## 9. Non-Goals

This step does not implement:

- production publishing
- production deployment
- Manual Publish Approval V1
- Production Publish Pack
- workflow dispatch
- OpenAI calls
- scraping
- backend APIs
- database storage
- Knowledge Graph writes
- Prediction Engine
- Confidence Calibration
- Multi-source Correlation
- social distribution
- final public visual polish

No production deployment is authorized by this document.
