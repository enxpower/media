import ast
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dysonx_manual_publish_approval.py"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "manual_publish_approval_v1"
MANIFEST = FIXTURE_DIR / "public_signal_pages_manifest.json"
APPROVAL_INPUT = FIXTURE_DIR / "manual_publish_approval_input.json"
EXPECTED = FIXTURE_DIR / "expected_manual_publish_approval_report.json"


class DysonXManualPublishApprovalTests(unittest.TestCase):
    def run_approval(self, manifest=MANIFEST, approval_input=APPROVAL_INPUT):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        output = pathlib.Path(tmpdir.name) / "manual_publish_approval_report.json"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--manifest",
            str(manifest),
            "--approval-input",
            str(approval_input),
            "--output",
            str(output),
        ]
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
        report = json.loads(output.read_text(encoding="utf-8")) if output.exists() else None
        return result, report

    def write_fixture(self, data):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = pathlib.Path(tmpdir.name) / "input.json"
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def test_valid_generated_draft_page_approve_creates_approved_entry(self):
        result, report = self.run_approval()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["pages_approved"], 1)
        approved = report["approved"][0]
        self.assertEqual(approved["slug"], "agent-evaluation-recovery-metric")
        self.assertTrue(approved["approved_for_production_pack"])
        self.assertFalse(approved["published"])
        self.assertFalse(approved["production_publish_performed"])

    def test_hold_decision_blocks_approval(self):
        _, report = self.run_approval()

        hold = next(item for item in report["blocked"] if item["slug"] == "agent-evaluation-recovery-metric" and item["decision"] == "hold")
        self.assertIn("decision_not_approve_for_production_pack", hold["blockers"])

    def test_reject_decision_blocks_approval(self):
        _, report = self.run_approval()

        rejected = next(item for item in report["blocked"] if item["slug"] == "agent-evaluation-recovery-metric" and item["decision"] == "reject")
        self.assertIn("decision_not_approve_for_production_pack", rejected["blockers"])

    def test_unknown_slug_blocks_approval(self):
        _, report = self.run_approval()

        unknown = next(item for item in report["blocked"] if item["slug"] == "unknown-slug")
        self.assertIn("page_not_found_in_generator_manifest", unknown["blockers"])

    def test_missing_owner_identity_blocks_approval(self):
        data = json.loads(APPROVAL_INPUT.read_text(encoding="utf-8"))
        data["owner"] = {"name": "", "role": "Owner"}

        _, report = self.run_approval(approval_input=self.write_fixture(data))

        self.assertEqual(report["pages_approved"], 0)
        self.assertTrue(all("missing_owner_identity" in item["blockers"] for item in report["blocked"]))

    def test_missing_approved_at_blocks_approval(self):
        data = json.loads(APPROVAL_INPUT.read_text(encoding="utf-8"))
        data["approved_at"] = ""

        _, report = self.run_approval(approval_input=self.write_fixture(data))

        self.assertEqual(report["pages_approved"], 0)
        self.assertTrue(all("missing_approved_at" in item["blockers"] for item in report["blocked"]))

    def test_published_true_blocks_approval(self):
        _, report = self.run_approval()

        blocked = next(item for item in report["blocked"] if item["slug"] == "published-true-page")
        self.assertIn("published_true_blocks_manual_approval", blocked["blockers"])

    def test_production_publish_performed_true_blocks_approval(self):
        _, report = self.run_approval()

        blocked = next(item for item in report["blocked"] if item["slug"] == "production-publish-performed-page")
        self.assertIn("page_production_publish_performed_true", blocked["blockers"])

    def test_approval_report_never_sets_published_true(self):
        _, report = self.run_approval()

        self.assertFalse(any(item.get("published") is True for item in report["approved"]))
        self.assertFalse(report["production_publish_performed"])

    def test_approval_report_never_sets_production_publish_performed_true(self):
        _, report = self.run_approval()

        self.assertFalse(any(item.get("production_publish_performed") is True for item in report["approved"]))
        self.assertFalse(report["production_publish_performed"])

    def test_report_includes_required_safety_flags(self):
        _, report = self.run_approval()

        self.assertEqual(report["approval_version"], "manual_publish_approval_v1")
        self.assertTrue(report["manual_publish_approval_completed"])
        self.assertTrue(report["no_public_publishing_performed"])
        self.assertTrue(report["no_deployment_performed"])
        self.assertTrue(report["no_openai_call_performed"])
        self.assertTrue(report["no_workflow_dispatch_performed"])
        self.assertFalse(report["production_publish_performed"])
        self.assertTrue(report["production_pack_required"])

    def test_cli_output_matches_expected_fixture_without_timestamp_paths(self):
        _, report = self.run_approval()
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))

        self.assertEqual(report["pages_seen"], expected["pages_seen"])
        self.assertEqual(report["pages_approved"], expected["pages_approved"])
        self.assertEqual(report["pages_blocked"], expected["pages_blocked"])
        self.assertEqual([item["slug"] for item in report["approved"]], expected["approved_slugs"])
        blocked = {f"{item['slug']}:{item['decision']}": item["blockers"] for item in report["blocked"]}
        for key, blocker in expected["blocked_expectations"].items():
            self.assertIn(blocker, blocked[key])

    def test_blocked_generator_signal_cannot_be_approved(self):
        _, report = self.run_approval()

        blocked = next(item for item in report["blocked"] if item["slug"] == "blocked-by-generator")
        self.assertIn("signal_was_blocked_by_generator", blocked["blockers"])

    def test_script_uses_standard_library_only(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        self.assertLessEqual(imports, {"__future__", "argparse", "json", "pathlib", "sys", "datetime", "typing"})


if __name__ == "__main__":
    unittest.main()
