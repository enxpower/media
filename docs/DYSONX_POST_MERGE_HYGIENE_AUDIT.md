# DysonX Post-Merge Repository Hygiene Audit

Status: audit-only after DysonX V1 dry-run stack landed in `main`

Branch: `audit/dysonx-post-merge-hygiene-review`

Base: `main`

This audit reviews repository hygiene after the V1 dry-run stack was integrated.
It does not delete files, change runtime behavior, connect external services,
publish pages, post to social platforms, or deploy.

## Scope

Checked:

- Tracked repository structure on `main`.
- Leftover legacy feed/article aggregation artifacts.
- Orphan static assets and unused browser-side modules.
- Stale references to removed generated pages, old feed files, removed scripts,
  old ad assets, and removed sitemap/feed outputs.
- Obsolete dependency manifest entries.
- Disabled workflows and maintenance workflows that may no longer be needed.
- DysonX V1 dry-run pipeline health.
- Static preview safety health.

Not checked:

- Private content repository ownership or current business need.
- Runtime behavior of GitHub Pages, because this PR does not deploy.
- Real Notion API behavior.
- Real LLM provider behavior.
- Social platform behavior.
- Production DNS, CDN, analytics, or secrets.

## Current Repository Shape

The current public shell is DysonX-oriented:

- `index.html` is a self-contained DysonX static shell.
- `README.md` presents the DysonX V1 dry-run stack.
- `robots.txt` no longer references removed sitemap output.
- Removed generated public files are absent from the tracked tree:
  `posts/page*.html`, `rss.xml`, `sitemap.xml`, `feeds.json`,
  `scripts/aggregator.py`, `scripts/openai_summary.py`, and
  `scripts/generate_sitemap.py`.
- The V1 dry-run path is present under `scripts/dysonx_*.py` and
  `tests/test_dysonx_*.py`.

## LOW RISK Cleanup

These look safe to remove in a follow-up cleanup PR, subject to a normal diff
review:

- `scripts/__pycache__/openai_summary.cpython-313.pyc` is tracked even though
  `scripts/openai_summary.py` was removed. It is a generated Python cache file
  and should not be versioned.
- Empty placeholder files may be reviewed after static assets are removed:
  `ads/.gitkeep` and `downloads/.gitkeep`.
- `static/data/downloads.json` and `static/data/sponsored.json` are empty files.
  They are not referenced by the DysonX static shell.
- Historical disabled workflow files can be deleted after the decommission audit
  is accepted:
  `.github/workflows/update.yml.disabled` and
  `.github/workflows/update-content.yml.disabled`.

## MEDIUM RISK Cleanup

These are probably obsolete for DysonX V1, but should be removed only after one
explicit cleanup PR verifies there is no remaining public-shell or private-sync
dependency:

- `components/*.js` contains browser modules from the previous static experience.
  `index.html` does not load these files now. Notable examples:
  `components/pagination.js` still fetches `posts/page*.html`, and
  `components/nativeAds.js` / `components/ops.js` still read
  `/static/data/ads.json`.
- `styles/main.css` is not loaded by the current inline-styled `index.html`.
- `ads/bess1200_*` and `downloads/ANSICANUL9540A.pdf` appear to be orphan static
  business assets for the old public experience. They are referenced by
  `static/data/ads.json` but not by the DysonX shell.
- `static/data/ads.json` still enables native ad cards and references the
  retained `ads/` and `downloads/` paths. This is no longer part of the V1
  DysonX dry-run shell.
- `og-cover.jpg` is tracked but not referenced by the current `index.html`.
- `requirements.txt` still lists packages for the removed feed/article path:
  `feedparser`, `newspaper3k`, `lxml_html_clean`, and `nltk`. It also lists
  `openai`, while V1 intentionally uses a fake/provider-neutral LLM layer and
  does not import the real OpenAI client. A follow-up PR should replace this
  manifest with the actual V1 needs or remove it if no install step uses it.

## HIGH RISK Cleanup

These should not be deleted casually because they have active workflows,
branch-repair behavior, or possible owner/business coupling:

- `.github/workflows/sync-content.yml` is active on schedule and
  `workflow_dispatch`. It mirrors `ads/`, `downloads/`, and
  `static/data/ads.json` from a private repository and can commit back to the
  public branch. It should be disabled or removed only after owner confirmation,
  because it may still mutate `main`.
- `.github/workflows/validate-ads.yml` is active manually and validates
  `static/data/ads.json` against the private content repository. It should be
  removed together with, or after, any decision about `sync-content.yml`.
- Submodule repair workflows remain active:
  `fix-ops-submodule.yml`, `nuke-ops-lite.yml`, `nuke-ops.yml`,
  `nuke-submodules.yml`, and `repair-gitlinks.yml`. They are maintenance tools
  with write permissions. Keep them until the owner confirms the old submodule
  incident is fully closed.
- `block-submodules.yml` should stay active until the repair workflows are
  retired or replaced, because it prevents reintroducing gitlinks.
- `CNAME` should not be deleted in a hygiene PR. Domain ownership and preview /
  production routing need a separate release review.

## DO NOT DELETE / Keep

Keep these as part of the current DysonX V1 foundation:

- `AGENTS.md`.
- `.github/pull_request_template.md`.
- `.github/workflows/governance-check.yml`.
- `README.md`.
- `index.html`.
- `robots.txt`.
- `docs/DYSONX_OWNER_INTENT.md`.
- `docs/DYSONX_PROJECT_CONTEXT.md`.
- `docs/DYSONX_PRODUCT_CONSTITUTION.md`.
- `docs/DYSONX_SYSTEM_ARCHITECTURE.md`.
- `docs/DYSONX_ENGINEERING_GOVERNANCE.md`.
- V1 implementation docs:
  `docs/DYSONX_SOURCE_INTAKE_V1.md`,
  `docs/DYSONX_SIGNAL_CANDIDATE_V1.md`,
  `docs/DYSONX_LLM_INTELLIGENCE_LAYER_V1.md`,
  `docs/DYSONX_LLM_JOB_AUDIT_V1.md`,
  `docs/DYSONX_SIGNAL_RANKING_ENGINE_V1.md`,
  `docs/DYSONX_QUALITY_REVIEW_GATE_V1.md`,
  `docs/DYSONX_PUBLISH_PACKAGE_V1.md`,
  `docs/DYSONX_V1_PIPELINE_ORCHESTRATOR.md`, and
  `docs/DYSONX_STATIC_PREVIEW_SAFETY.md`.
- V1 scripts under `scripts/dysonx_*.py`, plus
  `scripts/constitution_guard.py`, `scripts/architecture_guard.py`, and
  `scripts/release_guard.py`.
- V1 tests and fixtures under `tests/`.
- `docs/DYSONX_LEGACY_AGGREGATOR_DECOMMISSION_PLAN.md`, until the owner accepts
  a final cleanup PR. It is useful audit context even though it names removed
  files.

## Stale Reference Findings

- Active workflows do not reference the removed legacy scripts or generated
  public files.
- Disabled workflows still contain references to the removed scripts and
  generated public files. They are retained as audit context only.
- Tests and static-preview checks intentionally reference removed filenames to
  prevent regressions.
- `components/pagination.js` still references `posts/page*.html`, but that file
  is not loaded by the current `index.html`.
- `static/data/ads.json`, `components/nativeAds.js`, `components/ops.js`, and
  active private-content workflows still represent the old ad/content sync path.

## Recommended Next Cleanup PR

Recommended branch:

`chore/dysonx-remove-orphan-legacy-static-assets`

Recommended scope:

1. Remove tracked Python cache files.
2. Remove or archive disabled legacy workflow files after owner acceptance.
3. Remove unused component/style files that are not loaded by `index.html`.
4. Remove orphan ad/download/static-data assets after confirming
   `sync-content.yml` and `validate-ads.yml` are disabled or retired.
5. Update `requirements.txt` to match the V1 dry-run stack.
6. Re-run the full guard, unit test, dry-run pipeline, and static preview safety
   command set.

Do not combine this cleanup with real integrations or publishing behavior.

## Recommended Next Product PR

Recommended branch:

`feature/dysonx-notion-readonly-source-sync-v1`

Recommended scope:

- Add the first real read-only Notion source sync behind explicit environment
  requirements.
- Fail closed when credentials or database configuration are absent.
- Preserve local fixture dry runs as the default validation path.
- Do not add collectors, real LLM provider calls, page publishing, social
  posting, Knowledge Graph writes, Prediction Engine behavior, or deployment.

## Validation Notes

The audit PR should run:

- `python3 scripts/constitution_guard.py`
- `python3 scripts/architecture_guard.py`
- `python3 scripts/release_guard.py`
- `python3 -m py_compile scripts/*.py`
- `python3 -m unittest discover -s tests`
- `python3 scripts/dysonx_v1_pipeline.py --raw-fixture tests/fixtures/raw_items_v1.json --output-dir tmp/dysonx_v1_pipeline --dry-run`
- `python3 scripts/dysonx_static_preview_check.py`
- `git diff --check`

## Go / No-Go

Go for audit-only PR review.

No-go for deleting files in this PR. Deletions should happen in the separate
cleanup PR above after human review of the active private-content workflows and
retained static assets.
