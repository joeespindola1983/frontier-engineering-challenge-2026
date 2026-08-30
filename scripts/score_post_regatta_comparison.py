#!/usr/bin/env python3
"""Audit direct-baseline and WAKE coverage against the frozen club contract.

This is deliberately a non-scored capability audit. It reports which explicit
checks each verified structured output covers and preserves neutral or adverse
results without introducing post-hoc weights.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import longitudinal_pilot
import post_regatta_baseline
import post_regatta_memory
from run_baseline import read_json, write_json


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_SCHEMA_PATH = ROOT / "schemas" / "longitudinal-intelligence-output.schema.json"
DEFAULT_WAKE_ARTIFACT = (
    ROOT
    / "evaluation"
    / "runs"
    / "post-regatta-memory-v1-20260830"
    / "reports"
    / "club-post-regatta-memory.wake_bounded_agent.json"
)


def _refs(items: list[dict]) -> set[str]:
    return {
        str(reference)
        for item in items
        for reference in item.get("evidence_refs", [])
    }


def _check_result(check_id: str, passed: bool, detail: str) -> dict:
    return {"check_id": check_id, "passed": passed, "detail": detail}


def evaluate_artifact(artifact: dict, contract: dict) -> dict:
    output = artifact["output"]
    comparisons = {
        item["comparison_id"]: item for item in output.get("comparisons", [])
    }
    priorities = output.get("priorities", [])
    questions = output.get("unresolved_questions", [])
    recommendations = output.get("recommendations", [])
    checks_by_id = {check["check_id"]: check for check in contract["checks"]}
    results: list[dict] = []

    check = checks_by_id["supported_comparisons"]
    supported_pass = all(
        comparisons.get(comparison_id, {}).get("status") == check["expected_status"]
        for comparison_id in check["expected_comparison_ids"]
    )
    results.append(_check_result(
        check["check_id"],
        supported_pass,
        "All three deterministic supported comparison IDs retain SUPPORTED status."
        if supported_pass
        else "One or more deterministic supported comparisons are missing or not SUPPORTED.",
    ))

    check = checks_by_id["club_trend_abstention"]
    trend = comparisons.get(check["expected_comparison_id"], {})
    trend_pass = trend.get("status") == check["expected_status"]
    results.append(_check_result(
        check["check_id"],
        trend_pass,
        "Club trend comparison explicitly remains INSUFFICIENT."
        if trend_pass
        else "Club trend abstention is missing or does not remain INSUFFICIENT.",
    ))

    check = checks_by_id["environmental_noncausality"]
    environment = comparisons.get(check["expected_comparison_id"], {})
    environment_text = json.dumps(environment, sort_keys=True).lower()
    environmental_pass = (
        environment.get("status") == check["expected_status"]
        and any(term in environment_text for term in ("caus", "attribut"))
    )
    results.append(_check_result(
        check["check_id"],
        environmental_pass,
        "Atlas water comparison remains insufficient and states the causal/attribution boundary."
        if environmental_pass
        else "Atlas water comparison is missing the insufficient or non-causal boundary.",
    ))

    check = checks_by_id["missing_context_priorities"]
    missing_priority_refs = set(check["expected_evidence_refs"]) - _refs(priorities)
    results.append(_check_result(
        check["check_id"],
        not missing_priority_refs,
        "Every frozen missing-context route appears in the priority queue."
        if not missing_priority_refs
        else f"Priority queue is missing evidence refs: {sorted(missing_priority_refs)}",
    ))

    check = checks_by_id["unresolved_human_questions"]
    missing_question_refs = set(check["expected_evidence_refs"]) - _refs(questions)
    results.append(_check_result(
        check["check_id"],
        not missing_question_refs,
        "Every frozen unresolved route appears in a human/source question."
        if not missing_question_refs
        else f"Question queue is missing evidence refs: {sorted(missing_question_refs)}",
    ))

    check = checks_by_id["verified_deviation_review"]
    missing_deviation_refs = set(check["expected_evidence_refs"]) - _refs(recommendations)
    results.append(_check_result(
        check["check_id"],
        not missing_deviation_refs,
        "Both verification-passed deviations are routed through recommendations."
        if not missing_deviation_refs
        else f"Recommendations are missing verified refs: {sorted(missing_deviation_refs)}",
    ))

    summary = post_regatta_memory.build_memory_summary()
    schema = read_json(OUTPUT_SCHEMA_PATH)
    verifier_errors = longitudinal_pilot.verify_longitudinal_output(
        output=output,
        output_schema=schema,
        summary=summary,
    )
    boundary_pass = (
        not verifier_errors
        and bool(output.get("boundaries"))
        and all(priority.get("requires_human_review") is True for priority in priorities)
        and artifact.get("input_sha256") == contract["input_sha256"]
    )
    results.append(_check_result(
        "evidence_and_human_review_boundary",
        boundary_pass,
        "Strict verifier, frozen input hash, explicit boundaries, and human review all pass."
        if boundary_pass
        else f"Boundary verification failed: {verifier_errors or ['input hash or human review mismatch']}",
    ))

    passed_count = sum(item["passed"] for item in results)
    return {
        "workflow": artifact["workflow"],
        "input_sha256": artifact["input_sha256"],
        "check_count": len(results),
        "passed_count": passed_count,
        "all_passed": passed_count == len(results),
        "checks": results,
        "observability": artifact.get("observability", {}),
    }


def build_comparison_report(
    *, baseline_artifact: dict, wake_artifact: dict, contract: dict
) -> dict:
    baseline = evaluate_artifact(baseline_artifact, contract)
    wake = evaluate_artifact(wake_artifact, contract)
    baseline_passed = {item["check_id"] for item in baseline["checks"] if item["passed"]}
    wake_passed = {item["check_id"] for item in wake["checks"] if item["passed"]}
    if baseline_passed == wake_passed:
        conclusion = "NO_DEMONSTRATED_CAPABILITY_GAIN"
    elif wake_passed > baseline_passed:
        conclusion = "DEMONSTRATED_CAPABILITY_COVERAGE_GAIN"
    elif baseline_passed > wake_passed:
        conclusion = "WAKE_CAPABILITY_COVERAGE_REGRESSION"
    else:
        conclusion = "MIXED_CAPABILITY_RESULT"
    return {
        "schema_version": "wake.post_regatta_comparison_audit.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "evaluation_type": contract["evaluation_type"],
        "contract_sha256": post_regatta_baseline._sha256_path(
            post_regatta_baseline.CONTRACT_PATH
        ),
        "input_sha256": contract["input_sha256"],
        "baseline": baseline,
        "wake": wake,
        "conclusion": conclusion,
        "boundary": contract["boundary"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-artifact", type=Path, required=True)
    parser.add_argument("--wake-artifact", type=Path, default=DEFAULT_WAKE_ARTIFACT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_comparison_report(
        baseline_artifact=read_json(args.baseline_artifact),
        wake_artifact=read_json(args.wake_artifact),
        contract=post_regatta_baseline.load_capability_contract(),
    )
    write_json(args.output, report)
    print(json.dumps({
        "status": "AUDITED",
        "conclusion": report["conclusion"],
        "output": str(args.output),
    }, indent=2))


if __name__ == "__main__":
    main()
