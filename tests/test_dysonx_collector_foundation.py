import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_collector_foundation as collector


SOURCE_STORE = ROOT / "tests" / "fixtures" / "source_sync_store_v1.json"


class DysonXCollectorFoundationTests(unittest.TestCase):
    def setUp(self):
        self.sources = collector.load_source_store(SOURCE_STORE)
        self.base_dir = ROOT

    def test_collector_selection(self):
        selected = {source["id"]: collector.select_collector(source) for source in self.sources}

        self.assertEqual(selected["source_openai_rss"], "rss")
        self.assertEqual(selected["source_manual_policy"], "manual_url")
        self.assertEqual(selected["source_github_release"], "github_release_fixture")

    def test_rss_fixture_parsing(self):
        source = self.sources[0]
        items = collector.collect_rss(source, self.base_dir)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "OpenAI announces agent reliability update")
        self.assertEqual(items[0]["metadata"]["collector"], "rss")

    def test_manual_url_skeleton_is_metadata_only(self):
        source = self.sources[1]
        items = collector.collect_manual_url(source, self.base_dir)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["url"], "https://example.gov/ai-policy-update")
        self.assertIsNone(items[0]["raw_content"])
        self.assertTrue(items[0]["metadata"]["metadata_only"])

    def test_github_release_fixture_parsing(self):
        source = self.sources[2]
        items = collector.collect_github_release_fixture(source, self.base_dir)

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "v1.2.0 agent runtime")
        self.assertEqual(items[0]["metadata"]["collector"], "github_release_fixture")

    def test_normalization_canonicalizes_url_and_preserves_raw_boundary(self):
        source = self.sources[0]
        raw = {
            "title": "  OpenAI   Update  ",
            "url": "HTTPS://OPENAI.COM/blog/update/?utm_source=test",
            "raw_excerpt": "Short excerpt",
            "metadata": {"collector": "rss"},
        }

        item = collector.normalize_raw_item(source, raw, "2026-06-19T00:00:00+00:00")

        self.assertEqual(item["raw_title"], "OpenAI Update")
        self.assertEqual(item["canonical_url"], "https://openai.com/blog/update")
        self.assertEqual(item["raw_excerpt"], "Short excerpt")
        self.assertIsNone(item["raw_content"])

    def test_deduplication_by_source_url_and_title(self):
        source = self.sources[0]
        first = collector.normalize_raw_item(
            source,
            {"title": "Same", "url": "https://example.com/a?utm=1", "raw_excerpt": "one"},
            "2026-06-19T00:00:00+00:00",
        )
        second = collector.normalize_raw_item(
            source,
            {"title": "Same", "url": "https://example.com/a", "raw_excerpt": "two"},
            "2026-06-19T00:00:00+00:00",
        )

        unique, results = collector.deduplicate_raw_items([first, second])

        self.assertEqual(len(unique), 1)
        self.assertEqual(results[0]["status"], "unique")
        self.assertEqual(results[1]["status"], "duplicate")

    def test_run_collection_writes_report_and_store_with_safety_flags(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = pathlib.Path(tmpdir) / "collector_report.json"
            store_path = pathlib.Path(tmpdir) / "raw_items_store.json"

            report = collector.run_collection(SOURCE_STORE, report_path=report_path, raw_store_path=store_path)

            store = json.loads(store_path.read_text(encoding="utf-8"))
            self.assertEqual(set(store), {"raw_items", "collection_metadata", "deduplication_results"})
            self.assertEqual(report["total_sources"], 3)
            self.assertEqual(report["total_raw_items_before_deduplication"], 4)
            self.assertEqual(report["total_raw_items"], 3)
            self.assertEqual(report["duplicates_removed"], 1)
            self.assertFalse(report["notion_write_operations_performed"])
            self.assertFalse(report["live_github_api_used"])
            self.assertFalse(report["llm_api_calls_performed"])
            self.assertFalse(report["publishing_performed"])
            self.assertFalse(report["social_posting_performed"])
            self.assertFalse(report["article_body_scraping_performed"])
            self.assertTrue(report_path.exists())


if __name__ == "__main__":
    unittest.main()
