import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
INDEX = ROOT / "index.html"
ROBOTS = ROOT / "robots.txt"


def read_lower(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8").lower()


class DysonXIdentityLandingTests(unittest.TestCase):
    def test_readme_uses_dysonx_identity(self):
        text = README.read_text(encoding="utf-8")

        self.assertIn("AI / AGI Intelligence OS", text)
        self.assertIn("AGI signal tracker", text)
        self.assertIn("first-source AI intelligence platform", text)
        self.assertIn("Signal, not the Article", text)
        self.assertIn("English-default", text)
        self.assertIn("Chinese-switchable", text)
        self.assertIn("Notion-managed sources", text)
        self.assertIn("V1 dry-run pipeline", text)

    def test_readme_does_not_use_legacy_positioning(self):
        text = read_lower(README)
        forbidden_phrases = (
            "news aggregator",
            "rss news site",
            "ai-generated news blog",
            "automated article farm",
            "hourly rss fetch",
            "energizeos",
        )

        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, text)

    def test_index_contains_dysonx_landing_identity(self):
        html = INDEX.read_text(encoding="utf-8")

        self.assertIn("DysonX tracks the signals shaping AGI.", html)
        self.assertIn("First-source AI intelligence, structured into Signals, rankings, and decision-ready context.", html)
        for nav_item in ("Signals", "Trackers", "AGI Map", "Companies", "People", "Research", "Reports"):
            self.assertIn(nav_item, html)
        self.assertIn("V1 dry-run pipeline available", html)
        self.assertIn("First public Signal published", html)
        self.assertNotIn("Real publishing not enabled yet", html)
        self.assertIn("EN", html)
        self.assertIn("中文", html)

    def test_index_metadata_is_english_default(self):
        html = INDEX.read_text(encoding="utf-8")

        self.assertIn('<html lang="en">', html)
        self.assertIn("<title>DysonX | Signals Shaping AGI</title>", html)
        self.assertIn('name="description"', html)
        self.assertIn('property="og:title"', html)
        self.assertIn('property="og:description"', html)
        self.assertIn('name="twitter:title"', html)
        self.assertIn('name="twitter:description"', html)
        self.assertIn("English default; Chinese optional future localization", html)
        self.assertNotIn('property="og:url"', html)
        self.assertNotIn('rel="canonical"', html)

    def test_index_public_links_are_domain_agnostic_and_valid(self):
        html = INDEX.read_text(encoding="utf-8")

        self.assertIn('href="/"', html)
        self.assertIn('href="/signals/"', html)
        self.assertNotIn('href="#signals"', html)
        self.assertNotIn("https://dysonx." + "ai", html)
        for nav_item in ("Trackers", "AGI Map", "Companies", "People", "Research", "Reports"):
            self.assertIn(f'<span class="nav-disabled" aria-disabled="true">{nav_item}</span>', html)

    def test_index_does_not_use_legacy_public_positioning(self):
        html = read_lower(INDEX)
        forbidden_phrases = (
            "news aggregator",
            "rss news site",
            "ai-generated news blog",
            "automated article farm",
            "hourly rss",
            "search news",
            "newscontainer",
            "posts/page",
            "energizeos news",
        )

        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, html)

    def test_robots_points_to_public_signals_sitemap(self):
        text = read_lower(ROBOTS)

        self.assertIn("sitemap: https://media.energizeos.com/sitemap.xml", text)
        self.assertNotIn("posts/", text)


if __name__ == "__main__":
    unittest.main()
