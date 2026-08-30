from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import score_longitudinal_pilot  # noqa: E402


class LongitudinalPilotResultTests(unittest.TestCase):
    def test_official_run_passes_capability_audit_without_post_hoc_quality_score(self) -> None:
        run_dir = ROOT / "evaluation/runs/longitudinal-pilot-v1-20260830"
        report = score_longitudinal_pilot.build_capability_audit(run_dir)

        self.assertEqual(report["schema_version"], "wake.longitudinal_capability_audit.v1")
        self.assertEqual(report["evaluation_design"], "POST_RUN_CAPABILITY_AUDIT_NOT_PREREGISTERED")
        self.assertIsNone(report["quality_score"])
        self.assertEqual(report["quality_conclusion"], "NO_DEMONSTRATED_QUALITY_GAIN")
        self.assertEqual(report["execution_count"], 4)
        self.assertTrue(all(item["all_checks_passed"] for item in report["reports"]))

        athlete = {
            item["workflow"]: item
            for item in report["reports"]
            if item["pilot_id"] == "athlete-lucas"
        }
        club = {
            item["workflow"]: item
            for item in report["reports"]
            if item["pilot_id"] == "club-coach"
        }
        self.assertEqual(
            athlete["DIRECT_BASELINE"]["checks"],
            athlete["WAKE_BOUNDED_AGENT"]["checks"],
        )
        self.assertEqual(
            club["DIRECT_BASELINE"]["checks"],
            club["WAKE_BOUNDED_AGENT"]["checks"],
        )
        self.assertEqual(report["costs"]["total_usd"], 0.110426)
        self.assertEqual(report["costs"]["direct_baseline_usd"], 0.06458)
        self.assertEqual(report["costs"]["wake_bounded_agent_usd"], 0.045846)
        self.assertLess(report["costs"]["wake_vs_baseline_percent"], 0)
        self.assertEqual(report["tool_use"]["wake_tool_events"], 16)
        self.assertEqual(report["tool_use"]["baseline_tool_events"], 0)

    def test_audit_is_byte_reproducible(self) -> None:
        run_dir = ROOT / "evaluation/runs/longitudinal-pilot-v1-20260830"
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "capability-audit.json"
            first = score_longitudinal_pilot.write_capability_audit(run_dir, output)
            first_bytes = first.read_bytes()
            second = score_longitudinal_pilot.write_capability_audit(run_dir, output)
            self.assertEqual(first_bytes, second.read_bytes())


if __name__ == "__main__":
    unittest.main()
