import json
import unittest
import sys
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_pr_checks_gate as gate  # noqa: E402


EXCLUDED = "DysonX Public Signals Auto-Merge V1 / Gate and auto-merge public Signals sync PRs"


def check(name, conclusion=None, state="COMPLETED", workflow="CI"):
    return {
        "name": name,
        "workflowName": workflow,
        "state": state,
        "status": state,
        "conclusion": conclusion,
    }


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class Runner:
    def __init__(self, snapshots):
        self.snapshots = list(snapshots)
        self.calls = 0

    def __call__(self, args):
        self.calls += 1
        index = min(self.calls - 1, len(self.snapshots) - 1)
        return json.dumps(self.snapshots[index])


class DysonXPRChecksGateTests(unittest.TestCase):
    def wait(self, snapshots, timeout=60, poll=5):
        clock = FakeClock()
        runner = Runner(snapshots)
        gate.wait_for_checks(
            repo="owner/repo",
            pr_number="12",
            exclude_check_name=EXCLUDED,
            timeout_seconds=timeout,
            poll_seconds=poll,
            runner=runner,
            sleeper=clock.sleep,
            clock=clock,
        )
        return runner.calls

    def test_passes_when_all_checks_success_skipped_or_neutral(self):
        calls = self.wait([[check("unit", "success"), check("docs", "skipped"), check("lint", "neutral")]])
        self.assertEqual(calls, 1)

    def test_fails_when_any_check_is_failure(self):
        with self.assertRaisesRegex(gate.PRChecksGateError, "unit: failure"):
            self.wait([[check("unit", "failure")]])

    def test_fails_when_any_check_is_cancelled(self):
        with self.assertRaisesRegex(gate.PRChecksGateError, "unit: cancelled"):
            self.wait([[check("unit", "cancelled")]])

    def test_fails_when_any_check_is_timed_out(self):
        with self.assertRaisesRegex(gate.PRChecksGateError, "unit: timed_out"):
            self.wait([[check("unit", "timed_out")]])

    def test_fails_when_any_check_is_action_required(self):
        with self.assertRaisesRegex(gate.PRChecksGateError, "unit: action_required"):
            self.wait([[check("unit", "action_required")]])

    def test_pending_in_progress_and_queued_wait_until_terminal(self):
        calls = self.wait(
            [
                [check("unit", None, state="QUEUED")],
                [check("unit", None, state="IN_PROGRESS")],
                [check("unit", "success", state="COMPLETED")],
            ]
        )
        self.assertEqual(calls, 3)

    def test_excluded_auto_merge_check_does_not_block(self):
        calls = self.wait(
            [
                [
                    check("Gate and auto-merge public Signals sync PRs", None, state="IN_PROGRESS", workflow="DysonX Public Signals Auto-Merge V1"),
                    check("unit", "success"),
                ]
            ]
        )
        self.assertEqual(calls, 1)

    def test_timeout_fails_with_clear_message(self):
        with self.assertRaisesRegex(gate.PRChecksGateError, "timed out waiting for checks"):
            self.wait([[check("unit", None, state="IN_PROGRESS")]], timeout=10, poll=5)


if __name__ == "__main__":
    unittest.main()
