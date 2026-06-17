#!/usr/bin/env python3
"""DysonX Signal Candidate Pipeline V1.

Loads RawItem fixtures, applies deterministic pre-LLM normalization rules, and
writes a candidate audit report. It does not perform network requests, call LLM
APIs, publish pages, or implement graph/prediction features.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from dysonx_raw_item import RawItemV1, SignalCandidateV1


REQUIRED_RAW_ITEM_FIELDS = (
    "source_id",
    "source_name",
    "title",
    "url",
    "published_at",
    "language",
    "collected_at",
    "raw_content",
    "metadata",
)


def load_raw_item_records(path: str | pathlib.Path) -> list[dict[str, Any]]:
    fixture_path = pathlib.Path(path)
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Raw item fixture must contain a list of records")
    if not all(isinstance(record, dict) for record in data):
        raise ValueError("Every raw item fixture record must be an object")
    return data


def validate_raw_item_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field_name in REQUIRED_RAW_ITEM_FIELDS:
        if field_name not in record:
            errors.append(f"{field_name} is required")

    for field_name in ("source_id", "source_name", "title", "url", "language", "collected_at"):
        if record.get(field_name) in (None, ""):
            errors.append(f"{field_name} must be present")

    if "metadata" in record and not isinstance(record.get("metadata"), dict):
        errors.append("metadata must be an object")

    return errors


def raw_item_from_record(record: dict[str, Any]) -> RawItemV1:
    return RawItemV1(
        source_id=str(record["source_id"]),
        source_name=str(record["source_name"]),
        title=str(record["title"]),
        url=str(record["url"]),
        published_at=str(record.get("published_at") or ""),
        language=str(record["language"]),
        collected_at=str(record["collected_at"]),
        raw_content=str(record.get("raw_content") or ""),
        metadata=dict(record.get("metadata") or {}),
    )


def classify_candidate_type(raw_item: RawItemV1) -> str:
    text = f"{raw_item.title} {raw_item.raw_content}".lower()
    if "openai" in text and ("release" in text or "launch" in text):
        return "model_release"
    if "anthropic" in text and ("announce" in text or "announcement" in text):
        return "company_announcement"
    if "ai act" in text or "regulation" in text or "regulatory" in text:
        return "regulation"
    if "deepmind" in text or "research" in text or "paper" in text:
        return "research_update"
    return "general_signal"


def extract_entities(raw_item: RawItemV1) -> tuple[str, ...]:
    text = f"{raw_item.title} {raw_item.raw_content}".lower()
    entities = []
    for entity in ("OpenAI", "Anthropic", "Google DeepMind", "EU"):
        if entity.lower() in text:
            entities.append(entity)
    return tuple(entities)


def tags_for_candidate_type(candidate_type: str) -> tuple[str, ...]:
    tags = {
        "model_release": ("model", "release"),
        "company_announcement": ("company", "announcement"),
        "regulation": ("policy", "regulation"),
        "research_update": ("research", "technical"),
        "general_signal": ("signal",),
    }
    return tags[candidate_type]


def candidate_id_for_raw_item(raw_item: RawItemV1) -> str:
    digest = hashlib.sha256(f"{raw_item.source_id}|{raw_item.url}|{raw_item.title}".encode("utf-8")).hexdigest()
    return f"candidate_{digest[:16]}"


def create_signal_candidate(raw_item: RawItemV1, created_at: str) -> SignalCandidateV1:
    candidate_type = classify_candidate_type(raw_item)
    return SignalCandidateV1(
        candidate_id=candidate_id_for_raw_item(raw_item),
        title=raw_item.title,
        source_id=raw_item.source_id,
        source_name=raw_item.source_name,
        url=raw_item.url,
        candidate_type=candidate_type,
        entities=extract_entities(raw_item),
        tags=tags_for_candidate_type(candidate_type),
        status="candidate",
        confidence=0.55,
        created_at=created_at,
    )


def run_pipeline(records: list[dict[str, Any]], created_at: str | None = None) -> dict[str, Any]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    candidates: list[SignalCandidateV1] = []
    rejected_items: list[dict[str, Any]] = []
    processing_warnings: list[str] = []

    for index, record in enumerate(records):
        errors = validate_raw_item_record(record)
        if errors:
            rejected_items.append(
                {
                    "index": index,
                    "title": record.get("title", ""),
                    "errors": errors,
                }
            )
            continue

        raw_item = raw_item_from_record(record)
        candidate = create_signal_candidate(raw_item, created_at=timestamp)
        if candidate.candidate_type == "general_signal":
            processing_warnings.append(f"Raw item {index} used fallback candidate type")
        candidates.append(candidate)

    candidate_type_counts: dict[str, int] = {}
    for candidate in candidates:
        candidate_type_counts[candidate.candidate_type] = candidate_type_counts.get(candidate.candidate_type, 0) + 1

    return {
        "generated_at": timestamp,
        "total_raw_items": len(records),
        "candidates_created": len(candidates),
        "candidate_types": candidate_type_counts,
        "candidates": [
            {
                **asdict(candidate),
                "entities": list(candidate.entities),
                "tags": list(candidate.tags),
            }
            for candidate in candidates
        ],
        "rejected_items": rejected_items,
        "processing_warnings": processing_warnings,
        "llm_used": False,
        "network_requests_performed": False,
        "publishing_performed": False,
    }


def write_report(report: dict[str, Any], output_path: str | pathlib.Path) -> None:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Signal Candidate Pipeline V1.")
    parser.add_argument("--fixture", required=True, help="Path to raw item fixture JSON.")
    parser.add_argument("--output", required=True, help="Path to write signal candidate audit report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    records = load_raw_item_records(args.fixture)
    report = run_pipeline(records)
    write_report(report, args.output)
    print(
        "[signal-candidate-pipeline] wrote report: "
        f"{args.output} candidates={report['candidates_created']} rejected={len(report['rejected_items'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
