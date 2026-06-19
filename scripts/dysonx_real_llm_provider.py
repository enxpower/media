#!/usr/bin/env python3
"""DysonX Real LLM Provider Gated V1.

Processes existing SignalCandidate reports into validated IntelligenceSignal
records through a fake provider by default or a tightly gated OpenAI adapter.
The CLI never publishes, writes website pages, posts to social platforms,
mutates Notion, calls GitHub, scrapes article bodies, or deploys.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import pathlib
from datetime import datetime, timezone
from typing import Any


PROMPT_VERSION = "real_llm_provider_gated_v1"
DEFAULT_FAKE_MODEL = "fake-dysonx-real-provider-gated-v1"
DEFAULT_OPENAI_MODEL = "gpt-5.5-mini"
MAX_ALLOWED_ITEMS = 5
OPENAI_HOST = "api.openai.com"
OPENAI_PATH = "/v1/responses"

REQUIRED_INTELLIGENCE_FIELDS = (
    "title",
    "summary",
    "why_it_matters",
    "agi_capability",
    "related_entities",
    "confidence",
    "watch_next",
    "source_url",
)

SAFETY_FLAGS = {
    "publishing_performed": False,
    "website_pages_written": False,
    "public_content_files_written": False,
    "social_posting_performed": False,
    "deployment_performed": False,
    "notion_write_operations_performed": False,
    "live_github_api_used": False,
    "article_body_scraping_performed": False,
    "raw_provider_response_stored": False,
}


class ProviderGateError(RuntimeError):
    """Raised when the real provider gate is not explicitly satisfied."""


class ProviderResponseError(RuntimeError):
    """Raised when a provider response cannot be parsed safely."""


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:16]}"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_signal_candidates(path: str | pathlib.Path) -> list[dict[str, Any]]:
    report_path = pathlib.Path(path)
    if not report_path.exists() and report_path.name == "signal_candidates_report.json":
        singular_path = report_path.with_name("signal_candidate_report.json")
        if singular_path.exists():
            report_path = singular_path
    data = json.loads(report_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("SignalCandidate report must be a JSON object")
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not all(isinstance(candidate, dict) for candidate in candidates):
        raise ValueError("SignalCandidate report must contain a candidates list")
    return candidates


def validate_max_items(value: int | None) -> int | None:
    if value is None:
        return None
    if value <= 0:
        raise ValueError("--max-items must be a positive integer")
    if value > MAX_ALLOWED_ITEMS:
        raise ValueError(f"--max-items must be no greater than {MAX_ALLOWED_ITEMS}")
    return value


def enforce_provider_gate(provider: str, allow_real_llm: bool, api_key: str | None, max_items: int | None) -> None:
    if provider == "fake":
        return
    if provider != "openai":
        raise ProviderGateError(f"Unsupported provider: {provider}")
    if not allow_real_llm:
        raise ProviderGateError("OpenAI provider requires --allow-real-llm")
    if not api_key:
        raise ProviderGateError("OpenAI provider requires OPENAI_API_KEY")
    if max_items is None:
        raise ProviderGateError("OpenAI provider requires --max-items")
    validate_max_items(max_items)


def normalize_text(value: Any) -> str:
    return str(value or "").strip()


def candidate_source_url(candidate: dict[str, Any]) -> str:
    return normalize_text(candidate.get("url") or candidate.get("source_url"))


def build_prompt(candidate: dict[str, Any]) -> str:
    compact_candidate = {
        "candidate_id": candidate.get("candidate_id"),
        "title": candidate.get("title"),
        "source_name": candidate.get("source_name"),
        "source_url": candidate_source_url(candidate),
        "candidate_type": candidate.get("candidate_type"),
        "entities": candidate.get("entities") or [],
        "tags": candidate.get("tags") or [],
        "confidence": candidate.get("confidence"),
    }
    return (
        "You are DysonX, an AI / AGI intelligence system. "
        "Transform the SignalCandidate into one concise IntelligenceSignal. "
        "Return only strict JSON with these fields: title, summary, why_it_matters, "
        "agi_capability, related_entities, confidence, watch_next, source_url. "
        "Do not write an article. Do not publish. Candidate JSON: "
        f"{json.dumps(compact_candidate, sort_keys=True)}"
    )


def intelligence_schema() -> dict[str, Any]:
    properties = {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "agi_capability": {"type": "string"},
        "related_entities": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
        "watch_next": {"type": "string"},
        "source_url": {"type": "string"},
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(REQUIRED_INTELLIGENCE_FIELDS),
        "properties": properties,
    }


def fake_provider_response(candidate: dict[str, Any]) -> dict[str, Any]:
    entities = candidate.get("entities") or []
    tags = candidate.get("tags") or []
    title = normalize_text(candidate.get("title")) or "Untitled SignalCandidate"
    capability = "Agents"
    if "policy" in tags or candidate.get("candidate_type") == "regulation":
        capability = "Policy"
    elif "research" in tags:
        capability = "Evaluation"
    elif "model" in tags:
        capability = "Reasoning"

    return {
        "title": title,
        "summary": f"{title} is a candidate DysonX signal from {normalize_text(candidate.get('source_name'))}.",
        "why_it_matters": "It may affect AI / AGI capability tracking and should be reviewed before publication.",
        "agi_capability": capability,
        "related_entities": [str(entity) for entity in entities],
        "confidence": min(1.0, max(0.0, float(candidate.get("confidence") or 0.5))),
        "watch_next": "Verify the original source and compare with related signals.",
        "source_url": candidate_source_url(candidate),
    }


def extract_response_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return str(response["output_text"])
    output = response.get("output")
    if isinstance(output, list):
        chunks: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
        if chunks:
            return "\n".join(chunks)
    raise ProviderResponseError("OpenAI response did not include text output")


def parse_provider_json(text: str) -> dict[str, Any]:
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ProviderResponseError("Provider output must be a JSON object")
    return data


def call_openai_provider(
    candidate: dict[str, Any],
    api_key: str,
    model: str = DEFAULT_OPENAI_MODEL,
    timeout: int = 30,
) -> tuple[dict[str, Any], dict[str, int]]:
    payload = {
        "model": model,
        "input": build_prompt(candidate),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "dysonx_intelligence_signal",
                "schema": intelligence_schema(),
                "strict": True,
            }
        },
    }
    body = json.dumps(payload).encode("utf-8")
    connection = http.client.HTTPSConnection(OPENAI_HOST, timeout=timeout)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        connection.request("POST", OPENAI_PATH, body=body, headers=headers)
        response = connection.getresponse()
        response_body = response.read().decode("utf-8")
    finally:
        connection.close()

    if response.status >= 400:
        raise ProviderResponseError(f"OpenAI request failed with status {response.status}")
    response_json = json.loads(response_body)
    if not isinstance(response_json, dict):
        raise ProviderResponseError("OpenAI response must be a JSON object")
    output = parse_provider_json(extract_response_text(response_json))
    usage = response_json.get("usage")
    token_usage: dict[str, int] = {}
    if isinstance(usage, dict):
        for key in ("input_tokens", "output_tokens", "total_tokens"):
            if isinstance(usage.get(key), int):
                token_usage[key] = usage[key]
    return output, token_usage


def validate_intelligence_signal(output: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    for field_name in REQUIRED_INTELLIGENCE_FIELDS:
        if field_name not in output:
            errors.append(f"{field_name} is required")

    for field_name in ("title", "summary", "why_it_matters", "agi_capability", "watch_next", "source_url"):
        if field_name in output and not normalize_text(output.get(field_name)):
            errors.append(f"{field_name} must be a non-empty string")

    if "related_entities" in output and not isinstance(output.get("related_entities"), list):
        errors.append("related_entities must be a list")
    elif isinstance(output.get("related_entities"), list):
        if not all(isinstance(entity, str) for entity in output["related_entities"]):
            errors.append("related_entities must contain only strings")

    confidence = output.get("confidence")
    if not isinstance(confidence, int | float) or confidence < 0 or confidence > 1:
        errors.append("confidence must be a number from 0 to 1")

    return len(errors) == 0, errors


def create_job(candidate: dict[str, Any], provider: str, model: str, created_at: str) -> dict[str, Any]:
    candidate_id = normalize_text(candidate.get("candidate_id"))
    return {
        "job_id": stable_id("llm_job", candidate_id, provider, PROMPT_VERSION),
        "candidate_id": candidate_id,
        "provider": provider,
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "status": "created",
        "created_at": created_at,
    }


def create_signal(candidate: dict[str, Any], output: dict[str, Any], provider: str, created_at: str) -> dict[str, Any]:
    candidate_id = normalize_text(candidate.get("candidate_id"))
    return {
        "signal_id": stable_id("intelligence_signal", candidate_id, normalize_text(output.get("source_url"))),
        "candidate_id": candidate_id,
        "provider": provider,
        "prompt_version": PROMPT_VERSION,
        "title": normalize_text(output["title"]),
        "summary": normalize_text(output["summary"]),
        "why_it_matters": normalize_text(output["why_it_matters"]),
        "agi_capability": normalize_text(output["agi_capability"]),
        "related_entities": [str(entity) for entity in output["related_entities"]],
        "confidence": float(output["confidence"]),
        "watch_next": normalize_text(output["watch_next"]),
        "source_url": normalize_text(output["source_url"]),
        "created_at": created_at,
    }


def run_provider(
    signal_candidate_report_path: str | pathlib.Path,
    provider: str = "fake",
    allow_real_llm: bool = False,
    max_items: int | None = None,
    output_path: str | pathlib.Path | None = None,
    api_key: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    validate_max_items(max_items)
    api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY")
    enforce_provider_gate(provider, allow_real_llm, api_key, max_items)

    timestamp = created_at or utc_now()
    candidates = load_signal_candidates(signal_candidate_report_path)
    requested = len(candidates) if max_items is None else min(len(candidates), max_items)
    selected_candidates = candidates[:requested]
    model = DEFAULT_OPENAI_MODEL if provider == "openai" else DEFAULT_FAKE_MODEL

    jobs: list[dict[str, Any]] = []
    validations: list[dict[str, Any]] = []
    audit_records: list[dict[str, Any]] = []
    signals: list[dict[str, Any]] = []
    estimated_token_usage: dict[str, int] = {}

    for candidate in selected_candidates:
        job = create_job(candidate, provider, model, timestamp)
        jobs.append(job)
        output: dict[str, Any]
        token_usage: dict[str, int] = {}
        try:
            if provider == "openai":
                output, token_usage = call_openai_provider(candidate, api_key or "", model=model)
            else:
                output = fake_provider_response(candidate)
        except Exception as exc:  # noqa: BLE001 - audit needs failure reason without leaking secrets.
            validation = {
                "validation_id": stable_id("validation", job["job_id"]),
                "job_id": job["job_id"],
                "candidate_id": job["candidate_id"],
                "passed": False,
                "errors": [str(exc)],
            }
            validations.append(validation)
            audit_records.append(
                {
                    "audit_id": stable_id("audit", job["job_id"], validation["validation_id"]),
                    "job_id": job["job_id"],
                    "validation_id": validation["validation_id"],
                    "provider": provider,
                    "raw_provider_response_stored": False,
                    "created_at": timestamp,
                }
            )
            continue

        passed, errors = validate_intelligence_signal(output)
        validation = {
            "validation_id": stable_id("validation", job["job_id"]),
            "job_id": job["job_id"],
            "candidate_id": job["candidate_id"],
            "passed": passed,
            "errors": errors,
            "required_fields": list(REQUIRED_INTELLIGENCE_FIELDS),
        }
        validations.append(validation)
        audit_records.append(
            {
                "audit_id": stable_id("audit", job["job_id"], validation["validation_id"]),
                "job_id": job["job_id"],
                "validation_id": validation["validation_id"],
                "provider": provider,
                "raw_provider_response_stored": False,
                "created_at": timestamp,
            }
        )
        for key, value in token_usage.items():
            estimated_token_usage[key] = estimated_token_usage.get(key, 0) + value
        if passed:
            signals.append(create_signal(candidate, output, provider, timestamp))

    real_llm_used = provider == "openai"
    report = {
        "generated_at": timestamp,
        "provider": provider,
        "model": model,
        "prompt_version": PROMPT_VERSION,
        "items_requested": requested,
        "items_processed": len(selected_candidates),
        "items_skipped": max(0, len(candidates) - len(selected_candidates)),
        "jobs_created": len(jobs),
        "validations_passed": sum(1 for validation in validations if validation["passed"]),
        "validations_failed": sum(1 for validation in validations if not validation["passed"]),
        "intelligence_signals_created": len(signals),
        "estimated_token_usage": estimated_token_usage,
        "jobs": jobs,
        "validations": validations,
        "audit_records": audit_records,
        "intelligence_signals": signals,
        "real_llm_api_used": real_llm_used,
        "llm_api_calls_performed": real_llm_used,
        **SAFETY_FLAGS,
    }
    if output_path is not None:
        write_report(report, output_path)
    return report


def write_report(report: dict[str, Any], output_path: str | pathlib.Path) -> None:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX Real LLM Provider Gated V1.")
    parser.add_argument("--signal-candidates", required=True, help="Path to SignalCandidate report JSON.")
    parser.add_argument("--provider", choices=("fake", "openai"), default="fake", help="Provider to use.")
    parser.add_argument("--allow-real-llm", action="store_true", help="Required to allow OpenAI provider calls.")
    parser.add_argument("--max-items", type=int, help="Small positive maximum item count for provider execution.")
    parser.add_argument("--output", required=True, help="Path to write LLM provider audit report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = run_provider(
            args.signal_candidates,
            provider=args.provider,
            allow_real_llm=args.allow_real_llm,
            max_items=args.max_items,
            output_path=args.output,
        )
    except ProviderGateError as exc:
        print(f"[real-llm-provider] provider gate blocked run: {exc}")
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI should fail closed with concise non-secret error.
        print(f"[real-llm-provider] failed: {exc}")
        return 1

    print(
        "[real-llm-provider] wrote report: "
        f"{args.output} provider={report['provider']} "
        f"items_processed={report['items_processed']} "
        f"signals={report['intelligence_signals_created']} "
        f"real_llm_api_used={report['real_llm_api_used']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
