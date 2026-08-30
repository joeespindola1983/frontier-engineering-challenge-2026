from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_evaluation_results  # noqa: E402


class EvaluationResultsTests(unittest.TestCase):
    def test_builds_public_read_only_summary_from_official_artifacts(self) -> None:
        result = build_evaluation_results.build_evaluation_results(ROOT)

        self.assertEqual(result["schema_version"], "wake.evaluation_results.v1")
        self.assertEqual(result["comparison"]["case_count"], 10)
        self.assertEqual(result["comparison"]["baseline_score"], 49.0)
        self.assertEqual(result["comparison"]["wake_score"], 83.76)
        self.assertEqual(result["comparison"]["absolute_gain"], 34.76)
        self.assertEqual(result["comparison"]["relative_gain_percent"], 70.94)
        self.assertEqual(result["cost"]["total_usd"], 1.139688)
        self.assertEqual(result["cost"]["incremental_agent_usd"], 0.283344)
        self.assertEqual(result["agent_observability"]["tool_calls"], 40)
        self.assertEqual(result["agent_observability"]["verifier_retries"], 5)
        self.assertEqual(len(result["cases"]), 10)
        self.assertTrue(all(case["wake_score"] > case["baseline_score"] for case in result["cases"]))
        self.assertTrue(all(case["scenario"] for case in result["cases"]))
        self.assertTrue(all(case["dimensions"] for case in result["cases"]))
        for case in result["cases"]:
            for dimension in case["dimensions"]:
                self.assertEqual(
                    set(dimension),
                    {"dimension", "label", "baseline_score", "wake_score", "delta"},
                )

        environment = next(
            dimension for dimension in result["dimensions"]
            if dimension["dimension"] == "environmental_interpretation"
        )
        self.assertEqual(environment["delta"], -4.0)
        self.assertTrue(environment["regression"])

        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("ground_truth", serialized)
        self.assertNotIn("coach_briefing", serialized)
        self.assertNotIn("input/", serialized)
        self.assertNotIn("evidence_refs", serialized)
        self.assertNotIn("reasons", serialized)

    def test_generated_module_is_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.mjs"
            second = Path(directory) / "second.mjs"
            build_evaluation_results.write_evaluation_results(ROOT, first)
            build_evaluation_results.write_evaluation_results(ROOT, second)

            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
