#!/usr/bin/env python3
"""Assemble uploaded WAKE evidence into a compact agent-ready case summary.

The assembler is deterministic and evidence-only. It reconciles source quality,
route similarity, clocks, distance, and environmental context without running an
LLM or treating an evaluation answer key as product input.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
import statistics
from collections import defaultdict
from datetime import datetime


SUMMARY_VERSION = "wake.case_summary.v1"
ASSEMBLER_VERSION = "scripts/bundle_assembler.py@1.2"
DOMAIN_KNOWLEDGE = [
    {
        "term": "voga",
        "meaning": "Target stroke rate in strokes per minute (SPM).",
        "status": "HUMAN_CONFIRMED",
        "limitations": [],
    },
    {
        "term": "B0-B7 and E1-E7",
        "meaning": "Standardized rowing training-zone codes.",
        "status": "HUMAN_CONFIRMED",
        "limitations": [
            "Exact effort, physiological, heart-rate, lactate, and power boundaries are not supplied."
        ],
    },
]


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _rows(content: bytes) -> list[dict[str, str]]:
    parsed = list(csv.DictReader(io.StringIO(content.decode("utf-8"))))
    if not parsed:
        raise ValueError("Normalized telemetry contains no rows.")
    return parsed


def _positive_numbers(rows: list[dict[str, str]], key: str) -> list[float]:
    values = []
    for row in rows:
        raw = (row.get(key) or "").strip()
        if raw and float(raw) > 0:
            values.append(float(raw))
    return values


def _gps_route(rows: list[dict[str, str]]) -> list[tuple[float, float]]:
    route = []
    for row in rows:
        latitude = (row.get("latitude") or "").strip()
        longitude = (row.get("longitude") or "").strip()
        if latitude and longitude:
            route.append((float(latitude), float(longitude)))
    return route


def _sample_route(
    route: list[tuple[float, float]], maximum_points: int = 1000
) -> list[tuple[float, float]]:
    if len(route) <= maximum_points:
        return route
    step = math.ceil(len(route) / maximum_points)
    sampled = route[::step]
    if sampled[-1] != route[-1]:
        sampled.append(route[-1])
    return sampled


def _haversine_m(
    first: tuple[float, float], second: tuple[float, float]
) -> float:
    radius_m = 6_371_000
    lat_1, lon_1 = map(math.radians, first)
    lat_2, lon_2 = map(math.radians, second)
    delta_lat = lat_2 - lat_1
    delta_lon = lon_2 - lon_1
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_1) * math.cos(lat_2) * math.sin(delta_lon / 2) ** 2
    )
    return radius_m * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _bearing_deg(
    first: tuple[float, float], second: tuple[float, float]
) -> float:
    lat_1, lon_1 = map(math.radians, first)
    lat_2, lon_2 = map(math.radians, second)
    delta_lon = lon_2 - lon_1
    east = math.sin(delta_lon) * math.cos(lat_2)
    north = (
        math.cos(lat_1) * math.sin(lat_2)
        - math.sin(lat_1) * math.cos(lat_2) * math.cos(delta_lon)
    )
    return math.degrees(math.atan2(east, north)) % 360


def _derive_route_heading(rows: list[dict[str, str]]) -> dict | None:
    """Return a representative GPS heading only for a directionally consistent track."""
    route = _gps_route(rows)
    bearings = [
        _bearing_deg(first, second)
        for first, second in zip(route, route[1:])
        if _haversine_m(first, second) >= 5
    ]
    if not bearings:
        return None
    east = statistics.mean(math.sin(math.radians(value)) for value in bearings)
    north = statistics.mean(math.cos(math.radians(value)) for value in bearings)
    consistency = math.hypot(east, north)
    if consistency < 0.75:
        return None
    return {
        "heading_deg": round(math.degrees(math.atan2(east, north)) % 360, 1) % 360,
        "source": "SPEEDCOACH_GPS_DERIVED",
        "directional_consistency": round(consistency, 3),
        "segment_count": len(bearings),
    }


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _nearest_stats(
    route: list[tuple[float, float]], reference: list[tuple[float, float]]
) -> dict:
    sampled_route = _sample_route(route)
    sampled_reference = _sample_route(reference)
    distances = [
        min(_haversine_m(point, candidate) for candidate in sampled_reference)
        for point in sampled_route
    ]
    return {
        "median_m": round(statistics.median(distances), 3),
        "p95_m": round(_percentile(distances, 0.95), 3),
        "max_m": round(max(distances), 3),
        "sampled_points": len(sampled_route),
    }


def _aggregate_windows(rows: list[dict[str, str]], window_s: int = 30) -> list[dict]:
    buckets: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        buckets[int(float(row["elapsed_s"]) // window_s)].append(row)
    windows = []
    for bucket, items in sorted(buckets.items()):
        distances = [float(item["distance_m"]) for item in items]
        speeds = [float(item["speed_m_s"]) for item in items]
        spm = _positive_numbers(items, "stroke_rate_spm")
        windows.append(
            {
                "start_offset_s": bucket * window_s,
                "end_offset_s": (bucket + 1) * window_s,
                "distance_start_m": round(min(distances), 1),
                "distance_end_m": round(max(distances), 1),
                "average_speed_m_s": round(statistics.mean(speeds), 3),
                "average_spm": round(statistics.mean(spm), 2) if spm else None,
                "samples": len(items),
            }
        )
    return windows


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _clock_offset(first: str | None, second: str | None) -> float | None:
    speedcoach = _parse_timestamp(first)
    mobile = _parse_timestamp(second)
    if speedcoach is None or mobile is None:
        return None
    speedcoach_aware = speedcoach.utcoffset() is not None
    mobile_aware = mobile.utcoffset() is not None
    if speedcoach_aware != mobile_aware:
        return None
    return round((mobile - speedcoach).total_seconds(), 3)


def _context_source(context: dict, kind: str) -> dict:
    aliases = {"PLAN": "TRAINING_PLAN"}
    expected = aliases.get(kind, kind)
    return next(
        (
            source
            for source in context.get("provided_sources", [])
            if source.get("kind") == expected
        ),
        {},
    )


def _source_summary(source: dict, context: dict) -> tuple[dict, list[dict[str, str]]]:
    rows = _rows(source["normalized_csv"])
    report = source["normalization"]
    kind = source["kind"]
    declared = _context_source(context, kind)
    evidence_ref = source["evidence_ref"]
    spm = _positive_numbers(rows, "stroke_rate_spm")
    route = _gps_route(rows)
    route_heading = _derive_route_heading(rows) if kind == "SPEEDCOACH" else None
    start_time = next((row["timestamp"] for row in rows if row["timestamp"]), None)
    metrics = {
        "start_time": start_time,
        "duration_s": round(
            max(float(row["elapsed_s"]) for row in rows)
            - min(float(row["elapsed_s"]) for row in rows),
            3,
        ),
        "end_distance_m": round(max(float(row["distance_m"]) for row in rows), 3),
        "average_positive_spm": round(statistics.mean(spm), 2) if spm else None,
        "positive_spm_rows": len(spm),
        "route_points": len(route),
        "route_heading_deg": (
            route_heading["heading_deg"] if route_heading else None
        ),
        "route_heading_source": (
            route_heading["source"] if route_heading else None
        ),
        "route_heading_directional_consistency": (
            route_heading["directional_consistency"] if route_heading else None
        ),
        "rejected_rows": report.get("rejected_row_count", 0),
        "input_format": report["input_format"],
        "normalized_sha256": report["normalized_sha256"],
    }
    return (
        {
            "source_id": source.get(
                "source_id", declared.get("source_id", kind.lower())
            ),
            "kind": kind,
            "evidence_refs": [evidence_ref],
            "metrics": metrics,
            "quality_flags": list(report["quality_flags"]),
            "time_series_windows": _aggregate_windows(rows) if kind == "SPEEDCOACH" else [],
        },
        rows,
    )


def _environment_summary(
    environment: dict | None,
    context: dict,
    observed_route_heading: dict | None = None,
) -> dict | None:
    if not environment:
        return None
    heading = context.get("session_candidate", {}).get("route_heading_deg")
    heading_source = "SESSION_CONTEXT" if heading is not None else None
    if heading is None and observed_route_heading is not None:
        heading = observed_route_heading["heading_deg"]
        heading_source = observed_route_heading["source"]
    samples = environment.get("samples", [])
    if not samples:
        return None
    session_window = environment.get("session_window") or {}
    start = _parse_timestamp(session_window.get("start_utc")) or _parse_timestamp(
        samples[0].get("timestamp")
    )
    windows = []
    for index, sample in enumerate(samples):
        timestamp = _parse_timestamp(sample.get("timestamp"))
        elapsed_s = (
            round((timestamp - start).total_seconds(), 3)
            if timestamp is not None and start is not None
            else float(index)
        )
        window = {
            "elapsed_s": elapsed_s,
            "wind_speed_m_s": sample["wind_speed_m_s"],
            "wind_direction_from_deg": sample["wind_direction_deg"],
            "gust_speed_m_s": sample.get("gust_speed_m_s"),
            "temperature_c": sample.get("temperature_c"),
        }
        if "relative_humidity_pct" in sample:
            window["relative_humidity_pct"] = sample.get(
                "relative_humidity_pct"
            )
        if heading is not None:
            relative_direction = math.radians(
                float(sample["wind_direction_deg"]) - float(heading)
            )
            window["effective_headwind_m_s"] = round(
                float(sample["wind_speed_m_s"]) * math.cos(relative_direction),
                3,
            )
            window["effective_crosswind_m_s"] = round(
                float(sample["wind_speed_m_s"]) * math.sin(relative_direction),
                3,
            )
        windows.append(window)
    if heading_source == "SPEEDCOACH_GPS_DERIVED":
        method = (
            "Effective headwind and signed crosswind project meteorological wind-from "
            "direction onto a representative heading derived from the directionally "
            "consistent SpeedCoach GPS track; time alignment supports association but "
            "does not establish causation."
        )
    elif heading is not None:
        method = (
            "Effective headwind and signed crosswind project meteorological wind-from "
            "direction onto the known boat heading; time alignment supports association "
            "but does not establish causation."
        )
    else:
        method = "Wind is retained without boat-relative projection because route heading is unknown."
    limitations = list(environment.get("limitations", []))
    if heading_source == "SPEEDCOACH_GPS_DERIVED":
        limitations.append(
            "Representative boat heading is derived from a directionally consistent GPS track and is not independently confirmed; turning or out-and-back routes require segment-level projection."
        )
    return {
        "schema_version": environment.get("schema_version"),
        "timeline_id": environment["timeline_id"],
        "source": environment["source"],
        "direction_convention": environment["direction_convention"],
        "units": environment.get("units"),
        "session_window": environment.get("session_window"),
        "route_heading_deg": heading,
        "route_heading_source": heading_source,
        "method": method,
        "time_series_windows": windows,
        "limitations": limitations,
    }


def _known_context(context: dict) -> dict:
    excluded = {
        "schema_version",
        "case_id",
        "investigation_request",
        "provided_sources",
    }
    return {key: value for key, value in context.items() if key not in excluded}


def _default_context(plan: dict) -> dict:
    """Create neutral process context without inventing rowing facts."""
    plan_id = plan["plan_id"]
    return {
        "schema_version": "wake.generated_session_context.v1",
        "case_id": f"uploaded-{plan_id}",
        "investigation_request": (
            "Compare the planned and performed session and state what remains unknown."
        ),
        "provided_sources": [],
        "session_candidate": {},
        "human_confirmations": {},
        "input_notice": (
            "No session context was supplied; boat, crew, goal, and human observations "
            "remain unknown."
        ),
    }


def _human_evidence_gaps(context: dict, plan: dict | None) -> list[str]:
    confirmations = context.get("human_confirmations", {})
    gaps = []
    equipment = {
        item
        for block in (plan or {}).get("blocks", [])
        for item in block.get("equipment", [])
    }
    if "RESISTANCE_BAND" in equipment and confirmations.get("resistance_band_used") is None:
        gaps.append("Telemetry cannot confirm whether the prescribed resistance band was used.")
    if confirmations.get("coach_observed_technique") is None:
        gaps.append("No coach technique or crew-synchronization observation is supplied.")
    if confirmations.get("perceived_effort") is None:
        gaps.append("No perceived effort report is supplied.")
    return gaps


def assemble_case_summary(
    *,
    plan: dict | None,
    context: dict | None,
    environment: dict | None,
    telemetry_sources: list[dict],
    input_hashes: dict[str, str],
) -> dict:
    """Return a deterministic compact summary from validated source values."""
    if plan is None:
        raise ValueError("Summary assembly requires a training plan.")
    context_supplied = context is not None
    context = context or _default_context(plan)
    by_kind = {source["kind"]: source for source in telemetry_sources}
    if (
        "SPEEDCOACH" not in by_kind
        or not set(by_kind).issubset({"SPEEDCOACH", "MOBILE"})
        or len(by_kind) != len(telemetry_sources)
    ):
        raise ValueError(
            "Summary assembly requires one SPEEDCOACH source and accepts one optional MOBILE source."
        )

    summaries = {}
    source_rows = {}
    for kind in ("SPEEDCOACH", "MOBILE"):
        if kind not in by_kind:
            continue
        summaries[kind], source_rows[kind] = _source_summary(by_kind[kind], context)

    speedcoach = summaries["SPEEDCOACH"]
    findings = []
    evidence_gaps = _human_evidence_gaps(context, plan)
    if not context_supplied:
        evidence_gaps.append(
            "Session context is not supplied; boat, crew, goal, and human observations remain unknown."
        )
    mobile = summaries.get("MOBILE")
    if mobile is None:
        evidence_gaps.append(
            "Mobile telemetry is not supplied; route and distance cannot be independently corroborated."
        )
    else:
        refs = [speedcoach["evidence_refs"][0], mobile["evidence_refs"][0]]
        offset = _clock_offset(
            speedcoach["metrics"]["start_time"], mobile["metrics"]["start_time"]
        )
        if offset is not None:
            findings.append(
                {
                    "finding_id": "mobile-clock-offset",
                    "type": "CLOCK_OFFSET",
                    "summary": "The mobile clock start differs from the SpeedCoach clock start.",
                    "values": {"mobile_from_speedcoach_s": offset},
                    "evidence_refs": refs,
                }
            )
        else:
            evidence_gaps.append(
                "Clock offset cannot be computed safely because timestamp timezone context is missing or incompatible."
            )

        speedcoach_distance = speedcoach["metrics"]["end_distance_m"]
        mobile_distance = mobile["metrics"]["end_distance_m"]
        if speedcoach_distance > 0:
            ratio = mobile_distance / speedcoach_distance
            difference_percent = round((ratio - 1) * 100, 3)
            findings.append(
                {
                    "finding_id": "distance-bias",
                    "type": "DISTANCE_CONFLICT",
                    "summary": "The two cumulative distance sources end at different values.",
                    "values": {
                        "mobile_to_speedcoach_ratio": round(ratio, 5),
                        "difference_percent": difference_percent,
                    },
                    "evidence_refs": refs,
                }
            )
            if abs(difference_percent) >= 1:
                mobile["quality_flags"] = list(
                    dict.fromkeys([*mobile["quality_flags"], "DISTANCE_BIAS_PRESENT"])
                )

        routes = {kind: _gps_route(rows) for kind, rows in source_rows.items()}
        if routes["SPEEDCOACH"] and routes["MOBILE"]:
            findings.append(
                {
                    "finding_id": "route-overlap",
                    "type": "ROUTE_OVERLAP",
                    "summary": "The two GPS routes are compared spatially in both directions.",
                    "values": {
                        "speedcoach_to_mobile": _nearest_stats(
                            routes["SPEEDCOACH"], routes["MOBILE"]
                        ),
                        "mobile_to_speedcoach": _nearest_stats(
                            routes["MOBILE"], routes["SPEEDCOACH"]
                        ),
                    },
                    "evidence_refs": refs,
                }
            )
        else:
            evidence_gaps.append(
                "Route overlap cannot be assessed because one GPS route is absent."
            )

    if environment is None:
        evidence_gaps.append(
            "Environmental timeline is not supplied; condition-aware interpretation is unavailable."
        )

    case_id = context["case_id"]
    return {
        "schema_version": SUMMARY_VERSION,
        "summary_id": f"uploaded-summary-v1-{case_id}",
        "case_id": case_id,
        "generated_by": ASSEMBLER_VERSION,
        "input_hashes": dict(sorted(input_hashes.items())),
        "investigation_request": context["investigation_request"],
        "domain_knowledge": DOMAIN_KNOWLEDGE,
        "known_context": _known_context(context),
        "plan": plan,
        "sources": [
            summaries[kind]
            for kind in ("SPEEDCOACH", "MOBILE")
            if kind in summaries
        ],
        "cross_source_findings": findings,
        "environment": _environment_summary(
            environment,
            context,
            {
                "heading_deg": speedcoach["metrics"]["route_heading_deg"],
                "source": speedcoach["metrics"]["route_heading_source"],
            }
            if speedcoach["metrics"]["route_heading_deg"] is not None
            else None,
        ),
        "evidence_gaps": evidence_gaps,
    }
