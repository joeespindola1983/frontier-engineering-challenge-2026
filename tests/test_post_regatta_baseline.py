from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import post_regatta_baseline  # noqa: E402


class PostRegattaBaselineTests(unittest.TestCase):
    def test_freezes_same_input_as_saved_wake_memory_without_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            manifest_path = post_regatta_baseline.write_baseline_dry_run(output_dir)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            input_path = output_dir / manifest["input"]["path"]
            request_path = output_dir / manifest["request"]["path"]
            summary = json.loads(input_path.read_text(encoding="utf-8"))
            request = json.loads(request_path.read_text(encoding="utf-8"))

        saved_wake_manifest = json.loads(
            (
                ROOT
                / "evaluation"
                / "runs"
                / "post-regatta-memory-v1-20260830"
                / "run-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertFalse(manifest["api_called"])
        self.assertEqual(manifest["request_count"], 1)
        self.assertEqual(manifest["request"]["workflow"], "DIRECT_BASELINE")
        self.assertEqual(manifest["authorization"]["required_total_usd"], 0.2)
        self.assertFalse(manifest["authorization"]["provider_cap"])
        self.assertEqual(
            manifest["input"]["semantic_sha256"],
            saved_wake_manifest["input_sha256"],
        )
        self.assertEqual(post_regatta_baseline.sha256_json(summary), saved_wake_manifest["input_sha256"])
        self.assertFalse(request["store"])
        self.assertNotIn("tools", request)
        self.assertNotIn("tool_choice", request)

    def test_capability_contract_is_frozen_before_baseline_execution(self) -> None:
        contract = post_regatta_baseline.load_capability_contract()

        self.assertEqual(contract["schema_version"], "wake.post_regatta_capability_contract.v1")
        self.assertEqual(contract["input_sha256"], post_regatta_baseline.sha256_json(
            post_regatta_baseline.post_regatta_memory.build_memory_summary()
        ))
        self.assertEqual(contract["evaluation_type"], "NON_SCORED_CAPABILITY_AUDIT")
        self.assertEqual(len(contract["checks"]), 7)
        self.assertEqual(
            {check["check_id"] for check in contract["checks"]},
            {
                "supported_comparisons",
                "club_trend_abstention",
                "environmental_noncausality",
                "missing_context_priorities",
                "unresolved_human_questions",
                "verified_deviation_review",
                "evidence_and_human_review_boundary",
            },
        )

    def test_preflight_verifier_detects_request_or_contract_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            post_regatta_baseline.write_baseline_dry_run(output_dir)
            self.assertEqual(post_regatta_baseline.verify_baseline_directory(output_dir), [])

            contract_path = output_dir / "capability-contract.json"
            contract_path.write_text("{}\n", encoding="utf-8")
            errors = post_regatta_baseline.verify_baseline_directory(output_dir)

        self.assertTrue(any("contract" in error.lower() and "hash" in error.lower() for error in errors))


if __name__ == "__main__":
    unittest.main()
