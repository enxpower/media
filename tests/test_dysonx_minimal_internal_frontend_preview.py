import json
import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PREVIEW = ROOT / "internal" / "dysonx-owner-intelligence-preview"
INDEX = PREVIEW / "index.html"
APP = PREVIEW / "app.js"
STYLES = PREVIEW / "styles.css"
FIXTURE = PREVIEW / "brief_fixture.json"
DOC = ROOT / "docs" / "DYSONX_MINIMAL_INTERNAL_FRONTEND_PREVIEW_V1.md"


class DysonXMinimalInternalFrontendPreviewTests(unittest.TestCase):
    def read_index(self) -> str:
        return INDEX.read_text(encoding="utf-8")

    def read_app(self) -> str:
        return APP.read_text(encoding="utf-8")

    def load_fixture(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_preview_fixture_can_be_loaded(self):
        fixture = self.load_fixture()

        self.assertEqual(fixture["brief_version"], "internal_intelligence_brief_v1")
        self.assertGreaterEqual(len(fixture["owner_review_queue"]), 1)

    def test_required_sections_render_from_static_markup(self):
        html = self.read_index()

        for section in (
            "Brief Metadata",
            "Executive Summary",
            "Decision-Grade Candidates",
            "Useful Signals Requiring Review",
            "Blocked / Low-Value Signals",
            "Owner Review Queue",
            "Safety Boundary",
        ):
            self.assertIn(section, html)

    def test_owner_decision_values_are_limited_to_allowed_values(self):
        app = self.read_app()

        allowed = {
            "approve_for_future_publish_readiness_review",
            "request_more_sources",
            "request_regeneration",
            "reject",
            "hold",
        }
        match = re.search(r"const ALLOWED_DECISIONS = \[(.*?)\];", app, re.S)
        self.assertIsNotNone(match)
        actual = set(re.findall(r'"([^"]+)"', match.group(1)))
        self.assertEqual(actual, allowed)

    def test_priority_values_are_limited_to_allowed_values(self):
        app = self.read_app()

        match = re.search(r"const ALLOWED_PRIORITIES = \[(.*?)\];", app, re.S)
        self.assertIsNotNone(match)
        actual = set(re.findall(r'"([^"]+)"', match.group(1)))
        self.assertEqual(actual, {"high", "medium", "low"})

    def test_generated_feedback_json_includes_required_top_level_fields(self):
        app = self.read_app()

        for field in (
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
        ):
            self.assertIn(field, app)

    def test_generated_feedback_records_include_required_fields(self):
        app = self.read_app()

        for field in (
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
        ):
            self.assertIn(field, app)

    def test_approve_for_future_review_does_not_imply_publish_readiness(self):
        app = self.read_app()

        self.assertIn(
            "owner_approved_for_later_publish_readiness_review_only",
            app,
        )
        self.assertIn("later_publish_readiness_review_required", app)
        self.assertIn("publish_readiness_enabled: false", app)
        self.assertIn("Do not publish yet.", app)

    def test_safety_boundary_text_is_present(self):
        html = self.read_index()

        for phrase in (
            "Internal preview only",
            "Not publish-ready",
            "No public publishing",
            "No deployment",
            "No OpenAI call",
            "No Knowledge Graph writes",
            "No Prediction Engine work",
            "No Confidence Calibration",
            "No Correlation",
        ):
            self.assertIn(phrase, html)

    def test_no_openai_api_key_requirement_or_network_api_behavior(self):
        combined = self.read_index() + self.read_app() + DOC.read_text(encoding="utf-8")

        self.assertIn("does not require `OPENAI_API_KEY`", combined)
        self.assertNotIn("process.env", combined)
        self.assertNotIn("OPENAI_API_KEY =", combined)
        self.assertNotIn("XMLHttpRequest", combined)
        self.assertNotIn("axios", combined)
        self.assertNotIn("httpx", combined)
        self.assertNotIn("requests", combined)

    def test_no_public_publishing_social_kg_prediction_deployment_behavior(self):
        app = self.read_app()

        for flag in (
            "public_content_generated: false",
            "website_pages_written: false",
            "social_posting_performed: false",
            "knowledge_graph_write_performed: false",
            "prediction_engine_performed: false",
            "deployment_performed: false",
            "workflow_dispatched: false",
        ):
            self.assertIn(flag, app)
        self.assertNotIn("seo_metadata", app)
        self.assertNotIn("social_draft", app)

    def test_preview_avoids_horizontal_overflow(self):
        css = STYLES.read_text(encoding="utf-8")

        self.assertIn("overflow-x: hidden", css)
        self.assertIn("minmax(0, 1fr)", css)
        self.assertIn("overflow-wrap: anywhere", css)

    def test_preview_is_not_under_public_static_output(self):
        relative = INDEX.relative_to(ROOT).as_posix()

        self.assertTrue(relative.startswith("internal/"))
        self.assertFalse(relative.startswith("static/"))
        self.assertFalse(relative.startswith("downloads/"))


if __name__ == "__main__":
    unittest.main()
