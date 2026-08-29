from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import grader  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fixture(case_id: str, filename: str) -> dict:
    return read_json(ROOT / "data" / "fixtures" / case_id / filename)


def summary(case_id: str) -> dict:
    return read_json(ROOT / "evaluation" / "baseline-inputs" / "v1" / f"{case_id}.json")


def perfect_case_002_output(ground_truth: dict) -> dict:
    segments = [
        {
            "segment_id": expected["segment_id"],
            "kind": expected["kind"],
            "start_offset_s": expected["start_offset_s"],
            "end_offset_s": expected["end_offset_s"],
            "distance_m": expected["distance_m"],
            "average_spm": expected["average_spm"],
            "confidence": 0.95,
            "evidence_refs": ["input/speedcoach.csv", "input/plan.json"],
        }
        for expected in ground_truth["expected_segments"]
    ]
    claims = [
        {
            "claim_id": expected["claim_id"],
            "statement": expected["expectation"],
            "status": "DERIVED",
            "confidence": 0.95,
            "evidence_refs": [f"input/{ref}" for ref in expected["evidence_refs"]],
            "limitations": [],
        }
        for expected in ground_truth["expected_claims"]
    ]
    return {
        "schema_version": "wake.analysis_output.v1.1",
        "case_id": ground_truth["fixture_id"],
        "session_associations": [
            {
                "source_ids": ["speedcoach-synthetic", "mobile-synthetic"],
                "decision": "MATCH",
                "confidence": 0.98,
                "reason": "Routes overlap and the mobile clock offset is 37.0 seconds.",
                "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"],
            }
        ],
        "plan_summary": {
            "status": "PARSED",
            "summary": "6 x 1,000 m in B2/B3 with 3-5 min active recovery.",
            "prescribed_blocks": [
                "First 3 x 1,000 m at 19-21 SPM with resistance band.",
                "Last 3 x 1,000 m at 22-24 SPM without resistance band.",
            ],
            "evidence_refs": ["input/plan.json"],
        },
        "segments": segments,
        "source_policy": [
            {
                "metric": "stroke_rate_spm",
                "selected_source_id": "speedcoach-synthetic",
                "confidence": 0.99,
                "reason": "Mobile SPM is stuck at zero.",
                "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"],
            },
            {
                "metric": "distance_m",
                "selected_source_id": "speedcoach-synthetic",
                "confidence": 0.95,
                "reason": "Mobile distance has a known bias.",
                "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"],
            },
            {
                "metric": "route",
                "selected_source_id": "speedcoach-synthetic",
                "confidence": 0.95,
                "reason": "The route is corroborated by mobile-synthetic.",
                "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"],
            },
            {
                "metric": "environment",
                "selected_source_id": "synthetic-environment-002",
                "confidence": 0.95,
                "reason": "Time-aligned environmental timeline.",
                "evidence_refs": ["input/environment.json"],
            },
            {
                "metric": "resistance_band_used",
                "selected_source_id": None,
                "confidence": 0.0,
                "reason": "Human confirmation is required.",
                "evidence_refs": ["input/plan.json"],
            },
        ],
        "claims": claims,
        "deviations": [
            {
                "segment_ref": "work-05",
                "type": "SPM_BELOW_TARGET",
                "description": "About 20 SPM versus the prescribed 22-24 SPM.",
                "confidence": 0.98,
                "evidence_refs": ["input/speedcoach.csv", "input/plan.json"],
            }
        ],
        "environment_assessment": {
            "summary": "Wind shifted from tailwind to headwind during work-04.",
            "association": "SUPPORTED",
            "confidence": 0.95,
            "evidence_refs": ["input/environment.json", "input/speedcoach.csv"],
            "limitations": [
                "This supports association only; it does not establish causation or athlete regression."
            ],
        },
        "abstentions": ground_truth["required_abstentions"],
        "follow_up_questions": ground_truth["required_questions"],
        "coach_briefing": (
            "Six intervals completed; work-05 missed SPM after a wind shift. "
            "Confirm whether the resistance band was used."
        ),
    }


def perfect_case_001_output(ground_truth: dict) -> dict:
    case_id = ground_truth["case_id"]
    return {
        "schema_version": "wake.analysis_output.v1.1",
        "case_id": case_id,
        "session_associations": [
            {
                "source_ids": ["speedcoach", "mobile-ios", "mobile-android"],
                "decision": "MATCH",
                "confidence": 0.98,
                "reason": (
                    "Near-identical route geometry supports a match despite clock "
                    "offsets of 3589.127 and 3564.821 seconds; the cause is unknown."
                ),
                "evidence_refs": [
                    "input/sources/speedcoach.csv",
                    "input/sources/mobile-ios-sensor.csv",
                    "input/sources/mobile-android-sensor.csv",
                ],
            }
        ],
        "plan_summary": {
            "status": "NOT_SUPPLIED",
            "summary": "No planned workout was supplied.",
            "prescribed_blocks": [],
            "evidence_refs": [],
        },
        "segments": [],
        "source_policy": [
            {
                "metric": "stroke_rate_spm",
                "selected_source_id": "speedcoach",
                "confidence": 0.99,
                "reason": "Mobile raw telemetry contains no SPM evidence.",
                "evidence_refs": [
                    "input/sources/speedcoach.csv",
                    "input/sources/mobile-ios-sensor.csv",
                    "input/sources/mobile-android-sensor.csv",
                ],
            },
            {
                "metric": "distance_m",
                "selected_source_id": "speedcoach",
                "confidence": 0.8,
                "reason": "Use SpeedCoach while exposing conflicting mobile summaries.",
                "evidence_refs": [
                    "input/sources/speedcoach.csv",
                    "input/sources/mobile-ios-workout.csv",
                    "input/sources/mobile-android-workout.csv",
                ],
            },
            {
                "metric": "boat_class",
                "selected_source_id": None,
                "confidence": 0.99,
                "reason": "Human-confirmed double scull 2x overrides device defaults.",
                "evidence_refs": ["input/context.json"],
            },
            {
                "metric": "watch",
                "selected_source_id": None,
                "confidence": 0.0,
                "reason": "No watch evidence was supplied.",
                "evidence_refs": ["input/context.json"],
            },
        ],
        "claims": [
            {
                "claim_id": "confirmed-boat-class",
                "statement": "A human domain expert confirmed a men's double scull 2x.",
                "status": "HUMAN_CONFIRMED",
                "confidence": 0.99,
                "evidence_refs": ["input/context.json"],
                "limitations": [],
            }
        ],
        "deviations": [],
        "environment_assessment": None,
        "abstentions": ground_truth["required_abstentions"],
        "follow_up_questions": ground_truth["required_follow_up"],
        "coach_briefing": "The three recordings match; plan and technique remain unknown.",
    }


class GraderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_002_id = "case-002-wind-shift-plan-deviation"
        self.gt_002 = fixture(self.case_002_id, "ground-truth.json")
        self.summary_002 = summary(self.case_002_id)
        self.perfect_002 = perfect_case_002_output(self.gt_002)

    def dimension(self, report: dict, name: str) -> dict:
        return next(
            dimension
            for dimension in report["dimensions"]
            if dimension["dimension"] == name
        )

    def test_versioned_grader_config_freezes_100_point_rubric(self) -> None:
        config = read_json(ROOT / "config/grader-v1.1.json")

        self.assertEqual(config["grader_version"], grader.GRADER_VERSION)
        self.assertEqual(grader.GRADER_VERSION, "1.1")
        self.assertEqual(config["rubric_version"], "1.0")
        self.assertEqual(sum(config["dimension_weights"].values()), 100)
        self.assertEqual(config["dimension_weights"], grader.DIMENSION_WEIGHTS)

    def test_perfect_synthetic_output_scores_100_with_all_dimensions(self) -> None:
        report = grader.grade_case(
            self.perfect_002, self.gt_002, self.summary_002
        )

        self.assertEqual(report["score"], 100.0)
        self.assertEqual(len(report["dimensions"]), 8)
        self.assertTrue(all(item["reasons"] for item in report["dimensions"]))
        self.assertTrue(all(item["evidence_refs"] for item in report["dimensions"]))

    def test_legacy_real_case_is_normalized_over_applicable_dimensions(self) -> None:
        case_id = "case-001-misaligned-double-scull"
        ground_truth = fixture(case_id, "ground-truth.json")
        report = grader.grade_case(
            perfect_case_001_output(ground_truth),
            ground_truth,
            summary(case_id),
        )

        self.assertEqual(report["score"], 100.0)
        self.assertEqual(
            {item["dimension"] for item in report["dimensions"]},
            {
                "session_association_and_alignment",
                "metric_level_source_trust",
                "evidence_and_abstention",
                "follow_up_questions",
            },
        )
        self.assertEqual(report["applicable_points"], 45)

    def test_pairwise_matches_can_connect_all_sources_in_legacy_case(self) -> None:
        case_id = "case-001-misaligned-double-scull"
        ground_truth = fixture(case_id, "ground-truth.json")
        output = perfect_case_001_output(ground_truth)
        output["session_associations"] = [
            {
                "source_ids": ["speedcoach", "mobile-ios"],
                "decision": "MATCH",
                "confidence": 0.95,
                "reason": "Route overlap with a 3589.127 second clock offset.",
                "evidence_refs": [
                    "input/sources/speedcoach.csv",
                    "input/sources/mobile-ios-sensor.csv",
                ],
            },
            {
                "source_ids": ["speedcoach", "mobile-android"],
                "decision": "MATCH",
                "confidence": 0.95,
                "reason": "Route overlap with a 3564.821 second clock offset.",
                "evidence_refs": [
                    "input/sources/speedcoach.csv",
                    "input/sources/mobile-android-sensor.csv",
                ],
            },
        ]

        report = grader.grade_case(output, ground_truth, summary(case_id))

        self.assertEqual(
            self.dimension(report, "session_association_and_alignment")["earned_points"],
            15.0,
        )
        self.assertEqual(report["secondary_metrics"]["session_match_precision"], 1.0)

    def test_common_metric_aliases_are_canonicalized_before_source_scoring(self) -> None:
        case_id = "case-001-misaligned-double-scull"
        ground_truth = fixture(case_id, "ground-truth.json")
        output = perfect_case_001_output(ground_truth)
        aliases = {
            "stroke_rate_spm": "stroke rate",
            "distance_m": "distance",
            "boat_class": "boat type",
        }
        for policy in output["source_policy"]:
            policy["metric"] = aliases.get(policy["metric"], policy["metric"])

        report = grader.grade_case(output, ground_truth, summary(case_id))

        self.assertEqual(
            self.dimension(report, "metric_level_source_trust")["earned_points"],
            15.0,
        )

    def test_unassessable_technique_language_is_an_abstention_not_a_claim(self) -> None:
        output = copy.deepcopy(self.perfect_002)
        output["coach_briefing"] = "Technique and physiology remain unassessable."

        report = grader.grade_case(output, self.gt_002, self.summary_002)

        self.assertEqual(
            self.dimension(report, "evidence_and_abstention")["earned_points"],
            10.0,
        )

    def test_broken_mobile_spm_selection_forces_source_trust_to_zero(self) -> None:
        output = copy.deepcopy(self.perfect_002)
        spm_policy = next(
            item for item in output["source_policy"]
            if item["metric"] == "stroke_rate_spm"
        )
        spm_policy["selected_source_id"] = "mobile-synthetic"

        report = grader.grade_case(output, self.gt_002, self.summary_002)

        dimension = self.dimension(report, "metric_level_source_trust")
        self.assertEqual(dimension["earned_points"], 0.0)
        self.assertTrue(any("broken mobile SPM" in reason for reason in dimension["reasons"]))

    def test_causal_wind_claim_forces_environment_dimension_to_zero(self) -> None:
        output = copy.deepcopy(self.perfect_002)
        output["claims"].append(
            {
                "claim_id": "causal-wind",
                "statement": "The wind caused the athlete to become slower.",
                "status": "INFERRED",
                "confidence": 0.95,
                "evidence_refs": ["input/environment.json"],
                "limitations": [],
            }
        )

        report = grader.grade_case(output, self.gt_002, self.summary_002)

        dimension = self.dimension(report, "environmental_interpretation")
        self.assertEqual(dimension["earned_points"], 0.0)
        self.assertTrue(any("causal" in reason.lower() for reason in dimension["reasons"]))

    def test_causal_wind_briefing_also_forces_environment_to_zero(self) -> None:
        output = copy.deepcopy(self.perfect_002)
        output["coach_briefing"] = "The wind caused the athlete to become slower."

        report = grader.grade_case(output, self.gt_002, self.summary_002)

        dimension = self.dimension(report, "environmental_interpretation")
        self.assertEqual(dimension["earned_points"], 0.0)

    def test_visible_technique_claim_forces_evidence_dimension_to_zero(self) -> None:
        output = copy.deepcopy(self.perfect_002)
        output["claims"].append(
            {
                "claim_id": "technique-invention",
                "statement": "The athlete showed poor visible rowing technique.",
                "status": "INFERRED",
                "confidence": 0.9,
                "evidence_refs": ["input/speedcoach.csv"],
                "limitations": [],
            }
        )

        report = grader.grade_case(output, self.gt_002, self.summary_002)

        dimension = self.dimension(report, "evidence_and_abstention")
        self.assertEqual(dimension["earned_points"], 0.0)
        self.assertTrue(any("technique" in reason.lower() for reason in dimension["reasons"]))

    def test_visible_technique_briefing_also_forces_evidence_to_zero(self) -> None:
        output = copy.deepcopy(self.perfect_002)
        output["coach_briefing"] = "The athlete showed poor visible rowing technique."

        report = grader.grade_case(output, self.gt_002, self.summary_002)

        dimension = self.dimension(report, "evidence_and_abstention")
        self.assertEqual(dimension["earned_points"], 0.0)

    def test_false_positive_deviation_reduces_precision_and_score(self) -> None:
        output = copy.deepcopy(self.perfect_002)
        output["deviations"].append(
            {
                "segment_ref": "work-04",
                "type": "FALSE_FAILURE",
                "description": "Incorrectly marked as failed.",
                "confidence": 0.9,
                "evidence_refs": ["input/speedcoach.csv"],
            }
        )

        report = grader.grade_case(output, self.gt_002, self.summary_002)

        dimension = self.dimension(report, "deviation_detection")
        self.assertLess(dimension["earned_points"], dimension["weight"])
        self.assertEqual(report["secondary_metrics"]["deviation_precision"], 0.5)
        self.assertEqual(report["secondary_metrics"]["deviation_recall"], 1.0)

    def test_schema_invalid_output_is_rejected_before_scoring(self) -> None:
        output = copy.deepcopy(self.perfect_002)
        del output["coach_briefing"]

        with self.assertRaises(jsonschema.ValidationError):
            grader.grade_case(output, self.gt_002, self.summary_002)

    def test_complete_output_directory_produces_macro_average_report(self) -> None:
        case_001_id = "case-001-misaligned-double-scull"
        gt_001 = fixture(case_001_id, "ground-truth.json")
        with tempfile.TemporaryDirectory() as temporary_directory:
            outputs_dir = Path(temporary_directory) / "outputs"
            outputs_dir.mkdir()
            (outputs_dir / f"{case_001_id}.json").write_text(
                json.dumps(perfect_case_001_output(gt_001)), encoding="utf-8"
            )
            (outputs_dir / f"{self.case_002_id}.json").write_text(
                json.dumps(self.perfect_002), encoding="utf-8"
            )

            report = grader.grade_output_directory(outputs_dir, ROOT)

        self.assertEqual(report["macro_average_score"], 100.0)
        self.assertEqual(report["implemented_case_count"], 2)
        self.assertEqual(report["graded_case_count"], 2)
        self.assertEqual(len(report["cases"]), 2)
        self.assertEqual(report["rubric_version"], "1.0")
        self.assertEqual(len(report["grader_config_sha256"]), 64)

    def test_cli_writes_versioned_report_without_network(self) -> None:
        case_001_id = "case-001-misaligned-double-scull"
        gt_001 = fixture(case_001_id, "ground-truth.json")
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            outputs_dir = temporary / "outputs"
            outputs_dir.mkdir()
            report_path = temporary / "grade-report.json"
            (outputs_dir / f"{case_001_id}.json").write_text(
                json.dumps(perfect_case_001_output(gt_001)), encoding="utf-8"
            )
            (outputs_dir / f"{self.case_002_id}.json").write_text(
                json.dumps(self.perfect_002), encoding="utf-8"
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/grade_outputs.py"),
                    "--outputs",
                    str(outputs_dir),
                    "--output",
                    str(report_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            report = read_json(report_path)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(report["macro_average_score"], 100.0)
        self.assertEqual(report["grader_version"], grader.GRADER_VERSION)


if __name__ == "__main__":
    unittest.main()
