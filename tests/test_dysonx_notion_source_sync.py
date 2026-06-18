import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_notion_source_sync as source_sync
from dysonx_notion_readonly_adapter import FakeNotionSourceClient, NotionReadOnlySourceClient


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "notion_sources_v1.json"


class DysonXNotionSourceSyncTests(unittest.TestCase):
    def test_fixture_sync_validates_converts_persists_and_audits(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = pathlib.Path(tmpdir) / "source_sync_report.json"
            storage_path = pathlib.Path(tmpdir) / "source_sync_store.json"

            report = source_sync.sync_sources(
                FakeNotionSourceClient(FIXTURE_PATH),
                storage_path=storage_path,
                report_path=report_path,
                mode="fixture",
            )

            self.assertEqual(report["total_records"], 4)
            self.assertEqual(report["valid_records"], 1)
            self.assertEqual(report["invalid_records"], 2)
            self.assertEqual(report["skipped_records"], 1)
            self.assertFalse(report["write_operations_performed"])
            self.assertFalse(report["notion_write_operations_performed"])
            self.assertFalse(report["collection_performed"])
            self.assertFalse(report["llm_api_calls_performed"])
            self.assertFalse(report["publishing_performed"])
            self.assertTrue(report["storage_write_operations_performed"])
            self.assertEqual(report["valid_sources"][0]["name"], "OpenAI Blog")
            self.assertTrue(report_path.exists())
            self.assertTrue(storage_path.exists())

            stored = json.loads(storage_path.read_text(encoding="utf-8"))
            self.assertEqual(len(stored["sources"]), 1)
            self.assertEqual(stored["sync_metadata"]["valid_records"], 1)
            self.assertFalse(stored["raw_articles_stored"])
            self.assertFalse(stored["llm_outputs_stored"])
            self.assertFalse(stored["publish_packages_stored"])

    def test_invalid_records_are_audited_without_blocking_valid_records(self):
        valid_sources, invalid_records, skipped_records = source_sync.classify_source_records(
            FakeNotionSourceClient(FIXTURE_PATH).list_source_records()
        )

        self.assertEqual(len(valid_sources), 1)
        self.assertEqual({record["record_name"] for record in invalid_records}, {"Missing URL Source", "Invalid Authority Source"})
        self.assertEqual(skipped_records[0]["record_name"], "Disabled Research Lab")

    def test_real_sync_fails_closed_without_credentials(self):
        client = NotionReadOnlySourceClient(token=None, database_id=None)

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = pathlib.Path(tmpdir) / "source_sync_report.json"
            storage_path = pathlib.Path(tmpdir) / "source_sync_store.json"
            with self.assertRaises(Exception):
                source_sync.sync_sources(client, storage_path=storage_path, report_path=report_path)

            self.assertFalse(report_path.exists())
            self.assertFalse(storage_path.exists())


if __name__ == "__main__":
    unittest.main()
