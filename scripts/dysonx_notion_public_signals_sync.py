#!/usr/bin/env python3
"""Sync Notion-approved DysonX public Signals into static summary pages."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from typing import Any, Callable
from urllib.parse import urljoin, urlsplit

from dysonx_public_signals_contract import (
    ALLOWED_ARTIFACT_CLASSES,
    ALLOWED_SAFE_EMBEDS,
    FORBIDDEN_CONTENT_CLASSES,
    PUBLIC_SIGNAL_CONTRACT_VERSION,
    PUBLIC_SIGNAL_POLICY_VERSION,
    build_artifact_entry,
    public_seo_base_url,
)
from dysonx_public_signals_topic_policy import (
    has_core_public_topic as topic_has_core_public_topic,
    off_topic_public_signal as topic_off_topic_public_signal,
    public_topic_decision,
)


SYNC_VERSION = "notion_public_signals_sync_v1"
TOKEN_ENV = "NOTION_TOKEN"
DATABASE_ID_ENV = "NOTION_SIGNAL_INTAKE_DATABASE_ID"
NOTION_VERSION = "2022-06-28"
DEFAULT_OUTPUT_ROOT = pathlib.Path(".")
PUBLIC_SAFE_SOURCE_NOTE = "Source attribution retained in Notion launch metadata; external source URL omitted for this V1 public sample."
DEFAULT_MAX_PUBLIC_SIGNALS = 30
PUBLIC_OUTPUT_MIN_QUALITY = 80
PUBLIC_OUTPUT_ALLOWED_PRIORITIES = {"High", "Critical"}
PUBLIC_OUTPUT_ALLOWED_AGI_RELEVANCE = {"Medium", "High", "Critical"}
SOURCE_PRIORITY_RANK = {"Critical": 0, "High": 1}
AGI_RELEVANCE_RANK = {"Critical": 0, "High": 1, "Medium": 2}
FORBIDDEN_PUBLIC_TERMS = (
    "." "invalid",
    "." "test/",
    "source.dysonx." "invalid",
    "source.dysonx." "test",
    "tmp/" "production_publish_pack",
    "https://dysonx." "ai",
)


class NotionPublicSignalsSyncError(RuntimeError):
    """Raised when public Signal sync input is invalid or unsafe."""


NotionTransport = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled-signal"


def escape(value: Any, *, quote: bool = False) -> str:
    return html.escape(normalize_text(value), quote=quote)


def notion_plain_text(items: list[dict[str, Any]] | None) -> str:
    if not items:
        return ""
    return "".join(str(item.get("plain_text") or "") for item in items)


def notion_property_value(property_value: dict[str, Any]) -> Any:
    property_type = property_value.get("type")
    if property_type == "title":
        return notion_plain_text(property_value.get("title"))
    if property_type == "rich_text":
        return notion_plain_text(property_value.get("rich_text"))
    if property_type == "select":
        selected = property_value.get("select")
        return selected.get("name") if isinstance(selected, dict) else ""
    if property_type == "status":
        selected = property_value.get("status")
        return selected.get("name") if isinstance(selected, dict) else ""
    if property_type == "multi_select":
        values = property_value.get("multi_select")
        if not isinstance(values, list):
            return []
        return [str(item.get("name")) for item in values if isinstance(item, dict) and item.get("name")]
    if property_type == "url":
        return property_value.get("url") or ""
    if property_type == "number":
        return property_value.get("number")
    if property_type == "checkbox":
        return bool(property_value.get("checkbox"))
    if property_type == "date":
        date_value = property_value.get("date")
        return date_value.get("start") if isinstance(date_value, dict) else ""
    if property_type == "formula":
        formula = property_value.get("formula")
        if isinstance(formula, dict):
            return formula.get(formula.get("type", ""), "")
    return None


def notion_page_to_record(page: dict[str, Any]) -> dict[str, Any]:
    properties = page.get("properties")
    if not isinstance(properties, dict):
        raise NotionPublicSignalsSyncError("Notion page is missing properties")
    record = {
        field_name: notion_property_value(property_value)
        for field_name, property_value in properties.items()
        if isinstance(property_value, dict)
    }
    record["_notion_page_id"] = normalize_text(page.get("id"))
    return record


def urllib_notion_transport(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise NotionPublicSignalsSyncError(f"Notion query failed: {exc}") from exc
    data = json.loads(response_body)
    if not isinstance(data, dict):
        raise NotionPublicSignalsSyncError("Notion query returned a non-object response")
    return data


def query_notion_records(token: str, database_id: str, transport: NotionTransport = urllib_notion_transport) -> list[dict[str, Any]]:
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }
    payload: dict[str, Any] = {"page_size": 100}
    records: list[dict[str, Any]] = []
    while True:
        response = transport(url, headers, payload)
        results = response.get("results")
        if not isinstance(results, list):
            raise NotionPublicSignalsSyncError("Notion response is missing results")
        records.extend(notion_page_to_record(page) for page in results if isinstance(page, dict))
        if response.get("has_more") is not True:
            return records
        cursor = response.get("next_cursor")
        if not cursor:
            raise NotionPublicSignalsSyncError("Notion response is missing next_cursor")
        payload = {"page_size": 100, "start_cursor": cursor}


def field(record: dict[str, Any], *names: str) -> Any:
    lowered = {key.lower(): value for key, value in record.items()}
    for name in names:
        if name in record:
            return record[name]
        value = lowered.get(name.lower())
        if value is not None:
            return value
    return None


def quality_hint(record: dict[str, Any]) -> float:
    value = field(record, "Quality Hint", "quality_hint", "Quality")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def signal_title(record: dict[str, Any]) -> str:
    return normalize_text(field(record, "Signal Title", "Title", "Name", "signal_title"))


def signal_summary(record: dict[str, Any]) -> str:
    return normalize_text(field(record, "Summary", "Public Summary", "summary"))


def signal_slug(record: dict[str, Any]) -> str:
    return slugify(normalize_text(field(record, "Slug", "Public Slug", "slug")) or signal_title(record))


def source_url(record: dict[str, Any]) -> str:
    return normalize_text(field(record, "Source URL", "source_url", "Original Source URL"))


def source_label(record: dict[str, Any]) -> str:
    return normalize_text(field(record, "Source Label", "Source Name", "Source", "source_label", "source_name")) or "Source"


def source_priority(record: dict[str, Any]) -> str:
    return normalize_text(field(record, "Source Priority", "Priority", "source_priority"))


def attribution_status(record: dict[str, Any]) -> str:
    return normalize_text(field(record, "Attribution Status", "attribution_status"))


def copyright_status(record: dict[str, Any]) -> str:
    return normalize_text(field(record, "Copyright Status", "copyright_status"))


def agi_relevance(record: dict[str, Any]) -> str:
    return normalize_text(field(record, "AGI Relevance", "agi_relevance"))


def timestamp_value(record: dict[str, Any]) -> str:
    return normalize_text(
        field(
            record,
            "Published Date",
            "Updated Time",
            "Created Time",
            "Last Edited Time",
            "published_date",
            "updated_time",
            "created_time",
            "timestamp",
        )
    )


def tags(record: dict[str, Any]) -> list[str]:
    value = field(record, "Tags", "Tag", "Categories", "Category")
    return [normalize_text(item) for item in as_list(value) if normalize_text(item)]


def text_field(record: dict[str, Any], *names: str, default: str = "") -> str:
    return normalize_text(field(record, *names)) or default


def is_safe_source_url(url: str) -> bool:
    if not url:
        return False
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    lowered = url.lower()
    return not any(term in lowered for term in FORBIDDEN_PUBLIC_TERMS)


def off_topic_public_signal(record: dict[str, Any]) -> bool:
    return topic_off_topic_public_signal(record)


def has_core_public_topic(record: dict[str, Any]) -> bool:
    return topic_has_core_public_topic(record)


def eligibility_blockers(record: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    topic_decision = public_topic_decision(record)
    if source_priority(record) not in PUBLIC_OUTPUT_ALLOWED_PRIORITIES:
        blockers.append("source_priority_below_high")
    if attribution_status(record) != "Complete":
        blockers.append("attribution_incomplete")
    if copyright_status(record) != "Safe Summary Only":
        blockers.append("copyright_not_safe_summary_only")
    if quality_hint(record) < PUBLIC_OUTPUT_MIN_QUALITY:
        blockers.append("quality_hint_below_80")
    if agi_relevance(record) not in PUBLIC_OUTPUT_ALLOWED_AGI_RELEVANCE:
        blockers.append("agi_relevance_below_medium")
    if topic_decision["off_topic_public_signal"]:
        blockers.append("off_topic_public_signal")
    if not topic_decision["has_core_public_topic"]:
        blockers.append("missing_core_public_topic")
    if not signal_title(record):
        blockers.append("missing_signal_title")
    if not signal_summary(record):
        blockers.append("missing_summary")
    if not source_url(record) or not is_safe_source_url(source_url(record)):
        blockers.append("missing_source_url")
    raw_body_status = normalize_text(field(record, "Raw Body Status", "raw_body_status", "Raw Body")).lower()
    if "blocked" in raw_body_status or "raw article" in raw_body_status:
        blockers.append("raw_body_blocked")
    return blockers


def eligible_record(record: dict[str, Any]) -> bool:
    return not eligibility_blockers(record)


def build_sync_report(records: list[dict[str, Any]], existing_slugs: list[str], eligible: list[dict[str, Any]]) -> dict[str, Any]:
    blocked: list[dict[str, Any]] = []
    for record in records:
        reasons = eligibility_blockers(record)
        if reasons:
            blocked.append(
                {
                    "title": signal_title(record) or "(untitled)",
                    "slug": signal_slug(record),
                    "reasons": reasons,
                    "source_priority": source_priority(record),
                    "quality_hint": int(quality_hint(record)),
                    "agi_relevance": agi_relevance(record),
                    "ready_for_pipeline": field(record, "Ready for Pipeline", "ready_for_pipeline") is True,
                    "published": field(record, "Published", "published") is True,
                }
            )
    eligible_slugs = sorted({record["slug"] for record in eligible})
    existing_slug_set = set(existing_slugs)
    return {
        "sync_version": SYNC_VERSION,
        "total_notion_rows": len(records),
        "eligible_public_rows": len(eligible),
        "blocked_rows": len(blocked),
        "blocked_reasons_by_title": {item["title"]: item["reasons"] for item in blocked},
        "blocked": blocked,
        "new_slugs": [slug for slug in eligible_slugs if slug not in existing_slug_set],
        "existing_slugs": sorted(existing_slug_set),
    }


def auto_merge_entry_eligible(entry: dict[str, Any]) -> bool:
    try:
        quality = float(entry.get("quality_hint"))
    except (TypeError, ValueError):
        quality = 0.0
    return (
        entry.get("source_priority") in PUBLIC_OUTPUT_ALLOWED_PRIORITIES
        and entry.get("agi_relevance") in PUBLIC_OUTPUT_ALLOWED_AGI_RELEVANCE
        and quality >= PUBLIC_OUTPUT_MIN_QUALITY
        and entry.get("attribution_status") == "Complete"
        and entry.get("copyright_status") == "Safe Summary Only"
        and bool(entry.get("title"))
        and bool(entry.get("summary"))
        and is_safe_source_url(str(entry.get("source_url") or ""))
        and not off_topic_public_signal(entry)
        and has_core_public_topic(entry)
    )


def changed_signal_slugs(changed_files: list[str]) -> set[str]:
    slugs: set[str] = set()
    for path in changed_files:
        match = re.fullmatch(r"signals/([^/]+)/index\.html", path)
        if match and match.group(1) != "index":
            slugs.add(match.group(1))
    return slugs


def auto_merge_marker_eligible(manifest: dict[str, Any], changed_files: list[str]) -> bool:
    slugs = changed_signal_slugs(changed_files)
    if not slugs:
        return False
    entries = {entry.get("slug"): entry for entry in manifest.get("launched", []) if isinstance(entry, dict)}
    return all(slug in entries and auto_merge_entry_eligible(entries[slug]) for slug in slugs)


class ExistingSignalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.summary = ""
        self._capture: str | None = None
        self._after_summary_heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"h1", "h2", "p"}:
            self._capture = tag

    def handle_endtag(self, tag: str) -> None:
        if tag == self._capture:
            self._capture = None

    def handle_data(self, data: str) -> None:
        text = normalize_text(data)
        if not text:
            return
        if self._capture == "h1" and not self.title:
            self.title = text
        elif self._capture == "h2" and text == "Summary":
            self._after_summary_heading = True
        elif self._capture == "p" and self._after_summary_heading and not self.summary:
            self.summary = text
            self._after_summary_heading = False


def existing_public_signals(output_root: pathlib.Path) -> list[dict[str, Any]]:
    signals_root = output_root / "signals"
    if not signals_root.exists():
        return []
    manifest_slugs: set[str] | None = None
    manifest_path = signals_root / "public_launch_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            launched = manifest.get("launched")
            if isinstance(launched, list):
                manifest_slugs = {
                    normalize_text(item.get("slug"))
                    for item in launched
                    if isinstance(item, dict) and normalize_text(item.get("slug"))
                }
        except (OSError, json.JSONDecodeError):
            manifest_slugs = None
    records: list[dict[str, Any]] = []
    for page in sorted(signals_root.glob("*/index.html")):
        slug = page.parent.name
        if manifest_slugs is not None and slug not in manifest_slugs:
            continue
        html_text = page.read_text(encoding="utf-8", errors="ignore")
        parser = ExistingSignalParser()
        parser.feed(html_text)
        title = parser.title or slug.replace("-", " ").title()
        records.append(
            {
                "signal_id": f"existing_{slug.replace('-', '_')}",
                "slug": slug,
                "title": title,
                "summary": parser.summary or "Existing public Signal summary retained.",
                "source_label": "existing public Signal",
                "source_url": "",
                "source_priority": "",
                "attribution_status": "",
                "copyright_status": "",
                "ready_for_pipeline": True,
                "published": True,
                "agi_relevance": "Retained",
                "quality_hint": "",
                "timestamp": "",
                "tags": [],
                "existing": True,
                "page_path": page,
            }
        )
    return records


def record_from_notion(record: dict[str, Any]) -> dict[str, Any]:
    decision = public_topic_decision(record)
    return {
        "signal_id": normalize_text(field(record, "Signal ID", "signal_id", "_notion_page_id")) or f"notion_{signal_slug(record)}",
        "slug": signal_slug(record),
        "title": signal_title(record),
        "summary": signal_summary(record),
        "why_this_matters": text_field(record, "Why This Matters", "why_this_matters", default="This Signal is included because it passed DysonX public publication safety rules."),
        "agi_relevance": text_field(record, "AGI Relevance", "agi_relevance", default="AGI relevance retained in Notion metadata."),
        "source_label": source_label(record),
        "source_url": source_url(record),
        "source_priority": source_priority(record),
        "attribution_status": attribution_status(record),
        "copyright_status": copyright_status(record),
        "ready_for_pipeline": field(record, "Ready for Pipeline", "ready_for_pipeline") is True,
        "published": field(record, "Published", "published") is True,
        "quality_hint": int(quality_hint(record)),
        "timestamp": timestamp_value(record),
        "risk_notes": text_field(record, "Risk Notes", "Safety Notes", "risk_notes", default="Summary-only; source text not reproduced."),
        "watch_next": text_field(record, "Watch Next", "watch_next", default="Watch for follow-up Signals in the Notion-managed intake."),
        "tags": tags(record),
        "topic_decision": decision,
        "existing": False,
    }


def existing_record_safe(record: dict[str, Any]) -> bool:
    return bool(record.get("title")) and bool(record.get("summary"))


def timestamp_rank(value: Any) -> float:
    text = normalize_text(value)
    if not text:
        return 0.0
    normalized = text.replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return 0.0


def public_signal_sort_key(record: dict[str, Any]) -> tuple[int, int, float, int, int, float, str]:
    priority = SOURCE_PRIORITY_RANK.get(str(record.get("source_priority") or ""), 99)
    relevance = AGI_RELEVANCE_RANK.get(str(record.get("agi_relevance") or ""), 99)
    try:
        quality = float(record.get("quality_hint") or 0)
    except (TypeError, ValueError):
        quality = 0.0
    published_rank = 0 if record.get("published") is True else 1
    ready_rank = 0 if record.get("ready_for_pipeline") is True else 1
    return (priority, relevance, -quality, published_rank, ready_rank, -timestamp_rank(record.get("timestamp")), str(record.get("title") or "").lower())


def public_absolute_url(path: str, seo_base_url: str) -> str:
    return urljoin(f"{seo_base_url}/", path.lstrip("/"))


def seo_description(record: dict[str, Any]) -> str:
    summary = normalize_text(record.get("summary"))
    if len(summary) <= 155:
        return summary
    return summary[:152].rstrip() + "..."


def json_ld_script(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return f'<script type="application/ld+json">{html.escape(payload, quote=False)}</script>'


def render_layout(title: str, body: str, head_extra: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | DysonX Public Signal</title>
{head_extra}
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17202a; line-height: 1.6; background: #ffffff; }}
    main {{ max-width: 860px; margin: 0 auto; padding: 32px 20px 56px; }}
    h1 {{ margin: 0 0 16px; font-size: clamp(2rem, 5vw, 3.25rem); line-height: 1.05; }}
    h2 {{ margin-top: 28px; font-size: 1.05rem; }}
    a {{ color: #0f6f8f; }}
    code {{ background: #f6f8fa; padding: 1px 4px; }}
    .status {{ display: inline-block; margin-bottom: 16px; padding: 5px 9px; border: 1px solid #97b6c4; background: #eef7fa; color: #24505e; font-weight: 700; font-size: 0.85rem; }}
    .notice {{ border: 1px solid #d8dee6; border-left: 4px solid #97b6c4; background: #f6f8fa; padding: 14px; }}
    .meta {{ display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin: 20px 0; }}
    .muted {{ color: #667085; font-size: 0.9rem; }}
  </style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def signal_seo_head(record: dict[str, Any], refreshed_at: str, seo_base_url: str) -> str:
    title = f"{normalize_text(record['title'])} | DysonX Public Signal"
    description = seo_description(record)
    canonical = public_absolute_url(f"/signals/{record['slug']}/", seo_base_url)
    json_ld = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": normalize_text(record["title"]),
        "description": description,
        "url": canonical,
        "dateModified": refreshed_at,
        "isAccessibleForFree": True,
        "publisher": {
            "@type": "Organization",
            "name": "EnergizeOS Media",
            "url": seo_base_url,
        },
        "mainEntityOfPage": canonical,
    }
    if record.get("source_url"):
        json_ld["citation"] = normalize_text(record["source_url"])
    return f"""
  <meta name="description" content="{escape(description, quote=True)}">
  <link rel="canonical" href="{escape(canonical, quote=True)}">
  <meta property="og:title" content="{escape(title, quote=True)}">
  <meta property="og:description" content="{escape(description, quote=True)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{escape(canonical, quote=True)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{escape(title, quote=True)}">
  <meta name="twitter:description" content="{escape(description, quote=True)}">
  {json_ld_script(json_ld)}"""


def render_signal_page(record: dict[str, Any], refreshed_at: str, seo_base_url: str) -> str:
    source_html = PUBLIC_SAFE_SOURCE_NOTE
    if record.get("source_url") and is_safe_source_url(str(record["source_url"])):
        source_html = f'<a href="{escape(record["source_url"], quote=True)}" rel="nofollow noopener">{escape(record["source_label"])}</a>'
    category = " / ".join(record.get("tags") or []) or "Signal"
    body = f"""
<p class="status">Published</p>
<h1>{escape(record["title"])}</h1>
<div class="notice"><strong>DysonX Signal.</strong> This page is a summary-only public Signal from the Notion-managed content layer. It does not reproduce raw source text.</div>
<div class="meta">
  <div><strong>Slug</strong><br><code>{escape(record["slug"])}</code></div>
  <div><strong>Category</strong><br>{escape(category)}</div>
  <div><strong>AGI relevance</strong><br>{escape(record.get("agi_relevance") or "Retained")}</div>
</div>
<h2>Summary</h2>
<p>{escape(record["summary"])}</p>
<h2>Why This Matters</h2>
<p>{escape(record.get("why_this_matters") or "This Signal passed DysonX public publication safety rules.")}</p>
<h2>AGI Relevance</h2>
<p>{escape(record.get("agi_relevance") or "AGI relevance retained in Notion metadata.")}</p>
<h2>Source Attribution</h2>
<p>{source_html}</p>
<h2>Risk And Safety Notes</h2>
<p>{escape(record.get("risk_notes") or "Summary-only; source text not reproduced.")}</p>
<h2>Watch Next</h2>
<p>{escape(record.get("watch_next") or "Watch for follow-up Signals in the Notion-managed intake.")}</p>
<p><a href="/">Home</a> · <a href="/signals/">Back to Public Signals</a></p>
<p class="muted">Content refreshed at {escape(refreshed_at)}. OpenAI was not called. Source pages were not scraped.</p>
"""
    return render_layout(record["title"], body, signal_seo_head(record, refreshed_at, seo_base_url))


def organization_json_ld(seo_base_url: str) -> str:
    return json_ld_script(
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "EnergizeOS Media",
            "url": seo_base_url,
            "publishingPrinciples": public_absolute_url("/signals/", seo_base_url),
        }
    )


def render_index(records: list[dict[str, Any]], blocked_count: int, refreshed_at: str, seo_base_url: str) -> str:
    items = []
    for record in records:
        tag_html = "".join(f'<span class="tag">{escape(tag)}</span>' for tag in record.get("tags", []))
        quality = f" · Quality hint: {escape(record['quality_hint'])}" if record.get("quality_hint") != "" else ""
        items.append(
            f"""
<article>
  {tag_html}
  <h2><a href="/signals/{escape(record['slug'], quote=True)}/">{escape(record['title'])}</a></h2>
  <p>{escape(record['summary'])}</p>
  <p class="meta">Source: {escape(record.get('source_label') or 'Notion Signal Intake')}{quality}</p>
</article>
"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DysonX Public Signals</title>
  <meta name="description" content="DysonX Public Signals track source-attributed AI and AGI intelligence from the Notion-managed content layer.">
  <link rel="canonical" href="{escape(public_absolute_url('/signals/', seo_base_url), quote=True)}">
  <link rel="alternate" type="application/rss+xml" title="DysonX Public Signals RSS" href="{escape(public_absolute_url('/rss.xml', seo_base_url), quote=True)}">
  <link rel="alternate" type="application/feed+json" title="DysonX Public Signals JSON Feed" href="{escape(public_absolute_url('/feed.json', seo_base_url), quote=True)}">
  <meta property="og:title" content="DysonX Public Signals">
  <meta property="og:description" content="Source-attributed public Signals tracking AI and AGI intelligence.">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{escape(public_absolute_url('/signals/', seo_base_url), quote=True)}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="DysonX Public Signals">
  <meta name="twitter:description" content="Source-attributed public Signals tracking AI and AGI intelligence.">
  {organization_json_ld(seo_base_url)}
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17202a; line-height: 1.55; }}
    main {{ max-width: 1040px; margin: 0 auto; padding: 28px 20px 56px; }}
    .status {{ display: inline-block; margin-bottom: 16px; padding: 5px 9px; border: 1px solid #97b6c4; background: #eef7fa; color: #24505e; font-weight: 700; font-size: 0.85rem; }}
    .notice {{ border: 1px solid #d8dee6; border-left: 4px solid #97b6c4; background: #f6f8fa; padding: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; margin-top: 24px; }}
    article {{ border: 1px solid #d8dee6; padding: 18px; background: #fff; }}
    a {{ color: #0f6f8f; }}
    code {{ background: #f6f8fa; padding: 1px 4px; }}
    .meta {{ color: #667085; font-size: 0.9rem; }}
    .tag {{ display: inline-block; margin: 0 6px 6px 0; padding: 2px 7px; border: 1px solid #d8dee6; background: #f6f8fa; font-size: 0.78rem; color: #475467; }}
  </style>
</head>
<body>
<main>
<p class="status">Published · Notion content refresh</p>
<h1>DysonX Public Signals</h1>
<div class="notice">
  DysonX public Signals are refreshed from Notion-approved, source-attributed, summary-only records. The public surface remains static, domain-agnostic, and reviewable through pull requests.
</div>
<p><strong>Published Signals:</strong> {len(records)}. <strong>Blocked Notion rows:</strong> {blocked_count}. <strong>Source mode:</strong> public-safe summaries with attribution links.</p>
<div class="grid">
{''.join(items)}
</div>
<p class="meta">Content refreshed at {escape(refreshed_at)}. Source text is not reproduced. OpenAI was not called. Source pages were not scraped.</p>
<p><a href="/">Home</a></p>
</main>
</body>
</html>
"""


def assert_public_safe(text: str, label: str) -> None:
    lowered = text.lower()
    matches = [term for term in FORBIDDEN_PUBLIC_TERMS if term in lowered]
    if matches:
        raise NotionPublicSignalsSyncError(f"{label} contains forbidden public terms: {', '.join(matches)}")


def material_signature(records: list[dict[str, Any]], blocked_count: int) -> str:
    material_records = [
        {
            "signal_id": record.get("signal_id", ""),
            "slug": record.get("slug", ""),
            "title": record.get("title", ""),
            "summary": record.get("summary", ""),
            "why_this_matters": record.get("why_this_matters", ""),
            "agi_relevance": record.get("agi_relevance", ""),
            "source_label": record.get("source_label", ""),
            "source_url": record.get("source_url", ""),
            "source_priority": record.get("source_priority", ""),
            "attribution_status": record.get("attribution_status", ""),
            "copyright_status": record.get("copyright_status", ""),
            "ready_for_pipeline": bool(record.get("ready_for_pipeline")),
            "published": bool(record.get("published")),
            "quality_hint": record.get("quality_hint", ""),
            "risk_notes": record.get("risk_notes", ""),
            "watch_next": record.get("watch_next", ""),
            "tags": record.get("tags", []),
        }
        for record in records
    ]
    material = {
        "pages_launched": len(records),
        "pages_blocked": blocked_count,
        "records": material_records,
    }
    payload = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_manifest(records: list[dict[str, Any]], blocked_count: int, refreshed_at: str) -> dict[str, Any]:
    launched = [
        {
            "signal_id": record["signal_id"],
            "slug": record["slug"],
            "title": record["title"],
            "summary": record.get("summary", ""),
            "public_path": f"signals/{record['slug']}/index.html",
            "public_url_path": f"/signals/{record['slug']}/",
            "published": True,
            "source_name": record.get("source_label", ""),
            "source_url": record.get("source_url", ""),
            "source_priority": record.get("source_priority", ""),
            "agi_relevance": record.get("agi_relevance", ""),
            "attribution_status": record.get("attribution_status", ""),
            "copyright_status": record.get("copyright_status", ""),
            "quality_hint": record.get("quality_hint", ""),
            "ready_for_pipeline": bool(record.get("ready_for_pipeline")),
            "topic_decision": record.get("topic_decision") or public_topic_decision(record),
            "production_publish_performed": True,
        }
        for record in records
    ]
    return {
        "launch_version": "notion_public_signals_sync_v1",
        "content_refreshed_at": refreshed_at,
        "pages_launched": len(records),
        "pages_blocked": blocked_count,
        "public_output_root": ".",
        "material_signature": material_signature(records, blocked_count),
        "launched": launched,
        "openai_call_performed": False,
        "source_scraping_performed": False,
        "network_source_fetch_performed": False,
        "raw_article_body_copied": False,
        "manual_external_deployment_performed": False,
        "workflow_dispatch_performed": False,
        "social_distribution_performed": False,
        "newsletter_distribution_performed": False,
        "source_pack_manifest": "notion_signal_intake_public_safe_reference",
        "source_release_guard_report": "static_preview_link_integrity_check",
    }


def build_artifact_manifest(records: list[dict[str, Any]], public_manifest: dict[str, Any]) -> dict[str, Any]:
    material = normalize_text(public_manifest.get("material_signature"))
    artifact_paths = [
        "signals/index.html",
        "signals/public_launch_manifest.json",
        "signals/public_artifact_manifest.json",
        "robots.txt",
        "sitemap.xml",
        "rss.xml",
        "feed.json",
        *[f"signals/{record['slug']}/index.html" for record in records],
    ]
    artifacts = [build_artifact_entry(path, material) for path in sorted(set(artifact_paths))]
    return {
        "contract_version": PUBLIC_SIGNAL_CONTRACT_VERSION,
        "policy_version": PUBLIC_SIGNAL_POLICY_VERSION,
        "generated_from_public_signal_manifest": True,
        "public_launch_manifest_path": "signals/public_launch_manifest.json",
        "public_launch_manifest_material_signature": material,
        "allowed_artifact_classes": sorted(ALLOWED_ARTIFACT_CLASSES),
        "allowed_safe_embeds": sorted(ALLOWED_SAFE_EMBEDS),
        "forbidden_content_classes": sorted(FORBIDDEN_CONTENT_CLASSES),
        "artifacts": artifacts,
    }


def stable_lastmod(refreshed_at: str) -> str:
    text = normalize_text(refreshed_at)
    return text[:10] if len(text) >= 10 else text


def render_robots(seo_base_url: str) -> str:
    return f"""User-agent: *
Allow: /
Sitemap: {seo_base_url}/sitemap.xml
"""


def render_sitemap(records: list[dict[str, Any]], refreshed_at: str, seo_base_url: str) -> str:
    lastmod = stable_lastmod(refreshed_at)
    urls = ["/", "/signals/", *[f"/signals/{record['slug']}/" for record in records]]
    items = "\n".join(
        f"""  <url>
    <loc>{escape(public_absolute_url(path, seo_base_url))}</loc>
    <lastmod>{escape(lastmod)}</lastmod>
  </url>"""
        for path in urls
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{items}
</urlset>
"""


def render_rss(records: list[dict[str, Any]], refreshed_at: str, seo_base_url: str) -> str:
    items = []
    for record in records[:DEFAULT_MAX_PUBLIC_SIGNALS]:
        public_url = public_absolute_url(f"/signals/{record['slug']}/", seo_base_url)
        source = record.get("source_url") or public_url
        items.append(
            f"""    <item>
      <title>{escape(record['title'])}</title>
      <link>{escape(public_url)}</link>
      <guid>{escape(public_url)}</guid>
      <description>{escape(record.get('summary', ''))}</description>
      <source url="{escape(source, quote=True)}">{escape(record.get('source_label') or 'Source')}</source>
      <pubDate>{escape(refreshed_at)}</pubDate>
    </item>"""
        )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>DysonX Public Signals</title>
    <link>{seo_base_url}/signals/</link>
    <description>Source-attributed public Signals tracking AI and AGI intelligence.</description>
{chr(10).join(items)}
  </channel>
</rss>
"""


def render_json_feed(records: list[dict[str, Any]], refreshed_at: str, seo_base_url: str) -> str:
    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": "DysonX Public Signals",
        "home_page_url": public_absolute_url("/signals/", seo_base_url),
        "feed_url": public_absolute_url("/feed.json", seo_base_url),
        "description": "Source-attributed public Signals tracking AI and AGI intelligence.",
        "items": [
            {
                "id": public_absolute_url(f"/signals/{record['slug']}/", seo_base_url),
                "url": public_absolute_url(f"/signals/{record['slug']}/", seo_base_url),
                "title": normalize_text(record["title"]),
                "summary": normalize_text(record.get("summary", "")),
                "content_text": normalize_text(record.get("summary", "")),
                "date_modified": refreshed_at,
                "external_url": normalize_text(record.get("source_url", "")),
                "authors": [{"name": normalize_text(record.get("source_label") or "Source")}],
            }
            for record in records[:DEFAULT_MAX_PUBLIC_SIGNALS]
        ],
    }
    return json.dumps(feed, indent=2, sort_keys=True) + "\n"


def manifest_material_view(manifest: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in manifest.items() if key != "content_refreshed_at"}


def existing_manifest(signals_root: pathlib.Path) -> dict[str, Any] | None:
    manifest_path = signals_root / "public_launch_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def stable_refreshed_at(signals_root: pathlib.Path, candidate_manifest: dict[str, Any], fallback_refreshed_at: str) -> str:
    previous_manifest = existing_manifest(signals_root)
    if not previous_manifest:
        return fallback_refreshed_at
    previous_refreshed_at = normalize_text(previous_manifest.get("content_refreshed_at"))
    if not previous_refreshed_at:
        return fallback_refreshed_at
    if manifest_material_view(previous_manifest) == manifest_material_view(candidate_manifest):
        return previous_refreshed_at
    return fallback_refreshed_at


def sync_records(
    records: list[dict[str, Any]],
    output_root: pathlib.Path = DEFAULT_OUTPUT_ROOT,
    refreshed_at: str | None = None,
    output_report: pathlib.Path | None = None,
    max_public_signals: int = DEFAULT_MAX_PUBLIC_SIGNALS,
) -> dict[str, Any]:
    refreshed_at = refreshed_at or utc_now()
    output_root = output_root.resolve()
    seo_base_url = public_seo_base_url(output_root)
    signals_root = output_root / "signals"
    signals_root.mkdir(parents=True, exist_ok=True)

    existing = existing_public_signals(output_root)
    existing_slugs = [record["slug"] for record in existing]
    eligible = [record_from_notion(record) for record in records if eligible_record(record)]
    blocked_count = len(records) - len(eligible)
    report = build_sync_report(records, existing_slugs, eligible)
    eligible_by_slug = {record["slug"]: record for record in eligible}
    ranked_eligible = sorted(eligible_by_slug.values(), key=public_signal_sort_key)
    selected = ranked_eligible[:max_public_signals]
    selected_slugs = {record["slug"] for record in selected}
    remaining_slots = max(0, max_public_signals - len(selected))
    preserved_existing = [
        record
        for record in existing
        if record["slug"] not in selected_slugs and existing_record_safe(record)
    ][:remaining_slots]
    by_slug = {record["slug"]: record for record in preserved_existing}
    for record in selected:
        by_slug[record["slug"]] = record
    merged = sorted(by_slug.values(), key=public_signal_sort_key)
    candidate_manifest = build_manifest(merged, blocked_count, refreshed_at)
    refreshed_at = stable_refreshed_at(signals_root, candidate_manifest, refreshed_at)

    for record in merged:
        if record.get("existing") and not any(item["slug"] == record["slug"] for item in eligible):
            continue
        page_html = render_signal_page(record, refreshed_at, seo_base_url)
        assert_public_safe(page_html, f"Signal page {record['slug']}")
        page_dir = signals_root / record["slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(page_html, encoding="utf-8")

    index_html = render_index(merged, blocked_count, refreshed_at, seo_base_url)
    assert_public_safe(index_html, "Signals index")
    (signals_root / "index.html").write_text(index_html, encoding="utf-8")

    manifest = build_manifest(merged, blocked_count, refreshed_at)
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    assert_public_safe(manifest_text, "public launch manifest")
    (signals_root / "public_launch_manifest.json").write_text(manifest_text, encoding="utf-8")
    artifact_manifest = build_artifact_manifest(merged, manifest)
    artifact_manifest_text = json.dumps(artifact_manifest, indent=2, sort_keys=True) + "\n"
    assert_public_safe(artifact_manifest_text, "public artifact manifest")
    (signals_root / "public_artifact_manifest.json").write_text(artifact_manifest_text, encoding="utf-8")
    seo_outputs = {
        "robots.txt": render_robots(seo_base_url),
        "sitemap.xml": render_sitemap(merged, refreshed_at, seo_base_url),
        "rss.xml": render_rss(merged, refreshed_at, seo_base_url),
        "feed.json": render_json_feed(merged, refreshed_at, seo_base_url),
    }
    for relative_path, text in seo_outputs.items():
        assert_public_safe(text, relative_path)
        (output_root / relative_path).write_text(text, encoding="utf-8")
    if output_report:
        output_report.parent.mkdir(parents=True, exist_ok=True)
        report_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
        assert_public_safe(report_text, "public Signals sync report")
        output_report.write_text(report_text, encoding="utf-8")
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync Notion-approved DysonX public Signals into static pages.")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Repository/public output root.")
    parser.add_argument("--fixture-json", help="Optional local Notion-shaped fixture JSON for offline validation.")
    parser.add_argument("--output-report", help="Optional JSON diagnostics report path.")
    parser.add_argument("--max-public-signals", type=int, default=DEFAULT_MAX_PUBLIC_SIGNALS, help="Maximum public Signals to include.")
    return parser.parse_args(argv)


def load_fixture_records(path: pathlib.Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return [item for item in data["records"] if isinstance(item, dict)]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    raise NotionPublicSignalsSyncError("fixture JSON must be a list or object with records")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.fixture_json:
            records = load_fixture_records(pathlib.Path(args.fixture_json))
        else:
            token = os.environ.get(TOKEN_ENV)
            database_id = os.environ.get(DATABASE_ID_ENV)
            missing = [name for name, value in ((TOKEN_ENV, token), (DATABASE_ID_ENV, database_id)) if not value]
            if missing:
                raise NotionPublicSignalsSyncError(f"Missing required environment variables: {', '.join(missing)}")
            assert token is not None and database_id is not None
            records = query_notion_records(token, database_id)
        manifest = sync_records(
            records,
            pathlib.Path(args.output_root),
            output_report=pathlib.Path(args.output_report) if args.output_report else None,
            max_public_signals=args.max_public_signals,
        )
    except (OSError, json.JSONDecodeError, NotionPublicSignalsSyncError) as exc:
        print(f"[notion-public-signals-sync] failed: {exc}", file=sys.stderr)
        return 2
    print(
        "[notion-public-signals-sync] PASS "
        f"pages_launched={manifest['pages_launched']} pages_blocked={manifest['pages_blocked']} "
        "openai_call_performed=False source_scraping_performed=False"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
