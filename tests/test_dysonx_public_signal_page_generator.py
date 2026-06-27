import ast
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dysonx_public_signal_page_generator.py"
FIXTURE = ROOT / "tests" / "fixtures" / "public_signal_page_generator_v1" / "publish_readiness_gate_report.json"


class DysonXPublicSignalPageGeneratorTests(unittest.TestCase):
    def run_generator(self, gate_report=FIXTURE):
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        output_dir = pathlib.Path(tmpdir.name) / "public_signal_pages"
        cmd = [
            sys.executable,
            str(SCRIPT),
            "--gate-report",
            str(gate_report),
            "--output-dir",
            str(output_dir),
        ]
        result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
        manifest_path = output_dir / "public_signal_pages_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
        return result, manifest, output_dir

    def test_ready_signal_generates_static_html_page(self):
        result, manifest, output_dir = self.run_generator()
        page = output_dir / "signals" / "agent-evaluation-recovery-metric" / "index.html"

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(page.exists())
        html = page.read_text(encoding="utf-8")
        self.assertIn("Agent evaluation benchmark adds recovery metric", html)
        self.assertIn("Draft Preview / Not Published", html)
        self.assertEqual(manifest["signals_generated"], 1)

    def test_blocked_signal_does_not_generate_page(self):
        _, manifest, output_dir = self.run_generator()

        blocked_page = output_dir / "signals" / "enterprise-memory-control-needs-more-sources" / "index.html"
        self.assertFalse(blocked_page.exists())
        blocked_ids = {item["signal_id"] for item in manifest["blocked"]}
        self.assertIn("sig_blocked_needs_more_sources", blocked_ids)

    def test_missing_gate_fields_block_generation(self):
        _, manifest, output_dir = self.run_generator()

        self.assertFalse((output_dir / "signals" / "missing-gate-fields" / "index.html").exists())
        missing = next(item for item in manifest["blocked"] if item["signal_id"] == "sig_missing_gate_fields")
        self.assertIn("publish_readiness_gate_not_passed", missing["blockers"])
        self.assertIn("not_ready_for_public_generation", missing["blockers"])

    def test_published_true_blocks_draft_generation(self):
        _, manifest, output_dir = self.run_generator()

        self.assertFalse((output_dir / "signals" / "published-true-should-not-generate" / "index.html").exists())
        blocked = next(item for item in manifest["blocked"] if item["signal_id"] == "sig_published_true")
        self.assertIn("already_published_true", blocked["blockers"])

    def test_publication_approved_true_is_not_required_and_does_not_generate(self):
        _, manifest, output_dir = self.run_generator()

        self.assertFalse((output_dir / "signals" / "publication-approved-true-should-not-generate" / "index.html").exists())
        blocked = next(item for item in manifest["blocked"] if item["signal_id"] == "sig_publication_approved_true")
        self.assertIn("publication_approved_true_requires_later_manual_approval_step", blocked["blockers"])
        self.assertEqual(manifest["pages"][0]["publication_approved"], False)

    def test_raw_article_body_is_not_copied(self):
        _, _, output_dir = self.run_generator()

        all_html = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.rglob("*.html"))
        self.assertNotIn("This raw article body must never appear", all_html)

    def test_source_attribution_appears(self):
        _, _, output_dir = self.run_generator()
        html = (output_dir / "signals" / "agent-evaluation-recovery-metric" / "index.html").read_text(encoding="utf-8")

        self.assertIn("Source attributed to Synthetic Research Lab benchmark note.", html)
        self.assertIn("https://source.dysonx.test/research/agent-recovery-benchmark", html)

    def test_index_page_includes_generated_signals_and_summary(self):
        _, _, output_dir = self.run_generator()
        index = output_dir / "signals" / "index.html"
        html = index.read_text(encoding="utf-8")

        self.assertIn("DysonX Public Signals Draft Preview", html)
        self.assertIn("Agent evaluation benchmark adds recovery metric", html)
        self.assertIn("Generated Signals", html)
        self.assertIn("Blocked Signals", html)
        self.assertIn("Manual Publish Approval V1 is required", html)

    def test_manifest_includes_required_safety_flags(self):
        _, manifest, _ = self.run_generator()

        self.assertEqual(manifest["generator_version"], "public_signal_page_generator_v1")
        self.assertTrue(manifest["no_public_publishing_performed"])
        self.assertTrue(manifest["no_deployment_performed"])
        self.assertTrue(manifest["no_openai_call_performed"])
        self.assertTrue(manifest["no_workflow_dispatch_performed"])
        self.assertTrue(manifest["manual_publish_approval_required"])
        self.assertFalse(manifest["production_publish_performed"])

    def test_local_preview_output_structure_is_correct(self):
        _, manifest, output_dir = self.run_generator()

        self.assertTrue((output_dir / "signals" / "index.html").exists())
        self.assertTrue((output_dir / "signals" / "agent-evaluation-recovery-metric" / "index.html").exists())
        self.assertTrue((output_dir / "public_signal_pages_manifest.json").exists())
        self.assertTrue((output_dir / "README.md").exists())
        self.assertEqual(manifest["pages"][0]["preview_path"], "signals/agent-evaluation-recovery-metric/")

    def test_cli_is_deterministic_enough_for_tests(self):
        _, first, _ = self.run_generator()
        _, second, _ = self.run_generator()

        for report in (first, second):
            report.pop("created_at", None)
            report["output_directory"] = "<output>"
            for page in report["pages"]:
                page["output_path"] = pathlib.Path(page["output_path"]).name
        self.assertEqual(first, second)

    def test_output_dir_must_be_under_tmp_when_relative(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = pathlib.Path("public_signal_pages_not_tmp")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--gate-report",
                    str(FIXTURE),
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Output directory must be under tmp/", result.stderr)

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
