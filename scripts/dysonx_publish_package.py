#!/usr/bin/env python3
"""DysonX Publish Package V1.

Converts publish-ready Intelligence Signals into structured publish packages.
This is still pre-publishing: it writes only an audit JSON report and does not
generate website pages, post to social platforms, or write public content files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from dysonx_seo_metadata import build_seo_metadata, serialize_seo_metadata
from dysonx_social_draft import build_social_drafts, serialize_social_draft


CANONICAL_LANGUAGE = "en"
OPTIONAL_LOCALIZED_LANGUAGES = ("zh",)


@dataclass(frozen=True)
class PublishPackageV1:
    package_id: str
    signal_id: str
    title: str
    slug: str
    summary: str
    source_url: str
    source_name: str
    canonical_language: str
    localized_languages: tuple[str, ...]
    seo_metadata: dict[str, str]
    social_drafts: tuple[dict[str, str], ...]
    status: str
    created_at: str


def slugify(title: str) -> str:
    normalized = title.lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "untitled-signal"


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:16]}"


def load_quality_report(path: str | pathlib.Path) -> dict[str, Any]:
    data = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Quality report must be a JSON object")
    if not isinstance(data.get("reviews"), list):
        raise ValueError("Quality report must contain reviews")
    return data


def eligibility_status_by_signal(quality_report: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for eligibility in quality_report.get("eligibilities", []):
        if isinstance(eligibility, dict):
            statuses[str(eligibility.get("signal_id"))] = str(eligibility.get("eligibility_status"))
    return statuses


def signal_by_id_from_ranking_report(ranking_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    signals: dict[str, dict[str, Any]] = {}
    for ranked in ranking_report.get("ranked_signals", []):
        if isinstance(ranked, dict) and isinstance(ranked.get("signal"), dict):
            signal = ranked["signal"]
            signals[str(signal.get("signal_id"))] = signal
    return signals


def signal_by_id_from_quality_report(quality_report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    ranking_report = quality_report.get("ranking_report")
    if isinstance(ranking_report, dict):
        return signal_by_id_from_ranking_report(ranking_report)
    signals = quality_report.get("signals")
    if isinstance(signals, list):
        return {str(signal.get("signal_id")): signal for signal in signals if isinstance(signal, dict)}
    return {}


def create_publish_package(signal: dict[str, Any], created_at: str) -> PublishPackageV1:
    signal_id = str(signal["signal_id"])
    title = str(signal["title"])
    summary = str(signal["summary"])
    source_name = str(signal["source_name"])
    source_url = str(signal.get("url") or signal.get("source_url") or "")
    slug = slugify(title)
    seo_metadata = build_seo_metadata(title=title, summary=summary, slug=slug)
    social_drafts = build_social_drafts(title=title, summary=summary, link_url=seo_metadata.canonical_url)

    return PublishPackageV1(
        package_id=stable_id("publish_package", signal_id, slug),
        signal_id=signal_id,
        title=title,
        slug=slug,
        summary=summary,
        source_url=source_url,
        source_name=source_name,
        canonical_language=CANONICAL_LANGUAGE,
        localized_languages=OPTIONAL_LOCALIZED_LANGUAGES,
        seo_metadata=serialize_seo_metadata(seo_metadata),
        social_drafts=tuple(serialize_social_draft(draft) for draft in social_drafts),
        status="package_ready",
        created_at=created_at,
    )


def serialize_publish_package(package: PublishPackageV1) -> dict[str, Any]:
    data = asdict(package)
    data["localized_languages"] = list(package.localized_languages)
    data["social_drafts"] = list(package.social_drafts)
    return data


def run_publish_package(quality_report: dict[str, Any], created_at: str | None = None) -> dict[str, Any]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    eligibility_statuses = eligibility_status_by_signal(quality_report)
    signals_by_id = signal_by_id_from_quality_report(quality_report)
    skipped: list[dict[str, str]] = []
    packages: list[PublishPackageV1] = []

    for review in quality_report.get("reviews", []):
        if not isinstance(review, dict):
            continue
        signal_id = str(review.get("signal_id"))
        status = eligibility_statuses.get(signal_id, str(review.get("decision")))
        if status != "publish_ready":
            skipped.append({"signal_id": signal_id, "reason": f"eligibility_status={status}"})
            continue
        signal = signals_by_id.get(signal_id)
        if signal is None:
            skipped.append({"signal_id": signal_id, "reason": "signal payload missing"})
            continue
        packages.append(create_publish_package(signal, created_at=timestamp))

    return {
        "generated_at": timestamp,
        "quality_report_id": str(quality_report.get("ranking_id") or "unknown_quality_report"),
        "packages_created": len(packages),
        "signals_seen": len(quality_report.get("reviews", [])),
        "skipped": skipped,
        "packages": [serialize_publish_package(package) for package in packages],
        "canonical_language": CANONICAL_LANGUAGE,
        "localized_languages": list(OPTIONAL_LOCALIZED_LANGUAGES),
        "website_pages_written": False,
        "public_content_files_written": False,
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
    parser = argparse.ArgumentParser(description="Run DysonX Publish Package V1.")
    parser.add_argument("--quality-report", required=True, help="Path to quality review report JSON.")
    parser.add_argument("--output", required=True, help="Path to write publish package report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    quality_report = load_quality_report(args.quality_report)
    report = run_publish_package(quality_report)
    write_report(report, args.output)
    print(
        "[publish-package] wrote report: "
        f"{args.output} packages={report['packages_created']} skipped={len(report['skipped'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
