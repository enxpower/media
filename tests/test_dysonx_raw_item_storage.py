import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_raw_item_storage as storage


class DysonXRawItemStorageTests(unittest.TestCase):
    def test_raw_item_store_shape(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "raw_items_store.json"
            document = storage.write_raw_item_store(
                output,
                raw_items=[{"id": "raw_1", "raw_title": "Fixture"}],
                collection_metadata={"store_version": storage.STORE_VERSION, "total_raw_items": 1},
                deduplication_results=[{"status": "unique", "raw_item_id": "raw_1"}],
            )

            disk_document = json.loads(output.read_text(encoding="utf-8"))

            self.assertEqual(document, disk_document)
            self.assertEqual(set(disk_document), {"raw_items", "collection_metadata", "deduplication_results"})
            self.assertEqual(disk_document["collection_metadata"]["store_version"], storage.STORE_VERSION)

    def test_raw_item_store_read_validates_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "raw_items_store.json"
            storage.write_raw_item_store(
                output,
                raw_items=[],
                collection_metadata={"store_version": storage.STORE_VERSION},
                deduplication_results=[],
            )

            loaded = storage.read_raw_item_store(output)

            self.assertEqual(loaded["collection_metadata"]["store_version"], storage.STORE_VERSION)


if __name__ == "__main__":
    unittest.main()
