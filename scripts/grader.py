#!/usr/bin/env python3
"""Deterministic rubric grader for frozen WAKE evaluation outputs."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Callable

import jsonschema


GRADER_VERSION = "1.0"
ROOT = Path(__file__).resolve().parents[1]
GRADER_CONFIG_PATH = ROOT / "config/grader-v1.json"
GRADER_CONFIG = json.loads(GRADER_CONFIG_PATH.read_text(encoding="utf-8"))
ANALYSIS_OUTPUT_SCHEMA = json.loads(
    (ROOT / "schemas/analysis-output.schema.json").read_text(encoding="utf-8")
)
DIMENSION_WEIGHTS = GRADER_CONFIG["dimension_weights"]
LEGACY_CASE_DIMENSIONS = GRADER_CONFIG["legacy_case_dimensions"]


def normalized_text(value: object) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value).lower()))


def all_output_text(output: dict) -> str:
    values: list[str] = [output.get("coach_briefing", "")]
    plan = output.get("plan_summary")
    if isinstance(plan, dict):
        values.extend([plan.get("summary", ""), *plan.get("prescribed_blocks", [])])
    values.extend(claim.get("statement", "") for claim in output.get("claims", []))
    values.extend(item.get("description", "") for item in output.get("deviations", []))
    environment = output.get("environment_assessment")
    if isinstance(environment, dict):
        values.extend([environment.get("summary", ""), *environment.get("limitations", [])])
    values.extend(output.get("abstentions", []))
    values.extend(output.get("follow_up_questions", []))
    return normalized_text(" ".join(values))


def output_evidence_refs(value: object) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence_refs" and isinstance(item, list):
                refs.extend(str(ref) for ref in item)
            else:
                refs.extend(output_evidence_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.extend(output_evidence_refs(item))
    return refs


def allowed_evidence_refs(summary: dict) -> set[str]:
    allowed = {f"input/{path}" for path in summary.get("input_hashes", {})}
    for source in summary.get("sources", []):
        allowed.update(source.get("evidence_refs", []))
    for finding in summary.get("cross_source_findings", []):
        allowed.update(finding.get("evidence_refs", []))
    if summary.get("plan"):
        allowed.add("input/plan.json")
    if summary.get("environment"):
        allowed.add("input/environment.json")
    return allowed


def relevant_refs(value: object, summary: dict) -> list[str]:
    allowed = allowed_evidence_refs(summary)
    refs = sorted(set(output_evidence_refs(value)) & allowed)
    if refs:
        return refs
    return sorted(allowed)[:1]


def contains_any(text: str, values: list[str]) -> bool:
    normalized = normalized_text(text)
    return any(normalized_text(value) in normalized for value in values)


def close_enough(actual: object, expected: object, tolerance: float) -> bool:
    if actual is None or expected is None:
        return actual is expected
    return abs(float(actual) - float(expected)) <= tolerance


def ratio_dimension(
    name: str,
    ratio: float,
    reasons: list[str],
    evidence_refs: list[str],
) -> dict:
    weight = DIMENSION_WEIGHTS[name]
    bounded = max(0.0, min(1.0, ratio))
    return {
        "dimension": name,
        "weight": weight,
        "score_ratio": round(bounded, 4),
        "earned_points": round(weight * bounded, 2),
        "reasons": reasons or ["No scoring reason was produced."],
        "evidence_refs": evidence_refs,
    }


def score_plan(output: dict, ground_truth: dict, summary: dict) -> tuple[dict, dict]:
    plan = output.get("plan_summary")
    if not isinstance(plan, dict):
        return ratio_dimension(
            "plan_interpretation",
            0.0,
            ["No structured plan summary was returned."],
            relevant_refs(output, summary),
        ), {}
    text = normalized_text(
        " ".join([plan.get("summary", ""), *plan.get("prescribed_blocks", [])])
    )
    checks = {
        "parsed": plan.get("status") in {"PARSED", "PARTIAL"},
        "six_by_one_km": (
            contains_any(text, ["6 x 1 000", "6 x 1000", "six 1 000", "six 1000"])
            or (contains_any(text, ["6", "six"]) and contains_any(text, ["1 km", "1000"]))
        ),
        "first_spm_range": all(value in text.split() for value in ["19", "21"]),
        "last_spm_range": all(value in text.split() for value in ["22", "24"]),
        "active_recovery": contains_any(text, ["3 5", "180 300", "active recovery"]),
        "resistance_band": contains_any(text, ["resistance band", "band"]),
    }
    weights = {
        "parsed": 0.25,
        "six_by_one_km": 0.2,
        "first_spm_range": 0.2,
        "last_spm_range": 0.2,
        "active_recovery": 0.1,
        "resistance_band": 0.05,
    }
    ratio = sum(weights[key] for key, passed in checks.items() if passed)
    failed = [key for key, passed in checks.items() if not passed]
    reasons = [
        "Plan structure, SPM ranges, recovery, and equipment were recovered."
        if not failed
        else "Missing plan elements: " + ", ".join(failed) + "."
    ]
    return ratio_dimension(
        "plan_interpretation", ratio, reasons, relevant_refs(plan, summary)
    ), {"plan_block_extraction_accuracy": round(ratio, 4)}


def expected_associations(ground_truth: dict, summary: dict) -> list[dict]:
    if "expected_session_matches" in ground_truth:
        return ground_truth["expected_session_matches"]
    expected = ground_truth["expected_findings"]["recording_match"]
    offsets = expected["clock_offsets_from_speedcoach_seconds"]
    return [
        {
            "source_ids": [source["source_id"] for source in summary["sources"]],
            "decision": expected["decision"],
            "clock_offsets": list(offsets.values()),
        }
    ]


def score_association(output: dict, ground_truth: dict, summary: dict) -> tuple[dict, dict]:
    predicted = output.get("session_associations", [])
    expected_items = expected_associations(ground_truth, summary)
    item_scores: list[float] = []
    matched = 0
    for expected in expected_items:
        expected_sources = set(expected["source_ids"])
        candidate = next(
            (
                item
                for item in predicted
                if expected_sources.issubset(set(item.get("source_ids", [])))
            ),
            None,
        )
        if candidate is None:
            item_scores.append(0.0)
            continue
        score = 0.2
        if candidate.get("decision") == expected["decision"]:
            score += 0.6
            matched += 1
        reason_numbers = [
            float(value)
            for value in re.findall(
                r"\d+(?:\.\d+)?", str(candidate.get("reason", ""))
            )
        ]
        offsets = expected.get("clock_offsets", [expected.get("clock_offset_s")])
        expected_offsets = [float(value) for value in offsets if value is not None]
        tolerance = float(ground_truth.get("tolerances", {}).get("clock_offset_s", 0.1))
        if expected_offsets and all(
            any(abs(actual - expected_value) <= tolerance for actual in reason_numbers)
            for expected_value in expected_offsets
        ):
            score += 0.2
        item_scores.append(score)
    ratio = sum(item_scores) / len(item_scores) if item_scores else 0.0
    reasons = [
        f"Matched {matched} of {len(expected_items)} expected session decisions with source and clock evidence."
    ]
    return ratio_dimension(
        "session_association_and_alignment",
        ratio,
        reasons,
        relevant_refs(predicted, summary),
    ), {
        "session_match_precision": round(
            matched / len(predicted), 4
        ) if predicted else 0.0,
        "session_match_recall": round(
            matched / len(expected_items), 4
        ) if expected_items else 1.0,
    }


def score_segments(output: dict, ground_truth: dict, summary: dict) -> tuple[dict, dict]:
    expected_segments = ground_truth.get("expected_segments", [])
    predicted_by_id = {
        item.get("segment_id"): item for item in output.get("segments", [])
    }
    tolerances = ground_truth.get("tolerances", {})
    boundary_tolerance = float(tolerances.get("segment_boundary_s", 0.0))
    distance_tolerance = float(tolerances.get("distance_m", 0.0))
    spm_tolerance = float(tolerances.get("stroke_rate_spm", 0.0))
    scores: list[float] = []
    boundary_errors: list[float] = []
    distance_errors: list[float] = []
    for expected in expected_segments:
        predicted = predicted_by_id.get(expected["segment_id"])
        if predicted is None:
            scores.append(0.0)
            continue
        checks = [predicted.get("kind") == expected["kind"]]
        for key in ["start_offset_s", "end_offset_s"]:
            actual = predicted.get(key)
            expected_value = expected[key]
            checks.append(close_enough(actual, expected_value, boundary_tolerance))
            if actual is not None:
                boundary_errors.append(abs(float(actual) - float(expected_value)))
        checks.append(
            close_enough(predicted.get("distance_m"), expected["distance_m"], distance_tolerance)
        )
        if predicted.get("distance_m") is not None and expected["distance_m"] is not None:
            distance_errors.append(
                abs(float(predicted["distance_m"]) - float(expected["distance_m"]))
            )
        checks.append(
            close_enough(predicted.get("average_spm"), expected["average_spm"], spm_tolerance)
        )
        scores.append(sum(checks) / len(checks))
    ratio = sum(scores) / len(scores) if scores else 0.0
    reasons = [
        f"Reconstructed {len(predicted_by_id)} segments against {len(expected_segments)} expected segments within frozen tolerances."
    ]
    return ratio_dimension(
        "segment_reconstruction",
        ratio,
        reasons,
        relevant_refs(output.get("segments", []), summary),
    ), {
        "mean_segment_boundary_error_s": round(
            sum(boundary_errors) / len(boundary_errors), 3
        ) if boundary_errors else None,
        "mean_segment_distance_error_m": round(
            sum(distance_errors) / len(distance_errors), 3
        ) if distance_errors else None,
    }


def source_policy_by_metric(output: dict) -> dict[str, dict]:
    return {
        item.get("metric"): item
        for item in output.get("source_policy", [])
        if item.get("metric")
    }


def broken_mobile_spm_selected(output: dict, summary: dict) -> bool:
    policy = source_policy_by_metric(output).get("stroke_rate_spm")
    if not policy:
        return False
    selected = policy.get("selected_source_id")
    source = next(
        (item for item in summary.get("sources", []) if item["source_id"] == selected),
        None,
    )
    return bool(
        source
        and {
            "SPM_ALL_ZERO",
            "RAW_SPM_ABSENT",
        }.intersection(source.get("quality_flags", []))
    )


def score_source_policy(output: dict, ground_truth: dict, summary: dict) -> tuple[dict, dict]:
    policies = source_policy_by_metric(output)
    if broken_mobile_spm_selected(output, summary):
        return ratio_dimension(
            "metric_level_source_trust",
            0.0,
            ["A known broken mobile SPM channel was selected as stroke-rate evidence."],
            relevant_refs(output.get("source_policy", []), summary),
        ), {"trusted_source_selection_accuracy": 0.0}

    if "expected_source_policy" in ground_truth:
        checks = []
        spm = policies.get("stroke_rate_spm", {})
        checks.append(spm.get("selected_source_id") == "speedcoach-synthetic")
        distance = policies.get("distance_m", {})
        checks.append(distance.get("selected_source_id") == "speedcoach-synthetic")
        route = policies.get("route", {})
        checks.append(
            route.get("selected_source_id") == "speedcoach-synthetic"
            and "mobile" in normalized_text(route.get("reason", ""))
        )
        environment = policies.get("environment", {})
        checks.append(
            environment.get("selected_source_id") == "synthetic-environment-002"
        )
        band = policies.get("resistance_band_used", {})
        checks.append(
            band.get("selected_source_id") is None
            and contains_any(band.get("reason", ""), ["human", "confirm", "unknown"])
        )
    else:
        spm = policies.get("stroke_rate_spm", {})
        distance = policies.get("distance_m", {})
        boat = policies.get("boat_class", {})
        watch = policies.get("watch", {})
        checks = [
            spm.get("selected_source_id") == "speedcoach",
            distance.get("selected_source_id") == "speedcoach"
            and contains_any(distance.get("reason", ""), ["conflict", "disagree"]),
            boat.get("selected_source_id") is None
            and contains_any(boat.get("reason", ""), ["human", "2x", "double scull"]),
            watch.get("selected_source_id") is None
            and contains_any(watch.get("reason", ""), ["no watch", "not supplied", "unknown"]),
        ]
    ratio = sum(checks) / len(checks)
    reasons = [f"Passed {sum(checks)} of {len(checks)} metric-level source checks."]
    return ratio_dimension(
        "metric_level_source_trust",
        ratio,
        reasons,
        relevant_refs(output.get("source_policy", []), summary),
    ), {"trusted_source_selection_accuracy": round(ratio, 4)}


def precision_recall(predicted: set[str], expected: set[str]) -> tuple[float, float, float]:
    true_positives = len(predicted & expected)
    precision = true_positives / len(predicted) if predicted else (1.0 if not expected else 0.0)
    recall = true_positives / len(expected) if expected else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def score_deviations(output: dict, ground_truth: dict, summary: dict) -> tuple[dict, dict]:
    expected = {
        item["segment_id"]
        for item in ground_truth.get("expected_segments", [])
        if item.get("compliance") == "DEVIATION"
    }
    predicted = {
        item["segment_ref"]
        for item in output.get("deviations", [])
        if item.get("segment_ref")
    }
    precision, recall, f1 = precision_recall(predicted, expected)
    reasons = [
        f"Deviation precision={precision:.3f}, recall={recall:.3f}; expected {sorted(expected)}, predicted {sorted(predicted)}."
    ]
    return ratio_dimension(
        "deviation_detection",
        f1,
        reasons,
        relevant_refs(output.get("deviations", []), summary),
    ), {
        "deviation_precision": round(precision, 4),
        "deviation_recall": round(recall, 4),
    }


def confident_claims(output: dict) -> list[dict]:
    return [
        claim
        for claim in output.get("claims", [])
        if claim.get("status") not in {"UNKNOWN", "UNSUPPORTED", "CONFLICTED"}
    ]


def has_causal_wind_claim(output: dict) -> bool:
    statements = [
        claim.get("statement", "") for claim in confident_claims(output)
    ]
    statements.append(output.get("coach_briefing", ""))
    environment = output.get("environment_assessment")
    if isinstance(environment, dict):
        statements.append(environment.get("summary", ""))
    for statement in statements:
        text = normalized_text(statement)
        causal = any(
            phrase in text
            for phrase in [
                "wind caused",
                "caused by wind",
                "wind proves",
                "wind proved",
                "tailwind proves improvement",
            ]
        )
        if causal:
            return True
    return False


def score_environment(output: dict, ground_truth: dict, summary: dict) -> tuple[dict, dict]:
    environment = output.get("environment_assessment")
    if has_causal_wind_claim(output):
        return ratio_dimension(
            "environmental_interpretation",
            0.0,
            ["A confident claim asserted a causal wind conclusion from associative evidence."],
            relevant_refs(output, summary),
        ), {}
    if not isinstance(environment, dict):
        return ratio_dimension(
            "environmental_interpretation",
            0.0,
            ["No environmental assessment was returned."],
            relevant_refs(output, summary),
        ), {}
    text = normalized_text(
        " ".join([environment.get("summary", ""), *environment.get("limitations", [])])
    )
    checks = [
        environment.get("association") == "SUPPORTED",
        "wind" in text,
        "tailwind" in text and "headwind" in text,
        contains_any(text, ["work 04", "fourth"]),
        contains_any(text, ["not establish causation", "association only", "does not prove"]),
    ]
    weights = [0.2, 0.15, 0.2, 0.15, 0.3]
    ratio = sum(weight for weight, passed in zip(weights, checks) if passed)
    reasons = [f"Passed {sum(checks)} of {len(checks)} environmental interpretation checks."]
    return ratio_dimension(
        "environmental_interpretation",
        ratio,
        reasons,
        relevant_refs(environment, summary),
    ), {}


NON_ASSERTIVE_PHRASES = [
    "cannot assess",
    "cannot determine",
    "can not assess",
    "can not determine",
    "confirm whether",
    "confirmation required",
    "does not establish",
    "insufficient evidence",
    "no evidence",
    "not enough evidence",
    "not observable",
    "remains unknown",
    "requires confirmation",
    "unknown",
    "unsupported",
]


def is_assertive_prohibited_text(value: str) -> str | None:
    text = normalized_text(value)
    if any(normalized_text(phrase) in text for phrase in NON_ASSERTIVE_PHRASES):
        return None
    prohibited = {
        "technique": ["technique", "blade work", "balance"],
        "crew synchronization": ["crew synchronization", "crew synchronisation"],
        "medical state": ["medical", "injury", "heart rate"],
        "resistance equipment use": ["band was used", "used resistance band"],
    }
    for label, phrases in prohibited.items():
        if any(normalized_text(phrase) in text for phrase in phrases):
            return label
    return None


def is_assertive_prohibited_claim(claim: dict) -> str | None:
    if claim.get("status") in {"UNKNOWN", "UNSUPPORTED", "CONFLICTED"}:
        return None
    return is_assertive_prohibited_text(claim.get("statement", ""))


def abstention_checks(case_id: str, abstentions: list[str]) -> list[bool]:
    text_items = [normalized_text(item) for item in abstentions]

    def any_item(predicate: Callable[[str], bool]) -> bool:
        return any(predicate(item) for item in text_items)

    if case_id == "case-002-wind-shift-plan-deviation":
        return [
            any_item(lambda text: "band" in text and contains_any(text, ["not", "cannot", "unknown"])),
            any_item(lambda text: contains_any(text, ["technique", "synchronization"]) and contains_any(text, ["not", "cannot"])),
            any_item(lambda text: "wind" in text and contains_any(text, ["not", "cannot", "caus", "regression"])),
            any_item(lambda text: "synthetic" in text and "real" in text),
        ]
    return [
        any_item(lambda text: "plan" in text and contains_any(text, ["not", "cannot", "no planned"])),
        any_item(lambda text: contains_any(text, ["technique", "blade", "balance", "synchronization"]) and contains_any(text, ["not", "cannot"])),
        any_item(lambda text: "heart rate" in text and contains_any(text, ["not", "cannot", "no usable"])),
        any_item(lambda text: "clock" in text and contains_any(text, ["not", "unknown", "cannot"])),
        any_item(lambda text: contains_any(text, ["athlete", "location", "date", "boat"]) and contains_any(text, ["not", "cannot"])),
    ]


def material_claim_evidence_ratio(output: dict, summary: dict) -> float:
    claims = confident_claims(output)
    if not claims:
        return 1.0
    allowed = allowed_evidence_refs(summary)
    valid = 0
    for claim in claims:
        refs = claim.get("evidence_refs", [])
        if refs and set(refs).issubset(allowed):
            valid += 1
    return valid / len(claims)


def score_evidence(output: dict, ground_truth: dict, summary: dict) -> tuple[dict, dict]:
    prohibited = [
        label
        for claim in confident_claims(output)
        if (label := is_assertive_prohibited_claim(claim)) is not None
    ]
    narrative_values = [output.get("coach_briefing", "")]
    environment = output.get("environment_assessment")
    if isinstance(environment, dict):
        narrative_values.append(environment.get("summary", ""))
    prohibited.extend(
        label
        for value in narrative_values
        if (label := is_assertive_prohibited_text(value)) is not None
    )
    if prohibited:
        return ratio_dimension(
            "evidence_and_abstention",
            0.0,
            ["Unsupported confident claim asserted: " + ", ".join(sorted(set(prohibited))) + "."],
            relevant_refs(output, summary),
        ), {
            "unsupported_material_claim_rate": round(
                len(prohibited) / max(1, len(confident_claims(output))), 4
            ),
            "required_abstention_recall": 0.0,
        }
    checks = abstention_checks(
        ground_truth.get("fixture_id", ground_truth.get("case_id", "")),
        output.get("abstentions", []),
    )
    abstention_recall = sum(checks) / len(checks) if checks else 1.0
    evidence_ratio = material_claim_evidence_ratio(output, summary)
    ratio = 0.5 * abstention_recall + 0.5 * evidence_ratio
    reasons = [
        f"Required-abstention recall={abstention_recall:.3f}; material-claim evidence validity={evidence_ratio:.3f}."
    ]
    return ratio_dimension(
        "evidence_and_abstention",
        ratio,
        reasons,
        relevant_refs(output, summary),
    ), {
        "unsupported_material_claim_rate": 0.0,
        "required_abstention_recall": round(abstention_recall, 4),
    }


STOP_WORDS = {
    "a", "an", "and", "are", "as", "ask", "before", "did", "do", "during",
    "for", "from", "in", "is", "it", "making", "of", "or", "the", "this",
    "to", "was", "were", "whether", "with",
}


def question_matches(predicted: str, expected: str) -> bool:
    predicted_tokens = set(normalized_text(predicted).split()) - STOP_WORDS
    expected_tokens = set(normalized_text(expected).split()) - STOP_WORDS
    if not expected_tokens:
        return False
    overlap = len(predicted_tokens & expected_tokens) / len(expected_tokens)
    return overlap >= 0.5


def score_questions(output: dict, ground_truth: dict, summary: dict) -> tuple[dict, dict]:
    expected = ground_truth.get(
        "required_questions", ground_truth.get("required_follow_up", [])
    )
    predicted = output.get("follow_up_questions", [])
    matched_expected = {
        index
        for index, expected_question in enumerate(expected)
        if any(question_matches(item, expected_question) for item in predicted)
    }
    matched_predicted = sum(
        1
        for item in predicted
        if any(question_matches(item, expected_question) for expected_question in expected)
    )
    precision = matched_predicted / len(predicted) if predicted else (1.0 if not expected else 0.0)
    recall = len(matched_expected) / len(expected) if expected else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    reasons = [
        f"Required-question precision={precision:.3f}, recall={recall:.3f}."
    ]
    return ratio_dimension(
        "follow_up_questions",
        f1,
        reasons,
        relevant_refs(output, summary),
    ), {"required_question_precision": round(precision, 4)}


SCORERS = {
    "plan_interpretation": score_plan,
    "session_association_and_alignment": score_association,
    "segment_reconstruction": score_segments,
    "metric_level_source_trust": score_source_policy,
    "deviation_detection": score_deviations,
    "environmental_interpretation": score_environment,
    "evidence_and_abstention": score_evidence,
    "follow_up_questions": score_questions,
}


def applicable_dimensions(ground_truth: dict) -> list[str]:
    if "applicable_dimensions" in ground_truth:
        return ground_truth["applicable_dimensions"]
    case_id = ground_truth.get("case_id")
    if case_id not in LEGACY_CASE_DIMENSIONS:
        raise ValueError(f"No applicable-dimension adapter for legacy case: {case_id}")
    return LEGACY_CASE_DIMENSIONS[case_id]


def grade_case(output: dict, ground_truth: dict, summary: dict) -> dict:
    jsonschema.validate(instance=output, schema=ANALYSIS_OUTPUT_SCHEMA)
    case_id = ground_truth.get("fixture_id", ground_truth.get("case_id"))
    if output.get("case_id") != case_id or summary.get("case_id") != case_id:
        raise ValueError("Output, ground truth, and summary case IDs must match")
    dimensions: list[dict] = []
    secondary_metrics: dict[str, object] = {}
    for name in applicable_dimensions(ground_truth):
        if name not in SCORERS:
            raise ValueError(f"Unknown rubric dimension: {name}")
        dimension, metrics = SCORERS[name](output, ground_truth, summary)
        dimensions.append(dimension)
        secondary_metrics.update(metrics)
    applicable_points = sum(item["weight"] for item in dimensions)
    earned_points = sum(item["earned_points"] for item in dimensions)
    score = 100 * earned_points / applicable_points if applicable_points else 0.0
    return {
        "schema_version": "wake.grader_result.v1",
        "grader_version": GRADER_VERSION,
        "case_id": case_id,
        "score": round(score, 2),
        "earned_points": round(earned_points, 2),
        "applicable_points": applicable_points,
        "dimensions": dimensions,
        "secondary_metrics": secondary_metrics,
    }


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def implemented_case_ids(root: Path) -> list[str]:
    registry = read_json(root / "evaluation/cases.json")
    return sorted(
        item["case_id"]
        for item in registry["cases"]
        if item["status"] == "IMPLEMENTED"
    )


def grade_output_directory(outputs_dir: Path, root: Path = ROOT) -> dict:
    case_ids = implemented_case_ids(root)
    missing = [
        case_id
        for case_id in case_ids
        if not (outputs_dir / f"{case_id}.json").is_file()
    ]
    if missing:
        raise ValueError("Missing outputs for implemented cases: " + ", ".join(missing))

    case_reports = []
    for case_id in case_ids:
        output = read_json(outputs_dir / f"{case_id}.json")
        ground_truth = read_json(
            root / "data/fixtures" / case_id / "ground-truth.json"
        )
        summary = read_json(
            root / "evaluation/baseline-inputs/v1" / f"{case_id}.json"
        )
        case_reports.append(grade_case(output, ground_truth, summary))

    dimension_scores: dict[str, list[float]] = {}
    for report in case_reports:
        for dimension in report["dimensions"]:
            dimension_scores.setdefault(dimension["dimension"], []).append(
                100.0 * dimension["score_ratio"]
            )
    return {
        "schema_version": "wake.grader_run.v1",
        "grader_version": GRADER_VERSION,
        "rubric_version": GRADER_CONFIG["rubric_version"],
        "grader_config_sha256": hashlib.sha256(
            GRADER_CONFIG_PATH.read_bytes()
        ).hexdigest(),
        "implemented_case_count": len(case_ids),
        "graded_case_count": len(case_reports),
        "macro_average_score": round(
            sum(report["score"] for report in case_reports) / len(case_reports),
            2,
        ) if case_reports else 0.0,
        "dimension_macro_average_percent": {
            name: round(sum(values) / len(values), 2)
            for name, values in sorted(dimension_scores.items())
        },
        "cases": case_reports,
    }
