from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import bundle_assembler  # noqa: E402
import source_adapters  # noqa: E402
import wake_tools  # noqa: E402


CASE_ID = "case-002-wind-shift-plan-deviation"
CASE_INPUT = ROOT / "data/fixtures" / CASE_ID / "input"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_public_summary(*, route_heading: float | None = 0.0) -> dict:
    telemetry = []
    input_hashes = {}
    for kind, filename in (
        ("SPEEDCOACH", "speedcoach.csv"),
        ("MOBILE", "mobile.csv"),
    ):
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

    for filename in ("plan.json", "environment.json", "context.json"):
        input_hashes[filename] = bundle_assembler.sha256_bytes(
            (CASE_INPUT / filename).read_bytes()
        )

    context = read_json(CASE_INPUT / "context.json")
    if route_heading is None:
        context["session_candidate"].pop("route_heading_deg")
    return bundle_assembler.assemble_case_summary(
        plan=read_json(CASE_INPUT / "plan.json"),
        context=context,
        environment=read_json(CASE_INPUT / "environment.json"),
        telemetry_sources=telemetry,
        input_hashes=input_hashes,
    )


class BundleAssemblerTests(unittest.TestCase):
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

    def test_human_only_observations_remain_explicit_evidence_gaps(self) -> None:
        summary = build_public_summary()
        gaps = " ".join(summary["evidence_gaps"]).lower()

        self.assertIn("resistance band", gaps)
        self.assertIn("technique", gaps)
        self.assertIn("perceived effort", gaps)

    def test_summary_assembly_is_deterministic(self) -> None:
        self.assertEqual(build_public_summary(), build_public_summary())

    def test_environment_analysis_abstains_when_route_heading_is_unknown(self) -> None:
        summary = build_public_summary(route_heading=None)

        result = wake_tools.analyze_environment(summary)

        self.assertEqual(result["status"], "INSUFFICIENT")
        self.assertEqual(result["causal_conclusion"], "NOT_ESTABLISHED")
        self.assertIn("route heading", result["reason"].lower())


if __name__ == "__main__":
    unittest.main()
