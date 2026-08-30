#!/usr/bin/env python3
"""Generate isolated synthetic rowing cases 003-010 deterministically."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path


GENERATOR_VERSION = "1.0"
EARTH_RADIUS_M = 6_371_008.8
ORIGIN_LAT = 11.0
ORIGIN_LON = 11.0
START_TIME = datetime(2026, 2, 3, 6, 0, tzinfo=timezone(timedelta(hours=-3)))
PLAN_REPETITIONS = 4
WORK_DISTANCE_M = 500.0
TARGET_MIN_SPM = 20
TARGET_MAX_SPM = 22
RECOVERY_MIN_S = 120
RECOVERY_MAX_S = 180


SCENARIOS: dict[str, dict] = {
    "case-003-calm-expert-compliant": {
        "title": "Calm expert session, fully compliant",
        "seed": 20260830_003,
        "work_spm": [21.0, 21.0, 21.0, 21.0],
        "recovery_s": [150.0, 150.0, 150.0],
        "environment": {"wind_m_s": 0.5, "direction_deg": 90.0, "gust_m_s": 0.8},
        "expected_deviations": [],
    },
    "case-004-steady-headwind-compliant": {
        "title": "Steady headwind, compliant execution",
        "seed": 20260830_004,
        "work_spm": [21.0, 21.0, 21.0, 21.0],
        "recovery_s": [150.0, 150.0, 150.0],
        "environment": {"wind_m_s": 4.0, "direction_deg": 0.0, "gust_m_s": 4.5},
        "expected_deviations": [],
    },
    "case-005-tailwind-fast-not-improvement": {
        "title": "Tailwind-assisted speed without improvement claim",
        "seed": 20260830_005,
        "work_spm": [21.0, 21.0, 21.0, 21.0],
        "recovery_s": [150.0, 150.0, 150.0],
        "environment": {"wind_m_s": 4.0, "direction_deg": 180.0, "gust_m_s": 4.5},
        "expected_deviations": [],
    },
    "case-006-crosswind-gusts": {
        "title": "Strong crosswind and gusts, compliant SPM",
        "seed": 20260830_006,
        "work_spm": [21.0, 21.0, 21.0, 21.0],
        "recovery_s": [150.0, 150.0, 150.0],
        "environment": {"wind_m_s": 6.0, "direction_deg": 90.0, "gust_m_s": 9.0},
        "expected_deviations": [],
    },
    "case-007-incomplete-intervals": {
        "title": "Only three of four planned intervals observed",
        "seed": 20260830_007,
        "work_spm": [21.0, 21.0, 21.0],
        "recovery_s": [150.0, 150.0],
        "environment": None,
        "expected_deviations": ["work-04"],
    },
    "case-008-correct-distance-wrong-spm": {
        "title": "Distance completed with one low-SPM interval",
        "seed": 20260830_008,
        "work_spm": [21.0, 21.0, 19.0, 21.0],
        "recovery_s": [150.0, 150.0, 150.0],
        "environment": None,
        "expected_deviations": ["work-03"],
    },
    "case-009-excess-recovery": {
        "title": "Second recovery exceeds the prescribed maximum",
        "seed": 20260830_009,
        "work_spm": [21.0, 21.0, 21.0, 21.0],
        "recovery_s": [150.0, 300.0, 150.0],
        "environment": None,
        "expected_deviations": ["recovery-02"],
    },
    "case-010-mobile-spm-zero": {
        "title": "Mobile SPM stuck at zero while SpeedCoach remains usable",
        "seed": 20260830_010,
        "work_spm": [21.0, 21.0, 21.0, 21.0],
        "recovery_s": [150.0, 150.0, 150.0],
        "environment": None,
        "mobile_spm_zero": True,
        "expected_deviations": [],
    },
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iso_at(elapsed_s: float, offset_s: float = 0.0) -> str:
    return (START_TIME + timedelta(seconds=elapsed_s + offset_s)).isoformat(
        timespec="milliseconds"
    )


def coordinates(distance_m: float, elapsed_s: float) -> tuple[float, float]:
    north_m = distance_m
    east_m = 1.5 * math.sin(elapsed_s / 90.0)
    latitude = ORIGIN_LAT + math.degrees(north_m / EARTH_RADIUS_M)
    longitude = ORIGIN_LON + math.degrees(
        east_m / (EARTH_RADIUS_M * math.cos(math.radians(ORIGIN_LAT)))
    )
    return latitude, longitude


def plan(case_id: str) -> dict:
    return {
        "schema_version": "wake.training_plan.v1",
        "plan_id": f"plan-{case_id}",
        "scheduled_date": "2026-02-03",
        "timezone": "America/Sao_Paulo",
        "source": {
            "kind": "SYNTHETIC",
            "provenance": "SYNTHETIC",
            "source_ref": "scripts/generate_diagnostic_cases.py",
        },
        "modality": "WATER",
        "athlete_scope": {"kind": "CREW", "ids": ["synthetic-crew-diagnostic"]},
        "goal_id": "synthetic-goal-diagnostic",
        "coach_language": "4 x 500 m at 20-22 SPM with 2-3 minutes active recovery.",
        "blocks": [
            {
                "block_id": "work-500m",
                "kind": "WORK",
                "repetitions": PLAN_REPETITIONS,
                "distance_m": WORK_DISTANCE_M,
                "duration_s": None,
                "stroke_rate": {"min_spm": TARGET_MIN_SPM, "max_spm": TARGET_MAX_SPM},
                "zone": "B2/B3",
                "zone_system": "STANDARD_ROWING_ZONES",
                "recovery": {
                    "min_s": RECOVERY_MIN_S,
                    "max_s": RECOVERY_MAX_S,
                    "mode": "ACTIVE_LIGHT_ROWING",
                },
                "equipment": [],
                "instructions": ["Keep every work interval continuous."],
            }
        ],
        "unresolved_terms": [],
        "notes": "Entirely synthetic diagnostic prescription.",
    }


def context(case_id: str, scenario: dict, source_kinds: list[str]) -> dict:
    provided = [
        {
            "source_id": f"speedcoach-{case_id}",
            "kind": "SPEEDCOACH",
            "path": "speedcoach.csv",
        },
        {
            "source_id": f"plan-{case_id}",
            "kind": "TRAINING_PLAN",
            "path": "plan.json",
        },
    ]
    if "MOBILE" in source_kinds:
        provided.append(
            {
                "source_id": f"mobile-{case_id}",
                "kind": "MOBILE",
                "path": "mobile.csv",
            }
        )
    if "ENVIRONMENT" in source_kinds:
        provided.append(
            {
                "source_id": f"environment-{case_id}",
                "kind": "ENVIRONMENT",
                "path": "environment.json",
            }
        )
    return {
        "schema_version": "wake.synthetic_case_context.v1",
        "case_id": case_id,
        "investigation_request": (
            "Compare the planned and performed session, identify only supported "
            "deviations, select trustworthy metrics, and preserve uncertainty."
        ),
        "provided_sources": provided,
        "session_candidate": {
            "boat_class": "DOUBLE_SCULL",
            "world_rowing_code": "2x",
            "crew_category": "OPEN",
            "athlete_ids": ["synthetic-athlete-c", "synthetic-athlete-d"],
            "experience": "EXPERIENCED",
            "route_heading_deg": 0.0,
        },
        "human_confirmations": {
            "coach_observed_technique": None,
            "perceived_effort": None,
        },
        "scenario_label": scenario["title"],
        "input_notice": (
            "All people, dates, route coordinates, telemetry, and conditions in "
            "this diagnostic case are synthetic."
        ),
    }


def telemetry(case_id: str, scenario: dict) -> tuple[list[dict], list[dict], list[dict]]:
    rng = random.Random(scenario["seed"])
    rows: list[dict] = []
    phases: list[dict] = []
    elapsed_s = 0.0
    distance_m = 0.0
    environment = scenario.get("environment")
    effective_headwind = 0.0
    if environment:
        effective_headwind = environment["wind_m_s"] * math.cos(
            math.radians(environment["direction_deg"])
        )

    def append_row(speed_m_s: float, spm: float) -> None:
        latitude, longitude = coordinates(distance_m, elapsed_s)
        rows.append(
            {
                "timestamp": iso_at(elapsed_s),
                "elapsed_s": f"{elapsed_s:.3f}",
                "distance_m": f"{distance_m:.3f}",
                "speed_m_s": f"{speed_m_s:.3f}",
                "stroke_rate_spm": f"{spm:.2f}",
                "latitude": f"{latitude:.7f}",
                "longitude": f"{longitude:.7f}",
                "heading_deg": "0.0",
            }
        )

    for work_index, prescribed_spm in enumerate(scenario["work_spm"], start=1):
        phase_start_s = elapsed_s
        phase_start_m = distance_m
        speed_samples: list[float] = []
        spm_samples: list[float] = []
        while True:
            noise = rng.uniform(-0.025, 0.025)
            speed_m_s = max(2.0, 3.35 - 0.14 * effective_headwind + noise)
            remaining = WORK_DISTANCE_M - (distance_m - phase_start_m)
            final_step = remaining <= speed_m_s * 5.0
            step_s = remaining / speed_m_s if final_step else 5.0
            elapsed_s += step_s
            distance_m = (
                phase_start_m + WORK_DISTANCE_M
                if final_step
                else distance_m + speed_m_s * step_s
            )
            sampled_spm = prescribed_spm + rng.uniform(-0.12, 0.12)
            speed_samples.append(speed_m_s)
            spm_samples.append(sampled_spm)
            append_row(speed_m_s, sampled_spm)
            if final_step:
                break
        compliance = (
            "DEVIATION"
            if f"work-{work_index:02d}" in scenario["expected_deviations"]
            else "COMPLIANT"
        )
        phases.append(
            {
                "segment_id": f"work-{work_index:02d}",
                "kind": "WORK",
                "start_offset_s": round(phase_start_s, 3),
                "end_offset_s": round(elapsed_s, 3),
                "distance_m": round(distance_m - phase_start_m, 3),
                "average_speed_m_s": round(sum(speed_samples) / len(speed_samples), 3),
                "average_spm": round(sum(spm_samples) / len(spm_samples), 2),
                "compliance": compliance,
            }
        )
        if work_index > len(scenario["recovery_s"]):
            continue
        recovery_start_s = elapsed_s
        recovery_start_m = distance_m
        recovery_speed: list[float] = []
        recovery_spm: list[float] = []
        recovery_end_s = elapsed_s + scenario["recovery_s"][work_index - 1]
        while elapsed_s < recovery_end_s:
            step_s = min(5.0, recovery_end_s - elapsed_s)
            speed_m_s = 1.65 + rng.uniform(-0.02, 0.02)
            elapsed_s += step_s
            distance_m += speed_m_s * step_s
            sampled_spm = 16.0 + rng.uniform(-0.1, 0.1)
            recovery_speed.append(speed_m_s)
            recovery_spm.append(sampled_spm)
            append_row(speed_m_s, sampled_spm)
        recovery_id = f"recovery-{work_index:02d}"
        phases.append(
            {
                "segment_id": recovery_id,
                "kind": "RECOVERY",
                "start_offset_s": round(recovery_start_s, 3),
                "end_offset_s": round(elapsed_s, 3),
                "distance_m": round(distance_m - recovery_start_m, 3),
                "average_speed_m_s": round(sum(recovery_speed) / len(recovery_speed), 3),
                "average_spm": round(sum(recovery_spm) / len(recovery_spm), 2),
                "compliance": (
                    "DEVIATION"
                    if recovery_id in scenario["expected_deviations"]
                    else "COMPLIANT"
                ),
            }
        )

    if len(scenario["work_spm"]) < PLAN_REPETITIONS:
        phases.append(
            {
                "segment_id": "work-04",
                "kind": "WORK",
                "start_offset_s": round(elapsed_s, 3),
                "end_offset_s": round(elapsed_s, 3),
                "distance_m": None,
                "average_speed_m_s": None,
                "average_spm": None,
                "compliance": "DEVIATION",
            }
        )

    mobile: list[dict] = []
    if scenario.get("mobile_spm_zero"):
        for row in rows[::2]:
            mobile.append(
                {
                    "timestamp": iso_at(float(row["elapsed_s"]), 18.0),
                    "elapsed_s": row["elapsed_s"],
                    "distance_m": f"{float(row['distance_m']) * 1.01:.3f}",
                    "speed_m_s": row["speed_m_s"],
                    "stroke_rate_spm": "0.00",
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "gps_accuracy_m": "3.00",
                }
            )
    return rows, mobile, phases


def environment_timeline(case_id: str, scenario: dict, duration_s: float) -> dict | None:
    condition = scenario.get("environment")
    if not condition:
        return None
    samples = []
    elapsed_s = 0.0
    while elapsed_s <= duration_s + 30:
        samples.append(
            {
                "timestamp": iso_at(elapsed_s),
                "wind_speed_m_s": condition["wind_m_s"],
                "wind_direction_deg": condition["direction_deg"],
                "gust_speed_m_s": condition["gust_m_s"],
                "temperature_c": 19.0,
            }
        )
        elapsed_s += 30.0
    return {
        "schema_version": "wake.environment_timeline.v1",
        "timeline_id": f"environment-{case_id}",
        "source": {
            "kind": "SYNTHETIC",
            "source_ref": "scripts/generate_diagnostic_cases.py",
            "quality": "HIGH",
        },
        "direction_convention": "METEOROLOGICAL_FROM_DEGREES_TRUE_NORTH",
        "samples": samples,
    }


def ground_truth(case_id: str, scenario: dict, phases: list[dict]) -> dict:
    has_mobile = bool(scenario.get("mobile_spm_zero"))
    has_environment = scenario.get("environment") is not None
    dimensions = [
        "plan_interpretation",
        "segment_reconstruction",
        "deviation_detection",
        "evidence_and_abstention",
    ]
    if has_mobile:
        dimensions.extend(
            ["session_association_and_alignment", "metric_level_source_trust"]
        )
    if has_environment:
        dimensions.append("environmental_interpretation")
    if case_id == "case-007-incomplete-intervals":
        dimensions.append("follow_up_questions")

    speedcoach_id = f"speedcoach-{case_id}"
    policy = {
        "stroke_rate_spm": speedcoach_id,
        "distance_m": speedcoach_id,
        "route": speedcoach_id,
    }
    if has_environment:
        policy["environment"] = f"environment-{case_id}"
    if has_mobile:
        policy["mobile_spm"] = "reject"

    claims = [
        {
            "claim_id": "observed-work-count",
            "expectation": (
                f"Telemetry contains {len(scenario['work_spm'])} observed work intervals "
                f"against {PLAN_REPETITIONS} planned intervals."
            ),
            "evidence_refs": ["speedcoach.csv", "plan.json"],
        }
    ]
    if case_id == "case-008-correct-distance-wrong-spm":
        claims.append(
            {
                "claim_id": "work-03-low-spm",
                "expectation": "Work interval three is below the prescribed SPM range.",
                "evidence_refs": ["speedcoach.csv", "plan.json"],
            }
        )
    if case_id == "case-009-excess-recovery":
        claims.append(
            {
                "claim_id": "recovery-02-excess",
                "expectation": "Recovery interval two exceeds the prescribed maximum.",
                "evidence_refs": ["speedcoach.csv", "plan.json"],
            }
        )
    if has_mobile:
        claims.append(
            {
                "claim_id": "mobile-spm-unusable",
                "expectation": "Mobile SPM is stuck at zero and cannot support stroke-rate claims.",
                "evidence_refs": ["mobile.csv"],
            }
        )

    abstentions = [
        "Do not infer visible technique or crew synchronization from numeric telemetry.",
        "Do not present synthetic people, places, dates, or conditions as real observations.",
    ]
    if has_environment:
        abstentions.append(
            "Do not claim that wind caused the measured speed or proves athlete improvement or regression."
        )
    if has_mobile:
        abstentions.append("Do not use the zero-only mobile SPM channel.")

    return {
        "schema_version": "wake.evaluation_ground_truth.v1",
        "fixture_id": case_id,
        "fixture_version": "1.0",
        "applicable_dimensions": dimensions,
        "expected_session_matches": (
            [
                {
                    "source_ids": [speedcoach_id, f"mobile-{case_id}"],
                    "decision": "MATCH",
                    "clock_offset_s": 18.0,
                }
            ]
            if has_mobile
            else []
        ),
        "expected_segments": phases,
        "expected_source_policy": policy,
        "expected_claims": claims,
        "required_abstentions": abstentions,
        "required_questions": (
            ["Was the fourth planned work interval intentionally omitted or was the recording stopped early?"]
            if case_id == "case-007-incomplete-intervals"
            else []
        ),
        "tolerances": {
            "segment_boundary_s": 10.0,
            "distance_m": 15.0,
            "stroke_rate_spm": 1.0,
            "clock_offset_s": 0.1,
        },
    }


def readme(case_id: str, scenario: dict) -> str:
    return (
        f"# {scenario['title']}\n\n"
        "This fixture is entirely synthetic and isolates one evaluation behavior. "
        "Only `input/` belongs in model context; `ground-truth.json` and "
        "`fixture-manifest.json` are evaluator-only artifacts.\n"
    )


def build_case(case_id: str, scenario: dict, output: Path) -> None:
    input_dir = output / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    speedcoach, mobile, phases = telemetry(case_id, scenario)
    environment = environment_timeline(
        case_id, scenario, float(speedcoach[-1]["elapsed_s"])
    )
    source_kinds = ["SPEEDCOACH", "TRAINING_PLAN"]
    if mobile:
        source_kinds.append("MOBILE")
    if environment:
        source_kinds.append("ENVIRONMENT")

    write_json(input_dir / "plan.json", plan(case_id))
    write_json(input_dir / "context.json", context(case_id, scenario, source_kinds))
    write_csv(input_dir / "speedcoach.csv", speedcoach)
    if mobile:
        write_csv(input_dir / "mobile.csv", mobile)
    if environment:
        write_json(input_dir / "environment.json", environment)
    write_json(output / "ground-truth.json", ground_truth(case_id, scenario, phases))
    (output / "README.md").write_text(readme(case_id, scenario), encoding="utf-8")

    included = sorted(path for path in output.rglob("*") if path.is_file())
    manifest = {
        "schema": "wake.synthetic_fixture_manifest.v1",
        "fixture_id": case_id,
        "fixture_version": "1.0",
        "generator": "scripts/generate_diagnostic_cases.py",
        "generator_version": GENERATOR_VERSION,
        "seed": scenario["seed"],
        "files": {
            str(path.relative_to(output)): {
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
            for path in included
        },
    }
    write_json(output / "fixture-manifest.json", manifest)


def build_all(output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    for case_id, scenario in SCENARIOS.items():
        build_case(case_id, scenario, output_root / case_id)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/fixtures"),
    )
    args = parser.parse_args()
    build_all(args.output_root)
    print(f"Generated {len(SCENARIOS)} diagnostic cases under {args.output_root}")


if __name__ == "__main__":
    main()
