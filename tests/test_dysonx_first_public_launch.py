import ast
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dysonx_first_public_launch.py"
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "first_public_launch_v1"
PACK_DIR = FIXTURE_DIR / "production_publish_pack"
PACK_MANIFEST = FIXTURE_DIR / "production_publish_pack_manifest.json"
RELEASE_GUARD = FIXTURE_DIR / "release_guard_report.json"
EXPECTED_MANIFEST = FIXTURE_DIR / "expected_public_launch_manifest.json"
AUTHORIZATION = "explicit_owner_authorization_in_step_5_prompt"


class DysonXFirstPublicLaunchTests(unittest.TestCase):
    def run_launch(self, pack_dir=PACK_DIR, pack_manifest=PACK_MANIFEST, release_guard=RELEASE_GUARD, authorization=AUTHORIZATION):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        output_root = pathlib.Path(tmpdir.name) / "public_root"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--production-pack-dir",
            str(pack_dir),
            "--pack-manifest",
            str(pack_manifest),
            "--release-guard-report",
            str(release_guard),
            "--public-output-root",
            str(output_root),
            "--owner-launch-authorization",
            authorization,
        ]
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
        manifest_path = output_root / "signals" / "public_launch_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
        return result, manifest, output_root

    def write_json(self, data):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = pathlib.Path(tmpdir.name) / "fixture.json"
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def copy_pack(self):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        pack_dir = pathlib.Path(tmpdir.name) / "production_publish_pack"
        shutil.copytree(PACK_DIR, pack_dir)
        return pack_dir

    def load_pack_manifest(self):
        return json.loads(PACK_MANIFEST.read_text(encoding="utf-8"))

    def load_release_guard(self):
        return json.loads(RELEASE_GUARD.read_text(encoding="utf-8"))

    def test_valid_pack_release_guard_and_authorization_launches_page(self):
        result, manifest, output_root = self.run_launch()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(manifest["pages_launched"], 1)
        launched_page = output_root / "signals" / "agent-evaluation-recovery-metric" / "index.html"
        self.assertTrue(launched_page.exists())
        self.assertTrue((output_root / "signals" / "index.html").exists())
        html = launched_page.read_text(encoding="utf-8")
        self.assertIn("Published", html)
        self.assertNotIn("Production Publish Candidate / Not Yet Deployed", html)
        self.assertNotIn("noindex,nofollow", html)

    def test_missing_owner_launch_authorization_blocks_launch(self):
        result, manifest, output_root = self.run_launch(authorization="missing")

        self.assertEqual(result.returncode, 2)
        self.assertIsNone(manifest)
        self.assertFalse((output_root / "signals" / "agent-evaluation-recovery-metric" / "index.html").exists())
        self.assertIn("missing_owner_launch_authorization", result.stderr)

    def test_release_guard_passed_false_blocks_launch(self):
        guard = self.load_release_guard()
        guard["release_guard_passed"] = False
        guard["blockers"] = ["fixture_release_guard_failure"]
        release_guard = self.write_json(guard)

        result, manifest, _ = self.run_launch(release_guard=release_guard)

        self.assertEqual(result.returncode, 2)
        self.assertIsNone(manifest)
        self.assertIn("release_guard_not_passed", result.stderr)

    def test_missing_packaged_file_blocks_launch(self):
        manifest = self.load_pack_manifest()
        manifest["packaged"][0]["packaged_page_path"] = "tests/fixtures/first_public_launch_v1/production_publish_pack/signals/missing/index.html"
        pack_manifest = self.write_json(manifest)

        result, launch_manifest, _ = self.run_launch(pack_manifest=pack_manifest)

        self.assertEqual(result.returncode, 2)
        self.assertIsNone(launch_manifest)
        self.assertIn("no_pages_launched", result.stderr)

    def test_no_approved_packaged_pages_blocks_launch(self):
        manifest = self.load_pack_manifest()
        manifest["packaged"] = []
        manifest["pages_packaged"] = 0
        pack_manifest = self.write_json(manifest)

        result, launch_manifest, _ = self.run_launch(pack_manifest=pack_manifest)

        self.assertEqual(result.returncode, 2)
        self.assertIsNone(launch_manifest)
        self.assertIn("no_approved_packaged_pages", result.stderr)

    def test_raw_article_body_marker_blocks_launch(self):
        pack_dir = self.copy_pack()
        page = pack_dir / "signals" / "agent-evaluation-recovery-metric" / "index.html"
        page.write_text(page.read_text(encoding="utf-8") + "\nraw_body\n", encoding="utf-8")
        manifest = self.load_pack_manifest()
        manifest["packaged"][0]["packaged_page_path"] = str(page)
        pack_manifest = self.write_json(manifest)

        result, launch_manifest, _ = self.run_launch(pack_dir=pack_dir, pack_manifest=pack_manifest)

        self.assertEqual(result.returncode, 2)
        self.assertIsNone(launch_manifest)
        self.assertIn("no_pages_launched", result.stderr)

    def test_internal_review_state_marker_blocks_launch(self):
        pack_dir = self.copy_pack()
        page = pack_dir / "signals" / "agent-evaluation-recovery-metric" / "index.html"
        page.write_text(page.read_text(encoding="utf-8") + "\nowner_comment\n", encoding="utf-8")
        manifest = self.load_pack_manifest()
        manifest["packaged"][0]["packaged_page_path"] = str(page)
        pack_manifest = self.write_json(manifest)

        result, launch_manifest, _ = self.run_launch(pack_dir=pack_dir, pack_manifest=pack_manifest)

        self.assertEqual(result.returncode, 2)
        self.assertIsNone(launch_manifest)
        self.assertIn("no_pages_launched", result.stderr)

    def test_launch_manifest_sets_published_true_only_for_launched_pages(self):
        _, manifest, _ = self.run_launch()

        self.assertTrue(all(item["published"] is True for item in manifest["launched"]))
        self.assertFalse(any(item.get("published") is True for item in manifest["blocked"]))

    def test_launch_manifest_sets_production_publish_performed_true_only_for_launched_pages(self):
        _, manifest, _ = self.run_launch()

        self.assertTrue(all(item["production_publish_performed"] is True for item in manifest["launched"]))
        self.assertFalse(any(item.get("production_publish_performed") is True for item in manifest["blocked"]))

    def test_launch_manifest_confirms_no_openai_call(self):
        _, manifest, _ = self.run_launch()

        self.assertFalse(manifest["openai_call_performed"])

    def test_launch_manifest_confirms_no_workflow_dispatch(self):
        _, manifest, _ = self.run_launch()

        self.assertFalse(manifest["workflow_dispatch_performed"])

    def test_launch_manifest_confirms_no_manual_external_deployment(self):
        _, manifest, _ = self.run_launch()

        self.assertFalse(manifest["manual_external_deployment_performed"])

    def test_cli_output_is_deterministic_enough_for_fixture_comparison(self):
        _, manifest, _ = self.run_launch()
        expected = json.loads(EXPECTED_MANIFEST.read_text(encoding="utf-8"))

        self.assertEqual(manifest["pages_launched"], expected["pages_launched"])
        self.assertEqual(manifest["pages_blocked"], expected["pages_blocked"])
        self.assertEqual([item["slug"] for item in manifest["launched"]], expected["launched_slugs"])
        self.assertEqual([item["slug"] for item in manifest["blocked"]], expected["blocked_slugs"])
        self.assertEqual(manifest["release_guard_passed"], expected["release_guard_passed"])
        self.assertEqual(manifest["openai_call_performed"], expected["openai_call_performed"])
        self.assertEqual(manifest["workflow_dispatch_performed"], expected["workflow_dispatch_performed"])
        self.assertEqual(manifest["manual_external_deployment_performed"], expected["manual_external_deployment_performed"])
        self.assertEqual(manifest["social_distribution_performed"], expected["social_distribution_performed"])
        self.assertEqual(manifest["newsletter_distribution_performed"], expected["newsletter_distribution_performed"])

    def test_script_uses_standard_library_only(self):
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])

        allowed = {"__future__", "argparse", "json", "pathlib", "shutil", "sys", "datetime", "typing"}
        self.assertLessEqual(imports, allowed)


if __name__ == "__main__":
    unittest.main()
