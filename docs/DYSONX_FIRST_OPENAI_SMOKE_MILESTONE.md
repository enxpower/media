# DysonX First OpenAI Smoke Milestone

Status: milestone documentation after the first manual OpenAI gated smoke run

## Milestone Summary

DysonX has completed its first manually gated real OpenAI smoke test.

This milestone confirms that the gated OpenAI provider path can be invoked
manually from GitHub Actions with a strict one-item limit while preserving the
no-publishing, no-deployment, and no-side-effect boundaries required by the
DysonX governance model.

## Relevant Pull Requests

- PR #49 merged the gated OpenAI provider path.
- PR #50 merged the manual OpenAI smoke workflow.

## Smoke Run Record

- Workflow: `DysonX OpenAI Gated Smoke Test #1`
- Branch: `main`
- Commit: `870a525`
- Status: success
- Duration: 12s
- Artifacts: 1

## Confirmed Behavior

- Real OpenAI call was manually gated.
- `max-items=1`.
- No publishing occurred.
- No social posting occurred.
- No website or public content writing occurred.
- No deployment occurred.
- No Notion mutation occurred.
- No live GitHub API usage occurred.
- No article body scraping occurred.
- Raw provider response was not stored.
- Uploaded artifact was limited to safe smoke report and SignalCandidate report.

## Artifact Boundary

The successful smoke run confirmed that uploaded artifacts remain constrained to
safe audit outputs:

- OpenAI smoke report
- SignalCandidate report

The run did not upload:

- raw provider response
- secrets
- raw article content
- RawItem store
- publish package output
- website pages
- public content files

## Warning Observed

The workflow emitted a non-blocking runtime warning:

```text
Node.js 20 deprecation / Node 24 runtime notice
```

This did not block the smoke run. It can be addressed later as workflow runtime
maintenance and should not be treated as a product or architecture blocker.

## Governance Position

This milestone remains within the approved DysonX architecture:

```text
Source / Source store
-> Collector Foundation
-> RawItem persistence
-> SignalCandidate
-> gated LLM provider
-> validated IntelligenceSignal audit output
```

The milestone does not authorize publishing, social posting, Knowledge Graph
writes, Prediction Engine implementation, dashboard work, scheduling, or
deployment.

## Next Step

The next recommended step is a documentation or audit PR that reviews the first
real-provider output quality and decides whether the provider prompt and
validation layer need tightening before any broader real LLM run.

Do not proceed directly from this milestone to publishing, scheduled LLM runs,
Knowledge Graph writes, social distribution, or deployment.
