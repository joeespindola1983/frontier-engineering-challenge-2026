from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import generate_diagnostic_cases  # noqa: E402
import build_baseline_inputs  # noqa: E402
import verify_diagnostic_cases  # noqa: E402
import verify_baseline_inputs  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class DiagnosticCaseGeneratorTests(unittest.TestCase):
    def test_public_verifier_accepts_all_generated_diagnostic_cases(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate_diagnostic_cases.build_all(root)

            report = verify_diagnostic_cases.verify_fixture_set(root)

            self.assertEqual(report["status"], "verified")
            self.assertEqual(report["fixture_count"], 8)
            self.assertEqual(set(report["fixtures"]), set(generate_diagnostic_cases.SCENARIOS))

    def test_public_verifier_rejects_a_corrupted_generated_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate_diagnostic_cases.build_all(root)
            speedcoach = root / "case-003-calm-expert-compliant/input/speedcoach.csv"
            speedcoach.write_text(
                speedcoach.read_text(encoding="utf-8") + "corrupted\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(AssertionError, "Hash mismatch"):
                verify_diagnostic_cases.verify_fixture_set(root)

    def test_builds_cases_003_through_010_byte_reproducibly(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_root = Path(first)
            second_root = Path(second)

            generate_diagnostic_cases.build_all(first_root)
            generate_diagnostic_cases.build_all(second_root)

            first_files = {
                path.relative_to(first_root): path.read_bytes()
                for path in first_root.rglob("*")
                if path.is_file()
            }
            second_files = {
                path.relative_to(second_root): path.read_bytes()
                for path in second_root.rglob("*")
                if path.is_file()
            }
            self.assertEqual(first_files, second_files)
            self.assertEqual(
                sorted(path.name for path in first_root.iterdir()),
                sorted(generate_diagnostic_cases.SCENARIOS),
            )

    def test_every_case_is_schema_valid_and_keeps_ground_truth_out_of_input(self) -> None:
        ground_truth_schema = read_json(ROOT / "schemas/ground-truth.schema.json")
        plan_schema = read_json(ROOT / "schemas/training-plan.schema.json")
        environment_schema = read_json(ROOT / "schemas/environment-timeline.schema.json")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate_diagnostic_cases.build_all(root)

            for case_id in generate_diagnostic_cases.SCENARIOS:
                case = root / case_id
                jsonschema.validate(read_json(case / "ground-truth.json"), ground_truth_schema)
                jsonschema.validate(read_json(case / "input/plan.json"), plan_schema)
                environment = case / "input/environment.json"
                if environment.exists():
                    jsonschema.validate(read_json(environment), environment_schema)
                self.assertFalse((case / "input/ground-truth.json").exists())
                serialized_input = " ".join(
                    path.read_text(encoding="utf-8").lower()
                    for path in (case / "input").iterdir()
                )
                self.assertNotIn("expected_segments", serialized_input)
                self.assertNotIn("required_abstentions", serialized_input)
                self.assertNotIn("/users/", serialized_input)

    def test_scenarios_isolate_the_registered_failure_modes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            generate_diagnostic_cases.build_all(root)

            expected_deviations = {
                "case-003-calm-expert-compliant": [],
                "case-004-steady-headwind-compliant": [],
                "case-005-tailwind-fast-not-improvement": [],
                "case-006-crosswind-gusts": [],
                "case-007-incomplete-intervals": ["work-04"],
                "case-008-correct-distance-wrong-spm": ["work-03"],
                "case-009-excess-recovery": ["recovery-02"],
                "case-010-mobile-spm-zero": [],
            }
            for case_id, segment_ids in expected_deviations.items():
                truth = read_json(root / case_id / "ground-truth.json")
                actual = [
                    item["segment_id"]
                    for item in truth["expected_segments"]
                    if item["compliance"] == "DEVIATION"
                ]
                self.assertEqual(actual, segment_ids, case_id)

            for case_id in (
                "case-003-calm-expert-compliant",
                "case-004-steady-headwind-compliant",
                "case-005-tailwind-fast-not-improvement",
                "case-006-crosswind-gusts",
            ):
                rows = read_csv(root / case_id / "input/speedcoach.csv")
                self.assertTrue(all(float(row["stroke_rate_spm"]) > 0 for row in rows))

            mobile = read_csv(
                root / "case-010-mobile-spm-zero/input/mobile.csv"
            )
            self.assertTrue(mobile)
            self.assertTrue(all(float(row["stroke_rate_spm"]) == 0 for row in mobile))

    def test_configured_cases_match_the_frozen_registry_ids(self) -> None:
        registry = read_json(ROOT / "evaluation/cases.json")
        expected = {
            item["case_id"]
            for item in registry["cases"]
            if item["case_id"].startswith(tuple(f"case-{index:03d}" for index in range(3, 11)))
        }

        self.assertEqual(set(generate_diagnostic_cases.SCENARIOS), expected)

    def test_baseline_builder_emits_ten_ground_truth_free_case_summaries(self) -> None:
        summary_schema = read_json(ROOT / "schemas/case-summary.schema.json")
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)

            build_baseline_inputs.build(output)

            manifest = read_json(output / "manifest.json")
            self.assertEqual(manifest["version"], "2.0")
            self.assertEqual(len(manifest["summaries"]), 10)
            self.assertEqual(
                set(manifest["summaries"]),
                {
                    "case-001-misaligned-double-scull",
                    "case-002-wind-shift-plan-deviation",
                    *generate_diagnostic_cases.SCENARIOS,
                },
            )
            for case_id in manifest["summaries"]:
                path = output / f"{case_id}.json"
                jsonschema.validate(read_json(path), summary_schema)
                serialized = path.read_text(encoding="utf-8").lower()
                self.assertNotIn("ground-truth", serialized)
                self.assertNotIn("expected_segments", serialized)

            calm = read_json(output / "case-003-calm-expert-compliant.json")
            mobile_zero = read_json(output / "case-010-mobile-spm-zero.json")
            self.assertIsNotNone(calm["environment"])
            self.assertEqual(
                [source["kind"] for source in calm["sources"]],
                ["SPEEDCOACH"],
            )
            mobile = next(
                source for source in mobile_zero["sources"] if source["kind"] == "MOBILE"
            )
            self.assertEqual(mobile["metrics"]["positive_spm_rows"], 0)
            self.assertIn("SPM_ALL_ZERO", mobile["quality_flags"])

    def test_expansion_preserves_frozen_v1_and_publishes_a_v2_bundle(self) -> None:
        frozen_v1 = read_json(ROOT / "evaluation/baseline-inputs/v1/manifest.json")
        expanded_v2 = read_json(ROOT / "evaluation/baseline-inputs/v2/manifest.json")

        self.assertEqual(frozen_v1["version"], "1.0")
        self.assertEqual(len(frozen_v1["summaries"]), 2)
        self.assertEqual(expanded_v2["version"], "2.0")
        self.assertEqual(len(expanded_v2["summaries"]), 10)
        for case_id, frozen_entry in frozen_v1["summaries"].items():
            self.assertEqual(expanded_v2["summaries"][case_id], frozen_entry)

        report = verify_baseline_inputs.verify_all_versions()
        self.assertEqual(
            [item["cases"] for item in report["bundles"]],
            [list(frozen_v1["summaries"]), list(expanded_v2["summaries"])],
        )


if __name__ == "__main__":
    unittest.main()
