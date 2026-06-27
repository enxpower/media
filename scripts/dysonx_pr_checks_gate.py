#!/usr/bin/env python3
"""Wait for all relevant GitHub PR checks to pass."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from typing import Any, Callable


PASSING_BUCKETS = {"pass", "skipping"}
FAILING_BUCKETS = {"fail", "cancel"}
WAITING_BUCKETS = {"pending"}
PASSING_STATE_TOKENS = ("success", "pass", "skipped", "neutral")
FAILING_STATE_TOKENS = ("fail", "error", "cancel", "timed_out", "action_required")
WAITING_STATE_TOKENS = ("pending", "queued", "in_progress", "expected")


class PRChecksGateError(RuntimeError):
    """Raised when PR checks are not safe for auto-merge."""


Runner = Callable[[list[str]], str]
Sleeper = Callable[[float], None]
Clock = Callable[[], float]


def run_gh(args: list[str]) -> str:
    return subprocess.check_output(args, text=True)


def normalize(value: Any) -> str:
    return str(value or "").strip()


def check_name(check: dict[str, Any]) -> str:
    workflow = normalize(check.get("workflow"))
    name = normalize(check.get("name"))
    return f"{workflow} / {name}" if workflow and name else name or workflow or "<unnamed check>"


def check_bucket(check: dict[str, Any]) -> str:
    return normalize(check.get("bucket")).lower()


def check_state(check: dict[str, Any]) -> str:
    return normalize(check.get("state")).lower()


def load_checks(repo: str, pr_number: str, runner: Runner = run_gh) -> list[dict[str, Any]]:
    output = runner(
        [
            "gh",
            "pr",
            "checks",
            pr_number,
            "--repo",
            repo,
            "--json",
            "name,workflow,state,bucket,link",
        ]
    )
    data = json.loads(output)
    if not isinstance(data, list):
        raise PRChecksGateError("gh pr checks did not return a JSON list")
    return [item for item in data if isinstance(item, dict)]


def classify_checks(checks: list[dict[str, Any]], exclude_check_name: str) -> tuple[list[str], list[str], int]:
    failing: list[str] = []
    waiting: list[str] = []
    checked = 0
    for check in checks:
        name = check_name(check)
        if name == exclude_check_name:
            continue
        checked += 1
        bucket = check_bucket(check)
        state = check_state(check)
        if bucket in PASSING_BUCKETS:
            continue
        if bucket in FAILING_BUCKETS:
            failing.append(f"{name}: {bucket}")
            continue
        if bucket in WAITING_BUCKETS:
            waiting.append(f"{name}: {bucket}")
            continue
        if bucket:
            failing.append(f"{name}: unknown bucket {bucket}")
            continue
        if any(token in state for token in PASSING_STATE_TOKENS):
            continue
        if any(token in state for token in FAILING_STATE_TOKENS):
            failing.append(f"{name}: {state}")
            continue
        if any(token in state for token in WAITING_STATE_TOKENS) or not state:
            waiting.append(f"{name}: {state or 'pending'}")
            continue
        failing.append(f"{name}: unknown state {state}")
    return failing, waiting, checked


def wait_for_checks(
    repo: str,
    pr_number: str,
    exclude_check_name: str,
    timeout_seconds: int,
    poll_seconds: int,
    runner: Runner = run_gh,
    sleeper: Sleeper = time.sleep,
    clock: Clock = time.monotonic,
) -> None:
    deadline = clock() + timeout_seconds
    last_waiting: list[str] = []
    while True:
        checks = load_checks(repo, pr_number, runner=runner)
        failing, waiting, checked = classify_checks(checks, exclude_check_name)
        if failing:
            raise PRChecksGateError("failing checks: " + "; ".join(failing))
        if checked == 0:
            raise PRChecksGateError("no non-excluded PR checks found")
        if not waiting:
            print(f"[dysonx-pr-checks-gate] PASS checks={checked}")
            return
        last_waiting = waiting
        if clock() >= deadline:
            raise PRChecksGateError("timed out waiting for checks: " + "; ".join(last_waiting))
        print("[dysonx-pr-checks-gate] waiting: " + "; ".join(waiting))
        sleeper(poll_seconds)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wait for all non-excluded GitHub PR checks to pass.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr-number", required=True)
    parser.add_argument("--exclude-check-name", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--poll-seconds", type=int, default=15)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        wait_for_checks(
            repo=args.repo,
            pr_number=args.pr_number,
            exclude_check_name=args.exclude_check_name,
            timeout_seconds=args.timeout_seconds,
            poll_seconds=args.poll_seconds,
        )
    except (PRChecksGateError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        print(f"[dysonx-pr-checks-gate] FAIL: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
