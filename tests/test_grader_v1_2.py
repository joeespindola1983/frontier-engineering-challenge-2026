from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import grader_v1_2  # noqa: E402
from tests.test_grader import (  # noqa: E402
    perfect_case_001_output,
    perfect_case_002_output,
)


CASE_IDS = [
    "case-003-calm-expert-compliant",
    "case-004-steady-headwind-compliant",
    "case-005-tailwind-fast-not-improvement",
    "case-006-crosswind-gusts",
    "case-007-incomplete-intervals",
    "case-008-correct-distance-wrong-spm",
    "case-009-excess-recovery",
    "case-010-mobile-spm-zero",
]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def case_artifacts(case_id: str) -> tuple[dict, dict]:
    truth = read_json(ROOT / "data/fixtures" / case_id / "ground-truth.json")
    summary = read_json(ROOT / "evaluation/baseline-inputs/v2" / f"{case_id}.json")
    return truth, summary


def source_policy(truth: dict, summary: dict) -> list[dict]:
    result = []
    for metric, expectation in truth["expected_source_policy"].items():
        selected = expectation
        reason = "Selected the expected metric-level evidence source."
        if " corroborated by " in expectation:
            selected, corroborator = expectation.split(" corroborated by ", 1)
            reason = f"Selected {selected}; route corroborated by {corroborator}."
        elif expectation in {"human confirmation required", "reject"}:
            selected = None
            reason = (
                "Human confirmation is required."
                if expectation.startswith("human")
                else "Rejected because this channel is unusable."
            )
        evidence_refs = []
        if selected:
            source = next(
                (
                    item
                    for item in summary["sources"]
                    if item["source_id"] == selected
                ),
                None,
            )
            evidence_refs = (
                source["evidence_refs"][:1]
                if source
                else ["input/environment.json"]
            )
        elif summary.get("plan"):
            evidence_refs = ["input/plan.json"]
        result.append(
            {
                "metric": metric,
                "selected_source_id": selected,
                "confidence": 0.95 if selected else 0.0,
                "reason": reason,
                "evidence_refs": evidence_refs,
            }
        )
    return result


def perfect_output(case_id: str) -> dict:
    truth, summary = case_artifacts(case_id)
    environment_text = {
        "case-003-calm-expert-compliant": "Calm wind conditions were associated with the session.",
        "case-004-steady-headwind-compliant": "A steady headwind was associated with the session.",
        "case-005-tailwind-fast-not-improvement": "A steady tailwind was associated with faster measured speed.",
        "case-006-crosswind-gusts": "Strong crosswind and gusts were associated with the session.",
    }.get(case_id)
    environment = None
    if environment_text:
        environment = {
            "summary": environment_text,
            "association": "SUPPORTED",
            "confidence": 0.9,
            "evidence_refs": ["input/environment.json"],
            "limitations": [
                "The association does not establish causation or prove athlete improvement or regression."
            ],
        }
    associations = []
    for expected in truth["expected_session_matches"]:
        associations.append(
            {
                "source_ids": expected["source_ids"],
                "decision": expected["decision"],
                "confidence": 0.95,
                "reason": f"Route overlap supports a match with a {expected['clock_offset_s']} second clock offset.",
                "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"],
            }
        )
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
        for expected in truth["expected_segments"]
    ]
    deviations = [
        {
            "segment_ref": expected["segment_id"],
            "type": "PLAN_DEVIATION",
            "description": "The segment differs from the prescribed execution.",
            "confidence": 0.95,
            "evidence_refs": ["input/speedcoach.csv", "input/plan.json"],
        }
        for expected in truth["expected_segments"]
        if expected["compliance"] == "DEVIATION"
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
        for expected in truth["expected_claims"]
    ]
    return {
        "schema_version": "wake.analysis_output.v1.1",
        "case_id": case_id,
        "session_associations": associations,
        "plan_summary": {
            "status": "PARSED",
            "summary": "4 x 500 m at 20-22 SPM with 120-180 seconds active recovery.",
            "prescribed_blocks": ["Four continuous work intervals in zone B2/B3."],
            "evidence_refs": ["input/plan.json"],
        },
        "segments": segments,
        "source_policy": source_policy(truth, summary),
        "claims": claims,
        "deviations": deviations,
        "environment_assessment": environment,
        "abstentions": truth["required_abstentions"],
        "follow_up_questions": truth["required_questions"],
        "coach_briefing": "The plan was compared with the available synthetic evidence.",
    }


class ExpandedGraderTests(unittest.TestCase):
    def test_v1_2_registry_promotes_ten_cases_without_changing_v1(self) -> None:
        self.assertEqual(len(grader_v1_2.implemented_case_ids(ROOT)), 10)
        self.assertEqual(len(grader_v1_2.legacy.implemented_case_ids(ROOT)), 2)

    def dimension(self, report: dict, name: str) -> dict:
        return next(item for item in report["dimensions"] if item["dimension"] == name)

    def test_versioned_config_targets_expanded_bundle_without_mutating_v1_1(self) -> None:
        config = read_json(ROOT / "config/grader-v1.2.json")
        legacy = read_json(ROOT / "config/grader-v1.1.json")

        self.assertEqual(grader_v1_2.GRADER_VERSION, "1.2")
        self.assertEqual(config["grader_version"], "1.2")
        self.assertEqual(config["baseline_input_bundle"], "evaluation/baseline-inputs/v2")
        self.assertEqual(legacy["grader_version"], "1.1")
        self.assertEqual(legacy["baseline_input_bundle"], "evaluation/baseline-inputs/v1")

    def test_perfect_diagnostic_outputs_score_100(self) -> None:
        for case_id in CASE_IDS:
            with self.subTest(case_id=case_id):
                truth, summary = case_artifacts(case_id)
                report = grader_v1_2.grade_case(
                    perfect_output(case_id), truth, summary
                )
                self.assertEqual(report["score"], 100.0, report)

    def test_expanded_grader_preserves_perfect_scores_for_cases_001_and_002(self) -> None:
        for case_id, factory in (
            ("case-001-misaligned-double-scull", perfect_case_001_output),
            ("case-002-wind-shift-plan-deviation", perfect_case_002_output),
        ):
            with self.subTest(case_id=case_id):
                truth = read_json(
                    ROOT / "data/fixtures" / case_id / "ground-truth.json"
                )
                summary = read_json(
                    ROOT / "evaluation/baseline-inputs/v2" / f"{case_id}.json"
                )
                report = grader_v1_2.grade_case(factory(truth), truth, summary)
                self.assertEqual(report["score"], 100.0, report)

    def test_dynamic_source_policy_rejects_zero_only_mobile_spm(self) -> None:
        case_id = "case-010-mobile-spm-zero"
        truth, summary = case_artifacts(case_id)
        output = perfect_output(case_id)
        stroke_rate = next(
            item for item in output["source_policy"]
            if item["metric"] == "stroke_rate_spm"
        )
        stroke_rate["selected_source_id"] = f"mobile-{case_id}"

        report = grader_v1_2.grade_case(output, truth, summary)

        self.assertEqual(
            self.dimension(report, "metric_level_source_trust")["earned_points"],
            0.0,
        )

    def test_environment_categories_are_case_specific_and_noncausal(self) -> None:
        case_id = "case-006-crosswind-gusts"
        truth, summary = case_artifacts(case_id)
        output = perfect_output(case_id)
        wrong = copy.deepcopy(output)
        wrong["environment_assessment"]["summary"] = "A steady tailwind was present."

        correct_report = grader_v1_2.grade_case(output, truth, summary)
        wrong_report = grader_v1_2.grade_case(wrong, truth, summary)
        causal = copy.deepcopy(output)
        causal["coach_briefing"] = "The crosswind caused the athlete to slow down."
        causal_report = grader_v1_2.grade_case(causal, truth, summary)

        self.assertEqual(
            self.dimension(correct_report, "environmental_interpretation")["earned_points"],
            10.0,
        )
        self.assertLess(
            self.dimension(wrong_report, "environmental_interpretation")["earned_points"],
            10.0,
        )
        self.assertEqual(
            self.dimension(causal_report, "environmental_interpretation")["earned_points"],
            0.0,
        )

    def test_each_isolated_deviation_is_scored_by_segment_identity(self) -> None:
        for case_id, segment_id in {
            "case-007-incomplete-intervals": "work-04",
            "case-008-correct-distance-wrong-spm": "work-03",
            "case-009-excess-recovery": "recovery-02",
        }.items():
            with self.subTest(case_id=case_id):
                truth, summary = case_artifacts(case_id)
                report = grader_v1_2.grade_case(
                    perfect_output(case_id), truth, summary
                )
                self.assertEqual(
                    self.dimension(report, "deviation_detection")["earned_points"],
                    15.0,
                )
                output = perfect_output(case_id)
                output["deviations"][0]["segment_ref"] = "work-01"
                wrong = grader_v1_2.grade_case(output, truth, summary)
                self.assertEqual(
                    self.dimension(wrong, "deviation_detection")["earned_points"],
                    0.0,
                )

    def test_explicit_case_set_directory_report_covers_all_ten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            outputs = Path(directory)
            for case_id in CASE_IDS:
                (outputs / f"{case_id}.json").write_text(
                    json.dumps(perfect_output(case_id)), encoding="utf-8"
                )

            report = grader_v1_2.grade_output_directory(
                outputs, ROOT, case_ids=CASE_IDS
            )

        self.assertEqual(report["grader_version"], "1.2")
        self.assertEqual(report["graded_case_count"], 8)
        self.assertEqual(report["macro_average_score"], 100.0)

    def test_v2_runners_build_all_ten_requests_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            baseline_output = temporary / "baseline"
            agent_output = temporary / "agent"
            baseline = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/run_baseline.py"),
                    "--inputs",
                    str(ROOT / "evaluation/baseline-inputs/v2"),
                    "--output",
                    str(baseline_output),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            agent = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/wake_agent.py"),
                    "--inputs",
                    str(ROOT / "evaluation/baseline-inputs/v2"),
                    "--config",
                    str(ROOT / "config/wake-agent-v2.json"),
                    "--prompt",
                    str(ROOT / "prompts/wake-agent-v2.md"),
                    "--output",
                    str(agent_output),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            baseline_manifest = read_json(baseline_output / "dry-run-manifest.json")
            agent_manifest = read_json(agent_output / "dry-run-manifest.json")

        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        self.assertEqual(agent.returncode, 0, agent.stderr)
        self.assertEqual(len(baseline_manifest["requests"]), 10)
        self.assertEqual(len(agent_manifest["requests"]), 10)
        self.assertFalse(baseline_manifest["api_called"])
        self.assertFalse(agent_manifest["api_called"])

    def test_v1_2_cli_grades_an_explicit_case_set_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            outputs = temporary / "outputs"
            outputs.mkdir()
            report_path = temporary / "report.json"
            for case_id in CASE_IDS:
                (outputs / f"{case_id}.json").write_text(
                    json.dumps(perfect_output(case_id)), encoding="utf-8"
                )
            command = [
                sys.executable,
                str(ROOT / "scripts/grade_outputs_v1_2.py"),
                "--outputs",
                str(outputs),
                "--output",
                str(report_path),
            ]
            for case_id in CASE_IDS:
                command.extend(["--case", case_id])

            completed = subprocess.run(
                command,
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            report = read_json(report_path)

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(report["grader_version"], "1.2")
        self.assertEqual(report["graded_case_count"], 8)
        self.assertEqual(report["macro_average_score"], 100.0)


if __name__ == "__main__":
    unittest.main()
