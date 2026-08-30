#!/usr/bin/env python3
"""Generate the complete two-week real-informed synthetic demo-club batch."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from generate_demo_club_evidence import (
    CASES as VERIFIED_CASES,
    build_context,
    build_plan,
    build_telemetry,
    write_csv,
    write_json,
)


GENERATOR_VERSION = "1.2"

ATHLETES = {
    "crew-2x-men": ["athlete-lucas", "athlete-rafael"],
    "crew-2x-women": ["athlete-marina", "athlete-helena"],
    "crew-2x-mixed-a": ["athlete-bruno", "athlete-camila"],
    "crew-2x-mixed-b": ["athlete-diego", "athlete-julia"],
    "crew-4x-men": ["athlete-lucas", "athlete-rafael", "athlete-bruno", "athlete-diego"],
    "crew-4x-women": ["athlete-marina", "athlete-helena", "athlete-camila", "athlete-julia"],
    "crew-4x-mixed-a": ["athlete-caio", "athlete-bianca", "athlete-andre", "athlete-larissa"],
    "crew-4x-mixed-b": ["athlete-felipe", "athlete-renata", "athlete-mateus", "athlete-sofia"],
    "crew-8x-men": [
        "athlete-lucas", "athlete-rafael", "athlete-bruno", "athlete-diego",
        "athlete-caio", "athlete-andre", "athlete-felipe", "athlete-mateus",
    ],
    "crew-8x-women": [
        "athlete-marina", "athlete-helena", "athlete-camila", "athlete-julia",
        "athlete-bianca", "athlete-larissa", "athlete-renata", "athlete-sofia",
    ],
}

CREW_META = {
    "crew-2x-men": ("boat-2x-aurora", "DOUBLE_SCULL", "2x", "MEN"),
    "crew-2x-women": ("boat-2x-iris", "DOUBLE_SCULL", "2x", "WOMEN"),
    "crew-2x-mixed-a": ("boat-2x-horizon", "DOUBLE_SCULL", "2x", "MIXED"),
    "crew-2x-mixed-b": ("boat-2x-current", "DOUBLE_SCULL", "2x", "MIXED"),
    "crew-4x-men": ("boat-4x-atlas", "QUADRUPLE_SCULL", "4x", "MEN"),
    "crew-4x-women": ("boat-4x-gaia", "QUADRUPLE_SCULL", "4x", "WOMEN"),
    "crew-4x-mixed-a": ("boat-4x-mistral", "QUADRUPLE_SCULL", "4x", "MIXED"),
    "crew-4x-mixed-b": ("boat-4x-dawn", "QUADRUPLE_SCULL", "4x", "MIXED"),
    "crew-8x-men": ("boat-8x-north", "OCTUPLE_SCULL", "8x", "MEN"),
    "crew-8x-women": ("boat-8x-south", "OCTUPLE_SCULL", "8x", "WOMEN"),
}

SCHEDULES = {
    "crew-2x-men": [("2026-08-17", "AM"), ("2026-08-19", "AM"), ("2026-08-24", "AM"), ("2026-08-27", "PM")],
    "crew-2x-women": [("2026-08-18", "AM"), ("2026-08-20", "AM"), ("2026-08-25", "AM"), ("2026-08-28", "PM")],
    "crew-2x-mixed-a": [("2026-08-17", "PM"), ("2026-08-20", "PM"), ("2026-08-24", "PM"), ("2026-08-26", "PM")],
    "crew-2x-mixed-b": [("2026-08-18", "PM"), ("2026-08-21", "PM"), ("2026-08-25", "PM"), ("2026-08-26", "PM")],
    "crew-4x-men": [("2026-08-18", "AM"), ("2026-08-21", "AM"), ("2026-08-26", "AM"), ("2026-08-28", "AM")],
    "crew-4x-women": [("2026-08-17", "AM"), ("2026-08-19", "PM"), ("2026-08-24", "AM"), ("2026-08-27", "AM")],
    "crew-4x-mixed-a": [("2026-08-19", "AM"), ("2026-08-21", "AM"), ("2026-08-25", "AM"), ("2026-08-28", "AM")],
    "crew-4x-mixed-b": [("2026-08-18", "AM"), ("2026-08-20", "AM"), ("2026-08-27", "PM"), ("2026-08-28", "PM")],
    "crew-8x-men": [("2026-08-19", "EVENING"), ("2026-08-21", "EVENING"), ("2026-08-26", "EVENING")],
    "crew-8x-women": [("2026-08-20", "EVENING"), ("2026-08-25", "EVENING"), ("2026-08-28", "EVENING")],
}

UNAVAILABLE = {
    "crew-2x-men:2026-08-24",
    "crew-4x-women:2026-08-27",
    "crew-8x-men:2026-08-26",
}

PLAN_TITLES = {
    "2x": ["B0/B2 technical row", "2 × 4 km · rate 20", "6 × 1 km · rate 20", "B1 endurance · 12 km"],
    "4x": ["B2/B3 · 6 × 1 km", "B0/B2 technique · 12 km", "Rate ladder · 18–24 SPM", "Race pieces · 4 × 2 km"],
    "8x": ["Crew rhythm · B1", "Race pieces · 4 × 2 km", "B0/B2 technique · 14 km"],
}

BASE_DISTANCE = {"2x": 12_000, "4x": 14_000, "8x": 16_000}
START_HOUR = {"AM": 6, "PM": 18, "EVENING": 19}

VERIFIED_IDS = {
    "crew-2x-mixed-a:2026-08-20": "club-bridge-mixed-20260820-spm",
    "crew-4x-men:2026-08-28": "club-atlas-men-20260828-recovery",
}

ERG_SPECS = [
    {"session_id": "activity-marina-erg-20260827", "date": "2026-08-27", "slot": "AM", "athlete_id": "athlete-marina", "title": "10 km indoor alternative after 4x cancellation", "training_role": "ALTERNATIVE", "association_status": "PLAN_CONFIRMED", "workout_type": "FIXED_DISTANCE", "duration_s": 2450, "distance_m": 10000, "average_spm": 22.4, "average_watts": 188, "split_count": 5},
    {"session_id": "activity-helena-erg-20260827", "date": "2026-08-27", "slot": "AM", "athlete_id": "athlete-helena", "title": "10 km indoor alternative after 4x cancellation", "training_role": "ALTERNATIVE", "association_status": "PLAN_CONFIRMED", "workout_type": "FIXED_DISTANCE", "duration_s": 2480, "distance_m": 10000, "average_spm": 21.8, "average_watts": 178, "split_count": 5},
    *[
        {"session_id": f"activity-{athlete_id.removeprefix('athlete-')}-erg-20260826", "date": "2026-08-26", "slot": "EVENING", "athlete_id": athlete_id, "title": "6 × 2 km indoor alternative after 8x cancellation", "training_role": "ALTERNATIVE", "association_status": "PLAN_CONFIRMED", "workout_type": "INTERVAL", "duration_s": 3530 + index * 12, "distance_m": 12000, "average_spm": 21.5 + (index % 3) * 0.5, "average_watts": 190 - index * 3, "split_count": 11, "work_repetitions": 6, "recovery_s": 120}
        for index, athlete_id in enumerate(ATHLETES["crew-8x-men"][:6])
    ],
    {"session_id": "activity-lucas-erg-20260818", "date": "2026-08-18", "slot": "AM", "athlete_id": "athlete-lucas", "title": "1,000 m low-rate technique after water", "training_role": "POST_WATER", "association_status": "PLAN_CONFIRMED", "workout_type": "FIXED_DISTANCE", "duration_s": 250, "distance_m": 1000, "average_spm": 12, "average_watts": 179, "split_count": 5},
    {"session_id": "activity-marina-erg-20260820", "date": "2026-08-20", "slot": "AM", "athlete_id": "athlete-marina", "title": "1,000 m activation before water", "training_role": "PRE_WATER", "association_status": "PLAN_CONFIRMED", "workout_type": "FIXED_DISTANCE", "duration_s": 248, "distance_m": 1000, "average_spm": 18, "average_watts": 185, "split_count": 5},
    {"session_id": "activity-camila-erg-20260819", "date": "2026-08-19", "slot": "PM", "athlete_id": "athlete-camila", "title": "1,000 m activation before water", "training_role": "PRE_WATER", "association_status": "PLAN_CONFIRMED", "workout_type": "FIXED_DISTANCE", "duration_s": 244, "distance_m": 1000, "average_spm": 20, "average_watts": 195, "split_count": 5},
    {"session_id": "activity-sofia-erg-20260824", "date": "2026-08-24", "slot": "AM", "athlete_id": "athlete-sofia", "title": "30-minute steady indoor row", "training_role": "PRIMARY", "association_status": "STANDALONE", "workout_type": "FIXED_TIME", "duration_s": 1800, "distance_m": 6500, "average_spm": 20, "average_watts": 130, "split_count": 6},
    {"session_id": "activity-felipe-erg-20260825", "date": "2026-08-25", "slot": "PM", "athlete_id": "athlete-felipe", "title": "4–3–2–1 minute indoor ladder", "training_role": "PRIMARY", "association_status": "STANDALONE", "workout_type": "INTERVAL", "duration_s": 780, "distance_m": 2550, "average_spm": 22, "average_watts": 214, "split_count": 7, "work_durations_s": [240, 180, 120, 60], "recovery_s": 60},
    {"session_id": "activity-bianca-erg-20260824", "date": "2026-08-24", "slot": "PM", "athlete_id": "athlete-bianca", "title": "2 km indoor benchmark", "training_role": "PRIMARY", "association_status": "STANDALONE", "workout_type": "FIXED_DISTANCE", "duration_s": 480, "distance_m": 2000, "average_spm": 26, "average_watts": 203, "split_count": 5},
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def water_case(
    *,
    session_id: str,
    date: str,
    slot: str,
    title: str,
    crew_id: str | None,
    athlete_ids: list[str],
    boat_id: str,
    boat_class: str,
    world_rowing_code: str,
    category: str,
    distance_m: int,
) -> dict:
    if "2 × 4 km" in title:
        repetitions, work_distance_m, minimum, maximum = 2, 4_000, 20, 20
    elif "6 × 1 km" in title:
        repetitions, work_distance_m, minimum, maximum = 6, 1_000, 20, 20
    elif "4 × 2 km" in title:
        repetitions, work_distance_m, minimum, maximum = 4, 2_000, 20, 22
    elif "Rate ladder" in title:
        repetitions, work_distance_m, minimum, maximum = 4, 1_000, 18, 24
    else:
        repetitions, work_distance_m, minimum, maximum = 1, distance_m, 18, 22
    midpoint = float((minimum + maximum) / 2)
    return {
        "title": title,
        "date": date,
        "start_hour": START_HOUR[slot],
        "crew_id": crew_id,
        "boat_id": boat_id,
        "boat_class": boat_class,
        "world_rowing_code": world_rowing_code,
        "crew_category": category,
        "athlete_ids": athlete_ids,
        "repetitions": repetitions,
        "work_distance_m": work_distance_m,
        "target_min_spm": minimum,
        "target_max_spm": maximum,
        "work_spm": [midpoint] * repetitions,
        "recovery_s": [180.0] * max(repetitions - 1, 0),
        "recovery_min_s": 120,
        "recovery_max_s": 240,
        "zone": "B1/B3",
        "coach_language": title,
        "session_id": session_id,
    }


def session_entry(
    output_root: Path,
    *,
    session_id: str,
    modality: str,
    title: str,
    date: str,
    slot: str,
    athlete_ids: list[str],
    crew_id: str | None,
    boat_id: str | None,
    expected_route: str,
    case: dict | None = None,
    omit_plan: bool = False,
    omit_context: bool = False,
    agent_result_ref: str | None = None,
    training_role: str = "PRIMARY",
    association_status: str = "DIRECT_SESSION",
    erg_spec: dict | None = None,
) -> dict:
    directory = output_root / "sessions" / session_id
    sources: list[str] = []
    if modality.startswith("WATER"):
        assert case is not None
        if not omit_plan:
            plan = build_plan(session_id, case)
            if crew_id is None:
                plan["athlete_scope"] = {"kind": "INDIVIDUAL", "ids": athlete_ids}
            plan["source"]["source_ref"] = "scripts/generate_demo_club_batch.py"
            write_json(directory / "plan.json", plan)
            sources.append("plan.json")
        if not omit_context:
            context = build_context(session_id, case)
            context["scenario_label"] = title
            write_json(directory / "context.json", context)
            sources.append("context.json")
        write_csv(directory / "speedcoach.csv", build_telemetry(case))
        sources.append("speedcoach.csv")
    else:
        assert erg_spec is not None
        workout_type = erg_spec["workout_type"]
        duration_s = erg_spec["duration_s"]
        target_distance_m = erg_spec["distance_m"]
        plan = {
            "schema_version": "wake.training_plan.v1",
            "plan_id": f"plan-{session_id}",
            "scheduled_date": date,
            "timezone": "America/Sao_Paulo",
            "source": {
                "kind": "SYNTHETIC",
                "provenance": "SYNTHETIC",
                "source_ref": "scripts/generate_demo_club_batch.py",
            },
            "modality": "INDOOR_ROWER",
            "athlete_scope": {"kind": "INDIVIDUAL", "ids": athlete_ids},
            "goal_id": "wake-demo-club-two-week-period",
            "coach_language": title,
            "blocks": [{
                "block_id": "erg-main",
                "kind": "WORK",
                "repetitions": 1,
                "distance_m": target_distance_m,
                "duration_s": duration_s if workout_type == "FIXED_TIME" else None,
                "stroke_rate": {"min_spm": max(0, int(erg_spec["average_spm"] - 1)), "max_spm": int(erg_spec["average_spm"] + 1)},
                "zone": "B1/B2",
                "zone_system": "STANDARD_ROWING_ZONES",
                "recovery": None,
                "equipment": [],
                "instructions": ["Record the individual Concept2 result."],
            }],
            "unresolved_terms": [],
            "notes": f"Real-informed synthetic {training_role.lower().replace('_', ' ')} indoor record.",
        }
        write_json(directory / "plan.json", plan)
        context = {
            "schema_version": "wake.synthetic_case_context.v1",
            "case_id": session_id,
            "investigation_request": "Preserve this alternate indoor training record.",
            "provided_sources": [{"source_id": f"concept2-{session_id}", "kind": "CONCEPT2", "path": "concept2.csv"}],
            "session_candidate": {"boat_id": None, "boat_class": None, "crew_id": None, "athlete_ids": athlete_ids},
            "human_confirmations": {"perceived_effort": None},
            "scenario_label": title,
            "input_notice": "All identities and exact outcomes are synthetic.",
        }
        write_json(directory / "context.json", context)
        split_count = erg_spec["split_count"]
        average_spm = erg_spec["average_spm"]
        average_watts = erg_spec["average_watts"]
        if workout_type == "FIXED_DISTANCE":
            split_distance = target_distance_m / split_count
            split_time = duration_s / split_count
            rows = [
                {
                    "transcription_provenance": "SYNTHETIC",
                    "workout_type": "FIXED_DISTANCE",
                    "row_kind": "SPLIT",
                    "row_index": str(index + 1),
                    "display_time_s": f"{split_time:.3f}",
                    "display_distance_m": f"{(index + 1) * split_distance:.3f}",
                    "pace_500m_s": f"{duration_s / target_distance_m * 500:.3f}",
                    "stroke_rate_spm": f"{average_spm + ((index % 3) - 1) * 0.5:.2f}",
                    "heart_rate_bpm": "",
                    "watts": f"{average_watts + ((index % 3) - 1) * 2:.1f}",
                }
                for index in range(split_count)
            ]
        elif workout_type == "FIXED_TIME":
            split_duration = duration_s / split_count
            split_distance = target_distance_m / split_count
            rows = []
            remaining_distance = float(target_distance_m)
            for index in range(split_count):
                displayed_distance = remaining_distance if index == split_count - 1 else round(split_distance, 3)
                remaining_distance -= displayed_distance
                rows.append({
                    "transcription_provenance": "SYNTHETIC",
                    "workout_type": "FIXED_TIME",
                    "row_kind": "SPLIT",
                    "row_index": str(index + 1),
                    "display_time_s": f"{(index + 1) * split_duration:.3f}",
                    "display_distance_m": f"{displayed_distance:.3f}",
                    "pace_500m_s": f"{duration_s / target_distance_m * 500:.3f}",
                    "stroke_rate_spm": f"{average_spm + (index % 2) * 0.5:.2f}",
                    "heart_rate_bpm": "",
                    "watts": f"{average_watts + (index % 2) * 2:.1f}",
                })
        else:
            rows = []
            row_index = 1
            work_durations = erg_spec.get("work_durations_s")
            if work_durations is None:
                repetitions = erg_spec.get("work_repetitions", 1)
                recovery_total = erg_spec.get("recovery_s", 0) * max(repetitions - 1, 0)
                work_durations = [(duration_s - recovery_total) / repetitions] * repetitions
            total_work_s = sum(work_durations)
            remaining_distance = float(target_distance_m)
            for work_index, work_duration in enumerate(work_durations):
                work_distance = remaining_distance if work_index == len(work_durations) - 1 else target_distance_m * work_duration / total_work_s
                remaining_distance -= work_distance
                rows.append({
                    "transcription_provenance": "SYNTHETIC",
                    "workout_type": "INTERVAL",
                    "row_kind": "WORK",
                    "row_index": str(row_index),
                    "display_time_s": f"{work_duration:.3f}",
                    "display_distance_m": f"{work_distance:.3f}",
                    "pace_500m_s": f"{work_duration / work_distance * 500:.3f}",
                    "stroke_rate_spm": f"{average_spm + ((work_index % 3) - 1) * 0.5:.2f}",
                    "heart_rate_bpm": "",
                    "watts": f"{average_watts + ((work_index % 3) - 1) * 2:.1f}",
                })
                row_index += 1
                if work_index < len(work_durations) - 1:
                    rows.append({
                        "transcription_provenance": "SYNTHETIC",
                        "workout_type": "INTERVAL",
                        "row_kind": "RECOVERY",
                        "row_index": str(row_index),
                        "display_time_s": str(erg_spec.get("recovery_s", 0)),
                        "display_distance_m": "0",
                        "pace_500m_s": "",
                        "stroke_rate_spm": "",
                        "heart_rate_bpm": "",
                        "watts": "",
                    })
                    row_index += 1
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / "concept2.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        sources.extend(["plan.json", "context.json", "concept2.csv"])

    return {
        "session_id": session_id,
        "date": date,
        "slot": slot,
        "title": title,
        "modality": modality,
        "athlete_ids": athlete_ids,
        "crew_id": crew_id,
        "boat_id": boat_id,
        "provenance": "REAL_INFORMED_SYNTHETIC",
        "expected_route": expected_route,
        "training_role": training_role,
        "association_status": association_status,
        "workout_type": erg_spec["workout_type"] if erg_spec else None,
        "source_sha256": {name: sha256(directory / name) for name in sorted(sources)},
        "agent_result_ref": agent_result_ref,
    }


def build_demo_club_batch(output_root: Path) -> dict:
    output_root.mkdir(parents=True, exist_ok=True)
    sessions = []
    for crew_id, schedule in SCHEDULES.items():
        boat_id, boat_class, world_code, category = CREW_META[crew_id]
        for index, (date, slot) in enumerate(schedule):
            key = f"{crew_id}:{date}"
            if key in UNAVAILABLE:
                continue
            session_id = VERIFIED_IDS.get(key, f"club-{crew_id.removeprefix('crew-')}-{date.replace('-', '')}-{slot.lower()}")
            title = PLAN_TITLES[world_code][index]
            distance_m = BASE_DISTANCE[world_code] + ((index % 3) - 1) * 500
            case = (
                dict(VERIFIED_CASES[session_id])
                if session_id in VERIFIED_CASES
                else water_case(
                    session_id=session_id,
                    date=date,
                    slot=slot,
                    title=title,
                    crew_id=crew_id,
                    athlete_ids=ATHLETES[crew_id],
                    boat_id=boat_id,
                    boat_class=boat_class,
                    world_rowing_code=world_code,
                    category=category,
                    distance_m=distance_m,
                )
            )
            expected_route = "RECONSTRUCTED_NO_MATERIAL_SIGNAL"
            agent_result_ref = None
            if session_id in VERIFIED_CASES:
                expected_route = "AGENT_VERIFIED"
                agent_result_ref = "evaluation/runs/demo-club-investigations-v1-20260830/run-manifest.json"
            elif key == "crew-4x-mixed-b:2026-08-27":
                expected_route = "SOURCE_REQUIRED"
            elif key == "crew-8x-women:2026-08-28":
                expected_route = "HUMAN_CONTEXT_REQUIRED"
            sessions.append(session_entry(
                output_root,
                session_id=session_id,
                modality="WATER_CREW",
                title=title,
                date=date,
                slot=slot,
                athlete_ids=ATHLETES[crew_id],
                crew_id=crew_id,
                boat_id=boat_id,
                expected_route=expected_route,
                case=case,
                omit_plan=expected_route == "SOURCE_REQUIRED",
                omit_context=expected_route == "HUMAN_CONTEXT_REQUIRED",
                agent_result_ref=agent_result_ref,
            ))

    water_alternatives = [
        ("activity-lucas-solo-20260824", "2026-08-24", "AM", "WATER_SOLO", "Individual water session after crew cancellation", ["athlete-lucas"], "boat-1x-spare", 8_000),
        ("activity-camila-solo-20260827", "2026-08-27", "AM", "WATER_SOLO", "Individual water session after crew cancellation", ["athlete-camila"], "boat-1x-spare", 7_000),
        ("activity-felipe-solo-20260826", "2026-08-26", "EVENING", "WATER_SOLO", "Individual water session after 8x cancellation", ["athlete-felipe"], "boat-1x-spare", 9_000),
    ]
    for session_id, date, slot, modality, title, athlete_ids, boat_id, distance_m in water_alternatives:
        case = water_case(
            session_id=session_id,
            date=date,
            slot=slot,
            title=title,
            crew_id=None,
            athlete_ids=athlete_ids,
            boat_id=boat_id,
            boat_class="SINGLE_SCULL",
            world_rowing_code="1x",
            category="MIXED",
            distance_m=distance_m,
        )
        sessions.append(session_entry(
            output_root,
            session_id=session_id,
            modality=modality,
            title=title,
            date=date,
            slot=slot,
            athlete_ids=athlete_ids,
            crew_id=None,
            boat_id=boat_id,
            expected_route="RECONSTRUCTED_ALTERNATIVE",
            case=case,
            training_role="ALTERNATIVE",
            association_status="PLAN_CONFIRMED",
        ))

    for spec in ERG_SPECS:
        sessions.append(session_entry(
            output_root,
            session_id=spec["session_id"],
            modality="ERG",
            title=spec["title"],
            date=spec["date"],
            slot=spec["slot"],
            athlete_ids=[spec["athlete_id"]],
            crew_id=None,
            boat_id=None,
            expected_route="RECONSTRUCTED_ALTERNATIVE",
            training_role=spec["training_role"],
            association_status=spec["association_status"],
            erg_spec=spec,
        ))

    sessions.sort(key=lambda item: (item["date"], item["slot"], item["session_id"]))
    manifest = {
        "schema_version": "wake.demo_club_batch_manifest.v1",
        "generator": "scripts/generate_demo_club_batch.py",
        "generator_version": GENERATOR_VERSION,
        "period": {"start": "2026-08-17", "end": "2026-08-28"},
        "sessions": sessions,
        "boundary": (
            "All people, exact sessions, telemetry, and outcomes are synthetic. "
            "Formats, workout shapes, and operational failure modes are informed by supplied rowing material."
        ),
    }
    write_json(output_root / "manifest.json", manifest)
    (output_root / "README.md").write_text(
        "# Demo-club two-week batch\n\n"
        "Fifty-two independent real-informed synthetic activity records. Water sessions "
        "carry plan, SpeedCoach-shaped telemetry, and context when available; fourteen "
        "individual indoor sessions carry synthetic Concept2 PM5 transcription-format records. "
        "Every source is hashed per session.\n\n"
        "The Concept2 adapter distinguishes fixed-distance, fixed-time, and interval "
        "screen semantics and never assigns one PM5 result to multiple athletes. "
        "Automatic photo OCR and native ErgData ingestion are not "
        "implemented or implied.\n\n"
        "The batch is designed for mass submission with per-session isolation. It "
        "does not place multiple sessions in one model prompt. Agent execution is "
        "preserved only for the two separately authorized candidates; longitudinal "
        "synthesis has not run.\n\n"
        "Regenerate and verify without a model call:\n\n"
        "```bash\n"
        "uv run python scripts/generate_demo_club_batch.py\n"
        "uv run python scripts/verify_demo_club_batch.py\n"
        "```\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data/demo-club-batch"))
    args = parser.parse_args()
    manifest = build_demo_club_batch(args.output)
    print(f"Generated {len(manifest['sessions'])} independent activity records in {args.output}")


if __name__ == "__main__":
    main()
