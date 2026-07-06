import json
import pathlib
import tempfile
import unittest
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "source_collector_v1"
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_source_collector_v1 as collector  # noqa: E402


def load_records(name: str):
    data = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return data["records"]


class DysonXSourceCollectorV1Tests(unittest.TestCase):
    def fixture_fetch(self, url: str) -> str:
        mapping = {
            "https://example.org/rss.xml": FIXTURES / "rss_feed_sample.xml",
            "https://export.arxiv.org/rss/cs.AI": FIXTURES / "arxiv_feed_sample.xml",
            "https://example.org/medium-rss.xml": FIXTURES / "rss_feed_sample.xml",
        }
        path = mapping.get(url)
        if not path:
            raise collector.SourceCollectorError(f"missing fixture: {url}")
        return path.read_text(encoding="utf-8")

    def test_rss_item_becomes_signal_candidate(self):
        sources = [load_records("source_registry_sample.json")[0]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)

        titles = [item["Signal Title"] for item in result["candidates"]]
        self.assertIn("Agent evaluation benchmark improves reliability scoring", titles)

    def test_arxiv_feed_item_becomes_signal_candidate(self):
        sources = [load_records("source_registry_sample.json")[1]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)

        candidate = result["candidates"][0]
        self.assertEqual(candidate["Signal Title"], "Compute-aware evaluation for autonomous AI agents")
        self.assertEqual(candidate["Category"], "Research")
        self.assertEqual(candidate["Source Priority"], "Critical")

    def test_relative_canonical_path_becomes_absolute_url(self):
        source = collector.SourceRecord(
            notion_page_id="source-page",
            name="Official Lab",
            url="https://example.org/research/index.html",
            source_type="Official Website",
            platform="Website",
            priority="High",
            authority_score=95,
            enabled=True,
        )
        html = """
        <html>
          <head>
            <title>Agent safety evaluation update</title>
            <link rel="canonical" href="/research/agent-safety-update" />
            <meta name="description" content="Agent safety evaluation metadata summary." />
          </head>
        </html>
        """

        item = collector.parse_page_metadata(html, source)[0]
        candidate = collector.candidate_from_item(item)

        self.assertEqual(item.link, "https://example.org/research/agent-safety-update")
        self.assertEqual(candidate["Source URL"], "https://example.org/research/agent-safety-update")
        self.assertEqual(candidate["Attribution Status"], "Complete")

    def test_relative_rss_item_link_becomes_absolute_url(self):
        source = collector.SourceRecord(
            notion_page_id="source-feed",
            name="Official Lab RSS",
            url="https://example.org/rss.xml",
            source_type="RSS",
            platform="RSS",
            priority="High",
            authority_score=95,
            enabled=True,
        )
        feed = """
        <rss><channel>
          <item>
            <title>Agent benchmark update</title>
            <link>/research/agent-benchmark</link>
            <description>Agent benchmark metadata summary.</description>
          </item>
        </channel></rss>
        """

        item = collector.parse_feed_items(feed, source)[0]
        candidate = collector.candidate_from_item(item)

        self.assertEqual(item.link, "https://example.org/research/agent-benchmark")
        self.assertEqual(candidate["Source URL"], "https://example.org/research/agent-benchmark")
        self.assertEqual(candidate["Attribution Status"], "Complete")

    def test_unsupported_source_is_skipped(self):
        sources = [load_records("source_registry_sample.json")[5]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)

        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["source_results"][0]["status"], "skipped")

    def test_disabled_source_is_skipped(self):
        sources = [load_records("source_registry_sample.json")[3]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)

        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["source_results"][0]["status"], "skipped")

    def test_missing_url_is_skipped(self):
        sources = [load_records("source_registry_sample.json")[4]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)

        self.assertEqual(result["candidate_count"], 0)
        self.assertEqual(result["source_results"][0]["status"], "skipped")
        self.assertEqual(result["source_results"][0]["reason"], "missing_url")

    def test_openai_blocked_url_uses_official_rss_fallback(self):
        source = collector.SourceRecord(
            notion_page_id="openai-source",
            name="OpenAI Blog",
            url="https://openai.com/blog",
            source_type="Official Website",
            platform="Website",
            priority="Critical",
            authority_score=95,
            enabled=True,
        )
        feed = """
        <rss><channel>
          <item>
            <title>How agents are transforming work</title>
            <link>https://openai.com/index/how-agents-are-transforming-work</link>
            <description>OpenAI metadata summary about AI agents transforming work.</description>
            <pubDate>Thu, 25 Jun 2026 02:00:00 GMT</pubDate>
          </item>
        </channel></rss>
        """

        def fetch(url: str) -> str:
            if url == "https://openai.com/blog":
                raise collector.SourceCollectorError("source fetch failed: HTTP Error 403: Forbidden")
            if url == "https://openai.com/news/rss.xml":
                return feed
            raise collector.SourceCollectorError(f"unexpected fetch URL: {url}")

        result = collector.build_candidates([collector.asdict(source)], [], fetch=fetch)

        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["source_results"][0]["status"], "collected")
        self.assertTrue(result["source_results"][0]["fallback_used"])
        self.assertEqual(result["source_results"][0]["fetched_url"], "https://openai.com/news/rss.xml")
        self.assertEqual(result["candidates"][0]["Source URL"], "https://openai.com/index/how-agents-are-transforming-work")

    def test_nvidia_developer_blog_uses_official_blog_feed_fallback(self):
        source = collector.SourceRecord(
            notion_page_id="nvidia-source",
            name="NVIDIA Developer Blog AI",
            url="https://developer.nvidia.com/blog/category/ai/",
            source_type="RSS",
            platform="RSS",
            priority="High",
            authority_score=90,
            enabled=True,
        )
        feed = """
        <rss><channel>
          <item>
            <title>NVIDIA AI inference update for robotics agents</title>
            <link>https://developer.nvidia.com/blog/inference-robotics-agents</link>
            <description>NVIDIA metadata summary about AI inference for robotics agents.</description>
          </item>
        </channel></rss>
        """

        def fetch(url: str) -> str:
            if url == "https://developer.nvidia.com/blog/category/ai/":
                raise collector.SourceCollectorError("source fetch failed: HTTP Error 404: Not Found")
            if url == "https://developer.nvidia.com/blog/feed/":
                return feed
            raise collector.SourceCollectorError(f"unexpected fetch URL: {url}")

        result = collector.build_candidates([collector.asdict(source)], [], fetch=fetch)

        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["source_results"][0]["fetched_url"], "https://developer.nvidia.com/blog/feed/")
        self.assertTrue(result["source_results"][0]["fallback_used"])

    def test_low_authority_source_does_not_auto_publish(self):
        sources = [load_records("source_registry_sample.json")[2]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)

        candidate = next(item for item in result["candidates"] if "Agent evaluation" in item["Signal Title"])
        self.assertFalse(candidate["Ready for Pipeline"])
        self.assertFalse(candidate["Published"])
        self.assertEqual(candidate["Status"], "Needs Owner Review")

    def test_missing_attribution_does_not_auto_publish(self):
        item = collector.SourceItem(
            title="Agent safety evaluation update",
            link="",
            published_date="",
            summary="Agent safety evaluation metadata summary.",
            source_name="Official Lab",
            source_url="https://example.org/lab",
            source_type="RSS",
            priority="High",
            authority_score=95,
            attribution_complete=False,
        )
        candidate = collector.candidate_from_item(item)

        self.assertFalse(candidate["Ready for Pipeline"])
        self.assertFalse(candidate["Published"])
        self.assertEqual(candidate["Attribution Status"], "Missing")

    def test_non_http_source_url_cannot_auto_publish(self):
        item = collector.SourceItem(
            title="Agent safety evaluation update",
            link="mailto:research@example.org",
            published_date="",
            summary="Agent safety evaluation metadata summary.",
            source_name="Official Lab",
            source_url="mailto:research@example.org",
            source_type="RSS",
            priority="High",
            authority_score=95,
            attribution_complete=True,
        )
        candidate = collector.candidate_from_item(item)

        self.assertEqual(candidate["Source URL"], "")
        self.assertEqual(candidate["Attribution Status"], "Missing")
        self.assertFalse(candidate["Ready for Pipeline"])
        self.assertFalse(candidate["Published"])

    def test_raw_body_is_never_included(self):
        sources = [load_records("source_registry_sample.json")[0]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)
        text = json.dumps(result)

        self.assertNotIn("<article", text)
        self.assertNotIn("raw article body", text.lower())
        for candidate in result["candidates"]:
            self.assertLessEqual(len(candidate["Summary"]), 260)

    def test_duplicate_source_url_is_skipped(self):
        sources = [load_records("source_registry_sample.json")[0]]
        existing = load_records("existing_signal_intake_sample.json")
        result = collector.build_candidates(sources, existing, fetch=self.fixture_fetch)

        titles = [item["Signal Title"] for item in result["candidates"]]
        self.assertNotIn("Agent evaluation benchmark improves reliability scoring", titles)
        self.assertGreaterEqual(result["duplicates_skipped"], 1)
        self.assertGreaterEqual(result["skipped_by_reason"]["duplicate_source_url"], 1)
        self.assertEqual(result["skipped_candidates"][0]["reason"], "duplicate_source_url")
        self.assertIn("matched_keys", result["skipped_candidates"][0])

    def test_all_duplicates_reports_no_fresh_source_items(self):
        sources = [load_records("source_registry_sample.json")[0]]
        existing = [
            {"Source URL": "https://example.org/research/agent-evaluation-benchmark"},
            {"Source URL": "https://example.org/company/operations-update"},
        ]
        result = collector.build_candidates(sources, existing, fetch=self.fixture_fetch)

        self.assertEqual(result["raw_items_seen"], 2)
        self.assertEqual(result["new_candidates_created"], 0)
        self.assertEqual(result["duplicates_skipped"], 2)
        self.assertEqual(
            result["freshness_diagnostic"],
            "no fresh source items found; all fetched items matched existing Signal Intake rows",
        )

    def test_high_priority_quality_88_is_created_but_not_published(self):
        item = collector.SourceItem(
            title="AI driving scenario complexity detection via joint embedding predictive architecture",
            link="https://example.org/zero-label-driving-scenario-complexity",
            published_date="2026-06-30",
            summary="A research paper metadata summary about AI driving scenario complexity detection.",
            source_name="arXiv cs.CV RSS",
            source_url="https://export.arxiv.org/rss/cs.CV",
            source_type="arXiv",
            priority="High",
            authority_score=88,
            attribution_complete=True,
        )
        candidate = collector.candidate_from_item(item)

        self.assertEqual(candidate["Source Priority"], "High")
        self.assertEqual(candidate["Quality Hint"], 88)
        self.assertFalse(candidate["Ready for Pipeline"])
        self.assertFalse(candidate["Published"])

    def test_critical_quality_at_least_92_is_published_and_ready(self):
        sources = [load_records("source_registry_sample.json")[1]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)
        candidate = result["candidates"][0]

        self.assertTrue(candidate["Ready for Pipeline"])
        self.assertTrue(candidate["Published"])
        self.assertEqual(candidate["Status"], "Ready for Quality Audit")
        self.assertEqual(candidate["Source Priority"], "Critical")
        self.assertGreaterEqual(candidate["Quality Hint"], 92)

    def test_generated_candidate_has_safe_summary_only_copyright_status(self):
        sources = [load_records("source_registry_sample.json")[0]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)

        for candidate in result["candidates"]:
            self.assertEqual(candidate["Copyright Status"], "Safe Summary Only")

    def test_collector_does_not_write_public_static_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fetch_map = pathlib.Path(tmpdir) / "fetch_map.json"
            fetch_map.write_text(
                json.dumps(
                    {
                        "https://example.org/rss.xml": str(FIXTURES / "rss_feed_sample.xml"),
                        "https://export.arxiv.org/rss/cs.AI": str(FIXTURES / "arxiv_feed_sample.xml"),
                        "https://example.org/medium-rss.xml": str(FIXTURES / "rss_feed_sample.xml"),
                    }
                ),
                encoding="utf-8",
            )
            output = pathlib.Path(tmpdir) / "candidates.json"
            rc = collector.main(
                [
                    "--sources-fixture",
                    str(FIXTURES / "source_registry_sample.json"),
                    "--existing-signal-intake-fixture",
                    str(FIXTURES / "existing_signal_intake_sample.json"),
                    "--fetch-fixture-map",
                    str(fetch_map),
                    "--output-candidates",
                    str(output),
                ]
            )
            self.assertEqual(rc, 0)
            self.assertTrue(output.exists())
            self.assertFalse((pathlib.Path(tmpdir) / "signals").exists())

    def test_collector_does_not_call_openai(self):
        sources = [load_records("source_registry_sample.json")[1]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)

        self.assertFalse(result["openai_call_performed"])
        self.assertFalse(result["source_page_body_scraping_performed"])
        self.assertFalse(result["public_static_files_written"])

    def test_expected_fixture_shape_matches_candidates(self):
        sources = load_records("source_registry_sample.json")[:2]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)
        expected = json.loads((FIXTURES / "expected_signal_candidates.json").read_text(encoding="utf-8"))
        titles = [item["Signal Title"] for item in result["candidates"]]

        for title in expected["candidate_titles"]:
            self.assertIn(title, titles)
        auto = next(item for item in result["candidates"] if item["Signal Title"] == expected["auto_ready_title"])
        self.assertTrue(auto["Ready for Pipeline"])
        self.assertEqual(auto["Copyright Status"], expected["copyright_status"])
        self.assertEqual(result["openai_call_performed"], expected["openai_call_performed"])
        self.assertEqual(result["public_static_files_written"], expected["public_static_files_written"])

    def test_notion_writeback_properties_match_signal_intake_schema(self):
        sources = [load_records("source_registry_sample.json")[1]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)
        candidate = result["candidates"][0]
        properties = collector.notion_candidate_properties(candidate)
        allowed = {
            "Signal Title",
            "Source Name",
            "Source URL",
            "Published Date",
            "Category",
            "AGI Relevance",
            "Status",
            "Attribution Status",
            "Copyright Status",
            "Quality Hint",
            "Summary",
            "Why It Matters",
            "Evidence",
            "Risk / Safety Notes",
            "Ready for Pipeline",
            "Published",
            "Notes",
        }

        self.assertEqual(set(properties), allowed)
        self.assertNotIn("Slug", properties)
        self.assertNotIn("Collector Version", properties)
        self.assertEqual(properties["Notes"]["rich_text"][0]["text"]["content"], "Collector Version: source_collector_v1")

    def test_notion_writeback_includes_source_priority_when_schema_supports_it(self):
        sources = [load_records("source_registry_sample.json")[1]]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)
        candidate = result["candidates"][0]
        properties = collector.notion_candidate_properties(candidate, supported_properties={"Source Priority"})

        self.assertEqual(properties["Source Priority"]["select"]["name"], "Critical")

    def test_notion_select_values_match_signal_intake_schema(self):
        sources = load_records("source_registry_sample.json")[:3]
        result = collector.build_candidates(sources, [], fetch=self.fixture_fetch)
        allowed_categories = {
            "Frontier Lab",
            "Research",
            "Compute",
            "Open Source",
            "Policy",
            "Safety",
            "Enterprise AI",
            "Market Signal",
            "Other",
        }
        allowed_statuses = {
            "New",
            "Ready for Quality Audit",
            "Needs More Sources",
            "Needs Owner Review",
            "Blocked",
            "Archived",
        }
        allowed_attribution = {"Complete", "Partial", "Missing"}

        for candidate in result["candidates"]:
            properties = collector.notion_candidate_properties(candidate)
            self.assertIn(properties["Category"]["select"]["name"], allowed_categories)
            self.assertIn(properties["Status"]["select"]["name"], allowed_statuses)
            self.assertIn(properties["Attribution Status"]["select"]["name"], allowed_attribution)

    def test_source_collector_workflow_cron_is_offset_from_public_sync(self):
        collector_workflow = (ROOT / ".github" / "workflows" / "dysonx-source-collector-v1.yml").read_text(encoding="utf-8")
        public_sync_workflow = (ROOT / ".github" / "workflows" / "dysonx-notion-public-signals-sync.yml").read_text(encoding="utf-8")

        self.assertIn('cron: "50 23,5,11,17 * * *"', collector_workflow)
        self.assertNotIn('cron: "17 */6 * * *"', collector_workflow)
        self.assertIn('cron: "0 */6 * * *"', public_sync_workflow)


if __name__ == "__main__":
    unittest.main()
