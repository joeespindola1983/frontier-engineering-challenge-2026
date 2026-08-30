from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QA_ROOT = ROOT / "data" / "qa-interface"
SOURCE_ROOT = (
    ROOT
    / "data"
    / "fixtures"
    / "case-002-wind-shift-plan-deviation"
    / "input"
)
GUIDE = ROOT / "docs" / "OWNER_QA_GUIDE.md"
sys.path.insert(0, str(ROOT / "scripts"))

import build_owner_qa_pack  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class OwnerQaPackTests(unittest.TestCase):
    def test_full_replay_bundle_contains_only_the_five_upload_sources(self) -> None:
        bundle = QA_ROOT / "full-replay-bundle"
        expected = {
            "plan.json",
            "speedcoach.csv",
            "mobile.csv",
            "environment.json",
            "context.json",
        }

        self.assertEqual(
            {path.name for path in bundle.iterdir() if path.is_file()},
            expected,
        )
        for name in expected:
            self.assertEqual(sha256(bundle / name), sha256(SOURCE_ROOT / name))

        forbidden = ("ground-truth", "fixture-manifest", ".env", ".DS_Store")
        self.assertFalse(
            any(token in str(path) for path in QA_ROOT.rglob("*") for token in forbidden)
        )

    def test_pack_manifest_explains_full_and_minimum_evidence_scenarios(self) -> None:
        manifest = json.loads((QA_ROOT / "qa-pack-manifest.json").read_text())

        self.assertEqual(manifest["schema_version"], "wake.owner_qa_pack.v1")
        self.assertEqual(manifest["provenance"], "DERIVED_SYNTHETIC")
        self.assertEqual(manifest["privacy"], "PUBLIC_SYNTHETIC_ONLY")
        self.assertEqual(manifest["full_replay"]["file_count"], 5)
        self.assertEqual(
            manifest["minimum_preparation"]["files"],
            ["plan.json", "speedcoach.csv"],
        )
        self.assertEqual(manifest["full_replay"]["expected_cost_usd"], 0)
        self.assertEqual(manifest["minimum_preparation"]["expected_cost_usd"], 0)
        self.assertEqual(manifest["live_validation"]["start_count"], 3)
        self.assertEqual(manifest["live_validation"]["authorization_total_usd"], 0.60)

    def test_pack_is_byte_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            generated = Path(directory) / "qa-interface"
            build_owner_qa_pack.build_pack(generated)
            committed_files = {
                path.relative_to(QA_ROOT): sha256(path)
                for path in QA_ROOT.rglob("*")
                if path.is_file()
            }
            generated_files = {
                path.relative_to(generated): sha256(path)
                for path in generated.rglob("*")
                if path.is_file()
            }
            self.assertEqual(generated_files, committed_files)

    def test_owner_guide_is_sequential_and_has_expected_product_checks(self) -> None:
        guide = GUIDE.read_text(encoding="utf-8")

        for step in range(1, 17):
            self.assertIn(f"QA-{step:02d}", guide)
        for required in (
            "http://localhost:3000/",
            "Mode: replay (no model call)",
            "full-replay-bundle",
            "plan.json",
            "speedcoach.csv",
            "Validate and prepare · No agent call",
            "Validate and open replay",
            "52/52",
            "16 athletes",
            "10 crews",
            "Training Days",
            "Competition Review",
            "WAKE 7/7",
            "direct baseline 3/7",
            "not a semantic coaching-quality score",
            "US$0.00",
            "--live",
            "US$0.60",
            "three separately authorized starts",
            "Historical conditions added",
            "US$0.20 operational start authorization",
        ):
            self.assertIn(required, guide)


if __name__ == "__main__":
    unittest.main()
