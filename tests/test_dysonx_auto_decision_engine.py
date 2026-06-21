import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dysonx_auto_decision_engine.py"
FIXTURE = ROOT / "tests" / "fixtures" / "auto_decision_engine_v1" / "signal_quality_score.json"


REQUIRED_TOP_LEVEL_FIELDS = {
    "auto_decision_version",
    "created_at",
    "source_score_report",
    "signals_evaluated",
    "decision_counts",
    "auto_decision_records",
    "exception_records",
    "recommended_owner_attention",
    "safety_flags",
}

REQUIRED_RECORD_FIELDS = {
    "signal_id",
    "title",
    "quality_tier",
    "quality_score_total",
    "quality_score_max",
    "source_url",
    "source_authority",
    "agi_capability",
    "auto_decision",
    "decision_label",
    "decision_confidence",
    "decision_reasons",
    "blocking_reasons",
    "missing_fields",
    "risk_flags",
    "recommended_next_action",
    "owner_override_allowed",
    "publish_readiness_candidate",
    "publication_approved",
}

EXPECTED_SAFETY_FLAGS = {
    "openai_call_performed",
    "workflow_dispatched",
    "publishing_performed",
    "publication_approved",
    "publish_readiness_enabled",
    "public_content_generated",
    "website_pages_written",
    "social_posting_performed",
    "notion_mutation_performed",
    "live_github_api_used",
    "article_body_scraping_performed",
    "raw_provider_response_stored",
    "knowledge_graph_write_performed",
    "prediction_engine_performed",
    "confidence_calibration_performed",
    "correlation_performed",
    "deployment_performed",
}


class DysonXAutoDecisionEngineTests(unittest.TestCase):
    def run_script(self, fixture: pathlib.Path = FIXTURE) -> tuple[subprocess.CompletedProcess, pathlib.Path]:
        output_dir = pathlib.Path(tempfile.mkdtemp())
        output = output_dir / "auto_decision.json"
        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--score-report",
                str(fixture),
                "--output",
                str(output),
            ],
            cwd=ROOT,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        return result, output

    def load_report(self) -> dict:
        result, output = self.run_script()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(output.read_text(encoding="utf-8"))

    def records_by_signal_id(self, report: dict) -> dict:
        return {record["signal_id"]: record for record in report["auto_decision_records"]}

    def test_script_reads_fixture_and_writes_auto_decision_report(self):
        result, output = self.run_script()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(output.exists())
        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(report["auto_decision_version"], "auto_decision_engine_v1")
        self.assertEqual(report["signals_evaluated"], 5)

    def test_output_includes_required_top_level_fields(self):
        report = self.load_report()

        self.assertTrue(REQUIRED_TOP_LEVEL_FIELDS.issubset(report.keys()))

    def test_each_auto_decision_record_includes_required_fields(self):
        report = self.load_report()

        for record in report["auto_decision_records"]:
            self.assertTrue(REQUIRED_RECORD_FIELDS.issubset(record.keys()))

    def test_tier_d_generic_or_missing_source_maps_to_auto_reject(self):
        records = self.records_by_signal_id(self.load_report())

        record = records["sig_generic_market_noise"]
        self.assertEqual(record["auto_decision"], "auto_reject")
        self.assertEqual(record["decision_label"], "Reject automatically")
        self.assertEqual(record["recommended_next_action"], "remove_from_current_review_queue")
        self.assertIn("generic_summary", record["risk_flags"])

    def test_tier_c_or_missing_core_fields_maps_to_needs_regeneration(self):
        records = self.records_by_signal_id(self.load_report())

        record = records["sig_robotics_policy_regenerate"]
        self.assertEqual(record["auto_decision"], "needs_regeneration")
        self.assertEqual(record["decision_label"], "Regenerate analysis")
        self.assertEqual(record["recommended_next_action"], "regenerate_or_improve_signal_analysis")
        self.assertIn("why_it_matters", record["missing_fields"])
        self.assertIn("watch_next", record["missing_fields"])

    def test_weak_source_evidence_maps_to_needs_more_sources(self):
        records = self.records_by_signal_id(self.load_report())

        record = records["sig_enterprise_memory_controls"]
        self.assertEqual(record["auto_decision"], "needs_more_sources")
        self.assertEqual(record["decision_label"], "Need more sources")
        self.assertEqual(record["recommended_next_action"], "collect_or_attach_more_sources")

    def test_tier_b_incomplete_but_noncritical_maps_to_hold(self):
        records = self.records_by_signal_id(self.load_report())

        record = records["sig_inference_efficiency_hold"]
        self.assertEqual(record["auto_decision"], "hold")
        self.assertEqual(record["decision_label"], "Hold")
        self.assertEqual(record["recommended_next_action"], "keep_for_later_review")

    def test_tier_a_strong_signal_maps_to_candidate_for_publish_readiness_review(self):
        records = self.records_by_signal_id(self.load_report())

        record = records["sig_agent_eval_reliability"]
        self.assertEqual(record["auto_decision"], "candidate_for_publish_readiness_review")
        self.assertEqual(record["decision_label"], "Candidate for later readiness review")
        self.assertEqual(record["recommended_next_action"], "later_publish_readiness_review_required")

    def test_candidate_does_not_set_publication_approved_true(self):
        records = self.records_by_signal_id(self.load_report())

        record = records["sig_agent_eval_reliability"]
        self.assertTrue(record["publish_readiness_candidate"])
        self.assertFalse(record["publication_approved"])

    def test_publication_approved_is_always_false(self):
        report = self.load_report()

        self.assertFalse(report["safety_flags"]["publication_approved"])
        for record in report["auto_decision_records"]:
            self.assertFalse(record["publication_approved"])

    def test_publish_readiness_candidate_only_for_candidate_decision(self):
        report = self.load_report()

        for record in report["auto_decision_records"]:
            expected = record["auto_decision"] == "candidate_for_publish_readiness_review"
            self.assertEqual(record["publish_readiness_candidate"], expected)

    def test_owner_override_allowed_is_true(self):
        report = self.load_report()

        for record in report["auto_decision_records"]:
            self.assertTrue(record["owner_override_allowed"])

    def test_exception_records_include_candidates_and_high_value_more_source_items(self):
        report = self.load_report()
        exception_ids = {record["signal_id"] for record in report["exception_records"]}

        self.assertIn("sig_agent_eval_reliability", exception_ids)
        self.assertIn("sig_enterprise_memory_controls", exception_ids)
        self.assertIn("inspect_first_signal_ids", report["recommended_owner_attention"])

    def test_safety_flags_are_all_false(self):
        report = self.load_report()

        self.assertEqual(set(report["safety_flags"]), EXPECTED_SAFETY_FLAGS)
        self.assertTrue(all(value is False for value in report["safety_flags"].values()))

    def test_no_openai_api_key_is_required(self):
        result, output = self.run_script()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(output.exists())

    def test_malformed_input_fails_closed(self):
        bad = pathlib.Path(tempfile.mkdtemp()) / "bad.json"
        bad.write_text("{not-json", encoding="utf-8")

        result, _ = self.run_script(bad)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failed", result.stdout)

    def test_missing_required_score_fields_fails_closed(self):
        bad = pathlib.Path(tempfile.mkdtemp()) / "missing.json"
        bad.write_text(json.dumps({"score_version": "signal_quality_score_v1"}), encoding="utf-8")

        result, _ = self.run_script(bad)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing required fields", result.stdout)

    def test_no_public_or_live_operation_behavior(self):
        script = SCRIPT.read_text(encoding="utf-8")

        self.assertNotIn("requests", script)
        self.assertNotIn("urllib", script)
        self.assertNotIn("subprocess", script)
        self.assertNotIn("OPENAI_API_KEY", script)
        for phrase in (
            "public_content_generated",
            "social_posting_performed",
            "knowledge_graph_write_performed",
            "prediction_engine_performed",
            "deployment_performed",
            "confidence_calibration_performed",
            "correlation_performed",
            "notion_mutation_performed",
            "live_github_api_used",
            "workflow_dispatched",
        ):
            self.assertIn(phrase, script)


if __name__ == "__main__":
    unittest.main()
