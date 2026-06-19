import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_real_llm_provider as provider


FIXED_TIME = "2026-06-19T00:00:00+00:00"


class DysonXRealLLMProviderTests(unittest.TestCase):
    def write_candidate_report(self, tmpdir: str) -> pathlib.Path:
        path = pathlib.Path(tmpdir) / "signal_candidates.json"
        path.write_text(
            json.dumps(
                {
                    "generated_at": FIXED_TIME,
                    "candidates_created": 2,
                    "candidates": [
                        {
                            "candidate_id": "candidate_openai_release",
                            "title": "OpenAI releases agent infrastructure update",
                            "source_id": "source_openai",
                            "source_name": "OpenAI",
                            "url": "https://openai.com/example",
                            "candidate_type": "model_release",
                            "entities": ["OpenAI"],
                            "tags": ["model", "release"],
                            "confidence": 0.72,
                        },
                        {
                            "candidate_id": "candidate_policy",
                            "title": "EU AI Act implementation update",
                            "source_id": "source_eu",
                            "source_name": "EU",
                            "url": "https://example.eu/ai-act",
                            "candidate_type": "regulation",
                            "entities": ["EU"],
                            "tags": ["policy", "regulation"],
                            "confidence": 0.61,
                        },
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def test_fake_provider_is_default_and_offline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_report = self.write_candidate_report(tmpdir)
            output = pathlib.Path(tmpdir) / "real_llm_report.json"

            with mock.patch("http.client.HTTPSConnection") as connection_mock:
                exit_code = provider.main(
                    [
                        "--signal-candidates",
                        str(candidate_report),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(exit_code, 0)
            connection_mock.assert_not_called()
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["provider"], "fake")
            self.assertEqual(report["items_requested"], 2)
            self.assertEqual(report["items_processed"], 2)
            self.assertEqual(report["intelligence_signals_created"], 2)
            self.assertFalse(report["real_llm_api_used"])
            self.assertFalse(report["llm_api_calls_performed"])
            self.assertFalse(report["publishing_performed"])
            self.assertFalse(report["social_posting_performed"])
            self.assertFalse(report["deployment_performed"])
            self.assertFalse(report["raw_provider_response_stored"])

    def test_required_plural_candidate_path_can_read_existing_singular_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            singular = pathlib.Path(tmpdir) / "signal_candidate_report.json"
            plural = pathlib.Path(tmpdir) / "signal_candidates_report.json"
            generated = self.write_candidate_report(tmpdir)
            generated.replace(singular)

            report = provider.run_provider(plural, provider="fake", created_at=FIXED_TIME)

            self.assertEqual(report["items_processed"], 2)
            self.assertEqual(report["intelligence_signals_created"], 2)

    def test_openai_gate_fails_closed_without_allow_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_report = self.write_candidate_report(tmpdir)
            with self.assertRaises(provider.ProviderGateError):
                provider.run_provider(
                    candidate_report,
                    provider="openai",
                    api_key="test-key",
                    max_items=1,
                    created_at=FIXED_TIME,
                )

    def test_openai_gate_fails_closed_without_api_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_report = self.write_candidate_report(tmpdir)
            with mock.patch.dict("os.environ", {}, clear=True):
                with self.assertRaises(provider.ProviderGateError):
                    provider.run_provider(
                        candidate_report,
                        provider="openai",
                        allow_real_llm=True,
                        max_items=1,
                        created_at=FIXED_TIME,
                    )

    def test_openai_gate_fails_closed_without_max_items(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_report = self.write_candidate_report(tmpdir)
            with self.assertRaises(provider.ProviderGateError):
                provider.run_provider(
                    candidate_report,
                    provider="openai",
                    allow_real_llm=True,
                    api_key="test-key",
                    created_at=FIXED_TIME,
                )

    def test_validation_rejects_malformed_provider_output(self):
        malformed = {
            "title": "",
            "summary": "Missing required fields.",
            "confidence": 2,
            "related_entities": "OpenAI",
        }

        passed, errors = provider.validate_intelligence_signal(malformed)

        self.assertFalse(passed)
        self.assertIn("why_it_matters is required", errors)
        self.assertIn("agi_capability is required", errors)
        self.assertIn("watch_next is required", errors)
        self.assertIn("source_url is required", errors)
        self.assertIn("title must be a non-empty string", errors)
        self.assertIn("related_entities must be a list", errors)
        self.assertIn("confidence must be a number from 0 to 1", errors)

    def test_openai_adapter_response_validation_does_not_store_raw_response(self):
        valid_output = {
            "title": "Validated OpenAI signal",
            "summary": "A concise validated summary.",
            "why_it_matters": "It changes the AGI infrastructure watchlist.",
            "agi_capability": "Agents",
            "related_entities": ["OpenAI"],
            "confidence": 0.8,
            "watch_next": "Track follow-up product evidence.",
            "source_url": "https://openai.com/example",
        }
        fake_response = {
            "output_text": json.dumps(valid_output),
            "usage": {"input_tokens": 10, "output_tokens": 20, "total_tokens": 30},
        }

        class FakeHTTPResponse:
            status = 200

            def read(self):
                return json.dumps(fake_response).encode("utf-8")

        class FakeConnection:
            def __init__(self, *args, **kwargs):
                self.headers = None

            def request(self, method, path, body=None, headers=None):
                self.headers = headers

            def getresponse(self):
                return FakeHTTPResponse()

            def close(self):
                return None

        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_report = self.write_candidate_report(tmpdir)
            with mock.patch("http.client.HTTPSConnection", return_value=FakeConnection()) as connection_mock:
                report = provider.run_provider(
                    candidate_report,
                    provider="openai",
                    allow_real_llm=True,
                    api_key="test-api-key-placeholder",
                    max_items=1,
                    created_at=FIXED_TIME,
                )

        connection_mock.assert_called_once()
        self.assertTrue(report["real_llm_api_used"])
        self.assertTrue(report["llm_api_calls_performed"])
        self.assertFalse(report["raw_provider_response_stored"])
        self.assertEqual(report["estimated_token_usage"]["total_tokens"], 30)
        self.assertEqual(report["intelligence_signals_created"], 1)
        serialized_report = json.dumps(report)
        self.assertNotIn("test-api-key-placeholder", serialized_report)
        self.assertNotIn(json.dumps(fake_response), serialized_report)

    def test_no_publishing_social_or_deployment_side_effects(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_report = self.write_candidate_report(tmpdir)
            report = provider.run_provider(candidate_report, provider="fake", created_at=FIXED_TIME)

        for flag in (
            "publishing_performed",
            "website_pages_written",
            "public_content_files_written",
            "social_posting_performed",
            "deployment_performed",
            "notion_write_operations_performed",
            "live_github_api_used",
            "article_body_scraping_performed",
            "raw_provider_response_stored",
        ):
            self.assertFalse(report[flag])

    def test_cli_does_not_print_secret_when_gate_blocks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_report = self.write_candidate_report(tmpdir)
            output = pathlib.Path(tmpdir) / "blocked.json"
            with mock.patch("builtins.print") as print_mock:
                exit_code = provider.main(
                    [
                        "--signal-candidates",
                        str(candidate_report),
                        "--provider",
                        "openai",
                        "--max-items",
                        "1",
                        "--output",
                        str(output),
                    ]
                )

        self.assertEqual(exit_code, 2)
        printed = "\n".join(str(call.args[0]) for call in print_mock.call_args_list)
        self.assertNotIn("OPENAI_API_KEY" + "=", printed)
        self.assertNotIn("sk-", printed)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
