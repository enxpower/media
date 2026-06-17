#!/usr/bin/env python3
"""DysonX IntelligenceSignal V1 data structure."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntelligenceSignalV1:
    signal_id: str
    title: str
    source_id: str
    source_name: str
    signal_type: str
    importance: str
    confidence: float
    summary: str
    key_points: tuple[str, ...]
    affected_entities: tuple[str, ...]
    impact_horizon: str
    tags: tuple[str, ...]
    created_at: str
