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
WORKFLOW_COMPRESSION_DOC = ROOT / "docs" / "DYSONX_OWNER_CONSOLE_WORKFLOW_COMPRESSION_V2.md"


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

    def test_console_displays_auto_decision(self):
        html = self.read_index()
        app = self.read_app()
        fixture = self.load_fixture()

        self.assertIn("Auto Decision", app)
        self.assertIn("auto_decision", app)
        self.assertIn("Auto Decision is not publication approval", html)
        for record in (
            fixture["decision_grade_candidates"]
            + fixture["useful_review_queue"]
            + fixture["blocked_or_low_value"]
        ):
            self.assertIn("auto_decision", record)
            self.assertIn("decision_label", record)

    def test_console_defaults_controls_from_auto_decision(self):
        app = self.read_app()

        expected = {
            "auto_reject": "reject",
            "needs_more_sources": "request_more_sources",
            "needs_regeneration": "request_regeneration",
            "hold": "hold",
            "candidate_for_publish_readiness_review": "approve_for_future_publish_readiness_review",
        }
        for auto_decision, owner_decision in expected.items():
            self.assertIn(f"{auto_decision}: \"{owner_decision}\"", app)
        self.assertIn("ownerDecisionDefault(detail)", app)

    def test_console_uses_human_readable_action_labels(self):
        app = self.read_app()

        for label in (
            "Review for later readiness",
            "Candidate for later readiness review",
            "Needs human review",
            "Regenerate analysis",
            "Reject / blocked",
            "Reject automatically",
            "Need more sources",
            "Hold",
        ):
            self.assertIn(label, app)
        self.assertIn("humanAction(detail.auto_decision || detail.action || detail.recommended_action)", app)

    def test_console_shows_automation_aware_status_model(self):
        html = self.read_index()
        app = self.read_app()

        self.assertIn("Owner Work Summary", html)
        self.assertIn('id="workflow-status"', html)
        self.assertIn("System-decided:", app)
        self.assertIn("Owner-overridden:", app)
        self.assertIn("Needs Owner attention:", app)
        self.assertIn("Total Signals:", app)
        self.assertNotIn("Reviewed:", html)
        self.assertNotIn("Pending:", html)
        self.assertIn("System default decision applied. Owner can override.", app)

    def test_feedback_action_is_prominent_near_workflow(self):
        html = self.read_index()

        self.assertIn('id="generate-feedback-top"', html)
        self.assertIn('id="generate-feedback-sticky"', html)
        self.assertIn('id="copy-feedback-sticky"', html)
        self.assertIn('id="download-feedback-sticky"', html)
        self.assertIn("Review decisions", html)

    def test_owner_decision_queue_cards_include_score_values(self):
        app = self.read_app()

        start = app.index("function compactSignalCard(detail, index)")
        end = app.index("function renderReviewQueue(brief)")
        queue_renderer = app[start:end]
        self.assertIn('["Score", scoreText(detail)]', queue_renderer)

    def test_owner_decision_queue_keeps_context_fields_visible(self):
        app = self.read_app()

        start = app.index("function compactSignalCard(detail, index)")
        end = app.index("function renderReviewQueue(brief)")
        queue_renderer = app[start:end]
        for field in (
            '["Auto Decision", autoDecisionLabel(detail)]',
            '["Score", scoreText(detail)]',
            '["Tier", tierLabel(detail.tier || detail.quality_tier)]',
            '["Risk summary", shortText(riskSummary(detail), 150), risks(detail).length ? "risk" : ""]',
            '["Missing fields", compactList(detail.missing_fields)]',
            '["Why it matters", shortText(detail.why_it_matters, 160)]',
            '["Watch next", shortText(detail.watch_next, 160)]',
        ):
            self.assertIn(field, queue_renderer)

    def test_signals_are_grouped_by_work_category(self):
        html = self.read_index()
        app = self.read_app()

        self.assertIn("Needs Owner Attention", html)
        self.assertIn("Auto-handled", html)
        self.assertIn('id="needs-owner-attention"', html)
        self.assertIn('id="auto-handled"', html)
        self.assertIn("const attention = records.filter(isOwnerAttention)", app)
        self.assertIn("const autoHandled = records.filter", app)

    def test_blocked_low_value_is_compact_by_default(self):
        html = self.read_index()
        app = self.read_app()

        self.assertIn("Blocked / Low-value", html)
        self.assertIn("compact-list", html)
        self.assertIn('el("article", "compact-card")', app)
        self.assertIn("isBlockedLowValue", app)

    def test_full_technical_details_are_expandable(self):
        html = self.read_index()
        app = self.read_app()

        self.assertIn("Brief source and technical details", html)
        self.assertIn('details.className = "signal-details"', app)
        self.assertIn('summary.textContent = "Show details"', app)
        self.assertIn('["Raw auto decision", detail.auto_decision]', app)

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
            "auto_decision",
            "system_default_owner_decision",
            "selected_owner_decision",
            "owner_overridden",
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
        self.assertIn("publication_approved: false", app)
        self.assertIn("Do not publish yet.", app)
        self.assertIn("This is not publishing approval.", app)
        self.assertIn("This is not publication approval.", app)

    def test_owner_override_remains_possible(self):
        app = self.read_app()

        self.assertIn("Owner can override", app)
        self.assertIn("owner_override_allowed: true", app)
        self.assertIn("markOwnerConfirmed", app)
        self.assertIn('card.dataset.ownerOverridden = overridden ? "true" : "false"', app)
        self.assertIn('overridden ? "Owner override"', app)

    def test_feedback_json_includes_all_signals_with_system_defaults(self):
        app = self.read_app()

        self.assertIn("return allQueueDetails(state.brief).map", app)
        self.assertIn("const defaultDecision = card?.dataset.systemDefaultOwnerDecision || ownerDecisionDefault(detail)", app)
        self.assertIn("const ownerDecision = card?.querySelector(\".decision-input\").value || defaultDecision", app)
        self.assertIn("owner_overridden: ownerOverridden", app)

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
            + WORKFLOW_COMPRESSION_DOC.read_text(encoding="utf-8")
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
