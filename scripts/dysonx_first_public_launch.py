#!/usr/bin/env python3
"""DysonX First Public Launch V1.

Copies release-guarded Step 4 production publish pack artifacts into the
repository public static surface after explicit Owner launch authorization.
This tool does not call OpenAI, scrape sources, dispatch workflows, deploy
externally, write backend state, or perform social/newsletter distribution.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import sys
from datetime import datetime, timezone
from typing import Any


LAUNCH_VERSION = "first_public_launch_v1"
REQUIRED_AUTHORIZATION = "explicit_owner_authorization_in_step_5_prompt"
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


class FirstPublicLaunchError(ValueError):
    """Raised when Step 5 launch cannot safely proceed."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    input_path = pathlib.Path(path)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI fails closed on malformed JSON.
        raise FirstPublicLaunchError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise FirstPublicLaunchError(f"{label} must be a JSON object")
    return data


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def signal_id(record: dict[str, Any]) -> str:
    return normalize_text(record.get("signal_id") or record.get("canonical_signal_id") or record.get("id"))


def slug(record: dict[str, Any]) -> str:
    return normalize_text(record.get("slug") or record.get("public_slug") or record.get("signal_slug"))


def title(record: dict[str, Any]) -> str:
    return normalize_text(record.get("title") or record.get("public_title")) or "Untitled Signal"


def required_actions_for(blockers: list[str]) -> list[str]:
    actions: list[str] = []
    if "missing_owner_launch_authorization" in blockers:
        actions.append("provide_explicit_owner_launch_authorization_for_step_5")
    if "release_guard_not_passed" in blockers:
        actions.append("rerun_step_4_release_guard_and_resolve_blockers")
    if "no_approved_packaged_pages" in blockers:
        actions.append("provide_at_least_one_release_guarded_production_pack_page")
    if "packaged_file_missing" in blockers:
        actions.append("regenerate_step_4_production_publish_pack")
    if "raw_article_body_detected" in blockers:
        actions.append("remove_raw_article_body_before_public_launch")
    if "internal_review_state_detected" in blockers:
        actions.append("remove_internal_review_state_before_public_launch")
    if any("published" in blocker or "production_publish" in blocker or "deployed" in blocker for blocker in blockers):
        actions.append("use_only_not_yet_published_not_deployed_step_4_pack_entries")
    return list(dict.fromkeys(actions)) or ["resolve_first_public_launch_blockers"]


def resolve_packaged_page_path(production_pack_dir: pathlib.Path, entry: dict[str, Any]) -> pathlib.Path:
    raw_path = normalize_text(entry.get("packaged_page_path"))
    candidate = pathlib.Path(raw_path)
    if raw_path:
        return candidate
    page_slug = slug(entry)
    if page_slug:
        return production_pack_dir / "signals" / page_slug / "index.html"
    return candidate


def transform_launched_html(html: str, created_at: str) -> str:
    launched = html.replace("Production Publish Candidate / Not Yet Deployed", "Published")
    launched = launched.replace("Draft Preview / Not Published", "Published")
    launched = launched.replace('  <meta name="robots" content="noindex,nofollow">\n', "")
    launched = launched.replace(
        "Step 5 explicit Owner launch authorization is required before production release.",
        "Published through DysonX First Public Launch V1 after explicit Owner launch authorization.",
    )
    launched = launched.replace(
        "Step 5 explicit Owner launch authorization is required before these artifacts can be published to production.",
        "Explicit Owner launch authorization was provided for DysonX First Public Launch V1.",
    )
    launched = launched.replace(
        "Step 5 explicit Owner launch authorization is still required.",
        "Explicit Owner launch authorization was provided for DysonX First Public Launch V1.",
    )
    launched = launched.replace(
        "No production publishing or deployment has occurred.",
        "Production static files were published into the repository public surface. External deployment status depends on repository hosting automation.",
    )
    launched = launched.replace(
        "Production publish pack candidate only. Step 5 launch authorization required.",
        "Published static public Signal page.",
    )
    launched = launched.replace(
        "This packaged page is a production publish candidate. It is not published, not live, and not deployed.",
        "This page is a published DysonX public Signal. External deployment status depends on repository hosting automation.",
    )
    launched = launched.replace("DysonX Draft Preview", "DysonX Public Signal")
    launched = launched.replace("Back to Public Signals Draft Preview", "Back to Public Signals")
    if "</main>" in launched:
        launched = launched.replace(
            "</main>",
            f'<p class="muted">Launched at {created_at}. Manual external deployment was not performed by this tool.</p>\n</main>',
        )
    return launched


def page_blockers(entry: dict[str, Any], production_pack_dir: pathlib.Path) -> tuple[list[str], pathlib.Path | None, str]:
    blockers: list[str] = []
    html = ""
    page_path = resolve_packaged_page_path(production_pack_dir, entry)
    if entry.get("approved_for_production_pack") is not True:
        blockers.append("not_approved_for_production_pack")
    if entry.get("published") is True:
        blockers.append("pack_entry_published_true_before_launch")
    if entry.get("production_publish_performed") is True:
        blockers.append("pack_entry_production_publish_performed_true_before_launch")
    if entry.get("deployed") is True:
        blockers.append("pack_entry_deployed_true_before_launch")
    if not page_path.exists():
        blockers.append("packaged_file_missing")
        return list(dict.fromkeys(blockers)), page_path, html
    html = page_path.read_text(encoding="utf-8", errors="ignore")
    if contains_any(html, RAW_BODY_MARKERS):
        blockers.append("raw_article_body_detected")
    if contains_any(html, INTERNAL_STATE_MARKERS):
        blockers.append("internal_review_state_detected")
    return list(dict.fromkeys(blockers)), page_path, html


def block_entry(record: dict[str, Any], blockers: list[str]) -> dict[str, Any]:
    return {
        "signal_id": signal_id(record),
        "slug": slug(record),
        "title": title(record),
        "blockers": list(dict.fromkeys(blockers)),
        "required_next_actions": required_actions_for(blockers),
    }


def verify_launch_inputs(
    pack_manifest: dict[str, Any],
    release_guard_report: dict[str, Any],
    authorization: str,
) -> list[str]:
    blockers: list[str] = []
    if authorization != REQUIRED_AUTHORIZATION:
        blockers.append("missing_owner_launch_authorization")
    if release_guard_report.get("release_guard_passed") is not True or pack_manifest.get("release_guard_passed") is not True:
        blockers.append("release_guard_not_passed")
    if not as_list(pack_manifest.get("packaged")):
        blockers.append("no_approved_packaged_pages")
    if pack_manifest.get("production_publish_performed") is True:
        blockers.append("pack_manifest_production_publish_performed_true_before_launch")
    if pack_manifest.get("no_openai_call_performed") is not True:
        blockers.append("pack_manifest_openai_flag_invalid")
    if pack_manifest.get("no_workflow_dispatch_performed") is not True:
        blockers.append("pack_manifest_workflow_dispatch_flag_invalid")
    if pack_manifest.get("no_deployment_performed") is not True:
        blockers.append("pack_manifest_deployment_flag_invalid")
    if pack_manifest.get("step_5_launch_authorization_required") is not True:
        blockers.append("step_5_launch_authorization_not_required_by_pack")
    return list(dict.fromkeys(blockers))


def copy_index(production_pack_dir: pathlib.Path, public_output_root: pathlib.Path, created_at: str) -> None:
    source_index = production_pack_dir / "signals" / "index.html"
    target_index = public_output_root / "signals" / "index.html"
    target_index.parent.mkdir(parents=True, exist_ok=True)
    if source_index.exists():
        html = source_index.read_text(encoding="utf-8", errors="ignore")
        target_index.write_text(transform_launched_html(html, created_at), encoding="utf-8")
    else:
        target_index.write_text(
            "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>DysonX Public Signals</title></head>"
            "<body><main><h1>DysonX Public Signals</h1><p>Published Signal pages are listed in the launch manifest.</p></main></body></html>\n",
            encoding="utf-8",
        )


def generate_launch(
    production_pack_dir: pathlib.Path,
    pack_manifest_path: pathlib.Path,
    release_guard_report_path: pathlib.Path,
    public_output_root: pathlib.Path,
    owner_launch_authorization: str,
) -> dict[str, Any]:
    created_at = utc_now()
    pack_manifest = read_json_object(pack_manifest_path, "Production publish pack manifest")
    release_guard_report = read_json_object(release_guard_report_path, "Release guard report")
    blocked: list[dict[str, Any]] = []
    launched: list[dict[str, Any]] = []

    top_level_blockers = verify_launch_inputs(pack_manifest, release_guard_report, owner_launch_authorization)
    if top_level_blockers:
        raise FirstPublicLaunchError(", ".join(top_level_blockers))

    public_output_root.mkdir(parents=True, exist_ok=True)
    for entry in as_list(pack_manifest.get("packaged")):
        if not isinstance(entry, dict):
            continue
        blockers, source_path, html = page_blockers(entry, production_pack_dir)
        if blockers or source_path is None:
            blocked.append(block_entry(entry, blockers or ["unknown_first_public_launch_blocker"]))
            continue
        page_slug = slug(entry)
        target_path = public_output_root / "signals" / page_slug / "index.html"
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(transform_launched_html(html, created_at), encoding="utf-8")
        launched.append(
            {
                "signal_id": signal_id(entry),
                "title": title(entry),
                "slug": page_slug,
                "public_path": str(target_path),
                "public_url_path": f"/signals/{page_slug}/",
                "published": True,
                "production_publish_performed": True,
                "source_pack_entry": entry,
            }
        )

    for pack_blocked in as_list(pack_manifest.get("blocked")):
        if isinstance(pack_blocked, dict):
            blocked.append(
                {
                    "signal_id": signal_id(pack_blocked),
                    "slug": slug(pack_blocked),
                    "title": title(pack_blocked),
                    "blockers": as_list(pack_blocked.get("blockers")) or ["blocked_by_production_publish_pack"],
                    "required_next_actions": as_list(pack_blocked.get("required_next_actions")),
                }
            )

    if not launched:
        raise FirstPublicLaunchError("no_pages_launched")

    copy_index(production_pack_dir, public_output_root, created_at)
    manifest = {
        "launch_version": LAUNCH_VERSION,
        "created_at": created_at,
        "launch_authorization": REQUIRED_AUTHORIZATION,
        "source_pack_manifest": str(pack_manifest_path),
        "source_release_guard_report": str(release_guard_report_path),
        "public_output_root": str(public_output_root),
        "pages_launched": len(launched),
        "pages_blocked": len(blocked),
        "launched": launched,
        "blocked": blocked,
        "release_guard_passed": True,
        "manual_publish_approval_verified": True,
        "publish_readiness_gate_verified": True,
        "production_pack_verified": True,
        "openai_call_performed": False,
        "workflow_dispatch_performed": False,
        "manual_external_deployment_performed": False,
        "social_distribution_performed": False,
        "newsletter_distribution_performed": False,
    }
    manifest_path = public_output_root / "signals" / "public_launch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch DysonX First Public Signal Pages V1.")
    parser.add_argument("--production-pack-dir", required=True, help="Step 4 production publish pack directory.")
    parser.add_argument("--pack-manifest", required=True, help="Step 4 production publish pack manifest JSON.")
    parser.add_argument("--release-guard-report", required=True, help="Step 4 release guard report JSON.")
    parser.add_argument("--public-output-root", required=True, help="Repository public static output root.")
    parser.add_argument("--owner-launch-authorization", required=True, help="Explicit Owner launch authorization token.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = generate_launch(
            pathlib.Path(args.production_pack_dir),
            pathlib.Path(args.pack_manifest),
            pathlib.Path(args.release_guard_report),
            pathlib.Path(args.public_output_root),
            args.owner_launch_authorization,
        )
    except FirstPublicLaunchError as exc:
        print(f"[first-public-launch] failed: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[first-public-launch] failed: {exc}", file=sys.stderr)
        return 2
    print(
        "[first-public-launch] wrote launch: "
        f"{manifest['public_output_root']} pages_launched={manifest['pages_launched']} "
        f"pages_blocked={manifest['pages_blocked']} release_guard_passed={manifest['release_guard_passed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
