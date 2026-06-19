import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "dysonx-openai-gated-smoke-test.yml"


class DysonXOpenAIGatedSmokeWorkflowTests(unittest.TestCase):
    def workflow_text(self) -> str:
        return WORKFLOW.read_text(encoding="utf-8")

    def test_workflow_dispatch_only(self):
        text = self.workflow_text()

        self.assertIn("workflow_dispatch:", text)
        self.assertNotRegex(text, re.compile(r"^\s+push:", re.MULTILINE))
        self.assertNotRegex(text, re.compile(r"^\s+pull_request:", re.MULTILINE))
        self.assertNotRegex(text, re.compile(r"^\s+schedule:", re.MULTILINE))
        self.assertNotIn("deployment_status:", text)

    def test_openai_secret_is_referenced_but_not_printed(self):
        text = self.workflow_text()

        self.assertIn("DYSONX_OPENAI_SMOKE_API_KEY: ${{ secrets.OPENAI_API_KEY }}", text)
        self.assertIn('env["OPENAI_API_KEY"] = env["DYSONX_OPENAI_SMOKE_API_KEY"]', text)
        self.assertNotIn("echo $OPENAI_API_KEY", text)
        self.assertNotIn("printenv OPENAI_API_KEY", text)
        self.assertNotIn("OPENAI_API_KEY" + "=", text)

    def test_openai_provider_gate_is_manual_and_capped(self):
        text = self.workflow_text()

        self.assertIn("scripts/dysonx_real_llm_provider.py", text)
        self.assertIn('"--provider"', text)
        self.assertIn('"openai"', text)
        self.assertIn("--allow-real-llm", text)
        self.assertIn('"--max-items"', text)
        self.assertIn('"1"', text)
        self.assertIn("tmp/dysonx_openai_smoke_report.json", text)

    def test_safety_assertions_cover_required_flags(self):
        text = self.workflow_text()

        for token in (
            '"provider": "openai"',
            '"real_llm_api_used": True',
            '"llm_api_calls_performed": True',
            '"publishing_performed": False',
            '"website_pages_written": False',
            '"public_content_files_written": False',
            '"social_posting_performed": False',
            '"deployment_performed": False',
            '"notion_write_operations_performed": False',
            '"live_github_api_used": False',
            '"article_body_scraping_performed": False',
            '"raw_provider_response_stored": False',
            'report.get("items_requested"',
            'report.get("items_processed"',
        ):
            self.assertIn(token, text)

    def test_uploaded_artifacts_are_limited_to_safe_reports(self):
        text = self.workflow_text()

        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("tmp/dysonx_openai_smoke_report.json", text)
        self.assertIn("tmp/dysonx_v1_intelligence_pipeline/signal_candidates_report.json", text)
        self.assertNotIn("raw_items_store.json", text)
        self.assertNotIn("raw_provider_response", text.split("path:")[-1])
        self.assertNotIn("publish_package_report.json", text)


if __name__ == "__main__":
    unittest.main()
