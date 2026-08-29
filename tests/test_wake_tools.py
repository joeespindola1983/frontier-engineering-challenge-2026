from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import wake_tools  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class WakeToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        bundle = ROOT / "evaluation/baseline-inputs/v1"
        cls.case_001 = read_json(bundle / "case-001-misaligned-double-scull.json")
        cls.case_002 = read_json(bundle / "case-002-wind-shift-plan-deviation.json")

    def test_source_trust_rejects_broken_mobile_spm_per_metric(self) -> None:
        result = wake_tools.assess_source_trust(self.case_002)
        spm = result["metrics"]["stroke_rate_spm"]

        self.assertEqual(spm["selected_source_id"], "speedcoach-synthetic")
        self.assertIn("mobile-synthetic", spm["rejected_source_ids"])
        self.assertTrue(
            any("SPM_ALL_ZERO" in reason for reason in spm["reasons"])
        )

    def test_alignment_uses_route_evidence_despite_clock_conflict(self) -> None:
        result = wake_tools.assess_session_alignment(self.case_001)

        self.assertEqual(result["decision"], "MATCH")
        self.assertEqual(result["confidence"], "HIGH")
        self.assertGreater(result["largest_clock_offset_s"], 3500)
        self.assertLess(result["largest_route_p95_m"], 5)
        self.assertIn("clock", result["limitations"][0].lower())

    def test_plan_analysis_abstains_when_plan_is_missing(self) -> None:
        result = wake_tools.reconstruct_plan_execution(
            self.case_001,
            ROOT / "data/fixtures/case-001-misaligned-double-scull/input",
        )

        self.assertEqual(result["status"], "INSUFFICIENT")
        self.assertEqual(result["segments"], [])

    def test_plan_analysis_reconstructs_case_002_without_ground_truth(self) -> None:
        result = wake_tools.reconstruct_plan_execution(
            self.case_002,
            ROOT / "data/fixtures/case-002-wind-shift-plan-deviation/input",
        )

        work = [segment for segment in result["segments"] if segment["kind"] == "WORK"]
        recovery = [
            segment for segment in result["segments"]
            if segment["kind"] == "RECOVERY"
        ]
        deviations = [
            segment["segment_id"]
            for segment in work
            if segment["compliance"] == "DEVIATION"
        ]

        self.assertEqual(len(work), 6)
        self.assertEqual(len(recovery), 5)
        self.assertEqual(deviations, ["work-05"])
        self.assertEqual(result["equipment_confirmation"], "UNKNOWN")
        self.assertNotIn("ground-truth", json.dumps(result).lower())

    def test_environment_tool_reports_association_not_causation(self) -> None:
        result = wake_tools.analyze_environment(self.case_002)

        self.assertLess(result["effective_headwind_start_m_s"], 0)
        self.assertGreater(result["effective_headwind_end_m_s"], 0)
        self.assertEqual(result["causal_conclusion"], "NOT_ESTABLISHED")
        self.assertIn("association", result["interpretation"].lower())


if __name__ == "__main__":
    unittest.main()
