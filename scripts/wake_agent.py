#!/usr/bin/env python3
"""Single-agent WAKE investigation loop with deterministic tools and verification."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

import jsonschema

from run_baseline import (
    current_git_commit,
    estimate_cost_usd,
    normalize_usage,
    object_value,
    read_json,
    selected_summaries,
    sha256_json,
    sha256_path,
    utc_now,
    write_json,
)
from wake_tools import TOOL_DEFINITIONS, execute_tool, tool_definitions


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/wake-agent-v1.json"
DEFAULT_INPUTS = ROOT / "evaluation/baseline-inputs/v1"
DEFAULT_PROMPT = ROOT / "prompts/wake-agent-v1.md"
DEFAULT_SCHEMA = ROOT / "schemas/analysis-output.schema.json"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def build_agent_request(
    *,
    config: dict,
    prompt: str,
    conversation_input: list[object],
    output_schema: dict,
) -> dict:
    return {
        "model": config["model"],
        "instructions": prompt,
        "input": conversation_input,
        "reasoning": {"effort": config["reasoning_effort"]},
        "max_output_tokens": config["max_output_tokens"],
        "service_tier": config["service_tier"],
        "store": config["store"],
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": tool_definitions(config.get("tool_contract_version", "v1")),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "wake_analysis_output_v1_1",
                "schema": output_schema,
                "strict": True,
            }
        },
    }


def public_case_input_dir(root: Path, case_id: str) -> Path:
    input_dir = root / "data" / "fixtures" / case_id / "input"
    if not input_dir.is_dir() or (input_dir / "ground-truth.json").exists():
        raise ValueError(f"Unknown public case or unsafe input boundary: {case_id}")
    return input_dir


def write_agent_dry_run(
    *,
    config: dict,
    prompt: str,
    summaries: list[dict],
    output_schema: dict,
    output_dir: Path,
) -> Path:
    entries: dict[str, dict] = {}
    for summary in summaries:
        request = build_agent_request(
            config=config,
            prompt=prompt,
            conversation_input=[
                {
                    "role": "user",
                    "content": json.dumps(
                        summary, sort_keys=True, separators=(",", ":")
                    ),
                }
            ],
            output_schema=output_schema,
        )
        request_path = output_dir / "requests" / f"{summary['case_id']}.json"
        write_json(request_path, request)
        entries[summary["case_id"]] = {
            "path": str(request_path.relative_to(output_dir)),
            "sha256": sha256_path(request_path),
            "bytes": request_path.stat().st_size,
        }
    manifest_path = output_dir / "dry-run-manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": "wake.agent_dry_run.v1",
            "run_id": output_dir.name,
            "workflow": config["workflow"],
            "created_at": utc_now(),
            "api_called": False,
            "config_sha256": sha256_json(config),
            "requests": entries,
        },
    )
    return manifest_path


def default_output_dir(mode: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ROOT / "evaluation/runs/wake-agent-v1" / f"{timestamp}-{mode}"


def item_type(item: object) -> str:
    return str(object_value(item, "type", "unknown"))


def continuation_item(item: object) -> object:
    if isinstance(item, dict):
        return item
    model_dump = getattr(item, "model_dump", None)
    if callable(model_dump):
        return model_dump(exclude_none=True)
    kind = item_type(item)
    if kind == "function_call":
        return {
            "type": "function_call",
            "name": object_value(item, "name"),
            "call_id": object_value(item, "call_id"),
            "arguments": object_value(item, "arguments", "{}"),
        }
    return {"type": kind}


def allowed_evidence_refs(summary: dict) -> set[str]:
    allowed = {f"input/{path}" for path in summary["input_hashes"]}
    for source in summary["sources"]:
        allowed.update(source["evidence_refs"])
    for finding in summary["cross_source_findings"]:
        allowed.update(finding["evidence_refs"])
    if summary.get("environment"):
        allowed.add("input/environment.json")
    if summary.get("plan"):
        allowed.add("input/plan.json")
    return allowed


def output_evidence_refs(value: object) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence_refs" and isinstance(item, list):
                refs.extend(str(ref) for ref in item)
            else:
                refs.extend(output_evidence_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.extend(output_evidence_refs(item))
    return refs


def verify_output(
    *,
    output: dict,
    output_schema: dict,
    summary: dict,
    tool_contract_version: str = "v1",
) -> dict:
    errors: list[str] = []
    try:
        jsonschema.validate(instance=output, schema=output_schema)
    except jsonschema.ValidationError as error:
        errors.append(f"Schema violation: {error.message}")
    if output.get("case_id") != summary["case_id"]:
        errors.append(
            f"case_id {output.get('case_id')!r} does not match {summary['case_id']!r}"
        )

    allowed = allowed_evidence_refs(summary)
    invalid_refs = sorted(set(output_evidence_refs(output)) - allowed)
    for reference in invalid_refs:
        errors.append(f"Evidence reference does not exist in case input: {reference}")

    evidence_required: list[tuple[str, dict]] = []
    for collection_name in [
        "session_associations",
        "segments",
        "source_policy",
        "deviations",
    ]:
        evidence_required.extend(
            (collection_name, item) for item in output.get(collection_name, [])
        )
    evidence_required.extend(
        ("claims", claim)
        for claim in output.get("claims", [])
        if claim.get("status") not in {"UNKNOWN", "UNSUPPORTED"}
    )
    environment = output.get("environment_assessment")
    if isinstance(environment, dict):
        evidence_required.append(("environment_assessment", environment))
    plan_summary = output.get("plan_summary")
    if isinstance(plan_summary, dict) and plan_summary.get("status") != "NOT_SUPPLIED":
        evidence_required.append(("plan_summary", plan_summary))
    for collection_name, item in evidence_required:
        if not item.get("evidence_refs"):
            identifier = (
                item.get("claim_id")
                or item.get("segment_id")
                or item.get("metric")
                or item.get("segment_ref")
                or collection_name
            )
            errors.append(
                f"{collection_name} item {identifier!r} has no evidence references."
            )

    if tool_contract_version == "v2":
        for deviation in output.get("deviations", []):
            deviation_type = str(deviation.get("type", "")).upper()
            if (
                "DISTANCE" in deviation_type
                and any(
                    marker in deviation_type
                    for marker in ("SHORTFALL", "INCOMPLETE", "MISSED")
                )
            ):
                errors.append(
                    "Prescribed-distance completion deviation relies on "
                    "boundary-derived segment distance, which the v2 tool contract "
                    "marks insufficient for that conclusion."
                )

    prohibited_terms = {
        "technique": "visible technique",
        "synchronization": "crew synchronization",
        "medical": "medical state",
    }
    for claim in output.get("claims", []):
        statement = claim.get("statement", "").lower()
        if claim.get("status") in {"UNKNOWN", "UNSUPPORTED"}:
            continue
        for term, label in prohibited_terms.items():
            if term in statement:
                errors.append(
                    f"Claim {claim.get('claim_id')!r} asserts unsupported {label}."
                )

    sources_by_id = {source["source_id"]: source for source in summary["sources"]}
    environment = summary.get("environment")
    if isinstance(environment, dict) and environment.get("timeline_id"):
        sources_by_id[environment["timeline_id"]] = {
            "source_id": environment["timeline_id"],
            "quality_flags": [],
        }
    for policy in output.get("source_policy", []):
        selected_source_id = policy.get("selected_source_id")
        if (
            selected_source_id is not None
            and selected_source_id not in sources_by_id
        ):
            errors.append(f"Unknown selected source: {selected_source_id}")
            continue
        if policy.get("metric") not in {"stroke_rate_spm", "spm"}:
            continue
        source = sources_by_id.get(selected_source_id)
        if source and (
            "SPM_ALL_ZERO" in source["quality_flags"]
            or "RAW_SPM_ABSENT" in source["quality_flags"]
        ):
            errors.append(
                f"Broken SPM source selected: {source['source_id']}"
            )

    checks = [
        "schema",
        "case_identity",
        "evidence_references",
        "material_evidence_presence",
        "source_identity",
        "unsupported_claim_boundaries",
        "broken_spm_source",
    ]
    if tool_contract_version == "v2":
        checks.insert(4, "derived_distance_scope")
    return {
        "passed": not errors,
        "errors": errors,
        "checks": checks,
    }


def run_agent_case(
    *,
    client: object,
    config: dict,
    prompt: str,
    summary: dict,
    input_dir: Path,
    output_schema: dict,
    output_dir: Path,
    run_id: str,
    now: Callable[[], str],
    monotonic_values: Iterator[float] | None = None,
    git_commit: str,
) -> dict[str, Path]:
    monotonic_values = monotonic_values or iter(time.monotonic, None)
    started_at = now()
    started = next(monotonic_values)
    events: list[dict] = []
    conversation_input: list[object] = [
        {
            "role": "user",
            "content": json.dumps(summary, sort_keys=True, separators=(",", ":")),
        }
    ]
    final_output: dict | None = None
    final_verification: dict | None = None
    verifier_retries = 0
    total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def add_event(kind: str, **fields: object) -> None:
        events.append({"sequence": len(events) + 1, "type": kind, **fields})

    for round_number in range(1, int(config["max_rounds"]) + 1):
        request = build_agent_request(
            config=config,
            prompt=prompt,
            conversation_input=conversation_input,
            output_schema=output_schema,
        )
        response = client.responses.create(**request)
        if object_value(response, "status") != "completed":
            raise RuntimeError(
                f"Incomplete model response: {object_value(response, 'status')}"
            )
        usage = normalize_usage(object_value(response, "usage", {}))
        for key in total_usage:
            total_usage[key] += usage[key]
        output_items = list(object_value(response, "output", []) or [])
        add_event(
            "MODEL_RESPONSE",
            round=round_number,
            response_id=object_value(response, "id"),
            model=object_value(response, "model"),
            status=object_value(response, "status"),
            output_types=[item_type(item) for item in output_items],
            usage={key: usage[key] for key in total_usage},
        )
        function_calls = [
            item for item in output_items if item_type(item) == "function_call"
        ]
        if function_calls:
            conversation_input.extend(continuation_item(item) for item in output_items)
            for call in function_calls:
                name = str(object_value(call, "name"))
                call_id = str(object_value(call, "call_id"))
                arguments = json.loads(str(object_value(call, "arguments", "{}")))
                add_event(
                    "TOOL_CALL",
                    call_id=call_id,
                    tool=name,
                    arguments=arguments,
                )
                result = execute_tool(
                    name,
                    summary,
                    input_dir,
                    arguments,
                    contract_version=config.get("tool_contract_version", "v1"),
                )
                add_event(
                    "TOOL_RESULT",
                    call_id=call_id,
                    tool=name,
                    result=result,
                )
                conversation_input.append(
                    {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": json.dumps(result, sort_keys=True),
                    }
                )
            if round_number == int(config["max_rounds"]):
                raise RuntimeError(
                    "Agent exceeded maximum tool rounds without final output"
                )
            continue

        output_text = str(object_value(response, "output_text", ""))
        if not output_text:
            raise RuntimeError("Model returned neither tool calls nor final output")
        candidate = json.loads(output_text)
        verification = verify_output(
            output=candidate,
            output_schema=output_schema,
            summary=summary,
            tool_contract_version=config.get("tool_contract_version", "v1"),
        )
        add_event("VERIFICATION", **verification)
        if verification["passed"]:
            final_output = candidate
            final_verification = verification
            add_event("FINAL_OUTPUT", case_id=summary["case_id"])
            break
        if verifier_retries >= int(config["max_verifier_retries"]):
            raise RuntimeError(
                "Agent output failed verification: " + "; ".join(verification["errors"])
            )
        verifier_retries += 1
        add_event(
            "RETRY_REQUESTED",
            attempt=verifier_retries,
            errors=verification["errors"],
        )
        conversation_input.extend(continuation_item(item) for item in output_items)
        conversation_input.append(
            {
                "role": "user",
                "content": (
                    "The deterministic verifier rejected the candidate. Correct only "
                    "the listed issues and return a complete JSON output: "
                    + json.dumps(verification["errors"])
                ),
            }
        )

    if final_output is None or final_verification is None:
        raise RuntimeError("Agent stopped without a verified final output")

    finished = next(monotonic_values)
    finished_at = now()
    runtime_ms = round((finished - started) * 1000)

    case_id = summary["case_id"]
    output_path = output_dir / "outputs" / f"{case_id}.json"
    trajectory_path = output_dir / "trajectories" / f"{case_id}.trajectory.json"
    write_json(output_path, final_output)
    write_json(
        trajectory_path,
        {
            "schema_version": "wake.agent_trajectory.v1",
            "run_id": run_id,
            "workflow": config["workflow"],
            "case_id": case_id,
            "created_at": finished_at,
            "started_at": started_at,
            "finished_at": finished_at,
            "runtime_ms": runtime_ms,
            "git_commit": git_commit,
            "model": config["model"],
            "prompt_sha256": sha256_text(prompt),
            "summary_request_sha256": sha256_text(
                json.dumps(summary, sort_keys=True, separators=(",", ":"))
            ),
            "events": events,
            "verification": final_verification,
            "usage": total_usage,
            "approximate_cost_usd": estimate_cost_usd(
                total_usage, config["pricing"]
            ),
            "private_chain_of_thought_stored": False,
        },
    )
    return {"output_path": output_path, "trajectory_path": trajectory_path}


def build_agent_run_manifest(
    *,
    config: dict,
    prompt: str,
    output_dir: Path,
    run_id: str,
    git_commit: str,
    artifacts: list[dict[str, object]],
    trajectories: list[dict],
    started_at: str,
    finished_at: str,
    runtime_ms: int,
) -> dict:
    total_usage = {
        key: sum(item["usage"][key] for item in trajectories)
        for key in ["input_tokens", "output_tokens", "total_tokens"]
    }
    return {
        "schema_version": "wake.agent_run.v1",
        "run_id": run_id,
        "workflow": config["workflow"],
        "created_at": finished_at,
        "started_at": started_at,
        "finished_at": finished_at,
        "runtime_ms": runtime_ms,
        "case_runtime_ms_total": sum(item["runtime_ms"] for item in trajectories),
        "git_commit": git_commit,
        "cases": [item["case_id"] for item in trajectories],
        "config_sha256": sha256_json(config),
        "prompt_sha256": sha256_text(prompt),
        "total_usage": total_usage,
        "approximate_total_cost_usd": estimate_cost_usd(
            total_usage, config["pricing"]
        ),
        "trajectories": [
            str(Path(item["trajectory_path"]).relative_to(output_dir))
            for item in artifacts
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Call the OpenAI API.")
    parser.add_argument("--case", action="append", default=[], dest="case_ids")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    config = read_json(args.config)
    prompt = DEFAULT_PROMPT.read_text(encoding="utf-8")
    output_schema = read_json(DEFAULT_SCHEMA)
    summaries = [
        read_json(path)
        for path in selected_summaries(DEFAULT_INPUTS, args.case_ids)
    ]
    mode = "execute" if args.execute else "dry-run"
    output_dir = args.output or default_output_dir(mode)

    if not args.execute:
        manifest = write_agent_dry_run(
            config=config,
            prompt=prompt,
            summaries=summaries,
            output_schema=output_schema,
            output_dir=output_dir,
        )
        print(json.dumps({"mode": mode, "manifest": str(manifest)}, indent=2))
        return

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required with --execute.")
    try:
        from openai import OpenAI
    except ImportError as error:
        raise SystemExit("Missing dependency 'openai'. Run 'uv sync'.") from error

    client = OpenAI()
    run_id = output_dir.name
    git_commit = current_git_commit()
    run_started_at = utc_now()
    run_started = time.monotonic()
    artifacts: list[dict[str, str]] = []
    trajectories: list[dict] = []
    for summary in summaries:
        result = run_agent_case(
            client=client,
            config=config,
            prompt=prompt,
            summary=summary,
            input_dir=public_case_input_dir(ROOT, summary["case_id"]),
            output_schema=output_schema,
            output_dir=output_dir,
            run_id=run_id,
            now=utc_now,
            git_commit=git_commit,
        )
        artifacts.append({key: str(value) for key, value in result.items()})
        trajectories.append(read_json(result["trajectory_path"]))

    run_finished = time.monotonic()
    run_finished_at = utc_now()
    run_manifest = output_dir / "run-manifest.json"
    write_json(
        run_manifest,
        build_agent_run_manifest(
            config=config,
            prompt=prompt,
            output_dir=output_dir,
            run_id=run_id,
            git_commit=git_commit,
            artifacts=artifacts,
            trajectories=trajectories,
            started_at=run_started_at,
            finished_at=run_finished_at,
            runtime_ms=round((run_finished - run_started) * 1000),
        ),
    )
    print(
        json.dumps(
            {"mode": mode, "run_manifest": str(run_manifest), "artifacts": artifacts},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
