import copy
import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_llm_audit as llm_audit
import dysonx_signal_ranking as ranking
import dysonx_signal_scoring as scoring


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "raw_items_v1.json"
FIXED_TIME = "2026-06-17T10:00:00+00:00"


class DysonXSignalRankingTests(unittest.TestCase):
    def intelligence_signals(self):
        candidate_records = llm_audit.load_candidate_records_from_raw_fixture(FIXTURE_PATH)
        return llm_audit.run_llm_audit(candidate_records, created_at=FIXED_TIME)["signals"]

    def test_scoring_is_deterministic(self):
        signal = self.intelligence_signals()[0]
        reference_time = scoring.parse_timestamp(FIXED_TIME)

        first = scoring.score_signal(signal, reference_time=reference_time, created_at=FIXED_TIME)
        second = scoring.score_signal(signal, reference_time=reference_time, created_at=FIXED_TIME)

        self.assertEqual(first, second)

    def test_composite_score_is_calculated_correctly(self):
        score = scoring.calculate_composite_score(
            importance_score=1.0,
            authority_score=0.9,
            impact_score=0.95,
            confidence_score=0.75,
            freshness_score=1.0,
        )

        self.assertEqual(score, 0.9275)

    def test_ranking_order_is_stable(self):
        signals = self.intelligence_signals()
        first = ranking.rank_signals(signals, top_n=10, created_at=FIXED_TIME)
        second = ranking.rank_signals(signals, top_n=10, created_at=FIXED_TIME)

        first_ids = [item["signal"]["signal_id"] for item in first.ranked_signals]
        second_ids = [item["signal"]["signal_id"] for item in second.ranked_signals]

        self.assertEqual(first_ids, second_ids)
        self.assertEqual(first.ranked_signals[0]["rank"], 1)

    def test_low_confidence_signals_rank_lower(self):
        signals = self.intelligence_signals()
        low_confidence = copy.deepcopy(signals[0])
        low_confidence["signal_id"] = "signal_low_confidence"
        low_confidence["confidence"] = 0.05
        comparison = [signals[0], low_confidence]

        result = ranking.rank_signals(comparison, top_n=2, created_at=FIXED_TIME)
        ranked_ids = [item["signal"]["signal_id"] for item in result.ranked_signals]

        self.assertEqual(ranked_ids[-1], "signal_low_confidence")

    def test_missing_invalid_scoring_fields_are_handled_safely(self):
        invalid_signal = {
            "signal_id": "signal_invalid",
            "importance": "urgent",
            "confidence": "unknown",
            "signal_type": "",
            "source_id": "",
            "source_name": "",
            "created_at": "not-a-date",
        }

        result = ranking.rank_signals([invalid_signal], top_n=1, created_at=FIXED_TIME)
        ranked = result.ranked_signals[0]

        self.assertEqual(ranked["score"]["composite_score"], 0.12)
        self.assertTrue(result.audit_summary["invalid_or_missing_fields_handled"])
        self.assertIn("importance missing or invalid", ranked["score"]["scoring_reasons"])

    def test_no_llm_publishing_or_social_posting_occurs(self):
        signals = self.intelligence_signals()
        result = ranking.rank_signals(signals, top_n=10, created_at=FIXED_TIME)
        report = ranking.ranking_result_to_report(result)
        module_source = pathlib.Path(ranking.__file__).read_text(encoding="utf-8").lower()

        self.assertFalse(report["real_llm_api_used"])
        self.assertFalse(report["publishing_performed"])
        self.assertFalse(report["social_posting_performed"])
        self.assertNotIn("import openai", module_source)
        self.assertNotIn("from openai", module_source)
        self.assertNotIn("import anthropic", module_source)
        self.assertNotIn("from anthropic", module_source)
        self.assertNotIn("google.generativeai", module_source)

    def test_cli_writes_ranking_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_output = pathlib.Path(tmpdir) / "llm_audit.json"
            ranking_output = pathlib.Path(tmpdir) / "ranking.json"
            llm_audit.main(["--raw-fixture", str(FIXTURE_PATH), "--output", str(audit_output)])
            exit_code = ranking.main(
                ["--intelligence-report", str(audit_output), "--output", str(ranking_output), "--top-n", "10"]
            )

            self.assertEqual(exit_code, 0)
            report = json.loads(ranking_output.read_text(encoding="utf-8"))
            self.assertEqual(report["audit_summary"]["signals_seen"], 4)
            self.assertEqual(report["audit_summary"]["returned"], 4)
            self.assertEqual(report["top_n"], 10)


if __name__ == "__main__":
    unittest.main()
