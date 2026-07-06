#!/usr/bin/env python3
"""DysonX Source Collector V1.

Reads enabled Notion-managed DysonX Sources, collects recent public metadata,
and writes safe candidate Signals into DysonX Signal Intake.
"""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import http.client
import html
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from html.parser import HTMLParser
from typing import Any, Callable


NOTION_TOKEN_ENV = "NOTION_TOKEN"
SOURCES_DATABASE_ENV = "DYSONX_NOTION_SOURCES_DATABASE_ID"
SIGNAL_INTAKE_DATABASE_ENV = "NOTION_SIGNAL_INTAKE_DATABASE_ID"
NOTION_VERSION = "2022-06-28"
SUPPORTED_SOURCE_TYPES = {"rss", "atom", "feed", "arxiv", "official website", "website", "government", "policy", "manual"}
ALLOWED_PRIORITIES = {"Critical", "High", "Medium"}
COPYRIGHT_STATUS = "Safe Summary Only"
ATTRIBUTION_STATUS = "Complete"
OPENAI_CALL_PERFORMED = False
SOURCE_PAGE_BODY_SCRAPING_PERFORMED = False
PUBLIC_STATIC_FILES_WRITTEN = False

AI_RELEVANCE_KEYWORDS = (
    "ai",
    "agi",
    "agent",
    "agents",
    "agentic",
    "model",
    "models",
    "evaluation",
    "eval",
    "compute",
    "safety",
    "policy",
    "alignment",
    "robotics",
    "multimodal",
    "inference",
    "benchmark",
    "foundation model",
)


class SourceCollectorError(RuntimeError):
    """Raised when collector input or Notion IO fails."""


NotionTransport = Callable[[str, dict[str, str], dict[str, Any] | None, str], dict[str, Any]]
FetchTransport = Callable[[str], str]


@dataclass(frozen=True)
class CollectedSourceItems:
    items: list[SourceItem]
    fetched_url: str
    fallback_used: bool = False
    fallback_reason: str = ""


@dataclass(frozen=True)
class SourceRecord:
    notion_page_id: str
    name: str
    url: str
    source_type: str
    platform: str
    priority: str
    authority_score: int
    enabled: bool
    fetch_frequency: str = ""
    last_fetched_at: str = ""


@dataclass(frozen=True)
class SourceItem:
    title: str
    link: str
    published_date: str
    summary: str
    source_name: str
    source_url: str
    source_type: str
    priority: str
    authority_score: int
    attribution_complete: bool


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


def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def strip_markup(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value)
    return normalize_text(html.unescape(text))


def short_summary(value: str, limit: int = 260) -> str:
    text = strip_markup(value)
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."


def parse_date(value: str) -> str:
    value = normalize_text(value)
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except (TypeError, ValueError):
        return value


def absolute_http_url(value: str, base_url: str = "") -> str:
    url = urllib.parse.urljoin(normalize_text(base_url), normalize_text(value))
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return url


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
        raise SourceCollectorError("Notion page is missing properties")
    record = {
        field_name: notion_property_value(property_value)
        for field_name, property_value in properties.items()
        if isinstance(property_value, dict)
    }
    record["_notion_page_id"] = normalize_text(page.get("id"))
    return record


def field(record: dict[str, Any], *names: str) -> Any:
    lowered = {key.lower(): value for key, value in record.items()}
    for name in names:
        if name in record:
            return record[name]
        value = lowered.get(name.lower())
        if value is not None:
            return value
    return None


def source_from_record(record: dict[str, Any]) -> SourceRecord:
    source_type = normalize_text(field(record, "Source Type", "source_type", "Type"))
    platform = normalize_text(field(record, "Platform", "platform"))
    authority = field(record, "Authority Score", "authority_score", "Authority")
    try:
        authority_score = int(authority)
    except (TypeError, ValueError):
        authority_score = 0
    return SourceRecord(
        notion_page_id=normalize_text(field(record, "_notion_page_id", "id")),
        name=normalize_text(field(record, "Name", "Source Name", "name")) or "Untitled Source",
        url=normalize_text(field(record, "URL", "Feed URL", "Source URL", "url")),
        source_type=source_type,
        platform=platform,
        priority=normalize_text(field(record, "Priority", "priority")),
        authority_score=authority_score,
        enabled=field(record, "Enabled", "enabled") is True,
        fetch_frequency=normalize_text(field(record, "Fetch Frequency", "fetch_frequency")),
        last_fetched_at=normalize_text(field(record, "Last Fetched At", "last_fetched_at")),
    )


def supported_source(source: SourceRecord) -> bool:
    source_type = (source.source_type or source.platform).lower()
    platform = source.platform.lower()
    joined = f"{source_type} {platform}"
    return any(kind in joined for kind in SUPPORTED_SOURCE_TYPES)


def frequency_due(source: SourceRecord, now: dt.datetime | None = None) -> bool:
    if not source.last_fetched_at:
        return True
    frequency = source.fetch_frequency.lower()
    hours = 24
    if "hour" in frequency:
        match = re.search(r"(\d+)", frequency)
        hours = int(match.group(1)) if match else 1
    elif "daily" in frequency:
        hours = 24
    elif "weekly" in frequency:
        hours = 24 * 7
    try:
        last = dt.datetime.fromisoformat(source.last_fetched_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    now = now or dt.datetime.now(dt.timezone.utc)
    return now - last >= dt.timedelta(hours=hours)


def eligible_source(source: SourceRecord) -> bool:
    return (
        source.enabled
        and source.priority in ALLOWED_PRIORITIES
        and bool(source.url)
        and supported_source(source)
        and frequency_due(source)
    )


class MetadataHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title = ""
        self.description = ""
        self.canonical = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attr_map.get("name", "").lower()
            prop = attr_map.get("property", "").lower()
            if name == "description" or prop == "og:description":
                self.description = self.description or attr_map.get("content", "")
        elif tag == "link" and attr_map.get("rel", "").lower() == "canonical":
            self.canonical = attr_map.get("href", "")

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "DysonXSourceCollectorV1/1.0 (+https://github.com/enxpower/media)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html;q=0.8, */*;q=0.5",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read(2_000_000).decode("utf-8", errors="ignore")
    except (urllib.error.URLError, http.client.HTTPException, OSError, TimeoutError) as exc:
        raise SourceCollectorError(f"source fetch failed: {exc}") from exc


def official_metadata_fallback_urls(source: SourceRecord) -> list[str]:
    """Return same-owner metadata endpoints for stale or bot-blocked source URLs."""
    parsed = urllib.parse.urlparse(source.url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    name = source.name.lower()
    fallbacks: list[str] = []
    if host == "openai.com" or host.endswith(".openai.com"):
        fallbacks.append("https://openai.com/news/rss.xml")
    if host in {"developer.nvidia.com", "developer-blogs.nvidia.com"} or "nvidia developer" in name:
        fallbacks.append("https://developer.nvidia.com/blog/feed/")
    if "nvidia" in host and "blog" in path:
        fallbacks.append("https://developer.nvidia.com/blog/feed/")
    return [url for index, url in enumerate(fallbacks) if url and url not in fallbacks[:index] and url != source.url]


def xml_text(element: ET.Element, names: tuple[str, ...]) -> str:
    for child in list(element):
        local = child.tag.rsplit("}", 1)[-1].lower()
        if local in names and child.text:
            return normalize_text(child.text)
    return ""


def xml_link(element: ET.Element) -> str:
    for child in list(element):
        local = child.tag.rsplit("}", 1)[-1].lower()
        if local == "link":
            href = child.attrib.get("href")
            if href:
                return normalize_text(href)
            if child.text:
                return normalize_text(child.text)
    return ""


def parse_feed_items(xml_text_value: str, source: SourceRecord) -> list[SourceItem]:
    try:
        root = ET.fromstring(xml_text_value)
    except ET.ParseError as exc:
        raise SourceCollectorError(f"feed parse failed: {exc}") from exc
    entries = [item for item in root.iter() if item.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}]
    items: list[SourceItem] = []
    for entry in entries[:20]:
        title = xml_text(entry, ("title",))
        link = absolute_http_url(xml_link(entry), source.url)
        summary = xml_text(entry, ("description", "summary", "subtitle", "content"))
        published = xml_text(entry, ("pubdate", "published", "updated", "date"))
        if title and link:
            items.append(
                SourceItem(
                    title=title,
                    link=link,
                    published_date=parse_date(published),
                    summary=short_summary(summary or title),
                    source_name=source.name,
                    source_url=source.url,
                    source_type=source.source_type or source.platform,
                    priority=source.priority,
                    authority_score=source.authority_score,
                    attribution_complete=True,
                )
            )
    return items


def parse_page_metadata(page_html: str, source: SourceRecord) -> list[SourceItem]:
    parser = MetadataHTMLParser()
    parser.feed(page_html)
    title = normalize_text(parser.title) or source.name
    link = absolute_http_url(parser.canonical or source.url, source.url)
    summary = short_summary(parser.description or title)
    return [
        SourceItem(
            title=title,
            link=link,
            published_date="",
            summary=summary,
            source_name=source.name,
            source_url=source.url,
            source_type=source.source_type or source.platform,
            priority=source.priority,
            authority_score=source.authority_score,
            attribution_complete=bool(link),
        )
    ]


def collect_source_items_from_url(source: SourceRecord, url: str, fetch: FetchTransport = fetch_url) -> list[SourceItem]:
    try:
        content = fetch(url)
    except (urllib.error.URLError, http.client.HTTPException, OSError, TimeoutError) as exc:
        raise SourceCollectorError(f"source fetch failed: {exc}") from exc
    source = SourceRecord(
        notion_page_id=source.notion_page_id,
        name=source.name,
        url=url,
        source_type=source.source_type,
        platform=source.platform,
        priority=source.priority,
        authority_score=source.authority_score,
        enabled=source.enabled,
        fetch_frequency=source.fetch_frequency,
        last_fetched_at=source.last_fetched_at,
    )
    source_kind = f"{source.source_type} {source.platform}".lower()
    if "<rss" in content[:500].lower() or "<feed" in content[:500].lower() or any(token in source_kind for token in ("rss", "atom", "feed", "arxiv")):
        return parse_feed_items(content, source)
    return parse_page_metadata(content, source)


def collect_source_items(source: SourceRecord, fetch: FetchTransport = fetch_url) -> CollectedSourceItems:
    try:
        return CollectedSourceItems(items=collect_source_items_from_url(source, source.url, fetch=fetch), fetched_url=source.url)
    except SourceCollectorError as primary_error:
        fallback_errors: list[str] = []
        for fallback_url in official_metadata_fallback_urls(source):
            try:
                return CollectedSourceItems(
                    items=collect_source_items_from_url(source, fallback_url, fetch=fetch),
                    fetched_url=fallback_url,
                    fallback_used=True,
                    fallback_reason=f"{primary_error}; retried official metadata endpoint",
                )
            except SourceCollectorError as fallback_error:
                fallback_errors.append(f"{fallback_url}: {fallback_error}")
        if fallback_errors:
            raise SourceCollectorError(f"{primary_error}; fallback fetch failed: {'; '.join(fallback_errors)}") from primary_error
        raise


def ai_relevance_text(item: SourceItem) -> str:
    text = f"{item.title} {item.summary} {item.source_type}".lower()
    matches = [keyword for keyword in AI_RELEVANCE_KEYWORDS if keyword in text]
    if not matches:
        return "Low"
    if any(keyword in matches for keyword in ("agi", "agent", "agents", "agentic", "evaluation", "compute", "safety", "policy")):
        return "High"
    return "Medium"


def category_for(item: SourceItem) -> str:
    text = f"{item.title} {item.summary}".lower()
    if "policy" in text or "government" in item.source_type.lower():
        return "Policy"
    if "safety" in text or "alignment" in text:
        return "Safety"
    if "arxiv" in item.source_type.lower() or "research" in text or "paper" in text:
        return "Research"
    if "agent" in text:
        return "Research"
    if "compute" in text or "inference" in text:
        return "Compute"
    return "Market Signal"


def quality_hint(item: SourceItem) -> int:
    score = min(95, max(45, item.authority_score))
    if ai_relevance_text(item) == "Low":
        score -= 20
    if not item.attribution_complete or not item.link:
        score -= 25
    if len(item.summary) > 280:
        score -= 10
    if item.priority == "Critical":
        score += 3
    return max(0, min(100, score))


def safe_summary_only(item: SourceItem) -> str:
    return short_summary(item.summary or item.title, 240)


def can_auto_publish(item: SourceItem, candidate: dict[str, Any]) -> bool:
    return (
        item.priority == "Critical"
        and item.authority_score >= 85
        and item.attribution_complete
        and bool(absolute_http_url(item.link))
        and len(candidate["Summary"]) <= 260
        and candidate["Copyright Status"] == COPYRIGHT_STATUS
        and candidate["AGI Relevance"] != "Low"
        and candidate["Quality Hint"] >= 92
        and "raw" not in json.dumps(candidate).lower()
    )


def candidate_from_item(item: SourceItem) -> dict[str, Any]:
    summary = safe_summary_only(item)
    source_url = absolute_http_url(item.link)
    attribution_complete = item.attribution_complete and bool(source_url)
    candidate = {
        "Signal Title": item.title,
        "Slug": slugify(item.title),
        "Source Name": item.source_name,
        "Source URL": source_url,
        "Source Priority": item.priority,
        "Published Date": item.published_date,
        "Category": category_for(item),
        "AGI Relevance": ai_relevance_text(item),
        "Summary": summary,
        "Why It Matters": f"This source is a monitored DysonX {item.priority.lower()}-priority signal for {category_for(item).lower()} tracking.",
        "Evidence": f"Metadata collected from {item.source_name}; no source-page body was copied.",
        "Risk / Safety Notes": "Rule-based V1 candidate. Requires Owner review unless all auto-publish gates pass.",
        "Attribution Status": ATTRIBUTION_STATUS if attribution_complete else "Missing",
        "Copyright Status": COPYRIGHT_STATUS,
        "Quality Hint": quality_hint(item),
        "Status": "Needs Owner Review",
        "Ready for Pipeline": False,
        "Published": False,
        "Collector Version": "source_collector_v1",
    }
    if can_auto_publish(item, candidate):
        candidate["Ready for Pipeline"] = True
        candidate["Published"] = True
        candidate["Status"] = "Ready for Quality Audit"
    elif candidate["AGI Relevance"] == "Low":
        candidate["Status"] = "Needs More Sources"
    return candidate


def existing_keys(records: list[dict[str, Any]]) -> set[str]:
    keys: set[str] = set()
    for record in records:
        url = normalize_text(field(record, "Source URL", "source_url"))
        title = normalize_text(field(record, "Signal Title", "Title", "Name"))
        if url:
            keys.add(f"url:{url.lower()}")
        if title:
            keys.add(f"title:{normalized_title(title)}")
    return keys


def skip_source_reason(source: SourceRecord) -> str:
    if not source.enabled:
        return "source_disabled"
    if source.priority not in ALLOWED_PRIORITIES:
        return "priority_not_allowed"
    if not source.url:
        return "missing_url"
    if not supported_source(source):
        return "unsupported_source_type"
    if not frequency_due(source):
        return "fetch_frequency_not_due"
    return "not_eligible"


def dedupe_candidates(
    candidates: list[dict[str, Any]], existing_records: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], int, list[dict[str, Any]], dict[str, int]]:
    keys = existing_keys(existing_records)
    emitted: list[dict[str, Any]] = []
    skipped_candidates: list[dict[str, Any]] = []
    skipped_by_reason = {"duplicate_source_url": 0, "duplicate_title": 0}
    skipped = 0
    for candidate in candidates:
        url_key = f"url:{normalize_text(candidate.get('Source URL')).lower()}"
        title_key = f"title:{normalized_title(normalize_text(candidate.get('Signal Title')))}"
        matched_keys = [key for key in (url_key, title_key) if key in keys]
        if matched_keys:
            skipped += 1
            reason = "duplicate_source_url" if url_key in matched_keys else "duplicate_title"
            skipped_by_reason[reason] += 1
            skipped_candidates.append(
                {
                    "source": normalize_text(candidate.get("Source Name")),
                    "title": normalize_text(candidate.get("Signal Title")),
                    "source_url": normalize_text(candidate.get("Source URL")),
                    "reason": reason,
                    "matched_keys": matched_keys,
                }
            )
            continue
        keys.add(url_key)
        keys.add(title_key)
        emitted.append(candidate)
    return emitted, skipped, skipped_candidates, skipped_by_reason


def freshness_diagnostic(raw_items_seen: int, new_candidates_created: int, duplicates_skipped: int) -> str:
    if raw_items_seen > 0 and new_candidates_created == 0 and duplicates_skipped == raw_items_seen:
        return "no fresh source items found; all fetched items matched existing Signal Intake rows"
    if raw_items_seen == 0:
        return "no source items fetched"
    if new_candidates_created > 0:
        return "fresh source items found"
    return "no new candidates created"


def urllib_notion_transport(url: str, headers: dict[str, str], payload: dict[str, Any] | None, method: str) -> dict[str, Any]:
    data = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise SourceCollectorError(f"Notion request failed: {exc}") from exc
    return json.loads(body) if body else {}


class NotionClient:
    def __init__(self, token: str, sources_database_id: str, signal_intake_database_id: str, transport: NotionTransport = urllib_notion_transport):
        self.token = token
        self.sources_database_id = sources_database_id
        self.signal_intake_database_id = signal_intake_database_id
        self.transport = transport

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    def query_database(self, database_id: str) -> list[dict[str, Any]]:
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        payload: dict[str, Any] = {"page_size": 100}
        records: list[dict[str, Any]] = []
        while True:
            response = self.transport(url, self.headers, payload, "POST")
            results = response.get("results")
            if not isinstance(results, list):
                raise SourceCollectorError("Notion query response is missing results")
            records.extend(notion_page_to_record(page) for page in results if isinstance(page, dict))
            if response.get("has_more") is not True:
                return records
            cursor = response.get("next_cursor")
            if not cursor:
                raise SourceCollectorError("Notion query response is missing next_cursor")
            payload = {"page_size": 100, "start_cursor": cursor}

    def list_sources(self) -> list[dict[str, Any]]:
        return self.query_database(self.sources_database_id)

    def list_signal_intake(self) -> list[dict[str, Any]]:
        return self.query_database(self.signal_intake_database_id)

    def create_signal_intake_row(self, candidate: dict[str, Any]) -> None:
        payload = {
            "parent": {"database_id": self.signal_intake_database_id},
            "properties": notion_candidate_properties(candidate, supported_properties=self.signal_intake_property_names()),
        }
        self.transport("https://api.notion.com/v1/pages", self.headers, payload, "POST")

    def signal_intake_property_names(self) -> set[str]:
        response = self.transport(f"https://api.notion.com/v1/databases/{self.signal_intake_database_id}", self.headers, None, "GET")
        properties = response.get("properties")
        if not isinstance(properties, dict):
            return set()
        return {str(name) for name in properties}

    def update_source_fetch_status(self, source: SourceRecord, fetched_at: str, success: bool, error: str = "") -> None:
        if not source.notion_page_id:
            return
        properties: dict[str, Any] = {
            "Last Fetched At": {"date": {"start": fetched_at}},
            "Last Error": {"rich_text": [{"text": {"content": error[:1800]}}]},
        }
        if success:
            properties["Last Success At"] = {"date": {"start": fetched_at}}
        self.transport(f"https://api.notion.com/v1/pages/{source.notion_page_id}", self.headers, {"properties": properties}, "PATCH")


def notion_candidate_properties(candidate: dict[str, Any], supported_properties: set[str] | None = None) -> dict[str, Any]:
    def rich(value: Any) -> dict[str, Any]:
        return {"rich_text": [{"text": {"content": normalize_text(value)[:1900]}}]}

    notes = normalize_text(candidate.get("Notes")) or f"Collector Version: {normalize_text(candidate.get('Collector Version') or 'source_collector_v1')}"
    properties = {
        "Signal Title": {"title": [{"text": {"content": normalize_text(candidate["Signal Title"])[:1900]}}]},
        "Source Name": rich(candidate["Source Name"]),
        "Source URL": {"url": normalize_text(candidate["Source URL"])},
        "Published Date": {"date": {"start": candidate["Published Date"]}} if candidate.get("Published Date") else {"date": None},
        "Category": {"select": {"name": normalize_text(candidate["Category"])}},
        "AGI Relevance": {"select": {"name": normalize_text(candidate["AGI Relevance"])}},
        "Summary": rich(candidate["Summary"]),
        "Why It Matters": rich(candidate["Why It Matters"]),
        "Evidence": rich(candidate["Evidence"]),
        "Risk / Safety Notes": rich(candidate["Risk / Safety Notes"]),
        "Attribution Status": {"select": {"name": normalize_text(candidate["Attribution Status"])}},
        "Copyright Status": {"select": {"name": normalize_text(candidate["Copyright Status"])}},
        "Quality Hint": {"number": candidate["Quality Hint"]},
        "Status": {"select": {"name": normalize_text(candidate["Status"])}},
        "Ready for Pipeline": {"checkbox": bool(candidate["Ready for Pipeline"])},
        "Published": {"checkbox": bool(candidate["Published"])},
        "Notes": rich(notes),
    }
    if supported_properties and "Source Priority" in supported_properties and normalize_text(candidate.get("Source Priority")):
        properties["Source Priority"] = {"select": {"name": normalize_text(candidate["Source Priority"])}}
    return properties


def build_candidates(
    source_records: list[dict[str, Any]],
    existing_signal_intake: list[dict[str, Any]],
    fetch: FetchTransport = fetch_url,
) -> dict[str, Any]:
    sources = [source_from_record(record) for record in source_records]
    collected_candidates: list[dict[str, Any]] = []
    source_results: list[dict[str, Any]] = []
    for source in sources:
        if not eligible_source(source):
            source_results.append(
                {
                    "source": source.name,
                    "source_url": source.url,
                    "status": "skipped",
                    "reason": skip_source_reason(source),
                    "raw_items_seen": 0,
                    "candidates_built": 0,
                }
            )
            continue
        try:
            collected = collect_source_items(source, fetch=fetch)
            candidates = [candidate_from_item(item) for item in collected.items]
            collected_candidates.extend(candidates)
            result = {
                "source": source.name,
                "source_url": source.url,
                "status": "collected",
                "fetched_url": collected.fetched_url,
                "raw_items_seen": len(collected.items),
                "items": len(collected.items),
                "candidates_built": len(candidates),
            }
            if collected.fallback_used:
                result["fallback_used"] = True
                result["fallback_reason"] = collected.fallback_reason
                result["recommended_source_url"] = collected.fetched_url
            source_results.append(result)
        except SourceCollectorError as exc:
            source_results.append(
                {
                    "source": source.name,
                    "source_url": source.url,
                    "status": "error",
                    "error": str(exc),
                    "raw_items_seen": 0,
                    "candidates_built": 0,
                }
            )
    deduped, duplicates_skipped, skipped_candidates, skipped_by_reason = dedupe_candidates(collected_candidates, existing_signal_intake)
    raw_items_seen = len(collected_candidates)
    new_candidates_created = len(deduped)
    return {
        "collector_version": "source_collector_v1",
        "candidates": deduped,
        "candidate_count": new_candidates_created,
        "duplicates_skipped": duplicates_skipped,
        "raw_items_seen": raw_items_seen,
        "new_candidates_created": new_candidates_created,
        "freshness_diagnostic": freshness_diagnostic(raw_items_seen, new_candidates_created, duplicates_skipped),
        "skipped_candidates": skipped_candidates,
        "skipped_by_reason": skipped_by_reason,
        "sources_seen": len(source_records),
        "sources_fetched": sum(1 for item in source_results if item.get("status") == "collected"),
        "sources_failed": sum(1 for item in source_results if item.get("status") == "error"),
        "source_results": source_results,
        "openai_call_performed": OPENAI_CALL_PERFORMED,
        "source_page_body_scraping_performed": SOURCE_PAGE_BODY_SCRAPING_PERFORMED,
        "public_static_files_written": PUBLIC_STATIC_FILES_WRITTEN,
    }


def load_json_records(path: pathlib.Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("records"), list):
        return [item for item in data["records"] if isinstance(item, dict)]
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    raise SourceCollectorError(f"{path} must contain a list or records array")


def fixture_fetcher(mapping: dict[str, pathlib.Path]) -> FetchTransport:
    def fetch(url: str) -> str:
        path = mapping.get(url)
        if not path:
            raise SourceCollectorError(f"missing fixture for URL: {url}")
        return path.read_text(encoding="utf-8")

    return fetch


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect DysonX source metadata into Signal Intake candidates.")
    parser.add_argument("--sources-fixture", help="Offline source registry fixture JSON.")
    parser.add_argument("--existing-signal-intake-fixture", help="Offline existing Signal Intake fixture JSON.")
    parser.add_argument("--fetch-fixture-map", help="JSON object mapping source URL to local fixture path.")
    parser.add_argument("--output-candidates", help="Optional offline candidate report path.")
    parser.add_argument("--dry-run", action="store_true", help="Do not write Notion rows.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.sources_fixture:
            sources = load_json_records(pathlib.Path(args.sources_fixture))
            existing = load_json_records(pathlib.Path(args.existing_signal_intake_fixture)) if args.existing_signal_intake_fixture else []
            fetch_map = {}
            if args.fetch_fixture_map:
                raw_map = json.loads(pathlib.Path(args.fetch_fixture_map).read_text(encoding="utf-8"))
                fetch_map = {url: pathlib.Path(path) for url, path in raw_map.items()}
            result = build_candidates(sources, existing, fetch=fixture_fetcher(fetch_map) if fetch_map else fetch_url)
        else:
            missing = [
                name
                for name in (NOTION_TOKEN_ENV, SOURCES_DATABASE_ENV, SIGNAL_INTAKE_DATABASE_ENV)
                if not os.environ.get(name)
            ]
            if missing:
                raise SourceCollectorError(f"Missing required environment variables: {', '.join(missing)}")
            client = NotionClient(
                token=os.environ[NOTION_TOKEN_ENV],
                sources_database_id=os.environ[SOURCES_DATABASE_ENV],
                signal_intake_database_id=os.environ[SIGNAL_INTAKE_DATABASE_ENV],
            )
            sources = client.list_sources()
            existing = client.list_signal_intake()
            result = build_candidates(sources, existing)
            if not args.dry_run:
                for candidate in result["candidates"]:
                    client.create_signal_intake_row(candidate)

        if args.output_candidates:
            output_path = pathlib.Path(args.output_candidates)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(
            "[source-collector-v1] PASS "
            f"candidates={result['candidate_count']} duplicates_skipped={result['duplicates_skipped']} "
            f"raw_items_seen={result['raw_items_seen']} sources_fetched={result['sources_fetched']} "
            f"sources_failed={result['sources_failed']} "
            "openai_call_performed=False public_static_files_written=False"
        )
        return 0
    except (OSError, json.JSONDecodeError, SourceCollectorError) as exc:
        print(f"[source-collector-v1] failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
