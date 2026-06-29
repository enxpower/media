# DysonX Signal Intake Schema Fix V1

## Purpose

DysonX public Signals automation now carries source priority from DysonX Sources into Signal Intake and then into the public launch manifest.

This lets the Public Signals Auto-Merge Gate make deterministic decisions without reading Notion during merge.

## Required Signal Intake Property

Add this property to the DysonX Signal Intake database:

```text
Source Priority
```

Type:

```text
Select
```

Allowed options:

- `Critical`
- `High`
- `Medium`
- `Low`

## Why This Is Required

The auto-merge gate intentionally remains strict:

- `Quality Hint >= 92`
- `source_priority = Critical`
- `Attribution Status = Complete`
- `Copyright Status = Safe Summary Only`
- `Ready for Pipeline = true`
- `Published = true`

Source Collector V1 reads source priority from DysonX Sources and includes it in generated Signal candidates. If Signal Intake supports `Source Priority`, the collector writes that select value. Public Signals Sync then copies the value into `signals/public_launch_manifest.json` as `source_priority`.

Without this property, source-collected Signals may still appear in Signal Intake, but the public auto-merge gate cannot prove they are Critical-source Signals and will block automatic merge.

## Safety Boundary

This schema fix does not relax the auto-merge gate, lower quality thresholds, permit non-Critical auto-merge, call OpenAI, scrape source-page bodies, copy raw article bodies, dispatch workflows, or deploy.
