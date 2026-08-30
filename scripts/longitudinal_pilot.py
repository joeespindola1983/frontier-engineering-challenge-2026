#!/usr/bin/env python3
"""Prepare and verify WAKE's two-case longitudinal intelligence pilot.

The default path is a zero-cost dry run. Paid execution remains a separate,
explicitly authorized action.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

import source_adapters
from run_baseline import normalize_usage, object_value, read_json, sha256_json, write_json


ROOT = Path(__file__).resolve().parents[1]
BATCH_ROOT = ROOT / "data" / "demo-club-batch"
MANIFEST_PATH = BATCH_ROOT / "manifest.json"
INVESTIGATION_MANIFEST_PATH = (
    ROOT
    / "evaluation"
    / "runs"
    / "demo-club-investigations-v1-20260830"
    / "run-manifest.json"
)
CONFIG_PATH = ROOT / "config" / "longitudinal-pilot-v1.json"
OUTPUT_SCHEMA_PATH = ROOT / "schemas" / "longitudinal-intelligence-output.schema.json"
BASELINE_PROMPT_PATH = ROOT / "prompts" / "longitudinal-baseline-v1.md"
AGENT_PROMPT_PATH = ROOT / "prompts" / "longitudinal-agent-v1.md"
DEFAULT_OUTPUT = ROOT / "evaluation" / "longitudinal-pilot" / "v1" / "preflight"


TOOL_NAMES = (
    "inspect_scope_coverage",
    "list_attention_signals",
    "find_comparable_sessions",
    "get_verified_investigations",
)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _average(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def _normalized_metrics(session: dict) -> dict:
    session_dir = BATCH_ROOT / "sessions" / session["session_id"]
    if session["modality"] == "ERG":
        kind = "CONCEPT2"
        filename = "concept2.csv"
    else:
        kind = "SPEEDCOACH"
        filename = "speedcoach.csv"
    source = source_adapters.normalize_source(
        kind=kind,
        content=(session_dir / filename).read_bytes(),
        source_ref=f"session:{session['session_id']}:{filename}",
    )
    rows = list(csv.DictReader(source.normalized_csv.decode("utf-8").splitlines()))
    positive_spm = [
        float(row["stroke_rate_spm"])
        for row in rows
        if row.get("stroke_rate_spm") and float(row["stroke_rate_spm"]) > 0
    ]
    positive_speed = [
        float(row["speed_m_s"])
        for row in rows
        if row.get("speed_m_s") and float(row["speed_m_s"]) > 0
    ]
    pace = []
    watts = []
    if session["modality"] == "ERG":
        with (session_dir / filename).open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("pace_500m_s"):
                    pace.append(float(row["pace_500m_s"]))
                if row.get("watts"):
                    watts.append(float(row["watts"]))
    return {
        "distance_m": round(float(source.report["max_distance_m"]), 1),
        "duration_s": round(float(source.report["duration_s"]), 1),
        "average_spm": _average(positive_spm),
        "average_speed_m_s": _average(positive_speed),
        "average_pace_500m_s": _average(pace),
        "average_watts": _average(watts),
        "quality_flags": source.report["quality_flags"],
    }


def _session_records(manifest: dict) -> list[dict]:
    records = []
    for session in manifest["sessions"]:
        ref = f"record:{session['session_id']}"
        records.append({
            "session_id": session["session_id"],
            "date": session["date"],
            "title": session["title"],
            "modality": session["modality"],
            "athlete_ids": session["athlete_ids"],
            "crew_id": session["crew_id"],
            "boat_id": session["boat_id"],
            "training_role": session["training_role"],
            "association_status": session["association_status"],
            "workout_type": session["workout_type"],
            "route": session["expected_route"],
            "metrics": _normalized_metrics(session),
            "evidence_refs": [ref],
        })
    return records


def _verified_investigations(records: list[dict]) -> list[dict]:
    record_by_id = {record["session_id"]: record for record in records}
    manifest = read_json(INVESTIGATION_MANIFEST_PATH)
    results = []
    for execution in manifest["executions"]:
        case_id = execution["case_id"]
        results.append({
            "case_id": case_id,
            "scope_athlete_ids": record_by_id[case_id]["athlete_ids"],
            "deviations": execution["expected_deviations"],
            "verification_passed": True,
            "evidence_refs": [f"verified:{case_id}"],
        })
    return results


def _comparison_readiness(records: list[dict]) -> dict:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for record in records:
        key = (
            record["modality"],
            record["workout_type"],
            record["title"],
            record["crew_id"],
            record["boat_id"],
        )
        groups[key].append(record)
    repeated = [
        {
            "signature": "|".join(str(part or "NONE") for part in key),
            "session_ids": [item["session_id"] for item in items],
            "evidence_refs": [ref for item in items for ref in item["evidence_refs"]],
        }
        for key, items in groups.items()
        if len(items) >= 2
    ]
    return {
        "repeated_context_groups": repeated,
        "performance_trend_supported": False,
        "reason": (
            "Repeated context alone does not control environment, human effort, "
            "technical execution, or source comparability well enough for a performance trend."
        ),
    }


def _modality_totals(records: list[dict]) -> dict:
    return {
        "water_distance_m": round(sum(
            item["metrics"]["distance_m"]
            for item in records
            if item["modality"].startswith("WATER")
        ), 1),
        "indoor_distance_m": round(sum(
            item["metrics"]["distance_m"]
            for item in records
            if item["modality"] == "ERG"
        ), 1),
    }


def _evidence_catalog(records: list[dict], investigations: list[dict]) -> dict:
    catalog = {
        "batch:manifest": "Content-addressed two-week public batch manifest.",
    }
    for record in records:
        catalog[record["evidence_refs"][0]] = (
            f"Deterministically normalized {record['modality']} activity on {record['date']}."
        )
    for investigation in investigations:
        catalog[investigation["evidence_refs"][0]] = (
            f"Verified bounded-agent result for {investigation['case_id']}."
        )
    return catalog


def _attention(records: list[dict]) -> list[dict]:
    attention_routes = {"AGENT_VERIFIED", "SOURCE_REQUIRED", "HUMAN_CONTEXT_REQUIRED"}
    return [
        {
            "session_id": record["session_id"],
            "date": record["date"],
            "route": record["route"],
            "statement": {
                "AGENT_VERIFIED": "A bounded session investigation is preserved.",
                "SOURCE_REQUIRED": "A planned workout source is missing.",
                "HUMAN_CONTEXT_REQUIRED": "Athlete context is required before interpretation.",
            }[record["route"]],
            "evidence_refs": record["evidence_refs"],
        }
        for record in records
        if record["route"] in attention_routes
    ]


def _compact_activity(record: dict, *, club_scope: bool) -> dict:
    if not club_scope:
        return record
    return {
        "session_id": record["session_id"],
        "date": record["date"],
        "modality": record["modality"],
        "crew_id": record["crew_id"],
        "route": record["route"],
        "distance_m": record["metrics"]["distance_m"],
        "evidence_refs": record["evidence_refs"],
    }


def _base_summary(*, pilot_id: str, scope: dict, records: list[dict], all_records: list[dict], investigations: list[dict]) -> dict:
    routing = Counter(record["route"] for record in records)
    attention = _attention(records)
    catalog = _evidence_catalog(records, investigations)
    return {
        "schema_version": "wake.longitudinal_summary.v1",
        "pilot_id": pilot_id,
        "scope": scope,
        "period": {"start": "2026-08-17", "end": "2026-08-28"},
        "provenance": "REAL_INFORMED_SYNTHETIC",
        "model_called": False,
        "coverage": {
            "activity_count": len(records),
            "active_days": len({record["date"] for record in records}),
            "water_activity_count": sum(record["modality"].startswith("WATER") for record in records),
            "indoor_activity_count": sum(record["modality"] == "ERG" for record in records),
            "club_activity_count": len(all_records),
        },
        "modality_totals": _modality_totals(records),
        "routing": {
            **dict(routing),
            "HUMAN_OR_SOURCE_REQUIRED": (
                routing["SOURCE_REQUIRED"] + routing["HUMAN_CONTEXT_REQUIRED"]
            ),
        },
        "activity_summaries": [
            _compact_activity(record, club_scope=scope["type"] == "CLUB")
            for record in records
        ],
        "attention_signals": attention,
        "verified_investigations": investigations,
        "comparison_readiness": _comparison_readiness(records),
        "evidence_catalog": catalog,
        "boundaries": [
            "Water and indoor distance remain separate and must not be summed into one performance total.",
            "No visible technique, crew synchronization, health, strength, stamina, fitness, or commitment conclusion is supported.",
            "No performance trend is supported by this preflight.",
            "The data are real-informed synthetic and do not describe real athletes.",
        ],
    }


def build_pilot_summaries() -> dict[str, dict]:
    manifest = read_json(MANIFEST_PATH)
    records = _session_records(manifest)
    investigations = _verified_investigations(records)
    lucas_records = [item for item in records if "athlete-lucas" in item["athlete_ids"]]
    lucas_investigations = [
        item for item in investigations if "athlete-lucas" in item["scope_athlete_ids"]
    ]
    return {
        "athlete-lucas": _base_summary(
            pilot_id="athlete-lucas",
            scope={"type": "ATHLETE", "entity_id": "athlete-lucas", "display_name": "Lucas"},
            records=lucas_records,
            all_records=records,
            investigations=lucas_investigations,
        ),
        "club-coach": _base_summary(
            pilot_id="club-coach",
            scope={"type": "CLUB", "entity_id": "wake-demo-club", "display_name": "WAKE Demo Club"},
            records=records,
            all_records=records,
            investigations=investigations,
        ),
    }


def _tool(name: str, description: str, properties: dict | None = None) -> dict:
    return {
        "type": "function",
        "name": name,
        "description": description,
        "strict": True,
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": properties or {},
            "required": list((properties or {}).keys()),
        },
    }


def tool_definitions() -> list[dict]:
    return [
        _tool("inspect_scope_coverage", "Return scope, period, coverage, modality totals, and boundaries."),
        _tool("list_attention_signals", "Return only evidence-backed human, source, and verified-session attention signals."),
        _tool("find_comparable_sessions", "Return repeated-context groups and the deterministic trend-support boundary."),
        _tool("get_verified_investigations", "Return preserved verified session investigations inside this scope."),
    ]


def execute_tool(summary: dict, name: str) -> dict:
    if name == "inspect_scope_coverage":
        return {key: summary[key] for key in ("scope", "period", "coverage", "modality_totals", "boundaries")}
    if name == "list_attention_signals":
        return {"attention_signals": summary["attention_signals"]}
    if name == "find_comparable_sessions":
        return {"comparison_readiness": summary["comparison_readiness"]}
    if name == "get_verified_investigations":
        return {"verified_investigations": summary["verified_investigations"]}
    raise ValueError(f"Unknown longitudinal tool: {name}")


def _config() -> dict:
    return read_json(CONFIG_PATH)


def build_baseline_request(summary: dict, output_schema: dict) -> dict:
    config = _config()
    return {
        "model": config["model"],
        "instructions": BASELINE_PROMPT_PATH.read_text(encoding="utf-8"),
        "input": json.dumps(summary, sort_keys=True, separators=(",", ":")),
        "reasoning": {"effort": config["reasoning_effort"]},
        "max_output_tokens": config["max_output_tokens"],
        "service_tier": config["service_tier"],
        "store": config["store"],
        "text": {"format": {
            "type": "json_schema",
            "name": "wake_longitudinal_intelligence_v1",
            "schema": output_schema,
            "strict": True,
        }},
    }


def build_agent_request(summary: dict, output_schema: dict) -> dict:
    config = _config()
    scope_header = {
        "pilot_id": summary["pilot_id"],
        "scope": summary["scope"],
        "instruction": "Investigate this frozen longitudinal scope with the available tools.",
    }
    return {
        "model": config["model"],
        "instructions": AGENT_PROMPT_PATH.read_text(encoding="utf-8"),
        "input": [{"role": "user", "content": json.dumps(scope_header, sort_keys=True)}],
        "reasoning": {"effort": config["reasoning_effort"]},
        "max_output_tokens": config["max_output_tokens"],
        "service_tier": config["service_tier"],
        "store": config["store"],
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": tool_definitions(),
        "text": {"format": {
            "type": "json_schema",
            "name": "wake_longitudinal_intelligence_v1",
            "schema": output_schema,
            "strict": True,
        }},
    }


def _all_evidence_refs(value: object) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence_refs" and isinstance(item, list):
                refs.extend(str(ref) for ref in item)
            else:
                refs.extend(_all_evidence_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.extend(_all_evidence_refs(item))
    return refs


def verify_longitudinal_output(*, output: dict, output_schema: dict, summary: dict) -> list[str]:
    errors: list[str] = []
    try:
        jsonschema.validate(output, output_schema)
    except jsonschema.ValidationError as error:
        errors.append(f"Schema violation: {error.message}")
    if output.get("pilot_id") != summary["pilot_id"]:
        errors.append("Output pilot_id does not match the frozen summary.")
    if output.get("scope") != {
        "type": summary["scope"]["type"],
        "entity_id": summary["scope"]["entity_id"],
    }:
        errors.append("Output scope does not match the frozen summary.")
    allowed = set(summary["evidence_catalog"])
    for reference in sorted(set(_all_evidence_refs(output)) - allowed):
        errors.append(f"Evidence reference does not exist in pilot input: {reference}")
    serialized = json.dumps(output, sort_keys=True).lower()
    prohibited = (
        "improved fitness", "fitness improved", "declined fitness", "fitness declined",
        "improved stamina", "stronger athlete", "weaker athlete", "technique improved",
        "performance improved", "performance declined", "performance regressed",
    )
    if not summary["comparison_readiness"]["performance_trend_supported"]:
        if any(term in serialized for term in prohibited):
            errors.append("Unsupported longitudinal performance or physiology trend was asserted.")
    if any(term in serialized for term in ("combined water and indoor distance", "merged water and indoor")):
        errors.append("Water and indoor distance were merged despite the modality boundary.")
    return errors


def example_valid_output(summary: dict) -> dict:
    ref = next(iter(summary["evidence_catalog"]))
    return {
        "schema_version": "wake.longitudinal_intelligence_output.v1",
        "pilot_id": summary["pilot_id"],
        "scope": {"type": summary["scope"]["type"], "entity_id": summary["scope"]["entity_id"]},
        "headline": "The period is reconstructed; review attention items before drawing a trend.",
        "observed_facts": [{
            "fact_id": "coverage",
            "statement": f"{summary['coverage']['activity_count']} activities are represented in this scope.",
            "confidence": 1.0,
            "evidence_refs": [ref],
        }],
        "comparisons": [{
            "comparison_id": "trend-readiness",
            "status": "INSUFFICIENT",
            "statement": "The available sessions do not support a performance trend.",
            "evidence_refs": [ref],
            "limitations": [summary["comparison_readiness"]["reason"]],
        }],
        "priorities": [],
        "unresolved_questions": [],
        "recommendations": [],
        "boundaries": summary["boundaries"],
        "coach_briefing": "Use the reconstructed chronology and resolve open evidence gaps before comparison.",
    }


def _usage_total(items: list[dict[str, int]]) -> dict[str, int]:
    keys = (
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "cached_input_tokens",
        "reasoning_output_tokens",
    )
    return {key: sum(item.get(key, 0) for item in items) for key in keys}


def _estimate_cost(usage: dict[str, int]) -> float:
    pricing = _config()["pricing"]
    cached = usage["cached_input_tokens"]
    uncached = max(0, usage["input_tokens"] - cached)
    cost = (
        uncached * pricing["input_usd_per_million_tokens"]
        + cached * pricing["cached_input_usd_per_million_tokens"]
        + usage["output_tokens"] * pricing["output_usd_per_million_tokens"]
    ) / 1_000_000
    return round(cost, 6)


def required_authorization_usd(start_count: int) -> float:
    return round(start_count * _config()["authorization_gate_per_start_usd"], 2)


def validate_authorization(authorized_cost_usd: float, start_count: int) -> None:
    if not math.isfinite(authorized_cost_usd):
        raise ValueError("Cost authorization must be finite.")
    required = required_authorization_usd(start_count)
    if authorized_cost_usd < required:
        raise ValueError(
            f"US${required:.2f} authorization is required for {start_count} paid starts. "
            "This gate is not a provider billing cap."
        )


def _continuation_item(item: object) -> object:
    if isinstance(item, dict):
        return item
    dump = getattr(item, "model_dump", None)
    if callable(dump):
        return dump(exclude_none=True)
    if object_value(item, "type") == "function_call":
        return {
            "type": "function_call",
            "name": object_value(item, "name"),
            "call_id": object_value(item, "call_id"),
            "arguments": object_value(item, "arguments", "{}"),
        }
    return {"type": str(object_value(item, "type", "unknown"))}


def _artifact(
    *,
    workflow: str,
    summary: dict,
    output: dict,
    verification_errors: list[str],
    response_ids: list[str],
    usage: dict[str, int],
    runtime_ms: int,
    started_at: str,
    finished_at: str,
    tool_events: list[dict],
) -> dict:
    return {
        "schema_version": "wake.longitudinal_pilot_artifact.v1",
        "workflow": workflow,
        "pilot_id": summary["pilot_id"],
        "started_at": started_at,
        "finished_at": finished_at,
        "input_sha256": sha256_json(summary),
        "output": output,
        "verification": {
            "passed": not verification_errors,
            "errors": verification_errors,
        },
        "tool_events": tool_events,
        "response_ids": response_ids,
        "observability": {
            "model": _config()["model"],
            "reasoning_effort": _config()["reasoning_effort"],
            "runtime_ms": runtime_ms,
            "usage": usage,
            "approximate_cost_usd": _estimate_cost(usage),
        },
        "boundary": "Saved structured output can be reopened without another model call.",
    }


def _write_artifact(output_dir: Path, artifact: dict) -> Path:
    path = (
        output_dir
        / "reports"
        / f"{artifact['pilot_id']}.{artifact['workflow'].lower()}.json"
    )
    write_json(path, artifact)
    return path


def run_baseline_case(
    *,
    client: object,
    summary: dict,
    output_schema: dict,
    output_dir: Path,
    now=lambda: datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    monotonic_values=None,
) -> dict:
    request = build_baseline_request(summary, output_schema)
    clock = monotonic_values or iter(time.monotonic, None)
    started_at = now()
    started = next(clock)
    response = client.responses.create(**request)
    finished = next(clock)
    finished_at = now()
    if object_value(response, "status") != "completed":
        raise RuntimeError("Incomplete longitudinal baseline response.")
    output = json.loads(str(object_value(response, "output_text")))
    errors = verify_longitudinal_output(
        output=output, output_schema=output_schema, summary=summary
    )
    if errors:
        raise ValueError("; ".join(errors))
    usage = normalize_usage(object_value(response, "usage", {}))
    artifact = _artifact(
        workflow="DIRECT_BASELINE",
        summary=summary,
        output=output,
        verification_errors=errors,
        response_ids=[str(object_value(response, "id"))],
        usage=usage,
        runtime_ms=round((finished - started) * 1000),
        started_at=started_at,
        finished_at=finished_at,
        tool_events=[],
    )
    return {"artifact_path": _write_artifact(output_dir, artifact), "artifact": artifact}


def run_agent_case(
    *,
    client: object,
    summary: dict,
    output_schema: dict,
    output_dir: Path,
    now=lambda: datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
    monotonic_values=None,
) -> dict:
    request = build_agent_request(summary, output_schema)
    conversation = list(request["input"])
    clock = monotonic_values or iter(time.monotonic, None)
    started_at = now()
    started = next(clock)
    tool_events: list[dict] = []
    response_ids: list[str] = []
    usage_items: list[dict[str, int]] = []
    output = None
    for _round in range(_config()["max_rounds"]):
        response = client.responses.create(**{**request, "input": conversation})
        response_ids.append(str(object_value(response, "id")))
        usage_items.append(normalize_usage(object_value(response, "usage", {})))
        if object_value(response, "status") != "completed":
            raise RuntimeError("Incomplete longitudinal agent response.")
        calls = [
            item
            for item in object_value(response, "output", [])
            if object_value(item, "type") == "function_call"
        ]
        if calls:
            conversation.extend(_continuation_item(item) for item in object_value(response, "output", []))
            for call in calls:
                name = str(object_value(call, "name"))
                call_id = str(object_value(call, "call_id"))
                tool_events.append({"type": "TOOL_CALL", "name": name, "call_id": call_id})
                result = execute_tool(summary, name)
                tool_events.append({
                    "type": "TOOL_RESULT",
                    "name": name,
                    "call_id": call_id,
                    "result_sha256": sha256_json(result),
                })
                conversation.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result, sort_keys=True, separators=(",", ":")),
                })
            continue
        output = json.loads(str(object_value(response, "output_text")))
        break
    if output is None:
        raise RuntimeError("Longitudinal agent reached its round limit without a final output.")
    finished = next(clock)
    finished_at = now()
    errors = verify_longitudinal_output(
        output=output, output_schema=output_schema, summary=summary
    )
    if errors:
        raise ValueError("; ".join(errors))
    usage = _usage_total(usage_items)
    artifact = _artifact(
        workflow="WAKE_BOUNDED_AGENT",
        summary=summary,
        output=output,
        verification_errors=errors,
        response_ids=response_ids,
        usage=usage,
        runtime_ms=round((finished - started) * 1000),
        started_at=started_at,
        finished_at=finished_at,
        tool_events=tool_events,
    )
    return {"artifact_path": _write_artifact(output_dir, artifact), "artifact": artifact}


def write_pilot_dry_run(*, summaries: dict[str, dict], output_dir: Path) -> Path:
    output_schema = read_json(OUTPUT_SCHEMA_PATH)
    requests = []
    for pilot_id, summary in summaries.items():
        summary_path = output_dir / "inputs" / f"{pilot_id}.json"
        write_json(summary_path, summary)
        for workflow, builder in (
            ("DIRECT_BASELINE", build_baseline_request),
            ("WAKE_BOUNDED_AGENT", build_agent_request),
        ):
            request_path = output_dir / "requests" / f"{pilot_id}.{workflow.lower()}.json"
            write_json(request_path, builder(summary, output_schema))
            requests.append({
                "pilot_id": pilot_id,
                "workflow": workflow,
                "path": str(request_path.relative_to(output_dir)),
                "sha256": sha256_path(request_path),
            })
    config = _config()
    manifest_path = output_dir / "dry-run-manifest.json"
    write_json(manifest_path, {
        "schema_version": "wake.longitudinal_pilot_dry_run.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "api_called": False,
        "request_count": len(requests),
        "configuration": {
            "model": config["model"],
            "reasoning_effort": config["reasoning_effort"],
            "config_sha256": sha256_json(config),
            "output_schema_sha256": sha256_path(OUTPUT_SCHEMA_PATH),
        },
        "authorization": {
            "required_per_start_usd": config["authorization_gate_per_start_usd"],
            "required_total_usd": round(
                len(requests) * config["authorization_gate_per_start_usd"], 2
            ),
            "provider_cap": False,
            "authorized": False,
        },
        "requests": requests,
        "saved_reports": {"count": 0, "reopen_cost_usd": 0},
        "boundary": (
            "This artifact freezes requests only. It contains no model output and incurred no API cost."
        ),
    })
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--execute", action="store_true", help="Call the OpenAI API.")
    parser.add_argument(
        "--authorized-cost-usd",
        type=float,
        default=0.0,
        help="Explicit start-gate authorization; this is not a provider cap.",
    )
    parser.add_argument(
        "--pilot-id",
        action="append",
        choices=("athlete-lucas", "club-coach"),
        dest="pilot_ids",
        help="Limit execution to one frozen pilot case.",
    )
    parser.add_argument(
        "--workflow",
        choices=("baseline", "wake", "both"),
        default="both",
    )
    args = parser.parse_args()
    summaries = build_pilot_summaries()
    selected_ids = args.pilot_ids or list(summaries)
    selected = {pilot_id: summaries[pilot_id] for pilot_id in selected_ids}
    if not args.execute:
        manifest = write_pilot_dry_run(summaries=selected, output_dir=args.output)
        print(json.dumps({
            "status": "READY_FOR_AUTHORIZATION",
            "api_called": False,
            "manifest": str(manifest),
        }, indent=2))
        return

    workflows = (
        ("baseline", "wake") if args.workflow == "both" else (args.workflow,)
    )
    start_count = len(selected) * len(workflows)
    try:
        validate_authorization(args.authorized_cost_usd, start_count)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required with --execute.")
    try:
        from openai import OpenAI
    except ImportError as error:
        raise SystemExit("Missing dependency 'openai'. Run 'uv sync'.") from error

    client = OpenAI()
    output_schema = read_json(OUTPUT_SCHEMA_PATH)
    artifacts: list[dict] = []
    for summary in selected.values():
        for workflow in workflows:
            runner = run_baseline_case if workflow == "baseline" else run_agent_case
            result = runner(
                client=client,
                summary=summary,
                output_schema=output_schema,
                output_dir=args.output,
            )
            artifacts.append(result["artifact"])
    run_manifest = args.output / "run-manifest.json"
    write_json(run_manifest, {
        "schema_version": "wake.longitudinal_pilot_run.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "api_called": True,
        "authorized_cost_usd": args.authorized_cost_usd,
        "authorization_is_provider_cap": False,
        "execution_count": len(artifacts),
        "total_approximate_cost_usd": round(sum(
            artifact["observability"]["approximate_cost_usd"] for artifact in artifacts
        ), 6),
        "reports": [
            f"reports/{artifact['pilot_id']}.{artifact['workflow'].lower()}.json"
            for artifact in artifacts
        ],
    })
    print(json.dumps({
        "status": "COMPLETED",
        "api_called": True,
        "manifest": str(run_manifest),
        "execution_count": len(artifacts),
    }, indent=2))


if __name__ == "__main__":
    main()
