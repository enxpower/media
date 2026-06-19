import json
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_collector_foundation
import dysonx_publish_eligibility
import dysonx_publish_package
import dysonx_rawitem_signal_pipeline
import dysonx_real_llm_provider
import dysonx_signal_ranking
import dysonx_v1_intelligence_pipeline as pipeline


SOURCE_STORE = ROOT / "tests" / "fixtures" / "source_sync_store_v1.json"


class DysonXV1IntelligencePipelineTests(unittest.TestCase):
    def test_pipeline_writes_all_intermediate_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = pipeline.run_pipeline(SOURCE_STORE, tmpdir)
            output_dir = pathlib.Path(tmpdir)

            for report_name in (
                "collector_report.json",
                "raw_items_store.json",
                "signal_candidate_report.json",
                "llm_audit_report.json",
                "signal_ranking_report.json",
                "quality_review_report.json",
                "publish_package_report.json",
                "v1_intelligence_pipeline_report.json",
            ):
                self.assertTrue((output_dir / report_name).exists(), report_name)

            disk_report = json.loads((output_dir / "v1_intelligence_pipeline_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report, disk_report)

    def test_counts_are_consistent_across_layers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = pipeline.run_pipeline(SOURCE_STORE, tmpdir)

            self.assertEqual(report["sources_seen"], 3)
            self.assertEqual(report["raw_items_created"], 3)
            self.assertEqual(report["signal_candidates_created"], 3)
            self.assertEqual(report["llm_jobs_created"], 3)
            self.assertEqual(report["intelligence_signals_created"], 3)
            self.assertEqual(report["signals_ranked"], 3)
            self.assertEqual(report["packages_created"], report["publish_ready"])

    def test_existing_layers_are_reused(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                mock.patch("dysonx_collector_foundation.run_collection", wraps=dysonx_collector_foundation.run_collection) as collector_mock,
                mock.patch("dysonx_rawitem_signal_pipeline.run_integration", wraps=dysonx_rawitem_signal_pipeline.run_integration) as rawitem_mock,
                mock.patch("dysonx_real_llm_provider.run_provider", wraps=dysonx_real_llm_provider.run_provider) as provider_mock,
                mock.patch("dysonx_signal_ranking.rank_signals", wraps=dysonx_signal_ranking.rank_signals) as ranking_mock,
                mock.patch("dysonx_publish_eligibility.run_quality_review", wraps=dysonx_publish_eligibility.run_quality_review) as quality_mock,
                mock.patch("dysonx_publish_package.run_publish_package", wraps=dysonx_publish_package.run_publish_package) as package_mock,
            ):
                report = pipeline.run_pipeline(SOURCE_STORE, tmpdir)

            collector_mock.assert_called_once()
            rawitem_mock.assert_called_once()
            provider_mock.assert_called_once()
            ranking_mock.assert_called_once()
            quality_mock.assert_called_once()
            package_mock.assert_called_once()
            self.assertTrue(report["module_reuse"]["collector_foundation_reused"])
            self.assertTrue(report["module_reuse"]["rawitem_signal_pipeline_reused"])
            self.assertTrue(report["module_reuse"]["signal_candidate_pipeline_reused"])
            self.assertTrue(report["module_reuse"]["real_llm_provider_reused"])
            self.assertFalse(report["module_reuse"]["duplicate_provider_logic_introduced"])
            self.assertTrue(report["module_reuse"]["signal_ranking_reused"])
            self.assertTrue(report["module_reuse"]["quality_review_reused"])
            self.assertTrue(report["module_reuse"]["publish_package_reused"])

    def test_layer_boundaries_are_not_bypassed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = pipeline.run_pipeline(SOURCE_STORE, tmpdir)

            self.assertTrue(report["layer_boundaries"]["rawitem_separate_from_signal_candidate"])
            self.assertTrue(report["layer_boundaries"]["signal_candidate_separate_from_intelligence_signal"])
            self.assertTrue(report["layer_boundaries"]["intelligence_signal_separate_from_publish_package"])
            self.assertTrue(report["layer_boundaries"]["collector_stops_at_rawitem_persistence"])
            self.assertEqual(report["rejected_or_skipped"]["candidate_rejected"], 0)

    def test_fake_provider_remains_default_and_safety_flags_false(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = pipeline.run_pipeline(SOURCE_STORE, tmpdir)

            self.assertEqual(report["provider"], "fake")
            self.assertEqual(report["items_requested"], 3)
            self.assertEqual(report["items_processed"], 3)
            self.assertEqual(report["prompt_version"], dysonx_real_llm_provider.PROMPT_VERSION)
            self.assertIn("publish_package_created", report)
            self.assertFalse(report["notion_write_operations_performed"])
            self.assertFalse(report["live_github_api_used"])
            self.assertFalse(report["real_llm_api_used"])
            self.assertFalse(report["llm_api_calls_performed"])
            self.assertFalse(report["publishing_performed"])
            self.assertFalse(report["website_pages_written"])
            self.assertFalse(report["public_content_files_written"])
            self.assertFalse(report["social_posting_performed"])
            self.assertFalse(report["article_body_scraping_performed"])
            self.assertFalse(report["deployment_performed"])

    def test_orchestrator_can_invoke_existing_openai_provider_path(self):
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

        with tempfile.TemporaryDirectory() as tmpdir:
            with (
                mock.patch.dict("os.environ", {"OPENAI_API_KEY": "test-api-key-placeholder"}),
                mock.patch(
                    "dysonx_real_llm_provider.call_openai_provider",
                    return_value=(valid_output, {"total_tokens": 42}),
                ) as openai_mock,
                mock.patch("dysonx_real_llm_provider.run_provider", wraps=dysonx_real_llm_provider.run_provider) as provider_mock,
            ):
                report = pipeline.run_pipeline(
                    SOURCE_STORE,
                    tmpdir,
                    provider="openai",
                    allow_real_llm=True,
                    max_items=1,
                )

            provider_mock.assert_called_once()
            openai_mock.assert_called_once()
            self.assertEqual(report["provider"], "openai")
            self.assertTrue(report["real_llm_api_used"])
            self.assertTrue(report["llm_api_calls_performed"])
            self.assertEqual(report["items_requested"], 1)
            self.assertEqual(report["items_processed"], 1)
            self.assertEqual(report["prompt_version"], dysonx_real_llm_provider.PROMPT_VERSION)
            self.assertFalse(report["publishing_performed"])
            self.assertFalse(report["deployment_performed"])

    def test_missing_openai_gate_conditions_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = pipeline.main(
                [
                    "--source-store",
                    str(SOURCE_STORE),
                    "--output-dir",
                    tmpdir,
                    "--provider",
                    "openai",
                    "--max-items",
                    "1",
                ]
            )

        self.assertEqual(exit_code, 2)

    def test_report_fields_are_populated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = pipeline.run_pipeline(SOURCE_STORE, tmpdir)

            for field_name in (
                "provider",
                "real_llm_api_used",
                "llm_api_calls_performed",
                "items_requested",
                "items_processed",
                "prompt_version",
                "publish_package_created",
                "raw_provider_response_stored",
            ):
                self.assertIn(field_name, report)

    def test_no_prohibited_integrations_are_present(self):
        module_source = pathlib.Path(pipeline.__file__).read_text(encoding="utf-8").lower()

        self.assertNotIn("import openai", module_source)
        self.assertNotIn("from openai", module_source)
        self.assertNotIn("import anthropic", module_source)
        self.assertNotIn("import google.generativeai", module_source)
        self.assertNotIn("http.client", module_source)
        self.assertNotIn("openai_host", module_source)
        self.assertNotIn("api.github.com", module_source)
        self.assertNotIn("api.notion.com", module_source)
        self.assertNotIn("requests", module_source)
        self.assertNotIn("urllib.request", module_source)
        self.assertNotIn("import schedule", module_source)
        self.assertNotIn("from schedule", module_source)
        self.assertNotIn(".every(", module_source)


if __name__ == "__main__":
    unittest.main()
