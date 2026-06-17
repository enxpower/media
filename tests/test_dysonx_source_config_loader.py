import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_source_config_loader as loader


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "notion_sources_v1.json"


class DysonXSourceConfigLoaderTests(unittest.TestCase):
    def test_valid_enabled_source_becomes_source(self):
        result = loader.load_sources_from_fixture(FIXTURE_PATH)

        self.assertEqual(len(result.sources), 1)
        source = result.sources[0]
        self.assertEqual(source.name, "OpenAI Blog")
        self.assertEqual(source.source_type, "Official Company Blog")
        self.assertEqual(source.url, "https://openai.com/blog")
        self.assertTrue(source.enabled)
        self.assertEqual(source.authority_score, 95.0)

    def test_disabled_source_is_not_collection_eligible(self):
        result = loader.load_sources_from_fixture(FIXTURE_PATH)

        self.assertIn("Disabled Research Lab", result.validation_errors)
        self.assertIn(
            "Enabled must be true for collection eligibility",
            result.validation_errors["Disabled Research Lab"],
        )
        self.assertNotIn("Disabled Research Lab", {source.name for source in result.sources})

    def test_missing_url_is_rejected(self):
        result = loader.load_sources_from_fixture(FIXTURE_PATH)

        self.assertIn("Missing URL Source", result.validation_errors)
        self.assertIn("URL is required", result.validation_errors["Missing URL Source"])

    def test_invalid_authority_score_is_rejected(self):
        result = loader.load_sources_from_fixture(FIXTURE_PATH)

        self.assertIn("Invalid Authority Source", result.validation_errors)
        self.assertIn(
            "Authority Score must be between 0 and 100",
            result.validation_errors["Invalid Authority Source"],
        )

    def test_loader_does_not_call_notion_api(self):
        module_source = pathlib.Path(loader.__file__).read_text(encoding="utf-8")

        self.assertNotIn("notion_client", module_source)
        self.assertNotIn("api.notion.com", module_source)
        self.assertNotIn("Client(", module_source)

    def test_loader_does_not_perform_network_requests(self):
        module_source = pathlib.Path(loader.__file__).read_text(encoding="utf-8")

        self.assertNotIn("requests", module_source)
        self.assertNotIn("urllib", module_source)
        self.assertNotIn("http.client", module_source)
        self.assertNotIn("socket", module_source)


if __name__ == "__main__":
    unittest.main()
