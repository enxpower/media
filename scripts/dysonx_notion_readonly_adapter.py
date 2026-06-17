#!/usr/bin/env python3
"""Read-only Notion source adapter interface for DysonX V1.

This module defines an adapter protocol and a fixture-backed fake client for
tests. It does not connect to the real Notion API, read environment variables,
perform network I/O, write Notion data, run collectors, call LLM APIs, or
publish pages.
"""

from __future__ import annotations

import pathlib
import os
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


class NotionReadOnlyAdapterNotConfigured(RuntimeError):
    """Raised when real Notion read-only intake is requested without config."""


class NotionReadOnlySourceClient:
    """Read-only Notion adapter skeleton.

    This class intentionally does not perform a real network fetch yet. It only
    validates that future read-only integration has the required configuration.
    """

    TOKEN_ENV = "NOTION_TOKEN"
    DATABASE_ID_ENV = "DYSONX_NOTION_SOURCES_DATABASE_ID"

    def __init__(self, token: str | None = None, database_id: str | None = None):
        self.token = token
        self.database_id = database_id

    @classmethod
    def from_env(cls) -> "NotionReadOnlySourceClient":
        return cls(
            token=os.environ.get(cls.TOKEN_ENV),
            database_id=os.environ.get(cls.DATABASE_ID_ENV),
        )

    def ensure_configured(self) -> None:
        missing = [
            env_name
            for env_name, value in (
                (self.TOKEN_ENV, self.token),
                (self.DATABASE_ID_ENV, self.database_id),
            )
            if not value
        ]
        if missing:
            joined = ", ".join(missing)
            raise NotionReadOnlyAdapterNotConfigured(f"Missing required Notion read-only env vars: {joined}")

    def list_source_records(self) -> list[dict[str, Any]]:
        self.ensure_configured()
        raise NotImplementedError("Real Notion read-only fetch is intentionally not implemented in V1 source intake.")


def list_source_records(adapter: ReadOnlyNotionSourceAdapter) -> list[dict[str, Any]]:
    return adapter.list_source_records()
