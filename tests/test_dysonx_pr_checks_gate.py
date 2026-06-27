import json
import unittest
import sys
import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_pr_checks_gate as gate  # noqa: E402


EXCLUDED = "DysonX Public Signals Auto-Merge V1 / Gate and auto-merge public Signals sync PRs"


def check(name, bucket="pass", state="", workflow="CI"):
    return {
        "name": name,
        "workflow": workflow,
        "state": state,
        "bucket": bucket,
        "link": "https://example.org/check",
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

    def test_passes_when_bucket_is_pass(self):
        calls = self.wait([[check("unit", "pass")]])
        self.assertEqual(calls, 1)

    def test_passes_when_bucket_is_skipping(self):
        calls = self.wait([[check("docs", "skipping")]])
        self.assertEqual(calls, 1)

    def test_waits_when_bucket_pending_then_passes(self):
        calls = self.wait([[check("unit", "pending")], [check("unit", "pass")]])
        self.assertEqual(calls, 2)

    def test_fails_when_bucket_is_fail(self):
        with self.assertRaisesRegex(gate.PRChecksGateError, "unit: fail"):
            self.wait([[check("unit", "fail")]])

    def test_fails_when_bucket_is_cancel(self):
        with self.assertRaisesRegex(gate.PRChecksGateError, "unit: cancel"):
            self.wait([[check("unit", "cancel")]])

    def test_falls_back_to_state_when_bucket_missing(self):
        calls = self.wait([[check("unit", bucket="", state="SUCCESS")]])
        self.assertEqual(calls, 1)

    def test_fail_closed_on_unknown_bucket_or_state(self):
        with self.assertRaisesRegex(gate.PRChecksGateError, "unknown bucket mystery"):
            self.wait([[check("unit", "mystery")]])
        with self.assertRaisesRegex(gate.PRChecksGateError, "unknown state weird"):
            self.wait([[check("unit", bucket="", state="WEIRD")]])

    def test_excluded_auto_merge_check_does_not_block(self):
        calls = self.wait(
            [
                [
                    check("Gate and auto-merge public Signals sync PRs", None, state="IN_PROGRESS", workflow="DysonX Public Signals Auto-Merge V1"),
                    check("unit", "pass"),
                ]
            ]
        )
        self.assertEqual(calls, 1)

    def test_timeout_fails_with_clear_message(self):
        with self.assertRaisesRegex(gate.PRChecksGateError, "timed out waiting for checks"):
            self.wait([[check("unit", "pending")]], timeout=10, poll=5)


if __name__ == "__main__":
    unittest.main()
