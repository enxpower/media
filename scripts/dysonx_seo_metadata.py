#!/usr/bin/env python3
"""DysonX SEO metadata V1 for publish packages."""

from __future__ import annotations

from dataclasses import dataclass, asdict


DEFAULT_SITE_URL = ""


@dataclass(frozen=True)
class SEOMetadataV1:
    title: str
    description: str
    canonical_url: str
    og_title: str
    og_description: str
    x_title: str
    x_description: str


def truncate_text(value: str, limit: int) -> str:
    text = " ".join(value.split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def build_seo_metadata(title: str, summary: str, slug: str, site_url: str = DEFAULT_SITE_URL) -> SEOMetadataV1:
    seo_title = truncate_text(title, 70)
    description = truncate_text(summary, 160)
    canonical_url = f"{site_url.rstrip('/')}/signals/{slug}" if site_url else f"/signals/{slug}"
    return SEOMetadataV1(
        title=seo_title,
        description=description,
        canonical_url=canonical_url,
        og_title=seo_title,
        og_description=description,
        x_title=seo_title,
        x_description=description,
    )


def serialize_seo_metadata(metadata: SEOMetadataV1) -> dict[str, str]:
    return asdict(metadata)
