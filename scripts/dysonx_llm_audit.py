#!/usr/bin/env python3
"""DysonX LLM Job & Audit Foundation V1.

Runs SignalCandidate records through a provider-neutral fake model execution
chain, validates structured output, creates IntelligenceSignal records, and
writes an audit report. V1 performs no real provider calls, network requests,
publishing, social posting, graph writes, or prediction work.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from dataclasses import asdict
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from dysonx_intelligence_signal import IntelligenceSignalV1
from dysonx_llm_intelligence_layer import (
    FakeLLMProvider,
    candidate_from_record,
    signal_id_for_candidate,
)
from dysonx_llm_job import AuditRecordV1, LLMJobV1, ModelRunV1, OutputValidationV1
from dysonx_output_validation import VALIDATION_RULES, validate_intelligence_output
from dysonx_prompt_registry import PromptTemplateV1, get_prompt_template
import dysonx_signal_candidate_pipeline as candidate_pipeline


FAKE_PROVIDER_NAME = "fake"
FAKE_MODEL_NAME = "fake-dysonx-intelligence-v1"
DEFAULT_PROMPT_TEMPLATE_ID = "intelligence_signal_extraction"
DEFAULT_PROMPT_TEMPLATE_VERSION = "v1"


def stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{digest[:16]}"


def create_llm_job(candidate_id: str, prompt_template: PromptTemplateV1, created_at: str) -> LLMJobV1:
    return LLMJobV1(
        job_id=stable_id("llm_job", candidate_id, prompt_template.template_version),
        candidate_id=candidate_id,
        provider=FAKE_PROVIDER_NAME,
        model=FAKE_MODEL_NAME,
        prompt_template_version=prompt_template.template_version,
        status="created",
        created_at=created_at,
    )


def estimate_token_counts(prompt_template: PromptTemplateV1, output: dict[str, Any]) -> dict[str, int]:
    prompt_tokens = len(prompt_template.template_text.split())
    completion_tokens = len(json.dumps(output, sort_keys=True).split())
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


def execute_fake_model_run(
    job: LLMJobV1,
    candidate_record: dict[str, Any],
    prompt_template: PromptTemplateV1,
    provider: FakeLLMProvider | None = None,
) -> tuple[ModelRunV1, dict[str, Any]]:
    candidate = candidate_from_record(candidate_record)
    fake_provider = provider or FakeLLMProvider()
    start = perf_counter()
    output = fake_provider.analyze_candidate(candidate)
    latency_ms = max(0, int((perf_counter() - start) * 1000))
    run = ModelRunV1(
        run_id=stable_id("model_run", job.job_id, candidate.candidate_id),
        job_id=job.job_id,
        provider=fake_provider.provider_name,
        model=job.model,
        latency_ms=latency_ms,
        token_counts=estimate_token_counts(prompt_template, output),
        status="completed",
    )
    return run, output


def validate_model_output(run_id: str, output: dict[str, Any]) -> OutputValidationV1:
    passed, warnings = validate_intelligence_output(output)
    return OutputValidationV1(
        validation_id=stable_id("validation", run_id),
        run_id=run_id,
        passed=passed,
        warnings=warnings,
        validation_rules=VALIDATION_RULES,
    )


def create_audit_record(job_id: str, run_id: str, validation_id: str, created_at: str) -> AuditRecordV1:
    return AuditRecordV1(
        audit_id=stable_id("audit", job_id, run_id, validation_id),
        job_id=job_id,
        run_id=run_id,
        validation_id=validation_id,
        created_at=created_at,
    )


def create_signal_from_valid_output(
    candidate_record: dict[str, Any],
    output: dict[str, Any],
    created_at: str,
) -> IntelligenceSignalV1:
    candidate = candidate_from_record(candidate_record)
    return IntelligenceSignalV1(
        signal_id=signal_id_for_candidate(candidate),
        title=str(output["title"]),
        source_id=candidate.source_id,
        source_name=candidate.source_name,
        signal_type=str(output["signal_type"]),
        importance=str(output["importance"]),
        confidence=float(output["confidence"]),
        summary=str(output["summary"]),
        key_points=tuple(str(point) for point in output["key_points"]),
        affected_entities=tuple(str(entity) for entity in output["affected_entities"]),
        impact_horizon=str(output["impact_horizon"]),
        tags=tuple(str(tag) for tag in output["tags"]),
        created_at=created_at,
    )


def serialize_dataclass(value: Any) -> dict[str, Any]:
    data = asdict(value)
    for key, item in list(data.items()):
        if isinstance(item, tuple):
            data[key] = list(item)
    return data


def run_llm_audit(
    candidate_records: list[dict[str, Any]],
    created_at: str | None = None,
    prompt_template_id: str = DEFAULT_PROMPT_TEMPLATE_ID,
    prompt_template_version: str = DEFAULT_PROMPT_TEMPLATE_VERSION,
) -> dict[str, Any]:
    timestamp = created_at or datetime.now(timezone.utc).isoformat()
    prompt_template = get_prompt_template(prompt_template_id, prompt_template_version)

    jobs: list[LLMJobV1] = []
    runs: list[ModelRunV1] = []
    validations: list[OutputValidationV1] = []
    audit_records: list[AuditRecordV1] = []
    signals: list[IntelligenceSignalV1] = []

    for candidate_record in candidate_records:
        candidate_id = str(candidate_record["candidate_id"])
        job = create_llm_job(candidate_id, prompt_template, timestamp)
        run, output = execute_fake_model_run(job, candidate_record, prompt_template)
        validation = validate_model_output(run.run_id, output)
        audit_record = create_audit_record(job.job_id, run.run_id, validation.validation_id, timestamp)

        jobs.append(job)
        runs.append(run)
        validations.append(validation)
        audit_records.append(audit_record)
        if validation.passed:
            signals.append(create_signal_from_valid_output(candidate_record, output, timestamp))

    provider_distribution: dict[str, int] = {}
    prompt_versions_used: dict[str, int] = {}
    for job in jobs:
        provider_distribution[job.provider] = provider_distribution.get(job.provider, 0) + 1
        prompt_versions_used[job.prompt_template_version] = prompt_versions_used.get(job.prompt_template_version, 0) + 1

    return {
        "generated_at": timestamp,
        "jobs_created": len(jobs),
        "runs_completed": sum(1 for run in runs if run.status == "completed"),
        "validations_passed": sum(1 for validation in validations if validation.passed),
        "validations_failed": sum(1 for validation in validations if not validation.passed),
        "signals_generated": len(signals),
        "provider_distribution": provider_distribution,
        "prompt_versions_used": prompt_versions_used,
        "prompt_template": serialize_dataclass(prompt_template),
        "jobs": [serialize_dataclass(job) for job in jobs],
        "runs": [serialize_dataclass(run) for run in runs],
        "validations": [serialize_dataclass(validation) for validation in validations],
        "audit_records": [serialize_dataclass(record) for record in audit_records],
        "signals": [serialize_dataclass(signal) for signal in signals],
        "real_llm_api_used": False,
        "network_requests_performed": False,
        "publishing_performed": False,
    }


def load_candidate_records_from_raw_fixture(path: str | pathlib.Path) -> list[dict[str, Any]]:
    records = candidate_pipeline.load_raw_item_records(path)
    candidate_report = candidate_pipeline.run_pipeline(records)
    return list(candidate_report["candidates"])


def write_report(report: dict[str, Any], output_path: str | pathlib.Path) -> None:
    path = pathlib.Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run DysonX LLM Job & Audit Foundation V1.")
    parser.add_argument("--raw-fixture", required=True, help="Path to RawItem fixture JSON.")
    parser.add_argument("--output", required=True, help="Path to write LLM audit report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    candidate_records = load_candidate_records_from_raw_fixture(args.raw_fixture)
    report = run_llm_audit(candidate_records)
    write_report(report, args.output)
    print(
        "[llm-audit] wrote report: "
        f"{args.output} jobs={report['jobs_created']} "
        f"validations_passed={report['validations_passed']} signals={report['signals_generated']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
