from __future__ import annotations

import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import bundle_assembler  # noqa: E402
import source_adapters  # noqa: E402
import weather_enrichment  # noqa: E402
import wake_tools  # noqa: E402


CASE_ID = "case-002-wind-shift-plan-deviation"
CASE_INPUT = ROOT / "data/fixtures" / CASE_ID / "input"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_public_summary(
    *,
    route_heading: float | None = 0.0,
    include_mobile: bool = True,
    include_environment: bool = True,
    include_context: bool = True,
) -> dict:
    telemetry = []
    input_hashes = {}
    telemetry_files = [("SPEEDCOACH", "speedcoach.csv")]
    if include_mobile:
        telemetry_files.append(("MOBILE", "mobile.csv"))
    for kind, filename in telemetry_files:
        content = (CASE_INPUT / filename).read_bytes()
        normalized = source_adapters.normalize_source(
            kind=kind,
            content=content,
            source_ref=f"input/{filename}",
        )
        telemetry.append(
            {
                "kind": kind,
                "evidence_ref": f"input/{filename}",
                "normalized_csv": normalized.normalized_csv,
                "normalization": normalized.report,
            }
        )
        input_hashes[filename] = normalized.report["input_sha256"]

    json_filenames = ["plan.json"]
    if include_environment:
        json_filenames.append("environment.json")
    if include_context:
        json_filenames.append("context.json")
    for filename in json_filenames:
        input_hashes[filename] = bundle_assembler.sha256_bytes(
            (CASE_INPUT / filename).read_bytes()
        )

    context = read_json(CASE_INPUT / "context.json") if include_context else None
    if context is not None and route_heading is None:
        context["session_candidate"].pop("route_heading_deg")
    return bundle_assembler.assemble_case_summary(
        plan=read_json(CASE_INPUT / "plan.json"),
        context=context,
        environment=(
            read_json(CASE_INPUT / "environment.json")
            if include_environment
            else None
        ),
        telemetry_sources=telemetry,
        input_hashes=input_hashes,
    )


class BundleAssemblerTests(unittest.TestCase):
    def test_plan_and_speedcoach_are_a_valid_minimum_evidence_bundle(self) -> None:
        summary = build_public_summary(
            include_mobile=False,
            include_environment=False,
            include_context=False,
        )
        schema = read_json(ROOT / "schemas/case-summary.schema.json")

        jsonschema.validate(instance=summary, schema=schema)
        self.assertEqual(summary["case_id"], "uploaded-synthetic-plan-002")
        self.assertEqual(
            summary["investigation_request"],
            "Compare the planned and performed session and state what remains unknown.",
        )
        self.assertEqual(
            [source["kind"] for source in summary["sources"]],
            ["SPEEDCOACH"],
        )
        self.assertEqual(summary["cross_source_findings"], [])
        self.assertIsNone(summary["environment"])
        gaps = " ".join(summary["evidence_gaps"]).lower()
        self.assertIn("mobile telemetry is not supplied", gaps)
        self.assertIn("environmental timeline is not supplied", gaps)
        self.assertIn("session context is not supplied", gaps)

    def test_speedcoach_only_route_is_selected_without_false_corroboration(self) -> None:
        summary = build_public_summary(
            include_mobile=False,
            include_environment=False,
            include_context=False,
        )

        trust = wake_tools.assess_source_trust(summary)
        alignment = wake_tools.assess_session_alignment(summary)

        self.assertEqual(
            trust["metrics"]["route"]["selected_source_id"],
            "speedcoach",
        )
        self.assertEqual(
            trust["metrics"]["route"]["corroborating_source_ids"],
            [],
        )
        self.assertEqual(trust["metrics"]["route"]["confidence"], "MEDIUM")
        self.assertIn(
            "single GPS source",
            " ".join(trust["metrics"]["route"]["reasons"]),
        )
        self.assertEqual(alignment["decision"], "INSUFFICIENT")

    def test_five_sources_become_a_valid_ground_truth_free_summary(self) -> None:
        summary = build_public_summary()
        schema = read_json(ROOT / "schemas/case-summary.schema.json")

        jsonschema.validate(instance=summary, schema=schema)
        self.assertEqual(summary["case_id"], CASE_ID)
        self.assertEqual(summary["plan"]["plan_id"], "synthetic-plan-002")
        self.assertEqual(len(summary["sources"]), 2)
        self.assertNotIn("ground-truth", json.dumps(summary).lower())

    def test_source_quality_preserves_missing_mobile_spm(self) -> None:
        summary = build_public_summary()
        by_kind = {source["kind"]: source for source in summary["sources"]}

        self.assertIn("SPM_PRESENT", by_kind["SPEEDCOACH"]["quality_flags"])
        self.assertIn("SPM_ALL_ZERO", by_kind["MOBILE"]["quality_flags"])
        self.assertEqual(by_kind["MOBILE"]["metrics"]["positive_spm_rows"], 0)
        self.assertIsNone(
            by_kind["MOBILE"]["metrics"]["average_positive_spm"]
        )
        self.assertEqual(
            len(by_kind["SPEEDCOACH"]["metrics"]["normalized_sha256"]),
            64,
        )

    def test_alignment_distance_and_route_findings_are_computed(self) -> None:
        summary = build_public_summary()
        findings = {
            finding["type"]: finding for finding in summary["cross_source_findings"]
        }

        self.assertEqual(
            findings["CLOCK_OFFSET"]["values"]["mobile_from_speedcoach_s"],
            37.0,
        )
        self.assertEqual(
            findings["DISTANCE_CONFLICT"]["values"]["difference_percent"],
            1.2,
        )
        overlap = findings["ROUTE_OVERLAP"]["values"]
        self.assertLess(overlap["speedcoach_to_mobile"]["p95_m"], 25)
        self.assertLess(overlap["mobile_to_speedcoach"]["p95_m"], 25)

    def test_environment_is_projected_against_the_known_route_heading(self) -> None:
        summary = build_public_summary()
        environment = summary["environment"]

        self.assertEqual(environment["route_heading_deg"], 0.0)
        self.assertLess(
            environment["time_series_windows"][0]["effective_headwind_m_s"],
            0,
        )
        self.assertGreater(
            environment["time_series_windows"][-1]["effective_headwind_m_s"],
            0,
        )
        self.assertIn("does not establish causation", environment["method"])

    def test_environment_derives_heading_from_speedcoach_gps_without_context(self) -> None:
        summary = build_public_summary(
            include_mobile=False,
            include_context=False,
        )
        environment = summary["environment"]

        self.assertAlmostEqual(environment["route_heading_deg"], 0.0, places=1)
        self.assertEqual(
            environment["route_heading_source"],
            "SPEEDCOACH_GPS_DERIVED",
        )
        self.assertIn("derived", environment["method"].lower())
        result = wake_tools.analyze_environment(summary)
        self.assertEqual(result["status"], "COMPLETED")

    def test_provider_environment_keeps_humidity_resolution_and_crosswind(self) -> None:
        speedcoach = (CASE_INPUT / "speedcoach.csv").read_bytes()
        lookup = weather_enrichment.build_weather_lookup(speedcoach)
        provider_environment = weather_enrichment.normalize_open_meteo_response(
            request=lookup,
            response={
                "latitude": 10.0,
                "longitude": 10.0,
                "utc_offset_seconds": 0,
                "timezone": "GMT",
                "hourly": {
                    "time": ["2026-01-20T09:00", "2026-01-20T10:00"],
                    "temperature_2m": [18.0, 20.0],
                    "relative_humidity_2m": [90, 80],
                    "wind_speed_10m": [2.0, 4.0],
                    "wind_direction_10m": [90, 0],
                    "wind_gusts_10m": [3.0, 6.0],
                },
            },
            retrieved_at=datetime(2026, 8, 29, tzinfo=timezone.utc),
        )
        summary = build_public_summary(include_environment=False)
        environment = bundle_assembler._environment_summary(
            provider_environment,
            summary["known_context"],
        )

        self.assertEqual(environment["source"]["temporal_resolution_minutes"], 60)
        self.assertIn("modeled hourly", " ".join(environment["limitations"]))
        first = environment["time_series_windows"][0]
        self.assertEqual(first["temperature_c"], 18.0)
        self.assertEqual(first["relative_humidity_pct"], 90.0)
        self.assertAlmostEqual(first["effective_headwind_m_s"], 0.0, places=3)
        self.assertAlmostEqual(first["effective_crosswind_m_s"], 2.0, places=3)

        analysis = wake_tools.analyze_environment(
            {**summary, "environment": environment}
        )
        self.assertEqual(analysis["temperature_range_c"], [18.0, 18.0])
        self.assertEqual(analysis["relative_humidity_range_pct"], [90.0, 90.0])
        self.assertEqual(
            analysis["condition_change"],
            "INSUFFICIENT_TEMPORAL_RESOLUTION",
        )
        self.assertIn("60-minute", " ".join(analysis["limitations"]))

    def test_human_only_observations_remain_explicit_evidence_gaps(self) -> None:
        summary = build_public_summary()
        gaps = " ".join(summary["evidence_gaps"]).lower()

        self.assertIn("resistance band", gaps)
        self.assertIn("technique", gaps)
        self.assertIn("perceived effort", gaps)

    def test_summary_assembly_is_deterministic(self) -> None:
        self.assertEqual(build_public_summary(), build_public_summary())

    def test_environment_analysis_abstains_when_route_heading_is_unknown(self) -> None:
        environment = bundle_assembler._environment_summary(
            read_json(CASE_INPUT / "environment.json"),
            {},
        )

        result = wake_tools.analyze_environment({"environment": environment})

        self.assertEqual(result["status"], "INSUFFICIENT")
        self.assertEqual(result["causal_conclusion"], "NOT_ESTABLISHED")
        self.assertIn("route heading", result["reason"].lower())


if __name__ == "__main__":
    unittest.main()
