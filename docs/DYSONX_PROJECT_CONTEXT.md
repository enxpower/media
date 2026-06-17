# DysonX Project Context v1.0

This document exists so a new Codex, Claude Code, or other AI coding-agent session can understand the origin, intent, and product logic behind DysonX without relying on chat history.

## 1. Origin

DysonX started from the owner’s desire to build a focused AI / AGI intelligence engine, not a broad technology news site.

The original site began as a news aggregation experiment. That is useful as an input layer, but it is not the long-term product.

The project evolved after recognizing that normal news aggregation, RSS mirroring, and AI summaries are low-value and easy to replace.

The real opportunity is to convert first-source AI information into structured intelligence, long-term memory, and decision value.

## 2. Why This Project Exists

The AI / AGI field moves too quickly for ordinary news reading.

Important signals appear across:

- Official company blogs
- Research labs
- Papers
- GitHub repositories
- Government and regulatory sources
- Product changelogs
- Direct statements from key people
- Conferences and technical talks
- High-authority media

A normal reader, founder, investor, CTO, or researcher cannot reliably track all of this manually.

DysonX exists to monitor these first-source signals, understand them with LLMs, map them to AGI capabilities, and preserve them in a long-term knowledge graph.

## 3. What DysonX Is

DysonX is an AI / AGI Intelligence OS.

It should help decision-makers understand:

- What happened
- Where it came from
- Whether the source is authoritative
- Why it matters
- Which AGI capability it affects
- Which companies and people are involved
- What changed compared to previous signals
- What should be watched next

DysonX should feel closer to an intelligence terminal than a blog.

## 4. What DysonX Is Not

DysonX is not:

- A generic news site
- An RSS aggregation site
- A rewritten article site
- A general technology blog
- A content farm
- A thin AI-summary website
- A viral-content machine
- A generic SEO publishing system

If development starts optimizing for content volume, clickbait, or low-quality SEO, the product is drifting away from its purpose.

## 5. Core Product Philosophy

The core philosophy is:

- Signal > Article
- Knowledge > News
- Decision > Content
- Asset > Traffic
- Source authority > Speed
- Long-term memory > Daily noise
- Interpretation > Rewriting
- Trackers and graph > Flat posts

A news item expires quickly. A structured Signal can strengthen trackers, the AGI Map, company intelligence, person intelligence, reports, and predictions.

## 6. Why Signal Is the Core Object

An Article mainly says what happened.

A Signal captures why it matters.

A Signal should preserve:

- Original source
- Authority score
- Confidence score
- AGI impact score
- Related entities
- Related capabilities
- DysonX Take
- Watch Next
- Connections to trackers, reports, and predictions

This makes each item reusable across the entire intelligence system.

## 7. Why Knowledge Graph Matters

The long-term asset is not a pile of posts.

The long-term asset is a structured AI industry memory:

- Companies
- People
- Models
- Products
- Papers
- GitHub projects
- Policies
- Events
- AGI capabilities
- Predictions
- Outcomes

Years later, DysonX should be able to answer questions like:

- What did OpenAI do in agent infrastructure over the past 12 months?
- Which companies advanced world models?
- Which people changed their AGI views?
- Which predictions were correct?
- Which research ideas became products?

A flat news archive cannot do this. A knowledge graph can.

## 8. Why English Default and Chinese Switchable

DysonX targets global AI / AGI intelligence.

English is the default because most first-source AI materials, papers, company announcements, technical documentation, and global SEO demand English-first structure.

Chinese is important, but it should be a localization layer.

The architecture must use English canonical routes, keys, metadata, and structured data, with Chinese available through user switch and localized fields.

## 9. Why Sources Must Be Managed by Notion

The owner wants monitored sources to be dynamically editable without changing code.

Sources may include companies, people, organizations, papers, social accounts, GitHub repositories, government pages, and other high-value first sources.

Therefore monitored source configuration must live in Notion, not hardcoded arrays.

The code can cache Notion config, but Notion remains the source of truth.

## 10. Why LLM Analysis Must Come After Collection

Traditional rules cannot reliably judge:

- Importance
- AGI relevance
- Technical meaning
- Duplicate relationship
- Entity relationships
- Strategic impact
- Whether a paper is product-relevant
- Whether a statement changes the landscape

After raw content is collected, the next major step must be LLM interpretation.

Rules may assist. Rules must not replace LLM understanding.

## 11. Long-Term Product Destination

The long-term target is AI / AGI intelligence infrastructure.

Potential future surfaces:

- Signal feed
- AGI Map
- Company trackers
- Person trackers
- Model trackers
- Paper trackers
- Policy trackers
- Prediction database
- Daily brief
- Weekly AGI intelligence report
- Enterprise monitoring
- API access
- Custom competitor intelligence

The product should evolve gradually, but every phase must strengthen the intelligence asset.

## 12. Evolution Roadmap

Phase 1: Governance foundation

- Constitution
- Architecture
- Engineering governance
- AGENTS instructions
- PR template
- CI guards

Phase 2: Signal Engine

- Source database integration
- Raw item collection
- LLM analysis
- Signal schema
- Quality gate

Phase 3: Knowledge Graph

- Entity extraction
- Relationships
- AGI capability mapping
- Tracker generation

Phase 4: Publishing and Distribution

- Signal pages
- English / Chinese localization
- SEO metadata
- Social drafts
- Newsletter support

Phase 5: Reports and Prediction

- Daily and weekly briefs
- Company strategy reports
- Research-to-business translation
- Prediction and review system

Phase 6: Enterprise Intelligence

- Custom monitoring
- Team dashboards
- Private reports
- API access

## 13. Current Repository Context

Current repository:

`enxpower/media`

Current governance PR:

`https://github.com/enxpower/media/pull/15`

Current governance branch:

`chore/dysonx-governance-foundation`

This repository originally contains an EnergizeOS-style news aggregator. Future work should gradually migrate it toward DysonX AI / AGI Intelligence OS without breaking the existing site unexpectedly.

## 14. How Future Agents Should Use This Document

When starting a new session, read this file after AGENTS.md and before implementation.

Use it to understand the story behind the rules.

The governing order is:

1. AGENTS.md
2. DYSONX_PRODUCT_CONSTITUTION.md
3. DYSONX_SYSTEM_ARCHITECTURE.md
4. DYSONX_ENGINEERING_GOVERNANCE.md
5. DYSONX_PROJECT_CONTEXT.md
6. DYSONX_OWNER_INTENT.md

If chat instructions conflict with these documents, stop and ask for clarification before implementing.
