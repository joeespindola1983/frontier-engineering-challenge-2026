from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import post_regatta_memory  # noqa: E402


class PostRegattaMemoryTests(unittest.TestCase):
    def test_builds_one_compact_combined_club_memory_input(self) -> None:
        summary = post_regatta_memory.build_memory_summary()

        self.assertEqual(summary["schema_version"], "wake.longitudinal_summary.v1")
        self.assertEqual(summary["pilot_id"], "club-post-regatta-memory")
        self.assertEqual(summary["scope"]["type"], "CLUB")
        self.assertEqual(summary["period"], {"start": "2026-08-17", "end": "2026-09-18"})
        self.assertEqual(summary["coverage"]["activity_count"], 102)
        self.assertEqual(summary["coverage"]["water_activity_count"], 68)
        self.assertEqual(summary["coverage"]["indoor_activity_count"], 34)
        self.assertEqual(summary["coverage"]["athlete_count"], 16)
        self.assertEqual(summary["coverage"]["crew_count"], 10)
        self.assertEqual(len(summary["period_comparisons"]), 6)
        self.assertFalse(summary["comparison_readiness"]["performance_trend_supported"])
        self.assertFalse(summary["model_called"])
        self.assertLess(len(json.dumps(summary)), 30_000)

        serialized = json.dumps(summary).lower()
        self.assertNotIn("latitude", serialized)
        self.assertNotIn("longitude", serialized)
        self.assertNotIn("real athlete", serialized)
        self.assertTrue(all(
            ref in summary["evidence_catalog"]
            for comparison in summary["period_comparisons"]
            for ref in comparison["evidence_refs"]
        ))

    def test_freezes_one_store_false_wake_request_at_the_standard_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            manifest_path = post_regatta_memory.write_memory_dry_run(output_dir)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            request_path = output_dir / manifest["request"]["path"]
            request = json.loads(request_path.read_text(encoding="utf-8"))

        self.assertFalse(manifest["api_called"])
        self.assertEqual(manifest["request_count"], 1)
        self.assertEqual(manifest["authorization"]["required_total_usd"], 0.2)
        self.assertFalse(manifest["authorization"]["provider_cap"])
        self.assertEqual(manifest["saved_reports"], {"count": 0, "reopen_cost_usd": 0})
        self.assertFalse(request["store"])
        self.assertEqual(request["model"], "gpt-5.6-terra")
        self.assertEqual(request["reasoning"], {"effort": "medium"})
        self.assertEqual(request["tool_choice"], "auto")

    def test_verifier_accepts_the_frozen_preflight_and_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            post_regatta_memory.write_memory_dry_run(output_dir)
            self.assertEqual(post_regatta_memory.verify_memory_directory(output_dir), [])

            request_path = output_dir / "requests" / "club-post-regatta-memory.wake_bounded_agent.json"
            request_path.write_text("{}\n", encoding="utf-8")
            self.assertTrue(any(
                "hash" in error.lower()
                for error in post_regatta_memory.verify_memory_directory(output_dir)
            ))

    def test_committed_paid_memory_matches_the_frozen_input_and_reopens_free(self) -> None:
        run_dir = ROOT / "evaluation" / "runs" / "post-regatta-memory-v1-20260830"
        manifest = json.loads((run_dir / "run-manifest.json").read_text(encoding="utf-8"))
        artifact = json.loads((run_dir / manifest["report"]).read_text(encoding="utf-8"))
        summary = post_regatta_memory.build_memory_summary()
        schema = json.loads(
            (ROOT / "schemas" / "longitudinal-intelligence-output.schema.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(manifest["api_called"])
        self.assertFalse(manifest["store"])
        self.assertEqual(manifest["authorized_cost_usd"], 0.2)
        self.assertEqual(manifest["reopen_cost_usd"], 0)
        self.assertEqual(manifest["execution_count"], 1)
        self.assertEqual(manifest["total_approximate_cost_usd"], 0.037384)
        self.assertTrue(artifact["verification"]["passed"])
        self.assertEqual(artifact["input_sha256"], post_regatta_memory.sha256_json(summary))
        self.assertEqual(
            post_regatta_memory.longitudinal_pilot.verify_longitudinal_output(
                output=artifact["output"], output_schema=schema, summary=summary
            ),
            [],
        )
        self.assertEqual(len(artifact["response_ids"]), 2)
        self.assertEqual(len(artifact["tool_events"]), 8)


if __name__ == "__main__":
    unittest.main()
