#!/usr/bin/env python3
"""Freeze or execute a direct baseline over the saved 102-activity club input.

The default command writes a zero-cost preflight. Live execution requires the
literal ``--execute`` flag, ``OPENAI_API_KEY``, and one finite US$0.20 start
authorization. The baseline receives the same compact input and strict output
schema as the saved bounded WAKE memory, but receives no deterministic tools.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import longitudinal_pilot
import post_regatta_memory
from run_baseline import read_json, sha256_json, write_json


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_SCHEMA_PATH = ROOT / "schemas" / "longitudinal-intelligence-output.schema.json"
CONTRACT_PATH = (
    ROOT
    / "evaluation"
    / "post-regatta-baseline"
    / "v1"
    / "capability-contract.json"
)
DEFAULT_OUTPUT = (
    ROOT / "evaluation" / "post-regatta-baseline" / "v1" / "preflight"
)


def _sha256_path(path: Path) -> str:
    return longitudinal_pilot.sha256_path(path)


def load_capability_contract() -> dict:
    return read_json(CONTRACT_PATH)


def write_baseline_dry_run(output_dir: Path) -> Path:
    summary = post_regatta_memory.build_memory_summary()
    output_schema = read_json(OUTPUT_SCHEMA_PATH)
    contract = load_capability_contract()
    if contract["input_sha256"] != sha256_json(summary):
        raise ValueError("Capability contract does not match the current frozen input.")

    input_path = output_dir / "inputs" / "club-post-regatta-memory.json"
    request_path = (
        output_dir
        / "requests"
        / "club-post-regatta-memory.direct_baseline.json"
    )
    contract_path = output_dir / "capability-contract.json"
    write_json(input_path, summary)
    write_json(
        request_path,
        longitudinal_pilot.build_baseline_request(summary, output_schema),
    )
    write_json(contract_path, contract)

    manifest_path = output_dir / "dry-run-manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": "wake.post_regatta_baseline_dry_run.v1",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "api_called": False,
            "request_count": 1,
            "input": {
                "path": str(input_path.relative_to(output_dir)),
                "sha256": _sha256_path(input_path),
                "semantic_sha256": sha256_json(summary),
            },
            "request": {
                "workflow": "DIRECT_BASELINE",
                "path": str(request_path.relative_to(output_dir)),
                "sha256": _sha256_path(request_path),
            },
            "capability_contract": {
                "path": str(contract_path.relative_to(output_dir)),
                "sha256": _sha256_path(contract_path),
                "evaluation_type": "NON_SCORED_CAPABILITY_AUDIT",
            },
            "authorization": {
                "required_total_usd": longitudinal_pilot.required_authorization_usd(1),
                "provider_cap": False,
                "authorized": False,
            },
            "saved_reports": {"count": 0, "reopen_cost_usd": 0},
            "boundary": (
                "The preflight contains no model output. The direct baseline receives "
                "the same compact input and output schema as the saved WAKE memory, "
                "without tools. The capability contract was frozen before execution."
            ),
        },
    )
    return manifest_path


def verify_baseline_directory(directory: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = directory / "dry-run-manifest.json"
    if not manifest_path.exists():
        return ["Missing dry-run manifest."]
    manifest = read_json(manifest_path)
    for field in ("input", "request", "capability_contract"):
        artifact = manifest[field]
        path = directory / artifact["path"]
        if not path.exists():
            errors.append(f"Missing {field} artifact: {artifact['path']}")
        elif _sha256_path(path) != artifact["sha256"]:
            errors.append(f"{field.replace('_', ' ').title()} hash does not match the frozen manifest.")

    input_path = directory / manifest["input"]["path"]
    request_path = directory / manifest["request"]["path"]
    contract_path = directory / manifest["capability_contract"]["path"]
    if input_path.exists() and contract_path.exists():
        summary = read_json(input_path)
        contract = read_json(contract_path)
        if manifest["input"].get("semantic_sha256") != sha256_json(summary):
            errors.append("Input semantic hash does not match the frozen summary.")
        if contract.get("input_sha256") != sha256_json(summary):
            errors.append("Capability contract input hash does not match the frozen summary.")
    if request_path.exists():
        request = read_json(request_path)
        if request.get("store") is not False:
            errors.append("Frozen baseline request must use store:false.")
        if "tools" in request or "tool_choice" in request:
            errors.append("Direct baseline request must not receive tools.")
    return errors


def execute_baseline(output_dir: Path, authorized_cost_usd: float) -> Path:
    longitudinal_pilot.validate_authorization(authorized_cost_usd, 1)
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required with --execute.")
    try:
        from openai import OpenAI
    except ImportError as error:
        raise SystemExit("Missing dependency 'openai'. Run 'uv sync'.") from error

    summary = post_regatta_memory.build_memory_summary()
    contract = load_capability_contract()
    if contract["input_sha256"] != sha256_json(summary):
        raise ValueError("Capability contract does not match the current frozen input.")
    result = longitudinal_pilot.run_baseline_case(
        client=OpenAI(),
        summary=summary,
        output_schema=read_json(OUTPUT_SCHEMA_PATH),
        output_dir=output_dir,
    )
    artifact = result["artifact"]
    run_manifest = output_dir / "run-manifest.json"
    write_json(
        run_manifest,
        {
            "schema_version": "wake.post_regatta_baseline_run.v1",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "api_called": True,
            "workflow": "DIRECT_BASELINE",
            "store": False,
            "authorized_cost_usd": authorized_cost_usd,
            "authorization_is_provider_cap": False,
            "execution_count": 1,
            "total_approximate_cost_usd": artifact["observability"]["approximate_cost_usd"],
            "input_sha256": sha256_json(summary),
            "capability_contract_sha256": _sha256_path(CONTRACT_PATH),
            "report": str(result["artifact_path"].relative_to(output_dir)),
            "verification": artifact["verification"],
            "reopen_cost_usd": 0,
        },
    )
    return run_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--authorized-cost-usd", type=float, default=0.0)
    args = parser.parse_args()

    if not args.execute:
        manifest = write_baseline_dry_run(args.output)
        errors = verify_baseline_directory(args.output)
        if errors:
            raise SystemExit("; ".join(errors))
        print(
            json.dumps(
                {
                    "status": "READY_FOR_AUTHORIZATION",
                    "api_called": False,
                    "required_authorization_usd": 0.2,
                    "manifest": str(manifest),
                },
                indent=2,
            )
        )
        return
    manifest = execute_baseline(args.output, args.authorized_cost_usd)
    print(
        json.dumps(
            {"status": "COMPLETED", "api_called": True, "manifest": str(manifest)},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
