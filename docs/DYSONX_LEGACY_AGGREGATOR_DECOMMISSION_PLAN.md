# DysonX Legacy Aggregator Decommission Plan

Date: 2026-06-17

Branch: `chore/dysonx-legacy-aggregator-decommission-plan`

Base: `audit/dysonx-v1-dry-run-milestone-review`

Status: Planning and audit only. No legacy code deletion, real Notion API use,
real LLM API use, collector execution, publishing, deployment, or merge is
included.

## Governance Inputs Reviewed

Governance documents reviewed before this plan:

- `AGENTS.md`
- `docs/DYSONX_OWNER_INTENT.md`
- `docs/DYSONX_PROJECT_CONTEXT.md`
- `docs/DYSONX_PRODUCT_CONSTITUTION.md`
- `docs/DYSONX_SYSTEM_ARCHITECTURE.md`
- `docs/DYSONX_ENGINEERING_GOVERNANCE.md`

PR stack reviewed:

- PR #22: Source Intake V1
- PR #23: Signal Candidate Pipeline V1
- PR #24: LLM Intelligence Layer V1
- PR #25: Governance & Architecture Audit
- PR #26: LLM Job & Audit Foundation V1
- PR #27: Signal Scoring & Ranking Engine V1
- PR #28: Quality Review Gate V1
- PR #29: Publish Package V1
- PR #30: V1 Pipeline Orchestrator
- PR #31: V1 Dry-Run Milestone Review

At review time, PRs #22 through #31 were open draft PRs with clean merge
status.

## Executive Decision

The old main-branch news/RSS aggregation product has no long-term value for
DysonX and should be removed instead of preserved.

This plan recommends decommissioning the legacy EnergizeOS news aggregator in
small PRs while keeping the new DysonX V1 dry-run pipeline intact.

The replacement path is not a rewritten news site. The replacement path is:

```text
Notion-managed Sources
-> Raw Items
-> Signal Candidates
-> Provider-neutral LLM Job / Audit
-> Intelligence Signals
-> Scoring / Ranking
-> Quality Review
-> Publish Packages
-> Future Signal publishing
```

## Current Legacy Surface

### Legacy Runtime Scripts

Likely legacy-only:

- `scripts/aggregator.py`
  - Fetches RSS feeds with `feedparser`.
  - Optionally fetches full text with `newspaper.Article`.
  - Calls OpenAI directly for news summaries.
  - Categorizes articles with fixed energy tags.
  - Writes generated post pages.
  - Mixes collection, summarization, categorization, rendering, and publishing.

- `scripts/openai_summary.py`
  - Direct OpenAI SDK wrapper for old news summaries.
  - Produces English and Chinese article summaries.
  - Uses `OPENAI_API_KEY` directly.
  - Is not provider-neutral and is not part of the DysonX LLM job/audit layer.

- `scripts/generate_sitemap.py`
  - Generates `sitemap.xml` from legacy `posts/page*.html`.
  - Uses `https://media.energizeos.com`.
  - Should be replaced by a future DysonX Signal sitemap generator after
    publishing exists.

### Legacy Source and Output Files

Likely legacy-only:

- `feeds.json`
  - Hardcoded RSS source list.
  - Conflicts with the Notion Source Rule if retained as monitored source
    truth.

- `posts/page1.html`
- `posts/page2.html`
- `posts/page3.html`
- `posts/page4.html`
  - Generated legacy article/news pages.
  - Should not be treated as DysonX canonical content.

- `sitemap.xml`
  - Legacy sitemap generated from root and `posts/page*.html`.

- `index.html`
  - Current legacy public entry point for the old news site.
  - Should eventually be replaced by a DysonX Intelligence OS entry point or
    preview surface after the Signal publishing path exists.

### Legacy UI Assets

Likely legacy-only or needs review before deletion:

- `components/langToggle.js`
- `components/search.js`
- `components/pagination.js`
- `components/pagination-bottom.js`
- `components/pagination-dup.js`
- `components/shareButtons.js`
- `components/shareTracker.js`
- `components/outboundTracker.js`
- `components/nativeAds.js`
- `components/ops.js`
- `components/footer.js`
- `styles/main.css`

These files appear tied to the static legacy news pages. Some concepts may be
reused later, such as language switching or outbound analytics, but they should
not be preserved automatically unless a future DysonX UI uses them explicitly.

### Legacy Automation

Likely legacy-only:

- `.github/workflows/update.yml`
  - Manual workflow that runs `scripts/aggregator.py` and
    `scripts/generate_sitemap.py`, then commits generated content.

- `.github/workflows/update-content.yml`
  - Hourly aggregation workflow.
  - Uses `OPENAI_API_KEY`.
  - Runs the aggregator and sitemap generator.
  - Commits `posts/` and `sitemap.xml`.

Needs separate review:

- `.github/workflows/sync-content.yml`
- `.github/workflows/validate-ads.yml`

These workflows appear related to public content synchronization and ad
validation. They should be audited before deletion because they may contain
deployment or public-branch assumptions.

### Legacy Dependency Surface

Likely removable after the aggregator is removed:

- `feedparser==6.0.11`
- `newspaper3k==0.2.8`
- `lxml_html_clean==0.1.1`
- `nltk==3.8.1`

Needs review before removal:

- `openai>=1.51.0,<2`

The legacy scripts use the OpenAI SDK directly, but DysonX V1 currently uses a
fake provider and has no real provider dependency. Future real LLM integration
should add provider dependencies intentionally through the provider-neutral LLM
layer, not inherit them from legacy summary code.

## Files Likely To Remove

Recommended first-pass deletion candidates:

- `.github/workflows/update.yml`
- `.github/workflows/update-content.yml`
- `scripts/aggregator.py`
- `scripts/openai_summary.py`
- `scripts/generate_sitemap.py`
- `feeds.json`
- `posts/page1.html`
- `posts/page2.html`
- `posts/page3.html`
- `posts/page4.html`
- `sitemap.xml`

Recommended second-pass deletion or replacement candidates:

- `index.html`
- `components/*.js`
- `styles/main.css`
- old EnergizeOS README wording
- legacy-only Python dependencies in `requirements.txt`
- content sync and ad validation workflows if confirmed unrelated to DysonX

## Files Likely To Keep

Keep:

- `AGENTS.md`
- `docs/DYSONX_*.md`
- `.github/pull_request_template.md`
- guard scripts:
  - `scripts/constitution_guard.py`
  - `scripts/architecture_guard.py`
  - `scripts/release_guard.py`
- DysonX V1 modules:
  - `scripts/dysonx_schema.py`
  - `scripts/dysonx_notion_source_schema.py`
  - `scripts/dysonx_source_config_loader.py`
  - `scripts/dysonx_notion_readonly_adapter.py`
  - `scripts/dysonx_source_intake.py`
  - `scripts/dysonx_raw_item.py`
  - `scripts/dysonx_signal_candidate_pipeline.py`
  - `scripts/dysonx_intelligence_signal.py`
  - `scripts/dysonx_llm_intelligence_layer.py`
  - `scripts/dysonx_llm_job.py`
  - `scripts/dysonx_prompt_registry.py`
  - `scripts/dysonx_output_validation.py`
  - `scripts/dysonx_llm_audit.py`
  - `scripts/dysonx_signal_scoring.py`
  - `scripts/dysonx_signal_ranking.py`
  - `scripts/dysonx_quality_review.py`
  - `scripts/dysonx_publish_eligibility.py`
  - `scripts/dysonx_seo_metadata.py`
  - `scripts/dysonx_social_draft.py`
  - `scripts/dysonx_publish_package.py`
  - `scripts/dysonx_v1_pipeline.py`
- DysonX V1 tests and fixtures under `tests/`.

## Dependency Map

Legacy path:

```text
feeds.json
-> scripts/aggregator.py
-> feedparser
-> newspaper3k / lxml_html_clean / nltk
-> OpenAI SDK direct call
-> posts/page*.html
-> scripts/generate_sitemap.py
-> sitemap.xml
-> .github/workflows/update.yml
-> .github/workflows/update-content.yml
```

Legacy public surface:

```text
index.html
-> components/*.js
-> styles/main.css
-> posts/page*.html
-> sitemap.xml
```

DysonX V1 dry-run path:

```text
tests/fixtures/raw_items_v1.json
-> scripts/dysonx_signal_candidate_pipeline.py
-> scripts/dysonx_llm_audit.py
-> scripts/dysonx_signal_ranking.py
-> scripts/dysonx_publish_eligibility.py
-> scripts/dysonx_publish_package.py
-> scripts/dysonx_v1_pipeline.py
-> tmp/dysonx_v1_pipeline/*.json
```

The V1 dry-run path does not import `scripts/aggregator.py` or
`scripts/openai_summary.py`.

## Risks

- Removing the workflows will stop the old public site from updating. This is
  expected and aligned with the owner decision, but should be called out in the
  deletion PR.
- Removing `index.html` before a DysonX landing or preview surface exists may
  leave GitHub Pages without a useful root page.
- Removing `requirements.txt` dependencies too early may break legacy workflows
  if those workflows are not removed in the same PR.
- Existing release guard checks currently inspect `index.html` and sitemap/feed
  behavior. Guard expectations may need a governance-aligned update when the
  legacy static site is removed.
- Public sync or ad validation workflows may contain assumptions about public
  branch state. They should be audited before removal.
- Search engines may retain old EnergizeOS URLs temporarily after generated
  pages are removed.
- Any accidental reuse of `openai_summary.py` would bypass the provider-neutral
  LLM job/audit layer.

## Deletion Order

Recommended sequence:

1. Disable legacy automation.

   Remove or archive `.github/workflows/update.yml` and
   `.github/workflows/update-content.yml` first so deleted generated files are
   not recreated by scheduled jobs.

2. Remove legacy aggregation scripts and hardcoded RSS sources.

   Delete `scripts/aggregator.py`, `scripts/openai_summary.py`, and
   `feeds.json`.

3. Remove generated legacy outputs.

   Delete `posts/page*.html`, `sitemap.xml`, and any legacy caches if tracked.

4. Replace repository identity.

   Update `README.md` from EnergizeOS News Aggregator to DysonX Intelligence OS
   with clear notes that real integrations and publishing are not enabled yet.

5. Replace or remove public static shell.

   Either replace `index.html` with a minimal DysonX governance-aligned preview
   page or remove legacy public UI when the future DysonX Signal publishing
   surface exists.

6. Remove legacy UI assets.

   Delete `components/` and `styles/` only after confirming no DysonX page uses
   them.

7. Prune dependencies and guards.

   Remove legacy dependencies from `requirements.txt` and update release guard
   expectations so checks reflect DysonX, not the old static news site.

## Rollback Strategy

Rollback should be PR-based:

- Keep each deletion PR small and reversible.
- If a deletion breaks checks unexpectedly, revert only that deletion PR.
- Do not re-enable scheduled legacy aggregation unless the owner explicitly
  requests it.
- Preserve Git history as the archival source for removed legacy code.
- If a public placeholder is needed, add a DysonX-aligned static page rather
  than restoring the old news aggregator.

## What Replaces Legacy Functionality

Legacy RSS aggregation replacement:

- V1 Source Intake from Notion-managed source configuration.
- Future collectors that write RawItems without deciding publish status.

Legacy article summary replacement:

- Provider-neutral LLM Job and Audit layer.
- Prompt registry.
- Output validation.
- Intelligence Signal generation.

Legacy article page replacement:

- Future Signal publishing path behind Quality Review Gate.
- Publish Package V1 metadata as the pre-publishing object.

Legacy social share replacement:

- SocialDraft records with `draft_only` status.
- Future distribution path must remain draft-first and reviewable.

Legacy sitemap replacement:

- Future DysonX Signal sitemap generated from published Signals only.

## Recommended PR Sequence

1. `chore/dysonx-disable-legacy-aggregation-workflows`

   Remove `.github/workflows/update.yml` and
   `.github/workflows/update-content.yml`. Confirm no scheduled legacy content
   job remains.

2. `chore/dysonx-remove-legacy-aggregator-scripts`

   Remove `scripts/aggregator.py`, `scripts/openai_summary.py`,
   `scripts/generate_sitemap.py`, and `feeds.json`. Keep V1 independence tests.

3. `chore/dysonx-remove-generated-legacy-content`

   Remove `posts/page*.html` and `sitemap.xml`.

4. `docs/dysonx-repository-identity-readme`

   Replace README wording with DysonX Intelligence OS positioning and current
   dry-run status.

5. `chore/dysonx-release-guard-realignment`

   Update release guard expectations away from legacy `index.html` and old
   sitemap/feed assumptions, while keeping deployment risk checks.

6. `chore/dysonx-remove-legacy-static-ui`

   Remove or replace `index.html`, `components/`, and `styles/` after a DysonX
   preview or publishing surface is ready.

7. `chore/dysonx-prune-legacy-dependencies`

   Remove `feedparser`, `newspaper3k`, `lxml_html_clean`, `nltk`, and direct
   OpenAI SDK dependency unless reintroduced by a provider-neutral integration
   PR.

## Recommended Next Deletion PR

Next PR:

`chore/dysonx-disable-legacy-aggregation-workflows`

Scope:

- Delete `.github/workflows/update.yml`.
- Delete `.github/workflows/update-content.yml`.
- Add or keep tests proving the DysonX V1 pipeline does not use the legacy
  aggregator.
- Run the full governance and V1 dry-run validation suite.

Rationale:

Stopping scheduled legacy generation first is the safest removal step because it
prevents deleted legacy files from being recreated and avoids accidental OpenAI
or RSS execution from the old path.

## Go / No-Go

GO for staged legacy decommissioning beginning with workflow removal.

NO-GO for deleting the full static site, public root, or dependencies in one
large PR.

NO-GO for replacing legacy aggregation with a new generic RSS/news/article path.

NO-GO for real Notion API use, real LLM API use, publishing, deployment, or
merge as part of decommission planning.

## Final Confirmation

The DysonX V1 dry-run pipeline does not depend on the legacy aggregator or
legacy OpenAI summary module. Decommissioning can proceed in small PRs without
blocking the Signal-first V1 pipeline.

No merge or production deployment was performed.
