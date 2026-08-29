from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_baseline_inputs  # noqa: E402
import generate_synthetic_cases  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DomainContractTests(unittest.TestCase):
    def test_voga_is_normalized_to_target_spm(self) -> None:
        fact = next(
            item for item in build_baseline_inputs.DOMAIN_KNOWLEDGE
            if item["term"] == "voga"
        )
        self.assertEqual(
            fact["meaning"],
            "Target stroke rate in strokes per minute (SPM).",
        )
        self.assertEqual(fact["status"], "HUMAN_CONFIRMED")

    def test_committed_plan_marks_standardized_zone_system(self) -> None:
        plan = read_json(
            ROOT
            / "data/fixtures/case-002-wind-shift-plan-deviation/input/plan.json"
        )
        self.assertEqual(plan["unresolved_terms"], [])
        self.assertTrue(
            all(
                block["zone_system"] == "STANDARD_ROWING_ZONES"
                for block in plan["blocks"]
            )
        )


class SyntheticGeneratorTests(unittest.TestCase):
    def test_generation_is_byte_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_path = Path(first)
            second_path = Path(second)
            generate_synthetic_cases.build_case(first_path)
            generate_synthetic_cases.build_case(second_path)

            first_files = {
                path.relative_to(first_path): path.read_bytes()
                for path in first_path.rglob("*")
                if path.is_file()
            }
            second_files = {
                path.relative_to(second_path): path.read_bytes()
                for path in second_path.rglob("*")
                if path.is_file()
            }
            self.assertEqual(first_files, second_files)


class BaselineInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.output = Path(self.temporary_directory.name)
        build_baseline_inputs.build(self.output)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_manifest_hashes_prompt_and_summaries(self) -> None:
        manifest = read_json(self.output / "manifest.json")
        self.assertEqual(
            manifest["prompt"]["sha256"],
            sha256(ROOT / manifest["prompt"]["path"]),
        )
        for case_id, entry in manifest["summaries"].items():
            summary_path = self.output / f"{case_id}.json"
            self.assertEqual(entry["sha256"], sha256(summary_path))
            self.assertEqual(entry["bytes"], summary_path.stat().st_size)

    def test_real_case_summary_does_not_leak_evaluator_truth(self) -> None:
        path = self.output / "case-001-misaligned-double-scull.json"
        summary = read_json(path)
        serialized = path.read_text(encoding="utf-8").lower()
        self.assertIsNone(summary["plan"])
        self.assertNotIn("double_scull", serialized)
        self.assertNotIn("world_rowing_code", serialized)
        self.assertNotIn("ground-truth", serialized)
        self.assertNotIn("ground_truth", serialized)

    def test_synthetic_summary_preserves_failure_modes(self) -> None:
        summary = read_json(
            self.output / "case-002-wind-shift-plan-deviation.json"
        )
        mobile = next(
            source for source in summary["sources"]
            if source["source_id"] == "mobile-synthetic"
        )
        wind = summary["environment"]["time_series_windows"]
        self.assertEqual(mobile["metrics"]["positive_spm_rows"], 0)
        self.assertLess(wind[0]["effective_headwind_m_s"], 0)
        self.assertGreater(wind[-1]["effective_headwind_m_s"], 0)


if __name__ == "__main__":
    unittest.main()
