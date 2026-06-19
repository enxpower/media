import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_openai_output_quality_audit as audit


FIXTURE_DIR = ROOT / "tests" / "fixtures" / "openai_output_quality_audit_v1"
LLM_AUDIT_REPORT = FIXTURE_DIR / "llm_audit_report.json"
SIGNAL_CANDIDATE_REPORT = FIXTURE_DIR / "signal_candidate_report.json"
PIPELINE_REPORT = FIXTURE_DIR / "pipeline_report.json"
FIXED_TIME = "2026-06-19T00:00:00+00:00"


class DysonXOpenAIOutputQualityAuditTests(unittest.TestCase):
    def run_fixture_audit(self) -> dict:
        return audit.run_audit(
            LLM_AUDIT_REPORT,
            SIGNAL_CANDIDATE_REPORT,
            PIPELINE_REPORT,
            created_at=FIXED_TIME,
        )

    def test_script_reads_fixture_reports_and_writes_audit_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "quality_audit.json"

            exit_code = audit.main(
                [
                    "--llm-audit-report",
                    str(LLM_AUDIT_REPORT),
                    "--signal-candidate-report",
                    str(SIGNAL_CANDIDATE_REPORT),
                    "--pipeline-report",
                    str(PIPELINE_REPORT),
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["audit_version"], audit.AUDIT_VERSION)
            self.assertEqual(report["signals_reviewed"], 2)
            self.assertEqual(len(report["signal_reviews"]), 2)

    def test_no_openai_api_key_is_required(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            report = self.run_fixture_audit()

        self.assertEqual(report["signals_reviewed"], 2)

    def test_safety_flags_are_all_false(self):
        report = self.run_fixture_audit()

        for flag_name, value in report["safety_flags"].items():
            self.assertFalse(value, flag_name)

    def test_quality_dimensions_match_framework_dimensions(self):
        report = self.run_fixture_audit()

        self.assertEqual(report["quality_dimensions"], list(audit.QUALITY_DIMENSIONS))
        for review in report["signal_reviews"]:
            self.assertEqual(list(review["quality_scores"].keys()), list(audit.QUALITY_DIMENSIONS))

    def test_missing_source_url_creates_missing_source_url_risk(self):
        report = self.run_fixture_audit()
        weak = next(review for review in report["signal_reviews"] if review["candidate_id"] == "candidate_weak")

        self.assertIn("missing_source_url", weak["risk_flags"])

    def test_generic_summary_is_penalized(self):
        report = self.run_fixture_audit()
        weak = next(review for review in report["signal_reviews"] if review["candidate_id"] == "candidate_weak")

        self.assertIn("generic_summary", weak["risk_flags"])
        self.assertLessEqual(weak["quality_scores"]["Anti-Garbage Risk"], 2)

    def test_strong_fixture_signal_scores_above_weak_fixture_signal(self):
        report = self.run_fixture_audit()
        scores = {review["candidate_id"]: review["total_score"] for review in report["signal_reviews"]}

        self.assertGreater(scores["candidate_strong"], scores["candidate_weak"])

    def test_tier_a_is_not_granted_to_thin_generic_output(self):
        report = self.run_fixture_audit()
        weak = next(review for review in report["signal_reviews"] if review["candidate_id"] == "candidate_weak")

        self.assertNotEqual(weak["quality_tier"], "Tier A: Decision-grade Signal")
        self.assertEqual(weak["quality_tier"], "Tier D: Reject / Low-value")

    def test_critical_risk_prevents_publish_readiness_candidate(self):
        report = self.run_fixture_audit()
        weak = next(review for review in report["signal_reviews"] if review["candidate_id"] == "candidate_weak")

        self.assertIn("missing_source_url", weak["risk_flags"])
        self.assertFalse(weak["pass_publish_readiness_candidate"])

    def test_output_includes_framework_and_milestone_references(self):
        report = self.run_fixture_audit()

        self.assertEqual(report["framework_reference"], "docs/DYSONX_SIGNAL_QUALITY_FRAMEWORK_V1.md")
        self.assertEqual(report["milestone_reference"], "docs/DYSONX_V1_OPENAI_ORCHESTRATOR_SMOKE_MILESTONE.md")

    def test_no_raw_provider_response_is_required_or_stored(self):
        report = self.run_fixture_audit()
        serialized = json.dumps(report)

        self.assertFalse(report["safety_flags"]["raw_provider_response_stored"])
        self.assertNotIn("raw_provider_response\":", serialized)

    def test_cli_exits_nonzero_on_malformed_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            malformed = pathlib.Path(tmpdir) / "malformed.json"
            malformed.write_text("{not valid json", encoding="utf-8")
            output = pathlib.Path(tmpdir) / "quality_audit.json"

            exit_code = audit.main(
                [
                    "--llm-audit-report",
                    str(malformed),
                    "--signal-candidate-report",
                    str(SIGNAL_CANDIDATE_REPORT),
                    "--pipeline-report",
                    str(PIPELINE_REPORT),
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 1)
            self.assertFalse(output.exists())

    def test_audit_script_has_no_live_network_or_provider_dependency(self):
        source = pathlib.Path(audit.__file__).read_text(encoding="utf-8").lower()

        self.assertNotIn("http.client", source)
        self.assertNotIn("urllib", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("import openai", source)
        self.assertNotIn("dysonx_real_llm_provider", source)
        self.assertNotIn("api.github.com", source)
        self.assertNotIn("api.notion.com", source)


if __name__ == "__main__":
    unittest.main()
