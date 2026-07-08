# Acceptance Checklist

## General

- Project context files exist.
- Scope is clear.
- Repository purpose is documented.
- No unrelated files were changed.
- No secrets are committed.
- Documentation is concise and actionable.
- All generated repository content is English-only.

## For Public HTML / Website Repositories

- Mobile layout has no horizontal scroll.
- Desktop, tablet, and mobile layouts are checked.
- Page title and description are relevant.
- Social preview metadata exists.
- Favicon exists.
- Preview image exists or is explicitly listed as missing.
- Correct VI is applied.
- No dark scheme is used unless approved.
- No external tracking is added unless approved.
- Public pages do not expose internal credentials or private logic.

## For Backend / Automation Repositories

- Runtime entrypoints are documented.
- Required environment variables are listed by name only, not values.
- No secrets are committed.
- Failure handling is documented or marked To verify.
- Logs and output locations are documented or marked To verify.
- Deployment or scheduler path is documented or marked To verify.

## For AI / Agent Repositories

- Agent purpose is clear.
- Inputs and outputs are documented.
- Tool boundaries are documented.
- Human approval points are documented.
- Risky actions are gated.
- Memory / context handoff rules are documented.

## Repository-Specific Checks

- DysonX remains Signal-first and does not become a generic news or article site.
- Notion remains the managed source registry unless explicitly changed.
- Source Collector does not write public static files.
- Public Signals sync keeps attribution, copyright, topic, raw-body, and quality gates intact.
- Public output does not include raw article body text.
- Workflow changes do not expose secret values.
- Guard and test commands are run when script or workflow logic changes.
- No merge or production deployment occurs without explicit owner approval.
