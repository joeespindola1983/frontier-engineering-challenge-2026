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

    def test_committed_baseline_run_preserves_authorization_and_observability(self) -> None:
        run_dir = (
            ROOT
            / "evaluation"
            / "runs"
            / "post-regatta-baseline-v1-20260830"
        )
        manifest = json.loads(
            (run_dir / "run-manifest.json").read_text(encoding="utf-8")
        )
        artifact = json.loads(
            (
                run_dir
                / "reports"
                / "club-post-regatta-memory.direct_baseline.json"
            ).read_text(encoding="utf-8")
        )

        self.assertTrue(manifest["api_called"])
        self.assertEqual(manifest["execution_count"], 1)
        self.assertEqual(manifest["authorized_cost_usd"], 0.20)
        self.assertFalse(manifest["authorization_is_provider_cap"])
        self.assertFalse(manifest["store"])
        self.assertTrue(manifest["verification"]["passed"])
        self.assertEqual(manifest["total_approximate_cost_usd"], 0.0437)
        self.assertEqual(
            manifest["input_sha256"],
            "af3bf12be09d207d83f3500d3a614d342ff40fe667b6453ba806ae4728336530",
        )
        self.assertEqual(artifact["observability"]["runtime_ms"], 19_640)
        self.assertEqual(artifact["observability"]["usage"]["total_tokens"], 8_005)

    def test_construct_validity_review_limits_the_accepted_claim(self) -> None:
        run_dir = (
            ROOT
            / "evaluation"
            / "runs"
            / "post-regatta-baseline-v1-20260830"
        )
        review = json.loads(
            (run_dir / "construct-validity-review.json").read_text(encoding="utf-8")
        )

        self.assertTrue(review["frozen_audit_preserved"])
        self.assertEqual(
            review["frozen_audit_conclusion"],
            "DEMONSTRATED_CAPABILITY_COVERAGE_GAIN",
        )
        self.assertTrue(review["accepted_claims"]["structural_fidelity_gain"])
        self.assertFalse(review["accepted_claims"]["semantic_coaching_quality_gain"])
        self.assertFalse(review["accepted_claims"]["human_coach_superiority"])
        self.assertEqual(review["decision"], "ACCEPT_STRUCTURAL_FIDELITY_GAIN_ONLY")
        self.assertEqual(len(review["findings"]), 4)
        self.assertNotIn("score", review)


if __name__ == "__main__":
    unittest.main()
