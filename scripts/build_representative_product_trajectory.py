#!/usr/bin/env python3
"""Build or verify the public end-to-end replay trajectory with human gates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path("evaluation/trajectories/representative-product-replay-v1.json")
CASE_ID = "case-002-wind-shift-plan-deviation"
QUESTION = "Was the resistance band used for repetitions 1–3 and removed before repetition 4?"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(root: Path, relative_path: str) -> dict[str, str]:
    path = root / relative_path
    if not path.is_file():
        raise FileNotFoundError(path)
    return {"path": relative_path, "sha256": _sha256(path)}


def build_trajectory(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    source_paths = [
        f"data/fixtures/{CASE_ID}/input/plan.json",
        f"data/fixtures/{CASE_ID}/input/speedcoach.csv",
        f"data/fixtures/{CASE_ID}/input/mobile.csv",
        f"data/fixtures/{CASE_ID}/input/environment.json",
        f"data/fixtures/{CASE_ID}/input/context.json",
    ]
    sources = [_artifact(root, path) for path in source_paths]
    prompt = _artifact(root, "prompts/wake-agent-v2.md")
    agent_output = _artifact(
        root,
        "evaluation/runs/expanded-evaluation-v2/official-20260830/agent/outputs/"
        f"{CASE_ID}.json",
    )
    agent_trajectory = _artifact(
        root,
        "evaluation/runs/expanded-evaluation-v2/official-20260830/agent/trajectories/"
        f"{CASE_ID}.trajectory.json",
    )

    return {
        "schema_version": "wake.representative_product_trajectory.v1",
        "trajectory_id": "representative-product-replay-v1",
        "trajectory_type": "REPRESENTATIVE_REPLAY",
        "case_id": CASE_ID,
        "provenance": "PUBLIC_SYNTHETIC",
        "model_called": False,
        "approximate_cost_usd": 0.0,
        "private_chain_of_thought_stored": False,
        "agent_instructions": prompt,
        "agent_tool_trace": agent_trajectory,
        "events": [
            {
                "sequence": 1,
                "type": "SOURCES_SELECTED",
                "actor": "ATHLETE",
                "sources": sources,
                "note": "Uploader identity remains separate from source authority.",
            },
            {
                "sequence": 2,
                "type": "BUNDLE_PREPARED",
                "actor": "DETERMINISTIC_RUNTIME",
                "core_sources": ["PLAN", "SPEEDCOACH"],
                "optional_sources": ["MOBILE", "ENVIRONMENT", "CONTEXT"],
                "agent_called": False,
            },
            {
                "sequence": 3,
                "type": "AGENT_RESULT_REPLAYED",
                "actor": "WAKE_RUNTIME",
                "output": agent_output,
                "tool_actions_and_responses": agent_trajectory,
                "verification_passed": True,
                "new_model_call": False,
            },
            {
                "sequence": 4,
                "type": "COACH_VIEWED",
                "actor": "COACH",
                "changes_evidence": False,
            },
            {
                "sequence": 5,
                "type": "HUMAN_CHECKPOINT_REQUESTED",
                "actor": "WAKE_RUNTIME",
                "question": QUESTION,
                "expected_respondent_role": "ATHLETE",
                "reason": "Equipment use is not observable in supplied telemetry.",
            },
            {
                "sequence": 6,
                "type": "HUMAN_CHECKPOINT_ANSWERED",
                "actor": "COACH",
                "answer": "YES",
                "answered_by_role": "ATHLETE",
                "recorded_by_role": "COACH",
                "authority_basis": "RELAYED_REPORT",
                "matches_expected_respondent": True,
                "effect_on_telemetry": "NONE",
                "note": "Synthetic representative answer adds human context only.",
            },
            {
                "sequence": 7,
                "type": "BRIEFING_VERIFIED",
                "actor": "DETERMINISTIC_RUNTIME",
                "verification_passed": True,
                "evidence_boundary_preserved": True,
            },
            {
                "sequence": 8,
                "type": "MEMORY_APPROVAL_REQUESTED",
                "actor": "WAKE_RUNTIME",
                "required_role": "COACH",
                "memory_changed": False,
            },
            {
                "sequence": 9,
                "type": "COACH_APPROVED_MEMORY",
                "actor": "COACH",
                "memory_changed": True,
                "new_model_call": False,
            },
        ],
        "limitations": [
            "This is a deterministic replay of a public synthetic workflow, not a new model execution.",
            "The representative human answer is synthetic and does not convert telemetry into observed equipment evidence.",
            "Production authentication, verified identity, encryption, tenancy, and durable cloud storage are not implemented.",
        ],
    }


def _serialized(root: Path) -> str:
    return json.dumps(build_trajectory(root), indent=2, sort_keys=True) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help=f"Write the deterministic artifact to {OUTPUT}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    artifact_path = ROOT / OUTPUT
    expected = _serialized(ROOT)
    if args.write:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(expected, encoding="utf-8")
        print(f"Representative product trajectory written: {artifact_path}")
        return 0

    if not artifact_path.is_file():
        print(f"Missing representative product trajectory: {artifact_path}")
        return 1
    if artifact_path.read_text(encoding="utf-8") != expected:
        print(f"Representative product trajectory is stale: {artifact_path}")
        return 1
    print("Representative product trajectory verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
