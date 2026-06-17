#!/usr/bin/env python3
"""Local DysonX V1 source config fixture loader.

This module loads source records from local JSON fixtures only. It validates
records against the V1 Notion source schema and converts eligible records into
Source objects. It does not connect to Notion, perform network I/O, run
collectors, call LLM APIs, or publish pages.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

from dysonx_notion_source_schema import is_collection_eligible, validate_notion_source_record
from dysonx_schema import Source


@dataclass(frozen=True)
class SourceConfigLoadResult:
    sources: tuple[Source, ...]
    rejected_records: tuple[dict[str, Any], ...]
    validation_errors: dict[str, tuple[str, ...]]


def load_source_records_from_fixture(path: str | pathlib.Path) -> list[dict[str, Any]]:
    fixture_path = pathlib.Path(path)
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Source fixture must contain a list of records")
    if not all(isinstance(record, dict) for record in data):
        raise ValueError("Every source fixture record must be an object")
    return data


def notion_record_to_source(record: dict[str, Any], index: int) -> Source:
    return Source(
        id=f"source_fixture_{index}",
        notion_page_id=f"fixture_{index}",
        name=str(record["Name"]),
        source_type=str(record["Source Type"]),
        url=str(record["URL"]),
        authority_score=float(record["Authority Score"]),
        enabled=bool(record["Enabled"]),
        platform=str(record["Platform"]),
        language=str(record["Language"]),
        region=str(record["Region"]),
        priority=str(record["Priority"]),
        notes=str(record.get("Notes") or ""),
    )


def load_sources_from_fixture(path: str | pathlib.Path) -> SourceConfigLoadResult:
    records = load_source_records_from_fixture(path)
    return load_sources_from_records(records)


def load_sources_from_records(records: list[dict[str, Any]]) -> SourceConfigLoadResult:
    sources: list[Source] = []
    rejected_records: list[dict[str, Any]] = []
    validation_errors: dict[str, tuple[str, ...]] = {}

    for index, record in enumerate(records):
        record_id = str(record.get("Name") or f"record_{index}")
        errors = validate_notion_source_record(record)

        if record.get("Enabled") is not True:
            errors = [*errors, "Enabled must be true for collection eligibility"]

        if errors:
            rejected_records.append(record)
            validation_errors[record_id] = tuple(errors)
            continue

        if not is_collection_eligible(record):
            rejected_records.append(record)
            validation_errors[record_id] = ("Record is not collection-eligible",)
            continue

        sources.append(notion_record_to_source(record, index))

    return SourceConfigLoadResult(
        sources=tuple(sources),
        rejected_records=tuple(rejected_records),
        validation_errors=validation_errors,
    )
