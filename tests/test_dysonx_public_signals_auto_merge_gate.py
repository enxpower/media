import json
import pathlib
import tempfile
import unittest
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_public_signals_auto_merge_gate as gate  # noqa: E402
from dysonx_public_signals_contract import (  # noqa: E402
    PUBLIC_SIGNAL_CONTRACT_VERSION,
    PUBLIC_SIGNAL_POLICY_VERSION,
    build_artifact_entry,
)


def forbidden_domain() -> str:
    return "https://dysonx." + "ai"


class DysonXPublicSignalsAutoMergeGateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp_dir.name)
        self.signals = self.root / "signals"
        self.slug = "critical-agent-signal"
        (self.signals / self.slug).mkdir(parents=True)
        (self.root / "index.html").write_text('<a href="/signals/">Signals</a>', encoding="utf-8")
        (self.signals / "index.html").write_text(
            f'<h1>Signals</h1><a href="/signals/{self.slug}/">Signal</a><script type="application/ld+json">{{"@context":"https://schema.org","@type":"Organization","name":"EnergizeOS Media","url":"https://media.energizeos.com"}}</script>',
            encoding="utf-8",
        )
        (self.signals / self.slug / "index.html").write_text(
            '<h1>Critical AI Agent Evaluation Signal</h1><p>Summary-only public Signal about AI agent evaluation.</p><a href="/">Home</a> <a href="/signals/">Signals</a> <a href="https://example.org/source">Source</a><script type="application/ld+json">{"@context":"https://schema.org","@type":"TechArticle","headline":"Critical AI Agent Evaluation Signal","description":"Summary-only public Signal about AI agent evaluation.","url":"https://media.energizeos.com/signals/critical-agent-signal/"}</script>',
            encoding="utf-8",
        )
        (self.root / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://media.energizeos.com/sitemap.xml\n", encoding="utf-8")
        (self.root / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n  <url>\n    <loc>https://media.energizeos.com/</loc>\n    <lastmod>2026-06-27</lastmod>\n  </url>\n  <url>\n    <loc>https://media.energizeos.com/signals/</loc>\n    <lastmod>2026-06-27</lastmod>\n  </url>\n  <url>\n    <loc>https://media.energizeos.com/signals/critical-agent-signal/</loc>\n    <lastmod>2026-06-27</lastmod>\n  </url>\n</urlset>\n',
            encoding="utf-8",
        )
        (self.root / "rss.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>DysonX Public Signals</title><link>https://media.energizeos.com/signals/</link><description>Source-attributed public Signals tracking AI and AGI intelligence.</description><item><title>Critical AI Agent Evaluation Signal</title><link>https://media.energizeos.com/signals/critical-agent-signal/</link><guid>https://media.energizeos.com/signals/critical-agent-signal/</guid><description>Summary-only public Signal about AI agent evaluation.</description><source url="https://example.org/source">Example Source</source><pubDate>2026-06-27T00:00:00Z</pubDate></item></channel></rss>\n',
            encoding="utf-8",
        )
        (self.root / "feed.json").write_text(
            json.dumps(
                {
                    "version": "https://jsonfeed.org/version/1.1",
                    "title": "DysonX Public Signals",
                    "home_page_url": "https://media.energizeos.com/signals/",
                    "feed_url": "https://media.energizeos.com/feed.json",
                    "items": [
                        {
                            "id": "https://media.energizeos.com/signals/critical-agent-signal/",
                            "url": "https://media.energizeos.com/signals/critical-agent-signal/",
                            "title": "Critical AI Agent Evaluation Signal",
                            "content_text": "Summary-only public Signal about AI agent evaluation.",
                            "summary": "Summary-only public Signal about AI agent evaluation.",
                            "external_url": "https://example.org/source",
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.manifest_path = self.signals / "public_launch_manifest.json"
        self.artifact_manifest_path = self.signals / "public_artifact_manifest.json"
        self.changed_files_path = self.root / "changed_files.json"
        self.write_manifest()
        self.write_artifact_manifest()
        self.write_changed_files([f"signals/{self.slug}/index.html", "signals/index.html", "signals/public_launch_manifest.json"])

    def tearDown(self):
        self.temp_dir.cleanup()

    def manifest(self, **entry_overrides):
        entry = {
            "signal_id": "sig_critical_agent",
            "slug": self.slug,
            "title": "Critical AI Agent Evaluation Signal",
            "summary": "Summary-only public Signal about AI agent evaluation.",
            "public_path": f"signals/{self.slug}/index.html",
            "public_url_path": f"/signals/{self.slug}/",
            "source_name": "Example Source",
            "source_url": "https://example.org/source",
            "source_priority": "Critical",
            "agi_relevance": "High",
            "attribution_status": "Complete",
            "copyright_status": "Safe Summary Only",
            "quality_hint": 94,
            "ready_for_pipeline": True,
            "published": True,
            "production_publish_performed": True,
        }
        entry.update(entry_overrides)
        return {
            "launch_version": "notion_public_signals_sync_v1",
            "pages_launched": 1,
            "pages_blocked": 0,
            "launched": [entry],
            "openai_call_performed": False,
            "network_source_fetch_performed": False,
            "manual_external_deployment_performed": False,
        }

    def write_manifest(self, **entry_overrides):
        self.manifest_path.write_text(json.dumps(self.manifest(**entry_overrides), indent=2), encoding="utf-8")
        self.write_artifact_manifest()

    def artifact_manifest(self, paths=None):
        paths = paths or [
            "feed.json",
            "robots.txt",
            "rss.xml",
            "sitemap.xml",
            "signals/index.html",
            "signals/public_launch_manifest.json",
            "signals/public_artifact_manifest.json",
            f"signals/{self.slug}/index.html",
        ]
        return {
            "contract_version": PUBLIC_SIGNAL_CONTRACT_VERSION,
            "policy_version": PUBLIC_SIGNAL_POLICY_VERSION,
            "generated_from_public_signal_manifest": True,
            "public_launch_manifest_path": "signals/public_launch_manifest.json",
            "public_launch_manifest_material_signature": "test-material",
            "forbidden_content_classes": [
                "raw_body",
                "source_body",
                "verbatim_article",
                "unsafe_script",
                "unsafe_external_resource",
                "off_topic",
            ],
            "artifacts": [build_artifact_entry(path, "test-material") for path in paths],
        }

    def write_artifact_manifest(self, paths=None, data=None):
        self.artifact_manifest_path.write_text(json.dumps(data or self.artifact_manifest(paths), indent=2), encoding="utf-8")

    def write_changed_files(self, files):
        self.changed_files_path.write_text(json.dumps(files), encoding="utf-8")

    def run_gate(self):
        return gate.main(
            [
                "--manifest",
                str(self.manifest_path),
                "--changed-files-json",
                str(self.changed_files_path),
                "--min-quality",
                "80",
                "--allowed-priorities",
                "High,Critical",
                "--allowed-agi-relevance",
                "Medium,High,Critical",
                "--require-attribution-complete",
                "--require-safe-summary-only",
            ]
        )

    def test_high_priority_medium_agi_quality_80_passes(self):
        self.write_manifest(source_priority="High", agi_relevance="Medium", quality_hint=80)
        self.assertEqual(self.run_gate(), 0)

    def test_critical_priority_high_agi_quality_92_passes(self):
        self.write_manifest(source_priority="Critical", agi_relevance="High", quality_hint=92, attribution_status="Complete", copyright_status="Safe Summary Only")
        self.assertEqual(self.run_gate(), 0)

    def test_published_false_can_pass_when_safety_fields_are_valid(self):
        self.write_manifest(published=False)
        self.assertEqual(self.run_gate(), 0)

    def test_ready_for_pipeline_false_can_pass_when_safety_fields_are_valid(self):
        self.write_manifest(ready_for_pipeline=False)
        self.assertEqual(self.run_gate(), 0)

    def test_fails_when_quality_below_threshold(self):
        self.write_manifest(quality_hint=79)
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_source_priority_is_medium(self):
        self.write_manifest(source_priority="Medium")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_agi_relevance_is_low(self):
        self.write_manifest(agi_relevance="Low")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_attribution_is_partial_or_missing(self):
        for status in ("Partial", "Missing"):
            with self.subTest(status=status):
                self.write_manifest(attribution_status=status)
                self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_copyright_status_is_not_safe_summary_only(self):
        self.write_manifest(copyright_status="Unsafe")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_source_url_is_missing_or_invalid(self):
        for source_url in ("", "ftp://example.org/source", "not-a-url"):
            with self.subTest(source_url=source_url):
                self.write_manifest(source_url=source_url)
                self.assertNotEqual(self.run_gate(), 0)
                self.write_manifest()

    def test_fails_when_summary_is_missing(self):
        self.write_manifest(summary="")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_title_is_missing(self):
        self.write_manifest(title="")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_off_topic_terms_appear(self):
        polluted = [
            "biology medicine signal",
            "child online safety policy update",
            "medical object segmentation benchmark",
            "drug-drug interaction prediction model",
            "prostate cancer ultrasound detection model",
            "generic law deliberation with multi-agent debate",
            "oceanography update",
            "poetry politics roundup",
            "robot vacuum product update",
        ]
        for title in polluted:
            with self.subTest(title=title):
                self.write_manifest(title=title)
                self.assertNotEqual(self.run_gate(), 0)
                self.write_manifest()

    def test_fails_when_missing_core_public_topic(self):
        self.write_manifest(title="Distributed systems scheduling update", summary="Summary-only public Signal about scheduling.")
        self.assertNotEqual(self.run_gate(), 0)

    def test_core_public_topic_examples_pass(self):
        examples = [
            ("AgentBound autonomous AI agents benchmark", "AgentBound evaluates autonomous AI agent capability and control."),
            ("AgRefactor agentic workflow developer tool", "AgRefactor improves agentic workflow reliability for code agents."),
            ("RoPoLL LLM judges benchmark", "RoPoLL is a model evaluation benchmark for LLM judges."),
            ("OpenLife autonomous LLM agents", "OpenLife studies autonomous LLM agents and agent coordination."),
            ("AI regulation for frontier model governance", "AI governance and AI regulation for frontier model safety."),
            ("VLA robotics foundation model framework", "A vision-language-action robotics foundation model for embodied AI agent capability."),
        ]
        for title, summary in examples:
            with self.subTest(title=title):
                self.write_manifest(title=title, summary=summary, source_priority="High", agi_relevance="Medium", quality_hint=80, published=False, ready_for_pipeline=False)
                self.assertEqual(self.run_gate(), 0)
                self.write_manifest()

    def test_generic_indoor_robotics_without_agent_framing_fails(self):
        self.write_manifest(
            title="Generic indoor robotics navigation update",
            summary="Summary-only public Signal about indoor robotics navigation hardware.",
            source_priority="High",
            agi_relevance="Medium",
            quality_hint=90,
        )
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_unknown_changed_file_path_exists(self):
        self.write_changed_files([f"signals/{self.slug}/index.html", "index.html"])
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_raw_body_marker_appears(self):
        markers = [
            "full article text",
            "raw source body",
            "article body:",
            "raw_body",
            "Raw Body",
        ]
        for marker in markers:
            with self.subTest(marker=marker):
                (self.signals / self.slug / "index.html").write_text(marker, encoding="utf-8")
                self.assertNotEqual(self.run_gate(), 0)

    def test_safe_source_text_disclaimer_passes(self):
        (self.signals / self.slug / "index.html").write_text(
            '<h1>Critical AI Agent Evaluation Signal</h1><p>Summary-only; source text not reproduced.</p><a href="/">Home</a> <a href="/signals/">Signals</a> <a href="https://example.org/source">Source</a>',
            encoding="utf-8",
        )
        self.assertEqual(self.run_gate(), 0)

    def test_negative_raw_article_body_disclaimer_does_not_false_positive(self):
        (self.signals / self.slug / "index.html").write_text(
            '<h1>Critical AI Agent Evaluation Signal</h1><p>No raw article body copied.</p><a href="/">Home</a> <a href="/signals/">Signals</a> <a href="https://example.org/source">Source</a>',
            encoding="utf-8",
        )
        self.assertEqual(self.run_gate(), 0)

    def test_techarticle_json_ld_passes_on_signal_page(self):
        self.assertEqual(self.run_gate(), 0)

    def test_organization_json_ld_passes_on_signals_index(self):
        self.write_changed_files(["signals/index.html"])
        self.assertEqual(self.run_gate(), 0)

    def test_fails_when_normal_inline_script_tag_appears(self):
        (self.signals / self.slug / "index.html").write_text("<script>alert(1)</script>", encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_external_script_src_appears(self):
        (self.signals / self.slug / "index.html").write_text('<script src="https://example.org/app.js"></script>', encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_malformed_json_ld_appears(self):
        (self.signals / self.slug / "index.html").write_text('<script type="application/ld+json">{"@type":</script>', encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_json_ld_contains_raw_body_marker(self):
        (self.signals / self.slug / "index.html").write_text(
            '<script type="application/ld+json">{"@type":"TechArticle","description":"full article text"}</script>',
            encoding="utf-8",
        )
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_event_handler_attribute_appears(self):
        (self.signals / self.slug / "index.html").write_text('<a href="/" onclick="alert(1)">Home</a>', encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_forbidden_terms_appear(self):
        forbidden = [
            "." + "invalid",
            "." + "test/",
            forbidden_domain(),
            "tmp/" + "production_publish_pack",
        ]
        for term in forbidden:
            with self.subTest(term=term):
                self.write_manifest(title=term)
                self.assertNotEqual(self.run_gate(), 0)
                self.write_manifest()

    def test_fails_when_manifest_says_openai_call_performed_true(self):
        data = self.manifest()
        data["openai_call_performed"] = True
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_manifest_says_network_source_fetch_performed_true(self):
        data = self.manifest()
        data["network_source_fetch_performed"] = True
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_fails_when_manifest_says_manual_external_deployment_performed_true(self):
        data = self.manifest()
        data["manual_external_deployment_performed"] = True
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_passes_only_for_allowed_signals_paths(self):
        allowed = [
            "feed.json",
            "robots.txt",
            "rss.xml",
            "sitemap.xml",
            "signals/index.html",
            "signals/public_launch_manifest.json",
            "signals/public_artifact_manifest.json",
            f"signals/{self.slug}/index.html",
        ]
        for path in allowed:
            with self.subTest(path=path):
                self.write_changed_files([path])
                self.assertEqual(self.run_gate(), 0)

    def test_artifact_manifest_must_declare_every_changed_file(self):
        self.write_artifact_manifest(paths=["signals/index.html", "signals/public_launch_manifest.json", "signals/public_artifact_manifest.json"])
        self.write_changed_files([f"signals/{self.slug}/index.html"])
        self.assertNotEqual(self.run_gate(), 0)

    def test_artifact_manifest_unknown_class_fails(self):
        data = self.artifact_manifest()
        data["artifacts"][0]["artifact_class"] = "unknown_public_artifact"
        self.write_artifact_manifest(data=data)
        self.assertNotEqual(self.run_gate(), 0)

    def test_artifact_manifest_class_path_mismatch_fails(self):
        data = self.artifact_manifest()
        data["artifacts"][0]["path"] = "signals/index.html"
        data["artifacts"][0]["artifact_class"] = "rss_xml"
        self.write_artifact_manifest(data=data)
        self.assertNotEqual(self.run_gate(), 0)

    def test_artifact_manifest_policy_vocabulary_raw_body_passes(self):
        self.write_changed_files(["signals/public_artifact_manifest.json"])
        data = self.artifact_manifest()
        data["forbidden_content_classes"] = ["raw_body", "source_body", "verbatim_article"]
        self.write_artifact_manifest(data=data)
        self.assertEqual(self.run_gate(), 0)

    def test_artifact_manifest_raw_body_in_path_fails(self):
        self.write_changed_files(["signals/public_artifact_manifest.json"])
        data = self.artifact_manifest()
        data["artifacts"][0]["path"] = "signals/raw_body/index.html"
        self.write_artifact_manifest(data=data)
        self.assertNotEqual(self.run_gate(), 0)

    def test_artifact_manifest_raw_body_in_slug_fails(self):
        self.write_changed_files(["signals/public_artifact_manifest.json"])
        data = self.artifact_manifest()
        data["artifacts"][-1]["slug"] = "raw_body"
        self.write_artifact_manifest(data=data)
        self.assertNotEqual(self.run_gate(), 0)

    def test_artifact_manifest_raw_body_in_material_signature_fails(self):
        self.write_changed_files(["signals/public_artifact_manifest.json"])
        data = self.artifact_manifest()
        data["artifacts"][0]["material_signature"] = "raw_body"
        self.write_artifact_manifest(data=data)
        self.assertNotEqual(self.run_gate(), 0)

    def test_artifact_manifest_raw_body_in_unexpected_free_text_fails(self):
        self.write_changed_files(["signals/public_artifact_manifest.json"])
        data = self.artifact_manifest()
        data["unexpected_note"] = "raw_body"
        self.write_artifact_manifest(data=data)
        self.assertNotEqual(self.run_gate(), 0)

    def test_public_launch_manifest_raw_body_in_summary_still_fails(self):
        self.write_manifest(summary="raw_body")
        self.assertNotEqual(self.run_gate(), 0)

    def test_public_launch_manifest_raw_body_in_risk_notes_still_fails(self):
        data = self.manifest()
        data["launched"][0]["risk_notes"] = "raw source body"
        self.manifest_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_sitemap_with_blocked_signal_url_fails(self):
        self.write_changed_files(["sitemap.xml"])
        (self.root / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://media.energizeos.com/signals/blocked-medical-signal/</loc><lastmod>2026-06-27</lastmod></url></urlset>',
            encoding="utf-8",
        )
        self.assertNotEqual(self.run_gate(), 0)

    def test_rss_raw_body_leakage_fails(self):
        self.write_changed_files(["rss.xml"])
        (self.root / "rss.xml").write_text("full article text", encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)

    def test_json_feed_raw_body_leakage_fails(self):
        self.write_changed_files(["feed.json"])
        (self.root / "feed.json").write_text(json.dumps({"items": [{"url": "https://media.energizeos.com/signals/critical-agent-signal/", "content_text": "raw source body"}]}), encoding="utf-8")
        self.assertNotEqual(self.run_gate(), 0)


if __name__ == "__main__":
    unittest.main()
