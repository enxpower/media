import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_internal_intelligence_brief as brief


FIXTURE = ROOT / "tests" / "fixtures" / "internal_intelligence_brief_v1" / "signal_quality_score.json"
FIXED_TIME = "2026-06-20T00:00:00+00:00"


class DysonXInternalIntelligenceBriefTests(unittest.TestCase):
    def build_fixture_brief(self) -> dict:
        return brief.build_brief(FIXTURE, created_at=FIXED_TIME)

    def test_script_reads_score_fixture_and_writes_markdown_and_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_md = pathlib.Path(tmpdir) / "brief.md"
            output_json = pathlib.Path(tmpdir) / "brief.json"

            exit_code = brief.main([
                "--score-report",
                str(FIXTURE),
                "--output-md",
                str(output_md),
                "--output-json",
                str(output_json),
            ])

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_md.exists())
            self.assertTrue(output_json.exists())
            report = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertEqual(report["brief_version"], brief.BRIEF_VERSION)
            self.assertEqual(report["signals_reviewed"], 4)

    def test_markdown_includes_required_sections(self):
        report = self.build_fixture_brief()
        markdown = brief.render_markdown(report)

        for heading in (
            "# DysonX Internal Intelligence Brief V1",
            "## Brief Metadata",
            "## Executive Summary",
            "## Decision-Grade Candidates",
            "## Useful Signals Requiring Review",
            "## Blocked / Low-Value Signals",
            "## Owner Review Queue",
            "## Next Actions",
            "## Safety Boundary",
        ):
            self.assertIn(heading, markdown)

    def test_json_includes_required_top_level_fields(self):
        report = self.build_fixture_brief()

        expected = {
            "brief_version",
            "created_at",
            "source_score_report",
            "generated_for",
            "signals_reviewed",
            "tier_counts",
            "blocked_count",
            "human_review_count",
            "correlation_recommended_count",
            "overall_recommendation",
            "decision_grade_candidates",
            "useful_review_queue",
            "blocked_or_low_value",
            "owner_review_queue",
            "recommended_next_actions",
            "safety_flags",
        }
        self.assertEqual(set(report.keys()), expected)

    def test_tier_a_without_critical_risks_appears_in_decision_grade_candidates(self):
        report = self.build_fixture_brief()
        ids = {item["signal_id"] for item in report["decision_grade_candidates"]}

        self.assertIn("signal_tier_a", ids)

    def test_tier_b_appears_in_useful_review_queue(self):
        report = self.build_fixture_brief()
        ids = {item["signal_id"] for item in report["useful_review_queue"]}

        self.assertIn("signal_tier_b", ids)

    def test_tier_c_d_or_critical_risk_signals_appear_in_blocked_or_low_value(self):
        report = self.build_fixture_brief()
        ids = {item["signal_id"] for item in report["blocked_or_low_value"]}

        self.assertIn("signal_tier_c", ids)
        self.assertIn("signal_tier_d", ids)

    def test_owner_review_queue_includes_placeholders_but_no_auto_approval(self):
        report = self.build_fixture_brief()

        self.assertEqual(len(report["owner_review_queue"]), 4)
        for item in report["owner_review_queue"]:
            self.assertEqual(item["owner_decision_placeholder"], list(brief.OWNER_DECISION_PLACEHOLDERS))
            self.assertNotIn("auto_approved", item)
            self.assertNotIn("approved", item)

    def test_safety_flags_are_all_false(self):
        report = self.build_fixture_brief()

        expected_flags = {
            "openai_call_performed",
            "workflow_dispatched",
            "publishing_performed",
            "public_content_generated",
            "website_pages_written",
            "social_posting_performed",
            "notion_mutation_performed",
            "live_github_api_used",
            "article_body_scraping_performed",
            "raw_provider_response_stored",
            "knowledge_graph_write_performed",
            "prediction_engine_performed",
            "deployment_performed",
        }
        self.assertEqual(set(report["safety_flags"].keys()), expected_flags)
        for flag_name, value in report["safety_flags"].items():
            self.assertFalse(value, flag_name)

    def test_no_openai_api_key_is_required(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            report = self.build_fixture_brief()

        self.assertEqual(report["generated_for"], brief.GENERATED_FOR)

    def test_malformed_input_exits_nonzero_and_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            malformed = pathlib.Path(tmpdir) / "malformed.json"
            malformed.write_text("{not json", encoding="utf-8")
            output_md = pathlib.Path(tmpdir) / "brief.md"
            output_json = pathlib.Path(tmpdir) / "brief.json"

            exit_code = brief.main([
                "--score-report",
                str(malformed),
                "--output-md",
                str(output_md),
                "--output-json",
                str(output_json),
            ])

            self.assertEqual(exit_code, 1)
            self.assertFalse(output_md.exists())
            self.assertFalse(output_json.exists())

    def test_missing_required_score_fields_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            score_path = pathlib.Path(tmpdir) / "score.json"
            score_path.write_text(json.dumps({"score_version": "signal_quality_score_v1"}), encoding="utf-8")

            with self.assertRaises(brief.BriefInputError):
                brief.build_brief(score_path, created_at=FIXED_TIME)

    def test_no_public_content_path_is_required(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_md = pathlib.Path(tmpdir) / "owner" / "brief.md"
            output_json = pathlib.Path(tmpdir) / "owner" / "brief.json"

            report = brief.run_brief(FIXTURE, output_md, output_json, created_at=FIXED_TIME)

            self.assertEqual(report["signals_reviewed"], 4)
            self.assertTrue(output_md.exists())
            self.assertTrue(output_json.exists())

    def test_output_does_not_include_seo_metadata_or_social_post_drafts(self):
        report = self.build_fixture_brief()
        serialized = json.dumps(report).lower()
        markdown = brief.render_markdown(report).lower()

        self.assertNotIn("seo_metadata", serialized)
        self.assertNotIn("social_drafts", serialized)
        self.assertNotIn("social post draft", markdown)

    def test_brief_says_do_not_publish_yet(self):
        report = self.build_fixture_brief()
        markdown = brief.render_markdown(report)

        self.assertIn("Do not publish yet.", report["recommended_next_actions"])
        self.assertIn("Do not publish yet.", markdown)

    def test_no_raw_provider_response_is_required_or_stored(self):
        report = self.build_fixture_brief()
        serialized = json.dumps(report)

        self.assertFalse(report["safety_flags"]["raw_provider_response_stored"])
        self.assertNotIn('"raw_provider_response":', serialized)


if __name__ == "__main__":
    unittest.main()
