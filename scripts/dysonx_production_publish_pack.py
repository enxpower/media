#!/usr/bin/env python3
"""DysonX Production Publish Pack V1.

Creates a deterministic offline production publish pack candidate from Step 2
draft public pages and Step 3 manual approval. This tool does not publish,
deploy, call OpenAI, dispatch workflows, fetch URLs, scrape sources, write to
current deployment host, or mark any page as published.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import sys
from datetime import datetime, timezone
from html import escape
from typing import Any


PACK_VERSION = "production_publish_pack_v1"
RELEASE_GUARD_VERSION = "production_publish_pack_release_guard_v1"
DEFAULT_OUTPUT_DIR = pathlib.Path("tmp") / "production_publish_pack"
RAW_BODY_MARKERS = (
    "raw article body",
    "raw_body",
    "article_body",
    "scraped_text",
    "raw copyrighted article text",
)
INTERNAL_STATE_MARKERS = (
    "owner_comment",
    "owner comments",
    "internal decision trail",
    "private review state",
    "selected_owner_decision",
    "review_session",
)


class PublishPackInputError(ValueError):
    """Raised when the pack generator cannot safely process inputs."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    input_path = pathlib.Path(path)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI fails closed on malformed JSON.
        raise PublishPackInputError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise PublishPackInputError(f"{label} must be a JSON object")
    return data


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def first_present(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, "", []):
            return value
    return None


def signal_id(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "signal_id", "canonical_signal_id", "id"))


def slug(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "slug", "public_slug", "signal_slug"))


def title(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "title", "public_title")) or "Untitled Signal"


def safe_output_root(output_dir: pathlib.Path) -> pathlib.Path:
    normalized = pathlib.Path(output_dir)
    if normalized.is_absolute():
        if not any(part == "tmp" or part.startswith("tmp") for part in normalized.parts):
            raise PublishPackInputError("Absolute output directory must be under a temporary pack path")
        return normalized
    if not normalized.parts or normalized.parts[0] != "tmp":
        raise PublishPackInputError("Output directory must be under tmp/ for production publish pack generation")
    return normalized


def index_manifest_pages(manifest: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    pages = manifest.get("pages")
    if not isinstance(pages, list):
        raise PublishPackInputError("Public pages manifest must include a pages list")
    by_slug: dict[str, dict[str, Any]] = {}
    by_signal_id: dict[str, dict[str, Any]] = {}
    for page in pages:
        if not isinstance(page, dict):
            continue
        page_slug = slug(page)
        page_signal_id = signal_id(page)
        if page_slug:
            by_slug[page_slug] = page
        if page_signal_id:
            by_signal_id[page_signal_id] = page
    return by_slug, by_signal_id


def lookup_manifest_page(
    approval: dict[str, Any],
    pages_by_slug: dict[str, dict[str, Any]],
    pages_by_signal_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    approval_slug = slug(approval)
    approval_signal_id = signal_id(approval)
    if approval_slug and approval_slug in pages_by_slug:
        return pages_by_slug[approval_slug]
    if approval_signal_id and approval_signal_id in pages_by_signal_id:
        return pages_by_signal_id[approval_signal_id]
    return None


def source_html_path(public_pages_dir: pathlib.Path, page: dict[str, Any], approval: dict[str, Any]) -> pathlib.Path:
    page_slug = slug(page) or slug(approval)
    return public_pages_dir / "signals" / page_slug / "index.html"


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def page_text_summary(html: str, label: str) -> str:
    pattern = re.compile(rf"<h2>{re.escape(label)}</h2>\s*<p>(.*?)</p>", re.IGNORECASE | re.DOTALL)
    match = pattern.search(html)
    if not match:
        return ""
    text = re.sub(r"<[^>]+>", "", match.group(1))
    return re.sub(r"\s+", " ", text).strip()


def source_count(html: str) -> int:
    return len(re.findall(r"<a\s+[^>]*href=", html, flags=re.IGNORECASE))


def page_blockers(
    approval: dict[str, Any],
    page: dict[str, Any] | None,
    public_pages_dir: pathlib.Path,
    manifest: dict[str, Any],
    approval_report: dict[str, Any],
) -> tuple[list[str], pathlib.Path | None, str]:
    blockers: list[str] = []
    html = ""
    source_path: pathlib.Path | None = None
    if approval.get("approved_for_production_pack") is not True:
        blockers.append("not_approved_for_production_pack")
    if approval.get("published") is True:
        blockers.append("approval_published_true")
    if approval.get("production_publish_performed") is True:
        blockers.append("approval_production_publish_performed_true")
    if approval.get("deployed") is True:
        blockers.append("approval_deployed_true")
    if approval_report.get("production_publish_performed") is True:
        blockers.append("approval_report_production_publish_performed_true")
    if manifest.get("production_publish_performed") is True:
        blockers.append("public_pages_manifest_production_publish_performed_true")
    if page is None:
        blockers.append("page_not_found_in_public_pages_manifest")
    else:
        if page.get("publish_readiness_gate_passed") is not True:
            blockers.append("publish_readiness_gate_not_passed")
        if page.get("ready_for_public_generation") is not True:
            blockers.append("not_ready_for_public_generation")
        if page.get("published") is True:
            blockers.append("manifest_published_true")
        if page.get("production_publish_performed") is True:
            blockers.append("manifest_production_publish_performed_true")
        if page.get("deployed") is True:
            blockers.append("manifest_deployed_true")
        source_path = source_html_path(public_pages_dir, page, approval)
        if not source_path.exists():
            blockers.append("source_html_file_missing")
        else:
            html = source_path.read_text(encoding="utf-8", errors="ignore")
            if "Draft Preview / Not Published" not in html:
                blockers.append("source_page_missing_draft_not_published_status")
            if contains_any(html, RAW_BODY_MARKERS):
                blockers.append("raw_article_body_detected")
            if contains_any(html, INTERNAL_STATE_MARKERS):
                blockers.append("internal_review_state_detected")
            forbidden_status = ("Production deployed", "Deployed", "Live", ">Published<")
            if any(token in html for token in forbidden_status):
                blockers.append("source_page_claims_published_or_deployed")
    return list(dict.fromkeys(blockers)), source_path, html


def required_actions_for(blockers: list[str]) -> list[str]:
    actions: list[str] = []
    if "not_approved_for_production_pack" in blockers:
        actions.append("obtain_manual_publish_approval_before_packaging")
    if "page_not_found_in_public_pages_manifest" in blockers:
        actions.append("regenerate_public_signal_pages_manifest")
    if "source_html_file_missing" in blockers:
        actions.append("provide_generated_public_signal_page_html")
    if any("published_true" in blocker or "production_publish" in blocker or "deployed" in blocker for blocker in blockers):
        actions.append("use_only_not_published_not_deployed_step_2_and_step_3_artifacts")
    if "source_page_missing_draft_not_published_status" in blockers:
        actions.append("regenerate_step_2_draft_preview_page")
    if "raw_article_body_detected" in blockers:
        actions.append("remove_raw_article_body_before_packaging")
    if "internal_review_state_detected" in blockers:
        actions.append("remove_internal_review_state_before_packaging")
    return list(dict.fromkeys(actions)) or ["resolve_blockers_before_step_5_launch_pack"]


def block_entry(record: dict[str, Any], blockers: list[str]) -> dict[str, Any]:
    return {
        "signal_id": signal_id(record),
        "slug": slug(record),
        "title": title(record),
        "blockers": list(dict.fromkeys(blockers)),
        "required_next_actions": required_actions_for(blockers),
    }


def transform_candidate_html(html: str, generated_at: str) -> str:
    transformed = html.replace("Draft Preview / Not Published", "Production Publish Candidate / Not Yet Deployed")
    transformed = transformed.replace(
        "Manual Publish Approval V1 is required before production release.",
        "Step 5 explicit Owner launch authorization is required before production release.",
    )
    transformed = transformed.replace(
        "This generated page is a local static draft. It is not published, not production-approved, and not deployed.",
        "This packaged page is a production publish candidate. It is not published, not live, and not deployed.",
    )
    transformed = transformed.replace(
        "Static local draft preview only.",
        "Production publish pack candidate only. Step 5 launch authorization required.",
    )
    notice = (
        '<div class="notice"><strong>Production Publish Candidate / Not Yet Deployed.</strong> '
        "Step 5 explicit Owner launch authorization is still required. "
        "No production publishing or deployment has occurred.</div>"
    )
    transformed = transformed.replace("</main>", f"{notice}\n<p class=\"muted\">Packaged at {escape(generated_at)}.</p>\n</main>")
    return transformed


def render_index(packaged: list[dict[str, Any]], blocked: list[dict[str, Any]], generated_at: str) -> str:
    items = []
    for item in packaged:
        items.append(
            f"""
<article>
  <h2><a href="{escape(item['slug'], quote=True)}/">{escape(item['title'])}</a></h2>
  <p><strong>Slug:</strong> <code>{escape(item['slug'])}</code></p>
  <p><strong>Summary:</strong> {escape(item.get('summary') or 'Summary preserved in packaged Signal page.')}</p>
  <p><strong>AGI relevance:</strong> {escape(item.get('agi_relevance') or 'AGI relevance preserved in packaged Signal page.')}</p>
  <p><strong>Quality / confidence:</strong> {escape(item.get('quality_confidence') or 'Quality and confidence preserved in packaged Signal page.')}</p>
  <p><strong>Sources:</strong> {item.get('source_count', 0)} source link(s) detected in packaged page.</p>
</article>
"""
        )
    list_html = "\n".join(items) if items else "<p>No Signal pages were packaged.</p>"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>DysonX Public Signals</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #17202a; line-height: 1.55; }}
    main {{ max-width: 920px; margin: 0 auto; padding: 28px 20px 48px; }}
    .status {{ display: inline-block; margin-bottom: 16px; padding: 5px 9px; border: 1px solid #97b6c4; background: #eef7fa; color: #24505e; font-weight: 700; font-size: 0.85rem; }}
    .notice {{ border: 1px solid #d8dee6; border-left: 4px solid #97b6c4; background: #f6f8fa; padding: 14px; }}
    article {{ border-top: 1px solid #d8dee6; padding: 18px 0; }}
    a {{ color: #0f6f8f; }}
    code {{ background: #f6f8fa; padding: 1px 4px; }}
  </style>
</head>
<body>
<main>
<p class="status">Production Publish Candidate / Not Yet Deployed</p>
<h1>DysonX Public Signals</h1>
<div class="notice">
  Step 5 explicit Owner launch authorization is required before these artifacts can be published to production.
  No production publishing or deployment has occurred.
</div>
<p><strong>Generated pages:</strong> {len(packaged)}. <strong>Blocked pages:</strong> {len(blocked)}.</p>
{list_html}
<p>Generated at {escape(generated_at)}. Production publish pack candidate only.</p>
</main>
</body>
</html>
"""


def build_packaged_entry(
    approval: dict[str, Any],
    manifest_page: dict[str, Any],
    source_path: pathlib.Path,
    packaged_path: pathlib.Path,
    html: str,
) -> dict[str, Any]:
    page_slug = slug(approval) or slug(manifest_page)
    return {
        "signal_id": signal_id(approval) or signal_id(manifest_page),
        "title": title(approval) or title(manifest_page),
        "slug": page_slug,
        "source_page_path": str(source_path),
        "packaged_page_path": str(packaged_path),
        "packaged_preview_path": f"signals/{page_slug}/",
        "approved_for_production_pack": True,
        "published": False,
        "production_publish_performed": False,
        "deployed": False,
        "summary": page_text_summary(html, "Summary"),
        "agi_relevance": page_text_summary(html, "AGI Relevance"),
        "quality_confidence": page_text_summary(html, "Quality And Confidence"),
        "source_count": source_count(html),
    }


def release_guard_checks(manifest: dict[str, Any], output_dir: pathlib.Path) -> dict[str, bool]:
    packaged = [item for item in as_list(manifest.get("packaged")) if isinstance(item, dict)]
    all_html = ""
    for item in packaged:
        path = pathlib.Path(normalize_text(item.get("packaged_page_path")))
        if path.exists():
            all_html += "\n" + path.read_text(encoding="utf-8", errors="ignore")
    checks = {
        "manual_approval_report_present": bool(manifest.get("input_files", {}).get("approval_report")),
        "only_approved_pages_packaged": all(item.get("approved_for_production_pack") is True for item in packaged),
        "no_unapproved_pages_packaged": not any(item.get("approved_for_production_pack") is not True for item in packaged),
        "packaged_files_exist": all(pathlib.Path(normalize_text(item.get("packaged_page_path"))).exists() for item in packaged),
        "index_generated": (output_dir / "signals" / "index.html").exists(),
        "no_published_true_before_launch": not any(item.get("published") is True for item in packaged),
        "no_production_publish_performed_true": manifest.get("production_publish_performed") is False and not any(item.get("production_publish_performed") is True for item in packaged),
        "no_deployed_true": not any(item.get("deployed") is True for item in packaged),
        "no_raw_article_body_detected": not contains_any(all_html, RAW_BODY_MARKERS),
        "no_internal_review_state_detected": not contains_any(all_html, INTERNAL_STATE_MARKERS),
        "no_openai_call_performed": manifest.get("no_openai_call_performed") is True,
        "no_workflow_dispatch_performed": manifest.get("no_workflow_dispatch_performed") is True,
        "no_deployment_performed": manifest.get("no_deployment_performed") is True,
        "step_5_launch_authorization_required": manifest.get("step_5_launch_authorization_required") is True,
    }
    return checks


def build_release_guard_report(manifest: dict[str, Any], output_dir: pathlib.Path, created_at: str) -> dict[str, Any]:
    checks = release_guard_checks(manifest, output_dir)
    blockers = [name for name, passed in checks.items() if not passed]
    warnings: list[str] = []
    if manifest.get("pages_packaged", 0) == 0:
        warnings.append("no_pages_packaged")
    return {
        "release_guard_version": RELEASE_GUARD_VERSION,
        "created_at": created_at,
        "checked_pack_manifest": str(output_dir / "production_publish_pack_manifest.json"),
        "release_guard_passed": not blockers,
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
    }


def generate_pack(
    public_pages_dir: pathlib.Path,
    public_pages_manifest_path: pathlib.Path,
    approval_report_path: pathlib.Path,
    output_dir: pathlib.Path,
) -> dict[str, Any]:
    safe_root = safe_output_root(output_dir)
    if safe_root.exists():
        shutil.rmtree(safe_root)
    safe_root.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    manifest = read_json_object(public_pages_manifest_path, "Public Signal Page Generator manifest")
    approval_report = read_json_object(approval_report_path, "Manual Publish Approval report")
    pages_by_slug, pages_by_signal_id = index_manifest_pages(manifest)
    approved_entries = [item for item in as_list(approval_report.get("approved")) if isinstance(item, dict)]
    blocked: list[dict[str, Any]] = []
    packaged: list[dict[str, Any]] = []

    for approval in approved_entries:
        manifest_page = lookup_manifest_page(approval, pages_by_slug, pages_by_signal_id)
        blockers, source_path, html = page_blockers(approval, manifest_page, public_pages_dir, manifest, approval_report)
        if blockers or manifest_page is None or source_path is None:
            blocked.append(block_entry(approval, blockers or ["unknown_packaging_blocker"]))
            continue
        page_slug = slug(approval) or slug(manifest_page)
        packaged_path = safe_root / "signals" / page_slug / "index.html"
        packaged_path.parent.mkdir(parents=True, exist_ok=True)
        packaged_html = transform_candidate_html(html, created_at)
        packaged_path.write_text(packaged_html, encoding="utf-8")
        packaged.append(build_packaged_entry(approval, manifest_page, source_path, packaged_path, html))

    for approval_blocked in as_list(approval_report.get("blocked")):
        if isinstance(approval_blocked, dict):
            blocked.append(
                {
                    "signal_id": signal_id(approval_blocked),
                    "slug": slug(approval_blocked),
                    "title": title(approval_blocked),
                    "blockers": as_list(approval_blocked.get("blockers")) or ["blocked_by_manual_publish_approval"],
                    "required_next_actions": as_list(approval_blocked.get("required_next_actions")),
                }
            )

    (safe_root / "signals").mkdir(parents=True, exist_ok=True)
    (safe_root / "signals" / "index.html").write_text(render_index(packaged, blocked, created_at), encoding="utf-8")
    pack_manifest = {
        "pack_version": PACK_VERSION,
        "created_at": created_at,
        "input_files": {
            "public_pages_dir": str(public_pages_dir),
            "public_pages_manifest": str(public_pages_manifest_path),
            "approval_report": str(approval_report_path),
        },
        "output_directory": str(safe_root),
        "pages_seen": len(as_list(manifest.get("pages"))),
        "pages_approved_for_pack": len(approved_entries),
        "pages_packaged": len(packaged),
        "pages_blocked": len(blocked),
        "packaged": packaged,
        "blocked": blocked,
        "release_guard_passed": False,
        "step_5_launch_authorization_required": True,
        "no_public_publishing_performed": True,
        "no_deployment_performed": True,
        "no_openai_call_performed": True,
        "no_workflow_dispatch_performed": True,
        "production_publish_performed": False,
    }
    release_report = build_release_guard_report(pack_manifest, safe_root, created_at)
    pack_manifest["release_guard_passed"] = release_report["release_guard_passed"]
    (safe_root / "production_publish_pack_manifest.json").write_text(json.dumps(pack_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    release_report = build_release_guard_report(pack_manifest, safe_root, created_at)
    (safe_root / "release_guard_report.json").write_text(json.dumps(release_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    readme = """# DysonX Production Publish Pack

This directory contains a production publish pack candidate.

It is not deployed. Step 5 explicit Owner launch authorization is still required.

Suggested local check:

```bash
python3 -m http.server --directory tmp/<production-publish-pack> 8081
```

Then visit:

```text
http://localhost:8081/signals/
```

No production deployment was performed.
"""
    (safe_root / "README.md").write_text(readme, encoding="utf-8")
    return pack_manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate DysonX Production Publish Pack V1.")
    parser.add_argument("--public-pages-dir", required=True, help="Step 2 generated public Signal pages directory.")
    parser.add_argument("--public-pages-manifest", required=True, help="Step 2 public Signal pages manifest JSON.")
    parser.add_argument("--approval-report", required=True, help="Step 3 Manual Publish Approval report JSON.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Safe tmp/ output directory for the production publish pack.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = generate_pack(
            pathlib.Path(args.public_pages_dir),
            pathlib.Path(args.public_pages_manifest),
            pathlib.Path(args.approval_report),
            pathlib.Path(args.output_dir),
        )
    except PublishPackInputError as exc:
        print(f"[production-publish-pack] failed: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[production-publish-pack] failed: {exc}", file=sys.stderr)
        return 2
    print(
        "[production-publish-pack] wrote pack: "
        f"{manifest['output_directory']} pages_packaged={manifest['pages_packaged']} "
        f"pages_blocked={manifest['pages_blocked']} release_guard_passed={manifest['release_guard_passed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
