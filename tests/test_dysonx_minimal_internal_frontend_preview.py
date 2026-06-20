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
PREVIEW_DOC = ROOT / "docs" / "DYSONX_MINIMAL_INTERNAL_FRONTEND_PREVIEW_V1.md"
LAUNCH_PLAN = ROOT / "docs" / "DYSONX_OWNER_CONSOLE_LAUNCH_PLAN.md"


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

    def test_product_console_headings_are_visible(self):
        html = self.read_index()

        for phrase in (
            "DysonX Owner Intelligence Console",
            "Today’s AGI Signal Brief",
            "Top Signal",
            "Owner Decision Queue",
            "Blocked / Low-value",
            "Safety Status",
        ):
            self.assertIn(phrase, html)

    def test_raw_tier_counts_json_is_not_primary_summary(self):
        html = self.read_index()
        app = self.read_app()

        self.assertNotIn("raw tier_counts", html)
        self.assertNotIn("JSON.stringify(brief.tier_counts", app)
        for label in (
            "Decision-grade",
            "Useful review",
            "Needs work",
            "Rejected / blocked",
        ):
            self.assertIn(label, app)

    def test_fixture_includes_owner_judgment_fields(self):
        fixture = self.load_fixture()
        records = (
            fixture["decision_grade_candidates"]
            + fixture["useful_review_queue"]
            + fixture["blocked_or_low_value"]
        )

        for record in records:
            for field in (
                "title",
                "source_url",
                "source_authority",
                "agi_capability",
                "entities",
                "executive_takeaway",
                "why_it_matters",
                "watch_next",
                "score",
                "tier",
                "risk_summary",
                "missing_fields",
                "recommended_action",
            ):
                self.assertIn(field, record)
                self.assertNotEqual(record[field], None)

    def test_user_facing_decision_labels_map_to_allowed_internal_values(self):
        app = self.read_app()

        expected = {
            "Approve for later review": "approve_for_future_publish_readiness_review",
            "Need more sources": "request_more_sources",
            "Regenerate analysis": "request_regeneration",
            "Reject": "reject",
            "Hold": "hold",
        }
        for label, value in expected.items():
            self.assertIn(f'label: "{label}"', app)
            self.assertIn(f'value: "{value}"', app)

        match = re.search(r"const ALLOWED_DECISIONS = DECISION_OPTIONS\.map", app)
        self.assertIsNotNone(match)

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

    def test_feedback_json_generation_keeps_publish_readiness_disabled(self):
        app = self.read_app()

        self.assertIn("owner_approved_for_later_publish_readiness_review_only", app)
        self.assertIn("later_publish_readiness_review_required", app)
        self.assertIn("publish_readiness_enabled: false", app)
        self.assertIn("Do not publish yet.", app)
        self.assertIn("This is not publishing approval.", app)

    def test_safety_boundary_text_is_present(self):
        html = self.read_index()

        for phrase in (
            "Internal owner console only",
            "Not publish-ready",
            "No public publishing",
            "No deployment triggered by this page",
            "No OpenAI call from this page",
            "No KG writes",
            "No Prediction Engine",
        ):
            self.assertIn(phrase, html)

    def test_no_openai_api_key_requirement_or_network_api_behavior(self):
        combined = (
            self.read_index()
            + self.read_app()
            + PREVIEW_DOC.read_text(encoding="utf-8")
            + LAUNCH_PLAN.read_text(encoding="utf-8")
        )

        self.assertIn("does not require `OPENAI_API_KEY`", combined)
        self.assertNotIn("process.env", combined)
        self.assertNotIn("OPENAI" + "_API_KEY =", combined)
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
            "notion_mutation_performed: false",
            "live_github_api_used: false",
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
