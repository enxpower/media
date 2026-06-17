#!/usr/bin/env python3
"""DysonX Constitution Guard.

This guard checks for obvious architecture and product drift. It is intentionally
simple, deterministic, and CI-friendly. It does not replace human review.
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENTS.md",
    "docs/DYSONX_PRODUCT_CONSTITUTION.md",
    "docs/DYSONX_SYSTEM_ARCHITECTURE.md",
    "docs/DYSONX_ENGINEERING_GOVERNANCE.md",
    ".github/pull_request_template.md",
]

FORBIDDEN_PRIMARY_FRAMING = [
    "dysonx is an ai news aggregator",
    "dysonx is a news aggregator",
    "dysonx is an rss",
    "generic news site",
]

REQUIRED_CONCEPTS = [
    "AI / AGI Intelligence OS",
    "Signal",
    "English",
    "Chinese",
    "Notion",
    "LLM",
    "knowledge graph",
    "quality gate",
]


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def fail(message: str) -> None:
    print(f"[constitution-guard] FAIL: {message}")
    sys.exit(1)


def warn(message: str) -> None:
    print(f"[constitution-guard] WARN: {message}")


def check_required_files() -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            fail(f"missing required governance file: {rel}")


def check_required_concepts() -> None:
    combined = "\n".join(read_text(ROOT / rel) for rel in REQUIRED_FILES if (ROOT / rel).exists())
    for concept in REQUIRED_CONCEPTS:
        if concept.lower() not in combined.lower():
            fail(f"required governance concept missing: {concept}")


def check_forbidden_framing() -> None:
    text_files = [
        p for p in ROOT.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and p.suffix.lower() in {".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".json", ".yml", ".yaml"}
    ]
    for path in text_files:
        text = read_text(path).lower()
        for phrase in FORBIDDEN_PRIMARY_FRAMING:
            if phrase in text and "must not" not in text[max(0, text.find(phrase)-80):text.find(phrase)+80]:
                fail(f"forbidden product framing found in {path.relative_to(ROOT)}: {phrase}")


def check_signal_not_article_primary() -> None:
    suspicious_patterns = [
        r"primary\s+content\s+object\s+is\s+article",
        r"article\s+is\s+the\s+primary\s+content",
    ]
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".md", ".py", ".js", ".ts", ".tsx", ".jsx"}:
            continue
        text = read_text(path).lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, text):
                fail(f"Article-first framing detected in {path.relative_to(ROOT)}")


def main() -> None:
    check_required_files()
    check_required_concepts()
    check_forbidden_framing()
    check_signal_not_article_primary()
    print("[constitution-guard] PASS")


if __name__ == "__main__":
    main()
