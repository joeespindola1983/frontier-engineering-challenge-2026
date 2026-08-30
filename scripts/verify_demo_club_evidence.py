#!/usr/bin/env python3
"""Verify the public demo-club evidence bundles without calling a model."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import jsonschema

import bundle_assembler
import source_adapters
import wake_tools


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_ROOT = ROOT / "data" / "demo-club-evidence"
EXPECTED_DEVIATIONS = {
    "club-bridge-mixed-20260820-spm": ["work-02"],
    "club-atlas-men-20260828-recovery": ["recovery-02"],
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_privacy(fixture_root: Path) -> None:
    for path in fixture_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".csv", ".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8").lower()
        assert "/users/" not in text, f"Private path found: {path}"
        assert "private-data" not in text, f"Private data reference found: {path}"


def assemble_summary(case_dir: Path) -> dict:
    input_dir = case_dir / "input"
    speedcoach_path = input_dir / "speedcoach.csv"
    normalized = source_adapters.normalize_source(
        kind="SPEEDCOACH",
        content=speedcoach_path.read_bytes(),
        source_ref="input/speedcoach.csv",
    )
    return bundle_assembler.assemble_case_summary(
        plan=read_json(input_dir / "plan.json"),
        context=read_json(input_dir / "context.json"),
        environment=None,
        telemetry_sources=[
            {
                "kind": "SPEEDCOACH",
                "evidence_ref": "input/speedcoach.csv",
                "normalized_csv": normalized.normalized_csv,
                "normalization": normalized.report,
            }
        ],
        input_hashes={
            "plan.json": sha256(input_dir / "plan.json"),
            "context.json": sha256(input_dir / "context.json"),
            "speedcoach.csv": normalized.report["input_sha256"],
        },
    )


def verify_fixture_set(fixture_root: Path = DEFAULT_FIXTURE_ROOT) -> dict:
    manifest = read_json(fixture_root / "manifest.json")
    assert manifest["schema_version"] == "wake.demo_club_evidence_manifest.v1"
    assert manifest["boundary"].endswith("completed agent analyses.")
    assert {item["case_id"] for item in manifest["cases"]} == set(EXPECTED_DEVIATIONS)
    verify_privacy(fixture_root)

    plan_schema = read_json(ROOT / "schemas" / "training-plan.schema.json")
    fixtures = {}
    for item in manifest["cases"]:
        case_id = item["case_id"]
        case_dir = fixture_root / case_id
        input_dir = case_dir / "input"
        expected_files = {"context.json", "plan.json", "speedcoach.csv"}
        assert set(item["input_sha256"]) == expected_files
        for name, expected_hash in item["input_sha256"].items():
            assert sha256(input_dir / name) == expected_hash, f"Hash mismatch: {case_id}/{name}"

        jsonschema.validate(read_json(input_dir / "plan.json"), plan_schema)
        result = wake_tools.reconstruct_plan_execution(
            assemble_summary(case_dir),
            input_dir,
            contract_version="v2",
        )
        deviations = [item["segment_ref"] for item in result["plan_deviations"]]
        assert deviations == EXPECTED_DEVIATIONS[case_id], f"Deviation mismatch: {case_id}"
        fixtures[case_id] = {
            "deviation_segments": deviations,
            "execution_status": item["execution_status"],
            "execution_result_ref": item["execution_result_ref"],
            "input_count": len(item["input_sha256"]),
        }

    return {
        "status": "verified",
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
    }


def main() -> None:
    print(json.dumps(verify_fixture_set(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
