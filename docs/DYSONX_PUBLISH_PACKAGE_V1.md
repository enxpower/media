# DysonX Publish Package V1

This document defines the V1 publish package layer for DysonX.

This is still pre-publishing. It creates structured package metadata only. It
does not write website pages, write public content files, publish pages, or post
to social platforms.

## Target Flow

```text
Publish-Ready Signal
-> Publish Package
-> SEO Metadata
-> Social Draft Metadata
-> Audit Report
```

## Scope

Allowed in V1:

- Read quality review reports.
- Convert only `publish_ready` Intelligence Signals into publish packages.
- Generate deterministic slugs from titles.
- Generate SEO metadata.
- Generate social draft metadata with `draft_only` status.
- Produce an audit report.

Not included in V1:

- Website page generation.
- Writing files into public content directories.
- Social posting.
- Real LLM provider integration.
- Knowledge Graph writes.
- Prediction Engine behavior.
- Dashboard, billing, enterprise, or multi-tenant features.

## PublishPackageV1

- `package_id`
- `signal_id`
- `title`
- `slug`
- `summary`
- `source_url`
- `source_name`
- `canonical_language`
- `localized_languages`
- `seo_metadata`
- `social_drafts`
- `status`
- `created_at`

## SEOMetadataV1

- `title`
- `description`
- `canonical_url`
- `og_title`
- `og_description`
- `x_title`
- `x_description`

## SocialDraftV1

- `platform`
- `draft_text`
- `link_url`
- `status`

V1 requires `status = draft_only`.

## Deterministic Rules

- English is canonical.
- Chinese is optional localization metadata only.
- Slugs are generated from English titles.
- Social drafts are metadata only and remain `draft_only`.
- No platform posting occurs.
- No file or page publishing occurs.
- No website write occurs.

## Audit Report

The publish package audit report includes:

- Packages created.
- Signals seen.
- Skipped signals and reasons.
- Package metadata.
- SEO metadata.
- Social draft metadata.
- Confirmation that no website publishing, public content file write, social
  posting, real LLM API call, or network request occurred.

## Governance Notes

This layer packages already quality-approved intelligence for future publishing
review. It does not bypass the Quality Gate and does not create a public
distribution path.
