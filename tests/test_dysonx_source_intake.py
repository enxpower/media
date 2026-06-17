import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_source_intake as intake
from dysonx_notion_readonly_adapter import NotionReadOnlyAdapterNotConfigured, NotionReadOnlySourceClient


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "notion_sources_v1.json"


class DysonXSourceIntakeTests(unittest.TestCase):
    def test_fixture_dry_run_works(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = pathlib.Path(tmpdir) / "report.json"
            exit_code = intake.main(["--fixture", str(FIXTURE_PATH), "--dry-run", "--output", str(output)])

            self.assertEqual(exit_code, 0)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(report["mode"], "fixture")
            self.assertTrue(report["dry_run"])
            self.assertEqual(report["total_records"], 4)

    def test_missing_notion_env_vars_fail_closed(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(NotionReadOnlyAdapterNotConfigured):
                NotionReadOnlySourceClient.from_env().list_source_records()

    def test_adapter_remains_read_only(self):
        client = NotionReadOnlySourceClient(token="token", database_id="database")

        self.assertTrue(hasattr(client, "list_source_records"))
        self.assertFalse(hasattr(client, "create_source_record"))
        self.assertFalse(hasattr(client, "update_source_record"))
        self.assertFalse(hasattr(client, "delete_source_record"))

    def test_invalid_records_are_reported_without_crashing_full_run(self):
        report = intake.run_fixture_intake(FIXTURE_PATH, dry_run=True)

        self.assertEqual(report["rejected_record_count"], 3)
        self.assertIn("Missing URL Source", report["validation_errors"])
        self.assertIn("Invalid Authority Source", report["validation_errors"])

    def test_eligible_source_count_is_reported(self):
        report = intake.run_fixture_intake(FIXTURE_PATH, dry_run=True)

        self.assertEqual(report["eligible_source_count"], 1)
        self.assertEqual(report["eligible_sources"][0]["name"], "OpenAI Blog")

    def test_no_network_call_happens_in_fixture_mode(self):
        with mock.patch("socket.socket") as socket_mock:
            report = intake.run_fixture_intake(FIXTURE_PATH, dry_run=True)

        socket_mock.assert_not_called()
        self.assertEqual(report["mode"], "fixture")


if __name__ == "__main__":
    unittest.main()
