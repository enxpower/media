#!/usr/bin/env python3
"""DysonX Public Signal Page Generator V1.

Generates static draft preview pages from Publish Readiness Gate-approved
Signals. This tool is offline, deterministic, and standard-library only. It
does not publish, deploy, call OpenAI, dispatch workflows, fetch URLs, scrape
sources, write production public pages, or approve publication.
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


GENERATOR_VERSION = "public_signal_page_generator_v1"
DEFAULT_OUTPUT_DIR = pathlib.Path("tmp/public_signal_pages")
RAW_CONTENT_FIELDS = (
    "raw_body",
    "article_body",
    "scraped_text",
    "full_text",
    "provider_response",
    "raw_provider_response",
    "raw_copyrighted_article_text",
)


class GeneratorInputError(ValueError):
    """Raised when the generator cannot safely process input."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json_object(path: str | pathlib.Path, label: str) -> dict[str, Any]:
    input_path = pathlib.Path(path)
    try:
        data = json.loads(input_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - CLI fails closed on malformed JSON.
        raise GeneratorInputError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise GeneratorInputError(f"{label} must be a JSON object")
    return data


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def first_present(record: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = record.get(key)
        if value not in (None, "", []):
            return value
    return None


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled-signal"


def signal_id(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "signal_id", "canonical_signal_id", "id"))


def signal_title(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "public_title", "title")) or "Untitled Signal"


def signal_slug(record: dict[str, Any]) -> str:
    return slugify(normalize_text(first_present(record, "public_slug", "slug", "signal_slug", "title")))


def source_urls(record: dict[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("source_url", "first_source_url", "original_source_url"):
        value = normalize_text(record.get(key))
        if value and value not in values:
            values.append(value)
    for value in as_list(record.get("source_urls")):
        text = normalize_text(value)
        if text and text not in values:
            values.append(text)
    return values


def source_label(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "public_source_label", "source_title", "source_reference")) or "Source attribution provided"


def source_attribution(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "public_attribution", "source_attribution", "source_authority_reasoning", "source_authority")) or source_label(record)


def quality_summary(record: dict[str, Any]) -> str:
    score = first_present(record, "score_normalized_to_65", "quality_score_total", "score", "total_score")
    tier = normalize_text(first_present(record, "quality_tier", "tier"))
    confidence = normalize_text(first_present(record, "confidence_summary", "confidence_notes", "confidence"))
    pieces = []
    if score not in (None, ""):
        pieces.append(f"Quality score: {score}/65")
    if tier:
        pieces.append(f"Tier: {tier}")
    if confidence:
        pieces.append(f"Confidence: {confidence}")
    return "; ".join(pieces) if pieces else "Quality score and confidence summary available in gate inputs."


def risk_summary(record: dict[str, Any]) -> str:
    risks = [normalize_text(item) for item in as_list(record.get("warnings")) if normalize_text(item)]
    risks.extend(normalize_text(item) for item in as_list(record.get("risk_flags")) if normalize_text(item))
    if risks:
        return "; ".join(dict.fromkeys(risks))
    return "No blocking public-generation risk flags in the gate-passed record."


def public_summary(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "public_summary", "summary")) or "No public summary provided."


def why_it_matters(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "public_why_it_matters", "why_it_matters")) or "No public why-it-matters field provided."


def watch_next(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "public_watch_next", "watch_next")) or "No public watch-next field provided."


def agi_relevance(record: dict[str, Any]) -> str:
    return normalize_text(first_present(record, "public_capability_area", "specific_agi_capability", "agi_capability_affected", "agi_capability")) or "AGI capability relevance provided by gate input."


def has_raw_content(record: dict[str, Any]) -> bool:
    return any(record.get(field) for field in RAW_CONTENT_FIELDS)


def is_ready_for_generation(record: dict[str, Any]) -> bool:
    return (
        record.get("publish_readiness_gate_passed") is True
        and record.get("ready_for_public_generation") is True
        and record.get("public_generation_blocked") is False
        and record.get("published") is not True
        and record.get("publication_approved") is not True
        and not has_raw_content(record)
    )


def block_reasons(record: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if record.get("publish_readiness_gate_passed") is not True:
        reasons.append("publish_readiness_gate_not_passed")
    if record.get("ready_for_public_generation") is not True:
        reasons.append("not_ready_for_public_generation")
    if record.get("public_generation_blocked") is not False:
        reasons.append("public_generation_blocked")
    if record.get("published") is True:
        reasons.append("already_published_true")
    if record.get("publication_approved") is True:
        reasons.append("publication_approved_true_requires_later_manual_approval_step")
    if has_raw_content(record):
        reasons.append("raw_source_content_present")
    for blocker in as_list(record.get("blockers")) + as_list(record.get("public_generation_blockers")):
        text = normalize_text(blocker)
        if text:
            reasons.append(text)
    return list(dict.fromkeys(reasons)) or ["insufficient_gate_fields"]


def safe_output_root(output_dir: pathlib.Path) -> pathlib.Path:
    normalized = pathlib.Path(output_dir)
    if normalized.is_absolute():
        if not any(part == "tmp" or part.startswith("tmp") for part in normalized.parts):
            raise GeneratorInputError("Absolute output directory must be under a temporary preview path")
        return normalized
    if not normalized.parts or normalized.parts[0] != "tmp":
        raise GeneratorInputError("Output directory must be under tmp/ for draft preview generation")
    return normalized


def render_layout(title: str, body: str, generated_at: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex,nofollow">
  <title>{escape(title)} | DysonX Draft Preview</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #5f6f80;
      --line: #d8dee6;
      --panel: #f6f8fa;
      --accent: #0f6f8f;
      --warn: #8a4b00;
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: #ffffff;
      line-height: 1.55;
    }}
    main {{
      max-width: 920px;
      margin: 0 auto;
      padding: 28px 20px 48px;
    }}
    .status {{
      display: inline-block;
      margin-bottom: 16px;
      padding: 5px 9px;
      border: 1px solid #e6c36a;
      background: #fff7dc;
      color: var(--warn);
      font-weight: 700;
      font-size: 0.85rem;
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: 2rem;
      line-height: 1.18;
      letter-spacing: 0;
    }}
    h2 {{
      margin-top: 28px;
      padding-top: 18px;
      border-top: 1px solid var(--line);
      font-size: 1.1rem;
      letter-spacing: 0;
    }}
    p, li {{
      max-width: 76ch;
    }}
    a {{
      color: var(--accent);
    }}
    .meta, .notice {{
      background: var(--panel);
      border: 1px solid var(--line);
      padding: 14px;
    }}
    .notice {{
      border-left: 4px solid #e6c36a;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }}
    .card {{
      border: 1px solid var(--line);
      padding: 14px;
      background: #fff;
    }}
    .muted {{
      color: var(--muted);
    }}
    code {{
      background: var(--panel);
      padding: 1px 4px;
    }}
  </style>
</head>
<body>
<main>
{body}
<p class="muted">Generated at {escape(generated_at)}. Static local draft preview only.</p>
</main>
</body>
</html>
"""


def render_signal_page(record: dict[str, Any], generated_at: str) -> str:
    title = signal_title(record)
    slug = signal_slug(record)
    source_links = source_urls(record)
    sources_html = "".join(
        f'<li><a href="{escape(url, quote=True)}" rel="nofollow noopener">{escape(url)}</a></li>'
        for url in source_links
    ) or "<li>No public source URL provided in this draft record.</li>"
    body = f"""
<p class="status">Draft Preview / Not Published</p>
<h1>{escape(title)}</h1>
<div class="notice">
  <strong>Manual Publish Approval V1 is required before production release.</strong>
  This generated page is a local static draft. It is not published, not production-approved, and not deployed.
</div>
<div class="meta grid">
  <div><strong>Slug</strong><br><code>{escape(slug)}</code></div>
  <div><strong>Status</strong><br>Draft Preview / Not Published</div>
  <div><strong>Gate</strong><br>Publish Readiness Gate passed for future public generation only</div>
</div>
<h2>Summary</h2>
<p>{escape(public_summary(record))}</p>
<h2>Why This Matters</h2>
<p>{escape(why_it_matters(record))}</p>
<h2>AGI Relevance</h2>
<p>{escape(agi_relevance(record))}</p>
<h2>Source Attribution</h2>
<p>{escape(source_attribution(record))}</p>
<ul>{sources_html}</ul>
<h2>Quality And Confidence</h2>
<p>{escape(quality_summary(record))}</p>
<h2>Risk And Safety Notes</h2>
<p>{escape(risk_summary(record))}</p>
<h2>Watch Next</h2>
<p>{escape(watch_next(record))}</p>
<p><a href="/signals/">Back to Public Signals Draft Preview</a></p>
"""
    return render_layout(title, body, generated_at)


def render_index_page(pages: list[dict[str, Any]], blocked: list[dict[str, Any]], generated_at: str) -> str:
    items = []
    for page in pages:
        item = page["record"]
        href = f"/signals/{escape(page['slug'], quote=True)}/"
        items.append(
            f"""
<article class="card">
  <h2><a href="{href}">{escape(page['title'])}</a></h2>
  <p>{escape(public_summary(item))}</p>
  <p><strong>AGI relevance:</strong> {escape(agi_relevance(item))}</p>
  <p><strong>Quality / confidence:</strong> {escape(quality_summary(item))}</p>
  <p><strong>Sources:</strong> {len(source_urls(item))} source URL(s); {escape(source_label(item))}</p>
  <p><a href="{href}">Open draft preview</a></p>
</article>
"""
        )
    list_html = "\n".join(items) if items else "<p>No Signals were generated.</p>"
    body = f"""
<p class="status">Draft Preview / Not Published</p>
<h1>DysonX Public Signals Draft Preview</h1>
<div class="notice">
  <strong>Manual Publish Approval V1 is required before production release.</strong>
  These pages are local preview drafts only. They are not published and not deployed.
</div>
<div class="meta grid">
  <div><strong>Generated Signals</strong><br>{len(pages)}</div>
  <div><strong>Blocked Signals</strong><br>{len(blocked)}</div>
  <div><strong>Status</strong><br>Draft Preview / Not Published</div>
</div>
{list_html}
"""
    return render_layout("DysonX Public Signals Draft Preview", body, generated_at)


def write_text(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def build_manifest(
    gate_report_path: pathlib.Path,
    output_dir: pathlib.Path,
    pages: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
    signals_seen: int,
    created_at: str,
) -> dict[str, Any]:
    manifest_pages = []
    for page in pages:
        record = page["record"]
        manifest_pages.append(
            {
                "signal_id": signal_id(record),
                "title": page["title"],
                "slug": page["slug"],
                "output_path": str(page["output_path"]),
                "preview_path": page["preview_path"],
                "ready_for_public_generation": record.get("ready_for_public_generation") is True,
                "publish_readiness_gate_passed": record.get("publish_readiness_gate_passed") is True,
                "publication_approved": bool(record.get("publication_approved")),
                "published": bool(record.get("published")),
            }
        )
    return {
        "generator_version": GENERATOR_VERSION,
        "created_at": created_at,
        "input_files": {"gate_report": str(gate_report_path)},
        "output_directory": str(output_dir),
        "signals_seen": signals_seen,
        "signals_generated": len(pages),
        "signals_blocked": len(blocked),
        "pages": manifest_pages,
        "blocked": blocked,
        "no_public_publishing_performed": True,
        "no_deployment_performed": True,
        "no_openai_call_performed": True,
        "no_workflow_dispatch_performed": True,
        "manual_publish_approval_required": True,
        "production_publish_performed": False,
    }


def generate_pages(gate_report: dict[str, Any], gate_report_path: pathlib.Path, output_dir: pathlib.Path) -> dict[str, Any]:
    evaluations = gate_report.get("evaluations")
    if not isinstance(evaluations, list):
        raise GeneratorInputError("Gate report must include an evaluations list")

    safe_root = safe_output_root(output_dir)
    if safe_root.exists():
        shutil.rmtree(safe_root)
    signals_dir = safe_root / "signals"
    created_at = utc_now()
    pages: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for item in evaluations:
        if not isinstance(item, dict):
            blocked.append({"signal_id": "", "title": "", "blockers": ["invalid_evaluation_record"], "required_next_actions": ["provide_object_evaluation_records"]})
            continue
        title = signal_title(item)
        slug = signal_slug(item)
        if is_ready_for_generation(item):
            output_path = signals_dir / slug / "index.html"
            write_text(output_path, render_signal_page(item, created_at))
            pages.append(
                {
                    "record": item,
                    "title": title,
                    "slug": slug,
                    "output_path": output_path,
                    "preview_path": f"signals/{slug}/",
                }
            )
        else:
            blocked.append(
                {
                    "signal_id": signal_id(item),
                    "slug": slug,
                    "title": title,
                    "blockers": block_reasons(item),
                    "required_next_actions": [normalize_text(action) for action in as_list(item.get("required_next_actions")) if normalize_text(action)],
                }
            )

    write_text(signals_dir / "index.html", render_index_page(pages, blocked, created_at))
    manifest = build_manifest(gate_report_path, safe_root, pages, blocked, len(evaluations), created_at)
    write_text(safe_root / "public_signal_pages_manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    readme = """# DysonX Public Signal Pages Draft Preview

This directory contains local static draft preview artifacts only.

Run:

```bash
python3 -m http.server --directory tmp/public_signal_pages 8080
```

Then visit:

```text
http://localhost:8080/signals/
```

Manual Publish Approval V1 is still required before production release.
No production deployment was performed.
"""
    write_text(safe_root / "README.md", readme)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate DysonX public Signal draft preview pages.")
    parser.add_argument("--gate-report", required=True, help="Publish Readiness Gate report JSON input.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Safe tmp/ output directory for draft pages.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    gate_report_path = pathlib.Path(args.gate_report)
    output_dir = pathlib.Path(args.output_dir)
    try:
        gate_report = read_json_object(gate_report_path, "Publish Readiness Gate report")
        manifest = generate_pages(gate_report, gate_report_path, output_dir)
    except GeneratorInputError as exc:
        print(f"[public-signal-page-generator] failed: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[public-signal-page-generator] failed: {exc}", file=sys.stderr)
        return 2
    print(
        "[public-signal-page-generator] wrote draft preview: "
        f"{manifest['output_directory']} signals_generated={manifest['signals_generated']} "
        f"signals_blocked={manifest['signals_blocked']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
