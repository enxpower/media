# DysonX Agent Instructions

This repository must be developed GitHub-first through branches and pull requests.

Before doing any work, every Codex, Claude Code, or other AI coding agent must read:

1. `/docs/DYSONX_PRODUCT_CONSTITUTION.md`
2. `/docs/DYSONX_SYSTEM_ARCHITECTURE.md`
3. `/docs/DYSONX_ENGINEERING_GOVERNANCE.md`

Do not edit files before reading these documents.

## Non-negotiable product rules

- DysonX is an AI / AGI Intelligence OS, not a generic news aggregation site.
- English is the default language. Chinese is a user-switchable localization layer.
- The primary content object is `Signal`, not `Article`.
- Monitored sources must be managed by Notion, not permanently hardcoded in code.
- After collection, LLM analysis must be the first major interpretation step.
- The knowledge graph is the long-term asset.
- Quality gates must block thin, duplicated, unsupported, or low-value content.

## Required workflow

1. Read the three governing documents.
2. Explain how the requested task complies with them.
3. Create or use a feature branch.
4. Make small scoped changes.
5. Add or update tests where relevant.
6. Run guards, tests, and build checks.
7. Open a draft PR.
8. Do not merge.
9. Do not deploy.
10. Do not modify production secrets.

## Stop conditions

Stop and report conflict if a task would:

- Turn DysonX into a generic news/blog/RSS site.
- Break English-default / Chinese-switchable architecture.
- Replace Signal-first design with Article-first design.
- Hardcode monitored source lists permanently.
- Bypass LLM analysis or publishing quality gates.
- Generate thin SEO pages or content-farm behavior.
- Touch production deployment, production data, or secrets without explicit owner approval.

Default final statement for agent work:

`No merge or production deployment was performed.`
