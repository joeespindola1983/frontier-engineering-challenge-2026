from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import generate_demo_club_batch  # noqa: E402
import verify_demo_club_batch  # noqa: E402


BATCH_ROOT = ROOT / "data/demo-club-batch"


class DemoClubBatchTests(unittest.TestCase):
    def test_batch_contains_all_recorded_activities_with_independent_sources(self) -> None:
        manifest = json.loads((BATCH_ROOT / "manifest.json").read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema_version"], "wake.demo_club_batch_manifest.v1")
        self.assertEqual(len(manifest["sessions"]), 52)
        self.assertEqual(len({item["session_id"] for item in manifest["sessions"]}), 52)
        self.assertEqual(
            sum(item["modality"].startswith("WATER") for item in manifest["sessions"]),
            38,
        )
        self.assertEqual(
            sum(item["modality"] == "ERG" for item in manifest["sessions"]),
            14,
        )
        self.assertTrue(all(item["provenance"] == "REAL_INFORMED_SYNTHETIC" for item in manifest["sessions"]))
        erg_sessions = [item for item in manifest["sessions"] if item["modality"] == "ERG"]
        self.assertTrue(all(len(item["athlete_ids"]) == 1 for item in erg_sessions))
        self.assertEqual(
            {item["workout_type"] for item in erg_sessions},
            {"FIXED_DISTANCE", "FIXED_TIME", "INTERVAL"},
        )
        self.assertTrue(all(item["training_role"] for item in manifest["sessions"]))
        self.assertTrue(all(item["association_status"] for item in erg_sessions))

    def test_batch_summary_is_derived_from_sources_and_preserves_validation_levels(self) -> None:
        report = verify_demo_club_batch.verify_batch(BATCH_ROOT)

        self.assertEqual(report["status"], "verified")
        self.assertEqual(report["counts"], {
            "records_received": 52,
            "data_validated": 52,
            "sessions_reconstructed": 52,
            "plan_compared": 51,
            "agent_verified": 2,
            "human_approved": 0,
        })
        self.assertEqual(report["routing"], {
            "RECONSTRUCTED_NO_MATERIAL_SIGNAL": 31,
            "RECONSTRUCTED_ALTERNATIVE": 17,
            "AGENT_VERIFIED": 2,
            "SOURCE_REQUIRED": 1,
            "HUMAN_CONTEXT_REQUIRED": 1,
        })
        self.assertEqual(report["deviations"], {
            "SPM_OUTSIDE_TARGET": 1,
            "RECOVERY_DURATION_OUTSIDE_TARGET": 1,
        })
        self.assertEqual(report["agent_cost"]["approximate_total_cost_usd"], 0.194118)
        self.assertEqual(report["agent_cost"]["total_tokens"], 60094)
        self.assertFalse(report["longitudinal_synthesis_executed"])

    def test_every_manifest_hash_matches_and_no_private_path_is_committed(self) -> None:
        manifest = json.loads((BATCH_ROOT / "manifest.json").read_text(encoding="utf-8"))
        serialized = json.dumps(manifest).lower()
        self.assertNotIn("/users/", serialized)
        self.assertNotIn("private-data", serialized)
        for session in manifest["sessions"]:
            session_dir = BATCH_ROOT / "sessions" / session["session_id"]
            for name, expected in session["source_sha256"].items():
                self.assertEqual(
                    hashlib.sha256((session_dir / name).read_bytes()).hexdigest(),
                    expected,
                )

    def test_generation_is_byte_reproducible_and_matches_committed_batch(self) -> None:
        with tempfile.TemporaryDirectory() as first_raw, tempfile.TemporaryDirectory() as second_raw:
            first = Path(first_raw)
            second = Path(second_raw)
            generate_demo_club_batch.build_demo_club_batch(first)
            generate_demo_club_batch.build_demo_club_batch(second)

            first_files = sorted(path.relative_to(first) for path in first.rglob("*") if path.is_file())
            second_files = sorted(path.relative_to(second) for path in second.rglob("*") if path.is_file())
            committed_files = sorted(path.relative_to(BATCH_ROOT) for path in BATCH_ROOT.rglob("*") if path.is_file())
            self.assertEqual(first_files, second_files)
            self.assertEqual(first_files, committed_files)
            for relative in first_files:
                self.assertEqual((first / relative).read_bytes(), (second / relative).read_bytes())
                self.assertEqual((first / relative).read_bytes(), (BATCH_ROOT / relative).read_bytes())


if __name__ == "__main__":
    unittest.main()
