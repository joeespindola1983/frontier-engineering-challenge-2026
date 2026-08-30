from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import post_regatta_baseline  # noqa: E402
import score_post_regatta_comparison  # noqa: E402


class PostRegattaComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        artifact_path = (
            ROOT
            / "evaluation"
            / "runs"
            / "post-regatta-memory-v1-20260830"
            / "reports"
            / "club-post-regatta-memory.wake_bounded_agent.json"
        )
        cls.artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        cls.contract = post_regatta_baseline.load_capability_contract()

    def test_saved_wake_report_passes_the_frozen_seven_checks(self) -> None:
        result = score_post_regatta_comparison.evaluate_artifact(
            self.artifact,
            self.contract,
        )

        self.assertEqual(result["passed_count"], 7)
        self.assertEqual(result["check_count"], 7)
        self.assertTrue(result["all_passed"])
        self.assertTrue(all(check["passed"] for check in result["checks"]))

    def test_audit_detects_missing_trend_abstention_without_changing_weights(self) -> None:
        artifact = copy.deepcopy(self.artifact)
        artifact["output"]["comparisons"] = [
            comparison
            for comparison in artifact["output"]["comparisons"]
            if comparison["comparison_id"] != "comparison-club-performance-trend"
        ]

        result = score_post_regatta_comparison.evaluate_artifact(artifact, self.contract)
        by_id = {check["check_id"]: check for check in result["checks"]}

        self.assertFalse(by_id["club_trend_abstention"]["passed"])
        self.assertEqual(result["passed_count"], 6)
        self.assertNotIn("score", result)

    def test_equal_capability_coverage_produces_neutral_conclusion(self) -> None:
        report = score_post_regatta_comparison.build_comparison_report(
            baseline_artifact=self.artifact,
            wake_artifact=self.artifact,
            contract=self.contract,
        )

        self.assertEqual(report["evaluation_type"], "NON_SCORED_CAPABILITY_AUDIT")
        self.assertEqual(report["conclusion"], "NO_DEMONSTRATED_CAPABILITY_GAIN")
        self.assertEqual(report["baseline"]["passed_count"], 7)
        self.assertEqual(report["wake"]["passed_count"], 7)
        self.assertNotIn("quality_score", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
