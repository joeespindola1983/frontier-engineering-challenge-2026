from __future__ import annotations

import base64
import copy
import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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
        self.output_override: dict | None = None
        self.approximate_cost_usd = 0.087826
        self.runtime_ms = 19_219
        self.usage = {
            "input_tokens": 27_917,
            "output_tokens": 2_666,
            "total_tokens": 30_583,
        }

    def __call__(self, summary: dict, evidence: dict[str, bytes]) -> dict:
        self.calls.append((copy.deepcopy(summary), copy.deepcopy(evidence)))
        output = copy.deepcopy(self.output_override or read_json(COMMITTED_OUTPUT))
        output["case_id"] = summary["case_id"]
        return {
            "analysis": output,
            "observability": {
                "approximate_cost_usd": self.approximate_cost_usd,
                "runtime_ms": self.runtime_ms,
                "usage": copy.deepcopy(self.usage),
            },
        }


class FakeWeatherProvider:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def __call__(self, lookup: dict) -> dict:
        self.calls.append(copy.deepcopy(lookup))
        first_hour = datetime.fromisoformat(
            lookup["query_start_utc"].replace("Z", "+00:00")
        ).replace(minute=0, second=0, microsecond=0)
        return {
            "latitude": lookup["latitude"],
            "longitude": lookup["longitude"],
            "utc_offset_seconds": 0,
            "timezone": "GMT",
            "hourly": {
                "time": [
                    (first_hour + timedelta(hours=index)).strftime("%Y-%m-%dT%H:%M")
                    for index in range(3)
                ],
                "temperature_2m": [18.0, 19.0, 20.0],
                "relative_humidity_2m": [90, 85, 80],
                "wind_speed_10m": [1.0, 2.0, 4.0],
                "wind_direction_10m": [180, 170, 20],
                "wind_gusts_10m": [1.5, 3.0, 6.0],
            },
        }


class WakeProductServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.live_runner = FakeLiveRunner()
        self.bundle_runner = FakeBundleRunner()
        self.service = wake_product_service.WakeProductService(
            root=ROOT,
            live_runner=self.live_runner,
            bundle_live_runner=self.bundle_runner,
        )

    def test_required_cost_authorization_config_is_positive_and_finite(self) -> None:
        self.assertEqual(
            wake_product_service.validate_required_cost_authorization(0.25),
            0.25,
        )
        for invalid in (0, -0.01, math.nan, math.inf):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "positive finite"):
                    wake_product_service.validate_required_cost_authorization(invalid)

    def test_product_live_workflow_loads_the_accepted_v2_assets(self) -> None:
        config, prompt = wake_product_service.load_product_workflow_assets(ROOT)

        self.assertEqual(config["config_version"], "wake.agent_config.v2")
        self.assertEqual(config["tool_contract_version"], "v2")
        self.assertIn("WAKE Investigation Agent Prompt v2", prompt)
        self.assertIn("boundary-derived from SPM classification", prompt)

    def test_weather_enrichment_requires_explicit_location_authorization(self) -> None:
        provider = FakeWeatherProvider()
        service = wake_product_service.WakeProductService(
            root=ROOT,
            weather_provider=provider,
        )
        speedcoach = service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach.csv",
            content=(CASE_INPUT / "speedcoach.csv").read_bytes(),
            uploaded_by_role="ATHLETE",
        )

        with self.assertRaisesRegex(ValueError, "location lookup authorization"):
            service.enrich_environment_from_speedcoach(
                speedcoach["source_id"],
                requested_by_role="ATHLETE",
                authorized_location_lookup=False,
            )

        self.assertEqual(provider.calls, [])

    def test_weather_enrichment_creates_one_cached_service_source(self) -> None:
        provider = FakeWeatherProvider()
        service = wake_product_service.WakeProductService(
            root=ROOT,
            weather_provider=provider,
            weather_now=lambda: datetime(2026, 8, 29, tzinfo=timezone.utc),
        )
        speedcoach = service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach.csv",
            content=(CASE_INPUT / "speedcoach.csv").read_bytes(),
            uploaded_by_role="ATHLETE",
        )

        first = service.enrich_environment_from_speedcoach(
            speedcoach["source_id"],
            requested_by_role="ATHLETE",
            authorized_location_lookup=True,
        )
        second = service.enrich_environment_from_speedcoach(
            speedcoach["source_id"],
            requested_by_role="ATHLETE",
            authorized_location_lookup=True,
        )

        self.assertFalse(first["lookup"]["cache_hit"])
        self.assertTrue(second["lookup"]["cache_hit"])
        self.assertEqual(first["source"]["source_id"], second["source"]["source_id"])
        self.assertEqual(first["source"]["kind"], "ENVIRONMENT")
        self.assertEqual(first["source"]["provenance"]["origin_role"], "SERVICE")
        self.assertEqual(first["source"]["provenance"]["uploaded_by_role"], "ATHLETE")
        self.assertEqual(first["lookup"]["location_precision_decimals"], 2)
        self.assertEqual(first["preview"]["provider"], "Open-Meteo")
        self.assertEqual(first["preview"]["sample_count"], 3)
        self.assertEqual(first["preview"]["wind_speed_range_m_s"], [1.0, 4.0])
        self.assertEqual(first["preview"]["gust_max_m_s"], 6.0)
        self.assertEqual(first["preview"]["temperature_range_c"], [18.0, 20.0])
        self.assertEqual(first["preview"]["relative_humidity_range_pct"], [80.0, 90.0])
        self.assertEqual(first["preview"]["causal_conclusion"], "NOT_ESTABLISHED")
        self.assertNotIn("latitude", json.dumps(first["preview"]).lower())
        self.assertNotIn("longitude", json.dumps(first["preview"]).lower())
        self.assertNotIn("content", json.dumps(first).lower())
        self.assertEqual(len(provider.calls), 1)

    def test_weather_enrichment_http_endpoint_returns_a_bundle_ready_source(self) -> None:
        provider = FakeWeatherProvider()
        service = wake_product_service.WakeProductService(
            root=ROOT,
            weather_provider=provider,
            weather_now=lambda: datetime(2026, 8, 29, tzinfo=timezone.utc),
        )
        api = wake_product_service.WakeProductApi(service)
        speedcoach = service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach.csv",
            content=(CASE_INPUT / "speedcoach.csv").read_bytes(),
        )

        status, result = api.handle(
            "POST",
            "/api/environment-enrichments",
            {
                "speedcoach_source_id": speedcoach["source_id"],
                "requested_by_role": "COACH",
                "authorized_location_lookup": True,
            },
        )

        self.assertEqual(status, 201)
        self.assertEqual(result["source"]["kind"], "ENVIRONMENT")
        self.assertEqual(result["source"]["status"], "READY")
        self.assertEqual(result["lookup"]["provider"], "Open-Meteo")

    def test_enriched_environment_can_join_the_prepared_agent_bundle(self) -> None:
        provider = FakeWeatherProvider()
        service = wake_product_service.WakeProductService(
            root=ROOT,
            weather_provider=provider,
            weather_now=lambda: datetime(2026, 8, 29, tzinfo=timezone.utc),
        )
        selected = []
        for kind, filename in (
            ("PLAN", "plan.json"),
            ("SPEEDCOACH", "speedcoach.csv"),
            ("CONTEXT", "context.json"),
        ):
            source = service.upload_source(
                kind=kind,
                name=filename,
                content=(CASE_INPUT / filename).read_bytes(),
                uploaded_by_role="ATHLETE",
            )
            selected.append(source["source_id"])
        environment = service.enrich_environment_from_speedcoach(
            selected[1],
            requested_by_role="ATHLETE",
            authorized_location_lookup=True,
        )
        selected.append(environment["source"]["source_id"])

        prepared = service.prepare_source_bundle(selected)
        summary = service.source_bundles[prepared["bundle_id"]]["summary"]

        coverage = {item["kind"]: item["status"] for item in prepared["source_coverage"]}
        self.assertEqual(coverage["ENVIRONMENT"], "PRESENT")
        self.assertEqual(summary["environment"]["schema_version"], "wake.environment_timeline.v2")
        self.assertEqual(
            summary["environment"]["time_series_windows"][1][
                "relative_humidity_pct"
            ],
            85.0,
        )
        self.assertIn(
            "does not establish causation",
            summary["environment"]["method"],
        )

    def test_weather_enrichment_rejects_timezone_unknown_speedcoach(self) -> None:
        provider = FakeWeatherProvider()
        service = wake_product_service.WakeProductService(
            root=ROOT,
            weather_provider=provider,
        )
        speedcoach = service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach-vendor.csv",
            content=(
                ROOT
                / "data/fixtures/case-001-misaligned-double-scull/input/sources/speedcoach.csv"
            ).read_bytes(),
        )

        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            service.enrich_environment_from_speedcoach(
                speedcoach["source_id"],
                requested_by_role="COACH",
                authorized_location_lookup=True,
            )

        self.assertEqual(provider.calls, [])

    def test_weather_enrichment_uses_confirmed_timezone_for_vendor_speedcoach(self) -> None:
        provider = FakeWeatherProvider()
        service = wake_product_service.WakeProductService(
            root=ROOT,
            weather_provider=provider,
            weather_now=lambda: datetime(2026, 8, 29, tzinfo=timezone.utc),
        )
        speedcoach = service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach-vendor.csv",
            content=(
                ROOT
                / "data/fixtures/case-001-misaligned-double-scull/input/sources/speedcoach.csv"
            ).read_bytes(),
        )

        result = service.enrich_environment_from_speedcoach(
            speedcoach["source_id"],
            requested_by_role="COACH",
            authorized_location_lookup=True,
            session_timezone="America/Sao_Paulo",
        )

        self.assertEqual(result["lookup"]["time_zone_source"], "USER_SUPPLIED_IANA")
        self.assertEqual(result["lookup"]["assumed_timezone"], "America/Sao_Paulo")
        self.assertEqual(
            result["lookup"]["session_start_utc"],
            "2026-01-15T09:59:53.100000Z",
        )
        self.assertEqual(len(provider.calls), 1)

    def test_weather_provider_failure_leaves_the_core_bundle_usable(self) -> None:
        def failing_provider(_: dict) -> dict:
            raise ValueError("Weather provider unavailable.")

        service = wake_product_service.WakeProductService(
            root=ROOT,
            weather_provider=failing_provider,
        )
        selected = []
        for kind, filename in (
            ("PLAN", "plan.json"),
            ("SPEEDCOACH", "speedcoach.csv"),
        ):
            source = service.upload_source(
                kind=kind,
                name=filename,
                content=(CASE_INPUT / filename).read_bytes(),
            )
            selected.append(source["source_id"])

        with self.assertRaisesRegex(ValueError, "provider unavailable"):
            service.enrich_environment_from_speedcoach(
                selected[1],
                requested_by_role="COACH",
                authorized_location_lookup=True,
            )

        prepared = service.prepare_source_bundle(selected)
        coverage = {item["kind"]: item["status"] for item in prepared["source_coverage"]}
        self.assertEqual(coverage["ENVIRONMENT"], "ABSENT")
        self.assertTrue(
            any(
                gap.startswith("Environmental timeline is not supplied")
                for gap in prepared["evidence_gaps"]
            )
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
            answered_by_role="ATHLETE",
            recorded_by_role="ATHLETE",
            authority_basis="DIRECT_PARTICIPANT",
        )

        self.assertEqual(
            briefing["humanConfirmation"]["status"], "HUMAN_CONFIRMED"
        )
        self.assertEqual(
            briefing["humanConfirmation"]["source"], "Athlete direct confirmation"
        )
        self.assertEqual(
            self.service.get_investigation(investigation["investigation_id"])[
                "review"
            ]["analysis"],
            original_analysis,
        )

    def test_checkpoint_routes_actual_equipment_use_to_the_athlete(self) -> None:
        investigation = self.service.create_investigation(CASE_ID, mode="replay")

        checkpoint = investigation["review"]["checkpoint"]

        self.assertEqual(checkpoint["expected_respondent_role"], "ATHLETE")
        self.assertEqual(checkpoint["authority_scope"], "SESSION_EXECUTION")

    def test_checkpoint_records_answerer_recorder_and_authority_basis(self) -> None:
        investigation = self.service.create_investigation(CASE_ID, mode="replay")

        briefing = self.service.answer_checkpoint(
            investigation["checkpoint_id"],
            answer="YES",
            answered_by_role="ATHLETE",
            recorded_by_role="COACH",
            authority_basis="RELAYED_REPORT",
        )

        confirmation = briefing["humanConfirmation"]
        self.assertEqual(confirmation["expectedRespondentRole"], "ATHLETE")
        self.assertEqual(confirmation["answeredByRole"], "ATHLETE")
        self.assertEqual(confirmation["recordedByRole"], "COACH")
        self.assertEqual(confirmation["authorityBasis"], "RELAYED_REPORT")
        self.assertTrue(confirmation["matchesExpectedRespondent"])
        self.assertEqual(confirmation["source"], "Athlete report recorded by coach")

    def test_confirmed_checkpoint_rejects_missing_answer_provenance(self) -> None:
        investigation = self.service.create_investigation(CASE_ID, mode="replay")

        with self.assertRaisesRegex(ValueError, "answer provenance"):
            self.service.answer_checkpoint(
                investigation["checkpoint_id"],
                answer="YES",
            )

    def test_unknown_checkpoint_remains_unknown(self) -> None:
        investigation = self.service.create_investigation(CASE_ID, mode="replay")

        briefing = self.service.answer_checkpoint(
            investigation["checkpoint_id"],
            answer="UNKNOWN",
        )

        self.assertEqual(briefing["humanConfirmation"]["status"], "UNKNOWN")
        self.assertIsNone(briefing["humanConfirmation"]["value"])

    def test_goal_memory_changes_only_after_explicit_approval(self) -> None:
        investigation = self.service.create_investigation(CASE_ID, mode="replay")
        empty_goal = self.service.get_goal(investigation["goal_id"])
        briefing = self.service.answer_checkpoint(
            investigation["checkpoint_id"],
            answer="NO",
            answered_by_role="ATHLETE",
            recorded_by_role="ATHLETE",
            authority_basis="DIRECT_PARTICIPANT",
        )

        self.assertEqual(empty_goal["approvedSessions"], [])
        approved = self.service.approve_briefing(briefing["briefingId"])
        self.assertEqual(len(approved["approvedSessions"]), 1)
        self.assertEqual(
            approved["approvedSessions"][0]["humanConfirmation"]["value"],
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
            {
                "answer": "YES",
                "answered_by_role": "ATHLETE",
                "recorded_by_role": "ATHLETE",
                "authority_basis": "DIRECT_PARTICIPANT",
            },
        )
        approval_status, goal = api.handle(
            "POST",
            f"/api/briefings/{briefing['briefingId']}/approve",
            {},
        )

        self.assertEqual(checkpoint_status, 200)
        self.assertEqual(
            briefing["humanConfirmation"]["source"],
            "Athlete direct confirmation",
        )
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

    def test_source_provenance_separates_uploader_from_source_authority(self) -> None:
        plan = self.service.upload_source(
            kind="PLAN",
            name="plan.json",
            content=(CASE_INPUT / "plan.json").read_bytes(),
            uploaded_by_role="ATHLETE",
        )
        speedcoach = self.service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach.csv",
            content=(CASE_INPUT / "speedcoach.csv").read_bytes(),
            uploaded_by_role="COACH",
        )

        self.assertEqual(
            plan["provenance"],
            {
                "uploaded_by_role": "ATHLETE",
                "origin_role": "COACH",
                "authority_scope": "TRAINING_PRESCRIPTION",
            },
        )
        self.assertEqual(
            speedcoach["provenance"],
            {
                "uploaded_by_role": "COACH",
                "origin_role": "DEVICE",
                "authority_scope": "MEASURED_TELEMETRY",
            },
        )

    def test_same_source_uploaded_by_different_roles_keeps_both_contributions(self) -> None:
        content = (CASE_INPUT / "plan.json").read_bytes()

        athlete_upload = self.service.upload_source(
            kind="PLAN",
            name="plan.json",
            content=content,
            uploaded_by_role="ATHLETE",
        )
        coach_upload = self.service.upload_source(
            kind="PLAN",
            name="plan.json",
            content=content,
            uploaded_by_role="COACH",
        )

        self.assertNotEqual(athlete_upload["source_id"], coach_upload["source_id"])
        self.assertEqual(
            self.service.get_source(athlete_upload["source_id"])["provenance"][
                "uploaded_by_role"
            ],
            "ATHLETE",
        )
        self.assertEqual(
            self.service.get_source(coach_upload["source_id"])["provenance"][
                "uploaded_by_role"
            ],
            "COACH",
        )

    def test_bundle_identity_preserves_who_contributed_the_same_plan(self) -> None:
        plan_content = (CASE_INPUT / "plan.json").read_bytes()
        speedcoach = self.service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach.csv",
            content=(CASE_INPUT / "speedcoach.csv").read_bytes(),
            uploaded_by_role="ATHLETE",
        )
        athlete_plan = self.service.upload_source(
            kind="PLAN",
            name="plan.json",
            content=plan_content,
            uploaded_by_role="ATHLETE",
        )
        coach_plan = self.service.upload_source(
            kind="PLAN",
            name="plan.json",
            content=plan_content,
            uploaded_by_role="COACH",
        )

        athlete_bundle = self.service.prepare_source_bundle(
            [athlete_plan["source_id"], speedcoach["source_id"]]
        )
        coach_bundle = self.service.prepare_source_bundle(
            [coach_plan["source_id"], speedcoach["source_id"]]
        )

        self.assertEqual(
            athlete_bundle["summary_sha256"], coach_bundle["summary_sha256"]
        )
        self.assertNotEqual(athlete_bundle["bundle_id"], coach_bundle["bundle_id"])
        self.assertEqual(
            athlete_bundle["source_contributions"][0]["provenance"][
                "uploaded_by_role"
            ],
            "ATHLETE",
        )
        self.assertEqual(
            coach_bundle["source_contributions"][0]["provenance"][
                "uploaded_by_role"
            ],
            "COACH",
        )

    def test_source_upload_rejects_an_unknown_contributor_role(self) -> None:
        with self.assertRaisesRegex(ValueError, "uploader role"):
            self.service.upload_source(
                kind="PLAN",
                name="plan.json",
                content=(CASE_INPUT / "plan.json").read_bytes(),
                uploaded_by_role="ADMIN",
            )

    def test_device_telemetry_cannot_be_relabelled_as_human_origin(self) -> None:
        with self.assertRaisesRegex(ValueError, "origin role.*SPEEDCOACH"):
            self.service.upload_source(
                kind="SPEEDCOACH",
                name="speedcoach.csv",
                content=(CASE_INPUT / "speedcoach.csv").read_bytes(),
                uploaded_by_role="COACH",
                origin_role="COACH",
            )

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
        self.assertEqual(
            prepared["cost_authorization"],
            {
                "currency": "USD",
                "required_authorization_usd": 0.20,
                "hard_provider_cap": False,
                "basis": "START_GATE_WITH_POST_RUN_USAGE",
            },
        )
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
            authorized_cost_usd=0.20,
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
            {"mode": "live", "authorized_cost_usd": 0.20},
        )

        self.assertEqual(status, 201)
        self.assertEqual(result["status"], "AGENT_COMPLETED")
        self.assertTrue(result["agent_called"])
        self.assertEqual(result["analysis"]["case_id"], CASE_ID)
        self.assertEqual(
            set(result["review"]),
            {"analysis", "summary", "context", "checkpoint"},
        )
        self.assertEqual(
            result["review"]["checkpoint"]["expected_respondent_role"],
            "ATHLETE",
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
            {"mode": "live", "authorized_cost_usd": 0.20},
        )
        self.assertEqual(repeated_status, 200)
        self.assertEqual(repeated, result)
        self.assertEqual(len(self.bundle_runner.calls), 1)

    def test_live_bundle_requires_explicit_cost_authorization_before_runner(self) -> None:
        prepared = self.service.prepare_source_bundle(
            self._upload_public_bundle(kinds=("PLAN", "SPEEDCOACH"))
        )

        with self.assertRaisesRegex(ValueError, "cost authorization"):
            self.service.execute_source_bundle(
                prepared["bundle_id"],
                mode="live",
            )
        with self.assertRaisesRegex(ValueError, "cost authorization"):
            self.service.execute_source_bundle(
                prepared["bundle_id"],
                mode="live",
                authorized_cost_usd=math.nan,
            )

        self.assertEqual(self.bundle_runner.calls, [])

    def test_live_cost_observability_and_ledger_use_actual_runner_usage_once(self) -> None:
        prepared = self.service.prepare_source_bundle(
            self._upload_public_bundle(kinds=("PLAN", "SPEEDCOACH"))
        )

        result, created = self.service.execute_source_bundle(
            prepared["bundle_id"],
            mode="live",
            authorized_cost_usd=0.20,
        )
        repeated, repeated_created = self.service.execute_source_bundle(
            prepared["bundle_id"],
            mode="live",
        )
        ledger = self.service.get_cost_summary()

        self.assertTrue(created)
        self.assertFalse(repeated_created)
        self.assertEqual(repeated, result)
        self.assertEqual(
            result["cost"],
            {
                "currency": "USD",
                "authorized_cost_usd": 0.20,
                "approximate_cost_usd": 0.087826,
                "status": "WITHIN_AUTHORIZATION",
                "hard_provider_cap": False,
                "usage": self.bundle_runner.usage,
                "runtime_ms": self.bundle_runner.runtime_ms,
            },
        )
        self.assertEqual(ledger["execution_count"], 1)
        self.assertEqual(ledger["approximate_total_cost_usd"], 0.087826)
        self.assertEqual(ledger["total_usage"], self.bundle_runner.usage)
        self.assertEqual(len(self.bundle_runner.calls), 1)

    def test_product_run_envelope_reads_analysis_and_trajectory_observability(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            output_path = directory / "output.json"
            trajectory_path = directory / "trajectory.json"
            output = read_json(COMMITTED_OUTPUT)
            output_path.write_text(json.dumps(output), encoding="utf-8")
            trajectory_path.write_text(
                json.dumps(
                    {
                        "usage": self.bundle_runner.usage,
                        "approximate_cost_usd": self.bundle_runner.approximate_cost_usd,
                        "runtime_ms": self.bundle_runner.runtime_ms,
                    }
                ),
                encoding="utf-8",
            )

            envelope = wake_product_service.load_product_run_envelope(
                {
                    "output_path": output_path,
                    "trajectory_path": trajectory_path,
                }
            )

        self.assertEqual(envelope["analysis"], output)
        self.assertEqual(
            envelope["observability"],
            {
                "usage": self.bundle_runner.usage,
                "approximate_cost_usd": self.bundle_runner.approximate_cost_usd,
                "runtime_ms": self.bundle_runner.runtime_ms,
            },
        )

    def test_http_execution_authorizes_cost_and_exposes_process_ledger(self) -> None:
        prepared = self.service.prepare_source_bundle(
            self._upload_public_bundle(kinds=("PLAN", "SPEEDCOACH"))
        )
        api = wake_product_service.WakeProductApi(self.service)

        status, result = api.handle(
            "POST",
            f"/api/source-bundles/{prepared['bundle_id']}/execute",
            {"mode": "live", "authorized_cost_usd": 0.20},
        )
        ledger_status, ledger = api.handle("GET", "/api/runtime/costs")

        self.assertEqual(status, 201)
        self.assertEqual(result["cost"]["status"], "WITHIN_AUTHORIZATION")
        self.assertEqual(ledger_status, 200)
        self.assertEqual(ledger["execution_count"], 1)
        self.assertEqual(ledger["approximate_total_cost_usd"], 0.087826)

    def test_new_bundle_continues_through_generic_checkpoint_and_memory(self) -> None:
        plan = read_json(CASE_INPUT / "plan.json")
        plan.update(
            {
                "plan_id": "synthetic-plan-short-rate",
                "goal_id": "synthetic-goal-short-rate",
                "coach_language": "2 x 500 m at 25-27 SPM.",
                "blocks": [
                    {
                        "block_id": "short-rate",
                        "kind": "WORK",
                        "repetitions": 2,
                        "distance_m": 500,
                        "duration_s": None,
                        "stroke_rate": {"min_spm": 25, "max_spm": 27},
                        "zone": "B3",
                        "zone_system": "STANDARD_ROWING_ZONES",
                        "recovery": {
                            "min_s": 120,
                            "max_s": 180,
                            "mode": "ACTIVE_LIGHT_ROWING",
                        },
                        "equipment": [],
                        "instructions": [],
                    }
                ],
            }
        )
        plan_source = self.service.upload_source(
            kind="PLAN",
            name="short-plan.json",
            content=json.dumps(plan).encode("utf-8"),
        )
        speedcoach_source = self.service.upload_source(
            kind="SPEEDCOACH",
            name="speedcoach.csv",
            content=(CASE_INPUT / "speedcoach.csv").read_bytes(),
        )
        prepared = self.service.prepare_source_bundle(
            [plan_source["source_id"], speedcoach_source["source_id"]]
        )

        output = read_json(COMMITTED_OUTPUT)
        output["segments"] = output["segments"][:3]
        output["segments"][0]["average_spm"] = 26.0
        output["segments"][2]["average_spm"] = 23.0
        output["deviations"] = [
            {
                "confidence": 0.91,
                "description": (
                    "Work-02 averaged 23.0 SPM, below the prescribed 25-27 SPM range."
                ),
                "evidence_refs": ["input/plan.json", "input/speedcoach.csv"],
                "segment_ref": "work-02",
                "type": "STROKE_RATE_BELOW_PRESCRIPTION",
            }
        ]
        output["follow_up_questions"] = [
            "Did an equipment malfunction affect work interval two?"
        ]
        output["coach_briefing"] = (
            "Two work intervals were reconstructed; the second was below target SPM."
        )
        self.bundle_runner.output_override = output

        execution, _ = self.service.execute_source_bundle(
            prepared["bundle_id"], mode="live", authorized_cost_usd=0.20
        )

        self.assertEqual(execution["investigation_status"], "QUESTION_REQUIRED")
        self.assertTrue(execution["investigation_id"].startswith("investigation-"))
        self.assertTrue(execution["checkpoint_id"].startswith("checkpoint-"))
        briefing = self.service.answer_checkpoint(
            execution["checkpoint_id"],
            answer="YES",
            answered_by_role="ATHLETE",
            recorded_by_role="ATHLETE",
            authority_basis="DIRECT_PARTICIPANT",
        )
        self.assertEqual(briefing["title"], "2 x 500 m · rowing session")
        self.assertEqual(len(briefing["workIntervals"]), 2)
        self.assertEqual(briefing["workIntervals"][0]["targetMinSpm"], 25)
        self.assertEqual(briefing["workIntervals"][0]["targetMaxSpm"], 27)
        attention = next(
            finding
            for finding in briefing["findings"]
            if finding["status"] == "ATTENTION"
        )
        self.assertEqual(attention["title"], "Work interval 2 needs attention.")
        self.assertIn("1 plan deviation needs coach review", briefing["headline"])
        self.assertEqual(
            briefing["humanConfirmation"]["question"],
            "Did an equipment malfunction affect work interval two?",
        )
        serialized_briefing = json.dumps(briefing).lower()
        self.assertNotIn("resistance band", serialized_briefing)
        self.assertNotIn("work interval five", serialized_briefing)
        self.assertNotIn("all six", serialized_briefing)

        goal = self.service.approve_briefing(briefing["briefingId"])
        self.assertEqual(len(goal["approvedSessions"]), 1)
        self.assertEqual(
            goal["approvedSessions"][0]["humanConfirmation"]["answer"],
            "YES",
        )
        self.assertIn("does not establish a longitudinal trend", goal["currentConclusion"])


if __name__ == "__main__":
    unittest.main()
