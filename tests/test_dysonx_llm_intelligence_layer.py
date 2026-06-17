import json
import pathlib
import sys
import tempfile
import unittest
from dataclasses import fields
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_llm_intelligence_layer as layer
import dysonx_signal_candidate_pipeline as candidate_pipeline
from dysonx_intelligence_signal import IntelligenceSignalV1


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "raw_items_v1.json"
FIXED_TIME = "2026-06-17T10:00:00+00:00"


class DysonXLLMIntelligenceLayerTests(unittest.TestCase):
    def candidate_records(self):
        raw_records = candidate_pipeline.load_raw_item_records(FIXTURE_PATH)
        return candidate_pipeline.run_pipeline(raw_records, created_at=FIXED_TIME)["candidates"]

    def candidates(self):
        return [layer.candidate_from_record(record) for record in self.candidate_records()]

    def test_intelligence_signal_schema_is_signal_not_article(self):
        signal_fields = {field.name for field in fields(IntelligenceSignalV1)}

        self.assertIn("signal_id", signal_fields)
        self.assertIn("summary", signal_fields)
        self.assertIn("affected_entities", signal_fields)
        self.assertIn("impact_horizon", signal_fields)
        self.assertNotIn("article_body", signal_fields)
        self.assertNotIn("published_at", signal_fields)

    def test_llm_abstraction_and_fake_provider_work(self):
        provider = layer.FakeLLMProvider()
        candidate = self.candidates()[0]
        analysis = provider.analyze_candidate(candidate)

        self.assertEqual(provider.provider_name, "fake")
        self.assertIn("summary", analysis)
        self.assertIn("importance", analysis)
        self.assertGreaterEqual(analysis["confidence"], candidate.confidence)

    def test_intelligence_signal_generation_works(self):
        candidates = self.candidates()
        report = layer.run_intelligence_layer(candidates, provider=layer.FakeLLMProvider(), created_at=FIXED_TIME)

        self.assertEqual(report["candidates_processed"], 4)
        self.assertEqual(report["signals_generated"], 4)
        self.assertEqual(report["provider"], "fake")
        self.assertEqual(report["importance_distribution"], {"high": 2, "medium": 2})
        self.assertFalse(report["publishing_performed"])
        self.assertFalse(report["real_llm_api_used"])

    def test_generation_is_deterministic_with_fake_provider(self):
        candidates = self.candidates()
        first = layer.run_intelligence_layer(candidates, provider=layer.FakeLLMProvider(), created_at=FIXED_TIME)
        second = layer.run_intelligence_layer(candidates, provider=layer.FakeLLMProvider(), created_at=FIXED_TIME)

        self.assertEqual(first["signals"], second["signals"])
        self.assertEqual(first["confidence_distribution"], second["confidence_distribution"])

    def test_no_provider_specific_dependency_exists(self):
        module_source = pathlib.Path(layer.__file__).read_text(encoding="utf-8").lower()

        self.assertNotIn("import openai", module_source)
        self.assertNotIn("from openai", module_source)
        self.assertNotIn("import anthropic", module_source)
        self.assertNotIn("from anthropic", module_source)
        self.assertNotIn("google.generativeai", module_source)
        self.assertIn("fakellmprovider", module_source)

    def test_no_network_requests_or_publishing_occur(self):
        with mock.patch("socket.socket") as socket_mock:
            report = layer.run_intelligence_layer(self.candidates(), provider=layer.FakeLLMProvider(), created_at=FIXED_TIME)

        socket_mock.assert_not_called()
        self.assertFalse(report["network_requests_performed"])
        self.assertFalse(report["publishing_performed"])

    def test_cli_writes_audit_report_from_raw_fixture(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "intelligence_report.json"
            exit_code = layer.main(["--raw-fixture", str(FIXTURE_PATH), "--output", str(output)])

            self.assertEqual(exit_code, 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["signals_generated"], 4)
            self.assertEqual(report["provider_mode"], "fake_only")
            self.assertFalse(report["publishing_performed"])


if __name__ == "__main__":
    unittest.main()
