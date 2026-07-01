import json
import pathlib
import unittest
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_static_preview_check as preview_check  # noqa: E402

INDEX = ROOT / "index.html"
SIGNALS_INDEX = ROOT / "signals" / "index.html"
SEED_SIGNAL_SLUG = "agentic-ai-adoption-accelerates-from-codex-usage-evidence"
SIGNAL_PAGE = ROOT / "signals" / SEED_SIGNAL_SLUG / "index.html"
LAUNCH_MANIFEST = ROOT / "signals" / "public_launch_manifest.json"


class DysonXPublicLaunchCorrectnessTests(unittest.TestCase):
    def test_homepage_status_reflects_first_public_launch(self):
        html = INDEX.read_text(encoding="utf-8")

        self.assertIn("First public Signal published", html)
        self.assertNotIn("Real publishing not enabled yet", html)

    def test_homepage_links_are_valid_public_paths_or_disabled_labels(self):
        html = INDEX.read_text(encoding="utf-8")

        self.assertIn('href="/"', html)
        self.assertIn('href="/signals/"', html)
        self.assertNotIn('href="#signals"', html)
        self.assertNotIn("https://dysonx." + "ai", html)
        self.assertNotIn("media." + "energizeos.com", html)
        self.assertNotIn('href="#"', html)
        self.assertNotIn('href=""', html)

    def test_signals_index_uses_valid_public_links(self):
        html = SIGNALS_INDEX.read_text(encoding="utf-8")

        self.assertIn('href="/"', html)
        self.assertIn(f'href="/signals/{SEED_SIGNAL_SLUG}/"', html)
        self.assertNotIn(f'href="{SEED_SIGNAL_SLUG}/"', html)
        self.assertNotIn("source.dysonx." + "invalid", html)
        self.assertNotIn("." + "invalid", html)

    def test_public_signal_page_has_basic_trust_markers(self):
        html = SIGNAL_PAGE.read_text(encoding="utf-8")

        self.assertIn("Published", html)
        self.assertIn('href="/signals/"', html)
        self.assertIn('href="/"', html)
        self.assertIn("max-width", html)

    def test_public_signal_page_does_not_expose_test_source_url(self):
        html = SIGNAL_PAGE.read_text(encoding="utf-8")

        self.assertNotIn("source.dysonx." + "test", html)
        self.assertNotIn("source.dysonx." + "invalid", html)
        self.assertNotIn(".tes" + "t/", html)
        self.assertNotIn("." + "invalid", html)
        self.assertIn("Source Attribution", html)

    def test_public_launch_manifest_remains_sanitized(self):
        text = LAUNCH_MANIFEST.read_text(encoding="utf-8")
        data = json.loads(text)

        self.assertEqual(data["pages_launched"], 5)
        self.assertGreaterEqual(data["pages_blocked"], 0)
        self.assertNotIn("blocked", data)
        self.assertNotIn("source.dysonx." + "test", text)
        self.assertNotIn(".tes" + "t/", text)
        self.assertNotIn("required_next_actions", text)
        self.assertNotIn("not_approved_for_production_pack", text)
        self.assertNotIn("tmp/" + "production_publish_pack", text)
        self.assertNotIn("current deployment host", text)
        self.assertEqual(data["source_pack_manifest"], "notion_signal_intake_public_safe_reference")
        self.assertEqual(data["source_release_guard_report"], "static_preview_link_integrity_check")
        for entry in data["launched"]:
            self.assertTrue(entry["public_url_path"].startswith("/"))
            self.assertFalse(entry["public_url_path"].startswith("http://"))
            self.assertFalse(entry["public_url_path"].startswith("https://"))

    def test_static_link_checker_passes_on_current_public_output(self):
        passed = preview_check.run_checks()

        self.assertIn("public static links are valid", passed)


if __name__ == "__main__":
    unittest.main()
