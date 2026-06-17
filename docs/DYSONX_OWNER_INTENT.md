# DysonX Owner Intent v1.0

This document records the owner’s intent so future AI coding agents do not depend on chat memory.

## 1. Owner

Owner: Andy Gong

Working style:

- Wants Codex and Claude Code to work GitHub-first.
- Wants to reduce manual local development work.
- Wants AI agents to create branches, commits, checks, and draft PRs in GitHub.
- Does not want agents to merge, deploy, or touch production without explicit approval.

## 2. Core Fear

The owner’s biggest fear is not that development is slow.

The biggest fear is that the product runs off course.

Specific fears:

- DysonX becomes a generic news site.
- DysonX becomes an RSS mirror.
- DysonX becomes an AI summary farm.
- DysonX optimizes for traffic instead of value.
- Codex or Claude Code destroys the foundation while adding features.
- A future task bypasses the architecture and creates technical debt.
- Source lists become hardcoded.
- English-default / Chinese-switchable architecture is broken.
- The system forgets Signal-first design.
- The knowledge graph is skipped.
- Deployment happens accidentally.

## 3. What Success Means

Success means DysonX becomes long-term AI / AGI intelligence infrastructure.

The owner wants DysonX to become a durable system that accumulates:

- First-source intelligence
- Signals
- Source authority history
- Company trackers
- Person trackers
- Model trackers
- AGI capability map
- Research intelligence
- Policy intelligence
- Predictions and outcomes
- Knowledge graph
- Reports

A successful DysonX page should make the reader think:

`I could not get this value from a normal news site.`

## 4. What Failure Means

Failure means DysonX becomes:

- A content farm
- A low-value AI blog
- A rewritten-news website
- A generic technology portal
- A pile of posts with no knowledge graph
- A site built for SEO volume but not decision value

Traffic without intelligence value is not success.

## 5. Development Philosophy

The owner prefers architecture-first development.

Before features:

- Establish constitution
- Establish architecture
- Establish governance
- Establish PR process
- Establish CI guards
- Establish branch protection
- Establish review discipline

Do not rush into feature work if the foundations are not protected.

## 6. Required Agent Behavior

Every AI coding agent must:

- Work through GitHub
- Read AGENTS.md and all governing documents
- Use branches
- Open draft PRs
- Fill out PR checklist
- Run or rely on CI checks
- Report what changed
- Report what was not done
- Avoid broad refactors
- Avoid production deployment
- Avoid production secrets
- Avoid schema changes without migration plan

Every agent final report must include:

`No merge or production deployment was performed.`

## 7. What the Owner Values Most

In priority order:

1. Long-term value
2. Product direction
3. Architecture integrity
4. Governance discipline
5. Source authority
6. Knowledge graph
7. AGI impact interpretation
8. User decision usefulness
9. SEO only when it serves authority
10. Visual polish only after value is protected

## 8. What the Owner Rejects

The owner rejects:

- Shallow content generation
- Random feature additions
- UI polish that hides weak content
- SEO tricks
- Direct production changes
- Hardcoded source lists
- Unreviewed merges
- Local-only workflows that require excessive owner labor
- Agents asking the owner to manually do work that can be done through GitHub

## 9. Preferred AI Development Mode

Preferred mode:

GitHub-first.

The AI agent should use GitHub repository, branch, commit, PR, and Actions workflow as the development surface.

The owner should be able to supervise through:

- GitHub PR
- CI status
- Diff review
- Chat summary

The owner should not need to clone the repo or run local commands unless explicitly choosing to.

## 10. Current Active Governance Work

Repository:

`enxpower/media`

Draft PR:

`https://github.com/enxpower/media/pull/15`

Branch:

`chore/dysonx-governance-foundation`

Purpose:

Establish governance foundation so future Codex / Claude Code sessions understand DysonX’s product intent, architecture, and development rules.

## 11. Operating Instruction for Future Agents

If a future prompt says only:

`Continue DysonX development.`

The agent must still first read:

- AGENTS.md
- DYSONX_PRODUCT_CONSTITUTION.md
- DYSONX_SYSTEM_ARCHITECTURE.md
- DYSONX_ENGINEERING_GOVERNANCE.md
- DYSONX_PROJECT_CONTEXT.md
- DYSONX_OWNER_INTENT.md

Then the agent must inspect open PRs, especially PR #15 if it is still open, before making new changes.

## 12. Final Principle

The owner is not trying to build a website quickly.

The owner is trying to build a system that can evolve for years without losing its soul.

That is the purpose of these governance documents.
