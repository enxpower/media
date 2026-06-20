# DysonX Owner Console Launch Plan

## 1. Status

This launch plan prepares the shortest safe path from the local Minimal Internal Frontend Preview V1 to a usable DysonX Owner Intelligence Console MVP.

The console remains internal owner-review tooling. It does not publish content, generate public Signal pages, post to social platforms, write Knowledge Graph records, run the Prediction Engine, call OpenAI, mutate Notion, call live GitHub APIs, dispatch workflows, or deploy.

## 2. Current Local URL

From the repository root:

```bash
python3 -m http.server 8090
```

Open:

```text
http://127.0.0.1:8090/internal/dysonx-owner-intelligence-preview/
```

The page loads:

```text
internal/dysonx-owner-intelligence-preview/brief_fixture.json
```

It can also load a local Internal Intelligence Brief V1 JSON file through the browser file picker.

## 3. Existing Hosting / Deployment Path Observed

Repository inspection shows static files are tracked in the repository and GitHub workflow files exist under:

```text
.github/workflows/
```

Relevant workflow names include governance checks, content sync/update files, and smoke-test workflows. Some legacy update workflows are disabled with `.disabled` suffixes. No package-based frontend framework configuration such as `package.json`, Vite, Next.js, or Astro config is required for the current console.

The console is currently a dependency-free static page under:

```text
internal/dysonx-owner-intelligence-preview/
```

That path is safe for local review because it does not sit under legacy public output directories such as `static/` or `downloads/`.

## 4. Safest Online Hosting Option Using Current Conventions

The shortest safe online path is to serve the existing static `internal/` directory behind an access-controlled preview or internal static host that already serves repository files.

Minimum safe requirements:

- keep the console path under `internal/`
- require access control before exposing it online
- do not publish generated Signal pages from console data
- do not enable social posting
- do not write Knowledge Graph records
- do not run OpenAI from the page
- do not introduce automated deployment in this PR

This PR does not choose or configure a deployment platform.

## 5. Minimum Steps After Merge

After merge, the shortest safe path to make the console accessible online is:

1. Confirm which existing static hosting surface is approved for internal-only pages.
2. Confirm that the host can restrict access to the Owner or a small authorized reviewer set.
3. Serve the existing path:

```text
/internal/dysonx-owner-intelligence-preview/
```

4. Verify the page loads the fixture or a manually supplied Internal Intelligence Brief V1 JSON file.
5. Verify generated Owner Review Feedback V1 JSON can be copied or downloaded.
6. Confirm that no workflow dispatch, OpenAI call, Notion mutation, live GitHub API call, Knowledge Graph write, Prediction Engine action, public publishing, or deployment side effect is triggered by using the page.

## 6. Safety Warning

If this repository is served publicly as a static site, files under `internal/` may also become publicly reachable unless the hosting layer blocks them.

Before any online launch, the Owner Console must be protected by one of:

- private preview access
- authentication at the hosting layer
- network allowlisting
- a separate private internal host

Do not expose live or sensitive Owner review data in `brief_fixture.json` or any committed fixture. The committed fixture must remain representative sample data only.

## 7. Non-Goals

This launch plan does not authorize:

- production deployment
- broad deployment automation
- public publishing
- public website generation
- social distribution automation
- Knowledge Graph writes
- Prediction Engine work
- Confidence Calibration
- Multi-source Correlation
- OpenAI calls
- Notion mutation
- live GitHub API collection
- article scraping
- authentication implementation
- database persistence

## 8. Recommended Next Action

After this PR is reviewed and merged, run one Owner usability session against the local console.

If the Owner cannot decide from the displayed fields, do Brief Field Completeness V1.

If the Owner can decide but needs saved sessions, do Internal Frontend Persistence V1 or Review Session Save V1.

No production deployment was performed.
