#!/usr/bin/env python3
"""JSON persistence for DysonX RawItem collection V1."""

from __future__ import annotations

import json
import pathlib
from typing import Any


STORE_VERSION = "dysonx_raw_items_store_v1"


def build_raw_item_store(
    raw_items: list[dict[str, Any]],
    collection_metadata: dict[str, Any],
    deduplication_results: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "raw_items": raw_items,
        "collection_metadata": collection_metadata,
        "deduplication_results": deduplication_results,
    }


def write_raw_item_store(
    output_path: str | pathlib.Path,
    raw_items: list[dict[str, Any]],
    collection_metadata: dict[str, Any],
    deduplication_results: list[dict[str, Any]],
) -> dict[str, Any]:
    document = build_raw_item_store(raw_items, collection_metadata, deduplication_results)
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return document


def read_raw_item_store(path: str | pathlib.Path) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("DysonX raw item store must be a JSON object")
    metadata = data.get("collection_metadata")
    if not isinstance(metadata, dict) or metadata.get("store_version") != STORE_VERSION:
        raise ValueError("Unsupported DysonX raw item store version")
    return data
