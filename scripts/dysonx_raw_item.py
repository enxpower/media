#!/usr/bin/env python3
"""DysonX RawItem and SignalCandidate V1 data structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RawItemV1:
    source_id: str
    source_name: str
    title: str
    url: str
    published_at: str
    language: str
    collected_at: str
    raw_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SignalCandidateV1:
    candidate_id: str
    title: str
    source_id: str
    source_name: str
    url: str
    candidate_type: str
    entities: tuple[str, ...]
    tags: tuple[str, ...]
    status: str
    confidence: float
    created_at: str
