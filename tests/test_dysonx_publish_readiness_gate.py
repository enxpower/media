import ast
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dysonx_publish_readiness_gate.py"
FIXTURES = ROOT / "tests" / "fixtures" / "publish_readiness_gate_v1"
OWNER_FEEDBACK = FIXTURES / "owner_feedback.json"
BRIEF = FIXTURES / "internal_brief.json"
SCORE_REPORT = FIXTURES / "signal_quality_score.json"
EXPECTED = FIXTURES / "expected_publish_readiness_gate_report.json"


class DysonXPublishReadinessGateTests(unittest.TestCase):
    def run_gate(self, owner_feedback=OWNER_FEEDBACK, brief=BRIEF, score_report=SCORE_REPORT):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "gate.json"
            cmd = [
                sys.executable,
                str(SCRIPT),
                "--owner-feedback",
                str(owner_feedback),
                "--brief",
                str(brief),
                "--score-report",
                str(score_report),
                "--output",
                str(output),
            ]
            result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
            report = json.loads(output.read_text(encoding="utf-8")) if output.exists() else None
            return result, report

    def write_owner_feedback(self, data):
        tmpdir = tempfile.TemporaryDirectory()
        path = pathlib.Path(tmpdir.name) / "owner_feedback.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.addCleanup(tmpdir.cleanup)
        return path

    def fixture_owner_feedback(self):
        return json.loads(OWNER_FEEDBACK.read_text(encoding="utf-8"))

    def records_by_signal_id(self, report):
        return {item["signal_id"]: item for item in report["evaluations"]}

    def test_cli_file_exists_and_supports_required_arguments(self):
        script = SCRIPT.read_text(encoding="utf-8")

        self.assertTrue(SCRIPT.exists())
        self.assertIn("--owner-feedback", script)
        self.assertIn("--brief", script)
        self.assertIn("--score-report", script)
        self.assertIn("--output", script)
        self.assertIn("argparse.ArgumentParser", script)

    def test_cli_writes_json_report_with_top_level_safety_fields(self):
        result, report = self.run_gate()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[publish-readiness-gate] wrote report:", result.stdout)
        self.assertEqual(report["gate_version"], "publish_readiness_gate_v1")
        self.assertTrue(report["no_public_publishing_performed"])
        self.assertTrue(report["no_deployment_performed"])
        self.assertTrue(report["no_openai_call_performed"])
        self.assertTrue(report["no_workflow_dispatch_performed"])
        self.assertFalse(report["public_pages_generated"])
        self.assertFalse(report["knowledge_graph_write_performed"])

    def test_fixture_report_counts_and_expected_decisions_are_deterministic(self):
        _, report = self.run_gate()
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        by_id = self.records_by_signal_id(report)

        self.assertEqual(report["signals_evaluated"], expected["signals_evaluated"])
        self.assertEqual(report["ready_count"], expected["ready_count"])
        self.assertEqual(report["blocked_count"], expected["blocked_count"])
        self.assertIn("warning_count", report)
        self.assertIn("created_at", report)
        self.assertIn("input_files", report)
        for signal_id, decision in expected["expected_decisions"].items():
            self.assertEqual(by_id[signal_id]["gate_decision"], decision)

    def test_ready_synthetic_signal_passes_but_is_not_published(self):
        _, report = self.run_gate()
        ready = self.records_by_signal_id(report)["sig_ready_synthetic_agent_eval"]

        self.assertTrue(ready["publish_readiness_gate_passed"])
        self.assertTrue(ready["ready_for_public_generation"])
        self.assertFalse(ready["public_generation_blocked"])
        self.assertFalse(ready["published"])
        self.assertFalse(ready["publication_approved"])
        self.assertEqual(ready["gate_decision"], "ready_for_public_generation")

    def test_blocked_fixture_and_owner_decision_states_have_blockers_and_actions(self):
        _, report = self.run_gate()
        by_id = self.records_by_signal_id(report)

        expected_blockers = {
            "sig_fixture_candidate_missing_public_fields": "fixture_only_not_publishable",
            "sig_needs_more_sources": "blocked_needs_more_sources",
            "sig_hold": "blocked_hold",
            "sig_needs_regeneration": "blocked_needs_regeneration",
            "sig_rejected_generic": "blocked_rejected",
        }
        for signal_id, blocker in expected_blockers.items():
            record = by_id[signal_id]
            self.assertTrue(record["public_generation_blocked"])
            self.assertFalse(record["ready_for_public_generation"])
            self.assertIn(blocker, record["blockers"])
            self.assertGreaterEqual(len(record["required_next_actions"]), 1)

    def test_missing_source_blocks(self):
        feedback = self.fixture_owner_feedback()
        feedback["records"][0].pop("source_url")
        path = self.write_owner_feedback(feedback)
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "gate.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--owner-feedback",
                    str(path),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, result.stderr)
        ready = self.records_by_signal_id(report)["sig_ready_synthetic_agent_eval"]

        self.assertIn("missing_source_url", ready["blockers"])
        self.assertEqual(ready["gate_decision"], "blocked_missing_source")

    def test_example_source_blocks_unless_fixture_mode_and_fixture_mode_still_not_publishable(self):
        feedback = self.fixture_owner_feedback()
        feedback["records"][0]["source_url"] = "https://example.org/ready"
        feedback["records"][0].pop("fixture_mode", None)
        path = self.write_owner_feedback(feedback)
        _, report = self.run_gate(owner_feedback=path)
        blocked = self.records_by_signal_id(report)["sig_ready_synthetic_agent_eval"]
        self.assertIn("example_source_without_fixture_mode", blocked["blockers"])

        fixture_record = self.records_by_signal_id(self.run_gate()[1])["sig_fixture_candidate_missing_public_fields"]
        self.assertIn("fixture_only_not_publishable", fixture_record["blockers"])
        self.assertTrue(fixture_record["fixture_only_not_publishable"])

    def test_missing_public_content_fields_block(self):
        for field in ("public_title", "public_slug", "public_summary"):
            feedback = self.fixture_owner_feedback()
            feedback["records"][0].pop(field)
            path = self.write_owner_feedback(feedback)
            _, report = self.run_gate(owner_feedback=path)
            blocked = self.records_by_signal_id(report)["sig_ready_synthetic_agent_eval"]
            self.assertIn(f"missing_{field}", blocked["blockers"])
            self.assertFalse(blocked["ready_for_public_generation"])

    def test_score_below_threshold_blocks(self):
        feedback = self.fixture_owner_feedback()
        feedback["records"][0]["score"] = 40
        path = self.write_owner_feedback(feedback)

        _, report = self.run_gate(owner_feedback=path)
        blocked = self.records_by_signal_id(report)["sig_ready_synthetic_agent_eval"]

        self.assertIn("quality_below_threshold", blocked["blockers"])
        self.assertEqual(blocked["gate_decision"], "blocked_quality_threshold")

    def test_raw_source_content_blocks(self):
        feedback = self.fixture_owner_feedback()
        feedback["records"][0]["article_body"] = "Synthetic full article text should never be in public generation input."
        path = self.write_owner_feedback(feedback)

        _, report = self.run_gate(owner_feedback=path)
        blocked = self.records_by_signal_id(report)["sig_ready_synthetic_agent_eval"]

        self.assertIn("raw_source_content_present", blocked["blockers"])
        self.assertEqual(blocked["gate_decision"], "blocked_raw_source_content")

    def test_generic_summary_and_weak_attribution_risks_block(self):
        feedback = self.fixture_owner_feedback()
        feedback["records"][0]["generic_summary_risk"] = True
        feedback["records"][0]["weak_attribution_risk"] = True
        path = self.write_owner_feedback(feedback)

        _, report = self.run_gate(owner_feedback=path)
        blocked = self.records_by_signal_id(report)["sig_ready_synthetic_agent_eval"]

        self.assertIn("generic_summary_risk", blocked["blockers"])
        self.assertIn("weak_attribution_risk", blocked["blockers"])
        self.assertEqual(blocked["gate_decision"], "blocked_risk_flags")

    def test_publication_approved_true_without_gate_logic_blocks(self):
        feedback = self.fixture_owner_feedback()
        feedback["records"][0]["publication_approved"] = True
        path = self.write_owner_feedback(feedback)

        _, report = self.run_gate(owner_feedback=path)
        blocked = self.records_by_signal_id(report)["sig_ready_synthetic_agent_eval"]

        self.assertIn("publication_approved_true_without_gate_logic", blocked["blockers"])
        self.assertFalse(blocked["publication_approved"])

    def test_each_evaluation_includes_final_decision_fields(self):
        _, report = self.run_gate()

        for record in report["evaluations"]:
            for field in (
                "publish_readiness_gate_passed",
                "ready_for_public_generation",
                "public_generation_blocked",
                "public_generation_blockers",
                "gate_decision",
                "blockers",
                "warnings",
                "required_next_actions",
                "published",
                "publication_approved",
            ):
                self.assertIn(field, record)

    def test_exit_zero_when_all_signals_are_blocked(self):
        feedback = self.fixture_owner_feedback()
        for record in feedback["records"]:
            record["selected_owner_decision"] = "hold"
            record["auto_decision"] = "hold"
            record["owner_review_status"] = "owner_hold"
        path = self.write_owner_feedback(feedback)

        result, report = self.run_gate(owner_feedback=path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["ready_count"], 0)
        self.assertEqual(report["blocked_count"], report["signals_evaluated"])

    def test_invalid_json_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad = pathlib.Path(tmpdir) / "bad.json"
            output = pathlib.Path(tmpdir) / "out.json"
            bad.write_text("{not-json", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--owner-feedback",
                    str(bad),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[publish-readiness-gate] failed:", result.stderr)

    def test_owner_feedback_only_marks_missing_dependencies_clearly(self):
        # The helper always passes optional paths, so run a dedicated owner-only command.
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "owner_only.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--owner-feedback",
                    str(OWNER_FEEDBACK),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            report = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["input_files"]["brief"], None)
        self.assertEqual(report["input_files"]["score_report"], None)
        self.assertEqual(report["signals_evaluated"], 6)

    def test_script_uses_standard_library_only(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        self.assertLessEqual(imports, {"__future__", "argparse", "json", "pathlib", "sys", "datetime", "typing", "urllib"})


if __name__ == "__main__":
    unittest.main()
