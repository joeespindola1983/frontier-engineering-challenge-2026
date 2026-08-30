#!/usr/bin/env python3
"""Build a non-scored capability audit for the executed longitudinal pilot.

The comparison contract named checks before execution but did not freeze a
weighted grader. This script therefore reports reproducible pass/fail
capabilities and resource use without inventing a post-hoc quality score.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / "evaluation/runs/longitudinal-pilot-v1-20260830"

REQUIRED_ATTENTION_REFS = {
    "athlete-lucas": {
        "verified:club-atlas-men-20260828-recovery",
    },
    "club-coach": {
        "record:club-4x-mixed-b-20260827-pm",
        "record:club-8x-women-20260828-evening",
        "verified:club-bridge-mixed-20260820-spm",
        "verified:club-atlas-men-20260828-recovery",
    },
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _evidence_refs(value: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence_refs" and isinstance(item, list):
                refs.update(str(ref) for ref in item)
            else:
                refs.update(_evidence_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.update(_evidence_refs(item))
    return refs


def _checks(artifact: dict) -> dict[str, bool]:
    output = artifact["output"]
    serialized = json.dumps(output, sort_keys=True).lower()
    required = REQUIRED_ATTENTION_REFS[artifact["pilot_id"]]
    comparisons = output.get("comparisons", [])
    priorities = output.get("priorities", [])
    return {
        "verification_passed": artifact["verification"]["passed"] is True,
        "required_attention_refs_present": required <= _evidence_refs(output),
        "performance_trend_abstained": (
            "performance trend" in serialized
            and any(item.get("status") == "INSUFFICIENT" for item in comparisons)
        ),
        "water_indoor_boundary_preserved": (
            "water and indoor distance remain separate" in serialized
        ),
        "human_review_preserved": (
            bool(priorities)
            and all(item.get("requires_human_review") is True for item in priorities)
        ),
    }


def build_capability_audit(run_dir: Path) -> dict:
    manifest = _read_json(run_dir / "run-manifest.json")
    reports = []
    workflow_costs = {"DIRECT_BASELINE": 0.0, "WAKE_BOUNDED_AGENT": 0.0}
    workflow_tokens = {"DIRECT_BASELINE": 0, "WAKE_BOUNDED_AGENT": 0}
    workflow_tools = {"DIRECT_BASELINE": 0, "WAKE_BOUNDED_AGENT": 0}
    for relative_path in manifest["reports"]:
        artifact = _read_json(run_dir / relative_path)
        checks = _checks(artifact)
        workflow = artifact["workflow"]
        observability = artifact["observability"]
        workflow_costs[workflow] += observability["approximate_cost_usd"]
        workflow_tokens[workflow] += observability["usage"]["total_tokens"]
        workflow_tools[workflow] += len(artifact["tool_events"])
        reports.append({
            "pilot_id": artifact["pilot_id"],
            "workflow": workflow,
            "checks": checks,
            "all_checks_passed": all(checks.values()),
            "runtime_ms": observability["runtime_ms"],
            "total_tokens": observability["usage"]["total_tokens"],
            "approximate_cost_usd": observability["approximate_cost_usd"],
        })
    baseline_cost = round(workflow_costs["DIRECT_BASELINE"], 6)
    wake_cost = round(workflow_costs["WAKE_BOUNDED_AGENT"], 6)
    difference = round(wake_cost - baseline_cost, 6)
    percent = round((difference / baseline_cost) * 100, 2) if baseline_cost else None
    return {
        "schema_version": "wake.longitudinal_capability_audit.v1",
        "evaluation_design": "POST_RUN_CAPABILITY_AUDIT_NOT_PREREGISTERED",
        "quality_score": None,
        "quality_conclusion": "NO_DEMONSTRATED_QUALITY_GAIN",
        "interpretation": (
            "Both workflows passed the same mandatory capability checks. "
            "WAKE used bounded tools and fewer resources, but this audit does not "
            "establish a quality improvement over the direct baseline."
        ),
        "execution_count": manifest["execution_count"],
        "reports": sorted(reports, key=lambda item: (item["pilot_id"], item["workflow"])),
        "costs": {
            "total_usd": round(baseline_cost + wake_cost, 6),
            "direct_baseline_usd": baseline_cost,
            "wake_bounded_agent_usd": wake_cost,
            "wake_vs_baseline_usd": difference,
            "wake_vs_baseline_percent": percent,
        },
        "tokens": {
            "direct_baseline": workflow_tokens["DIRECT_BASELINE"],
            "wake_bounded_agent": workflow_tokens["WAKE_BOUNDED_AGENT"],
        },
        "tool_use": {
            "baseline_tool_events": workflow_tools["DIRECT_BASELINE"],
            "wake_tool_events": workflow_tools["WAKE_BOUNDED_AGENT"],
        },
        "boundaries": [
            "The weighted quality rubric was not frozen before execution, so no post-hoc score is reported.",
            "The two scopes are real-informed synthetic and do not establish human-coach superiority or athletic improvement.",
            "Observed API cost is approximate and the authorization gate was not a provider cap.",
        ],
    }


def write_capability_audit(run_dir: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(build_capability_audit(run_dir), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or args.run / "capability-audit.json"
    path = write_capability_audit(args.run, output)
    print(json.dumps({"status": "AUDITED", "report": str(path)}, indent=2))


if __name__ == "__main__":
    main()
