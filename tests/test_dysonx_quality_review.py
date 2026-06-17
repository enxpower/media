import copy
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_llm_audit as llm_audit
import dysonx_publish_eligibility as publish_eligibility
import dysonx_signal_ranking as ranking


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "raw_items_v1.json"
FIXED_TIME = "2026-06-17T10:00:00+00:00"


class DysonXQualityReviewTests(unittest.TestCase):
    def ranking_report(self):
        candidate_records = llm_audit.load_candidate_records_from_raw_fixture(FIXTURE_PATH)
        audit_report = llm_audit.run_llm_audit(candidate_records, created_at=FIXED_TIME)
        result = ranking.rank_signals(audit_report["signals"], top_n=10, created_at=FIXED_TIME)
        return ranking.ranking_result_to_report(result)

    def high_quality_ranked_signal(self):
        return self.ranking_report()["ranked_signals"][0]

    def test_high_quality_ranked_signal_becomes_publish_ready(self):
        report = publish_eligibility.run_quality_review(
            {"ranking_id": "ranking_test", "ranked_signals": [self.high_quality_ranked_signal()]},
            created_at=FIXED_TIME,
        )

        self.assertEqual(report["status_counts"]["publish_ready"], 1)
        self.assertTrue(report["eligibilities"][0]["eligible"])
        self.assertEqual(report["eligibilities"][0]["eligibility_status"], "publish_ready")

    def test_weak_signal_becomes_needs_review(self):
        weak = copy.deepcopy(self.high_quality_ranked_signal())
        weak["score"]["confidence_score"] = 0.65
        weak["signal"]["confidence"] = 0.65

        report = publish_eligibility.run_quality_review(
            {"ranking_id": "ranking_test", "ranked_signals": [weak]},
            created_at=FIXED_TIME,
        )

        self.assertEqual(report["status_counts"]["needs_review"], 1)
        self.assertTrue(report["eligibilities"][0]["required_manual_review"])

    def test_invalid_signal_becomes_rejected(self):
        invalid = copy.deepcopy(self.high_quality_ranked_signal())
        invalid["score"]["confidence_score"] = 0.2
        invalid["score"]["composite_score"] = 0.2

        report = publish_eligibility.run_quality_review(
            {"ranking_id": "ranking_test", "ranked_signals": [invalid]},
            created_at=FIXED_TIME,
        )

        self.assertEqual(report["status_counts"]["rejected"], 1)
        self.assertFalse(report["eligibilities"][0]["eligible"])

    def test_missing_source_attribution_blocks_publish_ready(self):
        missing_source = copy.deepcopy(self.high_quality_ranked_signal())
        missing_source["signal"]["source_id"] = ""

        report = publish_eligibility.run_quality_review(
            {"ranking_id": "ranking_test", "ranked_signals": [missing_source]},
            created_at=FIXED_TIME,
        )

        self.assertEqual(report["reviews"][0]["decision"], "rejected")
        self.assertIn("source_id", report["reviews"][0]["failed_checks"])

    def test_missing_summary_blocks_publish_ready(self):
        missing_summary = copy.deepcopy(self.high_quality_ranked_signal())
        missing_summary["signal"]["summary"] = ""

        report = publish_eligibility.run_quality_review(
            {"ranking_id": "ranking_test", "ranked_signals": [missing_summary]},
            created_at=FIXED_TIME,
        )

        self.assertEqual(report["reviews"][0]["decision"], "rejected")
        self.assertIn("summary", report["reviews"][0]["failed_checks"])

    def test_duplicate_fatal_warning_blocks_publish_ready(self):
        duplicate = copy.deepcopy(self.high_quality_ranked_signal())
        duplicate["warnings"] = ["duplicate fatal"]

        report = publish_eligibility.run_quality_review(
            {"ranking_id": "ranking_test", "ranked_signals": [duplicate]},
            created_at=FIXED_TIME,
        )

        self.assertEqual(report["reviews"][0]["decision"], "rejected")
        self.assertIn("duplicate", report["reviews"][0]["failed_checks"])

    def test_review_report_is_deterministic(self):
        ranking_report = self.ranking_report()
        first = publish_eligibility.run_quality_review(ranking_report, created_at=FIXED_TIME)
        second = publish_eligibility.run_quality_review(ranking_report, created_at=FIXED_TIME)

        self.assertEqual(first, second)

    def test_no_publishing_social_posting_or_real_llm_calls_occur(self):
        report = publish_eligibility.run_quality_review(self.ranking_report(), created_at=FIXED_TIME)
        module_source = pathlib.Path(publish_eligibility.__file__).read_text(encoding="utf-8").lower()

        self.assertFalse(report["publishing_performed"])
        self.assertFalse(report["social_posting_performed"])
        self.assertFalse(report["real_llm_api_used"])
        self.assertNotIn("import openai", module_source)
        self.assertNotIn("from openai", module_source)
        self.assertNotIn("import anthropic", module_source)
        self.assertNotIn("from anthropic", module_source)

    def test_cli_writes_quality_review_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_output = pathlib.Path(tmpdir) / "llm_audit.json"
            ranking_output = pathlib.Path(tmpdir) / "ranking.json"
            quality_output = pathlib.Path(tmpdir) / "quality.json"

            llm_audit.main(["--raw-fixture", str(FIXTURE_PATH), "--output", str(audit_output)])
            ranking.main(["--intelligence-report", str(audit_output), "--output", str(ranking_output), "--top-n", "10"])
            exit_code = publish_eligibility.main(["--ranking-report", str(ranking_output), "--output", str(quality_output)])

            self.assertEqual(exit_code, 0)
            report = json.loads(quality_output.read_text(encoding="utf-8"))
            self.assertEqual(report["signals_reviewed"], 4)
            self.assertEqual(report["status_counts"]["publish_ready"], 4)
            self.assertFalse(report["publishing_performed"])


if __name__ == "__main__":
    unittest.main()
