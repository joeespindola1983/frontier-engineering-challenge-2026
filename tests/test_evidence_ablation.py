from __future__ import annotations

import json
import copy
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_evidence_ablation  # noqa: E402
import score_evidence_ablation  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class FakeCaseRunner:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, **kwargs: object) -> dict:
        summary = kwargs["summary"]
        input_dir = kwargs["input_dir"]
        output_dir = kwargs["output_dir"]
        self.calls.append(
            {
                "case_id": summary["case_id"],
                "evidence_files": sorted(
                    path.name for path in input_dir.iterdir() if path.is_file()
                ),
            }
        )
        output_path = output_dir / "outputs" / f"{summary['case_id']}.json"
        trajectory_path = (
            output_dir / "trajectories" / f"{summary['case_id']}.trajectory.json"
        )
        run_evidence_ablation.write_json(
            output_path,
            {
                "schema_version": "wake.analysis_output.v1.1",
                "case_id": summary["case_id"],
                "session_associations": [],
                "plan_summary": None,
                "segments": [],
                "source_policy": [],
                "claims": [],
                "deviations": [],
                "environment_assessment": None,
                "abstentions": [],
                "follow_up_questions": [],
                "coach_briefing": "Synthetic fake output.",
            },
        )
        run_evidence_ablation.write_json(
            trajectory_path,
            {
                "case_id": summary["case_id"],
                "runtime_ms": 10,
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "total_tokens": 150,
                },
                "trajectory_path": str(trajectory_path),
            },
        )
        return {
            "output_path": output_path,
            "trajectory_path": trajectory_path,
        }


class EvidenceAblationRunnerTests(unittest.TestCase):
    def test_dry_run_builds_three_requests_without_a_client(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest_path = run_evidence_ablation.dry_run(output_dir=output)
            manifest = read_json(manifest_path)

            self.assertFalse(manifest["api_called"])
            self.assertEqual(manifest["experiment"]["condition_order"], [
                "core",
                "context-environment",
                "full",
            ])
            self.assertEqual(len(manifest["requests"]), 3)
            serialized = " ".join(
                path.read_text(encoding="utf-8").lower()
                for path in (output / "requests").glob("*.json")
            )
            self.assertNotIn("ground-truth", serialized)

    def test_execution_isolates_each_conditions_evidence_files(self) -> None:
        fake_runner = FakeCaseRunner()
        monotonic = iter([10.0, 10.5])

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            manifest_path = run_evidence_ablation.execute(
                client=object(),
                output_dir=output,
                case_runner=fake_runner,
                now=lambda: "2026-08-29T12:00:00.000+00:00",
                monotonic=lambda: next(monotonic),
                git_commit="abc123",
            )
            manifest = read_json(manifest_path)

        self.assertEqual(
            [call["evidence_files"] for call in fake_runner.calls],
            [
                ["plan.json", "speedcoach.csv"],
                ["context.json", "environment.json", "plan.json", "speedcoach.csv"],
                [
                    "context.json",
                    "environment.json",
                    "mobile.csv",
                    "plan.json",
                    "speedcoach.csv",
                ],
            ],
        )
        self.assertEqual(manifest["cases"], [call["case_id"] for call in fake_runner.calls])
        self.assertEqual(manifest["experiment"]["base_case_id"], run_evidence_ablation.BASE_CASE_ID)
        self.assertEqual(manifest["runtime_ms"], 500)
        self.assertEqual(manifest["total_usage"]["total_tokens"], 450)

    def test_loader_rejects_a_changed_frozen_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory)
            for source in run_evidence_ablation.DEFAULT_INPUTS.glob("*.json"):
                (copied / source.name).write_bytes(source.read_bytes())
            core = read_json(copied / "core.json")
            core["evidence_gaps"].append("Changed after freeze.")
            run_evidence_ablation.write_json(copied / "core.json", core)

            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                run_evidence_ablation.load_experiment(copied)


def condition_output(condition_id: str, summary: dict) -> dict:
    output = copy.deepcopy(
        read_json(
            ROOT
            / "evaluation/runs/comparison-v1-20260829/agent/outputs"
            / "case-002-wind-shift-plan-deviation.json"
        )
    )
    output["case_id"] = summary["case_id"]
    speedcoach_id = next(
        source["source_id"]
        for source in summary["sources"]
        if source["kind"] == "SPEEDCOACH"
    )
    output["claims"] = []
    output["session_associations"] = []
    output["source_policy"] = [
        {
            "metric": metric,
            "selected_source_id": speedcoach_id,
            "confidence": 0.9,
            "reason": "SpeedCoach is the available primary source.",
            "evidence_refs": ["input/speedcoach.csv"],
        }
        for metric in ("stroke_rate_spm", "distance_m", "speed_m_s", "route")
    ]
    output["environment_assessment"] = None
    output["coach_briefing"] = (
        "Six planned work intervals were reconstructed. Work five missed its "
        "prescribed SPM range. Technique and resistance-band use remain unknown."
    )

    if condition_id in {"context-environment", "full"}:
        environment_id = summary["environment"]["timeline_id"]
        output["source_policy"].append(
            {
                "metric": "environment_effective_headwind_m_s",
                "selected_source_id": environment_id,
                "confidence": 0.85,
                "reason": "The environmental timeline is time aligned.",
                "evidence_refs": ["input/environment.json", "input/speedcoach.csv"],
            }
        )
        output["environment_assessment"] = {
            "summary": "A tailwind-to-headwind change is time aligned with the session.",
            "association": "SUPPORTED",
            "confidence": 0.85,
            "evidence_refs": ["input/environment.json", "input/speedcoach.csv"],
            "limitations": ["The association does not establish causation."],
        }

    if condition_id == "full":
        mobile_id = next(
            source["source_id"]
            for source in summary["sources"]
            if source["kind"] == "MOBILE"
        )
        output["session_associations"] = [
            {
                "source_ids": [speedcoach_id, mobile_id],
                "decision": "MATCH",
                "confidence": 0.8,
                "reason": "Mobile corroborates the SpeedCoach route despite a 37 second offset.",
                "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"],
            }
        ]
        route = next(
            policy for policy in output["source_policy"] if policy["metric"] == "route"
        )
        route["reason"] = "Mobile GPS independently corroborates the SpeedCoach route."
        route["evidence_refs"] = ["input/speedcoach.csv", "input/mobile.csv"]
        spm = next(
            policy
            for policy in output["source_policy"]
            if policy["metric"] == "stroke_rate_spm"
        )
        spm["reason"] = "SpeedCoach is selected; mobile SPM is all zero and rejected."
        spm["evidence_refs"] = ["input/speedcoach.csv", "input/mobile.csv"]
    return output


class EvidenceAblationScorerTests(unittest.TestCase):
    def _write_run(self, directory: Path) -> tuple[Path, dict[str, dict]]:
        input_manifest, summaries = run_evidence_ablation.load_experiment()
        outputs = {}
        output_dir = directory / "outputs"
        for condition_id, summary in zip(
            run_evidence_ablation.CONDITION_ORDER,
            summaries,
            strict=True,
        ):
            output = condition_output(condition_id, summary)
            outputs[condition_id] = output
            run_evidence_ablation.write_json(
                output_dir / f"{summary['case_id']}.json",
                output,
            )
        run_manifest = {
            "schema_version": "wake.agent_run.v1",
            "cases": [summary["case_id"] for summary in summaries],
            "experiment": run_evidence_ablation.experiment_metadata(input_manifest),
        }
        path = directory / "run-manifest.json"
        run_evidence_ablation.write_json(path, run_manifest)
        return path, outputs

    def test_condition_aware_report_passes_available_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_manifest, _ = self._write_run(root)
            report = score_evidence_ablation.score_run(run_manifest)

        self.assertEqual(report["status"], "PASS")
        self.assertNotIn("overall_score", report)
        self.assertTrue(
            all(condition["status"] == "PASS" for condition in report["conditions"])
        )
        unlocked = report["marginal_capabilities"]
        self.assertEqual(
            unlocked["context-environment"],
            ["ENVIRONMENT_ASSOCIATION", "HUMAN_CONTEXT_BOUNDARY"],
        )
        self.assertEqual(
            unlocked["full"],
            ["SESSION_CORROBORATION", "MOBILE_CONFLICT_DETECTION"],
        )

    def test_report_rejects_mobile_claims_in_the_core_condition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_manifest, outputs = self._write_run(root)
            core = outputs["core"]
            core["source_policy"][0]["evidence_refs"].append("input/mobile.csv")
            case_id = core["case_id"]
            run_evidence_ablation.write_json(root / "outputs" / f"{case_id}.json", core)

            report = score_evidence_ablation.score_run(run_manifest)

        condition = report["conditions"][0]
        self.assertEqual(condition["status"], "FAIL")
        self.assertIn("OUTPUT_VERIFICATION", condition["failed_checks"])

    def test_report_rejects_causal_wind_and_broken_mobile_spm_selection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_manifest, outputs = self._write_run(root)
            contextual = outputs["context-environment"]
            contextual["coach_briefing"] = "Wind caused the fifth interval slowdown."
            full = outputs["full"]
            mobile_id = next(
                source["source_id"]
                for source in read_json(
                    run_evidence_ablation.DEFAULT_INPUTS / "full.json"
                )["sources"]
                if source["kind"] == "MOBILE"
            )
            next(
                policy
                for policy in full["source_policy"]
                if policy["metric"] == "stroke_rate_spm"
            )["selected_source_id"] = mobile_id
            for condition_id, output in (
                ("context-environment", contextual),
                ("full", full),
            ):
                run_evidence_ablation.write_json(
                    root / "outputs" / f"{output['case_id']}.json",
                    output,
                )

            report = score_evidence_ablation.score_run(run_manifest)

        by_id = {condition["condition_id"]: condition for condition in report["conditions"]}
        self.assertIn("NONCAUSAL_ENVIRONMENT", by_id["context-environment"]["failed_checks"])
        self.assertIn("MOBILE_SPM_REJECTION", by_id["full"]["failed_checks"])

    def test_report_handles_a_deviation_without_segment_reference_as_a_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run_manifest, outputs = self._write_run(root)
            core = outputs["core"]
            core["deviations"].append(
                {
                    "type": "RECONSTRUCTED_WORK_DISTANCE_SHORTFALL",
                    "segment_ref": None,
                    "description": "Aggregate reconstructed distance was below the plan.",
                    "confidence": 0.7,
                    "evidence_refs": ["input/plan.json", "input/speedcoach.csv"],
                }
            )
            run_evidence_ablation.write_json(
                root / "outputs" / f"{core['case_id']}.json",
                core,
            )

            report = score_evidence_ablation.score_run(run_manifest)

        self.assertEqual(report["status"], "FAIL")
        self.assertFalse(report["cross_condition"]["core_execution_consistent"])
        self.assertIn("DEVIATION_DETECTION", report["conditions"][0]["failed_checks"])


if __name__ == "__main__":
    unittest.main()
