#!/usr/bin/env python3
"""Verify integrity and the frozen semantics of synthetic cases 003-010."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import jsonschema

from generate_diagnostic_cases import GENERATOR_VERSION, SCENARIOS


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE_ROOT = ROOT / "data/fixtures"
TEXT_SUFFIXES = {".csv", ".json", ".md", ".txt"}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest(case_dir: Path, case_id: str, scenario: dict) -> None:
    manifest = read_json(case_dir / "fixture-manifest.json")
    assert manifest["schema"] == "wake.synthetic_fixture_manifest.v1"
    assert manifest["fixture_id"] == case_id
    assert manifest["generator"] == "scripts/generate_diagnostic_cases.py"
    assert manifest["generator_version"] == GENERATOR_VERSION
    assert manifest["seed"] == scenario["seed"]

    declared = set(manifest["files"])
    actual = {
        str(path.relative_to(case_dir))
        for path in case_dir.rglob("*")
        if path.is_file() and path.name != "fixture-manifest.json"
    }
    assert declared == actual, f"Manifest file set mismatch: {case_id}"
    for relative, expected in manifest["files"].items():
        path = case_dir / relative
        assert sha256(path) == expected["sha256"], f"Hash mismatch: {case_id}/{relative}"
        assert path.stat().st_size == expected["bytes"], f"Size mismatch: {case_id}/{relative}"


def verify_privacy(case_dir: Path) -> None:
    for path in case_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8").lower()
            assert "/users/" not in text, f"Private path found: {path}"
            if "input" in path.parts:
                assert "ground-truth" not in text, f"Ground truth leaked into input: {path}"


def verify_case(case_dir: Path, case_id: str, scenario: dict, schemas: dict) -> dict:
    verify_manifest(case_dir, case_id, scenario)
    verify_privacy(case_dir)

    input_dir = case_dir / "input"
    plan = read_json(input_dir / "plan.json")
    context = read_json(input_dir / "context.json")
    truth = read_json(case_dir / "ground-truth.json")
    speedcoach = read_csv(input_dir / "speedcoach.csv")
    jsonschema.validate(plan, schemas["plan"])
    jsonschema.validate(truth, schemas["truth"])

    assert context["case_id"] == case_id
    assert context["input_notice"].endswith("synthetic.")
    assert plan["blocks"][0]["repetitions"] == 4
    assert plan["blocks"][0]["distance_m"] == 500.0
    assert plan["blocks"][0]["stroke_rate"] == {"min_spm": 20, "max_spm": 22}
    assert truth["fixture_id"] == case_id

    assert speedcoach, f"Empty SpeedCoach file: {case_id}"
    elapsed = [float(row["elapsed_s"]) for row in speedcoach]
    distance = [float(row["distance_m"]) for row in speedcoach]
    assert elapsed == sorted(elapsed), f"Non-monotonic time: {case_id}"
    assert distance == sorted(distance), f"Non-monotonic distance: {case_id}"
    for row in speedcoach:
        assert 10.9 < float(row["latitude"]) < 11.1
        assert 10.9 < float(row["longitude"]) < 11.1

    expected_deviations = set(scenario["expected_deviations"])
    actual_deviations = {
        segment["segment_id"]
        for segment in truth["expected_segments"]
        if segment["compliance"] == "DEVIATION"
    }
    assert actual_deviations == expected_deviations, f"Deviation mismatch: {case_id}"
    observed_work = [
        segment
        for segment in truth["expected_segments"]
        if segment["kind"] == "WORK" and segment["distance_m"] is not None
    ]
    assert len(observed_work) == len(scenario["work_spm"])

    environment_path = input_dir / "environment.json"
    assert environment_path.exists() is (scenario["environment"] is not None)
    if environment_path.exists():
        environment = read_json(environment_path)
        jsonschema.validate(environment, schemas["environment"])
        first = environment["samples"][0]
        expected = scenario["environment"]
        assert first["wind_speed_m_s"] == expected["wind_m_s"]
        assert first["wind_direction_deg"] == expected["direction_deg"]
        assert first["gust_speed_m_s"] == expected["gust_m_s"]

    mobile_path = input_dir / "mobile.csv"
    assert mobile_path.exists() is bool(scenario.get("mobile_spm_zero"))
    if mobile_path.exists():
        mobile = read_csv(mobile_path)
        assert mobile
        assert all(float(row["stroke_rate_spm"]) == 0 for row in mobile)

    return {
        "deviation_segments": sorted(actual_deviations),
        "environment_present": environment_path.exists(),
        "mobile_present": mobile_path.exists(),
        "observed_work_intervals": len(observed_work),
    }


def verify_fixture_set(fixture_root: Path = DEFAULT_FIXTURE_ROOT) -> dict:
    schemas = {
        "plan": read_json(ROOT / "schemas/training-plan.schema.json"),
        "environment": read_json(ROOT / "schemas/environment-timeline.schema.json"),
        "truth": read_json(ROOT / "schemas/ground-truth.schema.json"),
    }
    registry = read_json(ROOT / "evaluation/cases.json")
    registered = {item["case_id"]: item for item in registry["cases"]}
    fixtures = {}
    for case_id, scenario in SCENARIOS.items():
        assert registered[case_id]["status"] in {"PLANNED", "IMPLEMENTED"}
        fixtures[case_id] = verify_case(
            fixture_root / case_id, case_id, scenario, schemas
        )
    return {
        "status": "verified",
        "fixture_count": len(fixtures),
        "fixtures": fixtures,
    }


def main() -> None:
    print(json.dumps(verify_fixture_set(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
