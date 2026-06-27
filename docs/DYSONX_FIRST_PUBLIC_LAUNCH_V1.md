# DysonX First Public Launch V1

## 1. Purpose

First Public Launch V1 is Step 5 of the strict 5-Step Final Launch Plan:

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

It consumes the Step 4 production publish pack and release guard report, requires explicit Owner launch authorization, and copies only approved static Signal pages into the repository public static output path.

In this repository, the public static surface is the repository root: `index.html`, `CNAME`, `robots.txt`, and `static/` are tracked at root. First Public Launch V1 therefore writes launched Signal files under:

```text
signals/
```

## 2. Required Authorization

Step 5 may run only with explicit Owner launch authorization.

The authorized launch token is:

```text
explicit_owner_authorization_in_step_5_prompt
```

This authorization permits only the first controlled public Signal launch from the already release-guarded Step 4 production publish pack. It does not authorize social distribution, newsletter distribution, scraping, OpenAI calls, backend/database work, manual workflow dispatch, or external deployment commands.

## 3. CLI

```bash
python3 scripts/dysonx_first_public_launch.py \
  --production-pack-dir tmp/production_publish_pack \
  --pack-manifest tmp/production_publish_pack/production_publish_pack_manifest.json \
  --release-guard-report tmp/production_publish_pack/release_guard_report.json \
  --public-output-root . \
  --owner-launch-authorization explicit_owner_authorization_in_step_5_prompt
```

The CLI reads local files only and uses Python standard library modules.

## 4. Launch Rules

The launch guard must verify:

- Step 4 release guard passed
- explicit Owner launch authorization is present
- at least one approved packaged page exists
- packaged files exist
- packaged entries are `approved_for_production_pack: true`
- packaged entries have `published: false`
- packaged entries have `production_publish_performed: false`
- packaged entries have `deployed: false`
- no raw article body markers are present
- no internal review state markers are present
- no OpenAI call was performed
- no workflow dispatch was performed
- no manual external deployment was performed by the tool

Only launched entries may be marked:

```json
{
  "published": true,
  "production_publish_performed": true
}
```

The tool must not set `deployed: true`.

## 5. Output

For the repository root public static surface, the launch writes:

```text
signals/index.html
signals/<slug>/index.html
signals/public_launch_manifest.json
```

The manifest records:

- launch version
- explicit Owner launch authorization
- source pack manifest
- source release guard report
- pages launched
- pages blocked
- release guard status
- manual approval verification
- Publish Readiness Gate verification
- production pack verification
- OpenAI call flag
- workflow dispatch flag
- manual external deployment flag
- social distribution flag
- newsletter distribution flag

## 6. Hosting Boundary

First Public Launch V1 copies static files into the repository public surface. It does not manually dispatch workflows and does not run an external deployment command.

If repository hosting deploys from `main` automatically, merging the static files to `main` may allow hosting automation to publish according to repository settings. The launch guard itself does not verify external deployment success and must not claim that external deployment succeeded.

## 7. Functional Publishing Priority

This step completes:

```text
Functional publishing before aesthetic polish;
quality and safety gates before public release.
```

The launched pages may remain visually simple. They must remain readable, credible, source-attributed, copyright-safe, and free of internal review state.

## 8. Non-Goals

This step does not implement:

- Step 6
- new milestones
- Owner Console polish
- public page visual polish
- backend APIs
- database storage
- OpenAI calls
- scraping
- Knowledge Graph writes
- Prediction Engine
- Confidence Calibration
- Multi-source Correlation
- social distribution
- newsletter distribution
- manual workflow dispatch
- manual external deployment
