#!/usr/bin/env python3
"""DysonX provider-neutral LLM job structures V1."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LLMJobV1:
    job_id: str
    candidate_id: str
    provider: str
    model: str
    prompt_template_version: str
    status: str
    created_at: str


@dataclass(frozen=True)
class ModelRunV1:
    run_id: str
    job_id: str
    provider: str
    model: str
    latency_ms: int
    token_counts: dict[str, int] = field(default_factory=dict)
    status: str = "completed"


@dataclass(frozen=True)
class OutputValidationV1:
    validation_id: str
    run_id: str
    passed: bool
    warnings: tuple[str, ...]
    validation_rules: tuple[str, ...]


@dataclass(frozen=True)
class AuditRecordV1:
    audit_id: str
    job_id: str
    run_id: str
    validation_id: str
    created_at: str
