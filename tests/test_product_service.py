from __future__ import annotations

import base64
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
CASE_INPUT = ROOT / "data/fixtures" / CASE_ID / "input"
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


class FakeBundleRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[dict, dict[str, bytes]]] = []

    def __call__(self, summary: dict, evidence: dict[str, bytes]) -> dict:
        self.calls.append((copy.deepcopy(summary), copy.deepcopy(evidence)))
        output = copy.deepcopy(read_json(COMMITTED_OUTPUT))
        output["case_id"] = summary["case_id"]
        return output


class WakeProductServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.live_runner = FakeLiveRunner()
        self.bundle_runner = FakeBundleRunner()
        self.service = wake_product_service.WakeProductService(
            root=ROOT,
            live_runner=self.live_runner,
            bundle_live_runner=self.bundle_runner,
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

    def test_independent_public_sources_can_start_the_exact_replay(self) -> None:
        source_ids = []
        for kind, filename in (
            ("PLAN", "plan.json"),
            ("SPEEDCOACH", "speedcoach.csv"),
            ("MOBILE", "mobile.csv"),
            ("ENVIRONMENT", "environment.json"),
            ("CONTEXT", "context.json"),
        ):
            source = self.service.upload_source(
                kind=kind,
                name=filename,
                content=(CASE_INPUT / filename).read_bytes(),
            )
            source_ids.append(source["source_id"])
            self.assertEqual(source["status"], "READY")
            self.assertNotIn("content", source)

        result = self.service.create_investigation_from_sources(
            source_ids,
            mode="replay",
        )

        self.assertEqual(result["case_id"], CASE_ID)
        self.assertEqual(result["status"], "QUESTION_REQUIRED")
        self.assertEqual(self.live_runner.calls, [])

    def test_invalid_plan_is_rejected_before_it_becomes_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "training plan"):
            self.service.upload_source(
                kind="PLAN",
                name="plan.json",
                content=b"{}",
            )

    def test_normalized_telemetry_requires_the_analysis_columns(self) -> None:
        with self.assertRaisesRegex(ValueError, "required columns"):
            self.service.upload_source(
                kind="SPEEDCOACH",
                name="speedcoach.csv",
                content=b"timestamp,distance_m\n2026-01-20T06:00:00Z,0\n",
            )

    def test_source_name_cannot_escape_the_source_store(self) -> None:
        with self.assertRaisesRegex(ValueError, "file name"):
            self.service.upload_source(
                kind="PLAN",
                name="../plan.json",
                content=(CASE_INPUT / "plan.json").read_bytes(),
            )

    def test_raw_vendor_and_native_mobile_formats_are_identified(self) -> None:
        case_one = (
            ROOT
            / "data/fixtures/case-001-misaligned-double-scull/input/sources"
        )
        speedcoach = self.service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach-export.csv",
            content=(case_one / "speedcoach.csv").read_bytes(),
        )
        mobile = self.service.upload_source(
            kind="MOBILE",
            name="mobile-sensor.csv",
            content=(case_one / "mobile-ios-sensor.csv").read_bytes(),
        )

        self.assertEqual(speedcoach["format"], "SPEEDCOACH_VENDOR_CSV")
        self.assertEqual(mobile["format"], "WAKE_MOBILE_SENSOR_CSV")
        self.assertEqual(speedcoach["normalization"]["row_count"], 549)
        self.assertIn(
            "TIMEZONE_UNKNOWN",
            speedcoach["normalization"]["quality_flags"],
        )
        self.assertEqual(mobile["normalization"]["row_count"], 923)
        self.assertEqual(mobile["normalization"]["positive_spm_rows"], 0)
        self.assertIn(
            "RAW_SPM_ABSENT",
            mobile["normalization"]["quality_flags"],
        )

    def test_source_metadata_endpoint_never_returns_normalized_rows(self) -> None:
        api = wake_product_service.WakeProductApi(self.service)
        source = self.service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach.csv",
            content=(
                ROOT
                / "data/fixtures/case-001-misaligned-double-scull/input/sources/speedcoach.csv"
            ).read_bytes(),
        )

        status, metadata = api.handle(
            "GET",
            f"/api/sources/{source['source_id']}",
        )

        self.assertEqual(status, 200)
        self.assertEqual(metadata["normalization"]["row_count"], 549)
        serialized = json.dumps(metadata)
        self.assertNotIn("normalized_csv", serialized)
        self.assertNotIn("_content", serialized)

    def test_modified_bundle_cannot_inherit_the_committed_replay(self) -> None:
        source_ids = []
        for kind, filename in (
            ("PLAN", "plan.json"),
            ("SPEEDCOACH", "speedcoach.csv"),
            ("MOBILE", "mobile.csv"),
            ("ENVIRONMENT", "environment.json"),
            ("CONTEXT", "context.json"),
        ):
            content = (CASE_INPUT / filename).read_bytes()
            if kind == "CONTEXT":
                context = json.loads(content)
                context["investigation_request"] += " New question."
                content = json.dumps(context).encode("utf-8")
            source_ids.append(
                self.service.upload_source(
                    kind=kind,
                    name=filename,
                    content=content,
                )["source_id"]
            )

        with self.assertRaisesRegex(ValueError, "committed public demonstration bundle"):
            self.service.create_investigation_from_sources(source_ids, mode="replay")

    def test_http_source_upload_accepts_base64_and_returns_metadata_only(self) -> None:
        api = wake_product_service.WakeProductApi(self.service)
        encoded = base64.b64encode((CASE_INPUT / "plan.json").read_bytes()).decode()

        status, response = api.handle(
            "POST",
            "/api/sources",
            {"kind": "PLAN", "name": "plan.json", "content_base64": encoded},
        )

        self.assertEqual(status, 201)
        self.assertEqual(response["kind"], "PLAN")
        self.assertEqual(response["status"], "READY")
        self.assertNotIn("content", response)

    def _upload_public_bundle(
        self,
        *,
        context_suffix: str = "",
        kinds: tuple[str, ...] = (
            "PLAN",
            "SPEEDCOACH",
            "MOBILE",
            "ENVIRONMENT",
            "CONTEXT",
        ),
    ) -> list[str]:
        source_ids = []
        for kind, filename in (
            ("PLAN", "plan.json"),
            ("SPEEDCOACH", "speedcoach.csv"),
            ("MOBILE", "mobile.csv"),
            ("ENVIRONMENT", "environment.json"),
            ("CONTEXT", "context.json"),
        ):
            if kind not in kinds:
                continue
            content = (CASE_INPUT / filename).read_bytes()
            if kind == "CONTEXT" and context_suffix:
                context = json.loads(content)
                context["investigation_request"] += context_suffix
                content = json.dumps(context).encode("utf-8")
            source_ids.append(
                self.service.upload_source(
                    kind=kind,
                    name=filename,
                    content=content,
                )["source_id"]
            )
        return source_ids

    def test_minimum_plan_and_speedcoach_bundle_prepares_with_explicit_gaps(self) -> None:
        source_ids = self._upload_public_bundle(kinds=("PLAN", "SPEEDCOACH"))

        prepared = self.service.prepare_source_bundle(source_ids)

        self.assertEqual(prepared["status"], "READY_FOR_LIVE")
        self.assertEqual(prepared["source_count"], 2)
        self.assertEqual(
            prepared["source_coverage"],
            [
                {"kind": "PLAN", "role": "CORE", "status": "PRESENT"},
                {"kind": "SPEEDCOACH", "role": "CORE", "status": "PRESENT"},
                {"kind": "MOBILE", "role": "ENHANCER", "status": "ABSENT"},
                {"kind": "ENVIRONMENT", "role": "ENHANCER", "status": "ABSENT"},
                {"kind": "CONTEXT", "role": "ENHANCER", "status": "ABSENT"},
            ],
        )
        self.assertEqual(prepared["finding_types"], [])
        gaps = " ".join(prepared["evidence_gaps"]).lower()
        self.assertIn("mobile telemetry is not supplied", gaps)
        self.assertIn("environmental timeline is not supplied", gaps)
        self.assertIn("session context is not supplied", gaps)
        self.assertEqual(self.bundle_runner.calls, [])

    def test_preparation_rejects_a_bundle_without_a_core_source(self) -> None:
        speedcoach_only = self._upload_public_bundle(kinds=("SPEEDCOACH",))
        plan_only = self._upload_public_bundle(kinds=("PLAN",))

        with self.assertRaisesRegex(ValueError, "PLAN and SPEEDCOACH"):
            self.service.prepare_source_bundle(speedcoach_only)
        with self.assertRaisesRegex(ValueError, "PLAN and SPEEDCOACH"):
            self.service.prepare_source_bundle(plan_only)

    def test_minimum_bundle_execution_passes_only_supplied_evidence(self) -> None:
        prepared = self.service.prepare_source_bundle(
            self._upload_public_bundle(kinds=("PLAN", "SPEEDCOACH"))
        )

        result, created = self.service.execute_source_bundle(
            prepared["bundle_id"],
            mode="live",
        )

        self.assertTrue(created)
        self.assertEqual(result["status"], "AGENT_COMPLETED")
        summary, evidence = self.bundle_runner.calls[0]
        self.assertEqual(summary["case_id"], "uploaded-synthetic-plan-002")
        self.assertEqual(set(evidence), {"plan.json", "speedcoach.csv"})

    def test_uploaded_sources_prepare_a_new_agent_bundle_without_api_call(self) -> None:
        source_ids = self._upload_public_bundle()
        prepared = self.service.prepare_source_bundle(source_ids)

        self.assertEqual(prepared["status"], "READY_FOR_LIVE")
        self.assertEqual(prepared["case_id"], CASE_ID)
        self.assertFalse(prepared["agent_called"])
        self.assertEqual(len(prepared["summary_sha256"]), 64)
        self.assertEqual(prepared["source_count"], 5)
        self.assertEqual(
            set(prepared["finding_types"]),
            {"CLOCK_OFFSET", "DISTANCE_CONFLICT", "ROUTE_OVERLAP"},
        )
        self.assertEqual(self.live_runner.calls, [])

        stored_summary = self.service.source_bundles[prepared["bundle_id"]]["summary"]
        telemetry_upload_ids = {
            source_id
            for source_id in source_ids
            if self.service.sources[source_id]["kind"] in {"SPEEDCOACH", "MOBILE"}
        }
        self.assertEqual(
            {source["source_id"] for source in stored_summary["sources"]},
            telemetry_upload_ids,
        )

    def test_modified_evidence_prepares_a_distinct_summary_not_a_canned_answer(self) -> None:
        original = self.service.prepare_source_bundle(
            self._upload_public_bundle()
        )
        modified = self.service.prepare_source_bundle(
            self._upload_public_bundle(context_suffix=" New coach question.")
        )

        self.assertNotEqual(original["bundle_id"], modified["bundle_id"])
        self.assertNotEqual(original["summary_sha256"], modified["summary_sha256"])
        self.assertEqual(self.live_runner.calls, [])

    def test_prepare_endpoint_returns_compact_metadata_not_telemetry_rows(self) -> None:
        api = wake_product_service.WakeProductApi(self.service)

        status, response = api.handle(
            "POST",
            "/api/source-bundles/prepare",
            {"source_ids": self._upload_public_bundle()},
        )

        serialized = json.dumps(response).lower()
        self.assertEqual(status, 201)
        self.assertNotIn("time_series_windows", serialized)
        self.assertNotIn("normalized_content", serialized)
        self.assertNotIn("ground-truth", serialized)
        self.assertNotIn("stroke_rate_spm", serialized)
        self.assertFalse(response["agent_called"])

    def test_prepared_bundle_execution_is_explicit_and_uses_normalized_evidence(self) -> None:
        prepared = self.service.prepare_source_bundle(
            self._upload_public_bundle()
        )
        api = wake_product_service.WakeProductApi(self.service)

        with self.assertRaisesRegex(ValueError, "explicit live mode"):
            api.handle(
                "POST",
                f"/api/source-bundles/{prepared['bundle_id']}/execute",
                {},
            )
        self.assertEqual(self.bundle_runner.calls, [])

        status, result = api.handle(
            "POST",
            f"/api/source-bundles/{prepared['bundle_id']}/execute",
            {"mode": "live"},
        )

        self.assertEqual(status, 201)
        self.assertEqual(result["status"], "AGENT_COMPLETED")
        self.assertTrue(result["agent_called"])
        self.assertEqual(result["analysis"]["case_id"], CASE_ID)
        self.assertEqual(
            set(result["review"]),
            {"analysis", "summary", "context"},
        )
        self.assertEqual(result["review"]["summary"]["case_id"], CASE_ID)
        serialized_review = json.dumps(result["review"])
        self.assertNotIn("time_series_windows", serialized_review)
        self.assertNotIn("input_hashes", serialized_review)
        self.assertEqual(len(self.bundle_runner.calls), 1)
        summary, evidence = self.bundle_runner.calls[0]
        self.assertEqual(summary["case_id"], CASE_ID)
        self.assertEqual(
            set(evidence),
            {"plan.json", "speedcoach.csv", "mobile.csv", "environment.json", "context.json"},
        )
        self.assertTrue(
            evidence["speedcoach.csv"].startswith(
                b"timestamp,elapsed_s,distance_m,speed_m_s,stroke_rate_spm"
            )
        )
        self.assertEqual(self.live_runner.calls, [])

        repeated_status, repeated = api.handle(
            "POST",
            f"/api/source-bundles/{prepared['bundle_id']}/execute",
            {"mode": "live"},
        )
        self.assertEqual(repeated_status, 200)
        self.assertEqual(repeated, result)
        self.assertEqual(len(self.bundle_runner.calls), 1)


if __name__ == "__main__":
    unittest.main()
