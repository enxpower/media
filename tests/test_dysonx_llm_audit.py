import pathlib
import sys
import tempfile
import unittest
import json
from dataclasses import fields
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_llm_audit as audit
from dysonx_llm_job import AuditRecordV1, LLMJobV1, ModelRunV1, OutputValidationV1
from dysonx_output_validation import validate_intelligence_output
from dysonx_prompt_registry import get_prompt_template, list_prompt_templates


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "raw_items_v1.json"
FIXED_TIME = "2026-06-17T10:00:00+00:00"


class DysonXLLMJobAuditTests(unittest.TestCase):
    def candidate_records(self):
        return audit.load_candidate_records_from_raw_fixture(FIXTURE_PATH)

    def test_provider_neutral_job_structures_exist(self):
        job_fields = {field.name for field in fields(LLMJobV1)}
        run_fields = {field.name for field in fields(ModelRunV1)}
        validation_fields = {field.name for field in fields(OutputValidationV1)}
        audit_fields = {field.name for field in fields(AuditRecordV1)}

        self.assertEqual(
            job_fields,
            {"job_id", "candidate_id", "provider", "model", "prompt_template_version", "status", "created_at"},
        )
        self.assertIn("provider", run_fields)
        self.assertIn("model", run_fields)
        self.assertIn("validation_rules", validation_fields)
        self.assertIn("validation_id", audit_fields)

    def test_prompt_versioning_works(self):
        template = get_prompt_template("intelligence_signal_extraction", "v1")

        self.assertEqual(template.template_version, "v1")
        self.assertIn(template, list_prompt_templates())
        self.assertIn("Do not write an article", template.template_text)

    def test_audit_chain_remains_intact(self):
        report = audit.run_llm_audit(self.candidate_records(), created_at=FIXED_TIME)

        self.assertEqual(report["jobs_created"], 4)
        self.assertEqual(report["runs_completed"], 4)
        self.assertEqual(report["validations_passed"], 4)
        self.assertEqual(report["validations_failed"], 0)
        self.assertEqual(report["signals_generated"], 4)

        job_ids = {job["job_id"] for job in report["jobs"]}
        run_ids = {run["run_id"] for run in report["runs"]}
        validation_ids = {validation["validation_id"] for validation in report["validations"]}

        for record in report["audit_records"]:
            self.assertIn(record["job_id"], job_ids)
            self.assertIn(record["run_id"], run_ids)
            self.assertIn(record["validation_id"], validation_ids)

    def test_validation_failures_are_captured(self):
        passed, warnings = validate_intelligence_output(
            {
                "title": "Bad output",
                "signal_type": "model_release",
                "importance": "urgent",
                "confidence": 1.5,
                "summary": "",
            }
        )

        self.assertFalse(passed)
        self.assertIn("importance must be one of: high, low, medium", warnings)
        self.assertIn("confidence must be a number from 0 to 1", warnings)
        self.assertIn("summary must be present", warnings)

    def test_intelligence_signal_generation_still_works(self):
        report = audit.run_llm_audit(self.candidate_records(), created_at=FIXED_TIME)
        first_signal = report["signals"][0]

        self.assertTrue(first_signal["signal_id"].startswith("signal_"))
        self.assertIn("summary", first_signal)
        self.assertIn("affected_entities", first_signal)
        self.assertEqual(report["provider_distribution"], {"fake": 4})
        self.assertEqual(report["prompt_versions_used"], {"v1": 4})

    def test_no_provider_specific_dependency_exists(self):
        module_source = pathlib.Path(audit.__file__).read_text(encoding="utf-8").lower()

        self.assertNotIn("import openai", module_source)
        self.assertNotIn("from openai", module_source)
        self.assertNotIn("import anthropic", module_source)
        self.assertNotIn("from anthropic", module_source)
        self.assertNotIn("google.generativeai", module_source)
        self.assertNotIn("import requests", module_source)
        self.assertNotIn("from requests", module_source)
        self.assertNotIn("import urllib", module_source)
        self.assertNotIn("from urllib", module_source)

    def test_no_network_requests_occur(self):
        with mock.patch("socket.socket") as socket_mock:
            report = audit.run_llm_audit(self.candidate_records(), created_at=FIXED_TIME)

        socket_mock.assert_not_called()
        self.assertFalse(report["network_requests_performed"])
        self.assertFalse(report["real_llm_api_used"])
        self.assertFalse(report["publishing_performed"])

    def test_cli_writes_audit_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "llm_audit_report.json"
            exit_code = audit.main(["--raw-fixture", str(FIXTURE_PATH), "--output", str(output)])

            self.assertEqual(exit_code, 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["jobs_created"], 4)
            self.assertEqual(report["validations_passed"], 4)
            self.assertEqual(report["signals_generated"], 4)


if __name__ == "__main__":
    unittest.main()
