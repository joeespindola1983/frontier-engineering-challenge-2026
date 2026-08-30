#!/usr/bin/env python3
"""Build compact, deterministic, ground-truth-free inputs for baseline evaluation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from verify_hero_fixture import nearest_stats, sensor_summary, speedcoach_summary, workout_summary


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_VERSION = "1.1"
SUMMARY_VERSION = "wake.case_summary.v1"
DOMAIN_KNOWLEDGE = [
    {
        "term": "voga",
        "meaning": "Target stroke rate in strokes per minute (SPM).",
        "status": "HUMAN_CONFIRMED",
        "limitations": []
    },
    {
        "term": "B0-B7 and E1-E7",
        "meaning": "Standardized rowing training-zone codes.",
        "status": "HUMAN_CONFIRMED",
        "limitations": [
            "Exact effort, physiological, heart-rate, lactate, and power boundaries are not supplied."
        ]
    }
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def input_hashes(input_dir: Path) -> dict[str, str]:
    return {
        str(path.relative_to(input_dir)): sha256(path)
        for path in sorted(input_dir.rglob("*"))
        if path.is_file()
    }


def parse_elapsed(value: str) -> float:
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def aggregate_windows(
    rows: list[dict], window_s: int, elapsed_key: str = "elapsed_s"
) -> list[dict]:
    buckets: dict[int, list[dict]] = defaultdict(list)
    for row in rows:
        bucket = int(float(row[elapsed_key]) // window_s)
        buckets[bucket].append(row)

    windows = []
    for bucket, items in sorted(buckets.items()):
        distances = [float(item["distance_m"]) for item in items]
        speeds = [float(item["speed_m_s"]) for item in items]
        spm_values = [
            float(item["stroke_rate_spm"])
            for item in items
            if item.get("stroke_rate_spm") not in {None, "", "0", "0.00"}
        ]
        windows.append(
            {
                "start_offset_s": bucket * window_s,
                "end_offset_s": (bucket + 1) * window_s,
                "distance_start_m": round(min(distances), 1),
                "distance_end_m": round(max(distances), 1),
                "average_speed_m_s": round(statistics.mean(speeds), 3),
                "average_spm": round(statistics.mean(spm_values), 2) if spm_values else None,
                "samples": len(items)
            }
        )
    return windows


def speedcoach_vendor_windows(path: Path, window_s: int = 60) -> list[dict]:
    parsed: list[dict] = []
    in_per_stroke = False
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.reader(handle):
            if row == ["Per-Stroke Data:"]:
                in_per_stroke = True
                continue
            if in_per_stroke and len(row) == 24 and row[0] == "1":
                parsed.append(
                    {
                        "elapsed_s": parse_elapsed(row[3]),
                        "distance_m": float(row[1]),
                        "speed_m_s": float(row[5]),
                        "stroke_rate_spm": float(row[8])
                    }
                )
    return aggregate_windows(parsed, window_s)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def public_sensor_values(summary: dict) -> dict:
    return {
        "rows": summary["rows"],
        "start_time": summary["start"].isoformat(timespec="milliseconds"),
        "duration_s": summary["duration_s"],
        "max_raw_distance_m": summary["max_distance_m"],
        "positive_spm_rows": summary["spm_values"],
        "nonzero_gyroscope_rows": summary["gyro_nonzero_rows"]
    }


def case_001_summary() -> dict:
    case_dir = ROOT / "data/fixtures/case-001-misaligned-double-scull"
    input_dir = case_dir / "input"
    sources = input_dir / "sources"
    context = read_json(input_dir / "context.json")
    speedcoach_path = sources / "speedcoach.csv"
    ios_sensor_path = sources / "mobile-ios-sensor.csv"
    android_sensor_path = sources / "mobile-android-sensor.csv"
    speedcoach = speedcoach_summary(speedcoach_path)
    ios = sensor_summary(ios_sensor_path)
    android = sensor_summary(android_sensor_path)
    ios_workout = workout_summary(sources / "mobile-ios-workout.csv")
    android_workout = workout_summary(sources / "mobile-android-workout.csv")
    ios_metadata = read_json(sources / "mobile-ios-metadata.json")
    android_metadata = read_json(sources / "mobile-android-metadata.json")
    local_zone = timezone(timedelta(hours=-3))
    speedcoach_start = speedcoach["start"].replace(tzinfo=local_zone)
    ios_offset = (ios["start"] - speedcoach_start).total_seconds()
    android_offset = (android["start"] - speedcoach_start).total_seconds()

    return {
        "schema_version": SUMMARY_VERSION,
        "summary_id": "baseline-input-v1-case-001",
        "case_id": "case-001-misaligned-double-scull",
        "generated_by": "scripts/build_baseline_inputs.py@1.0",
        "input_hashes": input_hashes(input_dir),
        "investigation_request": context["investigation_request"],
        "domain_knowledge": DOMAIN_KNOWLEDGE,
        "known_context": {
            "planned_workout": context["planned_workout"],
            "crew_context": context["crew_context"],
            "coach_observation": context["coach_observation"],
            "environment_observation": context["environment_observation"],
            "goal_context": context["goal_context"]
        },
        "plan": None,
        "sources": [
            {
                "source_id": "speedcoach",
                "kind": "SPEEDCOACH",
                "evidence_refs": ["input/sources/speedcoach.csv"],
                "metrics": {
                    "start_time": speedcoach_start.isoformat(),
                    **speedcoach["summary"],
                    "route_points": len(speedcoach["route"])
                },
                "quality_flags": ["GPS_PRESENT", "SPM_PRESENT", "HEART_RATE_ABSENT"],
                "time_series_windows": speedcoach_vendor_windows(speedcoach_path)
            },
            {
                "source_id": "mobile-ios",
                "kind": "MOBILE_IOS",
                "evidence_refs": [
                    "input/sources/mobile-ios-sensor.csv",
                    "input/sources/mobile-ios-workout.csv",
                    "input/sources/mobile-ios-metadata.json"
                ],
                "metrics": {
                    "raw": public_sensor_values(ios),
                    "reported_summary": {
                        "elapsed_s": float(ios_workout["elapsed_seconds"]),
                        "distance_m": float(ios_workout["total_distance_m"]),
                        "average_spm": float(ios_workout["avg_spm"]),
                        "total_strokes": int(ios_workout["total_strokes"])
                    },
                    "reported_boat_type": ios_metadata["boatType"],
                    "reported_has_watch_data": ios_metadata["hasWatchData"]
                },
                "quality_flags": [
                    "GPS_PRESENT",
                    "RAW_SPM_ABSENT",
                    "GYROSCOPE_PRESENT",
                    "RAW_AND_SUMMARY_DISTANCE_CONFLICT",
                    "WATCH_FILE_NOT_SUPPLIED"
                ],
                "time_series_windows": []
            },
            {
                "source_id": "mobile-android",
                "kind": "MOBILE_ANDROID",
                "evidence_refs": [
                    "input/sources/mobile-android-sensor.csv",
                    "input/sources/mobile-android-workout.csv",
                    "input/sources/mobile-android-metadata.json"
                ],
                "metrics": {
                    "raw": public_sensor_values(android),
                    "reported_summary": {
                        "elapsed_s": float(android_workout["elapsed_seconds"]),
                        "distance_m": float(android_workout["total_distance_m"]),
                        "average_spm": float(android_workout["avg_spm"]),
                        "total_strokes": int(android_workout["total_strokes"])
                    },
                    "reported_boat_type": android_metadata["boatType"],
                    "reported_has_watch_data": android_metadata["hasWatchData"]
                },
                "quality_flags": [
                    "GPS_PRESENT",
                    "RAW_SPM_ABSENT",
                    "GYROSCOPE_ALL_ZERO",
                    "RAW_AND_SUMMARY_DISTANCE_CONFLICT",
                    "WATCH_FILE_NOT_SUPPLIED"
                ],
                "time_series_windows": []
            }
        ],
        "cross_source_findings": [
            {
                "finding_id": "clock-offsets",
                "type": "CLOCK_OFFSET",
                "summary": "Mobile clocks start almost one hour after the SpeedCoach clock; the cause is not supplied.",
                "values": {
                    "ios_from_speedcoach_s": round(ios_offset, 3),
                    "android_from_speedcoach_s": round(android_offset, 3)
                },
                "evidence_refs": [
                    "input/sources/speedcoach.csv",
                    "input/sources/mobile-ios-sensor.csv",
                    "input/sources/mobile-android-sensor.csv"
                ]
            },
            {
                "finding_id": "route-overlap-speedcoach-ios",
                "type": "ROUTE_OVERLAP",
                "summary": "Nearest-route distances are small in both directions.",
                "values": {
                    "speedcoach_to_ios": nearest_stats(speedcoach["route"], ios["route"]),
                    "ios_to_speedcoach": nearest_stats(ios["route"], speedcoach["route"])
                },
                "evidence_refs": [
                    "input/sources/speedcoach.csv",
                    "input/sources/mobile-ios-sensor.csv"
                ]
            },
            {
                "finding_id": "route-overlap-speedcoach-android",
                "type": "ROUTE_OVERLAP",
                "summary": "Nearest-route distances are small in both directions.",
                "values": {
                    "speedcoach_to_android": nearest_stats(speedcoach["route"], android["route"]),
                    "android_to_speedcoach": nearest_stats(android["route"], speedcoach["route"])
                },
                "evidence_refs": [
                    "input/sources/speedcoach.csv",
                    "input/sources/mobile-android-sensor.csv"
                ]
            }
        ],
        "environment": None,
        "evidence_gaps": [
            "No planned workout is supplied.",
            "Boat class, crew, and seats are not confirmed in the input.",
            "No usable heart-rate or watch evidence is supplied.",
            "No coach technique observation is supplied.",
            "No environmental evidence is supplied."
        ]
    }


def case_002_summary() -> dict:
    case_dir = ROOT / "data/fixtures/case-002-wind-shift-plan-deviation"
    input_dir = case_dir / "input"
    context = read_json(input_dir / "context.json")
    plan = read_json(input_dir / "plan.json")
    environment = read_json(input_dir / "environment.json")
    speedcoach = csv_rows(input_dir / "speedcoach.csv")
    mobile = csv_rows(input_dir / "mobile.csv")
    speedcoach_start = datetime.fromisoformat(speedcoach[0]["timestamp"])
    mobile_start = datetime.fromisoformat(mobile[0]["timestamp"])
    distance_ratio = float(mobile[-1]["distance_m"]) / float(speedcoach[-1]["distance_m"])
    route_speedcoach = [(float(row["latitude"]), float(row["longitude"])) for row in speedcoach]
    route_mobile = [(float(row["latitude"]), float(row["longitude"])) for row in mobile]
    heading = float(context["session_candidate"]["route_heading_deg"])
    environment_start = datetime.fromisoformat(environment["samples"][0]["timestamp"])
    environment_windows = []
    for sample in environment["samples"]:
        timestamp = datetime.fromisoformat(sample["timestamp"])
        elapsed_s = (timestamp - environment_start).total_seconds()
        direction = float(sample["wind_direction_deg"])
        wind_speed = float(sample["wind_speed_m_s"])
        environment_windows.append(
            {
                "elapsed_s": elapsed_s,
                "wind_speed_m_s": wind_speed,
                "wind_direction_from_deg": direction,
                "gust_speed_m_s": sample["gust_speed_m_s"],
                "effective_headwind_m_s": round(
                    wind_speed * math.cos(math.radians(direction - heading)), 3
                )
            }
        )

    speedcoach_spm = [float(row["stroke_rate_spm"]) for row in speedcoach if float(row["stroke_rate_spm"]) > 0]
    mobile_spm = [float(row["stroke_rate_spm"]) for row in mobile if float(row["stroke_rate_spm"]) > 0]
    return {
        "schema_version": SUMMARY_VERSION,
        "summary_id": "baseline-input-v1-case-002",
        "case_id": "case-002-wind-shift-plan-deviation",
        "generated_by": "scripts/build_baseline_inputs.py@1.0",
        "input_hashes": input_hashes(input_dir),
        "investigation_request": context["investigation_request"],
        "domain_knowledge": DOMAIN_KNOWLEDGE,
        "known_context": {
            "session_candidate": context["session_candidate"],
            "human_confirmations": context["human_confirmations"],
            "input_notice": context["input_notice"]
        },
        "plan": plan,
        "sources": [
            {
                "source_id": "speedcoach-synthetic",
                "kind": "SPEEDCOACH",
                "evidence_refs": ["input/speedcoach.csv"],
                "metrics": {
                    "start_time": speedcoach[0]["timestamp"],
                    "duration_s": float(speedcoach[-1]["elapsed_s"]),
                    "end_distance_m": float(speedcoach[-1]["distance_m"]),
                    "average_positive_spm": round(statistics.mean(speedcoach_spm), 2),
                    "positive_spm_rows": len(speedcoach_spm),
                    "route_points": len(speedcoach)
                },
                "quality_flags": ["GPS_PRESENT", "SPM_PRESENT"],
                "time_series_windows": aggregate_windows(speedcoach, 30)
            },
            {
                "source_id": "mobile-synthetic",
                "kind": "MOBILE",
                "evidence_refs": ["input/mobile.csv"],
                "metrics": {
                    "start_time": mobile[0]["timestamp"],
                    "duration_s": float(mobile[-1]["elapsed_s"]),
                    "end_distance_m": float(mobile[-1]["distance_m"]),
                    "average_positive_spm": round(statistics.mean(mobile_spm), 2) if mobile_spm else None,
                    "positive_spm_rows": len(mobile_spm),
                    "route_points": len(mobile)
                },
                "quality_flags": ["GPS_PRESENT", "SPM_ALL_ZERO", "DISTANCE_BIAS_PRESENT"],
                "time_series_windows": []
            }
        ],
        "cross_source_findings": [
            {
                "finding_id": "mobile-clock-offset",
                "type": "CLOCK_OFFSET",
                "summary": "The mobile clock starts after the SpeedCoach clock.",
                "values": {
                    "mobile_from_speedcoach_s": (mobile_start - speedcoach_start).total_seconds()
                },
                "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"]
            },
            {
                "finding_id": "distance-bias",
                "type": "DISTANCE_CONFLICT",
                "summary": "The mobile cumulative distance ends above the SpeedCoach distance.",
                "values": {
                    "mobile_to_speedcoach_ratio": round(distance_ratio, 5),
                    "difference_percent": round((distance_ratio - 1) * 100, 3)
                },
                "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"]
            },
            {
                "finding_id": "route-overlap",
                "type": "ROUTE_OVERLAP",
                "summary": "The two synthetic routes overlap closely in both directions.",
                "values": {
                    "speedcoach_to_mobile": nearest_stats(route_speedcoach, route_mobile),
                    "mobile_to_speedcoach": nearest_stats(route_mobile, route_speedcoach)
                },
                "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"]
            }
        ],
        "environment": {
            "timeline_id": environment["timeline_id"],
            "source": environment["source"],
            "direction_convention": environment["direction_convention"],
            "route_heading_deg": heading,
            "method": "Effective headwind is positive when meteorological wind-from direction aligns with boat heading.",
            "time_series_windows": environment_windows
        },
        "evidence_gaps": [
            "Telemetry cannot confirm whether the prescribed resistance band was used.",
            "No coach technique or crew-synchronization observation is supplied.",
            "No perceived-effort report is supplied."
        ]
    }


def diagnostic_case_summary(case_id: str) -> dict:
    """Build one compact summary for a generated case 003-010."""
    case_dir = ROOT / "data/fixtures" / case_id
    input_dir = case_dir / "input"
    context = read_json(input_dir / "context.json")
    plan = read_json(input_dir / "plan.json")
    speedcoach = csv_rows(input_dir / "speedcoach.csv")
    provided = {
        item["kind"]: item for item in context["provided_sources"]
    }
    speedcoach_id = provided["SPEEDCOACH"]["source_id"]
    speedcoach_spm = [
        float(row["stroke_rate_spm"])
        for row in speedcoach
        if float(row["stroke_rate_spm"]) > 0
    ]
    route_speedcoach = [
        (float(row["latitude"]), float(row["longitude"])) for row in speedcoach
    ]
    sources = [
        {
            "source_id": speedcoach_id,
            "kind": "SPEEDCOACH",
            "evidence_refs": ["input/speedcoach.csv"],
            "metrics": {
                "start_time": speedcoach[0]["timestamp"],
                "duration_s": float(speedcoach[-1]["elapsed_s"]),
                "end_distance_m": float(speedcoach[-1]["distance_m"]),
                "average_positive_spm": round(statistics.mean(speedcoach_spm), 2),
                "positive_spm_rows": len(speedcoach_spm),
                "route_points": len(speedcoach),
            },
            "quality_flags": ["GPS_PRESENT", "SPM_PRESENT"],
            "time_series_windows": aggregate_windows(speedcoach, 30),
        }
    ]
    findings = []
    mobile_path = input_dir / "mobile.csv"
    if mobile_path.is_file():
        mobile = csv_rows(mobile_path)
        mobile_id = provided["MOBILE"]["source_id"]
        mobile_spm = [
            float(row["stroke_rate_spm"])
            for row in mobile
            if float(row["stroke_rate_spm"]) > 0
        ]
        route_mobile = [
            (float(row["latitude"]), float(row["longitude"])) for row in mobile
        ]
        speedcoach_start = datetime.fromisoformat(speedcoach[0]["timestamp"])
        mobile_start = datetime.fromisoformat(mobile[0]["timestamp"])
        distance_ratio = float(mobile[-1]["distance_m"]) / float(
            speedcoach[-1]["distance_m"]
        )
        sources.append(
            {
                "source_id": mobile_id,
                "kind": "MOBILE",
                "evidence_refs": ["input/mobile.csv"],
                "metrics": {
                    "start_time": mobile[0]["timestamp"],
                    "duration_s": float(mobile[-1]["elapsed_s"]),
                    "end_distance_m": float(mobile[-1]["distance_m"]),
                    "average_positive_spm": (
                        round(statistics.mean(mobile_spm), 2) if mobile_spm else None
                    ),
                    "positive_spm_rows": len(mobile_spm),
                    "route_points": len(mobile),
                },
                "quality_flags": [
                    "GPS_PRESENT",
                    "SPM_PRESENT" if mobile_spm else "SPM_ALL_ZERO",
                    "DISTANCE_BIAS_PRESENT",
                ],
                "time_series_windows": [],
            }
        )
        findings.extend(
            [
                {
                    "finding_id": "mobile-clock-offset",
                    "type": "CLOCK_OFFSET",
                    "summary": "The mobile clock starts after the SpeedCoach clock.",
                    "values": {
                        "mobile_from_speedcoach_s": (
                            mobile_start - speedcoach_start
                        ).total_seconds()
                    },
                    "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"],
                },
                {
                    "finding_id": "distance-bias",
                    "type": "DISTANCE_CONFLICT",
                    "summary": "Mobile cumulative distance ends above SpeedCoach distance.",
                    "values": {
                        "mobile_to_speedcoach_ratio": round(distance_ratio, 5),
                        "difference_percent": round((distance_ratio - 1) * 100, 3),
                    },
                    "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"],
                },
                {
                    "finding_id": "route-overlap",
                    "type": "ROUTE_OVERLAP",
                    "summary": "The two synthetic routes overlap closely.",
                    "values": {
                        "speedcoach_to_mobile": nearest_stats(
                            route_speedcoach, route_mobile
                        ),
                        "mobile_to_speedcoach": nearest_stats(
                            route_mobile, route_speedcoach
                        ),
                    },
                    "evidence_refs": ["input/speedcoach.csv", "input/mobile.csv"],
                },
            ]
        )

    environment_summary = None
    environment_path = input_dir / "environment.json"
    if environment_path.is_file():
        environment = read_json(environment_path)
        heading = float(context["session_candidate"]["route_heading_deg"])
        environment_start = datetime.fromisoformat(
            environment["samples"][0]["timestamp"]
        )
        windows = []
        for sample in environment["samples"]:
            timestamp = datetime.fromisoformat(sample["timestamp"])
            direction = float(sample["wind_direction_deg"])
            speed = float(sample["wind_speed_m_s"])
            relative = math.radians(direction - heading)
            windows.append(
                {
                    "elapsed_s": (timestamp - environment_start).total_seconds(),
                    "wind_speed_m_s": speed,
                    "wind_direction_from_deg": direction,
                    "gust_speed_m_s": sample["gust_speed_m_s"],
                    "effective_headwind_m_s": round(speed * math.cos(relative), 3),
                    "effective_crosswind_m_s": round(speed * math.sin(relative), 3),
                }
            )
        environment_summary = {
            "timeline_id": environment["timeline_id"],
            "source": environment["source"],
            "direction_convention": environment["direction_convention"],
            "route_heading_deg": heading,
            "method": (
                "Wind is projected against the confirmed synthetic route heading; "
                "the timeline supports association, not causation."
            ),
            "time_series_windows": windows,
        }

    evidence_gaps = [
        "No coach technique or crew-synchronization observation is supplied.",
        "No perceived-effort report is supplied.",
    ]
    if environment_summary is None:
        evidence_gaps.append("No environmental timeline is supplied.")
    if not mobile_path.is_file():
        evidence_gaps.append(
            "No independent mobile recording is supplied for route corroboration."
        )
    return {
        "schema_version": SUMMARY_VERSION,
        "summary_id": f"baseline-input-v2-{case_id}",
        "case_id": case_id,
        "generated_by": "scripts/build_baseline_inputs.py@1.1",
        "input_hashes": input_hashes(input_dir),
        "investigation_request": context["investigation_request"],
        "domain_knowledge": DOMAIN_KNOWLEDGE,
        "known_context": {
            "session_candidate": context["session_candidate"],
            "human_confirmations": context["human_confirmations"],
            "input_notice": context["input_notice"],
        },
        "plan": plan,
        "sources": sources,
        "cross_source_findings": findings,
        "environment": environment_summary,
        "evidence_gaps": evidence_gaps,
    }


def build(output_dir: Path) -> None:
    diagnostic_ids = [
        f"case-{index:03d}-{suffix}"
        for index, suffix in (
            (3, "calm-expert-compliant"),
            (4, "steady-headwind-compliant"),
            (5, "tailwind-fast-not-improvement"),
            (6, "crosswind-gusts"),
            (7, "incomplete-intervals"),
            (8, "correct-distance-wrong-spm"),
            (9, "excess-recovery"),
            (10, "mobile-spm-zero"),
        )
    ]
    summaries = [
        case_001_summary(),
        case_002_summary(),
        *(diagnostic_case_summary(case_id) for case_id in diagnostic_ids),
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_files = []
    for summary in summaries:
        path = output_dir / f"{summary['case_id']}.json"
        write_json(path, summary)
        summary_files.append(path)

    prompt_path = ROOT / "prompts/baseline-v1.md"
    manifest = {
        "schema": "wake.baseline_input_manifest.v1",
        "version": "2.0",
        "generator": "scripts/build_baseline_inputs.py",
        "generator_version": GENERATOR_VERSION,
        "summary_schema": "wake.case_summary.v1",
        "prompt": {
            "path": "prompts/baseline-v1.md",
            "sha256": sha256(prompt_path)
        },
        "summaries": {
            path.stem: {
                "path": str(path.relative_to(output_dir)),
                "sha256": sha256(path),
                "bytes": path.stat().st_size
            }
            for path in summary_files
        }
    }
    write_json(output_dir / "manifest.json", manifest)
    print(f"Built {len(summary_files)} compact baseline inputs in {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evaluation/baseline-inputs/v2"
    )
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
