import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_v1_pipeline as pipeline


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "raw_items_v1.json"


class DysonXV1PipelineTests(unittest.TestCase):
    def test_full_dry_run_pipeline_completes_and_creates_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = pipeline.run_pipeline(FIXTURE_PATH, tmpdir, dry_run=True)
            output_dir = pathlib.Path(tmpdir)

            expected_reports = (
                "llm_audit_report.json",
                "signal_ranking_report.json",
                "quality_review_report.json",
                "publish_package_report.json",
                "pipeline_summary.json",
            )
            for report_name in expected_reports:
                self.assertTrue((output_dir / report_name).exists(), report_name)

            disk_summary = json.loads((output_dir / "pipeline_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary, disk_summary)

    def test_output_counts_are_consistent_across_stages(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = pipeline.run_pipeline(FIXTURE_PATH, tmpdir, dry_run=True)
            output_dir = pathlib.Path(tmpdir)
            llm_audit = json.loads((output_dir / "llm_audit_report.json").read_text(encoding="utf-8"))
            ranking = json.loads((output_dir / "signal_ranking_report.json").read_text(encoding="utf-8"))
            quality = json.loads((output_dir / "quality_review_report.json").read_text(encoding="utf-8"))
            packages = json.loads((output_dir / "publish_package_report.json").read_text(encoding="utf-8"))

            self.assertEqual(summary["raw_items_seen"], 5)
            self.assertEqual(summary["candidates_created"], 4)
            self.assertEqual(summary["signals_generated"], llm_audit["signals_generated"])
            self.assertEqual(summary["signals_ranked"], ranking["audit_summary"]["signals_ranked"])
            self.assertEqual(summary["publish_ready"], quality["status_counts"]["publish_ready"])
            self.assertEqual(summary["packages_created"], packages["packages_created"])

    def test_dry_run_and_no_side_effect_flags_remain_true(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = pipeline.run_pipeline(FIXTURE_PATH, tmpdir, dry_run=True)

            self.assertTrue(summary["dry_run"])
            self.assertFalse(summary["real_llm_api_used"])
            self.assertFalse(summary["publishing_performed"])
            self.assertFalse(summary["social_posting_performed"])
            self.assertFalse(summary["network_requests_performed"])

    def test_pipeline_fails_closed_without_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                pipeline.run_pipeline(FIXTURE_PATH, tmpdir, dry_run=False)

    def test_cli_writes_pipeline_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = pipeline.main(["--raw-fixture", str(FIXTURE_PATH), "--output-dir", tmpdir, "--dry-run"])

            self.assertEqual(exit_code, 0)
            summary = json.loads((pathlib.Path(tmpdir) / "pipeline_summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["raw_items_seen"], 5)
            self.assertEqual(summary["packages_created"], 4)
            self.assertTrue(summary["dry_run"])


if __name__ == "__main__":
    unittest.main()
