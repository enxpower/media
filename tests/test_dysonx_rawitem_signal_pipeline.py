import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_collector_foundation
import dysonx_rawitem_signal_pipeline as integration


SOURCE_STORE = ROOT / "tests" / "fixtures" / "source_sync_store_v1.json"


class DysonXRawItemSignalPipelineTests(unittest.TestCase):
    def test_raw_item_store_is_read_correctly(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_store = pathlib.Path(tmpdir) / "raw_items_store.json"
            collector_report = pathlib.Path(tmpdir) / "collector_report.json"
            dysonx_collector_foundation.run_collection(
                SOURCE_STORE,
                report_path=collector_report,
                raw_store_path=raw_store,
            )

            loaded = integration.load_raw_item_store(raw_store)
            records = integration.raw_store_to_pipeline_records(loaded)

            self.assertEqual(set(loaded), {"raw_items", "collection_metadata", "deduplication_results"})
            self.assertEqual(len(records), 3)
            self.assertIn("title", records[0])
            self.assertIn("raw_content", records[0])
            self.assertIn("raw_item_id", records[0]["metadata"])

    def test_missing_raw_store_runs_collector_foundation_first(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_store = pathlib.Path(tmpdir) / "raw_items_store.json"
            collector_report = pathlib.Path(tmpdir) / "collector_report.json"
            signal_output = pathlib.Path(tmpdir) / "signal_candidates.json"

            report = integration.run_integration(
                SOURCE_STORE,
                raw_store_path=raw_store,
                collector_report_path=collector_report,
                signal_output_path=signal_output,
            )

            self.assertTrue(raw_store.exists())
            self.assertTrue(collector_report.exists())
            self.assertTrue(report["integration"]["collector_ran"])
            self.assertEqual(report["integration"]["raw_items_read"], 3)

    def test_raw_items_are_transformed_through_existing_pipeline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_store = pathlib.Path(tmpdir) / "raw_items_store.json"
            collector_report = pathlib.Path(tmpdir) / "collector_report.json"
            signal_output = pathlib.Path(tmpdir) / "signal_candidates.json"
            dysonx_collector_foundation.run_collection(
                SOURCE_STORE,
                report_path=collector_report,
                raw_store_path=raw_store,
            )

            with mock.patch("dysonx_signal_candidate_pipeline.run_pipeline", wraps=integration.dysonx_signal_candidate_pipeline.run_pipeline) as run_mock:
                report = integration.run_integration(
                    SOURCE_STORE,
                    raw_store_path=raw_store,
                    collector_report_path=collector_report,
                    signal_output_path=signal_output,
                )

            run_mock.assert_called_once()
            self.assertFalse(report["integration"]["signal_candidate_layer_bypassed"])
            self.assertTrue(report["integration"]["signal_candidate_pipeline_reused"])
            self.assertEqual(report["candidates_created"], 3)
            self.assertEqual(len(report["candidates"]), 3)

    def test_audit_flags_remain_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            signal_output = pathlib.Path(tmpdir) / "signal_candidates.json"
            report = integration.run_integration(
                SOURCE_STORE,
                raw_store_path=pathlib.Path(tmpdir) / "raw_items_store.json",
                collector_report_path=pathlib.Path(tmpdir) / "collector_report.json",
                signal_output_path=signal_output,
            )

            self.assertFalse(report["notion_write_operations_performed"])
            self.assertFalse(report["live_github_api_used"])
            self.assertFalse(report["llm_api_calls_performed"])
            self.assertFalse(report["publishing_performed"])
            self.assertFalse(report["social_posting_performed"])
            self.assertFalse(report["article_body_scraping_performed"])
            self.assertFalse(report["llm_used"])
            self.assertFalse(report["network_requests_performed"])

            disk_report = json.loads(signal_output.read_text(encoding="utf-8"))
            self.assertEqual(report, disk_report)

    def test_no_prohibited_integrations_are_present(self):
        module_source = pathlib.Path(integration.__file__).read_text(encoding="utf-8").lower()

        self.assertNotIn("import openai", module_source)
        self.assertNotIn("from openai", module_source)
        self.assertNotIn("import anthropic", module_source)
        self.assertNotIn("api.github.com", module_source)
        self.assertNotIn("api.notion.com", module_source)
        self.assertNotIn("requests", module_source)
        self.assertNotIn("urllib.request", module_source)
        self.assertNotIn("import schedule", module_source)
        self.assertNotIn("from schedule", module_source)
        self.assertNotIn(".every(", module_source)


if __name__ == "__main__":
    unittest.main()
