#!/usr/bin/env python3
"""Read-only Notion source adapter interface for DysonX V1.

This module defines read-only adapters for Notion-shaped source records. The
real client only queries a configured Notion database. It never writes,
updates, creates, deletes, runs collectors, calls LLM APIs, or publishes pages.
"""

from __future__ import annotations

import json
import pathlib
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Protocol

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


class NotionReadOnlyFetchError(RuntimeError):
    """Raised when a read-only Notion query fails."""


NotionTransport = Callable[[str, dict[str, str], dict[str, Any]], dict[str, Any]]


def _plain_text(items: list[dict[str, Any]] | None) -> str:
    if not items:
        return ""
    return "".join(str(item.get("plain_text") or "") for item in items)


def _notion_property_value(property_value: dict[str, Any]) -> Any:
    property_type = property_value.get("type")
    if property_type == "title":
        return _plain_text(property_value.get("title"))
    if property_type == "rich_text":
        return _plain_text(property_value.get("rich_text"))
    if property_type == "select":
        selected = property_value.get("select")
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
        return date_value.get("start") if isinstance(date_value, dict) else None
    return None


def notion_page_to_source_record(page: dict[str, Any]) -> dict[str, Any]:
    properties = page.get("properties")
    if not isinstance(properties, dict):
        raise NotionReadOnlyFetchError("Notion page is missing properties")

    record = {
        field_name: _notion_property_value(property_value)
        for field_name, property_value in properties.items()
        if isinstance(property_value, dict)
    }
    record["_notion_page_id"] = str(page.get("id") or "")
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
        raise NotionReadOnlyFetchError(f"Notion read-only query failed: {exc}") from exc

    data = json.loads(response_body)
    if not isinstance(data, dict):
        raise NotionReadOnlyFetchError("Notion read-only query returned a non-object response")
    return data


class NotionReadOnlySourceClient:
    """Read-only Notion database query client."""

    TOKEN_ENV = "NOTION_TOKEN"
    DATABASE_ID_ENV = "DYSONX_NOTION_SOURCES_DATABASE_ID"
    NOTION_VERSION = "2022-06-28"

    def __init__(
        self,
        token: str | None = None,
        database_id: str | None = None,
        transport: NotionTransport | None = None,
    ):
        self.token = token
        self.database_id = database_id
        self.transport = transport or urllib_notion_transport

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
        assert self.token is not None
        assert self.database_id is not None

        url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": self.NOTION_VERSION,
        }
        records: list[dict[str, Any]] = []
        payload: dict[str, Any] = {"page_size": 100}

        while True:
            response = self.transport(url, headers, payload)
            results = response.get("results")
            if not isinstance(results, list):
                raise NotionReadOnlyFetchError("Notion read-only query response is missing results")
            records.extend(notion_page_to_source_record(page) for page in results if isinstance(page, dict))

            if response.get("has_more") is not True:
                break
            next_cursor = response.get("next_cursor")
            if not next_cursor:
                raise NotionReadOnlyFetchError("Notion read-only query response is missing next_cursor")
            payload = {"page_size": 100, "start_cursor": next_cursor}

        return records


def list_source_records(adapter: ReadOnlyNotionSourceAdapter) -> list[dict[str, Any]]:
    return adapter.list_source_records()
