#!/usr/bin/env python3
"""DysonX V1 Notion source schema mapping and validation.

This module is schema-only. It does not import Notion clients, call network
APIs, fetch source records, collect content, call LLM APIs, or publish pages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


NotionPropertyType = Literal["title", "select", "url", "number", "multi_select", "checkbox", "date", "rich_text"]


ALLOWED_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        "Official Company Blog",
        "Research Lab",
        "Paper",
        "GitHub Repository",
        "Government",
        "Regulatory",
        "Product Changelog",
        "Key Person",
        "Conference",
        "High Authority Media",
        "Manual",
    }
)

ALLOWED_PLATFORMS: frozenset[str] = frozenset(
    {
        "Website",
        "RSS",
        "GitHub",
        "Paper Repository",
        "Government Site",
        "Social",
        "Manual",
    }
)

ALLOWED_PRIORITIES: frozenset[str] = frozenset({"Critical", "High", "Medium", "Low"})
ALLOWED_LANGUAGES: frozenset[str] = frozenset({"English", "Chinese", "Multilingual", "Other"})
ALLOWED_REGIONS: frozenset[str] = frozenset({"Global", "US", "China", "EU", "UK", "Japan", "Other"})

AUTHORITY_SCORE_MIN = 0
AUTHORITY_SCORE_MAX = 100
FETCH_FREQUENCY_MIN_MINUTES = 15
FETCH_FREQUENCY_MAX_MINUTES = 10080


@dataclass(frozen=True)
class NotionSourceField:
    name: str
    property_type: NotionPropertyType
    required: bool
    description: str


NOTION_SOURCE_FIELDS: tuple[NotionSourceField, ...] = (
    NotionSourceField("Name", "title", True, "Human-readable source name."),
    NotionSourceField("Source Type", "select", True, "Kind of source for future collector selection."),
    NotionSourceField("URL", "url", True, "Canonical source URL or entry point."),
    NotionSourceField("Platform", "select", True, "Platform where the source lives."),
    NotionSourceField("Priority", "select", True, "Future collection priority."),
    NotionSourceField("Authority Score", "number", True, "Source authority score from 0 to 100."),
    NotionSourceField("Language", "select", True, "Default language for source material."),
    NotionSourceField("Region", "select", True, "Geographic or policy region."),
    NotionSourceField("Topic Tags", "multi_select", False, "Lightweight categorization hints."),
    NotionSourceField("Related Entities", "multi_select", False, "Optional entity hints, not Knowledge Graph records."),
    NotionSourceField("Enabled", "checkbox", True, "Collection eligibility flag."),
    NotionSourceField("Fetch Frequency", "number", True, "Future collection cadence in minutes."),
    NotionSourceField("Last Fetched At", "date", False, "Future collection attempt timestamp."),
    NotionSourceField("Last Success At", "date", False, "Future successful collection timestamp."),
    NotionSourceField("Last Error", "rich_text", False, "Future validation or collection error details."),
    NotionSourceField("Notes", "rich_text", False, "Human review notes."),
)


def notion_source_field_names() -> tuple[str, ...]:
    return tuple(field.name for field in NOTION_SOURCE_FIELDS)


def required_notion_source_field_names() -> frozenset[str]:
    return frozenset(field.name for field in NOTION_SOURCE_FIELDS if field.required)


def notion_source_schema_by_name() -> dict[str, NotionSourceField]:
    return {field.name: field for field in NOTION_SOURCE_FIELDS}


def validate_notion_source_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for field_name in required_notion_source_field_names():
        value = record.get(field_name)
        if value is None or value == "":
            errors.append(f"{field_name} is required")

    source_type = record.get("Source Type")
    if source_type is not None and source_type != "" and source_type not in ALLOWED_SOURCE_TYPES:
        errors.append("Source Type is invalid")

    platform = record.get("Platform")
    if platform is not None and platform != "" and platform not in ALLOWED_PLATFORMS:
        errors.append("Platform is invalid")

    priority = record.get("Priority")
    if priority is not None and priority != "" and priority not in ALLOWED_PRIORITIES:
        errors.append("Priority is invalid")

    language = record.get("Language")
    if language is not None and language != "" and language not in ALLOWED_LANGUAGES:
        errors.append("Language is invalid")

    region = record.get("Region")
    if region is not None and region != "" and region not in ALLOWED_REGIONS:
        errors.append("Region is invalid")

    authority_score = record.get("Authority Score")
    if authority_score is not None and authority_score != "":
        if not isinstance(authority_score, (int, float)):
            errors.append("Authority Score must be numeric")
        elif not AUTHORITY_SCORE_MIN <= authority_score <= AUTHORITY_SCORE_MAX:
            errors.append("Authority Score must be between 0 and 100")

    fetch_frequency = record.get("Fetch Frequency")
    if fetch_frequency is not None and fetch_frequency != "":
        if not isinstance(fetch_frequency, (int, float)):
            errors.append("Fetch Frequency must be numeric")
        elif not FETCH_FREQUENCY_MIN_MINUTES <= fetch_frequency <= FETCH_FREQUENCY_MAX_MINUTES:
            errors.append("Fetch Frequency must be between 15 and 10080 minutes")

    enabled = record.get("Enabled")
    if enabled is not None and not isinstance(enabled, bool):
        errors.append("Enabled must be a boolean")

    return errors


def is_collection_eligible(record: dict[str, Any]) -> bool:
    if record.get("Enabled") is not True:
        return False
    return not validate_notion_source_record(record)
