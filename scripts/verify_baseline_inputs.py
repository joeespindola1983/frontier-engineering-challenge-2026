#!/usr/bin/env python3
"""Verify compact baseline inputs, provenance hashes, and information boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "evaluation/baseline-inputs/v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def verify(bundle: Path = DEFAULT_BUNDLE) -> dict:
    manifest = read_json(bundle / "manifest.json")
    assert manifest["schema"] == "wake.baseline_input_manifest.v1"

    prompt_path = ROOT / manifest["prompt"]["path"]
    assert sha256(prompt_path) == manifest["prompt"]["sha256"]

    verified_cases = []
    for case_id, entry in sorted(manifest["summaries"].items()):
        summary_path = bundle / entry["path"]
        assert summary_path.is_file(), f"Missing summary: {entry['path']}"
        assert sha256(summary_path) == entry["sha256"]
        assert summary_path.stat().st_size == entry["bytes"]

        summary = read_json(summary_path)
        assert summary["schema_version"] == "wake.case_summary.v1"
        assert summary["case_id"] == case_id
        serialized = summary_path.read_text(encoding="utf-8").lower()
        assert "ground-truth" not in serialized
        assert "ground_truth" not in serialized

        input_dir = ROOT / "data/fixtures" / case_id / "input"
        for relative_path, expected_hash in summary["input_hashes"].items():
            input_path = input_dir / relative_path
            assert input_path.is_file(), f"Missing input: {case_id}/{relative_path}"
            assert sha256(input_path) == expected_hash

        verified_cases.append(case_id)

    real_case_path = bundle / manifest["summaries"][
        "case-001-misaligned-double-scull"
    ]["path"]
    real_case_text = real_case_path.read_text(encoding="utf-8").lower()
    assert "double_scull" not in real_case_text
    assert "world_rowing_code" not in real_case_text

    synthetic = read_json(
        bundle / manifest["summaries"][
            "case-002-wind-shift-plan-deviation"
        ]["path"]
    )
    mobile = next(
        source for source in synthetic["sources"]
        if source["source_id"] == "mobile-synthetic"
    )
    assert mobile["metrics"]["positive_spm_rows"] == 0
    wind = synthetic["environment"]["time_series_windows"]
    assert wind[0]["effective_headwind_m_s"] < 0
    assert wind[-1]["effective_headwind_m_s"] > 0

    return {
        "status": "verified",
        "bundle": str(bundle.relative_to(ROOT)),
        "cases": verified_cases,
        "ground_truth_leakage": False,
        "prompt_sha256": manifest["prompt"]["sha256"],
    }


def main() -> None:
    print(json.dumps(verify(), indent=2))


if __name__ == "__main__":
    main()
