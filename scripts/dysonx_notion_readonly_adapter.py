#!/usr/bin/env python3
"""Read-only Notion source adapter interface for DysonX V1.

This module defines an adapter protocol and a fixture-backed fake client for
tests. It does not connect to the real Notion API, read environment variables,
perform network I/O, write Notion data, run collectors, call LLM APIs, or
publish pages.
"""

from __future__ import annotations

import pathlib
from typing import Any, Protocol

from dysonx_source_config_loader import load_source_records_from_fixture


class ReadOnlyNotionSourceAdapter(Protocol):
    """Read-only interface for retrieving Notion-shaped source records."""

    def list_source_records(self) -> list[dict[str, Any]]:
        """Return source records shaped like the V1 Notion source schema."""


class FakeNotionSourceClient:
    """Fixture-backed read-only source client for local tests."""

    def __init__(self, fixture_path: str | pathlib.Path):
        self.fixture_path = pathlib.Path(fixture_path)

    def list_source_records(self) -> list[dict[str, Any]]:
        return load_source_records_from_fixture(self.fixture_path)


def list_source_records(adapter: ReadOnlyNotionSourceAdapter) -> list[dict[str, Any]]:
    return adapter.list_source_records()
