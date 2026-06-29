import json
import pathlib
import tempfile
import unittest
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_public_signals_auto_merge_gate as gate  # noqa: E402


def forbidden_domain() -> str:
    return "https://dysonx." + "ai"


class DysonXPublicSignalsAutoMergeGateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp_dir.name)
        self.signals = self.root / "signals"
        self.slug = "critical-agent-signal"
        (self.signals / self.slug).mkdir(parents=True)
        (self.root / "index.html").write_text('<a href="/signals/">Signals</a>', encoding="utf-8")
        (self.signals / "index.html").write_text(
            f'<h1>Signals</h1><a href="/signals/{self.slug}/">Signal</a>',
            encoding="utf-8",
        )
        (self.signals / self.slug / "index.html").write_text(
            '<h1>Critical Agent Signal</h1><p>Summary-only public Signal.</p><a href="/">Home</a> <a href="/signals/">Signals</a> <a href="https://example.org/source">Source</a>',
            encoding="utf-8",
        )
        self.manifest_path = self.signals / "public_launch_manifest.json"
        self.changed_files_path = self.root / "changed_files.json"
        self.write_manifest()
        self.write_changed_files([f"signals/{self.slug}/index.html", "signals/index.html", "signals/public_launch_manifest.json"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def manifest(self, **entry_overrides):
        entry = {
            "signal_id": "sig_critical_agent",
            "slug": self.slug,
            "title": "Critical Agent Signal",
            "public_path": f"signals/{self.slug}/index.html",
            "public_url_path": f"/signals/{self.slug}/",
            "source_name": "Example Source",
            "source_url": "https://example.org/source",
            "source_priority": "Critical",
            "attribution_status": "Complete",
            "copyright_status": "Safe Summary Only",
            "quality_hint": 94,
            "ready_for_pipeline": True,
            "published": True,
            "production_publish_performed": True,
        }
        entry.update(entry_overrides)
        return {
            "launch_version": "notion_public_signals_sync_v1",
            "pages_launched": 1,
            "pages_blocked": 0,
            "launched": [entry],
            "openai_call_performed": False,
            "network_source_fetch_performed": False,
            "manual_external_deployment_performed": False,
        }

    def write_manifest(self, **entry_overrides):
        self.manifest_path.write_text(json.dumps(self.manifest(**entry_overrides), indent=2), encoding="utf-8")

    def write_changed_files(self, files):
        self.changed_files_path.write_text(json.dumps(files), encoding="utf-8")

    def run_gate(self):
        return gate.main(
            [
                "--manifest",
                str(self.manifest_path),
                "--changed-files-json",
                str(self.changed_files_path),
                "--min-quality",
                "92",
                "--required-priority",
                "Critical",
                "--require-attribution-complete",
                "--require-safe-summary-only",
            ]
        )

    def test_passes_for_critical_high_quality_complete_safe_summary_signal(self):
        self.assertEqual(self.run_gate(), 0)

    def test_critical_quality_at_least_92_complete_safe_summary_can_pass_gate(self):
        self.write_manifest(source_priority="Critical", quality_hint=92, attribution_status="Complete", copyright_status="Safe Summary Only")
        self.assertEqual(self.run_gate(), 0)

    def test_fails_when_quality_below_threshold(self):
        self.write_manifest(quality_hint=91)
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_source_priority_is_high_instead_of_critical(self):
        self.write_manifest(source_priority="High")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_attribution_is_partial_or_missing(self):
        for status in ("Partial", "Missing"):
            with self.subTest(status=status):
                self.write_manifest(attribution_status=status)
                self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_copyright_status_is_not_safe_summary_only(self):
        self.write_manifest(copyright_status="Unsafe")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_unknown_changed_file_path_exists(self):
        self.write_changed_files([f"signals/{self.slug}/index.html", "index.html"])
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_raw_body_marker_appears(self):
        (self.signals / self.slug / "index.html").write_text("full article text", encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_script_tag_appears(self):
        (self.signals / self.slug / "index.html").write_text("<script>alert(1)</script>", encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_forbidden_terms_appear(self):
        forbidden = [
            "." + "invalid",
            "." + "test/",
            "media." + "energizeos.com",
            forbidden_domain(),
            "tmp/" + "production_publish_pack",
        ]
        for term in forbidden:
            with self.subTest(term=term):
                self.write_manifest(title=term)
                self.assertNotEqual(self.run_gate(), 0)
                self.write_manifest()

    def test_fails_when_manifest_says_openai_call_performed_true(self):
        data = self.manifest()
        data["openai_call_performed"] = True
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_manifest_says_network_source_fetch_performed_true(self):
        data = self.manifest()
        data["network_source_fetch_performed"] = True
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_manifest_says_manual_external_deployment_performed_true(self):
        data = self.manifest()
        data["manual_external_deployment_performed"] = True
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_passes_only_for_allowed_signals_paths(self):
        allowed = [
            "signals/index.html",
            "signals/public_launch_manifest.json",
            f"signals/{self.slug}/index.html",
        ]
        for path in allowed:
            with self.subTest(path=path):
                self.write_changed_files([path])
                self.assertEqual(self.run_gate(), 0)


if __name__ == "__main__":
    unittest.main()
