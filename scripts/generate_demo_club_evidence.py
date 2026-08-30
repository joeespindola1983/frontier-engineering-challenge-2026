#!/usr/bin/env python3
"""Generate complete public evidence bundles for two demo-club candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path


GENERATOR_VERSION = "1.0"
EARTH_RADIUS_M = 6_371_008.8
ORIGIN_LAT = 12.0
ORIGIN_LON = 12.0

CASES = {
    "club-bridge-mixed-20260820-spm": {
        "title": "Bridge Mixed 2x · second 4 km interval below target SPM",
        "date": "2026-08-20",
        "start_hour": 18,
        "crew_id": "crew-2x-mixed-a",
        "boat_id": "boat-2x-horizon",
        "boat_class": "DOUBLE_SCULL",
        "world_rowing_code": "2x",
        "crew_category": "MIXED",
        "athlete_ids": ["athlete-bruno", "athlete-camila"],
        "repetitions": 2,
        "work_distance_m": 4_000,
        "target_min_spm": 20,
        "target_max_spm": 20,
        "work_spm": [20.0, 18.0],
        "recovery_s": [180.0],
        "recovery_min_s": 120,
        "recovery_max_s": 300,
        "zone": "B2/B3",
        "coach_language": "2 x 4 km at voga 20 with active recovery.",
    },
    "club-atlas-men-20260828-recovery": {
        "title": "Atlas Men 4x · second recovery above planned maximum",
        "date": "2026-08-28",
        "start_hour": 6,
        "crew_id": "crew-4x-men",
        "boat_id": "boat-4x-atlas",
        "boat_class": "QUADRUPLE_SCULL",
        "world_rowing_code": "4x",
        "crew_category": "MEN",
        "athlete_ids": [
            "athlete-lucas",
            "athlete-rafael",
            "athlete-bruno",
            "athlete-diego",
        ],
        "repetitions": 4,
        "work_distance_m": 2_000,
        "target_min_spm": 20,
        "target_max_spm": 22,
        "work_spm": [21.0, 21.0, 21.0, 21.0],
        "recovery_s": [180.0, 247.0, 180.0],
        "recovery_min_s": 120,
        "recovery_max_s": 180,
        "zone": "B2/B3",
        "coach_language": "4 x 2 km at 20-22 SPM with 2-3 minutes active recovery.",
    },
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def start_time(case: dict) -> datetime:
    return datetime.fromisoformat(
        f"{case['date']}T{case['start_hour']:02d}:00:00-03:00"
    )


def coordinates(distance_m: float, elapsed_s: float) -> tuple[float, float]:
    north_m = distance_m
    east_m = 1.2 * math.sin(elapsed_s / 80.0)
    latitude = ORIGIN_LAT + math.degrees(north_m / EARTH_RADIUS_M)
    longitude = ORIGIN_LON + math.degrees(
        east_m / (EARTH_RADIUS_M * math.cos(math.radians(ORIGIN_LAT)))
    )
    return latitude, longitude


def build_plan(case_id: str, case: dict) -> dict:
    return {
        "schema_version": "wake.training_plan.v1",
        "plan_id": f"plan-{case_id}",
        "scheduled_date": case["date"],
        "timezone": "America/Sao_Paulo",
        "source": {
            "kind": "SYNTHETIC",
            "provenance": "SYNTHETIC",
            "source_ref": "scripts/generate_demo_club_evidence.py",
        },
        "modality": "WATER",
        "athlete_scope": {"kind": "CREW", "ids": [case["crew_id"]]},
        "goal_id": "wake-demo-club-two-week-period",
        "coach_language": case["coach_language"],
        "blocks": [
            {
                "block_id": "work-main",
                "kind": "WORK",
                "repetitions": case["repetitions"],
                "distance_m": case["work_distance_m"],
                "duration_s": None,
                "stroke_rate": {
                    "min_spm": case["target_min_spm"],
                    "max_spm": case["target_max_spm"],
                },
                "zone": case["zone"],
                "zone_system": "STANDARD_ROWING_ZONES",
                "recovery": {
                    "min_s": case["recovery_min_s"],
                    "max_s": case["recovery_max_s"],
                    "mode": "ACTIVE_LIGHT_ROWING",
                },
                "equipment": [],
                "instructions": ["Keep each work interval continuous."],
            }
        ],
        "unresolved_terms": [],
        "notes": (
            "Real-informed synthetic prescription. It models a supplied rowing-plan "
            "pattern and does not describe a real athlete session."
        ),
    }


def build_context(case_id: str, case: dict) -> dict:
    return {
        "schema_version": "wake.synthetic_case_context.v1",
        "case_id": case_id,
        "investigation_request": (
            "Compare the planned and performed session, identify only supported "
            "deviations, select trustworthy metrics, and preserve uncertainty."
        ),
        "provided_sources": [
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
        ],
        "session_candidate": {
            "boat_id": case["boat_id"],
            "boat_class": case["boat_class"],
            "world_rowing_code": case["world_rowing_code"],
            "crew_id": case["crew_id"],
            "crew_category": case["crew_category"],
            "athlete_ids": case["athlete_ids"],
            "experience": "CLUB_COMPETITIVE",
            "route_heading_deg": 0.0,
        },
        "human_confirmations": {
            "coach_observed_technique": None,
            "perceived_effort": None,
        },
        "scenario_label": case["title"],
        "input_notice": (
            "All identities, dates, route coordinates, telemetry, and exact outcomes "
            "in this public demo-club bundle are synthetic. Formats and workout "
            "patterns are informed by supplied real rowing material."
        ),
    }


def build_telemetry(case: dict) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    start = start_time(case)
    elapsed_s = 0.0
    distance_m = 0.0

    def append_row(speed_m_s: float, spm: float) -> None:
        latitude, longitude = coordinates(distance_m, elapsed_s)
        timestamp = (start + timedelta(seconds=elapsed_s)).isoformat(timespec="milliseconds")
        rows.append(
            {
                "timestamp": timestamp,
                "elapsed_s": f"{elapsed_s:.3f}",
                "distance_m": f"{distance_m:.3f}",
                "speed_m_s": f"{speed_m_s:.3f}",
                "stroke_rate_spm": f"{spm:.2f}",
                "latitude": f"{latitude:.7f}",
                "longitude": f"{longitude:.7f}",
                "heading_deg": "0.0",
            }
        )

    for index, work_spm in enumerate(case["work_spm"]):
        work_start_m = distance_m
        work_speed_m_s = 3.4
        while True:
            remaining_m = case["work_distance_m"] - (distance_m - work_start_m)
            final_step = remaining_m <= work_speed_m_s * 5.0
            step_s = remaining_m / work_speed_m_s if final_step else 5.0
            elapsed_s += step_s
            distance_m = (
                work_start_m + case["work_distance_m"]
                if final_step
                else distance_m + work_speed_m_s * step_s
            )
            append_row(work_speed_m_s, work_spm)
            if final_step:
                break

        if index >= len(case["recovery_s"]):
            continue
        recovery_elapsed = 0.0
        recovery_speed_m_s = 1.4
        while recovery_elapsed < case["recovery_s"][index]:
            step_s = min(5.0, case["recovery_s"][index] - recovery_elapsed)
            elapsed_s += step_s
            recovery_elapsed += step_s
            distance_m += recovery_speed_m_s * step_s
            append_row(recovery_speed_m_s, 14.0)
    return rows


def build_demo_club_evidence(output_root: Path) -> dict:
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_cases = []
    for case_id, case in CASES.items():
        input_dir = output_root / case_id / "input"
        write_json(input_dir / "plan.json", build_plan(case_id, case))
        write_json(input_dir / "context.json", build_context(case_id, case))
        write_csv(input_dir / "speedcoach.csv", build_telemetry(case))
        input_sha256 = {
            name: sha256(input_dir / name)
            for name in ("context.json", "plan.json", "speedcoach.csv")
        }
        manifest_cases.append(
            {
                "case_id": case_id,
                "title": case["title"],
                "provenance": "REAL_INFORMED_SYNTHETIC",
                "generator_version": GENERATOR_VERSION,
                "input_sha256": input_sha256,
                "agent_executed": False,
            }
        )

    manifest = {
        "schema_version": "wake.demo_club_evidence_manifest.v1",
        "generator": "scripts/generate_demo_club_evidence.py",
        "cases": manifest_cases,
        "boundary": (
            "These are complete public synthetic source bundles, not observed athlete "
            "sessions and not completed agent analyses."
        ),
    }
    write_json(output_root / "manifest.json", manifest)
    (output_root / "README.md").write_text(
        "# Demo-club evidence bundles\n\n"
        "Two complete real-informed synthetic plan + SpeedCoach + context bundles "
        "for the numeric candidates selected by the zero-cost club-period screen. "
        "They are public fixtures, not real athlete sessions. `agent_executed` remains "
        "false until an explicit paid run is preserved.\n\n"
        "- `club-bridge-mixed-20260820-spm` reconstructs two planned 4 km work "
        "intervals and exposes only `work-02` below the prescribed 20 SPM.\n"
        "- `club-atlas-men-20260828-recovery` reconstructs four planned 2 km work "
        "intervals and exposes only `recovery-02` above the allowed recovery duration.\n\n"
        "Regenerate and verify them without a model call:\n\n"
        "```bash\n"
        "uv run python scripts/generate_demo_club_evidence.py\n"
        "uv run python scripts/verify_demo_club_evidence.py\n"
        "```\n\n"
        "The verifier checks manifest hashes, text privacy invariants, the "
        "training-plan schema, and exact deterministic v2 reconstruction. Passing "
        "preflight proves fixture and tool behavior; it does not prove agent quality "
        "or a longitudinal coaching conclusion.\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/demo-club-evidence"),
    )
    args = parser.parse_args()
    manifest = build_demo_club_evidence(args.output)
    print(f"Generated {len(manifest['cases'])} demo-club evidence bundles in {args.output}")


if __name__ == "__main__":
    main()
