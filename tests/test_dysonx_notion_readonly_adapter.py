import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_notion_readonly_adapter as adapter_module
import dysonx_source_config_loader as loader
from dysonx_notion_source_schema import notion_source_field_names


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "notion_sources_v1.json"


class DysonXNotionReadOnlyAdapterTests(unittest.TestCase):
    def test_adapter_returns_records_in_notion_source_schema_shape(self):
        adapter = adapter_module.FakeNotionSourceClient(FIXTURE_PATH)
        records = adapter.list_source_records()
        expected_fields = set(notion_source_field_names())

        self.assertGreater(len(records), 0)
        for record in records:
            self.assertEqual(set(record), expected_fields)

    def test_adapter_output_can_be_passed_into_source_config_loader(self):
        adapter = adapter_module.FakeNotionSourceClient(FIXTURE_PATH)
        records = adapter_module.list_source_records(adapter)
        result = loader.load_sources_from_records(records)

        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.sources[0].name, "OpenAI Blog")

    def test_disabled_sources_remain_non_eligible(self):
        adapter = adapter_module.FakeNotionSourceClient(FIXTURE_PATH)
        result = loader.load_sources_from_records(adapter.list_source_records())

        self.assertIn("Disabled Research Lab", result.validation_errors)
        self.assertNotIn("Disabled Research Lab", {source.name for source in result.sources})

    def test_invalid_records_preserve_validation_errors(self):
        adapter = adapter_module.FakeNotionSourceClient(FIXTURE_PATH)
        result = loader.load_sources_from_records(adapter.list_source_records())

        self.assertIn("Missing URL Source", result.validation_errors)
        self.assertIn("URL is required", result.validation_errors["Missing URL Source"])
        self.assertIn("Invalid Authority Source", result.validation_errors)
        self.assertIn(
            "Authority Score must be between 0 and 100",
            result.validation_errors["Invalid Authority Source"],
        )

    def test_adapter_is_read_only(self):
        adapter = adapter_module.FakeNotionSourceClient(FIXTURE_PATH)

        self.assertTrue(hasattr(adapter, "list_source_records"))
        self.assertFalse(hasattr(adapter, "create_source_record"))
        self.assertFalse(hasattr(adapter, "update_source_record"))
        self.assertFalse(hasattr(adapter, "delete_source_record"))

    def test_adapter_does_not_perform_network_requests(self):
        module_source = pathlib.Path(adapter_module.__file__).read_text(encoding="utf-8")

        self.assertNotIn("requests", module_source)
        self.assertNotIn("urllib", module_source)
        self.assertNotIn("http.client", module_source)
        self.assertNotIn("socket", module_source)

    def test_adapter_does_not_require_real_notion_credentials(self):
        module_source = pathlib.Path(adapter_module.__file__).read_text(encoding="utf-8")

        self.assertNotIn("NOTION_TOKEN", module_source)
        self.assertNotIn("NOTION_API_KEY", module_source)
        self.assertNotIn("os.environ", module_source)
        self.assertNotIn("notion_client", module_source)
        self.assertNotIn("api.notion.com", module_source)


if __name__ == "__main__":
    unittest.main()
