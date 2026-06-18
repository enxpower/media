import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_source_sync_storage as storage


class DysonXSourceSyncStorageTests(unittest.TestCase):
    def test_store_writes_only_source_sync_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "source_sync_store.json"
            document = storage.write_source_sync_store(
                output,
                sources=[{"id": "source_openai", "name": "OpenAI Blog"}],
                sync_metadata={"total_records": 1, "notion_write_operations_performed": False},
                validation_results=[{"record_name": "OpenAI Blog", "status": "valid"}],
            )

            self.assertTrue(output.exists())
            disk_document = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(document, disk_document)
            self.assertEqual(disk_document["store_version"], storage.STORE_VERSION)
            self.assertFalse(disk_document["raw_articles_stored"])
            self.assertFalse(disk_document["llm_outputs_stored"])
            self.assertFalse(disk_document["publish_packages_stored"])

    def test_store_read_validates_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "source_sync_store.json"
            storage.write_source_sync_store(output, sources=[], sync_metadata={}, validation_results=[])

            loaded = storage.read_source_sync_store(output)

            self.assertEqual(loaded["store_version"], storage.STORE_VERSION)


if __name__ == "__main__":
    unittest.main()
