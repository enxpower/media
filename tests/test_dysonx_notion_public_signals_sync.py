import json
import pathlib
import shutil
import tempfile
import unittest
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_notion_public_signals_sync as sync  # noqa: E402


def eligible_record(**overrides):
    record = {
        "Signal ID": "sig_notion_agent_eval",
        "Signal Title": "Notion approved agent reliability Signal",
        "Slug": "notion-agent-reliability",
        "Summary": "A Notion-approved summary-only Signal about agent reliability evaluation.",
        "Why This Matters": "Agent reliability metrics affect whether agentic systems can be trusted for longer tasks.",
        "AGI Relevance": "Agents and evaluation",
        "Source URL": "https://example.org/agent-reliability",
        "Source Label": "Example Research Source",
        "Source Priority": "Critical",
        "Ready for Pipeline": True,
        "Published": True,
        "Attribution Status": "Complete",
        "Copyright Status": "Safe Summary Only",
        "Quality Hint": 91,
        "Risk Notes": "Summary-only treatment.",
        "Watch Next": "Watch whether this metric appears in standard agent evaluations.",
        "Tags": ["Agents", "Evaluation"],
    }
    record.update(overrides)
    return record


class DysonXNotionPublicSignalsSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp_dir.name)
        shutil.copytree(ROOT / "signals", self.root / "signals")

    def tearDown(self):
        self.temp_dir.cleanup()

    def read_output(self) -> str:
        return "\n".join(path.read_text(encoding="utf-8") for path in sorted((self.root / "signals").rglob("*")) if path.is_file())

    def test_eligible_row_generates_page(self):
        manifest = sync.sync_records([eligible_record()], self.root, refreshed_at="2026-06-27T00:00:00Z")

        page = self.root / "signals" / "notion-agent-reliability" / "index.html"
        self.assertTrue(page.exists())
        html = page.read_text(encoding="utf-8")
        self.assertIn("Notion approved agent reliability Signal", html)
        self.assertIn("https://example.org/agent-reliability", html)
        self.assertEqual(manifest["openai_call_performed"], False)
        self.assertEqual(manifest["source_scraping_performed"], False)

    def test_row_with_missing_attribution_does_not_generate_page(self):
        manifest = sync.sync_records([eligible_record(**{"Attribution Status": "Incomplete"})], self.root)

        self.assertFalse((self.root / "signals" / "notion-agent-reliability" / "index.html").exists())
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_row_with_raw_body_blocked_does_not_generate_page(self):
        manifest = sync.sync_records([eligible_record(**{"Raw Body Status": "Raw Body Blocked"})], self.root)

        self.assertFalse((self.root / "signals" / "notion-agent-reliability" / "index.html").exists())
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_output_uses_relative_public_paths(self):
        sync.sync_records([eligible_record()], self.root)
        manifest = json.loads((self.root / "signals" / "public_launch_manifest.json").read_text(encoding="utf-8"))

        public_paths = [entry["public_url_path"] for entry in manifest["launched"]]
        self.assertIn("/signals/notion-agent-reliability/", public_paths)
        for path in public_paths:
            self.assertTrue(path.startswith("/"))
            self.assertFalse(path.startswith("http://"))
            self.assertFalse(path.startswith("https://"))

    def test_output_does_not_contain_forbidden_public_terms(self):
        sync.sync_records([eligible_record()], self.root)
        text = self.read_output()

        forbidden = [
            "." + "test/",
            "." + "invalid",
            "tmp/" + "production_publish_pack",
            "media." + "energizeos.com",
            "https://dysonx." + "ai",
        ]
        for term in forbidden:
            self.assertNotIn(term, text)

    def test_unsafe_source_url_is_blocked(self):
        manifest = sync.sync_records([eligible_record(**{"Source URL": "https://source.dysonx." + "invalid/research"})], self.root)

        self.assertFalse((self.root / "signals" / "notion-agent-reliability" / "index.html").exists())
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_manifest_never_sets_openai_call_performed_true(self):
        manifest = sync.sync_records([eligible_record()], self.root)

        self.assertIs(manifest["openai_call_performed"], False)
        self.assertIs(manifest["source_scraping_performed"], False)
        self.assertIs(manifest["network_source_fetch_performed"], False)
        self.assertIs(manifest["raw_article_body_copied"], False)

    def test_manifest_includes_auto_merge_gate_fields(self):
        manifest = sync.sync_records([eligible_record(**{"Quality Hint": 94})], self.root)
        entry = next(item for item in manifest["launched"] if item["slug"] == "notion-agent-reliability")

        self.assertEqual(entry["source_name"], "Example Research Source")
        self.assertEqual(entry["source_url"], "https://example.org/agent-reliability")
        self.assertEqual(entry["source_priority"], "Critical")
        self.assertEqual(entry["attribution_status"], "Complete")
        self.assertEqual(entry["copyright_status"], "Safe Summary Only")
        self.assertEqual(entry["quality_hint"], 94)
        self.assertIs(entry["ready_for_pipeline"], True)
        self.assertIs(entry["published"], True)


if __name__ == "__main__":
    unittest.main()
