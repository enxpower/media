#!/usr/bin/env python3
"""DysonX Manual Publish Approval V1.

Consumes a Public Signal Page Generator manifest and an Owner manual approval
input, then writes an approval report for a future Production Publish Pack.
This tool is offline, deterministic, and standard-library only. It does not
publish, deploy, call OpenAI, dispatch workflows, fetch URLs, scrape sources,
modify generated pages, write production public pages, or approve production
release.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any


APPROVAL_VERSION = "manual_publish_approval_v1"
APPROVE_DECISION = "approve_for_production_pack"
ALLOWED_DECISIONS = {APPROVE_DECISION, "hold", "reject"}


class ApprovalInputError(ValueError):
    """Raised when the approval tool cannot safely process input."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    input_path = pathlib.Path(path)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI fails closed on malformed JSON.
        raise ApprovalInputError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ApprovalInputError(f"{label} must be a JSON object")
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


def page_signal_id(page: dict[str, Any]) -> str:
    return normalize_text(first_present(page, "signal_id", "canonical_signal_id", "id"))


def page_slug(page: dict[str, Any]) -> str:
    return normalize_text(first_present(page, "slug", "public_slug", "signal_slug"))


def decision_key(decision: dict[str, Any]) -> str:
    return normalize_text(first_present(decision, "slug", "signal_id", "id"))


def owner_is_valid(owner: Any) -> bool:
    if not isinstance(owner, dict):
        return False
    return bool(normalize_text(owner.get("name")) and normalize_text(owner.get("role")))


def index_pages(manifest: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    pages = manifest.get("pages")
    if not isinstance(pages, list):
        raise ApprovalInputError("Public Signal Page Generator manifest must include a pages list")
    by_slug: dict[str, dict[str, Any]] = {}
    by_signal_id: dict[str, dict[str, Any]] = {}
    for page in pages:
        if not isinstance(page, dict):
            continue
        slug = page_slug(page)
        signal_id = page_signal_id(page)
        if slug:
            by_slug[slug] = page
        if signal_id:
            by_signal_id[signal_id] = page
    return by_slug, by_signal_id


def blocked_manifest_entries(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    blocked: dict[str, dict[str, Any]] = {}
    for entry in as_list(manifest.get("blocked")):
        if not isinstance(entry, dict):
            continue
        for key in (page_slug(entry), page_signal_id(entry)):
            if key:
                blocked[key] = entry
    return blocked


def lookup_page(
    decision: dict[str, Any],
    pages_by_slug: dict[str, dict[str, Any]],
    pages_by_signal_id: dict[str, dict[str, Any]],
) -> dict[str, Any] | None:
    slug = normalize_text(decision.get("slug"))
    signal_id = normalize_text(first_present(decision, "signal_id", "id"))
    if slug and slug in pages_by_slug:
        return pages_by_slug[slug]
    if signal_id and signal_id in pages_by_signal_id:
        return pages_by_signal_id[signal_id]
    return None


def page_blockers(page: dict[str, Any], manifest: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if page.get("publish_readiness_gate_passed") is not True:
        blockers.append("publish_readiness_gate_not_passed")
    if page.get("ready_for_public_generation") is not True:
        blockers.append("not_ready_for_public_generation")
    if page.get("published") is True:
        blockers.append("published_true_blocks_manual_approval")
    if page.get("production_publish_performed") is True:
        blockers.append("page_production_publish_performed_true")
    if manifest.get("production_publish_performed") is True:
        blockers.append("manifest_production_publish_performed_true")
    if manifest.get("manual_publish_approval_required") is not True:
        blockers.append("manual_publish_approval_required_not_true")
    if not normalize_text(page.get("output_path")):
        blockers.append("missing_source_page_path")
    if not normalize_text(page.get("preview_path")):
        blockers.append("missing_preview_path")
    return blockers


def required_actions_for(blockers: list[str], decision: str | None = None) -> list[str]:
    actions: list[str] = []
    if "missing_owner_identity" in blockers:
        actions.append("provide_owner_name_and_role")
    if "missing_approved_at" in blockers:
        actions.append("provide_manual_approval_timestamp")
    if "missing_approval_decision" in blockers:
        actions.append("provide_approval_decision")
    if "unsupported_decision" in blockers:
        actions.append("use_approve_for_production_pack_hold_or_reject")
    if "decision_not_approve_for_production_pack" in blockers:
        actions.append("change_decision_to_approve_for_production_pack_after_owner_review")
    if "page_not_found_in_generator_manifest" in blockers:
        actions.append("regenerate_or_select_a_manifest_page")
    if "signal_was_blocked_by_generator" in blockers:
        actions.append("resolve_generator_blockers_before_manual_approval")
    if any("published" in blocker or "production_publish" in blocker for blocker in blockers):
        actions.append("use_only_unpublished_draft_preview_pages")
    if any("publish_readiness" in blocker or "ready_for_public_generation" in blocker for blocker in blockers):
        actions.append("rerun_publish_readiness_gate_and_public_signal_page_generator")
    if "manual_publish_approval_required_not_true" in blockers:
        actions.append("use_a_step_2_manifest_that_requires_manual_publish_approval")
    if decision in {"hold", "reject"} and not actions:
        actions.append("resolve_manual_publish_decision_before_step_4")
    return list(dict.fromkeys(actions)) or ["resolve_blockers_before_step_4_production_pack"]


def blocked_entry(
    decision: dict[str, Any],
    page: dict[str, Any] | None,
    blockers: list[str],
    manifest_blocked: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = page or manifest_blocked or decision
    signal_id = normalize_text(first_present(decision, "signal_id", "id", "slug")) or page_signal_id(source)
    slug = normalize_text(decision.get("slug")) or page_slug(source)
    entry: dict[str, Any] = {
        "signal_id": signal_id,
        "slug": slug,
        "title": normalize_text(first_present(source, "title", "public_title")),
        "decision": normalize_text(decision.get("decision")),
        "blockers": list(dict.fromkeys(blockers)),
        "required_next_actions": required_actions_for(blockers, normalize_text(decision.get("decision"))),
    }
    return entry


def approved_entry(page: dict[str, Any], decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "signal_id": page_signal_id(page),
        "title": normalize_text(page.get("title")),
        "slug": page_slug(page),
        "source_page_path": normalize_text(page.get("output_path")),
        "preview_path": normalize_text(page.get("preview_path")),
        "decision": normalize_text(decision.get("decision")),
        "approved_for_production_pack": True,
        "published": False,
        "production_publish_performed": False,
    }


def build_approval_report(
    manifest: dict[str, Any],
    approval_input: dict[str, Any],
    manifest_path: pathlib.Path,
    approval_input_path: pathlib.Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    pages_by_slug, pages_by_signal_id = index_pages(manifest)
    blocked_by_key = blocked_manifest_entries(manifest)
    owner = approval_input.get("owner")
    approved_at = normalize_text(approval_input.get("approved_at"))
    owner_blockers: list[str] = []
    if not owner_is_valid(owner):
        owner_blockers.append("missing_owner_identity")
    if not approved_at:
        owner_blockers.append("missing_approved_at")

    decisions = approval_input.get("decisions")
    if not isinstance(decisions, list):
        raise ApprovalInputError("Approval input must include a decisions list")

    approved: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for decision in decisions:
        if not isinstance(decision, dict):
            blocked.append(
                {
                    "signal_id": "",
                    "slug": "",
                    "title": "",
                    "decision": "",
                    "blockers": ["invalid_decision_record"],
                    "required_next_actions": ["provide_object_decision_records"],
                }
            )
            continue

        blockers = list(owner_blockers)
        decision_value = normalize_text(decision.get("decision"))
        if not decision_value:
            blockers.append("missing_approval_decision")
        elif decision_value not in ALLOWED_DECISIONS:
            blockers.append("unsupported_decision")
        elif decision_value != APPROVE_DECISION:
            blockers.append("decision_not_approve_for_production_pack")

        page = lookup_page(decision, pages_by_slug, pages_by_signal_id)
        manifest_blocked = blocked_by_key.get(decision_key(decision))
        if page is None:
            if manifest_blocked is not None:
                blockers.append("signal_was_blocked_by_generator")
            else:
                blockers.append("page_not_found_in_generator_manifest")
        else:
            blockers.extend(page_blockers(page, manifest))

        if blockers:
            blocked.append(blocked_entry(decision, page, blockers, manifest_blocked))
        else:
            approved.append(approved_entry(page, decision))

    return {
        "approval_version": APPROVAL_VERSION,
        "created_at": created_at or utc_now(),
        "input_files": {
            "manifest": str(manifest_path),
            "approval_input": str(approval_input_path),
        },
        "owner": owner if isinstance(owner, dict) else {},
        "approved_at": approved_at,
        "pages_seen": len(as_list(manifest.get("pages"))),
        "pages_approved": len(approved),
        "pages_blocked": len(blocked),
        "approved": approved,
        "blocked": blocked,
        "manual_publish_approval_completed": True,
        "no_public_publishing_performed": True,
        "no_deployment_performed": True,
        "no_openai_call_performed": True,
        "no_workflow_dispatch_performed": True,
        "production_publish_performed": False,
        "production_pack_required": True,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create DysonX Manual Publish Approval V1 report.")
    parser.add_argument("--manifest", required=True, help="Public Signal Page Generator manifest JSON input.")
    parser.add_argument("--approval-input", required=True, help="Owner manual approval input JSON.")
    parser.add_argument("--output", required=True, help="Output approval report JSON path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = pathlib.Path(args.manifest)
    approval_input_path = pathlib.Path(args.approval_input)
    output_path = pathlib.Path(args.output)
    try:
        manifest = read_json_object(manifest_path, "Public Signal Page Generator manifest")
        approval_input = read_json_object(approval_input_path, "Manual publish approval input")
        report = build_approval_report(manifest, approval_input, manifest_path, approval_input_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except ApprovalInputError as exc:
        print(f"[manual-publish-approval] failed: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[manual-publish-approval] failed: {exc}", file=sys.stderr)
        return 2
    print(
        "[manual-publish-approval] wrote approval report: "
        f"{output_path} pages_approved={report['pages_approved']} pages_blocked={report['pages_blocked']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
