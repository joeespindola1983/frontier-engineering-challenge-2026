from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import verify_demo_club_investigation_run  # noqa: E402


RUN_ROOT = ROOT / "evaluation" / "runs" / "demo-club-investigations-v1-20260830"


class DemoClubInvestigationRunTests(unittest.TestCase):
    def test_public_verifier_accepts_both_paid_candidate_results(self) -> None:
        report = verify_demo_club_investigation_run.verify_run(RUN_ROOT)

        self.assertEqual(report["status"], "verified")
        self.assertEqual(report["execution_count"], 2)
        self.assertEqual(report["approximate_total_cost_usd"], 0.194118)
        self.assertEqual(report["total_tokens"], 60_094)
        self.assertEqual(report["results"], {
            "club-bridge-mixed-20260820-spm": {
                "deviation_segments": ["work-02"],
                "deviation_types": ["SPM_OUTSIDE_TARGET"],
                "verification_passed": True,
            },
            "club-atlas-men-20260828-recovery": {
                "deviation_segments": ["recovery-02"],
                "deviation_types": ["RECOVERY_DURATION_OUTSIDE_TARGET"],
                "verification_passed": True,
            },
        })


if __name__ == "__main__":
    unittest.main()
