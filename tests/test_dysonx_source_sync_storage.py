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
                sync_metadata={
                    "store_version": storage.STORE_VERSION,
                    "total_records": 1,
                    "notion_write_operations_performed": False,
                },
                validation_results=[{"record_name": "OpenAI Blog", "status": "valid"}],
            )

            self.assertTrue(output.exists())
            disk_document = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(document, disk_document)
            self.assertEqual(set(disk_document), {"sources", "sync_metadata", "validation_results"})
            self.assertEqual(disk_document["sync_metadata"]["store_version"], storage.STORE_VERSION)
            self.assertNotIn("store_version", disk_document)
            self.assertNotIn("raw_articles_stored", disk_document)
            self.assertNotIn("llm_outputs_stored", disk_document)
            self.assertNotIn("publish_packages_stored", disk_document)

    def test_store_read_validates_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "source_sync_store.json"
            storage.write_source_sync_store(
                output,
                sources=[],
                sync_metadata={"store_version": storage.STORE_VERSION},
                validation_results=[],
            )

            loaded = storage.read_source_sync_store(output)

            self.assertEqual(loaded["sync_metadata"]["store_version"], storage.STORE_VERSION)


if __name__ == "__main__":
    unittest.main()
