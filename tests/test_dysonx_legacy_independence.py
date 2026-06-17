import ast
import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
REMOVED_LEGACY_PATHS = (
    ROOT / "scripts" / "aggregator.py",
    ROOT / "scripts" / "openai_summary.py",
    ROOT / "scripts" / "generate_sitemap.py",
    ROOT / "feeds.json",
)
REMOVED_GENERATED_CONTENT_PATHS = (
    ROOT / "posts" / "page1.html",
    ROOT / "posts" / "page2.html",
    ROOT / "posts" / "page3.html",
    ROOT / "posts" / "page4.html",
    ROOT / "sitemap.xml",
)


def imported_modules(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


class DysonXLegacyIndependenceTests(unittest.TestCase):
    def test_legacy_aggregator_files_are_removed(self):
        existing = [str(path.relative_to(ROOT)) for path in REMOVED_LEGACY_PATHS if path.exists()]

        self.assertEqual([], existing)

    def test_legacy_generated_news_content_is_removed(self):
        existing = [str(path.relative_to(ROOT)) for path in REMOVED_GENERATED_CONTENT_PATHS if path.exists()]

        self.assertEqual([], existing)

    def test_python_cache_files_are_not_tracked(self):
        result = subprocess.run(
            ["git", "ls-files", "*__pycache__*", "*.pyc", "*.pyo"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        tracked_cache_files = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual([], tracked_cache_files)

    def test_v1_pipeline_does_not_import_legacy_aggregator(self):
        imports = imported_modules(SCRIPTS_DIR / "dysonx_v1_pipeline.py")

        self.assertNotIn("aggregator", imports)
        self.assertNotIn("openai_summary", imports)

    def test_dysonx_v1_modules_do_not_import_legacy_news_flow(self):
        legacy_modules = {"aggregator", "openai_summary"}
        offenders = {}

        for path in sorted(SCRIPTS_DIR.glob("dysonx_*.py")):
            overlap = imported_modules(path) & legacy_modules
            if overlap:
                offenders[path.name] = sorted(overlap)

        self.assertEqual({}, offenders)

    def test_active_workflows_do_not_run_legacy_aggregation(self):
        legacy_tokens = (
            "scripts/aggregator.py",
            "scripts/openai_summary.py",
            "scripts/generate_sitemap.py",
            "hashFiles('feeds.json')",
            "git add posts/ sitemap.xml",
            "OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}",
            "group: aggregator-${{ github.repository }}-${{ github.ref_name }}",
        )
        offenders = {}

        for path in sorted(WORKFLOWS_DIR.glob("*.yml")) + sorted(WORKFLOWS_DIR.glob("*.yaml")):
            text = path.read_text(encoding="utf-8")
            matches = [token for token in legacy_tokens if token in text]
            if matches:
                offenders[path.name] = matches

        self.assertEqual({}, offenders)


if __name__ == "__main__":
    unittest.main()
