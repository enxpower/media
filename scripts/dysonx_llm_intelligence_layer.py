#!/usr/bin/env python3
"""DysonX LLM Intelligence Layer V1.

Transforms SignalCandidate records into structured IntelligenceSignal records
through a provider abstraction. V1 ships only a deterministic fake provider: it
does not call real LLM APIs, perform network requests, publish pages, or create
social posts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Protocol

from dysonx_intelligence_signal import IntelligenceSignalV1
from dysonx_raw_item import SignalCandidateV1
import dysonx_signal_candidate_pipeline as candidate_pipeline


SUPPORTED_FUTURE_PROVIDER_FAMILIES = ("openai", "anthropic", "gemini", "local")


class LLMProvider(Protocol):
    provider_name: str

    def analyze_candidate(self, candidate: SignalCandidateV1) -> dict[str, Any]:
        """Return structured intelligence fields for one SignalCandidate."""


class FakeLLMProvider:
    """Deterministic provider for V1 tests and audit reports."""

    provider_name = "fake"

    def analyze_candidate(self, candidate: SignalCandidateV1) -> dict[str, Any]:
        importance = importance_for_candidate_type(candidate.candidate_type)
        impact_horizon = impact_horizon_for_candidate_type(candidate.candidate_type)
        confidence = min(0.95, round(candidate.confidence + 0.2, 2))
        entity_text = ", ".join(candidate.entities) if candidate.entities else "the tracked AI ecosystem"

        return {
            "title": f"Intelligence Signal: {candidate.title}",
            "signal_type": candidate.candidate_type,
            "importance": importance,
            "confidence": confidence,
            "summary": (
                f"{candidate.title} is a {candidate.candidate_type.replace('_', ' ')} "
                f"signal involving {entity_text}."
            ),
            "key_points": (
                f"Source candidate type: {candidate.candidate_type}",
                f"Original source: {candidate.source_name}",
                "Provider output is deterministic fake analysis for V1.",
            ),
            "affected_entities": candidate.entities,
            "impact_horizon": impact_horizon,
            "tags": candidate.tags,
        }


def importance_for_candidate_type(candidate_type: str) -> str:
    importance = {
        "model_release": "high",
        "company_announcement": "medium",
        "research_update": "medium",
        "regulation": "high",
        "general_signal": "low",
    }
    return importance.get(candidate_type, "low")


def impact_horizon_for_candidate_type(candidate_type: str) -> str:
    horizons = {
        "model_release": "near_term",
        "company_announcement": "near_term",
        "research_update": "mid_term",
        "regulation": "mid_term",
        "general_signal": "unknown",
    }
    return horizons.get(candidate_type, "unknown")


def signal_id_for_candidate(candidate: SignalCandidateV1) -> str:
    digest = hashlib.sha256(f"{candidate.candidate_id}|{candidate.url}|{candidate.title}".encode("utf-8")).hexdigest()
    return f"signal_{digest[:16]}"


def candidate_from_record(record: dict[str, Any]) -> SignalCandidateV1:
    required_fields = (
        "candidate_id",
        "title",
        "source_id",
        "source_name",
        "url",
        "candidate_type",
        "entities",
        "tags",
        "status",
        "confidence",
        "created_at",
    )
    missing = [field for field in required_fields if field not in record]
    if missing:
        raise ValueError(f"SignalCandidate record missing fields: {', '.join(missing)}")

    return SignalCandidateV1(
        candidate_id=str(record["candidate_id"]),
        title=str(record["title"]),
        source_id=str(record["source_id"]),
        source_name=str(record["source_name"]),
        url=str(record["url"]),
        candidate_type=str(record["candidate_type"]),
        entities=tuple(str(entity) for entity in record.get("entities", ())),
        tags=tuple(str(tag) for tag in record.get("tags", ())),
        status=str(record["status"]),
        confidence=float(record["confidence"]),
        created_at=str(record["created_at"]),
    )


def create_intelligence_signal(
    candidate: SignalCandidateV1,
    provider: LLMProvider,
    created_at: str,
) -> IntelligenceSignalV1:
    analysis = provider.analyze_candidate(candidate)
    return IntelligenceSignalV1(
        signal_id=signal_id_for_candidate(candidate),
        title=str(analysis["title"]),
        source_id=candidate.source_id,
        source_name=candidate.source_name,
        signal_type=str(analysis["signal_type"]),
        importance=str(analysis["importance"]),
        confidence=float(analysis["confidence"]),
        summary=str(analysis["summary"]),
        key_points=tuple(str(point) for point in analysis["key_points"]),
        affected_entities=tuple(str(entity) for entity in analysis["affected_entities"]),
        impact_horizon=str(analysis["impact_horizon"]),
        tags=tuple(str(tag) for tag in analysis["tags"]),
        created_at=created_at,
    )


def run_intelligence_layer(
    candidates: list[SignalCandidateV1],
    provider: LLMProvider | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    llm_provider = provider or FakeLLMProvider()
    signals = [create_intelligence_signal(candidate, llm_provider, timestamp) for candidate in candidates]

    confidence_distribution = {"low": 0, "medium": 0, "high": 0}
    importance_distribution: dict[str, int] = {}
    warnings: list[str] = []

    for signal in signals:
        if signal.confidence < 0.5:
            confidence_distribution["low"] += 1
        elif signal.confidence < 0.75:
            confidence_distribution["medium"] += 1
        else:
            confidence_distribution["high"] += 1
        importance_distribution[signal.importance] = importance_distribution.get(signal.importance, 0) + 1
        if not signal.affected_entities:
            warnings.append(f"{signal.signal_id} has no affected entities")

    return {
        "generated_at": timestamp,
        "provider": llm_provider.provider_name,
        "provider_mode": "fake_only",
        "future_provider_families": list(SUPPORTED_FUTURE_PROVIDER_FAMILIES),
        "candidates_processed": len(candidates),
        "signals_generated": len(signals),
        "confidence_distribution": confidence_distribution,
        "importance_distribution": importance_distribution,
        "signals": [
            {
                **asdict(signal),
                "key_points": list(signal.key_points),
                "affected_entities": list(signal.affected_entities),
                "tags": list(signal.tags),
            }
            for signal in signals
        ],
        "warnings": warnings,
        "real_llm_api_used": False,
        "network_requests_performed": False,
        "publishing_performed": False,
    }


def load_candidates_from_candidate_report(path: str | pathlib.Path) -> list[SignalCandidateV1]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    records = data.get("candidates")
    if not isinstance(records, list):
        raise ValueError("Candidate report must contain a candidates list")
    return [candidate_from_record(record) for record in records]


def load_candidates_from_raw_fixture(path: str | pathlib.Path) -> list[SignalCandidateV1]:
    records = candidate_pipeline.load_raw_item_records(path)
    candidate_report = candidate_pipeline.run_pipeline(records)
    return [candidate_from_record(record) for record in candidate_report["candidates"]]


def write_report(report: dict[str, Any], output_path: str | pathlib.Path) -> None:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX LLM Intelligence Layer V1 with FakeLLMProvider.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--candidate-report", help="Path to an existing SignalCandidate audit report JSON.")
    source.add_argument("--raw-fixture", help="Path to a RawItem fixture JSON to convert through the candidate layer first.")
    parser.add_argument("--output", required=True, help="Path to write intelligence signal audit report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.candidate_report:
        candidates = load_candidates_from_candidate_report(args.candidate_report)
    else:
        candidates = load_candidates_from_raw_fixture(args.raw_fixture)

    report = run_intelligence_layer(candidates, provider=FakeLLMProvider())
    write_report(report, args.output)
    print(
        "[llm-intelligence-layer] wrote report: "
        f"{args.output} signals={report['signals_generated']} provider={report['provider']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
