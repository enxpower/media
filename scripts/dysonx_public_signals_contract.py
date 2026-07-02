#!/usr/bin/env python3
"""Contract metadata for DysonX Public Signals artifacts."""

from __future__ import annotations

import pathlib
from typing import Any


PUBLIC_SIGNAL_CONTRACT_VERSION = "dysonx_public_signal_contract_v1"
PUBLIC_SIGNAL_POLICY_VERSION = "dysonx_public_signal_policy_v2"
CNAME_FILE = "CNAME"

ARTIFACT_SIGNAL_HTML = "signal_html"
ARTIFACT_SIGNALS_INDEX_HTML = "signals_index_html"
ARTIFACT_PUBLIC_LAUNCH_MANIFEST = "public_launch_manifest"
ARTIFACT_PUBLIC_ARTIFACT_MANIFEST = "public_artifact_manifest"
ARTIFACT_ROBOTS_TXT = "robots_txt"
ARTIFACT_SITEMAP_XML = "sitemap_xml"
ARTIFACT_RSS_XML = "rss_xml"
ARTIFACT_JSON_FEED = "json_feed"

ALLOWED_ARTIFACT_CLASSES = {
    ARTIFACT_SIGNAL_HTML,
    ARTIFACT_SIGNALS_INDEX_HTML,
    ARTIFACT_PUBLIC_LAUNCH_MANIFEST,
    ARTIFACT_PUBLIC_ARTIFACT_MANIFEST,
    ARTIFACT_ROBOTS_TXT,
    ARTIFACT_SITEMAP_XML,
    ARTIFACT_RSS_XML,
    ARTIFACT_JSON_FEED,
}

SAFE_EMBED_JSON_LD_ARTICLE = "json_ld_article"
SAFE_EMBED_JSON_LD_ORGANIZATION = "json_ld_organization"
ALLOWED_SAFE_EMBEDS = {
    SAFE_EMBED_JSON_LD_ARTICLE,
    SAFE_EMBED_JSON_LD_ORGANIZATION,
}

FORBIDDEN_CONTENT_CLASSES = {
    "raw_body",
    "source_body",
    "verbatim_article",
    "unsafe_script",
    "unsafe_external_resource",
    "off_topic",
}

ROOT_ARTIFACT_CLASSES = {
    "robots.txt": ARTIFACT_ROBOTS_TXT,
    "sitemap.xml": ARTIFACT_SITEMAP_XML,
    "rss.xml": ARTIFACT_RSS_XML,
    "feed.json": ARTIFACT_JSON_FEED,
}

SIGNALS_ARTIFACT_CLASSES = {
    "signals/index.html": ARTIFACT_SIGNALS_INDEX_HTML,
    "signals/public_launch_manifest.json": ARTIFACT_PUBLIC_LAUNCH_MANIFEST,
    "signals/public_artifact_manifest.json": ARTIFACT_PUBLIC_ARTIFACT_MANIFEST,
}


def normalize_public_path(value: str | pathlib.PurePath) -> str:
    return str(value).strip().replace("\\", "/").lstrip("./")


def public_domain_from_cname(root: pathlib.Path | str = ".") -> str:
    cname_path = pathlib.Path(root) / CNAME_FILE
    try:
        domain = cname_path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    except (OSError, IndexError):
        domain = ""
    if not domain or "://" in domain or "/" in domain or any(char.isspace() for char in domain):
        raise ValueError(f"{CNAME_FILE} must contain a single public domain")
    return domain


def public_seo_base_url(root: pathlib.Path | str = ".") -> str:
    return f"https://{public_domain_from_cname(root)}"


def signal_slug_from_public_path(path: str | pathlib.PurePath) -> str | None:
    parts = pathlib.PurePosixPath(normalize_public_path(path)).parts
    if len(parts) == 3 and parts[0] == "signals" and parts[2] == "index.html" and parts[1] != "index":
        return parts[1]
    return None


def artifact_class_for_path(path: str | pathlib.PurePath) -> str | None:
    normalized = normalize_public_path(path)
    if normalized in ROOT_ARTIFACT_CLASSES:
        return ROOT_ARTIFACT_CLASSES[normalized]
    if normalized in SIGNALS_ARTIFACT_CLASSES:
        return SIGNALS_ARTIFACT_CLASSES[normalized]
    if signal_slug_from_public_path(normalized):
        return ARTIFACT_SIGNAL_HTML
    return None


def allowed_embeds_for_artifact_class(artifact_class: str) -> list[str]:
    if artifact_class == ARTIFACT_SIGNAL_HTML:
        return [SAFE_EMBED_JSON_LD_ARTICLE]
    if artifact_class == ARTIFACT_SIGNALS_INDEX_HTML:
        return [SAFE_EMBED_JSON_LD_ORGANIZATION]
    return []


def is_allowed_public_artifact_path(path: str | pathlib.PurePath) -> bool:
    return artifact_class_for_path(path) in ALLOWED_ARTIFACT_CLASSES


def artifact_slug(path: str | pathlib.PurePath, artifact_class: str) -> str | None:
    if artifact_class == ARTIFACT_SIGNAL_HTML:
        return signal_slug_from_public_path(path)
    return None


def build_artifact_entry(path: str, material_signature: str, *, generated: bool = True) -> dict[str, Any]:
    artifact_class = artifact_class_for_path(path)
    if artifact_class not in ALLOWED_ARTIFACT_CLASSES:
        raise ValueError(f"unsupported public artifact path: {path}")
    entry: dict[str, Any] = {
        "path": normalize_public_path(path),
        "artifact_class": artifact_class,
        "contract_version": PUBLIC_SIGNAL_CONTRACT_VERSION,
        "policy_version": PUBLIC_SIGNAL_POLICY_VERSION,
        "allowed_embeds": allowed_embeds_for_artifact_class(artifact_class),
        "material_signature": material_signature,
        "generated_from_public_signal_manifest": generated,
    }
    slug = artifact_slug(path, artifact_class)
    if slug:
        entry["slug"] = slug
    return entry
