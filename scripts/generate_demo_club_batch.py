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


GENERATOR_VERSION = "1.1"

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
            "athlete_scope": {"kind": "SQUAD", "ids": athlete_ids},
            "goal_id": "wake-demo-club-two-week-period",
            "coach_language": title,
            "blocks": [{
                "block_id": "erg-main",
                "kind": "WORK",
                "repetitions": 1,
                "distance_m": 10_000 if len(athlete_ids) <= 2 else 12_000,
                "duration_s": None,
                "stroke_rate": {"min_spm": 20, "max_spm": 24},
                "zone": "B1/B2",
                "zone_system": "STANDARD_ROWING_ZONES",
                "recovery": None,
                "equipment": [],
                "instructions": ["Record the individual Concept2 result."],
            }],
            "unresolved_terms": [],
            "notes": "Real-informed synthetic indoor alternative.",
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
        target_distance_m = plan["blocks"][0]["distance_m"]
        if target_distance_m == 10_000:
            rows = [
                {
                    "transcription_provenance": "SYNTHETIC",
                    "workout_type": "FIXED_DISTANCE",
                    "row_kind": "SPLIT",
                    "row_index": str(index + 1),
                    "display_time_s": str(480 + index * 5),
                    "display_distance_m": str((index + 1) * 2_000),
                    "pace_500m_s": str(120 + index),
                    "stroke_rate_spm": str(22 + index % 2),
                    "heart_rate_bpm": "",
                    "watts": str(195 - index * 3),
                }
                for index in range(5)
            ]
        else:
            rows = []
            row_index = 1
            for work_index in range(6):
                rows.append({
                    "transcription_provenance": "SYNTHETIC",
                    "workout_type": "INTERVAL",
                    "row_kind": "WORK",
                    "row_index": str(row_index),
                    "display_time_s": str(485 + work_index * 4),
                    "display_distance_m": "2000",
                    "pace_500m_s": str(121 + work_index),
                    "stroke_rate_spm": str(21 + work_index % 3),
                    "heart_rate_bpm": "",
                    "watts": str(192 - work_index * 2),
                })
                row_index += 1
                if work_index < 5:
                    rows.append({
                        "transcription_provenance": "SYNTHETIC",
                        "workout_type": "INTERVAL",
                        "row_kind": "RECOVERY",
                        "row_index": str(row_index),
                        "display_time_s": "120",
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

    alternatives = [
        ("activity-lucas-solo-20260824", "2026-08-24", "AM", "WATER_SOLO", "Individual water session after crew cancellation", ["athlete-lucas"], "boat-1x-spare", 8_000),
        ("activity-gaia-erg-20260827", "2026-08-27", "AM", "ERG", "Ergometer alternative after crew cancellation", ["athlete-marina", "athlete-helena"], None, 10_000),
        ("activity-camila-solo-20260827", "2026-08-27", "AM", "WATER_SOLO", "Individual water session after crew cancellation", ["athlete-camila"], "boat-1x-spare", 7_000),
        ("activity-north-erg-20260826", "2026-08-26", "EVENING", "ERG", "Squad ergometer alternative after 8x cancellation", ATHLETES["crew-8x-men"][:6], None, 12_000),
        ("activity-felipe-solo-20260826", "2026-08-26", "EVENING", "WATER_SOLO", "Individual water session after 8x cancellation", ["athlete-felipe"], "boat-1x-spare", 9_000),
    ]
    for session_id, date, slot, modality, title, athlete_ids, boat_id, distance_m in alternatives:
        case = None
        if modality == "WATER_SOLO":
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
        "Forty independent real-informed synthetic activity records. Water sessions "
        "carry plan, SpeedCoach-shaped telemetry, and context when available; two "
        "indoor alternatives carry synthetic Concept2 PM5 transcription-format records. "
        "Every source is hashed per session.\n\n"
        "The Concept2 adapter distinguishes fixed-distance, fixed-time, and interval "
        "screen semantics. Automatic photo OCR and native ErgData ingestion are not "
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
