import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SIGNAL_PAGE = ROOT / "signals" / "agent-evaluation-recovery-metric" / "index.html"
LAUNCH_MANIFEST = ROOT / "signals" / "public_launch_manifest.json"


class DysonXPublicLaunchCorrectnessTests(unittest.TestCase):
    def test_homepage_status_reflects_first_public_launch(self):
        html = INDEX.read_text(encoding="utf-8")

        self.assertIn("First public Signal published", html)
        self.assertNotIn("Real publishing not enabled yet", html)

    def test_public_signal_page_has_basic_trust_markers(self):
        html = SIGNAL_PAGE.read_text(encoding="utf-8")

        self.assertIn("Published", html)
        self.assertIn('href="/signals/"', html)
        self.assertIn("max-width", html)

    def test_public_signal_page_does_not_expose_test_source_url(self):
        html = SIGNAL_PAGE.read_text(encoding="utf-8")

        self.assertNotIn("source.dysonx.test", html)
        self.assertNotIn(".test/", html)

    def test_public_launch_manifest_remains_sanitized(self):
        text = LAUNCH_MANIFEST.read_text(encoding="utf-8")
        data = json.loads(text)

        self.assertEqual(data["pages_launched"], 1)
        self.assertEqual(data["pages_blocked"], 6)
        self.assertNotIn("blocked", data)
        self.assertNotIn("source.dysonx.test", text)
        self.assertNotIn(".test/", text)
        self.assertNotIn("required_next_actions", text)
        self.assertNotIn("not_approved_for_production_pack", text)


if __name__ == "__main__":
    unittest.main()
