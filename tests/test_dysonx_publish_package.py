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
import dysonx_publish_package as publish_package
import dysonx_signal_ranking as ranking
from dysonx_social_draft import SocialDraftV1


FIXTURE_PATH = ROOT / "tests" / "fixtures" / "raw_items_v1.json"
FIXED_TIME = "2026-06-17T10:00:00+00:00"


class DysonXPublishPackageTests(unittest.TestCase):
    def quality_report(self):
        candidate_records = llm_audit.load_candidate_records_from_raw_fixture(FIXTURE_PATH)
        audit_report = llm_audit.run_llm_audit(candidate_records, created_at=FIXED_TIME)
        ranking_result = ranking.rank_signals(audit_report["signals"], top_n=10, created_at=FIXED_TIME)
        ranking_report = ranking.ranking_result_to_report(ranking_result)
        quality_report = publish_eligibility.run_quality_review(ranking_report, created_at=FIXED_TIME)
        quality_report["ranking_report"] = ranking_report
        return quality_report

    def test_only_publish_ready_signals_become_packages(self):
        report = publish_package.run_publish_package(self.quality_report(), created_at=FIXED_TIME)

        self.assertEqual(report["packages_created"], 4)
        self.assertEqual(report["skipped"], [])

    def test_needs_review_signals_do_not_become_packages(self):
        quality = self.quality_report()
        quality["eligibilities"][0]["eligibility_status"] = "needs_review"

        report = publish_package.run_publish_package(quality, created_at=FIXED_TIME)

        self.assertEqual(report["packages_created"], 3)
        self.assertEqual(report["skipped"][0]["reason"], "eligibility_status=needs_review")

    def test_rejected_signals_do_not_become_packages(self):
        quality = self.quality_report()
        quality["eligibilities"][0]["eligibility_status"] = "rejected"

        report = publish_package.run_publish_package(quality, created_at=FIXED_TIME)

        self.assertEqual(report["packages_created"], 3)
        self.assertEqual(report["skipped"][0]["reason"], "eligibility_status=rejected")

    def test_slug_generation_is_deterministic(self):
        title = "OpenAI Releases GPT-6 for Advanced Reasoning!"

        self.assertEqual(
            publish_package.slugify(title),
            "openai-releases-gpt-6-for-advanced-reasoning",
        )
        self.assertEqual(publish_package.slugify(title), publish_package.slugify(title))

    def test_seo_metadata_is_generated(self):
        report = publish_package.run_publish_package(self.quality_report(), created_at=FIXED_TIME)
        metadata = report["packages"][0]["seo_metadata"]

        self.assertIn("canonical_url", metadata)
        self.assertIn("/signals/", metadata["canonical_url"])
        self.assertLessEqual(len(metadata["title"]), 70)
        self.assertTrue(report["packages"][0]["title"].startswith(metadata["title"].rstrip(".")))

    def test_social_drafts_are_draft_only(self):
        report = publish_package.run_publish_package(self.quality_report(), created_at=FIXED_TIME)

        for package in report["packages"]:
            for draft in package["social_drafts"]:
                self.assertEqual(draft["status"], "draft_only")

        with self.assertRaises(ValueError):
            SocialDraftV1(platform="x", draft_text="post", link_url="https://example.com", status="posted")

    def test_english_remains_canonical(self):
        report = publish_package.run_publish_package(self.quality_report(), created_at=FIXED_TIME)

        self.assertEqual(report["canonical_language"], "en")
        self.assertIn("zh", report["localized_languages"])
        self.assertTrue(all(package["canonical_language"] == "en" for package in report["packages"]))

    def test_no_publishing_social_posting_or_real_llm_calls_occur(self):
        report = publish_package.run_publish_package(self.quality_report(), created_at=FIXED_TIME)
        module_source = pathlib.Path(publish_package.__file__).read_text(encoding="utf-8").lower()

        self.assertFalse(report["website_pages_written"])
        self.assertFalse(report["public_content_files_written"])
        self.assertFalse(report["publishing_performed"])
        self.assertFalse(report["social_posting_performed"])
        self.assertFalse(report["real_llm_api_used"])
        self.assertNotIn("import openai", module_source)
        self.assertNotIn("from openai", module_source)
        self.assertNotIn("import anthropic", module_source)
        self.assertNotIn("from anthropic", module_source)

    def test_cli_writes_publish_package_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_output = pathlib.Path(tmpdir) / "llm_audit.json"
            ranking_output = pathlib.Path(tmpdir) / "ranking.json"
            quality_output = pathlib.Path(tmpdir) / "quality.json"
            package_output = pathlib.Path(tmpdir) / "packages.json"

            llm_audit.main(["--raw-fixture", str(FIXTURE_PATH), "--output", str(audit_output)])
            ranking.main(["--intelligence-report", str(audit_output), "--output", str(ranking_output), "--top-n", "10"])
            publish_eligibility.main(["--ranking-report", str(ranking_output), "--output", str(quality_output)])

            quality = json.loads(quality_output.read_text(encoding="utf-8"))
            ranking_report = json.loads(ranking_output.read_text(encoding="utf-8"))
            quality["ranking_report"] = ranking_report
            quality_output.write_text(json.dumps(quality), encoding="utf-8")

            exit_code = publish_package.main(["--quality-report", str(quality_output), "--output", str(package_output)])

            self.assertEqual(exit_code, 0)
            report = json.loads(package_output.read_text(encoding="utf-8"))
            self.assertEqual(report["packages_created"], 4)
            self.assertFalse(report["publishing_performed"])


if __name__ == "__main__":
    unittest.main()
