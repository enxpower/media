import json
import pathlib
import sys
import tempfile
import unittest
from dataclasses import fields
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_signal_candidate_pipeline as pipeline
from dysonx_raw_item import RawItemV1, SignalCandidateV1


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "raw_items_v1.json"
FIXED_TIME = "2026-06-17T10:00:00+00:00"


class DysonXSignalCandidatePipelineTests(unittest.TestCase):
    def test_raw_item_and_signal_candidate_remain_separate(self):
        raw_fields = {field.name for field in fields(RawItemV1)}
        candidate_fields = {field.name for field in fields(SignalCandidateV1)}

        self.assertIn("raw_content", raw_fields)
        self.assertIn("metadata", raw_fields)
        self.assertNotIn("candidate_id", raw_fields)
        self.assertNotIn("candidate_type", raw_fields)

        self.assertIn("candidate_id", candidate_fields)
        self.assertIn("candidate_type", candidate_fields)
        self.assertNotIn("raw_content", candidate_fields)

    def test_candidate_generation_is_deterministic(self):
        records = pipeline.load_raw_item_records(FIXTURE_PATH)
        first = pipeline.run_pipeline(records, created_at=FIXED_TIME)
        second = pipeline.run_pipeline(records, created_at=FIXED_TIME)

        self.assertEqual(first["candidates"], second["candidates"])
        self.assertEqual(
            first["candidate_types"],
            {
                "company_announcement": 1,
                "model_release": 1,
                "regulation": 1,
                "research_update": 1,
            },
        )

    def test_invalid_raw_items_do_not_crash_processing(self):
        records = pipeline.load_raw_item_records(FIXTURE_PATH)
        report = pipeline.run_pipeline(records, created_at=FIXED_TIME)

        self.assertEqual(report["total_raw_items"], 5)
        self.assertEqual(report["candidates_created"], 4)
        self.assertEqual(len(report["rejected_items"]), 1)
        self.assertIn("title must be present", report["rejected_items"][0]["errors"])

    def test_audit_report_is_generated(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "candidate_report.json"
            exit_code = pipeline.main(["--fixture", str(FIXTURE_PATH), "--output", str(output)])

            self.assertEqual(exit_code, 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["candidates_created"], 4)
            self.assertFalse(report["llm_used"])
            self.assertFalse(report["publishing_performed"])

    def test_no_llm_calls_occur(self):
        module_source = pathlib.Path(pipeline.__file__).read_text(encoding="utf-8")

        self.assertNotIn("import openai", module_source.lower())
        self.assertNotIn("from openai", module_source.lower())
        self.assertNotIn("import anthropic", module_source.lower())
        self.assertNotIn("from anthropic", module_source.lower())
        self.assertNotIn("chat.completions", module_source)
        self.assertNotIn("responses.create", module_source)

    def test_no_network_requests_occur(self):
        with mock.patch("socket.socket") as socket_mock:
            records = pipeline.load_raw_item_records(FIXTURE_PATH)
            report = pipeline.run_pipeline(records, created_at=FIXED_TIME)

        socket_mock.assert_not_called()
        self.assertFalse(report["network_requests_performed"])


if __name__ == "__main__":
    unittest.main()
