#!/usr/bin/env python3
"""Verify WAKE case 002 integrity, deterministic facts, and evaluation contract."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASE_ID = "case-002-wind-shift-plan-deviation"
FIXTURE = ROOT / "data/fixtures" / CASE_ID


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def declared_schema_versions(schema: dict) -> set[str]:
    """Return explicit schema_version constants from root or local oneOf refs."""
    candidates = [schema]
    for option in schema.get("oneOf", []):
        reference = option.get("$ref") if isinstance(option, dict) else None
        if isinstance(reference, str) and reference.startswith("#/$defs/"):
            candidates.append(schema["$defs"][reference.removeprefix("#/$defs/")])
        elif isinstance(option, dict):
            candidates.append(option)
    return {
        version
        for candidate in candidates
        if isinstance(candidate, dict)
        for version in [
            candidate.get("properties", {})
            .get("schema_version", {})
            .get("const")
        ]
        if isinstance(version, str)
    }


def verify_hashes() -> None:
    manifest = read_json(FIXTURE / "fixture-manifest.json")
    assert manifest["fixture_id"] == CASE_ID
    assert manifest["seed"] == 20260829
    for relative_path, expected in manifest["files"].items():
        path = FIXTURE / relative_path
        assert path.is_file(), f"Missing generated file: {relative_path}"
        assert sha256(path) == expected["sha256"], f"Hash mismatch: {relative_path}"
        assert path.stat().st_size == expected["bytes"], f"Size mismatch: {relative_path}"


def verify_contract_files() -> None:
    schemas = {
        "training-plan.schema.json": {"wake.training_plan.v1"},
        "recorded-session.schema.json": {"wake.recorded_session.v1"},
        "environment-timeline.schema.json": {
            "wake.environment_timeline.v1",
            "wake.environment_timeline.v2",
        },
        "evidence-claim.schema.json": {"wake.evidence_claim.v1"},
        "ground-truth.schema.json": {"wake.evaluation_ground_truth.v1"},
    }
    for filename, versions in schemas.items():
        schema = read_json(ROOT / "schemas" / filename)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert declared_schema_versions(schema) == versions

    registry = read_json(ROOT / "evaluation/cases.json")
    registered = {case["case_id"]: case for case in registry["cases"]}
    assert registered[CASE_ID]["status"] == "IMPLEMENTED"
    assert len(registry["cases"]) == 16


def rows_for_segment(rows: list[dict[str, str]], start_s: float, end_s: float) -> list[dict[str, str]]:
    return [row for row in rows if start_s < float(row["elapsed_s"]) <= end_s]


def distance_at(rows: list[dict[str, str]], elapsed_s: float) -> float:
    row = min(rows, key=lambda item: abs(float(item["elapsed_s"]) - elapsed_s))
    return float(row["distance_m"])


def verify_case() -> dict:
    input_dir = FIXTURE / "input"
    plan = read_json(input_dir / "plan.json")
    context = read_json(input_dir / "context.json")
    environment = read_json(input_dir / "environment.json")
    truth = read_json(FIXTURE / "ground-truth.json")
    speedcoach = read_csv(input_dir / "speedcoach.csv")
    mobile = read_csv(input_dir / "mobile.csv")

    assert plan["schema_version"] == "wake.training_plan.v1"
    assert [block["repetitions"] for block in plan["blocks"]] == [3, 3]
    assert [block["distance_m"] for block in plan["blocks"]] == [1000, 1000]
    assert plan["blocks"][0]["stroke_rate"] == {"min_spm": 19, "max_spm": 21}
    assert plan["blocks"][1]["stroke_rate"] == {"min_spm": 22, "max_spm": 24}
    assert all(block["zone_system"] == "STANDARD_ROWING_ZONES" for block in plan["blocks"])
    assert plan["blocks"][0]["equipment"] == ["RESISTANCE_BAND"]
    assert context["session_candidate"]["boat_class"] == "DOUBLE_SCULL"
    assert context["human_confirmations"]["resistance_band_used"] is None

    assert truth["schema_version"] == "wake.evaluation_ground_truth.v1"
    expected_segments = truth["expected_segments"]
    work_segments = [segment for segment in expected_segments if segment["kind"] == "WORK"]
    recovery_segments = [segment for segment in expected_segments if segment["kind"] == "RECOVERY"]
    assert len(work_segments) == 6 and len(recovery_segments) == 5
    assert [segment["compliance"] for segment in work_segments] == [
        "COMPLIANT", "COMPLIANT", "COMPLIANT", "COMPLIANT", "DEVIATION", "COMPLIANT"
    ]

    for expected in expected_segments:
        rows = rows_for_segment(
            speedcoach, expected["start_offset_s"], expected["end_offset_s"]
        )
        assert rows, f"No rows found for {expected['segment_id']}"
        start_distance = distance_at(speedcoach, expected["start_offset_s"])
        end_distance = distance_at(speedcoach, expected["end_offset_s"])
        measured_distance = end_distance - start_distance
        measured_speed = sum(float(row["speed_m_s"]) for row in rows) / len(rows)
        measured_spm = sum(float(row["stroke_rate_spm"]) for row in rows) / len(rows)
        assert abs(measured_distance - expected["distance_m"]) <= 0.01
        assert abs(measured_speed - expected["average_speed_m_s"]) <= 0.002
        assert abs(measured_spm - expected["average_spm"]) <= 0.02

    assert all(float(row["stroke_rate_spm"]) == 0 for row in mobile)
    speedcoach_start = datetime.fromisoformat(speedcoach[0]["timestamp"])
    mobile_start = datetime.fromisoformat(mobile[0]["timestamp"])
    clock_offset_s = (mobile_start - speedcoach_start).total_seconds()
    assert abs(clock_offset_s - 37.0) < 0.001
    distance_ratio = float(mobile[-1]["distance_m"]) / float(speedcoach[-1]["distance_m"])
    assert abs(distance_ratio - 1.012) < 0.0001

    samples = environment["samples"]
    assert environment["direction_convention"] == "METEOROLOGICAL_FROM_DEGREES_TRUE_NORTH"
    assert samples[0]["wind_direction_deg"] == 180.0
    assert samples[0]["wind_speed_m_s"] == 1.0
    assert samples[-1]["wind_direction_deg"] == 0.0
    assert samples[-1]["wind_speed_m_s"] == 5.5
    wind_claim = next(
        claim for claim in truth["expected_claims"] if claim["claim_id"] == "wind-shift-during-fourth"
    )
    shift_s = float(wind_claim["expectation"].split("around ")[1].split(" seconds")[0])
    fourth = work_segments[3]
    assert fourth["start_offset_s"] < shift_s < fourth["end_offset_s"]
    fourth_before = rows_for_segment(
        speedcoach, fourth["start_offset_s"], shift_s - 90
    )
    fourth_after = rows_for_segment(
        speedcoach, shift_s + 90, fourth["end_offset_s"]
    )
    before_speed = sum(float(row["speed_m_s"]) for row in fourth_before) / len(fourth_before)
    after_speed = sum(float(row["speed_m_s"]) for row in fourth_after) / len(fourth_after)
    assert before_speed - after_speed > 0.4

    for path in FIXTURE.rglob("*"):
        if path.is_file():
            assert "/Users/" not in path.read_text(encoding="utf-8")
    for row in speedcoach + mobile:
        assert 9.9 < float(row["latitude"]) < 10.1
        assert 9.9 < float(row["longitude"]) < 10.1

    return {
        "fixture": CASE_ID,
        "status": "verified",
        "work_intervals": len(work_segments),
        "recovery_intervals": len(recovery_segments),
        "deviation_segments": [
            segment["segment_id"]
            for segment in work_segments
            if segment["compliance"] == "DEVIATION"
        ],
        "work_average_speed_m_s": {
            segment["segment_id"]: segment["average_speed_m_s"]
            for segment in work_segments
        },
        "mobile_clock_offset_s": clock_offset_s,
        "mobile_distance_bias_percent": round((distance_ratio - 1) * 100, 3),
        "mobile_positive_spm_rows": 0,
        "wind_before": {
            "speed_m_s": samples[0]["wind_speed_m_s"],
            "direction_from_deg": samples[0]["wind_direction_deg"]
        },
        "wind_after": {
            "speed_m_s": samples[-1]["wind_speed_m_s"],
            "direction_from_deg": samples[-1]["wind_direction_deg"]
        },
        "wind_shift_inside_segment": fourth["segment_id"],
        "fourth_interval_speed_change_m_s": {
            "before_transition": round(before_speed, 3),
            "after_transition": round(after_speed, 3)
        }
    }


def main() -> None:
    verify_hashes()
    verify_contract_files()
    print(json.dumps(verify_case(), indent=2))


if __name__ == "__main__":
    main()
