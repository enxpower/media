# DysonX Static Preview Safety

This document defines the offline safety check for the temporary DysonX static landing shell.

The check exists to verify that the root page is safe to inspect as a static preview before any real external integrations or production publishing paths are introduced.

## Command

```bash
python3 scripts/dysonx_static_preview_check.py
```

The script performs local filesystem checks only. It does not require network access.

## What Is Checked

- `index.html` exists.
- `index.html` declares English canonical metadata with `<html lang="en">`, a DysonX title, description metadata, Open Graph metadata, Twitter/X metadata, and canonical root URL.
- `index.html` includes viewport metadata for basic static preview readiness.
- `index.html` preserves DysonX identity as an AI / AGI Intelligence OS and Signal-first shell.
- `index.html` includes the EN / Chinese switch placeholder.
- `index.html` does not reference removed legacy generated pages such as `posts/page1.html` through `posts/page4.html`.
- `index.html` does not reference removed `sitemap.xml`.
- `robots.txt` does not reference removed `sitemap.xml`.
- Active `.yml` and `.yaml` workflows do not reference deleted legacy aggregation scripts or legacy generated artifacts.
- The DysonX V1 fixture dry-run pipeline still runs and reports no real LLM API use, no network requests, no publishing, and no social posting.

## What Is Not Checked

- Real GitHub Pages deployment behavior.
- DNS, CDN, caching, custom domain, TLS, or production routing.
- Real Notion API behavior.
- Real LLM provider behavior.
- Real social posting behavior.
- Knowledge Graph writes.
- Prediction Engine behavior.
- Production sitemap generation.
- Accessibility, visual QA, or browser layout correctness beyond static metadata checks.

## Why This Is Not Production Publishing

The current root shell is a preview/static-site shell only. It presents DysonX identity and V1 status, but it does not publish Signal pages, write public content from publish packages, call Notion, call real LLM providers, post to social platforms, or update production infrastructure.

The V1 pipeline command used by the check is fixture-based and dry-run only. It writes JSON audit reports under `tmp/` and confirms that publishing and external-provider flags remain false.

## Future GitHub Pages Preview Validation

Before enabling a future GitHub Pages preview, validate at minimum:

1. Run all governance guards, unit tests, V1 dry-run pipeline, and `dysonx_static_preview_check.py`.
2. Confirm the preview branch or environment does not publish pages from Signal packages unless a separate publishing PR explicitly adds and reviews that behavior.
3. Confirm any sitemap or robots behavior points only to routes that exist in the preview output.
4. Confirm English remains canonical and Chinese remains a switchable localization layer.
5. Confirm no workflow uses deleted legacy aggregation scripts or hardcoded monitored source lists.
6. Confirm the preview workflow requires review before any production deployment path can run.

Production publishing still requires a separate reviewed PR, explicit approval, passing CI, and no merge or deployment by an AI agent.
