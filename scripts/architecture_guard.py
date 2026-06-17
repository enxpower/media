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

GOVERNANCE_FILES = {
    "AGENTS.md",
    "docs/DYSONX_PRODUCT_CONSTITUTION.md",
    "docs/DYSONX_SYSTEM_ARCHITECTURE.md",
    "docs/DYSONX_ENGINEERING_GOVERNANCE.md",
    "docs/DYSONX_PROJECT_CONTEXT.md",
    "docs/DYSONX_OWNER_INTENT.md",
    ".github/pull_request_template.md",
}

GUARD_FILES = {
    "scripts/architecture_guard.py",
}

SCAN_SUFFIXES = {".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".json", ".yml", ".yaml"}

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


def drift_scan_files() -> list[pathlib.Path]:
    return [
        path for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.relative_to(ROOT).as_posix() not in GOVERNANCE_FILES
        and path.relative_to(ROOT).as_posix() not in GUARD_FILES
        and path.suffix.lower() in SCAN_SUFFIXES
    ]


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

    for path in drift_scan_files():
        text = read(path).lower()
        for phrase in FORBIDDEN_ARCHITECTURE_HINTS:
            if phrase in text:
                fail(f"forbidden architecture hint found in {path.relative_to(ROOT)}: {phrase}")

    print("[architecture-guard] PASS")


if __name__ == "__main__":
    main()
