import ast
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"


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


if __name__ == "__main__":
    unittest.main()
