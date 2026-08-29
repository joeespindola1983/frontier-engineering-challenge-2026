#!/usr/bin/env python3
"""Build a condition-aware capability report for one WAKE ablation run."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

from run_baseline import read_json, sha256_path, write_json
from run_evidence_ablation import (
    CONDITION_ORDER,
    DEFAULT_INPUTS,
    ROOT,
    load_experiment,
)
from wake_agent import DEFAULT_SCHEMA, output_evidence_refs, verify_output


GROUND_TRUTH = (
    ROOT
    / "data/fixtures/case-002-wind-shift-plan-deviation/ground-truth.json"
)
MARGINAL_CAPABILITIES = {
    "context-environment": ["ENVIRONMENT_ASSOCIATION", "HUMAN_CONTEXT_BOUNDARY"],
    "full": ["SESSION_CORROBORATION", "MOBILE_CONFLICT_DETECTION"],
}


def normalized(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(character for character in text if not unicodedata.combining(character))
    return re.sub(r"\s+", " ", text.lower()).strip()


def policy_by_metric(output: dict) -> dict[str, dict]:
    return {
        policy.get("metric", ""): policy
        for policy in output.get("source_policy", [])
        if policy.get("metric")
    }


def contains_all(text: str, terms: tuple[str, ...]) -> bool:
    value = normalized(text)
    return all(term in value for term in terms)


def _common_checks(output: dict, summary: dict) -> dict[str, tuple[bool, str]]:
    verification = verify_output(
        output=output,
        output_schema=read_json(DEFAULT_SCHEMA),
        summary=summary,
    )
    plan = output.get("plan_summary") or {}
    work_segments = [
        segment for segment in output.get("segments", []) if segment.get("kind") == "WORK"
    ]
    deviation_refs = {
        deviation.get("segment_ref") for deviation in output.get("deviations", [])
    }
    policies = policy_by_metric(output)
    speedcoach_id = next(
        source["source_id"]
        for source in summary["sources"]
        if source["kind"] == "SPEEDCOACH"
    )
    questions = " ".join(output.get("follow_up_questions", []))
    abstentions = " ".join(output.get("abstentions", []))
    work_five = next(
        (segment for segment in work_segments if segment.get("segment_id") == "work-05"),
        None,
    )
    return {
        "OUTPUT_VERIFICATION": (
            verification["passed"],
            "Verified schema, identity, provenance, and supported-claim boundaries."
            if verification["passed"]
            else "; ".join(verification["errors"]),
        ),
        "PLAN_RECONSTRUCTION": (
            plan.get("status") in {"PARSED", "PARTIAL"}
            and len(plan.get("prescribed_blocks", [])) >= 2,
            "The two planned work blocks are represented in structured output.",
        ),
        "EXECUTION_RECONSTRUCTION": (
            len(work_segments) == 6
            and work_five is not None
            and work_five.get("average_spm") is not None
            and abs(float(work_five["average_spm"]) - 20.0) <= 1.0,
            "Six work intervals are reconstructed and work five remains near 20 SPM.",
        ),
        "DEVIATION_DETECTION": (
            deviation_refs == {"work-05"},
            "Work five is the only reported plan deviation.",
        ),
        "SPEEDCOACH_SPM_SELECTION": (
            policies.get("stroke_rate_spm", {}).get("selected_source_id")
            == speedcoach_id,
            "SpeedCoach remains the selected SPM source.",
        ),
        "HUMAN_REVIEW_BOUNDARY": (
            "band" in normalized(questions)
            and "band" in normalized(abstentions)
            and (
                "technique" in normalized(abstentions)
                or "synchronization" in normalized(abstentions)
            ),
            "Equipment and visible technique remain human-review questions or abstentions.",
        ),
    }


def _no_mobile_dependency(output: dict) -> tuple[bool, str]:
    refs = output_evidence_refs(output)
    policies = policy_by_metric(output)
    route_reason = policies.get("route", {}).get("reason", "")
    passed = (
        not any("mobile" in reference for reference in refs)
        and not output.get("session_associations")
        and "corrobor" not in normalized(route_reason)
    )
    return passed, "No mobile claim, citation, association, or false corroboration is present."


def _environment_abstention(output: dict) -> tuple[bool, str]:
    assessment = output.get("environment_assessment")
    refs = output_evidence_refs(output)
    passed = (
        assessment is None
        or assessment.get("association") in {"UNKNOWN", "NOT_SUPPORTED"}
    ) and not any("environment" in reference for reference in refs)
    return passed, "Environmental interpretation is withheld when no timeline is supplied."


def _environment_association(output: dict) -> tuple[bool, str]:
    assessment = output.get("environment_assessment") or {}
    passed = (
        assessment.get("association") == "SUPPORTED"
        and any(
            reference == "input/environment.json"
            for reference in assessment.get("evidence_refs", [])
        )
    )
    return passed, "The supplied environmental timeline supports a time-aligned association."


def _noncausal_environment(output: dict) -> tuple[bool, str]:
    assessment = output.get("environment_assessment") or {}
    limitations = " ".join(assessment.get("limitations", []))
    rendered = normalized(json.dumps(output, ensure_ascii=False))
    forbidden = ("wind caused", "caused by wind", "due to wind", "wind explains")
    passed = (
        contains_all(limitations, ("not", "caus"))
        and not any(phrase in rendered for phrase in forbidden)
    )
    return passed, "Environmental evidence is described as association rather than causation."


def _human_context_boundary(output: dict) -> tuple[bool, str]:
    questions = normalized(" ".join(output.get("follow_up_questions", [])))
    abstentions = normalized(" ".join(output.get("abstentions", [])))
    passed = "band" in questions and "band" in abstentions
    return passed, "Unconfirmed equipment use remains a focused human checkpoint."


def _session_corroboration(output: dict, summary: dict) -> tuple[bool, str]:
    source_ids = {source["kind"]: source["source_id"] for source in summary["sources"]}
    expected = {source_ids["SPEEDCOACH"], source_ids["MOBILE"]}
    passed = any(
        association.get("decision") == "MATCH"
        and expected.issubset(set(association.get("source_ids", [])))
        and any("mobile" in ref for ref in association.get("evidence_refs", []))
        for association in output.get("session_associations", [])
    )
    return passed, "Mobile and SpeedCoach are associated through explicit corroborating evidence."


def _mobile_spm_rejection(output: dict, summary: dict) -> tuple[bool, str]:
    policies = policy_by_metric(output)
    spm = policies.get("stroke_rate_spm", {})
    mobile_id = next(
        source["source_id"] for source in summary["sources"] if source["kind"] == "MOBILE"
    )
    reason = normalized(spm.get("reason", ""))
    passed = (
        spm.get("selected_source_id") != mobile_id
        and "mobile" in reason
        and any(term in reason for term in ("zero", "reject", "unusable", "broken"))
    )
    return passed, "Broken mobile SPM is identified and rejected instead of averaged."


def _route_corroboration(output: dict, summary: dict) -> tuple[bool, str]:
    route = policy_by_metric(output).get("route", {})
    speedcoach_id = next(
        source["source_id"]
        for source in summary["sources"]
        if source["kind"] == "SPEEDCOACH"
    )
    reason = normalized(route.get("reason", ""))
    passed = (
        route.get("selected_source_id") == speedcoach_id
        and "mobile" in reason
        and "corrobor" in reason
    )
    return passed, "Mobile GPS corroborates the selected SpeedCoach route."


def score_condition(condition_id: str, output: dict, summary: dict) -> dict:
    checks = _common_checks(output, summary)
    if condition_id == "core":
        checks["NO_MOBILE_DEPENDENCY"] = _no_mobile_dependency(output)
        checks["ENVIRONMENT_ABSTENTION"] = _environment_abstention(output)
    elif condition_id == "context-environment":
        checks["NO_MOBILE_DEPENDENCY"] = _no_mobile_dependency(output)
        checks["ENVIRONMENT_ASSOCIATION"] = _environment_association(output)
        checks["NONCAUSAL_ENVIRONMENT"] = _noncausal_environment(output)
        checks["HUMAN_CONTEXT_BOUNDARY"] = _human_context_boundary(output)
    elif condition_id == "full":
        checks["ENVIRONMENT_ASSOCIATION"] = _environment_association(output)
        checks["NONCAUSAL_ENVIRONMENT"] = _noncausal_environment(output)
        checks["HUMAN_CONTEXT_BOUNDARY"] = _human_context_boundary(output)
        checks["SESSION_CORROBORATION"] = _session_corroboration(output, summary)
        checks["MOBILE_SPM_REJECTION"] = _mobile_spm_rejection(output, summary)
        checks["ROUTE_CORROBORATION"] = _route_corroboration(output, summary)
    else:
        raise ValueError(f"Unknown ablation condition: {condition_id}")

    details = [
        {"check_id": check_id, "passed": passed, "reason": reason}
        for check_id, (passed, reason) in checks.items()
    ]
    failed = [item["check_id"] for item in details if not item["passed"]]
    return {
        "condition_id": condition_id,
        "case_id": summary["case_id"],
        "status": "PASS" if not failed else "FAIL",
        "passed_checks": len(details) - len(failed),
        "applicable_checks": len(details),
        "failed_checks": failed,
        "checks": details,
    }


def _execution_signature(output: dict) -> dict:
    return {
        "segment_ids": [segment.get("segment_id") for segment in output.get("segments", [])],
        "deviation_refs": sorted(
            deviation.get("segment_ref") for deviation in output.get("deviations", [])
        ),
    }


def score_run(run_manifest_path: Path) -> dict:
    run_manifest = read_json(run_manifest_path)
    input_manifest, summaries = load_experiment()
    expected_metadata = run_manifest.get("experiment", {})
    if expected_metadata.get("condition_order") != CONDITION_ORDER:
        raise ValueError("Run manifest does not contain the frozen condition order.")
    if expected_metadata.get("input_manifest_sha256") != sha256_path(
        DEFAULT_INPUTS / "manifest.json"
    ):
        raise ValueError("Run manifest references a different ablation input manifest.")
    expected_cases = [summary["case_id"] for summary in summaries]
    if run_manifest.get("cases") != expected_cases:
        raise ValueError("Run cases do not match the frozen ablation summaries.")

    outputs = []
    conditions = []
    for condition_id, summary in zip(CONDITION_ORDER, summaries, strict=True):
        output_path = run_manifest_path.parent / "outputs" / f"{summary['case_id']}.json"
        output = read_json(output_path)
        outputs.append(output)
        conditions.append(score_condition(condition_id, output, summary))

    signatures = [_execution_signature(output) for output in outputs]
    execution_consistent = all(signature == signatures[0] for signature in signatures[1:])
    marginal = {}
    by_id = {condition["condition_id"]: condition for condition in conditions}
    for condition_id, capability_ids in MARGINAL_CAPABILITIES.items():
        passed = set(by_id[condition_id]["failed_checks"])
        required_checks = {
            "ENVIRONMENT_ASSOCIATION": {"ENVIRONMENT_ASSOCIATION", "NONCAUSAL_ENVIRONMENT"},
            "HUMAN_CONTEXT_BOUNDARY": {"HUMAN_CONTEXT_BOUNDARY"},
            "SESSION_CORROBORATION": {"SESSION_CORROBORATION", "ROUTE_CORROBORATION"},
            "MOBILE_CONFLICT_DETECTION": {"MOBILE_SPM_REJECTION"},
        }
        marginal[condition_id] = [
            capability
            for capability in capability_ids
            if not required_checks[capability].intersection(passed)
        ]

    status = (
        "PASS"
        if execution_consistent and all(item["status"] == "PASS" for item in conditions)
        else "FAIL"
    )
    return {
        "schema_version": "wake.evidence_ablation_report.v1",
        "status": status,
        "run_manifest": str(run_manifest_path),
        "run_manifest_sha256": sha256_path(run_manifest_path),
        "input_manifest_sha256": sha256_path(DEFAULT_INPUTS / "manifest.json"),
        "evaluator_ground_truth_sha256": sha256_path(GROUND_TRUTH),
        "conditions": conditions,
        "cross_condition": {
            "core_execution_consistent": execution_consistent,
            "reason": (
                "Plan execution and deviation identity remain stable as evidence is added."
                if execution_consistent
                else "Core execution changed between evidence conditions and requires review."
            ),
        },
        "marginal_capabilities": marginal,
        "interpretation_boundary": (
            "This report tests behavior supported by each evidence condition. It does not "
            "compare WAKE with a human coach or claim improved athletic performance."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = score_run(args.run_manifest)
    output = args.output or args.run_manifest.parent / "ablation-report.json"
    write_json(output, report)
    print(json.dumps({"status": report["status"], "report": str(output)}, indent=2))


if __name__ == "__main__":
    main()
