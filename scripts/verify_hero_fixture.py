#!/usr/bin/env python3
"""Verify integrity, privacy invariants, and ground truth for WAKE's hero fixture."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data/fixtures/case-001-misaligned-double-scull"
EARTH_RADIUS_M = 6_371_008.8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * fraction
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(value))


def nearest_stats(
    reference: list[tuple[float, float]], candidate: list[tuple[float, float]]
) -> dict[str, float]:
    distances = [min(haversine(point, other) for other in candidate) for point in reference]
    return {
        "median_m": round(statistics.median(distances), 3),
        "p95_m": round(percentile(distances, 0.95), 3),
        "max_m": round(max(distances), 3),
    }


def speedcoach_summary(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    start = None
    summary = None
    route: list[tuple[float, float]] = []
    in_per_stroke = False
    for row in rows:
        if row and row[0] == "Start Time:":
            start = datetime.strptime(row[1], "%m/%d/%Y %H:%M:%S")
        if row == ["Per-Stroke Data:"]:
            in_per_stroke = True
            continue
        if summary is None and len(row) == 24 and row[0] == "1":
            summary = {
                "distance_m": float(row[1]),
                "elapsed": row[3],
                "avg_spm": float(row[8]),
                "strokes": int(row[9]),
            }
        if in_per_stroke and len(row) == 24 and row[0] == "1":
            route.append((float(row[-2]), float(row[-1])))
    assert start is not None and summary is not None
    return {"start": start, "summary": summary, "route": route, "rows": len(rows)}


def sensor_summary(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    route = [(float(row["latitude"]), float(row["longitude"])) for row in rows]
    timestamps = [int(row["timestamp"]) for row in rows]
    spm_values = [row["spm"] for row in rows if row["spm"]]
    gyro_nonzero = sum(
        any(abs(float(row[key])) > 0 for key in ("gyroX", "gyroY", "gyroZ"))
        for row in rows
    )
    return {
        "rows": len(rows),
        "route": route,
        "start": datetime.fromtimestamp(min(timestamps) / 1000, tz=timezone.utc).astimezone(
            timezone(timedelta(hours=-3))
        ),
        "duration_s": (max(timestamps) - min(timestamps)) / 1000,
        "max_distance_m": max(float(row["distance"]) for row in rows),
        "spm_values": len(spm_values),
        "gyro_nonzero_rows": gyro_nonzero,
    }


def workout_summary(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        rows = csv.reader(handle)
        for row in rows:
            if row == ["Device Info"]:
                break
            if len(row) == 2 and row[0] not in {"key", "Session Summary"}:
                values[row[0]] = row[1]
    return values


def verify_integrity() -> None:
    manifest = json.loads((FIXTURE / "source-manifest.json").read_text())
    for relative_path, expected in manifest["files"].items():
        path = FIXTURE / relative_path
        assert path.is_file(), f"Missing fixture source: {relative_path}"
        assert sha256(path) == expected["sha256"], f"Hash mismatch: {relative_path}"


def verify_privacy() -> None:
    for path in FIXTURE.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        assert "/Users/" not in text, f"Private absolute path found in {path}"

    sources = FIXTURE / "input/sources"
    for filename in ("mobile-ios-sensor.csv", "mobile-android-sensor.csv"):
        with (sources / filename).open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                assert 9.9 < float(row["latitude"]) < 10.1
                assert 9.9 < float(row["longitude"]) < 10.1

    for filename, expected_id, expected_model in (
        ("mobile-ios-metadata.json", "fixture-session-ios", "fixture-mobile-ios"),
        ("mobile-android-metadata.json", "fixture-session-android", "fixture-mobile-android"),
    ):
        metadata = json.loads((sources / filename).read_text())
        assert metadata["workoutId"] == expected_id
        assert metadata["deviceModel"] == expected_model
        assert metadata["startTime"].startswith("2026-01-15T")

    for filename, expected_id, expected_model in (
        ("mobile-ios-workout.csv", "fixture-session-ios", "fixture-mobile-ios"),
        ("mobile-android-workout.csv", "fixture-session-android", "fixture-mobile-android"),
    ):
        workout_text = (sources / filename).read_text()
        assert f"session_id,{expected_id}" in workout_text
        assert f"device_model,{expected_model}" in workout_text
        assert "2026-01-15T" in workout_text

    speedcoach_text = (sources / "speedcoach.csv").read_text()
    assert "SpeedCoach fixture-device" in speedcoach_text
    assert "01/15/2026 06:59:50" in speedcoach_text


def verify_case() -> dict:
    sources = FIXTURE / "input/sources"
    speedcoach = speedcoach_summary(sources / "speedcoach.csv")
    ios = sensor_summary(sources / "mobile-ios-sensor.csv")
    android = sensor_summary(sources / "mobile-android-sensor.csv")
    ios_workout = workout_summary(sources / "mobile-ios-workout.csv")
    android_workout = workout_summary(sources / "mobile-android-workout.csv")
    ios_metadata = json.loads((sources / "mobile-ios-metadata.json").read_text())
    android_metadata = json.loads((sources / "mobile-android-metadata.json").read_text())
    truth = json.loads((FIXTURE / "ground-truth.json").read_text())
    context = json.loads((FIXTURE / "input/context.json").read_text())

    assert truth["confirmed_context"]["boat_class"] == "DOUBLE_SCULL"
    assert truth["confirmed_context"]["world_rowing_code"] == "2x"
    assert truth["confirmed_context"]["crew_category"] == "MEN"
    assert truth["confirmed_context"]["athlete_count"] == 2
    assert truth["same_physical_session"] is True
    assert context["planned_workout"] is None

    assert speedcoach["summary"] == {
        "distance_m": 3915.3,
        "elapsed": "00:25:25.8",
        "avg_spm": 22.0,
        "strokes": 549,
    }
    assert len(speedcoach["route"]) == 549
    assert ios["rows"] == 923
    assert android["rows"] == 776
    assert abs(ios["max_distance_m"] - 3955.583797779428) < 1e-9
    assert abs(android["max_distance_m"] - 3973.992555239362) < 1e-9
    assert abs(ios["duration_s"] - 1543.24) < 0.001
    assert abs(android["duration_s"] - 1567.027) < 0.001
    assert ios["spm_values"] == 0 and android["spm_values"] == 0
    assert ios["gyro_nonzero_rows"] > 0 and android["gyro_nonzero_rows"] == 0
    assert ios_workout["total_distance_m"] == "4625"
    assert ios_workout["elapsed_seconds"] == "1564"
    assert ios_workout["avg_spm"] == "22"
    assert ios_workout["total_strokes"] == "562"
    assert android_workout["total_distance_m"] == "4456"
    assert android_workout["elapsed_seconds"] == "1618"
    assert android_workout["avg_spm"] == "24"
    assert android_workout["total_strokes"] == "556"
    assert ios_metadata["boatType"] == "SINGLE_SCULL"
    assert android_metadata["boatType"] == "OC1"

    speedcoach_local = speedcoach["start"].replace(
        tzinfo=timezone(timedelta(hours=-3))
    )
    ios_offset = (ios["start"] - speedcoach_local).total_seconds()
    android_offset = (android["start"] - speedcoach_local).total_seconds()
    assert abs(ios_offset - 3589.127) < 0.001
    assert abs(android_offset - 3564.821) < 0.001

    overlaps = {
        "speedcoach_to_ios": nearest_stats(speedcoach["route"], ios["route"]),
        "ios_to_speedcoach": nearest_stats(ios["route"], speedcoach["route"]),
        "speedcoach_to_android": nearest_stats(speedcoach["route"], android["route"]),
        "android_to_speedcoach": nearest_stats(android["route"], speedcoach["route"]),
    }
    assert all(result["p95_m"] < 5 for result in overlaps.values())

    return {
        "fixture": FIXTURE.name,
        "status": "verified",
        "speedcoach": speedcoach["summary"],
        "mobile_raw": {
            "ios": {key: value for key, value in ios.items() if key != "route" and key != "start"},
            "android": {key: value for key, value in android.items() if key != "route" and key != "start"},
        },
        "mobile_summary_distance_m": {
            "ios": float(ios_workout["total_distance_m"]),
            "android": float(android_workout["total_distance_m"]),
        },
        "clock_offsets_from_speedcoach_s": {
            "ios": round(ios_offset, 3),
            "android": round(android_offset, 3),
        },
        "route_overlap": overlaps,
    }


def main() -> None:
    verify_integrity()
    verify_privacy()
    print(json.dumps(verify_case(), indent=2))


if __name__ == "__main__":
    main()
