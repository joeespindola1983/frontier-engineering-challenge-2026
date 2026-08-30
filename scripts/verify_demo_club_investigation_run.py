#!/usr/bin/env python3
"""Verify the preserved paid demo-club candidate investigations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ROOT = ROOT / "evaluation" / "runs" / "demo-club-investigations-v1-20260830"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_artifact(run_root: Path, relative: str) -> Path:
    path = (run_root / relative).resolve()
    runs_root = (ROOT / "evaluation" / "runs").resolve()
    assert path.is_relative_to(runs_root), f"Artifact escapes evaluation runs: {relative}"
    return path


def verify_run(run_root: Path = DEFAULT_RUN_ROOT) -> dict:
    manifest = read_json(run_root / "run-manifest.json")
    assert manifest["schema_version"] == "wake.demo_club_investigation_run.v1"
    assert manifest["authorization"] == {
        "execution_count": 2,
        "authorized_cost_usd_per_execution": 0.2,
        "hard_provider_cap": False,
        "owner_authorized": True,
    }
    assert manifest["longitudinal_synthesis"] == {
        "status": "NOT_EXECUTED",
        "authorized": False,
    }
    output_schema = read_json(ROOT / "schemas" / "analysis-output.schema.json")
    results = {}
    input_tokens = output_tokens = total_tokens = runtime_ms = 0
    total_cost = 0.0

    for execution in manifest["executions"]:
        output_path = resolve_artifact(run_root, execution["output_path"])
        trajectory_path = resolve_artifact(run_root, execution["trajectory_path"])
        assert sha256(output_path) == execution["output_sha256"]
        assert sha256(trajectory_path) == execution["trajectory_sha256"]
        output = read_json(output_path)
        trajectory = read_json(trajectory_path)
        jsonschema.validate(output, output_schema)
        assert output["case_id"] == execution["case_id"] == trajectory["case_id"]
        assert trajectory["workflow"] == manifest["workflow"]
        assert trajectory["model"] == manifest["model"]
        assert trajectory["verification"]["passed"] is True
        assert trajectory["verification"]["errors"] == []
        assert trajectory["private_chain_of_thought_stored"] is False
        assert trajectory["approximate_cost_usd"] == execution["approximate_cost_usd"]
        assert trajectory["runtime_ms"] == execution["runtime_ms"]
        assert trajectory["usage"] == execution["usage"]
        assert execution["approximate_cost_usd"] <= execution["authorized_cost_usd"]

        actual_deviations = [
            {"segment_ref": item["segment_ref"], "type": item["type"]}
            for item in output["deviations"]
        ]
        assert actual_deviations == execution["expected_deviations"]
        results[execution["case_id"]] = {
            "deviation_segments": [item["segment_ref"] for item in actual_deviations],
            "deviation_types": [item["type"] for item in actual_deviations],
            "verification_passed": True,
        }
        input_tokens += execution["usage"]["input_tokens"]
        output_tokens += execution["usage"]["output_tokens"]
        total_tokens += execution["usage"]["total_tokens"]
        runtime_ms += execution["runtime_ms"]
        total_cost += execution["approximate_cost_usd"]

    totals = manifest["totals"]
    assert totals["execution_count"] == len(manifest["executions"])
    assert totals["input_tokens"] == input_tokens
    assert totals["output_tokens"] == output_tokens
    assert totals["total_tokens"] == total_tokens
    assert totals["runtime_ms"] == runtime_ms
    assert totals["approximate_cost_usd"] == round(total_cost, 6)
    return {
        "status": "verified",
        "execution_count": totals["execution_count"],
        "approximate_total_cost_usd": totals["approximate_cost_usd"],
        "total_tokens": totals["total_tokens"],
        "results": results,
    }


def main() -> None:
    print(json.dumps(verify_run(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
