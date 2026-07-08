# CLAUDE.md

## Project

This repository is the DysonX AI / AGI Signal intelligence and public Signals publishing automation repository.

## Operating Context

This repository belongs to DysonX and the EnergizeOS media publishing context. It supports first-source AI and AGI intelligence tracking, Signal intake, quality review, and public Signals publication.

## Current Purpose

The current practical purpose is to collect high-authority AI / AGI source metadata, convert source material into Signal candidates, synchronize eligible public Signals from Notion, and publish static public output through guarded GitHub workflows.

## Architecture

The repository is a Python-based automation and static publishing pipeline.

Known structure from inspection:

- `README.md` documents the DysonX purpose, Signal-first model, active architecture, public intelligence pipeline, governance files, and validation commands.
- `AGENTS.md` defines existing AI coding-agent rules for DysonX work.
- `.github/workflows/dysonx-source-collector-v1.yml` runs the scheduled Source Collector workflow and uses Notion secrets by name.
- `scripts/` contains pipeline, guard, source collector, quality, and publishing automation scripts.
- `tests/` contains Python tests for the DysonX pipeline and safety gates.
- `docs/` contains DysonX architecture, governance, source collector, public sync, and owner-intent documentation.
- `signals/` contains public Signal output.
- `tmp/` is used by local or workflow-generated diagnostics and audit output.

There is no `package.json` in the repository root based on inspection.

## Brand / UI Rules

This repository contains public Signals HTML/static output. Apply these rules to any public page or static output change:

- Desktop, tablet, and mobile layouts must be precisely responsive.
- Every release must be checked for responsive layout before publishing.
- Horizontal scrolling must be prevented on all screen sizes.
- Every public HTML page must include proper social preview metadata.
- Every public HTML page must include a strongly relevant title, description, favicon, and preview image.
- PNG preview images are preferred over SVG when social sharing compatibility matters.
- Use the correct company VI based on the brand involved.
- If no company brand applies, use Andy Gong / GONG-VI.
- Do not use dark color schemes unless the repository's VI explicitly requires it.
- Do not expose private source, credentials, or internal logic in public pages.
- All code, comments, filenames, and UI copy must be English.

For this repository:

- Preserve DysonX as an AI / AGI Intelligence OS, not a generic news or RSS site.
- Keep the product Signal-first, not Article-first.
- Keep monitored sources managed by Notion, not hardcoded permanently in code.
- Public output must remain quality-gated and attribution-safe.
- Public output must not copy raw article bodies.
- Avoid generic content-farm or thin SEO page behavior.

## Hard Rules

- Do not modify unrelated files.
- Do not add dependencies unless explicitly approved.
- Do not change deployment structure unless explicitly approved.
- Do not change public routes unless explicitly approved.
- Do not commit credentials, tokens, API keys, OAuth secrets, private keys, or environment variable values.
- Do not put secrets in frontend HTML or public JavaScript.
- Keep changes minimal, purposeful, and reversible.
- All generated repository content must be English-only.
- Update docs/todo-next.md at the end of every coding session.

## Session Handoff Rule

Every coding session must end by updating:

- docs/decision-log.md if a decision changed
- docs/change-log.md if files changed
- docs/todo-next.md with exact next steps

If docs/change-log.md does not exist and files were changed, create it.
