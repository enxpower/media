import pathlib
import unittest

import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_static_preview_check as preview_check  # noqa: E402


class DysonXStaticPreviewCheckTests(unittest.TestCase):
    def test_static_preview_check_passes(self):
        passed = preview_check.run_checks()

        self.assertIn("index.html exists", passed)
        self.assertIn("index.html has English canonical metadata", passed)
        self.assertIn("active workflows avoid deleted legacy scripts", passed)
        self.assertIn("V1 dry-run pipeline still works", passed)

    def test_active_workflow_scan_excludes_disabled_legacy_workflows(self):
        active_names = [
            path.name
            for path in sorted(preview_check.WORKFLOWS.glob("*.yml"))
            + sorted(preview_check.WORKFLOWS.glob("*.yaml"))
        ]

        self.assertNotIn("update.yml.disabled", active_names)
        self.assertNotIn("update-content.yml.disabled", active_names)

    def test_removed_artifact_tokens_are_explicit(self):
        self.assertIn("posts/page1.html", preview_check.REMOVED_PUBLIC_ARTIFACTS)
        self.assertIn("sitemap.xml", preview_check.REMOVED_PUBLIC_ARTIFACTS)
        self.assertIn("scripts/aggregator.py", preview_check.DELETED_LEGACY_SCRIPT_TOKENS)
        self.assertIn("scripts/generate_sitemap.py", preview_check.DELETED_LEGACY_SCRIPT_TOKENS)


if __name__ == "__main__":
    unittest.main()
