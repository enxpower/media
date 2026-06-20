import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_owner_review_feedback as feedback


FIXTURE_DIR = ROOT / "tests" / "fixtures" / "owner_review_feedback_v1"
BRIEF_FIXTURE = FIXTURE_DIR / "internal_intelligence_brief.json"
FEEDBACK_FIXTURE = FIXTURE_DIR / "owner_feedback_input.json"
FIXED_TIME = "2026-06-20T00:00:00+00:00"


class DysonXOwnerReviewFeedbackTests(unittest.TestCase):
    def build_fixture_feedback(self) -> dict:
        return feedback.build_feedback_report(BRIEF_FIXTURE, FEEDBACK_FIXTURE, created_at=FIXED_TIME)

    def write_json(self, path: pathlib.Path, data: dict) -> None:
        path.write_text(json.dumps(data), encoding="utf-8")

    def load_feedback_input(self) -> dict:
        return json.loads(FEEDBACK_FIXTURE.read_text(encoding="utf-8"))

    def test_script_reads_fixtures_and_writes_owner_review_feedback_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "owner_review_feedback.json"

            exit_code = feedback.main([
                "--brief-json",
                str(BRIEF_FIXTURE),
                "--feedback-input",
                str(FEEDBACK_FIXTURE),
                "--output",
                str(output),
            ])

            self.assertEqual(exit_code, 0)
            self.assertTrue(output.exists())
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["feedback_version"], feedback.FEEDBACK_VERSION)
            self.assertEqual(report["decisions_recorded"], 5)

    def test_output_includes_all_required_top_level_fields(self):
        report = self.build_fixture_feedback()

        expected = {
            "feedback_version",
            "created_at",
            "reviewer",
            "review_session_id",
            "reviewed_at",
            "source_brief",
            "brief_version",
            "signals_reviewed",
            "decisions_recorded",
            "decision_counts",
            "follow_up_required_count",
            "feedback_records",
            "recommended_next_actions",
            "safety_flags",
        }
        self.assertEqual(set(report.keys()), expected)

    def test_feedback_records_include_all_required_fields(self):
        report = self.build_fixture_feedback()
        expected = {
            "signal_id",
            "title",
            "original_tier",
            "original_recommended_action",
            "owner_decision",
            "owner_comment",
            "priority",
            "follow_up_required",
            "follow_up_note",
            "resulting_status",
            "next_action",
        }

        for record in report["feedback_records"]:
            self.assertEqual(set(record.keys()), expected)

    def test_allowed_decisions_map_to_correct_resulting_status(self):
        report = self.build_fixture_feedback()
        statuses = {record["owner_decision"]: record["resulting_status"] for record in report["feedback_records"]}

        self.assertEqual(
            statuses,
            {
                "approve_for_future_publish_readiness_review": "owner_approved_for_later_publish_readiness_review_only",
                "request_more_sources": "needs_more_sources",
                "request_regeneration": "needs_regeneration",
                "reject": "owner_rejected",
                "hold": "owner_hold",
            },
        )

    def test_allowed_decisions_map_to_correct_next_action(self):
        report = self.build_fixture_feedback()
        actions = {record["owner_decision"]: record["next_action"] for record in report["feedback_records"]}

        self.assertEqual(
            actions,
            {
                "approve_for_future_publish_readiness_review": "later_publish_readiness_review_required",
                "request_more_sources": "collect_or_attach_more_sources",
                "request_regeneration": "regenerate_or_improve_signal_analysis",
                "reject": "remove_from_current_review_queue",
                "hold": "keep_for_later_review",
            },
        )

    def test_unknown_decision_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_path = pathlib.Path(tmpdir) / "feedback.json"
            data = self.load_feedback_input()
            data["decisions"][0]["owner_decision"] = "publish_now"
            self.write_json(feedback_path, data)

            with self.assertRaises(feedback.FeedbackInputError):
                feedback.build_feedback_report(BRIEF_FIXTURE, feedback_path, created_at=FIXED_TIME)

    def test_unknown_priority_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_path = pathlib.Path(tmpdir) / "feedback.json"
            data = self.load_feedback_input()
            data["decisions"][0]["priority"] = "urgent"
            self.write_json(feedback_path, data)

            with self.assertRaises(feedback.FeedbackInputError):
                feedback.build_feedback_report(BRIEF_FIXTURE, feedback_path, created_at=FIXED_TIME)

    def test_missing_reviewer_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_path = pathlib.Path(tmpdir) / "feedback.json"
            data = self.load_feedback_input()
            del data["reviewer"]
            self.write_json(feedback_path, data)

            with self.assertRaises(feedback.FeedbackInputError):
                feedback.build_feedback_report(BRIEF_FIXTURE, feedback_path, created_at=FIXED_TIME)

    def test_empty_decisions_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_path = pathlib.Path(tmpdir) / "feedback.json"
            data = self.load_feedback_input()
            data["decisions"] = []
            self.write_json(feedback_path, data)

            with self.assertRaises(feedback.FeedbackInputError):
                feedback.build_feedback_report(BRIEF_FIXTURE, feedback_path, created_at=FIXED_TIME)

    def test_unknown_signal_id_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            feedback_path = pathlib.Path(tmpdir) / "feedback.json"
            data = self.load_feedback_input()
            data["decisions"][0]["signal_id"] = "unknown_signal"
            self.write_json(feedback_path, data)

            with self.assertRaises(feedback.FeedbackInputError):
                feedback.build_feedback_report(BRIEF_FIXTURE, feedback_path, created_at=FIXED_TIME)

    def test_approve_for_future_review_does_not_enable_publishing_or_publish_readiness(self):
        report = self.build_fixture_feedback()
        approved = [
            record for record in report["feedback_records"]
            if record["owner_decision"] == "approve_for_future_publish_readiness_review"
        ][0]

        self.assertEqual(
            approved["resulting_status"],
            "owner_approved_for_later_publish_readiness_review_only",
        )
        self.assertEqual(approved["next_action"], "later_publish_readiness_review_required")
        self.assertFalse(report["safety_flags"]["publish_readiness_enabled"])
        self.assertFalse(report["safety_flags"]["publishing_performed"])
        self.assertIn(
            "Future publish-readiness review is required; do not publish automatically.",
            report["recommended_next_actions"],
        )

    def test_safety_flags_are_all_false(self):
        report = self.build_fixture_feedback()

        expected_flags = {
            "openai_call_performed",
            "workflow_dispatched",
            "publishing_performed",
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
        self.assertEqual(set(report["safety_flags"].keys()), expected_flags)
        for flag_name, value in report["safety_flags"].items():
            self.assertFalse(value, flag_name)

    def test_no_openai_api_key_is_required(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            report = self.build_fixture_feedback()

        self.assertEqual(report["reviewer"], "Owner")

    def test_malformed_input_exits_nonzero_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            malformed = pathlib.Path(tmpdir) / "malformed.json"
            malformed.write_text("{not json", encoding="utf-8")
            output = pathlib.Path(tmpdir) / "owner_review_feedback.json"

            exit_code = feedback.main([
                "--brief-json",
                str(BRIEF_FIXTURE),
                "--feedback-input",
                str(malformed),
                "--output",
                str(output),
            ])

            self.assertEqual(exit_code, 1)
            self.assertFalse(output.exists())

    def test_no_raw_provider_response_is_required_or_stored(self):
        report = self.build_fixture_feedback()
        serialized = json.dumps(report)

        self.assertFalse(report["safety_flags"]["raw_provider_response_stored"])
        self.assertNotIn('"raw_provider_response":', serialized)

    def test_no_public_content_seo_social_kg_prediction_confidence_correlation_deployment_or_workflow_behavior(self):
        report = self.build_fixture_feedback()
        serialized = json.dumps(report).lower()

        for flag_name in (
            "public_content_generated",
            "website_pages_written",
            "social_posting_performed",
            "knowledge_graph_write_performed",
            "prediction_engine_performed",
            "confidence_calibration_performed",
            "correlation_performed",
            "deployment_performed",
            "workflow_dispatched",
        ):
            self.assertFalse(report["safety_flags"][flag_name], flag_name)
        self.assertNotIn("seo_metadata", serialized)
        self.assertNotIn("social_draft", serialized)


if __name__ == "__main__":
    unittest.main()
