# DysonX Public Signals Auto-Merge V1

## Purpose

Public Signals Auto-Merge V1 removes the daily manual merge step only for the existing Notion public Signals content PR path.

It is not a new launch step, product milestone, publishing architecture, UI redesign, deployment system, source collector, scraper, or OpenAI workflow.

Allowed chain:

```text
DysonX Sources
-> Signal Intake
-> Public Signals Sync PR
-> strict auto-merge gate
-> automatic squash merge
-> public page updates
```

## Eligible PR Scope

Auto-merge may consider only PRs created by the existing public Signals sync workflow.

Required PR identity:

- Title exactly equals `content: sync DysonX public Signals from Notion`.
- Head branch starts with `automation/dysonx-notion-signals-`.
- PR is not draft.
- PR is from the same repository, not a fork.
- PR body contains `AUTO_MERGE_CANDIDATE: dysonx-public-signals-v1`.

Allowed changed files:

- `signals/index.html`
- `signals/public_launch_manifest.json`
- `signals/<slug>/index.html`

Any file outside `signals/` blocks auto-merge.

## Emergency Kill Switch

Repository variable:

```text
DYSONX_PUBLIC_SIGNALS_AUTO_MERGE
```

Auto-merge runs only when:

```text
DYSONX_PUBLIC_SIGNALS_AUTO_MERGE=true
```

If the variable is missing or any value other than `true`, the gate may run and report, but no merge is performed.

Emergency disable method:

```text
DYSONX_PUBLIC_SIGNALS_AUTO_MERGE=false
```

## Strict Gate Rules

Every changed public Signal page must have a matching manifest entry and pass:

- `quality_hint >= 92`
- `source_priority = Critical`
- `attribution_status = Complete`
- `copyright_status = Safe Summary Only`
- `ready_for_pipeline = true`
- `published = true`
- source URL is absolute `http` or `https`
- summary-only public page
- no raw article body markers
- no source-page body copied
- no forbidden deployment host
- no fake test or invalid source domain
- no internal temporary artifact path
- no `script` tags
- no `iframe` tags
- no inline event handlers
- no external JavaScript
- no unknown generated file path

Manifest safety flags must include:

- `openai_call_performed = false`
- `network_source_fetch_performed = false`
- `manual_external_deployment_performed = false`

## Critical-Only Rule

Non-Critical content must not auto-merge.

High and Medium priority Signals may still be generated into a PR, but they require human review and manual merge.

## Manifest Requirements

Public sync manifests must include these fields per launched Signal so the gate can decide without reading Notion:

- `source_name`
- `source_url`
- `source_priority`
- `attribution_status`
- `copyright_status`
- `quality_hint`
- `ready_for_pipeline`
- `published`

## Public Safety Rules

The auto-merge gate does not call OpenAI, fetch sources, scrape source pages, copy raw article bodies, dispatch workflows, or manually deploy.

Public links remain domain-agnostic. Generated public links should use relative public paths by default. Source attribution links may be absolute `http` or `https` URLs.

## Monitoring

Monitor the workflow:

```text
DysonX Public Signals Auto-Merge V1
```

Blocked runs should be treated as normal safety behavior. The fix should be made in Notion source/intake data or in the public sync generator, then allowed to create a new public Signals sync PR.
