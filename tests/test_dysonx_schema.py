import pathlib
import sys
import unittest
from dataclasses import fields
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_schema


class DysonXSchemaTests(unittest.TestCase):
    def test_raw_item_is_separate_from_signal(self):
        raw_item_fields = {field.name for field in fields(dysonx_schema.RawItem)}
        signal_fields = {field.name for field in fields(dysonx_schema.Signal)}

        self.assertIn("raw_title", raw_item_fields)
        self.assertIn("content_hash", raw_item_fields)
        self.assertNotIn("publish_status", raw_item_fields)
        self.assertNotIn("signal_id", raw_item_fields)

        self.assertIn("signal_candidate_id", signal_fields)
        self.assertIn("publish_status", signal_fields)
        self.assertNotIn("raw_content", signal_fields)

    def test_llm_analysis_job_is_separate_from_signal_candidate(self):
        llm_fields = {field.name for field in fields(dysonx_schema.LLMAnalysisJob)}
        candidate_fields = {field.name for field in fields(dysonx_schema.SignalCandidate)}

        self.assertIn("provider", llm_fields)
        self.assertIn("model_name", llm_fields)
        self.assertIn("prompt_version", llm_fields)
        self.assertIn("output_json", llm_fields)
        self.assertNotIn("suggested_title_en", llm_fields)

        self.assertIn("llm_analysis_job_id", candidate_fields)
        self.assertIn("suggested_title_en", candidate_fields)
        self.assertNotIn("model_name", candidate_fields)

    def test_signal_candidate_is_separate_from_published_signal(self):
        candidate_fields = {field.name for field in fields(dysonx_schema.SignalCandidate)}
        signal_fields = {field.name for field in fields(dysonx_schema.Signal)}

        self.assertIn("suggested_publish_status", candidate_fields)
        self.assertIn("review_status", candidate_fields)
        self.assertNotIn("published_at", candidate_fields)

        self.assertIn("signal_candidate_id", signal_fields)
        self.assertIn("publish_status", signal_fields)
        self.assertIn("published_at", signal_fields)
        self.assertNotIn("review_status", signal_fields)

    def test_social_draft_is_draft_only(self):
        draft = dysonx_schema.SocialDraft(
            id="social_draft_1",
            signal_id="signal_1",
            platform="x",
            language="English",
            draft_text="Draft text",
            status="draft",
            created_at=datetime.now(timezone.utc),
        )

        self.assertEqual(draft.status, "draft")
        self.assertNotIn("posted", dysonx_schema.SocialDraft.DRAFT_ONLY_STATUSES)

        with self.assertRaises(ValueError):
            dysonx_schema.SocialDraft(
                id="social_draft_2",
                signal_id="signal_1",
                platform="x",
                language="English",
                draft_text="Posted text",
                status="posted",
            )

    def test_no_knowledge_graph_tables_are_implemented_in_v1(self):
        implemented = set(dysonx_schema.v1_schema_entity_names())
        out_of_scope = dysonx_schema.out_of_scope_schema_entity_names()

        self.assertEqual(
            implemented,
            {
                "Source",
                "RawItem",
                "LLMAnalysisJob",
                "SignalCandidate",
                "Signal",
                "QualityReview",
                "PublishJob",
                "SocialDraft",
            },
        )
        self.assertTrue(implemented.isdisjoint(out_of_scope))


if __name__ == "__main__":
    unittest.main()
