#!/usr/bin/env python3
"""JSON persistence for DysonX Notion source sync V1.

Stores only source configuration, sync metadata, and validation results. It does
not store raw content, LLM output, publish packages, social posts, graph data,
or prediction data.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any


STORE_VERSION = "dysonx_source_sync_store_v1"


def build_store_document(
    sources: list[dict[str, Any]],
    sync_metadata: dict[str, Any],
    validation_results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "sources": sources,
        "sync_metadata": sync_metadata,
        "validation_results": validation_results,
    }


def write_source_sync_store(
    output_path: str | pathlib.Path,
    sources: list[dict[str, Any]],
    sync_metadata: dict[str, Any],
    validation_results: list[dict[str, Any]],
) -> dict[str, Any]:
    document = build_store_document(sources, sync_metadata, validation_results)
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return document


def read_source_sync_store(path: str | pathlib.Path) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("DysonX source sync store must be a JSON object")
    sync_metadata = data.get("sync_metadata")
    if not isinstance(sync_metadata, dict) or sync_metadata.get("store_version") != STORE_VERSION:
        raise ValueError("Unsupported DysonX source sync store version")
    return data
