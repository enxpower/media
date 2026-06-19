import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_signal_quality_score as score


FIXTURE = ROOT / "tests" / "fixtures" / "signal_quality_score_v1" / "openai_output_quality_audit.json"
FIXED_TIME = "2026-06-19T00:00:00+00:00"


class DysonXSignalQualityScoreTests(unittest.TestCase):
    def run_fixture_score(self) -> dict:
        return score.run_score(FIXTURE, created_at=FIXED_TIME)

    def records_by_candidate(self) -> dict[str, dict]:
        report = self.run_fixture_score()
        return {record["candidate_id"]: record for record in report["score_records"]}

    def test_script_reads_audit_fixture_and_writes_score_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "signal_quality_score.json"

            exit_code = score.main(["--audit-report", str(FIXTURE), "--output", str(output)])

            self.assertEqual(exit_code, 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["score_version"], score.SCORE_VERSION)
            self.assertEqual(report["signals_scored"], 4)
            self.assertEqual(len(report["score_records"]), 4)

    def test_score_dimensions_exactly_match_framework_dimensions(self):
        report = self.run_fixture_score()

        self.assertEqual(report["score_dimensions"], list(score.SCORE_DIMENSIONS))
        for record in report["score_records"]:
            self.assertEqual(list(record["dimension_scores"].keys()), list(score.SCORE_DIMENSIONS))

    def test_score_percentage_is_total_score_divided_by_65(self):
        records = self.records_by_candidate()
        tier_a = records["candidate_tier_a"]

        self.assertEqual(tier_a["quality_score_total"], 57)
        self.assertEqual(tier_a["quality_score_max"], 65)
        self.assertAlmostEqual(tier_a["quality_score_percent"], 57 / 65)

    def test_critical_risks_block_publish_readiness_candidate(self):
        records = self.records_by_candidate()
        tier_d = records["candidate_tier_d"]

        self.assertIn("missing_source_url", tier_d["critical_risk_flags"])
        self.assertFalse(tier_d["publish_readiness_candidate"])

    def test_tier_a_without_critical_risks_maps_to_human_approval_not_publish_ready(self):
        records = self.records_by_candidate()
        tier_a = records["candidate_tier_a"]

        self.assertEqual(tier_a["recommended_action"], "candidate_for_human_approval")
        self.assertTrue(tier_a["publish_readiness_candidate"])
        self.assertTrue(tier_a["requires_human_review"])

    def test_tier_b_maps_to_needs_human_review(self):
        records = self.records_by_candidate()

        self.assertEqual(records["candidate_tier_b"]["recommended_action"], "needs_human_review")
        self.assertTrue(records["candidate_tier_b"]["requires_human_review"])

    def test_tier_c_maps_to_improve_or_regenerate(self):
        records = self.records_by_candidate()

        self.assertEqual(records["candidate_tier_c"]["recommended_action"], "improve_or_regenerate")

    def test_tier_d_maps_to_reject_or_regenerate_without_critical_risk(self):
        review = json.loads(FIXTURE.read_text(encoding="utf-8"))
        tier_d = next(item for item in review["signal_reviews"] if item["candidate_id"] == "candidate_tier_d")
        tier_d["risk_flags"] = []
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = pathlib.Path(tmpdir) / "audit.json"
            audit_path.write_text(json.dumps(review), encoding="utf-8")
            report = score.run_score(audit_path, created_at=FIXED_TIME)

        record = next(item for item in report["score_records"] if item["candidate_id"] == "candidate_tier_d")
        self.assertEqual(record["recommended_action"], "reject_or_regenerate")

    def test_tier_d_maps_to_blocked_by_quality_risk_when_critical(self):
        records = self.records_by_candidate()

        self.assertEqual(records["candidate_tier_d"]["recommended_action"], "blocked_by_quality_risk")

    def test_any_critical_risk_maps_to_blocked_by_quality_risk(self):
        review = json.loads(FIXTURE.read_text(encoding="utf-8"))
        tier_b = next(item for item in review["signal_reviews"] if item["candidate_id"] == "candidate_tier_b")
        tier_b["risk_flags"] = ["missing_watch_next"]
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = pathlib.Path(tmpdir) / "audit.json"
            audit_path.write_text(json.dumps(review), encoding="utf-8")
            report = score.run_score(audit_path, created_at=FIXED_TIME)

        record = next(item for item in report["score_records"] if item["candidate_id"] == "candidate_tier_b")
        self.assertEqual(record["recommended_action"], "blocked_by_quality_risk")
        self.assertFalse(record["publish_readiness_candidate"])

    def test_safety_flags_are_all_false_including_publish_readiness_enabled(self):
        report = self.run_fixture_score()

        self.assertIn("publish_readiness_enabled", report["safety_flags"])
        for flag_name, value in report["safety_flags"].items():
            self.assertFalse(value, flag_name)

    def test_no_openai_api_key_is_required(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            report = self.run_fixture_score()

        self.assertEqual(report["signals_scored"], 4)

    def test_malformed_audit_report_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            malformed = pathlib.Path(tmpdir) / "malformed.json"
            malformed.write_text("{not json", encoding="utf-8")
            output = pathlib.Path(tmpdir) / "score.json"

            exit_code = score.main(["--audit-report", str(malformed), "--output", str(output)])

            self.assertEqual(exit_code, 1)
            self.assertFalse(output.exists())

    def test_missing_required_audit_fields_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_path = pathlib.Path(tmpdir) / "audit.json"
            audit_path.write_text(json.dumps({"audit_version": "openai_output_quality_audit_v1"}), encoding="utf-8")

            with self.assertRaises(score.ScoreInputError):
                score.run_score(audit_path, created_at=FIXED_TIME)

    def test_output_includes_framework_and_audit_references(self):
        report = self.run_fixture_score()

        self.assertEqual(report["framework_reference"], "docs/DYSONX_SIGNAL_QUALITY_FRAMEWORK_V1.md")
        self.assertEqual(report["audit_reference"], "docs/DYSONX_OPENAI_OUTPUT_QUALITY_AUDIT_V1.md")

    def test_confidence_calibration_is_required_but_not_implemented(self):
        report = self.run_fixture_score()

        for record in report["score_records"]:
            self.assertTrue(record["requires_confidence_calibration"])
        self.assertNotIn("calibrated_confidence", json.dumps(report))

    def test_correlation_is_recommended_only_as_future_action_not_performed(self):
        records = self.records_by_candidate()

        self.assertTrue(records["candidate_tier_a"]["correlation_recommended"])
        self.assertTrue(records["candidate_tier_b"]["correlation_recommended"])
        serialized = json.dumps(self.run_fixture_score())
        self.assertNotIn("correlation_performed", serialized)
        self.assertNotIn("correlation_results", serialized)

    def test_no_raw_provider_response_is_required_or_stored(self):
        report = self.run_fixture_score()
        serialized = json.dumps(report)

        self.assertFalse(report["safety_flags"]["raw_provider_response_stored"])
        self.assertNotIn('"raw_provider_response":', serialized)

    def test_score_script_has_no_live_network_or_provider_dependency(self):
        source = pathlib.Path(score.__file__).read_text(encoding="utf-8").lower()

        self.assertNotIn("http.client", source)
        self.assertNotIn("urllib", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("import openai", source)
        self.assertNotIn("dysonx_real_llm_provider", source)
        self.assertNotIn("api.github.com", source)
        self.assertNotIn("api.notion.com", source)


if __name__ == "__main__":
    unittest.main()
