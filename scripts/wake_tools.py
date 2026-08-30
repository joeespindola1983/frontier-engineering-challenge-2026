#!/usr/bin/env python3
"""Deterministic, ground-truth-free investigation tools for the WAKE agent."""

from __future__ import annotations

import copy
import csv
import statistics
from datetime import datetime
from pathlib import Path


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "assess_source_trust",
        "description": (
            "Select or reject evidence independently for stroke rate, distance, and "
            "route. Returns selected source IDs, rejected sources, reasons, confidence, "
            "and evidence_refs. It never averages conflicting sources."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "assess_session_alignment",
        "description": (
            "Assess whether supplied recordings describe the same outing using clock "
            "offset and bidirectional route-overlap findings. Returns a decision, "
            "confidence, values, limitations, and evidence_refs."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "reconstruct_plan_execution",
        "description": (
            "When a plan exists, reconstruct work and recovery intervals from the "
            "approved input telemetry, compare work SPM with prescribed ranges, and "
            "state whether equipment use is confirmed. Returns INSUFFICIENT when a "
            "plan or compatible telemetry is unavailable."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "analyze_environment",
        "description": (
            "Summarize time-aligned effective headwind evidence and whether conditions "
            "changed. Reports association only and explicitly does not establish "
            "causation or athlete improvement."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


TOOL_DEFINITIONS_V2 = copy.deepcopy(TOOL_DEFINITIONS)
for definition in TOOL_DEFINITIONS_V2:
    if definition["name"] == "reconstruct_plan_execution":
        definition["description"] = (
            "When a plan exists, reconstruct work and recovery intervals from the "
            "approved input telemetry, compare work SPM and recovery duration with "
            "prescribed ranges, expose missing planned work intervals, and state "
            "whether equipment use is confirmed. Per-segment distances are "
            "boundary-derived from SPM classification and cannot establish total "
            "completed distance or a prescribed-distance shortfall. Returns "
            "INSUFFICIENT when a plan or compatible telemetry is unavailable."
        )
    if definition["name"] == "analyze_environment":
        definition["description"] = (
            "Summarize time-aligned headwind, tailwind, crosswind, wind-speed, and "
            "gust evidence. Classify the observed condition profile while reporting "
            "association only; environmental evidence cannot establish causation or "
            "athlete improvement."
        )


def tool_definitions(contract_version: str) -> list[dict]:
    if contract_version == "v1":
        return TOOL_DEFINITIONS
    if contract_version == "v2":
        return TOOL_DEFINITIONS_V2
    raise ValueError(f"Unsupported tool contract version: {contract_version}")


def source_has_flag(source: dict, flag: str) -> bool:
    return flag in source.get("quality_flags", [])


def assess_source_trust(summary: dict) -> dict:
    sources = summary["sources"]
    speedcoach = [
        source for source in sources
        if source_has_flag(source, "SPM_PRESENT")
        or source.get("kind") == "SPEEDCOACH"
    ]
    usable_spm = [source for source in sources if source_has_flag(source, "SPM_PRESENT")]
    rejected_spm = [
        source for source in sources
        if source_has_flag(source, "SPM_ALL_ZERO")
        or source_has_flag(source, "RAW_SPM_ABSENT")
    ]
    selected_spm = usable_spm[0] if usable_spm else None

    rejected_distance = [
        source for source in sources
        if source_has_flag(source, "DISTANCE_BIAS_PRESENT")
        or source_has_flag(source, "RAW_AND_SUMMARY_DISTANCE_CONFLICT")
    ]
    clean_distance = [source for source in speedcoach if source not in rejected_distance]
    selected_distance = clean_distance[0] if clean_distance else None

    gps_sources = [source for source in sources if source_has_flag(source, "GPS_PRESENT")]
    selected_route = speedcoach[0] if speedcoach else (gps_sources[0] if gps_sources else None)
    route_corrob = [
        source["source_id"] for source in gps_sources
        if selected_route and source["source_id"] != selected_route["source_id"]
    ]

    return {
        "status": "COMPLETED",
        "metrics": {
            "stroke_rate_spm": {
                "selected_source_id": selected_spm["source_id"] if selected_spm else None,
                "rejected_source_ids": [source["source_id"] for source in rejected_spm],
                "confidence": "HIGH" if selected_spm else "NONE",
                "reasons": [
                    *(
                        [f"{selected_spm['source_id']}: SPM_PRESENT"]
                        if selected_spm else ["No source contains usable SPM."]
                    ),
                    *[
                        f"{source['source_id']}: "
                        + ", ".join(
                            flag for flag in source["quality_flags"]
                            if flag in {"SPM_ALL_ZERO", "RAW_SPM_ABSENT"}
                        )
                        for source in rejected_spm
                    ],
                ],
                "evidence_refs": [
                    ref
                    for source in ([selected_spm] if selected_spm else []) + rejected_spm
                    for ref in source["evidence_refs"]
                ],
            },
            "distance_m": {
                "selected_source_id": (
                    selected_distance["source_id"] if selected_distance else None
                ),
                "rejected_source_ids": [
                    source["source_id"] for source in rejected_distance
                ],
                "confidence": "HIGH" if selected_distance else "LOW",
                "reasons": [
                    *(
                        [f"{selected_distance['source_id']}: no supplied distance conflict flag"]
                        if selected_distance else ["No conflict-free distance source."]
                    ),
                    *[
                        f"{source['source_id']}: distance conflict or bias flag"
                        for source in rejected_distance
                    ],
                ],
                "evidence_refs": [
                    ref
                    for source in ([selected_distance] if selected_distance else [])
                    + rejected_distance
                    for ref in source["evidence_refs"]
                ],
            },
            "route": {
                "selected_source_id": selected_route["source_id"] if selected_route else None,
                "corroborating_source_ids": route_corrob,
                "confidence": (
                    "HIGH" if selected_route and route_corrob
                    else "MEDIUM" if selected_route
                    else "NONE"
                ),
                "reasons": [
                    "Multiple GPS sources corroborate the selected route."
                    if selected_route and route_corrob
                    else "The route is observed by a single GPS source without independent corroboration."
                    if selected_route
                    else "No source contains usable GPS route evidence."
                ],
                "evidence_refs": [
                    ref for source in gps_sources for ref in source["evidence_refs"]
                ],
            },
        },
    }


def nested_numeric_values(value: object, key: str) -> list[float]:
    found: list[float] = []
    if isinstance(value, dict):
        for current_key, current_value in value.items():
            if current_key == key and isinstance(current_value, (int, float)):
                found.append(float(current_value))
            else:
                found.extend(nested_numeric_values(current_value, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(nested_numeric_values(item, key))
    return found


def numeric_leaf_values(value: object) -> list[float]:
    if isinstance(value, dict):
        return [
            number
            for current_value in value.values()
            for number in numeric_leaf_values(current_value)
        ]
    if isinstance(value, list):
        return [
            number for item in value for number in numeric_leaf_values(item)
        ]
    if isinstance(value, (int, float)):
        return [float(value)]
    return []


def assess_session_alignment(summary: dict) -> dict:
    clock_findings = [
        finding for finding in summary["cross_source_findings"]
        if finding["type"] == "CLOCK_OFFSET"
    ]
    route_findings = [
        finding for finding in summary["cross_source_findings"]
        if finding["type"] == "ROUTE_OVERLAP"
    ]
    offsets = [
        abs(value)
        for finding in clock_findings
        for value in numeric_leaf_values(finding["values"])
    ]
    p95_values = [
        value
        for finding in route_findings
        for value in nested_numeric_values(finding["values"], "p95_m")
    ]
    largest_p95 = max(p95_values, default=float("inf"))
    largest_offset = max(offsets, default=0.0)
    if route_findings and largest_p95 < 25:
        decision = "MATCH"
        confidence = "HIGH" if largest_p95 < 5 else "MEDIUM"
    elif route_findings:
        decision = "INSUFFICIENT"
        confidence = "LOW"
    else:
        decision = "INSUFFICIENT"
        confidence = "LOW"
    return {
        "status": "COMPLETED",
        "decision": decision,
        "confidence": confidence,
        "largest_clock_offset_s": round(largest_offset, 3),
        "largest_route_p95_m": round(largest_p95, 3) if p95_values else None,
        "limitations": [
            "Clock disagreement is preserved and its cause is unknown; route evidence, not clock equality, supports the decision."
        ],
        "evidence_refs": sorted(
            {
                ref
                for finding in clock_findings + route_findings
                for ref in finding["evidence_refs"]
            }
        ),
    }


def read_normalized_telemetry(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"elapsed_s", "distance_m", "speed_m_s", "stroke_rate_spm"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(f"Unsupported telemetry columns in {path.name}")
    return rows


def expanded_spm_targets(plan: dict) -> list[dict]:
    targets: list[dict] = []
    for block in plan["blocks"]:
        if block["kind"] != "WORK":
            continue
        for _ in range(block["repetitions"]):
            targets.append(block["stroke_rate"])
    return targets


def expanded_recovery_targets(plan: dict) -> list[dict]:
    work_blocks = [
        block
        for block in plan["blocks"]
        if block["kind"] == "WORK"
        for _ in range(block["repetitions"])
    ]
    return [block.get("recovery") or {} for block in work_blocks[:-1]]


def reconstruct_plan_execution(
    summary: dict,
    input_dir: Path,
    *,
    contract_version: str = "v1",
) -> dict:
    plan = summary.get("plan")
    if not plan:
        return {
            "status": "INSUFFICIENT",
            "reason": "No planned workout is supplied.",
            "segments": [],
            "equipment_confirmation": "UNKNOWN",
            "evidence_refs": [],
        }
    telemetry_path = input_dir / "speedcoach.csv"
    if not telemetry_path.is_file():
        return {
            "status": "INSUFFICIENT",
            "reason": "No compatible normalized SpeedCoach telemetry is supplied.",
            "segments": [],
            "equipment_confirmation": "UNKNOWN",
            "evidence_refs": [],
        }
    rows = read_normalized_telemetry(telemetry_path)
    targets = expanded_spm_targets(plan)
    recovery_targets = expanded_recovery_targets(plan)
    minimum_target = min(target["min_spm"] for target in targets)
    work_threshold = minimum_target - (2 if contract_version == "v2" else 1)

    groups: list[tuple[str, list[dict[str, str]]]] = []
    for row in rows:
        spm = float(row["stroke_rate_spm"])
        if spm <= 0:
            continue
        kind = "WORK" if spm >= work_threshold else "RECOVERY"
        if not groups or groups[-1][0] != kind:
            groups.append((kind, []))
        groups[-1][1].append(row)

    segments = []
    work_index = 0
    recovery_index = 0
    plan_deviations = []
    previous_group_end_s = None
    for kind, group_rows in groups:
        spm_values = [float(row["stroke_rate_spm"]) for row in group_rows]
        speed_values = [float(row["speed_m_s"]) for row in group_rows]
        group_start_s = float(group_rows[0]["elapsed_s"])
        group_end_s = float(group_rows[-1]["elapsed_s"])
        if kind == "WORK":
            work_index += 1
            segment_id = f"work-{work_index:02d}"
            target = targets[work_index - 1] if work_index <= len(targets) else None
            average_spm = statistics.mean(spm_values)
            compliance = (
                "COMPLIANT"
                if target
                and target["min_spm"] <= average_spm <= target["max_spm"]
                else "DEVIATION"
            )
        else:
            recovery_index += 1
            segment_id = f"recovery-{recovery_index:02d}"
            target = None
            average_spm = statistics.mean(spm_values)
            recovery_target = (
                recovery_targets[recovery_index - 1]
                if recovery_index <= len(recovery_targets)
                else {}
            )
            duration_s = group_end_s - (
                previous_group_end_s
                if previous_group_end_s is not None
                else group_start_s
            )
            minimum_s = recovery_target.get("min_s")
            maximum_s = recovery_target.get("max_s")
            compliance = (
                "COMPLIANT"
                if minimum_s is not None
                and maximum_s is not None
                and float(minimum_s) <= duration_s <= float(maximum_s)
                else "DEVIATION"
            )
        segment = {
                "segment_id": segment_id,
                "kind": kind,
                "start_offset_s": round(group_start_s, 3),
                "end_offset_s": round(group_end_s, 3),
                "distance_m": round(
                    float(group_rows[-1]["distance_m"])
                    - float(group_rows[0]["distance_m"]),
                    3,
                ),
                "average_speed_m_s": round(statistics.mean(speed_values), 3),
                "average_spm": round(average_spm, 2),
                "target_spm": target,
                "compliance": compliance,
                "evidence_refs": ["input/speedcoach.csv", "input/plan.json"],
            }
        if kind == "RECOVERY":
            segment["duration_s"] = round(duration_s, 3)
            segment["target_duration_s"] = {
                "min_s": minimum_s,
                "max_s": maximum_s,
            }
        segments.append(segment)
        if compliance == "DEVIATION":
            plan_deviations.append(
                {
                    "segment_ref": segment_id,
                    "type": (
                        "SPM_OUTSIDE_TARGET"
                        if kind == "WORK"
                        else "RECOVERY_DURATION_OUTSIDE_TARGET"
                    ),
                    "reason": (
                        f"Average SPM {average_spm:.2f} is outside the planned range."
                        if kind == "WORK"
                        else (
                            f"Recovery duration {duration_s:.3f} seconds is outside "
                            f"the planned {minimum_s}-{maximum_s} second range."
                        )
                    ),
                    "evidence_refs": ["input/speedcoach.csv", "input/plan.json"],
                }
            )
        previous_group_end_s = group_end_s

    missing_work_ids = [
        f"work-{index:02d}"
        for index in range(work_index + 1, len(targets) + 1)
    ]
    plan_deviations.extend(
        {
            "segment_ref": segment_id,
            "type": "PLANNED_WORK_INTERVAL_NOT_OBSERVED",
            "reason": "No compatible work segment was reconstructed for this planned interval.",
            "evidence_refs": ["input/speedcoach.csv", "input/plan.json"],
        }
        for segment_id in missing_work_ids
    )

    confirmations = summary.get("known_context", {}).get("human_confirmations", {})
    equipment_value = confirmations.get("resistance_band_used")
    equipment_confirmation = (
        "CONFIRMED_USED" if equipment_value is True
        else "CONFIRMED_NOT_USED" if equipment_value is False
        else "UNKNOWN"
    )
    result = {
        "status": "COMPLETED",
        "method": (
            "SPM threshold derived from the lowest planned work range minus 2 SPM "
            "to keep a slightly under-target work interval contiguous."
            if contract_version == "v2"
            else "SPM threshold derived from the lowest planned work range minus 1 SPM."
        ),
        "segments": segments,
        "execution_counts": {
            "planned_work_intervals": len(targets),
            "observed_work_intervals": work_index,
            "missing_work_interval_ids": missing_work_ids,
        },
        "plan_deviations": plan_deviations,
        "equipment_confirmation": equipment_confirmation,
        "limitations": [
            "Telemetry cannot observe resistance equipment or visible technique."
        ],
        "evidence_refs": ["input/speedcoach.csv", "input/plan.json"],
    }
    if contract_version == "v2":
        result["distance_assessment"] = {
            "status": "INSUFFICIENT",
            "scope": "PRESCRIBED_DISTANCE_COMPLETION",
            "reason": (
                "Per-segment distances are boundary-derived from SPM classification. "
                "They exclude transition samples and cannot establish total completed "
                "distance or a prescribed-distance shortfall."
            ),
            "evidence_refs": ["input/speedcoach.csv", "input/plan.json"],
        }
    return result


def analyze_environment(summary: dict, *, contract_version: str = "v1") -> dict:
    environment = summary.get("environment")
    if not environment or not environment.get("time_series_windows"):
        return {
            "status": "INSUFFICIENT",
            "reason": "No environmental timeline is supplied.",
            "causal_conclusion": "NOT_ESTABLISHED",
            "evidence_refs": [],
        }
    windows = environment["time_series_windows"]
    if any("effective_headwind_m_s" not in window for window in windows):
        return {
            "status": "INSUFFICIENT",
            "reason": (
                "Boat-relative wind cannot be computed because route heading is unknown."
            ),
            "causal_conclusion": "NOT_ESTABLISHED",
            "evidence_refs": ["input/environment.json"],
        }
    source = environment.get("source") or {}
    temporal_resolution = source.get("temporal_resolution_minutes")
    session_window = environment.get("session_window") or {}
    session_duration_s = None
    if session_window.get("start_utc") and session_window.get("end_utc"):
        session_start = datetime.fromisoformat(
            session_window["start_utc"].replace("Z", "+00:00")
        )
        session_end = datetime.fromisoformat(
            session_window["end_utc"].replace("Z", "+00:00")
        )
        session_duration_s = (session_end - session_start).total_seconds()
    session_windows = (
        [
            window
            for window in windows
            if 0 <= float(window["elapsed_s"]) <= session_duration_s
        ]
        if session_duration_s is not None
        else windows
    )
    analyzed_windows = session_windows or windows
    start = float(analyzed_windows[0]["effective_headwind_m_s"])
    end = float(analyzed_windows[-1]["effective_headwind_m_s"])
    sign_change = next(
        (
            float(window["elapsed_s"])
            for window in analyzed_windows
            if float(window["effective_headwind_m_s"]) >= 0
        ),
        None,
    )
    temperatures = [
        float(window["temperature_c"])
        for window in analyzed_windows
        if window.get("temperature_c") is not None
    ]
    humidities = [
        float(window["relative_humidity_pct"])
        for window in analyzed_windows
        if window.get("relative_humidity_pct") is not None
    ]
    limitations = list(environment.get("limitations", []))
    if temporal_resolution:
        limitations.append(
            f"Provider conditions have {temporal_resolution}-minute temporal resolution; "
            "they cannot establish a specific on-boat gust or stroke-level effect."
        )
    resolution_limited = (
        session_duration_s is not None
        and temporal_resolution is not None
        and (
            temporal_resolution * 60 > session_duration_s
            or len(session_windows) < 2
        )
    )
    result = {
        "status": "COMPLETED",
        "effective_headwind_start_m_s": start,
        "effective_headwind_end_m_s": end,
        "sign_change_offset_s": sign_change,
        "condition_change": (
            "INSUFFICIENT_TEMPORAL_RESOLUTION"
            if resolution_limited
            else "TAILWIND_TO_HEADWIND" if start < 0 < end else "OTHER"
        ),
        "session_environment_samples": len(session_windows),
        "temperature_range_c": (
            [min(temperatures), max(temperatures)] if temperatures else None
        ),
        "relative_humidity_range_pct": (
            [min(humidities), max(humidities)] if humidities else None
        ),
        "causal_conclusion": "NOT_ESTABLISHED",
        "interpretation": (
            "The time-aligned condition change supports an association with performance "
            "changes, but it does not establish causation or athlete regression."
        ),
        "limitations": limitations,
        "evidence_refs": ["input/environment.json", "input/speedcoach.csv"],
    }
    if contract_version == "v2":
        headwinds = [
            float(window["effective_headwind_m_s"])
            for window in analyzed_windows
        ]
        crosswinds = [
            float(window.get("effective_crosswind_m_s", 0.0))
            for window in analyzed_windows
        ]
        wind_speeds = [
            float(window["wind_speed_m_s"])
            for window in analyzed_windows
            if window.get("wind_speed_m_s") is not None
        ]
        gust_speeds = [
            float(window["gust_speed_m_s"])
            for window in analyzed_windows
            if window.get("gust_speed_m_s") is not None
        ]
        mean_headwind = statistics.mean(headwinds)
        maximum_crosswind = max((abs(value) for value in crosswinds), default=0.0)
        gust_excess = (
            max(gust_speeds) - max(wind_speeds)
            if gust_speeds and wind_speeds
            else 0.0
        )
        if min(headwinds) < -1.0 < max(headwinds):
            profile = "TAILWIND_TO_HEADWIND"
        elif wind_speeds and max(wind_speeds) <= 1.0:
            profile = "CALM"
        elif mean_headwind > 1.0:
            profile = "STEADY_HEADWIND"
        elif mean_headwind < -1.0:
            profile = "STEADY_TAILWIND"
        elif maximum_crosswind > 2.0 and gust_excess >= 2.0:
            profile = "CROSSWIND_GUSTS"
        elif maximum_crosswind > 2.0:
            profile = "CROSSWIND"
        else:
            profile = "MIXED_OR_LIGHT"
        result.update(
            {
                "condition_profile": profile,
                "effective_headwind_range_m_s": [min(headwinds), max(headwinds)],
                "effective_crosswind_range_m_s": [
                    min(crosswinds),
                    max(crosswinds),
                ],
                "wind_speed_range_m_s": (
                    [min(wind_speeds), max(wind_speeds)] if wind_speeds else None
                ),
                "gust_speed_range_m_s": (
                    [min(gust_speeds), max(gust_speeds)] if gust_speeds else None
                ),
            }
        )
    return result


def execute_tool(
    name: str,
    summary: dict,
    input_dir: Path,
    arguments: dict,
    *,
    contract_version: str = "v1",
) -> dict:
    if arguments:
        raise ValueError(f"{name} does not accept arguments")
    handlers = {
        "assess_source_trust": lambda: assess_source_trust(summary),
        "assess_session_alignment": lambda: assess_session_alignment(summary),
        "reconstruct_plan_execution": lambda: reconstruct_plan_execution(
            summary,
            input_dir,
            contract_version=contract_version,
        ),
        "analyze_environment": lambda: analyze_environment(
            summary, contract_version=contract_version
        ),
    }
    if name not in handlers:
        raise ValueError(f"Unknown WAKE tool: {name}")
    return handlers[name]()
