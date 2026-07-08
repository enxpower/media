# Next Tasks

## Current Status

The repository has a documented DysonX Signal-first architecture, existing AI-agent governance in `AGENTS.md`, Python automation scripts, tests, public Signal output, and GitHub Actions workflows that run Source Collector and public Signals publishing logic.

## Next Recommended Tasks

1. Verify the current production hosting path and canonical public domain before changing any SEO, CNAME, or public route behavior.
2. Review open PRs and recent workflow runs before modifying Source Collector, public sync, or auto-merge logic.
3. Confirm whether `DYSONX_PUBLIC_SIGNALS_AUTO_MERGE` should remain enabled before changing publishing gate behavior.
4. Keep the Source Collector workflow from writing public static files unless the public sync workflow is explicitly responsible for that output.
5. Run the documented guard and test commands after any script or workflow change.
6. Review public Signal pages for responsive layout, metadata, favicon, and preview image completeness before any public release.
7. Keep this Project Context Pack updated when architecture, workflow, or gate decisions change.

## Do Not Do

- Do not refactor the full pipeline before reading the DysonX governance docs.
- Do not add dependencies without explicit approval.
- Do not change public routes without explicit approval.
- Do not weaken source, attribution, copyright, topic, or raw-body gates.
- Do not hardcode monitored source lists permanently in code.
- Do not expose Notion tokens or other secret values.
- Do not merge or deploy without explicit owner approval.

## Handoff Prompt

Continue this repository from its project context.

First read:
1. CLAUDE.md
2. docs/project-brief.md
3. docs/decision-log.md
4. docs/todo-next.md
5. docs/acceptance-checklist.md

Then summarize the current state in no more than 8 bullets and execute only the next task listed in docs/todo-next.md. Do not change scope.
