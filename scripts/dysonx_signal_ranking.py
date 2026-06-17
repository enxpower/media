#!/usr/bin/env python3
"""DysonX Signal Ranking Engine V1.

Ranks IntelligenceSignal records for decision priority. V1 uses deterministic
scoring only. It does not call LLM APIs, publish, post to social platforms,
write graph data, or implement prediction features.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any

from dysonx_signal_scoring import SCORING_VERSION, SignalScoreV1, parse_timestamp, score_signal, serialize_score


@dataclass(frozen=True)
class RankingResultV1:
    ranking_id: str
    ranked_signals: tuple[dict[str, Any], ...]
    top_n: int
    scoring_version: str
    created_at: str
    audit_summary: dict[str, Any]


def load_intelligence_report(path: str | pathlib.Path) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Intelligence report must be a JSON object")
    if not isinstance(data.get("signals"), list):
        raise ValueError("Intelligence report must contain a signals list")
    return data


def reference_time_for_signals(signals: list[dict[str, Any]]) -> datetime | None:
    timestamps = [parse_timestamp(signal.get("created_at")) for signal in signals]
    valid_timestamps = [timestamp for timestamp in timestamps if timestamp is not None]
    if not valid_timestamps:
        return None
    return max(valid_timestamps)


def sort_ranked_signals(ranked_signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        ranked_signals,
        key=lambda item: (
            -float(item["score"]["composite_score"]),
            -float(item["score"]["importance_score"]),
            -float(item["score"]["confidence_score"]),
            str(item["signal"].get("signal_id", "")),
        ),
    )


def ranking_id_for(created_at: str, scores: list[SignalScoreV1]) -> str:
    seed = "|".join([created_at, *[score.signal_id for score in scores]])
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"ranking_{digest[:16]}"


def rank_signals(signals: list[dict[str, Any]], top_n: int, created_at: str | None = None) -> RankingResultV1:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    reference_time = reference_time_for_signals(signals)
    scored = [score_signal(signal, reference_time=reference_time, created_at=timestamp) for signal in signals]
    ranked = sort_ranked_signals(
        [
            {
                "rank": 0,
                "signal": signal,
                "score": serialize_score(score),
            }
            for signal, score in zip(signals, scored, strict=True)
        ]
    )

    limited = ranked[: max(0, top_n)]
    for index, item in enumerate(limited, start=1):
        item["rank"] = index

    audit_summary = {
        "signals_seen": len(signals),
        "signals_ranked": len(ranked),
        "top_n": top_n,
        "returned": len(limited),
        "scoring_version": SCORING_VERSION,
        "llm_used": False,
        "publishing_performed": False,
        "social_posting_performed": False,
        "invalid_or_missing_fields_handled": any(
            any("missing or invalid" in reason for reason in score.scoring_reasons) for score in scored
        ),
    }

    return RankingResultV1(
        ranking_id=ranking_id_for(timestamp, scored),
        ranked_signals=tuple(limited),
        top_n=top_n,
        scoring_version=SCORING_VERSION,
        created_at=timestamp,
        audit_summary=audit_summary,
    )


def ranking_result_to_report(result: RankingResultV1) -> dict[str, Any]:
    return {
        **asdict(result),
        "ranked_signals": list(result.ranked_signals),
        "real_llm_api_used": False,
        "network_requests_performed": False,
        "publishing_performed": False,
        "social_posting_performed": False,
    }


def write_report(report: dict[str, Any], output_path: str | pathlib.Path) -> None:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Signal Ranking Engine V1.")
    parser.add_argument("--intelligence-report", required=True, help="Path to LLM audit/intelligence report JSON.")
    parser.add_argument("--output", required=True, help="Path to write signal ranking audit report JSON.")
    parser.add_argument("--top-n", type=int, default=10, help="Number of ranked signals to return.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    intelligence_report = load_intelligence_report(args.intelligence_report)
    result = rank_signals(intelligence_report["signals"], top_n=args.top_n)
    report = ranking_result_to_report(result)
    write_report(report, args.output)
    print(
        "[signal-ranking] wrote report: "
        f"{args.output} ranked={report['audit_summary']['returned']} top_n={args.top_n}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
