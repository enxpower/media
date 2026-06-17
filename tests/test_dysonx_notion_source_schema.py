import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_notion_source_schema as schema


def valid_record(**overrides):
    record = {
        "Name": "OpenAI Blog",
        "Source Type": "Official Company Blog",
        "URL": "https://openai.com/blog",
        "Platform": "Website",
        "Priority": "Critical",
        "Authority Score": 95,
        "Language": "English",
        "Region": "Global",
        "Topic Tags": ["foundation models"],
        "Related Entities": ["OpenAI"],
        "Enabled": True,
        "Fetch Frequency": 60,
        "Last Fetched At": None,
        "Last Success At": None,
        "Last Error": "",
        "Notes": "",
    }
    record.update(overrides)
    return record


class DysonXNotionSourceSchemaTests(unittest.TestCase):
    def test_required_fields_are_defined(self):
        expected_fields = {
            "Name",
            "Source Type",
            "URL",
            "Platform",
            "Priority",
            "Authority Score",
            "Language",
            "Region",
            "Topic Tags",
            "Related Entities",
            "Enabled",
            "Fetch Frequency",
            "Last Fetched At",
            "Last Success At",
            "Last Error",
            "Notes",
        }

        self.assertEqual(set(schema.notion_source_field_names()), expected_fields)
        self.assertTrue({"Name", "Source Type", "URL", "Enabled"}.issubset(schema.required_notion_source_field_names()))

    def test_enabled_is_required_before_collection_eligibility(self):
        self.assertTrue(schema.is_collection_eligible(valid_record()))
        self.assertFalse(schema.is_collection_eligible(valid_record(Enabled=False)))
        self.assertFalse(schema.is_collection_eligible(valid_record(Enabled=None)))

    def test_source_type_and_url_are_required(self):
        source_type_errors = schema.validate_notion_source_record(valid_record(**{"Source Type": ""}))
        url_errors = schema.validate_notion_source_record(valid_record(URL=""))

        self.assertIn("Source Type is required", source_type_errors)
        self.assertIn("URL is required", url_errors)
        self.assertIn("Source Type is invalid", schema.validate_notion_source_record(valid_record(**{"Source Type": "Forum"})))

    def test_authority_score_and_priority_have_valid_ranges(self):
        self.assertEqual(schema.validate_notion_source_record(valid_record(**{"Authority Score": 0, "Priority": "Low"})), [])
        self.assertEqual(schema.validate_notion_source_record(valid_record(**{"Authority Score": 100, "Priority": "Critical"})), [])
        self.assertIn(
            "Authority Score must be between 0 and 100",
            schema.validate_notion_source_record(valid_record(**{"Authority Score": 101})),
        )
        self.assertIn("Priority is invalid", schema.validate_notion_source_record(valid_record(Priority="Urgent")))

    def test_fetch_frequency_has_valid_range(self):
        self.assertEqual(schema.validate_notion_source_record(valid_record(**{"Fetch Frequency": 15})), [])
        self.assertEqual(schema.validate_notion_source_record(valid_record(**{"Fetch Frequency": 10080})), [])
        self.assertIn(
            "Fetch Frequency must be between 15 and 10080 minutes",
            schema.validate_notion_source_record(valid_record(**{"Fetch Frequency": 5})),
        )

    def test_module_does_not_call_notion_api(self):
        module_source = pathlib.Path(schema.__file__).read_text(encoding="utf-8")

        self.assertNotIn("requests", module_source)
        self.assertNotIn("urllib", module_source)
        self.assertNotIn("notion_client", module_source)
        self.assertNotIn("Client(", module_source)
        self.assertNotIn("api.notion.com", module_source)


if __name__ == "__main__":
    unittest.main()
