#!/usr/bin/env python3
"""DysonX Architecture Guard.

Checks that key architectural layers and anti-drift terms remain present.
This is a lightweight guard for CI and PR review.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARCH_DOC = ROOT / "docs/DYSONX_SYSTEM_ARCHITECTURE.md"

REQUIRED_LAYERS = [
    "Source Configuration Layer",
    "Collection Layer",
    "Raw Data Layer",
    "Normalization Layer",
    "LLM Intelligence Layer",
    "Deduplication and Authority Layer",
    "Knowledge Graph Layer",
    "Publishing Layer",
    "Social Distribution Layer",
    "Reporting Layer",
    "Observability and Audit Layer",
    "Governance Layer",
]

REQUIRED_FLOW_TERMS = [
    "Source",
    "LLM Understanding",
    "Structured Knowledge",
    "Signal",
    "Tracker",
    "Report",
    "Distribution",
]

FORBIDDEN_ARCHITECTURE_HINTS = [
    "direct source-to-page publishing",
    "publish raw rss summaries directly",
    "website pages as the only data store",
]


def fail(message: str) -> None:
    print(f"[architecture-guard] FAIL: {message}")
    sys.exit(1)


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> None:
    if not ARCH_DOC.exists():
        fail("missing docs/DYSONX_SYSTEM_ARCHITECTURE.md")

    arch = read(ARCH_DOC)
    lower = arch.lower()

    for layer in REQUIRED_LAYERS:
        if layer.lower() not in lower:
            fail(f"missing architecture layer: {layer}")

    for term in REQUIRED_FLOW_TERMS:
        if term.lower() not in lower:
            fail(f"missing canonical flow term: {term}")

    for phrase in FORBIDDEN_ARCHITECTURE_HINTS:
        if phrase in lower and "forbidden" not in lower[max(0, lower.find(phrase)-120):lower.find(phrase)+120]:
            fail(f"forbidden architecture hint appears without prohibition: {phrase}")

    print("[architecture-guard] PASS")


if __name__ == "__main__":
    main()
