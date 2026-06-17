#!/usr/bin/env python3
"""DysonX Release Guard.

Lightweight release-readiness checks for GitHub Pages/static-site workflows.
This is intentionally conservative and non-destructive.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

RECOMMENDED_FILES = [
    "index.html",
    "README.md",
    "AGENTS.md",
    "docs/DYSONX_PRODUCT_CONSTITUTION.md",
    "docs/DYSONX_SYSTEM_ARCHITECTURE.md",
    "docs/DYSONX_ENGINEERING_GOVERNANCE.md",
]


def fail(message: str) -> None:
    print(f"[release-guard] FAIL: {message}")
    sys.exit(1)


def warn(message: str) -> None:
    print(f"[release-guard] WARN: {message}")


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def check_files() -> None:
    for rel in RECOMMENDED_FILES:
        if not (ROOT / rel).exists():
            fail(f"missing recommended release file: {rel}")


def check_html_basics() -> None:
    index = ROOT / "index.html"
    if not index.exists():
        return
    html = read(index).lower()
    for required in ["<title", "viewport", "description"]:
        if required not in html:
            warn(f"index.html may be missing {required}")

    risky_css = ["width: 100vw", "min-width:"]
    for token in risky_css:
        if token in html:
            warn(f"index.html contains layout token requiring mobile review: {token}")


def check_workflows() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    if not workflow_dir.exists():
        warn("no GitHub Actions workflow directory found")
        return
    if not any(p.suffix in {".yml", ".yaml"} for p in workflow_dir.iterdir() if p.is_file()):
        warn("no workflow files found")


def main() -> None:
    check_files()
    check_html_basics()
    check_workflows()
    print("[release-guard] PASS")


if __name__ == "__main__":
    main()
