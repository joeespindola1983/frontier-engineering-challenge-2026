#!/usr/bin/env python3
"""Expanded deterministic grader calibrated for WAKE input bundle v2."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import jsonschema

import grader as legacy


GRADER_VERSION = "1.2"
ROOT = Path(__file__).resolve().parents[1]
GRADER_CONFIG_PATH = ROOT / "config/grader-v1.2.json"
GRADER_CONFIG = json.loads(GRADER_CONFIG_PATH.read_text(encoding="utf-8"))
ANALYSIS_OUTPUT_SCHEMA = json.loads(
    (ROOT / GRADER_CONFIG["analysis_output_schema"]).read_text(encoding="utf-8")
)
DIMENSION_WEIGHTS = GRADER_CONFIG["dimension_weights"]
BASELINE_INPUTS = ROOT / GRADER_CONFIG["baseline_input_bundle"]


def number_present(text: str, value: object) -> bool:
    if value is None:
        return True
    number = float(value)
    if number.is_integer():
        integer = int(number)
        candidates = {str(integer), legacy.normalized_text(f"{integer:,}")}
    else:
        candidates = {str(number)}
    normalized = legacy.normalized_text(text)
    tokens = normalized.split()
    return any(
        candidate in tokens if " " not in candidate else candidate in normalized
        for candidate in candidates
    )


def score_plan(output: dict, ground_truth: dict, summary: dict) -> tuple[dict, dict]:
    plan_output = output.get("plan_summary")
    plan_input = summary.get("plan")
    if not isinstance(plan_output, dict) or not isinstance(plan_input, dict):
        return legacy.ratio_dimension(
            "plan_interpretation",
            0.0,
            ["No structured plan pair was available for scoring."],
            legacy.relevant_refs(output, summary),
        ), {}
    text = " ".join(
        [plan_output.get("summary", ""), *plan_output.get("prescribed_blocks", [])]
    )
    checks = [plan_output.get("status") in {"PARSED", "PARTIAL"}]
    for block in plan_input.get("blocks", []):
        checks.append(
            number_present(text, block.get("repetitions"))
            and (
                number_present(text, block.get("distance_m"))
                or number_present(text, block.get("duration_s"))
            )
        )
        stroke_rate = block.get("stroke_rate") or {}
        checks.append(
            number_present(text, stroke_rate.get("min_spm"))
            and number_present(text, stroke_rate.get("max_spm"))
        )
        recovery = block.get("recovery") or {}
        recovery_min = recovery.get("min_s")
        recovery_max = recovery.get("max_s")
        recovery_seconds_present = (
            number_present(text, recovery_min)
            and number_present(text, recovery_max)
        )
        recovery_minutes_present = (
            recovery_min is not None
            and recovery_max is not None
            and number_present(text, float(recovery_min) / 60)
            and number_present(text, float(recovery_max) / 60)
        )
        checks.append(
            recovery_seconds_present or recovery_minutes_present
        )
        equipment = block.get("equipment") or []
        checks.append(
            not equipment
            or all(
                legacy.contains_any(text, [item.replace("_", " ")])
                for item in equipment
            )
        )
    ratio = sum(checks) / len(checks) if checks else 0.0
    return legacy.ratio_dimension(
        "plan_interpretation",
        ratio,
        [f"Passed {sum(checks)} of {len(checks)} case-derived plan checks."],
        legacy.relevant_refs(plan_output, summary),
    ), {"plan_block_extraction_accuracy": round(ratio, 4)}


def expected_source_ids(summary: dict) -> set[str]:
    result = {item["source_id"] for item in summary.get("sources", [])}
    environment = summary.get("environment")
    if isinstance(environment, dict):
        timeline_id = environment.get("timeline_id")
        if timeline_id:
            result.add(timeline_id)
    return result


def score_source_policy(
    output: dict, ground_truth: dict, summary: dict
) -> tuple[dict, dict]:
    if "expected_source_policy" not in ground_truth:
        return legacy.score_source_policy(output, ground_truth, summary)
    policies = legacy.source_policy_by_metric(output)
    if legacy.broken_mobile_spm_selected(output, summary):
        return legacy.ratio_dimension(
            "metric_level_source_trust",
            0.0,
            ["A known broken mobile SPM channel was selected as stroke-rate evidence."],
            legacy.relevant_refs(output.get("source_policy", []), summary),
        ), {"trusted_source_selection_accuracy": 0.0}

    checks = []
    known_sources = expected_source_ids(summary)
    for metric, expectation in ground_truth.get("expected_source_policy", {}).items():
        policy = policies.get(metric, {})
        selected = policy.get("selected_source_id")
        reason = policy.get("reason", "")
        if expectation in known_sources:
            checks.append(selected == expectation)
        elif " corroborated by " in expectation:
            primary, corroborator = expectation.split(" corroborated by ", 1)
            checks.append(
                selected == primary and legacy.contains_any(reason, [corroborator])
            )
        elif expectation == "human confirmation required":
            checks.append(
                selected is None
                and legacy.contains_any(reason, ["human", "confirm", "unknown"])
            )
        elif expectation == "reject":
            checks.append(
                selected is None
                and legacy.contains_any(reason, ["reject", "unusable", "zero", "broken"])
            )
        else:
            checks.append(False)
    ratio = sum(checks) / len(checks) if checks else 0.0
    return legacy.ratio_dimension(
        "metric_level_source_trust",
        ratio,
        [f"Passed {sum(checks)} of {len(checks)} dynamic source-policy checks."],
        legacy.relevant_refs(output.get("source_policy", []), summary),
    ), {"trusted_source_selection_accuracy": round(ratio, 4)}


def causal_wind_claim(output: dict) -> bool:
    values = [
        claim.get("statement", "") for claim in legacy.confident_claims(output)
    ]
    values.append(output.get("coach_briefing", ""))
    environment = output.get("environment_assessment")
    if isinstance(environment, dict):
        values.append(environment.get("summary", ""))
    for value in values:
        text = legacy.normalized_text(value)
        if re.search(r"(?:wind|headwind|tailwind|crosswind)\s+caus", text):
            return True
        if re.search(r"caus\w*\s+by\s+(?:the\s+)?(?:wind|headwind|tailwind|crosswind)", text):
            return True
        if re.search(r"(?:wind|headwind|tailwind|crosswind)\s+prov", text):
            return True
    return False


def expected_environment_labels(summary: dict) -> tuple[list[str], bool]:
    environment = summary.get("environment") or {}
    windows = environment.get("time_series_windows", [])
    headwind = [
        float(item["effective_headwind_m_s"])
        for item in windows
        if item.get("effective_headwind_m_s") is not None
    ]
    crosswind = [
        abs(float(item["effective_crosswind_m_s"]))
        for item in windows
        if item.get("effective_crosswind_m_s") is not None
    ]
    speeds = [float(item["wind_speed_m_s"]) for item in windows]
    gusts = [
        float(item["gust_speed_m_s"])
        for item in windows
        if item.get("gust_speed_m_s") is not None
    ]
    labels: list[str]
    if headwind and min(headwind) < -1.0 and max(headwind) > 1.0:
        labels = ["tailwind", "headwind"]
    elif headwind and sum(headwind) / len(headwind) > 1.0:
        labels = ["headwind"]
    elif headwind and sum(headwind) / len(headwind) < -1.0:
        labels = ["tailwind"]
    elif crosswind and max(crosswind) > 2.0:
        labels = ["crosswind"]
    elif speeds and max(speeds) <= 1.0:
        labels = ["calm"]
    else:
        labels = ["wind"]
    gust_required = bool(gusts and speeds and max(gusts) - max(speeds) >= 2.0)
    return labels, gust_required


def score_environment(
    output: dict, ground_truth: dict, summary: dict
) -> tuple[dict, dict]:
    environment = output.get("environment_assessment")
    if causal_wind_claim(output):
        return legacy.ratio_dimension(
            "environmental_interpretation",
            0.0,
            ["A confident statement asserted wind causation from associative evidence."],
            legacy.relevant_refs(output, summary),
        ), {}
    if not isinstance(environment, dict):
        return legacy.ratio_dimension(
            "environmental_interpretation",
            0.0,
            ["No environmental assessment was returned."],
            legacy.relevant_refs(output, summary),
        ), {}
    text = legacy.normalized_text(
        " ".join(
            [environment.get("summary", ""), *environment.get("limitations", [])]
        )
    )
    labels, gust_required = expected_environment_labels(summary)
    checks = [
        environment.get("association") == "SUPPORTED",
        "wind" in text or "calm" in text,
        all(label in text for label in labels),
        not gust_required or "gust" in text,
        legacy.contains_any(
            text,
            ["not establish causation", "association only", "does not prove", "not prove"],
        ),
    ]
    weights = [0.2, 0.15, 0.25, 0.1, 0.3]
    ratio = sum(weight for weight, passed in zip(weights, checks) if passed)
    return legacy.ratio_dimension(
        "environmental_interpretation",
        ratio,
        [
            f"Expected {labels}; passed {sum(checks)} of {len(checks)} environment checks."
        ],
        legacy.relevant_refs(environment, summary),
    ), {}


def abstention_matches(predicted: str, expected: str) -> bool:
    predicted_text = legacy.normalized_text(predicted)
    expected_text = legacy.normalized_text(expected)
    if expected_text in predicted_text:
        return True
    negation = legacy.contains_any(
        predicted_text,
        ["not", "cannot", "unknown", "reject", "unusable", "insufficient", "synthetic"],
    )
    concept_groups = [
        ["technique", "synchronization", "synchronisation"],
        ["synthetic", "real"],
        ["wind", "causation", "improvement", "regression"],
        ["band", "resistance"],
        ["mobile", "spm", "zero"],
    ]
    expected_tokens = set(expected_text.split())
    for concepts in concept_groups:
        if expected_tokens.intersection(concepts):
            return negation and any(concept in predicted_text for concept in concepts)
    predicted_tokens = set(predicted_text.split()) - legacy.STOP_WORDS
    expected_tokens -= legacy.STOP_WORDS
    return bool(expected_tokens) and len(predicted_tokens & expected_tokens) / len(expected_tokens) >= 0.5


def score_evidence(
    output: dict, ground_truth: dict, summary: dict
) -> tuple[dict, dict]:
    prohibited = [
        label
        for claim in legacy.confident_claims(output)
        if (label := legacy.is_assertive_prohibited_claim(claim)) is not None
    ]
    narrative_values = [output.get("coach_briefing", "")]
    environment = output.get("environment_assessment")
    if isinstance(environment, dict):
        narrative_values.append(environment.get("summary", ""))
    prohibited.extend(
        label
        for value in narrative_values
        if (label := legacy.is_assertive_prohibited_text(value)) is not None
    )
    if prohibited:
        return legacy.ratio_dimension(
            "evidence_and_abstention",
            0.0,
            ["Unsupported confident claim asserted: " + ", ".join(sorted(set(prohibited))) + "."],
            legacy.relevant_refs(output, summary),
        ), {
            "unsupported_material_claim_rate": round(
                len(prohibited) / max(1, len(legacy.confident_claims(output))), 4
            ),
            "required_abstention_recall": 0.0,
        }
    predicted = output.get("abstentions", [])
    required = ground_truth.get("required_abstentions", [])
    matched = sum(
        any(abstention_matches(item, expected) for item in predicted)
        for expected in required
    )
    abstention_recall = matched / len(required) if required else 1.0
    evidence_ratio = legacy.material_claim_evidence_ratio(output, summary)
    ratio = 0.5 * abstention_recall + 0.5 * evidence_ratio
    return legacy.ratio_dimension(
        "evidence_and_abstention",
        ratio,
        [
            f"Required-abstention recall={abstention_recall:.3f}; material-claim evidence validity={evidence_ratio:.3f}."
        ],
        legacy.relevant_refs(output, summary),
    ), {
        "unsupported_material_claim_rate": 0.0,
        "required_abstention_recall": round(abstention_recall, 4),
    }


SCORERS = {
    "plan_interpretation": score_plan,
    "session_association_and_alignment": legacy.score_association,
    "segment_reconstruction": legacy.score_segments,
    "metric_level_source_trust": score_source_policy,
    "deviation_detection": legacy.score_deviations,
    "environmental_interpretation": score_environment,
    "evidence_and_abstention": score_evidence,
    "follow_up_questions": legacy.score_questions,
}


def grade_case(output: dict, ground_truth: dict, summary: dict) -> dict:
    jsonschema.validate(instance=output, schema=ANALYSIS_OUTPUT_SCHEMA)
    case_id = ground_truth.get("fixture_id", ground_truth.get("case_id"))
    if output.get("case_id") != case_id or summary.get("case_id") != case_id:
        raise ValueError("Output, ground truth, and summary case IDs must match")
    dimensions = []
    secondary_metrics: dict[str, object] = {}
    for name in legacy.applicable_dimensions(ground_truth):
        dimension, metrics = SCORERS[name](output, ground_truth, summary)
        dimensions.append(dimension)
        secondary_metrics.update(metrics)
    applicable_points = sum(item["weight"] for item in dimensions)
    earned_points = sum(item["earned_points"] for item in dimensions)
    return {
        "schema_version": "wake.grader_result.v1",
        "grader_version": GRADER_VERSION,
        "case_id": case_id,
        "score": round(100 * earned_points / applicable_points, 2),
        "earned_points": round(earned_points, 2),
        "applicable_points": applicable_points,
        "dimensions": dimensions,
        "secondary_metrics": secondary_metrics,
    }


def implemented_case_ids(root: Path = ROOT) -> list[str]:
    registry = legacy.read_json(root / GRADER_CONFIG["case_registry"])
    return sorted(
        item["case_id"]
        for item in registry["cases"]
        if item["status"] == "IMPLEMENTED"
    )


def grade_output_directory(
    outputs_dir: Path,
    root: Path = ROOT,
    *,
    case_ids: list[str] | None = None,
) -> dict:
    selected = sorted(case_ids or implemented_case_ids(root))
    missing = [
        case_id for case_id in selected
        if not (outputs_dir / f"{case_id}.json").is_file()
    ]
    if missing:
        raise ValueError("Missing outputs for selected cases: " + ", ".join(missing))
    reports = []
    for case_id in selected:
        reports.append(
            grade_case(
                legacy.read_json(outputs_dir / f"{case_id}.json"),
                legacy.read_json(root / "data/fixtures" / case_id / "ground-truth.json"),
                legacy.read_json(
                    root / GRADER_CONFIG["baseline_input_bundle"] / f"{case_id}.json"
                ),
            )
        )
    dimension_scores: dict[str, list[float]] = {}
    for report in reports:
        for dimension in report["dimensions"]:
            dimension_scores.setdefault(dimension["dimension"], []).append(
                100 * dimension["score_ratio"]
            )
    return {
        "schema_version": "wake.grader_run.v1",
        "grader_version": GRADER_VERSION,
        "rubric_version": GRADER_CONFIG["rubric_version"],
        "grader_config_sha256": hashlib.sha256(GRADER_CONFIG_PATH.read_bytes()).hexdigest(),
        "implemented_case_count": len(implemented_case_ids(root)),
        "graded_case_count": len(reports),
        "macro_average_score": (
            round(sum(report["score"] for report in reports) / len(reports), 2)
            if reports else 0.0
        ),
        "dimension_macro_average_percent": {
            name: round(sum(values) / len(values), 2)
            for name, values in sorted(dimension_scores.items())
        },
        "cases": reports,
    }
