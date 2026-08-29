#!/usr/bin/env python3
"""Generate deterministic public synthetic evaluation cases for WAKE."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


EARTH_RADIUS_M = 6_371_008.8
CASE_ID = "case-002-wind-shift-plan-deviation"
GENERATOR_VERSION = "1.0"
SEED = 20260829
START_TIME = datetime(2026, 1, 20, 6, 0, 0, tzinfo=timezone(timedelta(hours=-3)))
ORIGIN_LAT = 10.0
ORIGIN_LON = 10.0
MOBILE_CLOCK_OFFSET_S = 37.0


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iso_at(elapsed_s: float, offset_s: float = 0) -> str:
    value = START_TIME + timedelta(seconds=elapsed_s + offset_s)
    return value.isoformat(timespec="milliseconds")


def wind_at(elapsed_s: float, shift_center_s: float) -> dict[str, float]:
    transition_start = shift_center_s - 90
    transition_end = shift_center_s + 90
    if elapsed_s <= transition_start:
        fraction = 0.0
    elif elapsed_s >= transition_end:
        fraction = 1.0
    else:
        fraction = (elapsed_s - transition_start) / (transition_end - transition_start)
    speed = 1.0 + 4.5 * fraction
    direction = 180.0 * (1.0 - fraction)
    gust = speed + 0.3 + 1.2 * fraction
    effective_headwind = speed * math.cos(math.radians(direction))
    return {
        "wind_speed_m_s": speed,
        "wind_direction_deg": direction,
        "gust_speed_m_s": gust,
        "effective_headwind_m_s": effective_headwind,
    }


def coordinate_at(distance_m: float, elapsed_s: float) -> tuple[float, float]:
    north_m = distance_m
    east_m = 2.5 * math.sin(elapsed_s / 180.0)
    latitude = ORIGIN_LAT + math.degrees(north_m / EARTH_RADIUS_M)
    longitude = ORIGIN_LON + math.degrees(
        east_m / (EARTH_RADIUS_M * math.cos(math.radians(ORIGIN_LAT)))
    )
    return latitude, longitude


def generate_plan() -> dict:
    recovery = {"min_s": 180, "max_s": 300, "mode": "ACTIVE_LIGHT_ROWING"}
    return {
        "schema_version": "wake.training_plan.v1",
        "plan_id": "synthetic-plan-002",
        "scheduled_date": "2026-01-20",
        "timezone": "America/Sao_Paulo",
        "source": {
            "kind": "SYNTHETIC",
            "provenance": "DERIVED_SYNTHETIC",
            "source_ref": "anonymized pattern derived from an approved coach plan"
        },
        "modality": "WATER",
        "athlete_scope": {
            "kind": "CREW",
            "ids": ["synthetic-athlete-a", "synthetic-athlete-b"]
        },
        "goal_id": "synthetic-goal-regatta-01",
        "coach_language": "6 x 1 km; first 3 at 20 SPM with resistance band, last 3 at 23 SPM; 3-5 minutes active recovery.",
        "blocks": [
            {
                "block_id": "work-band",
                "kind": "WORK",
                "repetitions": 3,
                "distance_m": 1000,
                "duration_s": None,
                "stroke_rate": {"min_spm": 19, "max_spm": 21},
                "zone": "B2/B3",
                "zone_system": "STANDARD_ROWING_ZONES",
                "recovery": recovery,
                "equipment": ["RESISTANCE_BAND"],
                "instructions": ["Keep the work interval continuous."]
            },
            {
                "block_id": "work-free",
                "kind": "WORK",
                "repetitions": 3,
                "distance_m": 1000,
                "duration_s": None,
                "stroke_rate": {"min_spm": 22, "max_spm": 24},
                "zone": "B2/B3",
                "zone_system": "STANDARD_ROWING_ZONES",
                "recovery": recovery,
                "equipment": [],
                "instructions": ["Remove the resistance band before this block."]
            }
        ],
        "unresolved_terms": [],
        "notes": "Synthetic evaluation plan inspired by the structure of a real rowing prescription; it is not a record of an athlete's workout."
    }


def generate_context() -> dict:
    return {
        "schema_version": "wake.synthetic_case_context.v1",
        "case_id": CASE_ID,
        "investigation_request": "Compare the planned and performed session, explain supported speed changes, identify real deviations, and state what remains unknown.",
        "provided_sources": [
            {"source_id": "speedcoach-synthetic", "kind": "SPEEDCOACH", "path": "speedcoach.csv"},
            {"source_id": "mobile-synthetic", "kind": "MOBILE", "path": "mobile.csv"},
            {"source_id": "synthetic-environment-002", "kind": "ENVIRONMENT", "path": "environment.json"},
            {"source_id": "synthetic-plan-002", "kind": "TRAINING_PLAN", "path": "plan.json"}
        ],
        "session_candidate": {
            "boat_class": "DOUBLE_SCULL",
            "world_rowing_code": "2x",
            "crew_category": "MEN",
            "athlete_ids": ["synthetic-athlete-a", "synthetic-athlete-b"],
            "experience": "EXPERIENCED",
            "route_heading_deg": 0.0
        },
        "human_confirmations": {
            "resistance_band_used": None,
            "coach_observed_technique": None,
            "perceived_effort": None
        },
        "input_notice": "All people, dates, route coordinates, telemetry, and weather in this case are synthetic."
    }


def work_base_speed(rep: int) -> float:
    if rep <= 3:
        return 3.25
    if rep == 5:
        return 3.35
    return 3.55


def generate_telemetry(rng: random.Random) -> tuple[list[dict], list[dict], list[dict], float]:
    speedcoach_rows: list[dict] = []
    phases: list[dict] = []
    elapsed_s = 0.0
    cumulative_distance_m = 0.0
    shift_center_s: float | None = None

    def append_row(speed_m_s: float, spm: float) -> None:
        latitude, longitude = coordinate_at(cumulative_distance_m, elapsed_s)
        speedcoach_rows.append(
            {
                "timestamp": iso_at(elapsed_s),
                "elapsed_s": f"{elapsed_s:.3f}",
                "distance_m": f"{cumulative_distance_m:.3f}",
                "speed_m_s": f"{speed_m_s:.3f}",
                "stroke_rate_spm": f"{spm:.2f}",
                "latitude": f"{latitude:.7f}",
                "longitude": f"{longitude:.7f}",
                "heading_deg": "0.0"
            }
        )

    append_row(0.0, 0.0)
    for rep in range(1, 7):
        phase_start_s = elapsed_s
        phase_start_distance_m = cumulative_distance_m
        if rep == 4:
            shift_center_s = elapsed_s + 150.0
        actual_spm = 20.0 if rep in {1, 2, 3, 5} else 23.0
        phase_distance_m = 0.0
        spm_samples: list[float] = []
        speed_samples: list[float] = []

        while phase_distance_m < 1000.0:
            wind = wind_at(elapsed_s, shift_center_s or 10_000.0)
            noise = 0.035 * math.sin(elapsed_s / 17.0) + rng.uniform(-0.025, 0.025)
            speed_m_s = max(
                2.2,
                work_base_speed(rep) - 0.07 * wind["effective_headwind_m_s"] + noise
            )
            remaining_m = 1000.0 - phase_distance_m
            step_s = min(5.0, remaining_m / speed_m_s)
            travelled_m = speed_m_s * step_s
            elapsed_s += step_s
            phase_distance_m += travelled_m
            cumulative_distance_m += travelled_m
            sampled_spm = actual_spm + 0.35 * math.sin(elapsed_s / 11.0) + rng.uniform(-0.12, 0.12)
            spm_samples.append(sampled_spm)
            speed_samples.append(speed_m_s)
            append_row(speed_m_s, sampled_spm)

        phases.append(
            {
                "segment_id": f"work-{rep:02d}",
                "kind": "WORK",
                "start_offset_s": round(phase_start_s, 3),
                "end_offset_s": round(elapsed_s, 3),
                "distance_m": round(cumulative_distance_m - phase_start_distance_m, 3),
                "average_speed_m_s": round(sum(speed_samples) / len(speed_samples), 3),
                "average_spm": round(sum(spm_samples) / len(spm_samples), 2),
                "compliance": "DEVIATION" if rep == 5 else "COMPLIANT"
            }
        )

        if rep == 6:
            continue

        recovery_start_s = elapsed_s
        recovery_start_distance_m = cumulative_distance_m
        recovery_end_s = recovery_start_s + 240.0
        recovery_spm: list[float] = []
        recovery_speeds: list[float] = []
        while elapsed_s < recovery_end_s:
            step_s = min(5.0, recovery_end_s - elapsed_s)
            speed_m_s = 1.7 + 0.05 * math.sin(elapsed_s / 23.0) + rng.uniform(-0.03, 0.03)
            elapsed_s += step_s
            cumulative_distance_m += speed_m_s * step_s
            sampled_spm = 16.0 + 0.25 * math.sin(elapsed_s / 13.0) + rng.uniform(-0.1, 0.1)
            recovery_spm.append(sampled_spm)
            recovery_speeds.append(speed_m_s)
            append_row(speed_m_s, sampled_spm)
        phases.append(
            {
                "segment_id": f"recovery-{rep:02d}",
                "kind": "RECOVERY",
                "start_offset_s": round(recovery_start_s, 3),
                "end_offset_s": round(elapsed_s, 3),
                "distance_m": round(cumulative_distance_m - recovery_start_distance_m, 3),
                "average_speed_m_s": round(sum(recovery_speeds) / len(recovery_speeds), 3),
                "average_spm": round(sum(recovery_spm) / len(recovery_spm), 2),
                "compliance": "COMPLIANT"
            }
        )

    assert shift_center_s is not None
    mobile_rows: list[dict] = []
    sampled_speedcoach = speedcoach_rows[::2]
    if sampled_speedcoach[-1] is not speedcoach_rows[-1]:
        sampled_speedcoach.append(speedcoach_rows[-1])
    for row in sampled_speedcoach:
        elapsed = float(row["elapsed_s"])
        base_lat = float(row["latitude"])
        base_lon = float(row["longitude"])
        north_noise_m = rng.uniform(-2.5, 2.5)
        east_noise_m = rng.uniform(-2.5, 2.5)
        latitude = base_lat + math.degrees(north_noise_m / EARTH_RADIUS_M)
        longitude = base_lon + math.degrees(
            east_noise_m / (EARTH_RADIUS_M * math.cos(math.radians(ORIGIN_LAT)))
        )
        mobile_rows.append(
            {
                "timestamp": iso_at(elapsed, MOBILE_CLOCK_OFFSET_S),
                "elapsed_s": row["elapsed_s"],
                "distance_m": f"{float(row['distance_m']) * 1.012:.3f}",
                "speed_m_s": f"{max(0.0, float(row['speed_m_s']) * 1.01 + rng.uniform(-0.05, 0.05)):.3f}",
                "stroke_rate_spm": "0.00",
                "latitude": f"{latitude:.7f}",
                "longitude": f"{longitude:.7f}",
                "gps_accuracy_m": f"{rng.uniform(2.0, 5.0):.2f}"
            }
        )

    return speedcoach_rows, mobile_rows, phases, shift_center_s


def generate_environment(total_elapsed_s: float, shift_center_s: float) -> dict:
    samples = []
    elapsed_s = 0.0
    while elapsed_s <= total_elapsed_s + 30:
        wind = wind_at(elapsed_s, shift_center_s)
        samples.append(
            {
                "timestamp": iso_at(elapsed_s),
                "wind_speed_m_s": round(wind["wind_speed_m_s"], 3),
                "wind_direction_deg": round(wind["wind_direction_deg"], 3),
                "gust_speed_m_s": round(wind["gust_speed_m_s"], 3),
                "temperature_c": 18.0
            }
        )
        elapsed_s += 30.0
    return {
        "schema_version": "wake.environment_timeline.v1",
        "timeline_id": "synthetic-environment-002",
        "source": {
            "kind": "SYNTHETIC",
            "source_ref": "scripts/generate_synthetic_cases.py",
            "quality": "HIGH"
        },
        "direction_convention": "METEOROLOGICAL_FROM_DEGREES_TRUE_NORTH",
        "samples": samples
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def generate_ground_truth(phases: list[dict], shift_center_s: float) -> dict:
    expected_segments = [
        {
            "segment_id": phase["segment_id"],
            "kind": phase["kind"],
            "start_offset_s": phase["start_offset_s"],
            "end_offset_s": phase["end_offset_s"],
            "distance_m": phase["distance_m"],
            "average_speed_m_s": phase["average_speed_m_s"],
            "average_spm": phase["average_spm"],
            "compliance": phase["compliance"]
        }
        for phase in phases
    ]
    return {
        "schema_version": "wake.evaluation_ground_truth.v1",
        "fixture_id": CASE_ID,
        "fixture_version": "1.0",
        "applicable_dimensions": [
            "plan_interpretation",
            "session_association_and_alignment",
            "segment_reconstruction",
            "metric_level_source_trust",
            "deviation_detection",
            "environmental_interpretation",
            "evidence_and_abstention",
            "follow_up_questions"
        ],
        "expected_session_matches": [
            {
                "source_ids": ["speedcoach-synthetic", "mobile-synthetic"],
                "decision": "MATCH",
                "clock_offset_s": MOBILE_CLOCK_OFFSET_S
            }
        ],
        "expected_segments": expected_segments,
        "expected_source_policy": {
            "stroke_rate_spm": "speedcoach-synthetic",
            "distance_m": "speedcoach-synthetic",
            "route": "speedcoach-synthetic corroborated by mobile-synthetic",
            "environment": "synthetic-environment-002",
            "resistance_band_used": "human confirmation required"
        },
        "expected_claims": [
            {
                "claim_id": "completed-six-work-intervals",
                "expectation": "Six 1,000 m work intervals were completed.",
                "evidence_refs": ["speedcoach.csv", "plan.json"]
            },
            {
                "claim_id": "fifth-interval-spm-deviation",
                "expectation": "The fifth work interval averaged about 20 SPM, below the prescribed 22-24 SPM range.",
                "evidence_refs": ["speedcoach.csv", "plan.json"]
            },
            {
                "claim_id": "wind-shift-during-fourth",
                "expectation": f"Wind changed from light tailwind toward strong headwind around {shift_center_s:.1f} seconds, during the fourth work interval.",
                "evidence_refs": ["environment.json", "speedcoach.csv"]
            },
            {
                "claim_id": "slower-not-automatically-failed",
                "expectation": "Slower speed after the wind shift is not sufficient evidence of poor execution or athlete regression.",
                "evidence_refs": ["environment.json", "speedcoach.csv", "plan.json"]
            },
            {
                "claim_id": "mobile-spm-unusable",
                "expectation": "The mobile SPM channel is stuck at zero and must not support stroke-rate claims.",
                "evidence_refs": ["mobile.csv"]
            }
        ],
        "required_abstentions": [
            "Do not claim that the resistance band was used; the plan prescribes it but telemetry cannot observe it.",
            "Do not claim a technical rowing fault or crew synchronization problem from these inputs.",
            "Do not claim that wind caused every speed change or quantify athlete regression.",
            "Do not claim real athlete, location, date, or weather observations; the case is synthetic."
        ],
        "required_questions": [
            "Was the resistance band actually used during the first three work intervals?"
        ],
        "tolerances": {
            "segment_boundary_s": 10.0,
            "distance_m": 15.0,
            "stroke_rate_spm": 1.0,
            "clock_offset_s": 0.1
        }
    }


def readme() -> str:
    return """# Case 002: Wind Shift with a Real Plan Deviation

This fully synthetic case is derived from the structure of an approved coach prescription. It does not represent a real athlete, outing, location, date, or weather observation.

The plan prescribes six 1,000 m work intervals: the first three at 19-21 SPM with a resistance band, the final three at 22-24 SPM without it, and 3-5 minutes of active recovery.

The generated session contains two simultaneous explanations that the workflow must keep separate:

- wind changes from a light tailwind to a strong headwind during work interval four, reducing later speed;
- work interval five is a genuine execution deviation at about 20 SPM instead of 22-24 SPM.

The SpeedCoach-like source contains usable SPM. The mobile source follows the same route with a 37-second clock offset and a small distance bias, but its SPM channel is stuck at zero. The files cannot confirm resistance-band use, visible technique, or crew synchronization.

Only `input/` belongs in model context. `ground-truth.json` and `fixture-manifest.json` are evaluator artifacts.

Regenerate and verify from the repository root:

```bash
python3 scripts/generate_synthetic_cases.py
python3 scripts/verify_synthetic_case.py
```
"""


def build_case(output: Path) -> None:
    rng = random.Random(SEED)
    input_dir = output / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    plan = generate_plan()
    context = generate_context()
    speedcoach, mobile, phases, shift_center_s = generate_telemetry(rng)
    environment = generate_environment(float(speedcoach[-1]["elapsed_s"]), shift_center_s)
    ground_truth = generate_ground_truth(phases, shift_center_s)

    write_json(input_dir / "plan.json", plan)
    write_json(input_dir / "context.json", context)
    write_csv(input_dir / "speedcoach.csv", speedcoach)
    write_csv(input_dir / "mobile.csv", mobile)
    write_json(input_dir / "environment.json", environment)
    write_json(output / "ground-truth.json", ground_truth)
    (output / "README.md").write_text(readme(), encoding="utf-8")

    included = [
        output / "README.md",
        input_dir / "plan.json",
        input_dir / "context.json",
        input_dir / "speedcoach.csv",
        input_dir / "mobile.csv",
        input_dir / "environment.json",
        output / "ground-truth.json"
    ]
    manifest = {
        "schema": "wake.synthetic_fixture_manifest.v1",
        "fixture_id": CASE_ID,
        "fixture_version": "1.0",
        "generator": "scripts/generate_synthetic_cases.py",
        "generator_version": GENERATOR_VERSION,
        "seed": SEED,
        "files": {
            str(path.relative_to(output)): {
                "sha256": sha256(path),
                "bytes": path.stat().st_size
            }
            for path in included
        }
    }
    write_json(output / "fixture-manifest.json", manifest)
    print(
        f"Generated {CASE_ID}: {len(speedcoach)} SpeedCoach rows, "
        f"{len(mobile)} mobile rows, {len(environment['samples'])} environment samples"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/fixtures") / CASE_ID
    )
    args = parser.parse_args()
    build_case(args.output)


if __name__ == "__main__":
    main()
