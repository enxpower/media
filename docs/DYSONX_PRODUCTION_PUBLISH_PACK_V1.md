# DysonX Production Publish Pack V1

## 1. Purpose

Production Publish Pack V1 is Step 4 of the strict 5-Step Final Launch Plan:

```text
Owner Review Wizard
-> Publish Readiness Gate
-> Public Signal Page Generator
-> Public Signals Index
-> Local Public Preview
-> Manual Publish Approval
-> Production Publish Pack
-> media.energizeos.com
```

It creates deterministic offline production-ready artifacts for Step 5 from:

- Step 2 Public Signal Page Generator output and manifest
- Step 3 Manual Publish Approval report

The pack is a launch candidate only. It is not deployment and not publication.

## 2. Boundary

Production Publish Pack V1 does not:

- publish to production
- deploy
- dispatch workflows
- call OpenAI
- scrape or fetch sources
- write to `media.energizeos.com`
- write to a production site root
- mark `published` true
- mark `production_publish_performed` true
- mark `deployed` true

Step 5 explicit Owner launch authorization is still required before production release. First Public Launch V1 is governed by `docs/DYSONX_FIRST_PUBLIC_LAUNCH_V1.md`; it consumes this pack plus the release guard report and may copy only approved, release-guarded static files into the repository public static output path.

## 3. CLI

```bash
python3 scripts/dysonx_production_publish_pack.py \
  --public-pages-dir tests/fixtures/production_publish_pack_v1/public_signal_pages \
  --public-pages-manifest tests/fixtures/production_publish_pack_v1/public_signal_pages_manifest.json \
  --approval-report tests/fixtures/production_publish_pack_v1/manual_publish_approval_report.json \
  --output-dir tmp/production_publish_pack
```

The CLI reads local files only and uses Python standard library modules.

## 4. Packaging Rules

The pack may include only pages where:

- `approved_for_production_pack` is true
- `published` is false
- `production_publish_performed` is false
- `deployed` is false or absent
- the corresponding generated page exists in the Step 2 manifest
- the corresponding HTML file exists under the provided public pages directory
- the source page says `Draft Preview / Not Published`
- no raw article body is detected
- no internal review state is detected

All other pages are blocked with explicit blockers and required next actions.

## 5. Output Structure

Default output:

```text
tmp/production_publish_pack/
```

Generated files:

```text
tmp/production_publish_pack/signals/<slug>/index.html
tmp/production_publish_pack/signals/index.html
tmp/production_publish_pack/production_publish_pack_manifest.json
tmp/production_publish_pack/release_guard_report.json
tmp/production_publish_pack/README.md
```

Packaged pages may relabel:

```text
Draft Preview / Not Published
```

to:

```text
Production Publish Candidate / Not Yet Deployed
```

They must not claim the page is published, live, deployed, or production deployed.

## 6. Release Guard Report

The pack includes:

```text
tmp/production_publish_pack/release_guard_report.json
```

The release guard checks:

- manual approval report exists in the input set
- only approved pages are packaged
- no unapproved pages are packaged
- packaged files exist
- index is generated
- `published` is not true before launch
- `production_publish_performed` is not true before launch
- `deployed` is not true
- no raw article body is detected
- no internal review state is detected
- no OpenAI call is performed
- no workflow dispatch is performed
- no deployment is performed
- Step 5 launch authorization remains required

If any critical check fails, `release_guard_passed` must be false.

## 7. Functional Publishing Priority

This step supports:

```text
Functional publishing before aesthetic polish;
quality and safety gates before public release.
```

The pack prioritizes a safe, controllable, verifiable launch path over visual polish. Quality gates, attribution, copyright safety, Manual Publish Approval, release guards, and explicit Step 5 launch authorization remain mandatory.

## 8. Non-Goals

This step does not implement:

- Step 5 public launch, which is governed separately by `docs/DYSONX_FIRST_PUBLIC_LAUNCH_V1.md`
- production deployment
- workflow dispatch
- OpenAI calls
- backend APIs
- database storage
- scraping
- Knowledge Graph writes
- Prediction Engine
- Confidence Calibration
- Multi-source Correlation
- social distribution
- visual polish

No production deployment is authorized by this document.
