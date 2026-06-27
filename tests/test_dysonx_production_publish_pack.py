import ast
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dysonx_production_publish_pack.py"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "production_publish_pack_v1"
PUBLIC_PAGES_DIR = FIXTURE_DIR / "public_signal_pages"
PUBLIC_PAGES_MANIFEST = FIXTURE_DIR / "public_signal_pages_manifest.json"
APPROVAL_REPORT = FIXTURE_DIR / "manual_publish_approval_report.json"
EXPECTED_MANIFEST = FIXTURE_DIR / "expected_production_publish_pack_manifest.json"
EXPECTED_GUARD = FIXTURE_DIR / "expected_release_guard_report.json"


def load_module():
    spec = importlib.util.spec_from_file_location("dysonx_production_publish_pack", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DysonXProductionPublishPackTests(unittest.TestCase):
    def run_pack(self, manifest=PUBLIC_PAGES_MANIFEST, approval=APPROVAL_REPORT, public_pages_dir=PUBLIC_PAGES_DIR):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        output_dir = pathlib.Path(tmpdir.name) / "production_publish_pack"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--public-pages-dir",
            str(public_pages_dir),
            "--public-pages-manifest",
            str(manifest),
            "--approval-report",
            str(approval),
            "--output-dir",
            str(output_dir),
        ]
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
        pack_manifest_path = output_dir / "production_publish_pack_manifest.json"
        guard_path = output_dir / "release_guard_report.json"
        pack_manifest = json.loads(pack_manifest_path.read_text(encoding="utf-8")) if pack_manifest_path.exists() else None
        guard = json.loads(guard_path.read_text(encoding="utf-8")) if guard_path.exists() else None
        return result, pack_manifest, guard, output_dir

    def write_json(self, data):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = pathlib.Path(tmpdir.name) / "fixture.json"
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def test_approved_for_production_pack_true_packages_page(self):
        result, manifest, _, output_dir = self.run_pack()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(manifest["pages_packaged"], 1)
        page = output_dir / "signals" / "agent-evaluation-recovery-metric" / "index.html"
        self.assertTrue(page.exists())
        html = page.read_text(encoding="utf-8")
        self.assertIn("Production Publish Candidate / Not Yet Deployed", html)
        self.assertNotIn(">Published<", html)

    def test_unapproved_page_is_blocked(self):
        _, manifest, _, _ = self.run_pack()

        blocked = next(item for item in manifest["blocked"] if item["slug"] == "unapproved-page")
        self.assertIn("not_approved_for_production_pack", blocked["blockers"])

    def test_missing_source_html_file_blocks_packaging(self):
        _, manifest, _, _ = self.run_pack()

        blocked = next(item for item in manifest["blocked"] if item["slug"] == "missing-source-html")
        self.assertIn("source_html_file_missing", blocked["blockers"])

    def test_published_true_blocks_packaging(self):
        _, manifest, _, _ = self.run_pack()

        blocked = next(item for item in manifest["blocked"] if item["slug"] == "published-true-page")
        self.assertIn("approval_published_true", blocked["blockers"])

    def test_production_publish_performed_true_blocks_packaging(self):
        _, manifest, _, _ = self.run_pack()

        blocked = next(item for item in manifest["blocked"] if item["slug"] == "production-publish-performed-page")
        self.assertIn("approval_production_publish_performed_true", blocked["blockers"])

    def test_deployed_true_blocks_packaging(self):
        _, manifest, _, _ = self.run_pack()

        blocked = next(item for item in manifest["blocked"] if item["slug"] == "deployed-true-page")
        self.assertIn("approval_deployed_true", blocked["blockers"])

    def test_no_raw_article_body_appears_in_packaged_output(self):
        _, _, _, output_dir = self.run_pack()

        html = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.rglob("*.html"))
        self.assertNotIn("This raw article body must never appear", html)
        self.assertNotIn("raw_body", html)

    def test_no_internal_review_state_appears_in_packaged_output(self):
        _, _, _, output_dir = self.run_pack()

        html = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.rglob("*.html"))
        self.assertNotIn("owner_comment", html)
        self.assertNotIn("selected_owner_decision", html)
        self.assertNotIn("review_session", html)

    def test_production_index_is_generated(self):
        _, manifest, _, output_dir = self.run_pack()

        index = output_dir / "signals" / "index.html"
        self.assertTrue(index.exists())
        html = index.read_text(encoding="utf-8")
        self.assertIn("DysonX Public Signals", html)
        self.assertIn("Production Publish Candidate / Not Yet Deployed", html)
        self.assertIn("Step 5 explicit Owner launch authorization", html)
        self.assertEqual(manifest["pages_packaged"], 1)

    def test_pack_manifest_includes_safety_flags(self):
        _, manifest, _, _ = self.run_pack()

        self.assertTrue(manifest["step_5_launch_authorization_required"])
        self.assertTrue(manifest["no_public_publishing_performed"])
        self.assertTrue(manifest["no_deployment_performed"])
        self.assertTrue(manifest["no_openai_call_performed"])
        self.assertTrue(manifest["no_workflow_dispatch_performed"])
        self.assertFalse(manifest["production_publish_performed"])
        self.assertFalse(any(item["published"] for item in manifest["packaged"]))
        self.assertFalse(any(item["production_publish_performed"] for item in manifest["packaged"]))
        self.assertFalse(any(item["deployed"] for item in manifest["packaged"]))

    def test_release_guard_passes_for_valid_fixture(self):
        _, manifest, guard, _ = self.run_pack()

        self.assertTrue(manifest["release_guard_passed"])
        self.assertTrue(guard["release_guard_passed"])
        expected = json.loads(EXPECTED_GUARD.read_text(encoding="utf-8"))
        for check, expected_value in expected["checks"].items():
            self.assertEqual(guard["checks"][check], expected_value)

    def test_release_guard_fails_if_unapproved_page_is_packaged(self):
        module = load_module()
        manifest = {
            "input_files": {"approval_report": "approval.json"},
            "packaged": [{"approved_for_production_pack": False, "packaged_page_path": "missing.html"}],
            "no_openai_call_performed": True,
            "no_workflow_dispatch_performed": True,
            "no_deployment_performed": True,
            "production_publish_performed": False,
            "step_5_launch_authorization_required": True,
        }

        checks = module.release_guard_checks(manifest, pathlib.Path("/tmp/no-such-pack"))

        self.assertFalse(checks["only_approved_pages_packaged"])
        self.assertFalse(checks["no_unapproved_pages_packaged"])

    def test_release_guard_fails_if_published_true_appears_before_launch(self):
        module = load_module()
        manifest = {
            "input_files": {"approval_report": "approval.json"},
            "packaged": [{"approved_for_production_pack": True, "published": True, "packaged_page_path": "missing.html"}],
            "no_openai_call_performed": True,
            "no_workflow_dispatch_performed": True,
            "no_deployment_performed": True,
            "production_publish_performed": False,
            "step_5_launch_authorization_required": True,
        }

        checks = module.release_guard_checks(manifest, pathlib.Path("/tmp/no-such-pack"))

        self.assertFalse(checks["no_published_true_before_launch"])

    def test_release_guard_fails_if_production_publish_performed_true_before_launch(self):
        module = load_module()
        manifest = {
            "input_files": {"approval_report": "approval.json"},
            "packaged": [{"approved_for_production_pack": True, "production_publish_performed": True, "packaged_page_path": "missing.html"}],
            "no_openai_call_performed": True,
            "no_workflow_dispatch_performed": True,
            "no_deployment_performed": True,
            "production_publish_performed": True,
            "step_5_launch_authorization_required": True,
        }

        checks = module.release_guard_checks(manifest, pathlib.Path("/tmp/no-such-pack"))

        self.assertFalse(checks["no_production_publish_performed_true"])

    def test_cli_output_is_deterministic_enough_for_fixture_comparison(self):
        _, manifest, guard, _ = self.run_pack()
        expected_manifest = json.loads(EXPECTED_MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(manifest["pages_seen"], expected_manifest["pages_seen"])
        self.assertEqual(manifest["pages_approved_for_pack"], expected_manifest["pages_approved_for_pack"])
        self.assertEqual(manifest["pages_packaged"], expected_manifest["pages_packaged"])
        self.assertEqual(manifest["pages_blocked"], expected_manifest["pages_blocked"])
        self.assertEqual([item["slug"] for item in manifest["packaged"]], expected_manifest["packaged_slugs"])
        blocked = {item["slug"]: item["blockers"] for item in manifest["blocked"]}
        for item_slug, blocker in expected_manifest["required_blockers"].items():
            self.assertIn(blocker, blocked[item_slug])
        self.assertTrue(guard["release_guard_passed"])

    def test_script_uses_standard_library_only(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        self.assertLessEqual(
            imports,
            {"__future__", "argparse", "json", "pathlib", "re", "shutil", "sys", "datetime", "html", "typing"},
        )


if __name__ == "__main__":
    unittest.main()
