import json
import pathlib
import shutil
import tempfile
import unittest
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import dysonx_notion_public_signals_sync as sync  # noqa: E402


FIXTURE_DOMAIN = "example.com"
FIXTURE_BASE_URL = f"https://{FIXTURE_DOMAIN}"


def eligible_record(**overrides):
    record = {
        "Signal ID": "sig_notion_agent_eval",
        "Signal Title": "Notion approved agent reliability Signal",
        "Slug": "notion-agent-reliability",
        "Summary": "A Notion-approved summary-only Signal about agent reliability evaluation.",
        "Why This Matters": "Agent reliability metrics affect whether agentic systems can be trusted for longer tasks.",
        "AGI Relevance": "High",
        "Source URL": "https://example.org/agent-reliability",
        "Source Label": "Example Research Source",
        "Source Priority": "Critical",
        "Ready for Pipeline": True,
        "Published": True,
        "Attribution Status": "Complete",
        "Copyright Status": "Safe Summary Only",
        "Quality Hint": 92,
        "Risk Notes": "Summary-only treatment.",
        "Watch Next": "Watch whether this metric appears in standard agent evaluations.",
        "Tags": ["Agents", "Evaluation"],
    }
    record.update(overrides)
    return record


class DysonXNotionPublicSignalsSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp_dir.name)
        shutil.copytree(ROOT / "signals", self.root / "signals")
        (self.root / "CNAME").write_text(f"{FIXTURE_DOMAIN}\n", encoding="utf-8")

    def tearDown(self):
        self.temp_dir.cleanup()

    def read_output(self) -> str:
        return "\n".join(path.read_text(encoding="utf-8") for path in sorted((self.root / "signals").rglob("*")) if path.is_file())

    def output_snapshot(self) -> dict[str, str]:
        files = {
            str(path.relative_to(self.root)): path.read_text(encoding="utf-8")
            for path in sorted((self.root / "signals").rglob("*"))
            if path.is_file()
        }
        for name in ("robots.txt", "sitemap.xml", "rss.xml", "feed.json"):
            path = self.root / name
            if path.exists():
                files[name] = path.read_text(encoding="utf-8")
        return files

    def test_eligible_row_generates_page(self):
        manifest = sync.sync_records([eligible_record()], self.root, refreshed_at="2026-06-27T00:00:00Z")

        page = self.root / "signals" / "notion-agent-reliability" / "index.html"
        self.assertTrue(page.exists())
        html = page.read_text(encoding="utf-8")
        self.assertIn("Notion approved agent reliability Signal", html)
        self.assertIn("https://example.org/agent-reliability", html)
        self.assertEqual(manifest["openai_call_performed"], False)
        self.assertEqual(manifest["source_scraping_performed"], False)

    def test_generated_page_uses_safe_source_text_disclaimer(self):
        sync.sync_records([eligible_record(**{"Risk Notes": ""})], self.root, refreshed_at="2026-06-27T00:00:00Z")

        html = (self.root / "signals" / "notion-agent-reliability" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Summary-only; source text not reproduced.", html)
        self.assertNotIn("raw article body", html.lower())

    def test_rerunning_identical_records_does_not_churn_timestamps_or_files(self):
        shutil.rmtree(self.root / "signals")
        records = [eligible_record()]

        first_manifest = sync.sync_records(records, self.root, refreshed_at="2026-06-27T00:00:00Z")
        first_snapshot = self.output_snapshot()
        second_manifest = sync.sync_records(records, self.root, refreshed_at="2026-06-28T00:00:00Z")
        second_snapshot = self.output_snapshot()

        self.assertEqual(first_manifest["content_refreshed_at"], "2026-06-27T00:00:00Z")
        self.assertEqual(second_manifest["content_refreshed_at"], "2026-06-27T00:00:00Z")
        self.assertEqual(second_snapshot, first_snapshot)

    def test_material_content_change_updates_outputs(self):
        shutil.rmtree(self.root / "signals")
        records = [eligible_record()]
        sync.sync_records(records, self.root, refreshed_at="2026-06-27T00:00:00Z")
        first_snapshot = self.output_snapshot()

        changed = [eligible_record(**{"Summary": "Updated summary-only Signal about AI agent evaluation."})]
        manifest = sync.sync_records(changed, self.root, refreshed_at="2026-06-28T00:00:00Z")
        second_snapshot = self.output_snapshot()

        self.assertEqual(manifest["content_refreshed_at"], "2026-06-28T00:00:00Z")
        self.assertNotEqual(second_snapshot, first_snapshot)
        self.assertIn("Updated summary-only Signal about AI agent evaluation.", second_snapshot["signals/notion-agent-reliability/index.html"])
        self.assertIn("Updated summary-only Signal about AI agent evaluation.", second_snapshot["rss.xml"])
        self.assertIn("Updated summary-only Signal about AI agent evaluation.", second_snapshot["feed.json"])
        self.assertIn("<lastmod>2026-06-28</lastmod>", second_snapshot["sitemap.xml"])

    def test_risk_note_change_updates_outputs(self):
        shutil.rmtree(self.root / "signals")
        records = [eligible_record()]
        sync.sync_records(records, self.root, refreshed_at="2026-06-27T00:00:00Z")
        first_snapshot = self.output_snapshot()

        changed = [eligible_record(**{"Risk Notes": "Summary-only; updated source text safety note."})]
        manifest = sync.sync_records(changed, self.root, refreshed_at="2026-06-28T00:00:00Z")
        second_snapshot = self.output_snapshot()

        self.assertEqual(manifest["content_refreshed_at"], "2026-06-28T00:00:00Z")
        self.assertNotEqual(second_snapshot, first_snapshot)
        self.assertIn("updated source text safety note", second_snapshot["signals/notion-agent-reliability/index.html"])

    def test_new_eligible_signal_creates_content_changes(self):
        shutil.rmtree(self.root / "signals")
        records = [eligible_record()]
        sync.sync_records(records, self.root, refreshed_at="2026-06-27T00:00:00Z")
        first_snapshot = self.output_snapshot()

        records.append(
            eligible_record(
                **{
                    "Signal ID": "sig_second_agent",
                    "Signal Title": "Second AI agent evaluation Signal",
                    "Slug": "second-ai-agent-evaluation",
                    "Summary": "A second summary-only Signal about AI agent evaluation.",
                    "Quality Hint": 93,
                }
            )
        )
        manifest = sync.sync_records(records, self.root, refreshed_at="2026-06-28T00:00:00Z")
        second_snapshot = self.output_snapshot()

        self.assertEqual(manifest["content_refreshed_at"], "2026-06-28T00:00:00Z")
        self.assertNotEqual(second_snapshot, first_snapshot)
        self.assertIn("signals/second-ai-agent-evaluation/index.html", second_snapshot)

    def test_row_with_missing_attribution_does_not_generate_page(self):
        manifest = sync.sync_records([eligible_record(**{"Attribution Status": "Incomplete"})], self.root)

        self.assertFalse((self.root / "signals" / "notion-agent-reliability" / "index.html").exists())
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_row_with_raw_body_blocked_does_not_generate_page(self):
        manifest = sync.sync_records([eligible_record(**{"Raw Body Status": "Raw Body Blocked"})], self.root)

        self.assertFalse((self.root / "signals" / "notion-agent-reliability" / "index.html").exists())
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_output_uses_relative_public_paths(self):
        sync.sync_records([eligible_record()], self.root)
        manifest = json.loads((self.root / "signals" / "public_launch_manifest.json").read_text(encoding="utf-8"))

        public_paths = [entry["public_url_path"] for entry in manifest["launched"]]
        self.assertIn("/signals/notion-agent-reliability/", public_paths)
        for path in public_paths:
            self.assertTrue(path.startswith("/"))
            self.assertFalse(path.startswith("http://"))
            self.assertFalse(path.startswith("https://"))

    def test_output_does_not_contain_forbidden_public_terms(self):
        sync.sync_records([eligible_record()], self.root)
        text = self.read_output()

        forbidden = [
            "." + "test/",
            "." + "invalid",
            "tmp/" + "production_publish_pack",
            "https://dysonx." + "ai",
        ]
        for term in forbidden:
            self.assertNotIn(term, text)

    def test_generates_robots_sitemap_and_feeds(self):
        manifest = sync.sync_records([eligible_record()], self.root, refreshed_at="2026-06-27T00:00:00Z")

        robots = (self.root / "robots.txt").read_text(encoding="utf-8")
        sitemap = (self.root / "sitemap.xml").read_text(encoding="utf-8")
        rss = (self.root / "rss.xml").read_text(encoding="utf-8")
        feed = json.loads((self.root / "feed.json").read_text(encoding="utf-8"))
        launched_urls = {
            f"{FIXTURE_BASE_URL}{entry['public_url_path']}"
            for entry in manifest["launched"]
        }

        self.assertEqual(robots, f"User-agent: *\nAllow: /\nSitemap: {FIXTURE_BASE_URL}/sitemap.xml\n")
        self.assertIn(f"{FIXTURE_BASE_URL}/", sitemap)
        self.assertIn(f"{FIXTURE_BASE_URL}/signals/", sitemap)
        for url in launched_urls:
            self.assertIn(url, sitemap)
        self.assertIn(f"{FIXTURE_BASE_URL}/signals/notion-agent-reliability/", rss)
        self.assertEqual(feed["feed_url"], f"{FIXTURE_BASE_URL}/feed.json")
        self.assertLessEqual(len(feed["items"]), sync.DEFAULT_JSON_FEED_ITEM_LIMIT)

    def test_generates_public_artifact_manifest_for_every_public_artifact(self):
        sync.sync_records([eligible_record()], self.root, refreshed_at="2026-06-27T00:00:00Z")

        artifact_manifest = json.loads((self.root / "signals" / "public_artifact_manifest.json").read_text(encoding="utf-8"))
        artifact_paths = {item["path"] for item in artifact_manifest["artifacts"]}

        self.assertEqual(artifact_manifest["contract_version"], "dysonx_public_signal_contract_v1")
        self.assertIn("signals/public_artifact_manifest.json", artifact_paths)
        self.assertIn("robots.txt", artifact_paths)
        self.assertIn("sitemap.xml", artifact_paths)
        self.assertIn("rss.xml", artifact_paths)
        self.assertIn("feed.json", artifact_paths)
        signal_artifact = next(item for item in artifact_manifest["artifacts"] if item["path"] == "signals/notion-agent-reliability/index.html")
        self.assertEqual(signal_artifact["artifact_class"], "signal_html")
        self.assertEqual(signal_artifact["allowed_embeds"], ["json_ld_article"])

    def test_sitemap_excludes_blocked_signals(self):
        sync.sync_records(
            [
                eligible_record(),
                eligible_record(
                    **{
                        "Signal ID": "sig_blocked",
                        "Signal Title": "Blocked biology medicine Signal",
                        "Slug": "blocked-biology-medicine",
                        "Category": "Biology",
                    }
                ),
            ],
            self.root,
        )

        sitemap = (self.root / "sitemap.xml").read_text(encoding="utf-8")
        self.assertIn(f"{FIXTURE_BASE_URL}/signals/notion-agent-reliability/", sitemap)
        self.assertNotIn("blocked-biology-medicine", sitemap)

    def test_rss_and_json_feed_do_not_contain_raw_body_markers(self):
        sync.sync_records([eligible_record()], self.root, refreshed_at="2026-06-27T00:00:00Z")
        text = (self.root / "rss.xml").read_text(encoding="utf-8") + (self.root / "feed.json").read_text(encoding="utf-8")

        for marker in ("full article text", "raw source body", "article body:", "raw_body", "Raw Body"):
            self.assertNotIn(marker, text)
        self.assertIn("https://example.org/agent-reliability", text)

    def test_signal_page_has_seo_head_and_absolute_canonical(self):
        sync.sync_records([eligible_record()], self.root, refreshed_at="2026-06-27T00:00:00Z")

        html = (self.root / "signals" / "notion-agent-reliability" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<meta name="description"', html)
        self.assertIn(f'<link rel="canonical" href="{FIXTURE_BASE_URL}/signals/notion-agent-reliability/">', html)
        self.assertIn('property="og:title"', html)
        self.assertIn('property="og:description"', html)
        self.assertIn('property="og:type" content="article"', html)
        self.assertIn(f'property="og:url" content="{FIXTURE_BASE_URL}/signals/notion-agent-reliability/"', html)
        self.assertIn('name="twitter:card"', html)
        self.assertIn('type="application/ld+json"', html)
        self.assertIn('"@type": "TechArticle"', html)

    def test_signals_index_has_organization_json_ld(self):
        sync.sync_records([eligible_record()], self.root, refreshed_at="2026-06-27T00:00:00Z")

        html = (self.root / "signals" / "index.html").read_text(encoding="utf-8")
        self.assertIn('"@type": "Organization"', html)
        self.assertIn('"name": "EnergizeOS Media"', html)
        self.assertIn('<link rel="alternate" type="application/rss+xml"', html)

    def test_unsafe_source_url_is_blocked(self):
        manifest = sync.sync_records([eligible_record(**{"Source URL": "https://source.dysonx." + "invalid/research"})], self.root)

        self.assertFalse((self.root / "signals" / "notion-agent-reliability" / "index.html").exists())
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_manifest_never_sets_openai_call_performed_true(self):
        manifest = sync.sync_records([eligible_record()], self.root)

        self.assertIs(manifest["openai_call_performed"], False)
        self.assertIs(manifest["source_scraping_performed"], False)
        self.assertIs(manifest["network_source_fetch_performed"], False)
        self.assertIs(manifest["raw_article_body_copied"], False)

    def test_manifest_includes_auto_merge_gate_fields(self):
        manifest = sync.sync_records([eligible_record(**{"Quality Hint": 94})], self.root)
        entry = next(item for item in manifest["launched"] if item["slug"] == "notion-agent-reliability")

        self.assertEqual(entry["source_name"], "Example Research Source")
        self.assertEqual(entry["source_url"], "https://example.org/agent-reliability")
        self.assertEqual(entry["source_priority"], "Critical")
        self.assertEqual(entry["attribution_status"], "Complete")
        self.assertEqual(entry["copyright_status"], "Safe Summary Only")
        self.assertEqual(entry["agi_relevance"], "High")
        self.assertEqual(entry["summary"], "A Notion-approved summary-only Signal about agent reliability evaluation.")
        self.assertEqual(entry["quality_hint"], 94)
        self.assertIs(entry["ready_for_pipeline"], True)
        self.assertIs(entry["published"], True)

    def test_manifest_carries_source_priority_from_priority_fallback(self):
        record = eligible_record(**{"Quality Hint": 94, "Priority": "Critical"})
        del record["Source Priority"]
        manifest = sync.sync_records([record], self.root)
        entry = next(item for item in manifest["launched"] if item["slug"] == "notion-agent-reliability")

        self.assertEqual(entry["source_priority"], "Critical")

    def test_high_priority_medium_agi_quality_80_is_eligible(self):
        manifest = sync.sync_records(
            [
                eligible_record(
                    **{
                        "Source Priority": "High",
                        "Quality Hint": 80,
                        "AGI Relevance": "Medium",
                    }
                )
            ],
            self.root,
        )

        self.assertTrue((self.root / "signals" / "notion-agent-reliability" / "index.html").exists())
        self.assertEqual(manifest["pages_blocked"], 0)
        entry = next(item for item in manifest["launched"] if item["slug"] == "notion-agent-reliability")
        self.assertEqual(entry["source_priority"], "High")
        self.assertEqual(entry["quality_hint"], 80)

    def test_critical_priority_high_agi_quality_92_is_eligible(self):
        manifest = sync.sync_records([eligible_record(**{"Source Priority": "Critical", "Quality Hint": 92, "AGI Relevance": "High"})], self.root)

        self.assertTrue((self.root / "signals" / "notion-agent-reliability" / "index.html").exists())
        self.assertEqual(manifest["pages_blocked"], 0)

    def test_published_false_can_still_pass_when_other_fields_are_safe(self):
        manifest = sync.sync_records([eligible_record(**{"Published": False})], self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertIn("notion-agent-reliability", launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 0)

    def test_ready_false_can_still_pass_when_other_fields_are_safe(self):
        manifest = sync.sync_records([eligible_record(**{"Ready for Pipeline": False})], self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertIn("notion-agent-reliability", launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 0)

    def test_quality_79_is_blocked_from_public_output(self):
        manifest = sync.sync_records([eligible_record(**{"Quality Hint": 79})], self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertNotIn("notion-agent-reliability", launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_source_priority_medium_is_blocked_from_public_output(self):
        manifest = sync.sync_records([eligible_record(**{"Source Priority": "Medium", "Quality Hint": 95})], self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertNotIn("notion-agent-reliability", launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_agi_relevance_low_is_blocked_from_public_output(self):
        manifest = sync.sync_records([eligible_record(**{"Quality Hint": 95, "AGI Relevance": "Low"})], self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertNotIn("notion-agent-reliability", launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_published_polluted_rows_are_blocked_unless_all_strict_public_rules_pass(self):
        records = [
            eligible_record(
                **{
                    "Signal ID": "sig_general_science",
                    "Signal Title": "General science RSS page about oceanography and eclipses",
                    "Slug": "general-science-oceanography-eclipses",
                    "Source Priority": "Critical",
                    "Quality Hint": 95,
                    "AGI Relevance": "High",
                    "Category": "General Science",
                }
            ),
            eligible_record(
                **{
                    "Signal ID": "sig_robot_vacuum",
                    "Signal Title": "Robot vacuum product roundup",
                    "Slug": "robot-vacuum-product-roundup",
                    "Source Priority": "Critical",
                    "Quality Hint": 95,
                    "AGI Relevance": "High",
                }
            ),
            eligible_record(
                **{
                    "Signal ID": "sig_valid",
                    "Signal Title": "Critical AGI agent reliability Signal",
                    "Slug": "critical-agi-agent-reliability",
                    "Source Priority": "Critical",
                    "Quality Hint": 95,
                    "AGI Relevance": "Critical",
                }
            ),
        ]
        manifest = sync.sync_records(records, self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertNotIn("general-science-oceanography-eclipses", launched_slugs)
        self.assertNotIn("robot-vacuum-product-roundup", launched_slugs)
        self.assertIn("critical-agi-agent-reliability", launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 2)

    def test_off_topic_rows_are_blocked(self):
        polluted = [
            ("biology-medicine", "Biology medicine update", "Biology"),
            ("oceanography", "Oceanography research update", "Science"),
            ("poetry-politics", "Poetry and politics roundup", "General News"),
            ("robot-vacuum", "Robot vacuum product roundup", "Hardware"),
        ]
        records = [
            eligible_record(
                **{
                    "Signal ID": f"sig_{slug}",
                    "Signal Title": title,
                    "Slug": slug,
                    "Category": category,
                    "Source Priority": "Critical",
                    "Quality Hint": 95,
                    "AGI Relevance": "High",
                }
            )
            for slug, title, category in polluted
        ]
        manifest = sync.sync_records([], self.root)

        self.assertEqual(manifest["pages_launched"], len(manifest["launched"]))
        self.assertGreaterEqual(manifest["pages_launched"], 1)
        manifest = sync.sync_records(records, self.root)
        launched_slugs = {item["slug"] for item in manifest["launched"]}
        for slug, _, _ in polluted:
            self.assertNotIn(slug, launched_slugs)
        self.assertEqual(manifest["pages_blocked"], len(polluted))

    def test_new_public_topic_blockers_reject_polluted_rows(self):
        polluted = [
            ("child-online-safety", "Child online safety policy update", "Policy"),
            ("medical-object-segmentation", "Medical object segmentation benchmark", "Medical Imaging"),
            ("surgical-laparoscopic", "Surgical laparoscopic clinical model", "Clinical"),
            ("drug-drug-interaction", "Drug-drug interaction prediction model", "Biomedical"),
            ("prostate-cancer-ultrasound", "Prostate cancer ultrasound detection model", "Clinical"),
            ("legal-deliberation", "Generic law deliberation with multi-agent debate", "Law"),
            ("agricultural-dairy", "Agricultural dairy methane forecasting model", "Agriculture"),
        ]
        records = [
            eligible_record(
                **{
                    "Signal ID": f"sig_{slug}",
                    "Signal Title": title,
                    "Slug": slug,
                    "Summary": "A summary-only Signal with enough model language but outside DysonX public scope.",
                    "Category": category,
                    "Source Priority": "High",
                    "AGI Relevance": "Medium",
                    "Quality Hint": 90,
                }
            )
            for slug, title, category in polluted
        ]
        manifest = sync.sync_records(records, self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        for slug, _, _ in polluted:
            self.assertNotIn(slug, launched_slugs)
        self.assertEqual(manifest["pages_blocked"], len(polluted))

    def test_core_public_topic_examples_pass(self):
        examples = [
            ("agentbound", "AgentBound autonomous AI agents benchmark", "AgentBound evaluates autonomous AI agent capability and control."),
            ("agrefactor", "AgRefactor agentic workflow developer tool", "AgRefactor improves agentic workflow reliability for code agents."),
            ("ropoll", "RoPoLL LLM judges benchmark", "RoPoLL is a model evaluation benchmark for LLM judges."),
            ("openlife", "OpenLife autonomous LLM agents", "OpenLife studies autonomous LLM agents and agent coordination."),
            ("ai-governance", "AI regulation for frontier model governance", "AI governance and AI regulation for frontier model safety."),
            ("vla-robotics", "VLA robotics foundation model framework", "A vision-language-action robotics foundation model for embodied AI agent capability."),
            ("uav-agents", "UAV multi-agent planning benchmark", "A multi-agent planning benchmark for autonomous AI agent capability evaluation."),
        ]
        records = [
            eligible_record(
                **{
                    "Signal ID": f"sig_{slug}",
                    "Signal Title": title,
                    "Slug": slug,
                    "Summary": summary,
                    "Source Priority": "High",
                    "AGI Relevance": "Medium",
                    "Quality Hint": 80,
                    "Published": False,
                    "Ready for Pipeline": False,
                }
            )
            for slug, title, summary in examples
        ]
        manifest = sync.sync_records(records, self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        for slug, _, _ in examples:
            self.assertIn(slug, launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 0)

    def test_generic_indoor_robotics_without_agent_framing_is_blocked(self):
        manifest = sync.sync_records(
            [
                eligible_record(
                    **{
                        "Signal ID": "sig_indoor_robotics",
                        "Signal Title": "Generic indoor robotics navigation update",
                        "Slug": "generic-indoor-robotics",
                        "Summary": "A summary-only Signal about indoor robotics navigation hardware.",
                        "Category": "Robotics",
                        "Source Priority": "High",
                        "AGI Relevance": "Medium",
                        "Quality Hint": 90,
                    }
                )
            ],
            self.root,
        )

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertNotIn("generic-indoor-robotics", launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_domain_risk_can_pass_with_explicit_ai_safety_evaluation_framing(self):
        manifest = sync.sync_records(
            [
                eligible_record(
                    **{
                        "Signal ID": "sig_medical_eval",
                        "Signal Title": "Medical AI agent safety evaluation benchmark",
                        "Slug": "medical-ai-agent-safety-evaluation",
                        "Summary": "A summary-only Signal about AI safety evaluation for agent behavior in a domain-risk setting.",
                        "Category": "AI Safety",
                        "Source Priority": "High",
                        "AGI Relevance": "Medium",
                        "Quality Hint": 84,
                    }
                )
            ],
            self.root,
        )

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertIn("medical-ai-agent-safety-evaluation", launched_slugs)

    def test_missing_core_public_topic_is_reported(self):
        report_path = self.root / "tmp" / "dysonx_public_signals_sync_report.json"
        sync.sync_records(
            [
                eligible_record(
                    **{
                        "Signal Title": "Distributed systems scheduling update",
                        "Slug": "distributed-systems-scheduling",
                        "Summary": "A summary-only Signal about distributed systems scheduling.",
                        "Why This Matters": "Scheduling metrics affect distributed infrastructure operations.",
                        "Watch Next": "Watch whether scheduling behavior changes in future releases.",
                        "Category": "Infrastructure",
                        "Source Priority": "High",
                        "AGI Relevance": "Medium",
                        "Quality Hint": 90,
                    }
                )
            ],
            self.root,
            output_report=report_path,
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertIn("missing_core_public_topic", report["blocked_reasons_by_title"]["Distributed systems scheduling update"])

    def test_missing_attribution_fails(self):
        manifest = sync.sync_records([eligible_record(**{"Attribution Status": "Missing"})], self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertNotIn("notion-agent-reliability", launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_unsafe_copyright_fails(self):
        manifest = sync.sync_records([eligible_record(**{"Copyright Status": "Unsafe"})], self.root)

        launched_slugs = {item["slug"] for item in manifest["launched"]}
        self.assertNotIn("notion-agent-reliability", launched_slugs)
        self.assertEqual(manifest["pages_blocked"], 1)

    def test_existing_public_signals_still_pass_as_safe_existing_public_signals(self):
        manifest = sync.sync_records([], self.root)

        self.assertEqual(manifest["pages_launched"], len(manifest["launched"]))
        self.assertGreaterEqual(manifest["pages_launched"], 1)

    def test_valid_undeclared_existing_page_is_reconciled(self):
        shutil.rmtree(self.root / "signals")
        signals_root = self.root / "signals"
        orphan_dir = signals_root / "valid-orphan-signal"
        orphan_dir.mkdir(parents=True)
        (signals_root / "public_launch_manifest.json").write_text(
            json.dumps({"launched": []}),
            encoding="utf-8",
        )
        (orphan_dir / "index.html").write_text(
            "<h1>Valid orphan Signal</h1><h2>Summary</h2><p>Existing summary-only public Signal retained.</p>",
            encoding="utf-8",
        )
        report_path = self.root / "tmp" / "dysonx_public_signals_sync_report.json"

        manifest = sync.sync_records([], self.root, output_report=report_path)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        launched_slugs = {item["slug"] for item in manifest["launched"]}

        self.assertIn("valid-orphan-signal", launched_slugs)
        self.assertTrue((orphan_dir / "index.html").exists())
        self.assertEqual(report["orphan_pages_detected"], 1)
        self.assertEqual(report["orphan_pages_reconciled"], 1)
        self.assertEqual(report["orphan_pages_removed"], 0)

    def test_invalid_stale_orphan_page_is_removed(self):
        shutil.rmtree(self.root / "signals")
        signals_root = self.root / "signals"
        orphan_dir = signals_root / "invalid-stale-orphan"
        orphan_dir.mkdir(parents=True)
        (signals_root / "public_launch_manifest.json").write_text(
            json.dumps({"launched": []}),
            encoding="utf-8",
        )
        (orphan_dir / "index.html").write_text("<h1>Invalid stale orphan</h1>", encoding="utf-8")
        report_path = self.root / "tmp" / "dysonx_public_signals_sync_report.json"

        manifest = sync.sync_records([], self.root, output_report=report_path)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        launched_slugs = {item["slug"] for item in manifest["launched"]}

        self.assertNotIn("invalid-stale-orphan", launched_slugs)
        self.assertFalse((orphan_dir / "index.html").exists())
        self.assertEqual(report["orphan_pages_detected"], 1)
        self.assertEqual(report["orphan_pages_reconciled"], 0)
        self.assertEqual(report["orphan_pages_removed"], 1)

    def test_invalid_declared_existing_page_is_not_left_orphaned(self):
        shutil.rmtree(self.root / "signals")
        signals_root = self.root / "signals"
        stale_dir = signals_root / "invalid-declared-signal"
        stale_dir.mkdir(parents=True)
        (signals_root / "public_launch_manifest.json").write_text(
            json.dumps({"launched": [{"slug": "invalid-declared-signal"}]}),
            encoding="utf-8",
        )
        (stale_dir / "index.html").write_text("<h1>Invalid declared Signal</h1>", encoding="utf-8")
        report_path = self.root / "tmp" / "dysonx_public_signals_sync_report.json"

        manifest = sync.sync_records([], self.root, output_report=report_path)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        launched_slugs = {item["slug"] for item in manifest["launched"]}

        self.assertNotIn("invalid-declared-signal", launched_slugs)
        self.assertFalse((stale_dir / "index.html").exists())
        self.assertEqual(report["orphan_pages_removed"], 1)

    def test_source_name_is_used_when_source_label_is_missing(self):
        record = eligible_record(**{"Source Name": "arXiv cs.CV RSS", "Quality Hint": 94})
        del record["Source Label"]
        manifest = sync.sync_records([record], self.root)
        entry = next(item for item in manifest["launched"] if item["slug"] == "notion-agent-reliability")
        page = (self.root / "signals" / "notion-agent-reliability" / "index.html").read_text(encoding="utf-8")

        self.assertEqual(entry["source_name"], "arXiv cs.CV RSS")
        self.assertIn(">arXiv cs.CV RSS</a>", page)

    def test_sync_report_includes_blocked_reasons(self):
        report_path = self.root / "tmp" / "dysonx_public_signals_sync_report.json"
        sync.sync_records(
            [
                eligible_record(),
                eligible_record(
                    **{
                        "Signal Title": "Blocked missing attribution Signal",
                        "Slug": "blocked-missing-attribution",
                        "Attribution Status": "Missing",
                    }
                ),
            ],
            self.root,
            output_report=report_path,
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(report["total_notion_rows"], 2)
        self.assertEqual(report["eligible_public_rows"], 1)
        self.assertEqual(report["unique_eligible_rows"], 1)
        self.assertEqual(report["duplicate_slug_count"], 0)
        self.assertEqual(report["blocked_rows"], 1)
        self.assertEqual(report["blocked_by_policy"], 1)
        self.assertGreaterEqual(report["published_total"], 1)
        self.assertLessEqual(report["index_displayed"], sync.DEFAULT_SIGNALS_INDEX_LIMIT)
        self.assertLessEqual(report["rss_items"], sync.DEFAULT_RSS_ITEM_LIMIT)
        self.assertLessEqual(report["feed_items"], sync.DEFAULT_JSON_FEED_ITEM_LIMIT)
        self.assertIn("orphan_pages_detected", report)
        self.assertIn("orphan_pages_reconciled", report)
        self.assertIn("orphan_pages_removed", report)
        self.assertIn("Blocked missing attribution Signal", report["blocked_reasons_by_title"])
        self.assertIn("attribution_incomplete", report["blocked_reasons_by_title"]["Blocked missing attribution Signal"])
        self.assertIn("notion-agent-reliability", report["new_slugs"])

    def test_sync_report_includes_strict_public_blocked_reasons(self):
        report_path = self.root / "tmp" / "dysonx_public_signals_sync_report.json"
        sync.sync_records(
            [
                eligible_record(
                    **{
                        "Signal Title": "Blocked loose public Signal",
                        "Slug": "blocked-loose-public-signal",
                        "Source Priority": "Medium",
                        "Quality Hint": 79,
                        "AGI Relevance": "Low",
                        "Ready for Pipeline": False,
                        "Published": False,
                    }
                )
            ],
            self.root,
            output_report=report_path,
        )
        report = json.loads(report_path.read_text(encoding="utf-8"))
        reasons = report["blocked_reasons_by_title"]["Blocked loose public Signal"]

        self.assertIn("source_priority_below_high", reasons)
        self.assertIn("quality_hint_below_80", reasons)
        self.assertIn("agi_relevance_below_medium", reasons)

    def test_persistent_inventory_exceeds_surface_windows(self):
        shutil.rmtree(self.root / "signals")
        records = []
        for index in range(35):
            records.append(
                eligible_record(
                    **{
                        "Signal ID": f"sig_inventory_{index:02d}",
                        "Signal Title": f"Window public Signal {index:02d}",
                        "Slug": f"window-public-signal-{index:02d}",
                        "Summary": f"Summary-only public Signal {index:02d} about AI agent evaluation.",
                        "Source Priority": "High",
                        "AGI Relevance": "Medium",
                        "Quality Hint": 90,
                        "Published": False,
                        "Ready for Pipeline": False,
                        "Published Date": "2026-06-01T00:00:00Z",
                    }
                )
            )

        manifest = sync.sync_records(records, self.root, refreshed_at="2026-06-27T00:00:00Z")
        launched_slugs = [item["slug"] for item in manifest["launched"]]
        artifact_manifest = json.loads((self.root / "signals" / "public_artifact_manifest.json").read_text(encoding="utf-8"))
        artifact_paths = {item["path"] for item in artifact_manifest["artifacts"]}
        sitemap = (self.root / "sitemap.xml").read_text(encoding="utf-8")
        index_html = (self.root / "signals" / "index.html").read_text(encoding="utf-8")
        rss = (self.root / "rss.xml").read_text(encoding="utf-8")
        feed = json.loads((self.root / "feed.json").read_text(encoding="utf-8"))
        thirty_first_slug = "window-public-signal-30"

        self.assertEqual(manifest["pages_launched"], 35)
        self.assertEqual(len(manifest["launched"]), 35)
        self.assertEqual(launched_slugs[30], thirty_first_slug)
        self.assertTrue((self.root / "signals" / thirty_first_slug / "index.html").exists())
        self.assertIn(thirty_first_slug, launched_slugs)
        self.assertIn(f"signals/{thirty_first_slug}/index.html", artifact_paths)
        self.assertIn(f"{FIXTURE_BASE_URL}/signals/{thirty_first_slug}/", sitemap)
        self.assertEqual(index_html.count("<article>"), sync.DEFAULT_SIGNALS_INDEX_LIMIT)
        self.assertEqual(rss.count("<item>"), sync.DEFAULT_RSS_ITEM_LIMIT)
        self.assertEqual(len(feed["items"]), sync.DEFAULT_JSON_FEED_ITEM_LIMIT)
        self.assertNotIn(f"/signals/{thirty_first_slug}/", index_html)
        self.assertNotIn(f"/signals/{thirty_first_slug}/", rss)
        self.assertNotIn(f"/signals/{thirty_first_slug}/", json.dumps(feed))

        records.append(
            eligible_record(
                **{
                    "Signal ID": "sig_inventory_35",
                    "Signal Title": "Window public Signal 35",
                    "Slug": "window-public-signal-35",
                    "Summary": "Summary-only public Signal 35 about AI agent evaluation.",
                    "Source Priority": "High",
                    "AGI Relevance": "Medium",
                    "Quality Hint": 90,
                    "Published": False,
                    "Ready for Pipeline": False,
                    "Published Date": "2026-06-01T00:00:00Z",
                }
            )
        )
        manifest = sync.sync_records(records, self.root, refreshed_at="2026-06-28T00:00:00Z")
        sitemap = (self.root / "sitemap.xml").read_text(encoding="utf-8")

        self.assertEqual(manifest["pages_launched"], 36)
        self.assertIn(f"{FIXTURE_BASE_URL}/signals/window-public-signal-35/", sitemap)

    def test_duplicate_slugs_select_deterministic_highest_ranked_record(self):
        shutil.rmtree(self.root / "signals")
        lower_ranked = eligible_record(
            **{
                "Signal ID": "sig_duplicate_low",
                "Signal Title": "Duplicate slug lower ranked Signal",
                "Slug": "duplicate-agent-signal",
                "Summary": "Lower ranked summary-only Signal about AI agent evaluation.",
                "Source Priority": "High",
                "AGI Relevance": "Medium",
                "Quality Hint": 86,
                "Published Date": "2026-06-01T00:00:00Z",
            }
        )
        higher_ranked = eligible_record(
            **{
                "Signal ID": "sig_duplicate_high",
                "Signal Title": "Duplicate slug higher ranked Signal",
                "Slug": "duplicate-agent-signal",
                "Summary": "Higher ranked summary-only Signal about AI agent evaluation.",
                "Source Priority": "Critical",
                "AGI Relevance": "Critical",
                "Quality Hint": 95,
                "Published Date": "2026-06-02T00:00:00Z",
            }
        )

        first_manifest = sync.sync_records([lower_ranked, higher_ranked], self.root, refreshed_at="2026-06-27T00:00:00Z")
        first_entry = first_manifest["launched"][0]
        shutil.rmtree(self.root / "signals")
        second_manifest = sync.sync_records([higher_ranked, lower_ranked], self.root, refreshed_at="2026-06-27T00:00:00Z")
        second_entry = second_manifest["launched"][0]

        self.assertEqual(first_manifest["pages_launched"], 1)
        self.assertEqual(first_entry["signal_id"], "sig_duplicate_high")
        self.assertEqual(second_entry["signal_id"], "sig_duplicate_high")
        self.assertEqual(first_manifest["material_signature"], second_manifest["material_signature"])

    def test_identical_rerun_with_large_inventory_has_no_material_diff(self):
        shutil.rmtree(self.root / "signals")
        records = [
            eligible_record(
                **{
                    "Signal ID": f"sig_stable_{index:02d}",
                    "Signal Title": f"Stable public Signal {index:02d}",
                    "Slug": f"stable-public-signal-{index:02d}",
                    "Summary": f"Summary-only public Signal {index:02d} about AI agent evaluation.",
                    "Quality Hint": 90,
                    "Published Date": "2026-06-01T00:00:00Z",
                }
            )
            for index in range(35)
        ]

        sync.sync_records(records, self.root, refreshed_at="2026-06-27T00:00:00Z")
        first_snapshot = self.output_snapshot()
        sync.sync_records(records, self.root, refreshed_at="2026-06-28T00:00:00Z")
        second_snapshot = self.output_snapshot()

        self.assertEqual(second_snapshot, first_snapshot)

    def test_auto_merge_marker_absent_for_changed_below_relaxed_public_policy(self):
        manifest = sync.sync_records(
            [
                eligible_record(**{"Source Priority": "Medium", "Quality Hint": 94}),
                eligible_record(
                    **{
                        "Signal ID": "sig_low_quality",
                        "Signal Title": "Critical but low quality Signal",
                        "Slug": "critical-low-quality",
                        "Quality Hint": 79,
                    }
                ),
                eligible_record(
                    **{
                        "Signal ID": "sig_low_relevance",
                        "Signal Title": "Low relevance Signal",
                        "Slug": "low-relevance-signal",
                        "AGI Relevance": "Low",
                        "Quality Hint": 94,
                    }
                )
            ],
            self.root,
        )

        self.assertFalse(sync.auto_merge_marker_eligible(manifest, ["signals/notion-agent-reliability/index.html"]))
        self.assertFalse(sync.auto_merge_marker_eligible(manifest, ["signals/critical-low-quality/index.html"]))
        self.assertFalse(sync.auto_merge_marker_eligible(manifest, ["signals/low-relevance-signal/index.html"]))

    def test_auto_merge_marker_present_when_all_changed_signals_satisfy_relaxed_public_policy(self):
        manifest = sync.sync_records(
            [
                eligible_record(**{"Source Priority": "High", "AGI Relevance": "Medium", "Quality Hint": 80, "Published": False}),
                eligible_record(
                    **{
                        "Signal ID": "sig_second_critical",
                        "Signal Title": "Second Critical Signal",
                        "Slug": "second-critical-signal",
                        "Quality Hint": 94,
                        "Ready for Pipeline": False,
                    }
                ),
            ],
            self.root,
        )

        self.assertTrue(
            sync.auto_merge_marker_eligible(
                manifest,
                [
                    "signals/notion-agent-reliability/index.html",
                    "signals/second-critical-signal/index.html",
                    "signals/index.html",
                    "signals/public_launch_manifest.json",
                ],
            )
        )

    def test_auto_merge_marker_absent_for_off_topic_manifest_entry(self):
        manifest = sync.sync_records(
            [
                eligible_record(
                    **{
                        "Signal ID": "sig_robot_vacuum",
                        "Signal Title": "AI agent benchmark Signal",
                        "Slug": "robot-vacuum-signal",
                        "Source Priority": "High",
                        "AGI Relevance": "Medium",
                        "Quality Hint": 90,
                    }
                )
            ],
            self.root,
        )
        entry = next(item for item in manifest["launched"] if item["slug"] == "robot-vacuum-signal")
        entry["title"] = "Robot vacuum roundup"

        self.assertFalse(sync.auto_merge_marker_eligible(manifest, ["signals/robot-vacuum-signal/index.html"]))

    def test_public_manifest_still_carries_source_priority(self):
        sync.sync_records([eligible_record(**{"Quality Hint": 94})], self.root)
        manifest = json.loads((self.root / "signals" / "public_launch_manifest.json").read_text(encoding="utf-8"))
        entry = next(item for item in manifest["launched"] if item["slug"] == "notion-agent-reliability")

        self.assertEqual(entry["source_priority"], "Critical")


if __name__ == "__main__":
    unittest.main()
