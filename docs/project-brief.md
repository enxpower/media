# Project Brief

## Repository

enxpower/media

## Purpose

This repository supports DysonX, an AI / AGI intelligence system that tracks high-authority AI and AGI source material as structured Signals rather than generic articles.

## Public / Private Status

The repository is public and appears public-facing. It also contains internal automation scripts and GitHub workflows that interact with Notion using repository secrets.

## Current Known Structure

- `README.md` — DysonX product purpose, Signal-first principles, pipeline overview, governance references, and validation commands.
- `AGENTS.md` — existing AI coding-agent instructions and stop conditions.
- `docs/` — DysonX architecture, governance, source collector, public sync, and owner-intent documentation.
- `.github/workflows/` — scheduled and manual GitHub Actions automation.
- `.github/workflows/dysonx-source-collector-v1.yml` — scheduled Source Collector workflow using Notion secret names.
- `scripts/` — Python automation, guards, source collection, scoring, public sync, and static preview checks.
- `tests/` — Python regression and safety tests.
- `signals/` — public Signal output.
- `tmp/` — local or workflow diagnostic output location.

## Deployment / Runtime

The repository uses Python scripts and GitHub Actions workflows. Public output is generated as static files and guarded by public Signals sync and auto-merge workflows. Exact production hosting should be verified before changing deployment behavior.

## Related Brand / Domain

- DysonX
- EnergizeOS media context
- `dysonx.com` appears in public Signal URLs in recent repository history.
- Related production domain: To verify before deployment changes.

## Important Constraints

- DysonX must remain an AI / AGI Intelligence OS, not a generic news site.
- The core content object is `Signal`, not `Article`.
- Monitored source configuration belongs in Notion, not permanent hardcoded source lists.
- Public output must remain quality-gated and attribution-safe.
- Workflows use secret names only; never commit secret values.
- Public output must not copy raw article bodies.
- No deployment or merge without explicit owner approval.

## What Future AI Agents Must Understand

- Read `AGENTS.md` and the DysonX governance docs before changing code.
- Treat GitHub and repository docs as the source of truth, not old chat history.
- Keep changes small and reversible.
- Do not weaken source, copyright, topic, raw-body, or auto-merge gates.
- Do not turn public Signals into generic SEO content.
- Run the documented Python guard and test commands when code changes are made.
- Update this context pack at the end of each coding session.
