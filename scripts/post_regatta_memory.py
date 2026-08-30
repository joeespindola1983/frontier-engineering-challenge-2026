#!/usr/bin/env python3
"""Freeze or execute one saved WAKE memory over both club periods.

The default command writes a zero-cost preflight. Live execution requires the
literal ``--execute`` flag, ``OPENAI_API_KEY``, and the standard finite start
authorization. The request uses ``store: false``; verified output is persisted
inside WAKE so it can be reopened without another model call.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import longitudinal_pilot
from run_baseline import read_json, sha256_json, write_json


ROOT = Path(__file__).resolve().parents[1]
POST_MANIFEST_PATH = ROOT / "data" / "demo-club-post-regatta" / "v1" / "manifest.json"
POST_EVIDENCE_PATH = (
    ROOT / "data" / "demo-club-post-regatta" / "v1" / "longitudinal-evidence.json"
)
OUTPUT_SCHEMA_PATH = ROOT / "schemas" / "longitudinal-intelligence-output.schema.json"
DEFAULT_OUTPUT = ROOT / "evaluation" / "post-regatta-memory" / "v1" / "preflight"


def _sha256_path(path: Path) -> str:
    return longitudinal_pilot.sha256_path(path)


def build_memory_summary() -> dict:
    pre = longitudinal_pilot.build_pilot_summaries()["club-coach"]
    post_manifest = read_json(POST_MANIFEST_PATH)
    post_evidence = read_json(POST_EVIDENCE_PATH)
    post_coverage = post_manifest["coverage"]
    evidence_catalog = dict(pre["evidence_catalog"])
    evidence_catalog["package:wake-demo-club-post-regatta-v1"] = (
        "Content-addressed real-informed synthetic post-regatta package manifest."
    )
    evidence_catalog.update(post_evidence["evidence_descriptions"])

    period_comparisons = post_evidence["comparisons"]
    comparison_attention = [
        {
            "session_id": item["comparison_id"],
            "date": None,
            "route": {
                "SUPPORTED": "PERIOD_COMPARISON",
                "CONFLICTED": "CONTEXT_REQUIRED",
                "INSUFFICIENT": "HUMAN_OR_SOURCE_REQUIRED",
            }[item["status"]],
            "statement": item["statement"],
            "evidence_refs": item["evidence_refs"],
        }
        for item in period_comparisons
    ]

    return {
        "schema_version": "wake.longitudinal_summary.v1",
        "pilot_id": "club-post-regatta-memory",
        "scope": {
            "type": "CLUB",
            "entity_id": "wake-demo-club",
            "display_name": "WAKE Demo Club",
        },
        "period": {"start": "2026-08-17", "end": post_manifest["period"]["end"]},
        "provenance": "REAL_INFORMED_SYNTHETIC",
        "model_called": False,
        "coverage": {
            "activity_count": pre["coverage"]["activity_count"] + post_coverage["activities"],
            "active_days": pre["coverage"]["active_days"] + post_manifest["period"]["weekdays"],
            "water_activity_count": (
                pre["coverage"]["water_activity_count"] + post_coverage["water_crew_activities"]
            ),
            "indoor_activity_count": (
                pre["coverage"]["indoor_activity_count"]
                + post_coverage["individual_concept2_activities"]
            ),
            "club_activity_count": pre["coverage"]["activity_count"] + post_coverage["activities"],
            "athlete_count": post_coverage["athletes"],
            "crew_count": post_coverage["crews"],
            "period_count": 2,
        },
        "modality_totals": {
            "pre_regatta": pre["modality_totals"],
            "post_regatta": {
                "status": "COUNT_COVERAGE_ONLY",
                "reason": (
                    "The second package preserves activity-level records and comparison evidence, "
                    "but does not expose a cross-modality combined-distance total."
                ),
            },
        },
        "routing": {
            **pre["routing"],
            "PERIOD_COMPARISON": sum(item["status"] == "SUPPORTED" for item in period_comparisons),
            "CONTEXT_REQUIRED": sum(item["status"] == "CONFLICTED" for item in period_comparisons),
            "POST_HUMAN_OR_SOURCE_REQUIRED": sum(
                item["status"] == "INSUFFICIENT" for item in period_comparisons
            ),
        },
        "activity_summaries": [
            {
                "period": "PRE_REGATTA",
                "activity_count": pre["coverage"]["activity_count"],
                "evidence_refs": ["batch:manifest"],
            },
            {
                "period": "POST_REGATTA",
                "activity_count": post_coverage["activities"],
                "evidence_refs": ["package:wake-demo-club-post-regatta-v1"],
            },
        ],
        "attention_signals": pre["attention_signals"] + comparison_attention,
        "verified_investigations": pre["verified_investigations"],
        "period_comparisons": period_comparisons,
        "comparison_readiness": {
            "repeated_context_groups": pre["comparison_readiness"]["repeated_context_groups"],
            "controlled_observations": [
                item for item in period_comparisons if item["status"] == "SUPPORTED"
            ],
            "performance_trend_supported": False,
            "reason": (
                "Three narrow workout comparisons support observed numeric differences only. "
                "The package does not control intent, effort, recovery, equipment, environment, "
                "or physiology well enough for an athletic-performance or causal trend."
            ),
        },
        "evidence_catalog": evidence_catalog,
        "boundaries": [
            "Water and indoor distance remain separate and must not be summed into one performance total.",
            "Observed faster, slower, or stable values do not establish fitness, strength, stamina, technique, or causation.",
            "Weather-confounded water evidence requires context rather than attribution to a crew.",
            "Missing activity creates a human question rather than a commitment or readiness conclusion.",
            "Every identity and activity in this public package is fictional and real-informed synthetic.",
        ],
    }


def write_memory_dry_run(output_dir: Path) -> Path:
    summary = build_memory_summary()
    output_schema = read_json(OUTPUT_SCHEMA_PATH)
    input_path = output_dir / "inputs" / "club-post-regatta-memory.json"
    request_path = (
        output_dir / "requests" / "club-post-regatta-memory.wake_bounded_agent.json"
    )
    write_json(input_path, summary)
    write_json(request_path, longitudinal_pilot.build_agent_request(summary, output_schema))
    required = longitudinal_pilot.required_authorization_usd(1)
    manifest_path = output_dir / "dry-run-manifest.json"
    write_json(manifest_path, {
        "schema_version": "wake.post_regatta_memory_dry_run.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "api_called": False,
        "request_count": 1,
        "input": {
            "path": str(input_path.relative_to(output_dir)),
            "sha256": _sha256_path(input_path),
        },
        "request": {
            "workflow": "WAKE_BOUNDED_AGENT",
            "path": str(request_path.relative_to(output_dir)),
            "sha256": _sha256_path(request_path),
        },
        "authorization": {
            "required_total_usd": required,
            "provider_cap": False,
            "authorized": False,
        },
        "saved_reports": {"count": 0, "reopen_cost_usd": 0},
        "boundary": (
            "The preflight contains no model output. Live execution uses store:false and "
            "persists the verified WAKE report locally."
        ),
    })
    return manifest_path


def verify_memory_directory(directory: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = directory / "dry-run-manifest.json"
    if not manifest_path.exists():
        return ["Missing dry-run manifest."]
    manifest = read_json(manifest_path)
    for field in ("input", "request"):
        artifact = manifest[field]
        path = directory / artifact["path"]
        if not path.exists():
            errors.append(f"Missing {field} artifact: {artifact['path']}")
        elif _sha256_path(path) != artifact["sha256"]:
            errors.append(f"{field.title()} hash does not match the frozen manifest.")
    request_path = directory / manifest["request"]["path"]
    if request_path.exists():
        request = read_json(request_path)
        if request.get("store") is not False:
            errors.append("Frozen request must use store:false.")
        if request.get("model") != longitudinal_pilot._config()["model"]:
            errors.append("Frozen request model does not match configuration.")
    return errors


def execute_memory(output_dir: Path, authorized_cost_usd: float) -> Path:
    longitudinal_pilot.validate_authorization(authorized_cost_usd, 1)
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required with --execute.")
    try:
        from openai import OpenAI
    except ImportError as error:
        raise SystemExit("Missing dependency 'openai'. Run 'uv sync'.") from error

    summary = build_memory_summary()
    result = longitudinal_pilot.run_agent_case(
        client=OpenAI(),
        summary=summary,
        output_schema=read_json(OUTPUT_SCHEMA_PATH),
        output_dir=output_dir,
    )
    artifact = result["artifact"]
    run_manifest = output_dir / "run-manifest.json"
    write_json(run_manifest, {
        "schema_version": "wake.post_regatta_memory_run.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "api_called": True,
        "store": False,
        "authorized_cost_usd": authorized_cost_usd,
        "authorization_is_provider_cap": False,
        "execution_count": 1,
        "total_approximate_cost_usd": artifact["observability"]["approximate_cost_usd"],
        "input_sha256": sha256_json(summary),
        "report": str(result["artifact_path"].relative_to(output_dir)),
        "verification": artifact["verification"],
        "reopen_cost_usd": 0,
    })
    return run_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorized-cost-usd", type=float, default=0.0)
    args = parser.parse_args()

    if not args.execute:
        manifest = write_memory_dry_run(args.output)
        print(json.dumps({
            "status": "READY_FOR_AUTHORIZATION",
            "api_called": False,
            "required_authorization_usd": 0.2,
            "manifest": str(manifest),
        }, indent=2))
        return
    manifest = execute_memory(args.output, args.authorized_cost_usd)
    print(json.dumps({
        "status": "COMPLETED",
        "api_called": True,
        "manifest": str(manifest),
    }, indent=2))


if __name__ == "__main__":
    main()
