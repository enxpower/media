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
REVIEW_SESSION_DOC = ROOT / "docs" / "DYSONX_REVIEW_SESSION_SAVE_V1.md"
GUIDED_WORKFLOW_DOC = ROOT / "docs" / "DYSONX_OWNER_GUIDED_REVIEW_WORKFLOW_V1.md"
SINGLE_ACTIVE_ACTION_DOC = ROOT / "docs" / "DYSONX_OWNER_SINGLE_ACTIVE_ACTION_WORKFLOW_V1.md"


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
        app = self.read_app()

        self.assertIn('id="owner-active-task"', html)
        self.assertIn('id="active-primary-action"', html)
        self.assertIn("Generate Owner Feedback JSON", app)
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

    def test_review_session_save_ui_exists(self):
        html = self.read_index()

        for phrase in (
            "Review Session Save",
            "Load Saved Session",
            "Reset local test state",
            "Download Review Session JSON",
        ):
            self.assertIn(phrase, html)
        for element_id in (
            'id="load-session"',
            'id="clear-session"',
            'id="download-session"',
            'id="session-status"',
        ):
            self.assertIn(element_id, html)

    def test_review_session_uses_namespaced_local_storage_key(self):
        app = self.read_app()

        self.assertIn('const REVIEW_SESSION_STORAGE_KEY = "dysonx.ownerConsole.reviewSession.v1"', app)
        self.assertIn("localStorage.setItem(REVIEW_SESSION_STORAGE_KEY", app)
        self.assertIn("localStorage.getItem(REVIEW_SESSION_STORAGE_KEY", app)
        self.assertIn("localStorage.removeItem(REVIEW_SESSION_STORAGE_KEY", app)

    def test_review_session_metadata_fields_are_present(self):
        app = self.read_app()

        for field in (
            "review_session_id",
            "created_at",
            "updated_at",
            "console_version",
            "brief_id",
            "source_brief_title",
            "source_fixture",
            "total_signals",
            "system_decided_count",
            "owner_overridden_count",
            "needs_owner_attention_count",
            "saved_locally",
            "publication_approved",
        ):
            self.assertIn(field, app)
        self.assertIn('const CONSOLE_VERSION = "owner_console_single_active_action_v1"', app)
        self.assertIn("dysonx-review-", app)

    def test_review_session_persists_form_values(self):
        app = self.read_app()

        for selector in (
            ".decision-input",
            ".priority-input",
            ".comment-input",
            ".follow-input",
            ".follow-note-input",
        ):
            self.assertIn(selector, app)
        for field in (
            "selected_owner_decision",
            "priority",
            "owner_comment",
            "follow_up_required",
            "follow_up_note",
            "owner_overridden",
        ):
            self.assertIn(field, app)
        self.assertIn("function autoSaveReviewSession()", app)
        self.assertIn("autoSaveReviewSession();", app)

    def test_review_session_restore_and_saved_status_messages_exist(self):
        app = self.read_app()

        self.assertIn("Local review session restored.", app)
        self.assertIn("Saved locally. Last saved:", app)
        self.assertIn("No saved local review session found.", app)
        self.assertIn("Saved local review session cleared. System defaults restored.", app)

    def test_review_session_owner_override_can_toggle_false_again(self):
        app = self.read_app()

        self.assertIn("const ownerOverridden = ownerDecision !== defaultDecision", app)
        self.assertIn("const overridden = decision !== defaultDecision", app)
        self.assertIn('card.dataset.ownerOverridden = overridden ? "true" : "false"', app)
        self.assertIn('status.textContent = overridden ? "Owner override" : "System default decision applied. Owner can override."', app)

    def test_feedback_json_includes_review_session_metadata_and_safety_flags(self):
        app = self.read_app()

        for field in (
            "review_session_id",
            "updated_at",
            "source_brief_title",
            "brief_id",
            "total_signals",
            "system_decided_count",
            "owner_overridden_count",
            "needs_owner_attention_count",
            "auto_decision_is_not_publication_approval: true",
            "owner_feedback_is_not_publication_approval: true",
            "review_session_is_not_publication_approval: true",
            "publication_approved: false",
        ):
            self.assertIn(field, app)

    def test_session_json_download_and_clear_behavior_are_present(self):
        app = self.read_app()

        self.assertIn("function downloadSessionJson()", app)
        self.assertIn("dysonx_owner_console_review_session.json", app)
        self.assertIn("function clearSavedSession()", app)
        self.assertIn("state.restoredSession = null", app)
        self.assertIn("Reset local test state", self.read_index())

    def test_guided_workflow_stepper_exists(self):
        html = self.read_index()
        app = self.read_app()

        self.assertIn('id="workflow-stepper"', html)
        for step in (
            "Review Attention Items",
            "Confirm Auto-handled",
            "Save Session",
            "Generate Feedback",
            "Download / Copy",
        ):
            self.assertIn(step, app)
        for state in ("active", "complete", "locked"):
            self.assertIn(state, app)

    def test_current_action_banner_exists(self):
        html = self.read_index()
        app = self.read_app()

        self.assertIn('id="current-action-banner"', html)
        self.assertIn("Current action:", html)
        self.assertIn("Current action:", app)
        self.assertIn("Review this Signal or accept the system decision.", app)

    def test_single_active_task_header_exists(self):
        html = self.read_index()
        app = self.read_app()

        self.assertIn('id="owner-active-task"', html)
        self.assertIn('id="active-task-step"', html)
        self.assertIn('id="active-task-title"', html)
        self.assertIn('id="active-task-instruction"', html)
        self.assertIn('id="active-task-progress"', html)
        self.assertIn("Step 1 of 5", html)
        self.assertIn("function activeTaskModel()", app)

    def test_exactly_one_primary_action_marker_exists(self):
        html = self.read_index()
        app = self.read_app()

        self.assertEqual(html.count('data-primary-action="true"'), 1)
        self.assertIn('primary.dataset.primaryAction = "true"', app)
        self.assertIn("active_primary_action", app)

    def test_active_task_primary_action_variants_exist(self):
        app = self.read_app()

        for phrase in (
            "Accept system decision and mark done",
            "Save review session locally",
            "Generate Owner Feedback JSON",
            "Download Owner Feedback JSON",
            "Start new review / clear saved review",
        ):
            self.assertIn(phrase, app)

    def test_attention_item_guided_states_exist(self):
        app = self.read_app()

        self.assertIn("active-attention-item", app)
        self.assertIn("completed-attention-item", app)
        self.assertIn("future-attention-item", app)
        self.assertIn("Done", app)
        self.assertIn("Next", app)
        self.assertIn("Current action", app)

    def test_per_card_guided_actions_exist(self):
        app = self.read_app()

        for phrase in (
            "Accept system decision and mark done",
            "Override decision",
            "Mark done",
            "accept-system-decision",
            "override-decision",
            "mark-done",
        ):
            self.assertIn(phrase, app)
        self.assertIn("function acceptSystemDecision", app)
        self.assertIn("function overrideDecision", app)
        self.assertIn("function markAttentionDone", app)

    def test_attention_cards_collapse_when_not_active(self):
        app = self.read_app()
        styles = STYLES.read_text(encoding="utf-8")

        for phrase in (
            "completed-summary",
            "future-summary",
            "Selected decision:",
            "System suggested decision:",
            "Locked until previous item complete",
            "edit-completed-card",
        ):
            self.assertIn(phrase, app)
        self.assertIn(".review-card.completed-attention-item", styles)
        self.assertIn(".review-card.future-attention-item", styles)
        self.assertIn("display: none", styles)

    def test_auto_handled_confirmation_step_exists(self):
        html = self.read_index()
        app = self.read_app()

        self.assertIn('id="auto-handled-confirmation"', html)
        self.assertIn("These Signals already have system decisions", html)
        self.assertIn("Accept all auto-handled system decisions", html)
        self.assertIn("Review auto-handled details", html)
        self.assertIn("function acceptAllAutoHandled", app)

    def test_workflow_gates_later_actions(self):
        app = self.read_app()
        html = self.read_index()

        self.assertIn("Save unlocks after attention and auto-handled steps are complete.", html)
        self.assertIn("Feedback unlocks after session save.", html)
        self.assertIn('setButtonsDisabled(["copy-feedback", "download-feedback"], !outputsReady)', app)
        self.assertIn('state.guidedWorkflow.active_step === "save_session"', app)
        self.assertIn('completedSteps().has("save_session")', app)
        self.assertIn('completedSteps().has("generate_feedback")', app)

    def test_workflow_state_is_persisted_in_local_storage(self):
        app = self.read_app()

        for field in (
            "guided_workflow_status",
            "active_step",
            "completed_steps",
            "attention_item_statuses",
            "auto_handled_confirmed",
            "session_saved",
            "feedback_generated",
            "outputs_ready",
            "active_attention_index",
            "override_mode_for_active_item",
            "output_downloaded",
            "output_step_complete",
            "active_primary_action",
        ):
            self.assertIn(field, app)
        self.assertIn("localStorage.setItem(REVIEW_SESSION_STORAGE_KEY", app)

    def test_clear_saved_session_resets_workflow_to_step_one(self):
        app = self.read_app()

        self.assertIn("state.guidedWorkflow = defaultGuidedWorkflowState();", app)
        self.assertIn('active_step: "review_attention_items"', app)
        self.assertIn("Saved local review session cleared. System defaults restored.", app)

    def test_final_completion_panel_exists(self):
        html = self.read_index()
        app = self.read_app()

        self.assertIn('id="completion-panel"', html)
        self.assertIn("Internal review complete.", html)
        self.assertIn("Completed internal review. No public publishing occurred.", html)
        self.assertIn("Next future stage", html)
        self.assertIn("Publish Readiness Gate V1", html)
        self.assertIn("completion.hidden = !completedSteps().has(\"download_copy\")", app)

    def test_feedback_json_includes_guided_workflow_status(self):
        app = self.read_app()

        self.assertIn("guided_workflow_status", app)
        self.assertIn("completed_steps", app)
        self.assertIn("internal_review_complete", app)
        self.assertIn("single_active_action_workflow_version", app)
        self.assertIn("active_primary_action", app)
        self.assertIn("output_step_complete", app)
        self.assertIn("publication_approved: false", app)

    def test_raw_json_stays_below_guided_workflow(self):
        html = self.read_index()

        workflow_index = html.index('id="owner-active-task"')
        output_index = html.index('id="feedback-output"')
        self.assertLess(workflow_index, output_index)
        self.assertIn("Brief source and technical details", html)
        self.assertIn("<details", html)

    def test_no_duplicate_primary_export_clusters_exist(self):
        html = self.read_index()
        app = self.read_app()

        self.assertNotIn("generate-feedback-top", html)
        self.assertNotIn("generate-feedback-sticky", html)
        self.assertNotIn("export-action-bar", html)
        self.assertIn("Generate Owner Feedback JSON", app)
        self.assertEqual(html.count('data-primary-action="true"'), 1)

    def test_responsive_css_avoids_obvious_metric_wrapping(self):
        styles = STYLES.read_text(encoding="utf-8")

        self.assertIn("word-break: normal", styles)
        self.assertIn("overflow-wrap: break-word", styles)
        self.assertIn(".owner-active-task", styles)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", styles)

    def test_guided_workflow_documentation_exists(self):
        doc = GUIDED_WORKFLOW_DOC.read_text(encoding="utf-8")

        for phrase in (
            "Why Button Existence Was Not Enough",
            "Owner Guided Workflow Model",
            "Stepper States",
            "Current Action Banner",
            "Active Item Highlighting",
            "Per-Card Actions",
            "Auto-Handled Confirmation",
            "Save / Generate / Download Gating",
            "Workflow Persistence",
            "Completion State",
            "Safety Boundaries",
            "If Owner can complete a review without external explanation, proceed to Publish Readiness Gate V1.",
        ):
            self.assertIn(phrase, doc)

    def test_single_active_action_documentation_exists(self):
        doc = SINGLE_ACTIVE_ACTION_DOC.read_text(encoding="utf-8")

        for phrase in (
            "Why The Previous Guided Workflow Still Failed",
            "Single Active Action Rule",
            "Active Task Header",
            "One Primary Action Rule",
            "Collapsed Completed Cards",
            "Collapsed Future Cards",
            "Auto-Handled Confirmation Behavior",
            "Save / Feedback / Output Gating",
            "Final Completion State",
            "Responsive Usability Requirement",
            "active_primary_action",
            "If Owner can complete internal review without asking what to click next, proceed to Publish Readiness Gate V1.",
        ):
            self.assertIn(phrase, doc)

    def test_existing_docs_reference_single_active_action_constraints(self):
        guided = GUIDED_WORKFLOW_DOC.read_text(encoding="utf-8")
        review_session = REVIEW_SESSION_DOC.read_text(encoding="utf-8")

        self.assertIn("single active action console", guided)
        self.assertIn("unexplained disabled buttons are product failures", guided)
        self.assertIn("must not appear as an unstructured button cluster", review_session)

    def test_saved_review_session_safety_text_is_present(self):
        html = self.read_index()
        doc = REVIEW_SESSION_DOC.read_text(encoding="utf-8")

        self.assertIn("Saved review session is not publication approval", html)
        self.assertIn("Owner feedback is not publication approval", html)
        self.assertIn("No public publishing", html)
        self.assertIn("No OpenAI call from this page", html)
        self.assertIn("No deployment triggered by this page", html)
        self.assertIn("saved review session does not publish", doc.lower())
        self.assertIn("does not implement", doc)

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
            + REVIEW_SESSION_DOC.read_text(encoding="utf-8")
            + GUIDED_WORKFLOW_DOC.read_text(encoding="utf-8")
            + SINGLE_ACTIVE_ACTION_DOC.read_text(encoding="utf-8")
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
