#!/usr/bin/env python3
"""DysonX Publish Eligibility V1.

Converts ranked Intelligence Signals into deterministic pre-publishing
eligibility decisions. This module does not publish pages, post to social
platforms, call real LLM providers, or write to external systems.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from dysonx_quality_review import QualityReviewV1, review_ranked_signal, serialize_review


@dataclass(frozen=True)
class PublishEligibilityV1:
    signal_id: str
    eligible: bool
    eligibility_status: str
    reasons: tuple[str, ...]
    required_manual_review: bool
    created_at: str


def load_ranking_report(path: str | pathlib.Path) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Ranking report must be a JSON object")
    if not isinstance(data.get("ranked_signals"), list):
        raise ValueError("Ranking report must contain ranked_signals")
    return data


def eligibility_from_review(review: QualityReviewV1) -> PublishEligibilityV1:
    eligible = review.decision == "publish_ready"
    required_manual_review = review.decision == "needs_review"
    return PublishEligibilityV1(
        signal_id=review.signal_id,
        eligible=eligible,
        eligibility_status=review.decision,
        reasons=review.reasons,
        required_manual_review=required_manual_review,
        created_at=review.created_at,
    )


def serialize_eligibility(eligibility: PublishEligibilityV1) -> dict[str, Any]:
    data = asdict(eligibility)
    data["reasons"] = list(eligibility.reasons)
    return data


def run_quality_review(ranking_report: dict[str, Any], created_at: str | None = None) -> dict[str, Any]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    ranking_id = str(ranking_report.get("ranking_id") or "unknown_ranking")
    ranked_signals = ranking_report["ranked_signals"]

    reviews = [review_ranked_signal(item, ranking_id=ranking_id, created_at=timestamp) for item in ranked_signals]
    eligibilities = [eligibility_from_review(review) for review in reviews]

    status_counts: dict[str, int] = {"publish_ready": 0, "needs_review": 0, "rejected": 0}
    for review in reviews:
        status_counts[review.status] = status_counts.get(review.status, 0) + 1

    return {
        "generated_at": timestamp,
        "ranking_id": ranking_id,
        "signals_reviewed": len(reviews),
        "status_counts": status_counts,
        "reviews": [serialize_review(review) for review in reviews],
        "eligibilities": [serialize_eligibility(eligibility) for eligibility in eligibilities],
        "ranking_report": ranking_report,
        "publishing_performed": False,
        "social_posting_performed": False,
        "real_llm_api_used": False,
        "network_requests_performed": False,
    }


def write_report(report: dict[str, Any], output_path: str | pathlib.Path) -> None:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Quality Review Gate V1.")
    parser.add_argument("--ranking-report", required=True, help="Path to Signal Ranking report JSON.")
    parser.add_argument("--output", required=True, help="Path to write quality review report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ranking_report = load_ranking_report(args.ranking_report)
    report = run_quality_review(ranking_report)
    write_report(report, args.output)
    print(
        "[quality-review] wrote report: "
        f"{args.output} reviewed={report['signals_reviewed']} "
        f"publish_ready={report['status_counts'].get('publish_ready', 0)} "
        f"needs_review={report['status_counts'].get('needs_review', 0)} "
        f"rejected={report['status_counts'].get('rejected', 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
