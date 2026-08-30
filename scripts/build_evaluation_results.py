#!/usr/bin/env python3
"""Build the public, read-only web summary from official evaluation artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_RUN = Path("evaluation/runs/expanded-evaluation-v2/official-20260830")
CLUB_BASELINE_RUN = Path("evaluation/runs/post-regatta-baseline-v1-20260830")
DEFAULT_OUTPUT = ROOT / "web/app/lib/evaluation-results.mjs"

DIMENSION_LABELS = {
    "plan_interpretation": "Plan interpretation",
    "session_association_and_alignment": "Session association and alignment",
    "segment_reconstruction": "Segment reconstruction",
    "metric_level_source_trust": "Metric-level source trust",
    "deviation_detection": "Deviation detection",
    "environmental_interpretation": "Environmental interpretation",
    "evidence_and_abstention": "Evidence and abstention",
    "follow_up_questions": "Follow-up questions",
}

CASE_SCENARIOS = {
    "case-001-misaligned-double-scull": "Tests whether route agreement can associate recordings despite conflicting device clocks.",
    "case-002-wind-shift-plan-deviation": "Tests plan reconstruction, a wind shift, a low-SPM deviation, and unusable mobile SPM.",
    "case-003-calm-expert-compliant": "Tests a calm, compliant session without inventing a deviation.",
    "case-004-steady-headwind-compliant": "Tests compliant execution under steady headwind without penalizing the athlete.",
    "case-005-tailwind-fast-not-improvement": "Tests whether tailwind-assisted speed is kept separate from athlete improvement.",
    "case-006-crosswind-gusts": "Tests crosswind and gust context without unsupported causal claims.",
    "case-007-incomplete-intervals": "Tests detection of one missing planned work interval.",
    "case-008-correct-distance-wrong-spm": "Tests a low-SPM work interval despite correct total distance.",
    "case-009-excess-recovery": "Tests detection of recovery that exceeded the plan.",
    "case-010-mobile-spm-zero": "Tests rejection of mobile SPM stuck at zero while SpeedCoach remains usable.",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def case_label(case_id: str) -> str:
    return case_id.split("-", 2)[-1].replace("-", " ").capitalize()


def build_evaluation_results(root: Path = ROOT) -> dict:
    run_dir = root / OFFICIAL_RUN
    baseline_report = read_json(run_dir / "baseline/grade-report-v1.2.json")
    agent_report = read_json(run_dir / "agent/grade-report-v1.2.json")
    baseline_manifest = read_json(run_dir / "baseline/run-manifest.json")
    agent_manifest = read_json(run_dir / "agent/run-manifest.json")
    registry = read_json(root / "evaluation/cases-v2.json")

    provenance = {
        item["case_id"]: item["provenance"]
        for item in registry["cases"]
        if item["status"] == "IMPLEMENTED"
    }
    baseline_cases = {item["case_id"]: item for item in baseline_report["cases"]}
    agent_cases = {item["case_id"]: item for item in agent_report["cases"]}
    case_ids = [item["case_id"] for item in agent_report["cases"]]

    cases = []
    for case_id in case_ids:
        baseline_score = baseline_cases[case_id]["score"]
        wake_score = agent_cases[case_id]["score"]
        baseline_dimensions = {
            item["dimension"]: item
            for item in baseline_cases[case_id]["dimensions"]
        }
        case_dimensions = []
        for wake_dimension in agent_cases[case_id]["dimensions"]:
            dimension = wake_dimension["dimension"]
            baseline_dimension = baseline_dimensions[dimension]
            dimension_baseline_score = round(100 * baseline_dimension["score_ratio"], 2)
            dimension_wake_score = round(100 * wake_dimension["score_ratio"], 2)
            case_dimensions.append(
                {
                    "dimension": dimension,
                    "label": DIMENSION_LABELS[dimension],
                    "baseline_score": dimension_baseline_score,
                    "wake_score": dimension_wake_score,
                    "delta": round(dimension_wake_score - dimension_baseline_score, 2),
                }
            )
        cases.append(
            {
                "case_id": case_id,
                "short_id": case_id.split("-", 2)[1],
                "label": case_label(case_id),
                "scenario": CASE_SCENARIOS[case_id],
                "provenance": provenance[case_id],
                "baseline_score": baseline_score,
                "wake_score": wake_score,
                "delta": round(wake_score - baseline_score, 2),
                "dimensions": case_dimensions,
            }
        )

    dimensions = []
    for dimension, wake_score in agent_report["dimension_macro_average_percent"].items():
        baseline_score = baseline_report["dimension_macro_average_percent"][dimension]
        delta = round(wake_score - baseline_score, 2)
        dimensions.append(
            {
                "dimension": dimension,
                "label": DIMENSION_LABELS[dimension],
                "baseline_score": baseline_score,
                "wake_score": wake_score,
                "delta": delta,
                "regression": delta < 0,
            }
        )

    trajectories = [
        read_json(path)
        for path in sorted((run_dir / "agent/trajectories").glob("*.json"))
    ]
    tool_calls = sum(
        event["type"] == "TOOL_CALL"
        for trajectory in trajectories
        for event in trajectory["events"]
    )
    verifier_retries = sum(
        event["type"] == "RETRY_REQUESTED"
        for trajectory in trajectories
        for event in trajectory["events"]
    )
    baseline_case_manifests = [
        read_json(path)
        for path in sorted((run_dir / "baseline/cases").glob("*.json"))
    ]
    club_audit = read_json(root / CLUB_BASELINE_RUN / "capability-audit.json")
    club_validity_review = read_json(
        root / CLUB_BASELINE_RUN / "construct-validity-review.json"
    )

    baseline_score = baseline_report["macro_average_score"]
    wake_score = agent_report["macro_average_score"]
    absolute_gain = round(wake_score - baseline_score, 2)
    baseline_cost = baseline_manifest["approximate_total_cost_usd"]
    wake_cost = agent_manifest["approximate_total_cost_usd"]

    return {
        "schema_version": "wake.evaluation_results.v1",
        "run_id": "official-20260830",
        "comparison": {
            "case_count": len(cases),
            "baseline_score": baseline_score,
            "wake_score": wake_score,
            "absolute_gain": absolute_gain,
            "relative_gain_percent": round(100 * absolute_gain / baseline_score, 2),
            "all_cases_improved": all(item["delta"] > 0 for item in cases),
        },
        "cost": {
            "baseline_usd": baseline_cost,
            "wake_usd": wake_cost,
            "incremental_agent_usd": round(wake_cost - baseline_cost, 6),
            "total_usd": round(wake_cost + baseline_cost, 6),
        },
        "usage": {
            "baseline_tokens": baseline_manifest["total_usage"]["total_tokens"],
            "wake_tokens": agent_manifest["total_usage"]["total_tokens"],
            "baseline_runtime_seconds": round(
                sum(item["runtime_ms"] for item in baseline_case_manifests) / 1000,
                3,
            ),
            "wake_runtime_seconds": round(agent_manifest["runtime_ms"] / 1000, 3),
        },
        "agent_observability": {
            "trajectory_count": len(trajectories),
            "tool_calls": tool_calls,
            "verifier_retries": verifier_retries,
            "all_final_outputs_verified": all(
                item["verification"]["passed"] for item in trajectories
            ),
            "private_chain_of_thought_stored": any(
                item["private_chain_of_thought_stored"] for item in trajectories
            ),
        },
        "club_memory_comparison": {
            "evaluation_type": club_audit["evaluation_type"],
            "baseline": {
                "passed_count": club_audit["baseline"]["passed_count"],
                "check_count": club_audit["baseline"]["check_count"],
                "cost_usd": club_audit["baseline"]["observability"][
                    "approximate_cost_usd"
                ],
                "tokens": club_audit["baseline"]["observability"]["usage"][
                    "total_tokens"
                ],
                "runtime_seconds": round(
                    club_audit["baseline"]["observability"]["runtime_ms"] / 1000,
                    3,
                ),
            },
            "wake": {
                "passed_count": club_audit["wake"]["passed_count"],
                "check_count": club_audit["wake"]["check_count"],
                "cost_usd": club_audit["wake"]["observability"][
                    "approximate_cost_usd"
                ],
                "tokens": club_audit["wake"]["observability"]["usage"][
                    "total_tokens"
                ],
                "runtime_seconds": round(
                    club_audit["wake"]["observability"]["runtime_ms"] / 1000,
                    3,
                ),
            },
            "accepted_claim": club_validity_review["decision"].removeprefix(
                "ACCEPT_"
            ),
            "semantic_quality_gain": club_validity_review["accepted_claims"][
                "semantic_coaching_quality_gain"
            ],
            "reopen_cost_usd": 0,
            "review_note": club_validity_review["review_note"],
        },
        "cases": cases,
        "dimensions": dimensions,
        "boundaries": [
            "Fixed-case agent-versus-direct-model evidence, not a human-coach comparison.",
            "One real anonymized case and nine synthetic or derived-synthetic cases.",
            "No claim of improved athletic performance or broad club generalization.",
            "Saved outputs can be reviewed and regraded without another model call.",
        ],
    }


def write_evaluation_results(root: Path, output_path: Path) -> None:
    result = build_evaluation_results(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    module = (
        "// Generated by scripts/build_evaluation_results.py. Do not edit by hand.\n"
        "export const evaluationResults = "
        + json.dumps(result, indent=2, ensure_ascii=False)
        + ";\n"
    )
    output_path.write_text(module, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    write_evaluation_results(ROOT, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
