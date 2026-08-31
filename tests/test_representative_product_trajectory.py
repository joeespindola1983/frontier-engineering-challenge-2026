from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from scripts.build_representative_product_trajectory import build_trajectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_representative_product_trajectory.py"
ARTIFACT = ROOT / "evaluation" / "trajectories" / "representative-product-replay-v1.json"


class RepresentativeProductTrajectoryTests(unittest.TestCase):
    def test_trace_covers_agent_tools_human_answer_and_memory_approval(self) -> None:
        trajectory = build_trajectory(ROOT)

        self.assertEqual(trajectory["trajectory_type"], "REPRESENTATIVE_REPLAY")
        self.assertFalse(trajectory["model_called"])
        self.assertFalse(trajectory["private_chain_of_thought_stored"])
        event_types = [event["type"] for event in trajectory["events"]]
        self.assertEqual(
            event_types,
            [
                "SOURCES_SELECTED",
                "BUNDLE_PREPARED",
                "AGENT_RESULT_REPLAYED",
                "COACH_VIEWED",
                "HUMAN_CHECKPOINT_REQUESTED",
                "HUMAN_CHECKPOINT_ANSWERED",
                "BRIEFING_VERIFIED",
                "MEMORY_APPROVAL_REQUESTED",
                "COACH_APPROVED_MEMORY",
            ],
        )
        answer = trajectory["events"][5]
        self.assertEqual(answer["answered_by_role"], "ATHLETE")
        self.assertEqual(answer["recorded_by_role"], "COACH")
        self.assertEqual(answer["authority_basis"], "RELAYED_REPORT")
        self.assertEqual(answer["effect_on_telemetry"], "NONE")

    def test_committed_trace_is_byte_reproducible(self) -> None:
        self.assertTrue(ARTIFACT.is_file())
        committed = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(committed, build_trajectory(ROOT))

        result = subprocess.run(
            [str(SCRIPT)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("Representative product trajectory verified", result.stdout)


if __name__ == "__main__":
    unittest.main()
