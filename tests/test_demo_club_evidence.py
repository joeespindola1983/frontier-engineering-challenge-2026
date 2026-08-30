from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import bundle_assembler  # noqa: E402
import generate_demo_club_evidence  # noqa: E402
import source_adapters  # noqa: E402
import verify_demo_club_evidence  # noqa: E402
import wake_tools  # noqa: E402


FIXTURE_ROOT = ROOT / "data" / "demo-club-evidence"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def case_summary(case_dir: Path) -> dict:
    input_dir = case_dir / "input"
    speedcoach_content = (input_dir / "speedcoach.csv").read_bytes()
    normalized = source_adapters.normalize_source(
        kind="SPEEDCOACH",
        content=speedcoach_content,
        source_ref="input/speedcoach.csv",
    )
    return bundle_assembler.assemble_case_summary(
        plan=read_json(input_dir / "plan.json"),
        context=read_json(input_dir / "context.json"),
        environment=None,
        telemetry_sources=[
            {
                "kind": "SPEEDCOACH",
                "evidence_ref": "input/speedcoach.csv",
                "normalized_csv": normalized.normalized_csv,
                "normalization": normalized.report,
            }
        ],
        input_hashes={
            "plan.json": bundle_assembler.sha256_bytes(
                (input_dir / "plan.json").read_bytes()
            ),
            "context.json": bundle_assembler.sha256_bytes(
                (input_dir / "context.json").read_bytes()
            ),
            "speedcoach.csv": normalized.report["input_sha256"],
        },
    )


class DemoClubEvidenceTests(unittest.TestCase):
    def test_public_verifier_proves_hashes_privacy_and_expected_reconstruction(self) -> None:
        report = verify_demo_club_evidence.verify_fixture_set(FIXTURE_ROOT)

        self.assertEqual(report["status"], "verified")
        self.assertEqual(report["fixture_count"], 2)
        self.assertEqual(
            report["fixtures"]["club-bridge-mixed-20260820-spm"]["deviation_segments"],
            ["work-02"],
        )
        self.assertEqual(
            report["fixtures"]["club-atlas-men-20260828-recovery"]["deviation_segments"],
            ["recovery-02"],
        )
        self.assertTrue(all(
            fixture["agent_executed"] is False
            for fixture in report["fixtures"].values()
        ))

    def test_telemetry_generation_has_a_bounded_row_count(self) -> None:
        for case in generate_demo_club_evidence.CASES.values():
            rows = generate_demo_club_evidence.build_telemetry(case)
            self.assertGreater(len(rows), 0)
            self.assertLess(len(rows), 3_000)

    def test_generation_is_byte_reproducible_and_matches_committed_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as first_raw, tempfile.TemporaryDirectory() as second_raw:
            first = Path(first_raw)
            second = Path(second_raw)
            generate_demo_club_evidence.build_demo_club_evidence(first)
            generate_demo_club_evidence.build_demo_club_evidence(second)

            first_files = sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file())
            second_files = sorted(path.relative_to(second) for path in second.rglob("*") if path.is_file())
            committed_files = sorted(path.relative_to(FIXTURE_ROOT) for path in FIXTURE_ROOT.rglob("*") if path.is_file())
            self.assertEqual(first_files, second_files)
            self.assertEqual(first_files, committed_files)
            for relative in first_files:
                self.assertEqual((first / relative).read_bytes(), (second / relative).read_bytes())
                self.assertEqual((first / relative).read_bytes(), (FIXTURE_ROOT / relative).read_bytes())

    def test_bridge_bundle_matches_two_by_four_kilometre_plan_and_low_spm(self) -> None:
        case_id = "club-bridge-mixed-20260820-spm"
        case_dir = FIXTURE_ROOT / case_id
        plan = read_json(case_dir / "input" / "plan.json")
        schema = read_json(ROOT / "schemas" / "training-plan.schema.json")
        jsonschema.validate(plan, schema)

        block = plan["blocks"][0]
        self.assertEqual(plan["scheduled_date"], "2026-08-20")
        self.assertEqual(plan["athlete_scope"]["ids"], ["crew-2x-mixed-a"])
        self.assertEqual(block["repetitions"], 2)
        self.assertEqual(block["distance_m"], 4000)
        self.assertEqual(block["stroke_rate"], {"min_spm": 20, "max_spm": 20})

        summary = case_summary(case_dir)
        result = wake_tools.reconstruct_plan_execution(
            summary,
            case_dir / "input",
            contract_version="v2",
        )
        self.assertEqual(result["execution_counts"]["planned_work_intervals"], 2)
        self.assertEqual(result["execution_counts"]["observed_work_intervals"], 2)
        self.assertEqual(
            [item["segment_ref"] for item in result["plan_deviations"]],
            ["work-02"],
        )

    def test_atlas_bundle_reconstructs_only_the_excess_recovery(self) -> None:
        case_id = "club-atlas-men-20260828-recovery"
        case_dir = FIXTURE_ROOT / case_id
        summary = case_summary(case_dir)
        result = wake_tools.reconstruct_plan_execution(
            summary,
            case_dir / "input",
            contract_version="v2",
        )

        self.assertEqual(result["execution_counts"]["planned_work_intervals"], 4)
        self.assertEqual(result["execution_counts"]["observed_work_intervals"], 4)
        self.assertEqual(
            [item["segment_ref"] for item in result["plan_deviations"]],
            ["recovery-02"],
        )
        recovery = next(
            segment
            for segment in result["segments"]
            if segment["segment_id"] == "recovery-02"
        )
        self.assertGreater(recovery["duration_s"], 180)

    def test_manifest_preserves_synthetic_provenance_and_input_hashes(self) -> None:
        manifest = read_json(FIXTURE_ROOT / "manifest.json")
        self.assertEqual(manifest["schema_version"], "wake.demo_club_evidence_manifest.v1")
        self.assertEqual(len(manifest["cases"]), 2)
        self.assertTrue(all(case["provenance"] == "REAL_INFORMED_SYNTHETIC" for case in manifest["cases"]))
        self.assertTrue(all(len(case["input_sha256"]) == 3 for case in manifest["cases"]))
        serialized = json.dumps(manifest).lower()
        self.assertNotIn("/users/", serialized)
        self.assertNotIn("private-data", serialized)


if __name__ == "__main__":
    unittest.main()
