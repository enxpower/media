# DysonX Notion Public Signals Sync V1

Notion Public Signals Sync V1 refreshes DysonX public static Signal pages from the Notion database `DysonX Signal Intake`.

This is not a new launch step. The V1 public launch remains sealed. This automation only prepares static public Signal updates through a pull request.

## Required Secrets

The scheduled workflow requires:

- `NOTION_TOKEN`
- `NOTION_SIGNAL_INTAKE_DATABASE_ID`

`NOTION_SIGNAL_INTAKE_DATABASE_ID` must point to the Owner-approved `DysonX Signal Intake` database.

## Eligibility Rules

A Notion row may generate or update a public Signal only when all of these are true:

- `Ready for Pipeline` is checked.
- `Published` is checked.
- `Attribution Status` is `Complete`.
- `Copyright Status` is `Safe Summary Only`.
- `Quality Hint` is at least `80`.
- `Signal Title` exists.
- `Summary` exists.
- `Source URL` exists and is public-safe.

Rows that do not satisfy these rules are blocked from public generation.

## Generated Files

The sync writes only static public Signal output:

- `signals/index.html`
- `signals/<slug>/index.html`
- `signals/public_launch_manifest.json`

Existing launched public Signals are preserved unless a later reviewed content PR intentionally removes them.

## Safety Rules

The sync is standard-library only and deterministic aside from refresh timestamps.

It must not:

- Call OpenAI.
- Scrape or fetch source pages.
- Copy raw article bodies.
- Hardcode a deployment domain.
- Emit reserved test-domain or fake-domain public URLs.
- Emit local temporary artifact paths.
- Expose internal blocker details or private review state.
- Dispatch deployment workflows.
- Auto-merge.

Public pages are summary-only. Source attribution links may come only from `Source URL`; the script does not dereference that URL.

Generated public links use relative public paths such as `/signals/` and `/signals/<slug>/`.

## Workflow Behavior

`.github/workflows/dysonx-notion-public-signals-sync.yml` runs every six hours and supports manual `workflow_dispatch`.

The workflow:

1. Checks out the repository.
2. Runs `scripts/dysonx_notion_public_signals_sync.py`.
3. Runs `python3 scripts/dysonx_static_preview_check.py --root .`.
4. Runs public-output grep guards for hardcoded domains, test domains, fake domains, and local temporary artifact paths.
5. Exits cleanly when no `signals/` files changed.
6. If `signals/` changed, creates an automation branch and opens a pull request titled `content: sync DysonX public Signals from Notion`.

The workflow opens a PR only. It does not publish directly and does not auto-merge.

No production deployment is performed by this automation.
