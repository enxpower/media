# DysonX Engineering Governance v1.0

DysonX will be built over time. The greatest risk is not slow development. The greatest risk is architecture drift, value drift, and accidental destruction of the foundation.

Codex, Claude Code, and any AI coding agent must be constrained by process, not by memory or good intentions.

## Required Reading Before Every Task

Before any implementation work, the agent must read:

1. `/docs/DYSONX_PRODUCT_CONSTITUTION.md`
2. `/docs/DYSONX_SYSTEM_ARCHITECTURE.md`
3. `/docs/DYSONX_ENGINEERING_GOVERNANCE.md`

The agent must not proceed until it can confirm:

- The product is English-default and Chinese-switchable.
- The primary content object is Signal, not Article.
- Sources are managed by Notion, not hardcoded.
- LLM analysis is the first major interpretation step after collection.
- The knowledge graph is the long-term asset.
- The system must not become a generic news site.

## Required Opening Prompt

Every Codex / Claude Code task prompt should begin with:

```text
Before doing anything, read:

/docs/DYSONX_PRODUCT_CONSTITUTION.md
/docs/DYSONX_SYSTEM_ARCHITECTURE.md
/docs/DYSONX_ENGINEERING_GOVERNANCE.md

Then briefly explain how this task complies with them.

Do not implement anything that conflicts with these documents.
If there is a conflict, stop and report it.
Do not modify production deployment files.
Do not merge.
Do not deploy.
Open a draft PR only.
```

## Branching Model

- `main` = production only, protected
- `dev` = integration branch
- `feature/*` = individual feature work
- `fix/*` = bug fixes
- `chore/*` = maintenance
- `docs/*` = documentation

Codex and Claude Code must not commit directly to `main`.

Preferred flow:

`feature branch -> draft PR -> review -> dev -> staging -> production PR -> main`

## Development Workflow

Every task must follow this order:

1. Read constitution, architecture, and governance.
2. Inspect current repository state.
3. Write a short implementation plan.
4. Identify files to be changed.
5. Make small, scoped changes.
6. Add or update tests.
7. Run formatting / linting.
8. Run unit tests.
9. Run build.
10. Run architecture or constitution guard checks.
11. Produce a summary of changes.
12. Open a draft PR.
13. Do not merge.
14. Do not deploy.

## Forbidden Actions

Codex and Claude Code must not:

- Push directly to `main`
- Merge PRs without explicit human approval
- Deploy production without explicit human approval
- Delete core data models without review
- Rewrite architecture without updating governing documents
- Hardcode monitored source lists
- Replace Signal with Article as the primary object
- Break English-default routing
- Remove Chinese localization capability
- Bypass LLM analysis after collection
- Bypass quality gates
- Generate SEO garbage pages
- Modify production secrets
- Print secrets in logs
- Modify live database schema without migration plan
- Remove tests to make CI pass
- Disable CI checks without approval
- Hide failing tests
- Make broad unrelated refactors inside feature PRs

## PR Requirements

Every PR must include:

- Purpose
- Scope
- Files changed
- Constitution compliance checklist
- Architecture impact
- Tests run
- Build result
- Deployment impact
- Rollback notes
- Known limitations

## Required Checks

Every PR must confirm:

- It read all governing documents.
- It does not turn DysonX into a generic news site.
- It preserves English-default / Chinese-switchable architecture.
- It preserves Signal-first design.
- It does not hardcode monitored sources.
- It keeps LLM analysis as the first major interpretation step after collection.
- It strengthens knowledge graph, trackers, reports, distribution, or governance value.
- It does not bypass the quality gate.
- It does not create thin SEO content.
- Tests passed.
- Build passed.
- No production deployment was performed.

## Testing Principles

Testing must protect product value, not only code syntax.

Minimum test categories:

- Unit tests
- Integration tests
- Build tests
- Route tests
- Localization tests
- Source configuration tests
- LLM output schema tests
- Quality gate tests
- Knowledge graph tests
- SEO metadata tests
- Social draft generation tests

Critical tests should verify:

- English remains default.
- Chinese switch remains available.
- Signal remains the primary content model.
- Permanent hardcoded source lists are not introduced.
- Raw items are not published directly.
- LLM output schema is valid.
- Quality gate blocks low-value content.

## CI Requirements

CI should run at least:

- Install dependencies
- Type check or syntax check
- Lint
- Unit tests where available
- Build where available
- Route smoke test where available
- Constitution guard
- Architecture guard
- Secret scan

A PR must not be merged if required CI fails.

## Guard Types

### Constitution Guard

Flags drift in product principles: missing docs, generic news framing, Article-first model, hardcoded sources, broken English default, bypassed LLM or quality gate.

### Architecture Guard

Flags broken system layering: source-to-page publishing, UI directly fetching raw sources, publishing without quality status, missing source attribution, missing raw item retention, and cross-layer scripts with too many responsibilities.

### Release Guard

Checks build, routes, mobile/no-horizontal-scroll expectations, SEO metadata, sitemap/feed behavior, env/secrets, and deployment risk.

## Database and Migration Rules

Schema changes require migration file, rollback strategy, data preservation plan, test coverage, staging validation, and explicit mention in PR.

Forbidden:

- Silent schema changes
- Manual production schema edits without record
- Deleting columns or tables without backup and approval
- Mixing experimental schema with production data

## Secrets and Environment Rules

Secrets must never be printed, committed, or included in PR summaries.

Production secrets must not be modified by Codex or Claude Code unless the owner explicitly authorizes that exact action.

## Deployment Rules

Allowed AI-agent actions:

- Create feature branch
- Modify code
- Run tests
- Open draft PR
- Prepare deployment notes

Not allowed without explicit human approval:

- Merge to main
- Deploy production
- Modify production server files
- Modify production secrets
- Run destructive production commands

## Completion Standard

At the end of every task, the agent must report:

- Files changed
- What was implemented
- Tests run
- Build status
- Constitution compliance summary
- Architecture impact
- Any skipped items
- Whether PR was opened
- Whether merge/deploy was performed

Default must be: no merge, no deploy.
