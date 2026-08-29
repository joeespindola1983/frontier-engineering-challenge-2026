from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import wake_product_service  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


CASE_ID = "case-002-wind-shift-plan-deviation"
COMMITTED_OUTPUT = (
    ROOT
    / "evaluation/runs/comparison-v1-20260829/agent/outputs"
    / f"{CASE_ID}.json"
)


class FakeLiveRunner:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def __call__(self, case_id: str) -> dict:
        self.calls.append(case_id)
        return copy.deepcopy(read_json(COMMITTED_OUTPUT))


class WakeProductServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.live_runner = FakeLiveRunner()
        self.service = wake_product_service.WakeProductService(
            root=ROOT,
            live_runner=self.live_runner,
        )

    def test_replay_investigation_uses_public_evidence_without_live_api(self) -> None:
        result = self.service.create_investigation(CASE_ID, mode="replay")

        self.assertEqual(result["status"], "QUESTION_REQUIRED")
        self.assertEqual(result["case_id"], CASE_ID)
        self.assertEqual(result["review"]["analysis"]["case_id"], CASE_ID)
        self.assertEqual(
            result["review"]["summary"]["case_id"],
            CASE_ID,
        )
        self.assertEqual(
            set(result["review"]["summary"]),
            {"case_id", "plan", "cross_source_findings"},
        )
        self.assertEqual(
            set(result["review"]["context"]),
            {"input_notice", "session_candidate"},
        )
        self.assertEqual(self.live_runner.calls, [])
        self.assertNotIn("ground-truth", json.dumps(result).lower())

    def test_live_mode_is_explicit_and_uses_the_injected_agent_runner(self) -> None:
        result = self.service.create_investigation(CASE_ID, mode="live")

        self.assertEqual(self.live_runner.calls, [CASE_ID])
        self.assertEqual(result["mode"], "live")
        self.assertEqual(result["status"], "QUESTION_REQUIRED")

    def test_checkpoint_answer_is_human_context_not_telemetry(self) -> None:
        investigation = self.service.create_investigation(CASE_ID, mode="replay")
        original_analysis = copy.deepcopy(investigation["review"]["analysis"])

        briefing = self.service.answer_checkpoint(
            investigation["checkpoint_id"],
            answer="YES",
        )

        self.assertEqual(briefing["equipment"]["status"], "HUMAN_CONFIRMED")
        self.assertEqual(briefing["equipment"]["source"], "Coach confirmation")
        self.assertEqual(
            self.service.get_investigation(investigation["investigation_id"])[
                "review"
            ]["analysis"],
            original_analysis,
        )

    def test_unknown_checkpoint_remains_unknown(self) -> None:
        investigation = self.service.create_investigation(CASE_ID, mode="replay")

        briefing = self.service.answer_checkpoint(
            investigation["checkpoint_id"],
            answer="UNKNOWN",
        )

        self.assertEqual(briefing["equipment"]["status"], "UNKNOWN")
        self.assertIsNone(briefing["equipment"]["value"])

    def test_goal_memory_changes_only_after_explicit_approval(self) -> None:
        investigation = self.service.create_investigation(CASE_ID, mode="replay")
        empty_goal = self.service.get_goal(investigation["goal_id"])
        briefing = self.service.answer_checkpoint(
            investigation["checkpoint_id"],
            answer="NO",
        )

        self.assertEqual(empty_goal["approvedSessions"], [])
        approved = self.service.approve_briefing(briefing["briefingId"])
        self.assertEqual(len(approved["approvedSessions"]), 1)
        self.assertEqual(
            approved["approvedSessions"][0]["equipment"]["value"],
            False,
        )
        self.assertIn(
            "does not establish a longitudinal trend",
            approved["currentConclusion"],
        )

    def test_http_boundary_exposes_tasks_not_low_level_agent_tools(self) -> None:
        api = wake_product_service.WakeProductApi(self.service)

        status, response = api.handle(
            "POST",
            "/api/investigations",
            {"case_id": CASE_ID, "mode": "replay"},
        )

        self.assertEqual(status, 201)
        self.assertEqual(response["status"], "QUESTION_REQUIRED")
        serialized = json.dumps(response)
        self.assertNotIn("assess_source_trust", serialized)
        self.assertNotIn("reconstruct_plan_execution", serialized)

    def test_http_boundary_completes_checkpoint_and_approval_transitions(self) -> None:
        api = wake_product_service.WakeProductApi(self.service)
        _, investigation = api.handle(
            "POST",
            "/api/investigations",
            {"case_id": CASE_ID, "mode": "replay"},
        )

        checkpoint_status, briefing = api.handle(
            "POST",
            f"/api/checkpoints/{investigation['checkpoint_id']}/answers",
            {"answer": "UNKNOWN"},
        )
        approval_status, goal = api.handle(
            "POST",
            f"/api/briefings/{briefing['briefingId']}/approve",
            {},
        )

        self.assertEqual(checkpoint_status, 200)
        self.assertEqual(approval_status, 200)
        self.assertEqual(len(goal["approvedSessions"]), 1)


if __name__ == "__main__":
    unittest.main()
