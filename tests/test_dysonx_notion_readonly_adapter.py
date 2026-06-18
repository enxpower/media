import pathlib
import sys
import unittest
from unittest import mock

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

    def test_fixture_adapter_does_not_perform_network_requests(self):
        module_source = pathlib.Path(adapter_module.__file__).read_text(encoding="utf-8")

        self.assertNotIn("requests", module_source)
        self.assertNotIn("http.client", module_source)
        self.assertNotIn("socket", module_source)

    def test_adapter_does_not_require_real_notion_credentials(self):
        adapter = adapter_module.FakeNotionSourceClient(FIXTURE_PATH)
        records = adapter.list_source_records()

        self.assertGreater(len(records), 0)

    def test_real_adapter_skeleton_fails_closed_without_credentials(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            client = adapter_module.NotionReadOnlySourceClient.from_env()

        with self.assertRaises(adapter_module.NotionReadOnlyAdapterNotConfigured):
            client.list_source_records()

    def test_real_adapter_queries_notion_database_read_only(self):
        calls = []

        def transport(url, headers, payload):
            calls.append((url, headers, payload))
            return {
                "results": [
                    {
                        "id": "page_openai",
                        "properties": {
                            "Name": {"type": "title", "title": [{"plain_text": "OpenAI Blog"}]},
                            "Source Type": {"type": "select", "select": {"name": "Official Company Blog"}},
                            "URL": {"type": "url", "url": "https://openai.com/blog"},
                            "Platform": {"type": "select", "select": {"name": "Website"}},
                            "Priority": {"type": "select", "select": {"name": "Critical"}},
                            "Authority Score": {"type": "number", "number": 95},
                            "Language": {"type": "select", "select": {"name": "English"}},
                            "Region": {"type": "select", "select": {"name": "Global"}},
                            "Topic Tags": {
                                "type": "multi_select",
                                "multi_select": [{"name": "foundation models"}, {"name": "agents"}],
                            },
                            "Related Entities": {"type": "multi_select", "multi_select": [{"name": "OpenAI"}]},
                            "Enabled": {"type": "checkbox", "checkbox": True},
                            "Fetch Frequency": {"type": "number", "number": 60},
                            "Last Fetched At": {"type": "date", "date": None},
                            "Last Success At": {"type": "date", "date": None},
                            "Last Error": {"type": "rich_text", "rich_text": []},
                            "Notes": {"type": "rich_text", "rich_text": [{"plain_text": "Read-only test"}]},
                        },
                    }
                ],
                "has_more": False,
                "next_cursor": None,
            }

        client = adapter_module.NotionReadOnlySourceClient(
            token="secret_token",
            database_id="database_id",
            transport=transport,
        )
        records = client.list_source_records()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["Name"], "OpenAI Blog")
        self.assertEqual(records[0]["_notion_page_id"], "page_openai")
        self.assertEqual(records[0]["Topic Tags"], ["foundation models", "agents"])
        self.assertEqual(calls[0][0], "https://api.notion.com/v1/databases/database_id/query")
        self.assertEqual(calls[0][1]["Authorization"], "Bearer secret_token")
        self.assertEqual(calls[0][2], {"page_size": 100})
        self.assertFalse(hasattr(client, "create_source_record"))
        self.assertFalse(hasattr(client, "update_source_record"))
        self.assertFalse(hasattr(client, "delete_source_record"))

    def test_real_adapter_paginates_read_only_queries(self):
        calls = []

        def transport(_url, _headers, payload):
            calls.append(payload)
            if len(calls) == 1:
                return {"results": [], "has_more": True, "next_cursor": "cursor_2"}
            return {"results": [], "has_more": False, "next_cursor": None}

        client = adapter_module.NotionReadOnlySourceClient(
            token="secret_token",
            database_id="database_id",
            transport=transport,
        )
        records = client.list_source_records()

        self.assertEqual([], records)
        self.assertEqual(calls, [{"page_size": 100}, {"page_size": 100, "start_cursor": "cursor_2"}])


if __name__ == "__main__":
    unittest.main()
