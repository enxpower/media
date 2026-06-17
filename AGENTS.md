# DysonX Agent Instructions

This repository must be developed GitHub-first through branches and pull requests.

Before doing any work, every Codex, Claude Code, or other AI coding agent must read:

1. `/docs/DYSONX_PRODUCT_CONSTITUTION.md`
2. `/docs/DYSONX_SYSTEM_ARCHITECTURE.md`
3. `/docs/DYSONX_ENGINEERING_GOVERNANCE.md`
4. `/docs/DYSONX_PROJECT_CONTEXT.md`
5. `/docs/DYSONX_OWNER_INTENT.md`

Do not edit files before reading these documents.

## Non-negotiable product rules

- DysonX is an AI / AGI Intelligence OS, not a generic news aggregation site.
- English is the default language. Chinese is a user-switchable localization layer.
- The primary content object is `Signal`, not `Article`.
- Monitored sources must be managed by Notion, not permanently hardcoded in code.
- After collection, LLM analysis must be the first major interpretation step.
- The knowledge graph is the long-term asset.
- Quality gates must block thin, duplicated, unsupported, or low-value content.
- Development must be GitHub-first. Do not ask the owner to clone or run local commands unless explicitly requested.

## Required workflow

1. Read all five governing/context documents.
2. Explain how the requested task complies with them.
3. Inspect open PRs and current branch context.
4. Create or use a feature branch.
5. Make small scoped changes.
6. Add or update tests where relevant.
7. Run guards, tests, and build checks where available.
8. Open or update a draft PR.
9. Do not merge.
10. Do not deploy.
11. Do not modify production secrets.

## New-session recovery

If a new AI coding-agent session starts with limited chat memory, it must recover project context from the repository itself:

1. Read this `AGENTS.md` file.
2. Read all five documents listed above.
3. Inspect open PRs, especially governance PRs.
4. Treat GitHub as the source of truth, not prior chat memory.

## Stop conditions

Stop and report conflict if a task would:

- Turn DysonX into a generic news/blog/RSS site.
- Break English-default / Chinese-switchable architecture.
- Replace Signal-first design with Article-first design.
- Hardcode monitored source lists permanently.
- Bypass LLM analysis or publishing quality gates.
- Generate thin SEO pages or content-farm behavior.
- Touch production deployment, production data, or secrets without explicit owner approval.
- Require unnecessary local owner labor when the work can be done through GitHub.

Default final statement for agent work:

`No merge or production deployment was performed.`
