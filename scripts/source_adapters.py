#!/usr/bin/env python3
"""Deterministic raw telemetry adapters for WAKE.

Adapters preserve source-specific uncertainty and emit a compact canonical CSV.
They do not infer technique, repair missing SPM, or decide metric trust.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


CANONICAL_COLUMNS = [
    "timestamp",
    "elapsed_s",
    "distance_m",
    "speed_m_s",
    "stroke_rate_spm",
    "latitude",
    "longitude",
]
REQUIRED_NORMALIZED_COLUMNS = {
    "elapsed_s",
    "distance_m",
    "speed_m_s",
    "stroke_rate_spm",
}
MOBILE_SENSOR_COLUMNS = {
    "sampleType",
    "timestamp",
    "distance",
    "latitude",
    "longitude",
    "speed",
    "spm",
}
CONCEPT2_TRANSCRIPTION_COLUMNS = {
    "transcription_provenance",
    "workout_type",
    "row_kind",
    "row_index",
    "display_time_s",
    "display_distance_m",
    "pace_500m_s",
    "stroke_rate_spm",
    "heart_rate_bpm",
    "watts",
}
CONCEPT2_NORMALIZED_COLUMNS = [
    *CANONICAL_COLUMNS,
    "segment_kind",
    "segment_index",
    "pace_500m_s",
    "heart_rate_bpm",
    "watts",
]


@dataclass(frozen=True)
class NormalizationResult:
    source_format: str
    normalized_csv: bytes
    report: dict


def _parse_elapsed(value: str) -> float:
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _format(value: float, places: int) -> str:
    return f"{value:.{places}f}"


def _require_finite(*values: float | None) -> None:
    if not all(value is None or math.isfinite(value) for value in values):
        raise ValueError("Telemetry contains a non-finite numeric value.")


def _normalized_csv(
    rows: list[dict[str, str]],
    fieldnames: list[str] = CANONICAL_COLUMNS,
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _quality_report(
    *,
    source_ref: str,
    source_format: str,
    normalized_csv: bytes,
    rows: list[dict[str, str]],
    rejected_rows: int,
    extra_flags: list[str] | None = None,
) -> dict:
    spm_cells = [row["stroke_rate_spm"].strip() for row in rows]
    supplied_spm = [float(value) for value in spm_cells if value]
    positive_spm_rows = sum(value > 0 for value in supplied_spm)
    gps_rows = sum(
        bool(row["latitude"].strip() and row["longitude"].strip())
        for row in rows
    )
    flags = list(extra_flags or [])
    if gps_rows:
        flags.append("GPS_PRESENT")
    else:
        flags.append("GPS_ABSENT")
    if positive_spm_rows:
        flags.append("SPM_PRESENT")
    elif supplied_spm:
        flags.append("SPM_ALL_ZERO")
    else:
        flags.append("RAW_SPM_ABSENT")
    if rejected_rows:
        flags.append("REJECTED_ROWS_PRESENT")

    elapsed = [float(row["elapsed_s"]) for row in rows]
    distances = [float(row["distance_m"]) for row in rows]
    timestamps = [row["timestamp"] for row in rows if row["timestamp"]]
    return {
        "schema_version": "wake.source_normalization.v1",
        "source_ref": source_ref,
        "input_format": source_format,
        "normalized_sha256": hashlib.sha256(normalized_csv).hexdigest(),
        "row_count": len(rows),
        "rejected_row_count": rejected_rows,
        "start_time": timestamps[0] if timestamps else None,
        "end_time": timestamps[-1] if timestamps else None,
        "duration_s": round(max(elapsed) - min(elapsed), 3),
        "max_distance_m": round(max(distances), 3),
        "positive_spm_rows": positive_spm_rows,
        "gps_rows": gps_rows,
        "quality_flags": list(dict.fromkeys(flags)),
    }


def _result(
    *,
    source_ref: str,
    source_format: str,
    rows: list[dict[str, str]],
    rejected_rows: int = 0,
    extra_flags: list[str] | None = None,
    fieldnames: list[str] = CANONICAL_COLUMNS,
) -> NormalizationResult:
    if not rows:
        raise ValueError(f"{source_format} contains no usable telemetry rows.")
    normalized_csv = _normalized_csv(rows, fieldnames)
    return NormalizationResult(
        source_format=source_format,
        normalized_csv=normalized_csv,
        report=_quality_report(
            source_ref=source_ref,
            source_format=source_format,
            normalized_csv=normalized_csv,
            rows=rows,
            rejected_rows=rejected_rows,
            extra_flags=extra_flags,
        ),
    )


def _normalize_speedcoach_vendor(text: str, source_ref: str) -> NormalizationResult:
    start_time: datetime | None = None
    in_per_stroke = False
    rows: list[dict[str, str]] = []
    rejected_rows = 0
    for source_row in csv.reader(io.StringIO(text)):
        if source_row and source_row[0] == "Start Time:":
            try:
                start_time = datetime.strptime(source_row[1], "%m/%d/%Y %H:%M:%S")
            except (IndexError, ValueError):
                start_time = None
        if source_row == ["Per-Stroke Data:"]:
            in_per_stroke = True
            continue
        if not in_per_stroke or len(source_row) < 24:
            continue
        try:
            int(source_row[0])
            elapsed_s = _parse_elapsed(source_row[3])
            distance_m = float(source_row[1])
            speed_m_s = float(source_row[5])
            spm = float(source_row[8])
            latitude = float(source_row[22])
            longitude = float(source_row[23])
            _require_finite(
                elapsed_s,
                distance_m,
                speed_m_s,
                spm,
                latitude,
                longitude,
            )
        except (ValueError, IndexError):
            if source_row and source_row[0] not in {"Interval", "(Interval)"}:
                rejected_rows += 1
            continue
        timestamp = (
            (start_time + timedelta(seconds=elapsed_s)).isoformat(timespec="milliseconds")
            if start_time
            else ""
        )
        rows.append(
            {
                "timestamp": timestamp,
                "elapsed_s": _format(elapsed_s, 3),
                "distance_m": _format(distance_m, 3),
                "speed_m_s": _format(speed_m_s, 3),
                "stroke_rate_spm": _format(spm, 2),
                "latitude": _format(latitude, 7),
                "longitude": _format(longitude, 7),
            }
        )
    if not rows:
        raise ValueError("SpeedCoach export contains no usable per-stroke telemetry.")
    return _result(
        source_ref=source_ref,
        source_format="SPEEDCOACH_VENDOR_CSV",
        rows=rows,
        rejected_rows=rejected_rows,
        extra_flags=["TIMEZONE_UNKNOWN"] if start_time else ["START_TIME_ABSENT"],
    )


def _normalize_mobile_sensor(text: str, source_ref: str) -> NormalizationResult:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not MOBILE_SENSOR_COLUMNS.issubset(reader.fieldnames):
        raise ValueError("Unsupported MOBILE telemetry columns.")
    source_rows = [row for row in reader if row.get("sampleType") == "sensor"]
    timestamps = []
    for row in source_rows:
        try:
            timestamps.append(int(row["timestamp"]))
        except (TypeError, ValueError):
            continue
    if not timestamps:
        raise ValueError("WAKE mobile export contains no usable sensor timestamps.")
    start_ms = min(timestamps)
    rows: list[dict[str, str]] = []
    rejected_rows = 0
    for source_row in source_rows:
        try:
            timestamp_ms = int(source_row["timestamp"])
            distance_m = float(source_row["distance"])
            speed_m_s = float(source_row["speed"])
            latitude = float(source_row["latitude"])
            longitude = float(source_row["longitude"])
            raw_spm = (source_row.get("spm") or "").strip()
            spm = float(raw_spm) if raw_spm else None
            _require_finite(distance_m, speed_m_s, latitude, longitude, spm)
        except (TypeError, ValueError):
            rejected_rows += 1
            continue
        timestamp = datetime.fromtimestamp(
            timestamp_ms / 1000,
            tz=timezone.utc,
        ).isoformat(timespec="milliseconds")
        rows.append(
            {
                "timestamp": timestamp,
                "elapsed_s": _format((timestamp_ms - start_ms) / 1000, 3),
                "distance_m": _format(distance_m, 3),
                "speed_m_s": _format(speed_m_s, 3),
                "stroke_rate_spm": "" if spm is None else _format(spm, 2),
                "latitude": _format(latitude, 7),
                "longitude": _format(longitude, 7),
            }
        )
    return _result(
        source_ref=source_ref,
        source_format="WAKE_MOBILE_SENSOR_CSV",
        rows=rows,
        rejected_rows=rejected_rows,
    )


def _optional_number(source_row: dict[str, str], key: str) -> float | None:
    raw = (source_row.get(key) or "").strip()
    return float(raw) if raw else None


def _normalize_concept2_transcription(
    text: str,
    source_ref: str,
) -> NormalizationResult:
    """Normalize a declared-provenance PM5 screen transcription.

    PM5 detail screens use different cumulative axes depending on the workout:
    fixed-distance rows show cumulative distance and split duration, while
    fixed-time rows show cumulative time and split distance. Interval rows are
    individual work or recovery segments. This adapter makes that distinction
    explicit instead of guessing it from values.
    """

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not CONCEPT2_TRANSCRIPTION_COLUMNS.issubset(
        reader.fieldnames
    ):
        raise ValueError("Unsupported CONCEPT2 confirmed-transcription columns.")
    source_rows = list(reader)
    if not source_rows:
        raise ValueError("CONCEPT2 transcription contains no rows.")

    workout_types = {
        (row.get("workout_type") or "").strip().upper() for row in source_rows
    }
    if len(workout_types) != 1 or "" in workout_types:
        raise ValueError("CONCEPT2 transcription must contain one workout type.")
    workout_type = next(iter(workout_types))
    if workout_type not in {"FIXED_DISTANCE", "FIXED_TIME", "INTERVAL"}:
        raise ValueError(f"Unsupported CONCEPT2 workout type: {workout_type}.")
    transcription_provenance_values = {
        (row.get("transcription_provenance") or "").strip().upper()
        for row in source_rows
    }
    if len(transcription_provenance_values) != 1:
        raise ValueError("CONCEPT2 transcription must contain one provenance value.")
    transcription_provenance = next(iter(transcription_provenance_values))
    if transcription_provenance not in {"HUMAN_CONFIRMED", "SYNTHETIC"}:
        raise ValueError(
            "CONCEPT2 transcription provenance must be HUMAN_CONFIRMED or SYNTHETIC."
        )

    rows = [{
        "timestamp": "",
        "elapsed_s": _format(0, 3),
        "distance_m": _format(0, 3),
        "speed_m_s": _format(0, 3),
        "stroke_rate_spm": "",
        "latitude": "",
        "longitude": "",
        "segment_kind": "ORIGIN",
        "segment_index": "0",
        "pace_500m_s": "",
        "heart_rate_bpm": "",
        "watts": "",
    }]
    cumulative_elapsed_s = 0.0
    cumulative_distance_m = 0.0
    previous_display_time_s = 0.0
    previous_display_distance_m = 0.0
    seen_indexes: set[int] = set()
    heart_rate_present = False
    power_present = False
    recovery_present = False

    for source_row in source_rows:
        try:
            row_index = int((source_row.get("row_index") or "").strip())
            row_kind = (source_row.get("row_kind") or "").strip().upper()
            display_time_s = float(source_row["display_time_s"])
            display_distance_m = float(source_row["display_distance_m"])
            pace_500m_s = _optional_number(source_row, "pace_500m_s")
            spm = _optional_number(source_row, "stroke_rate_spm")
            heart_rate = _optional_number(source_row, "heart_rate_bpm")
            watts = _optional_number(source_row, "watts")
            _require_finite(
                display_time_s,
                display_distance_m,
                pace_500m_s,
                spm,
                heart_rate,
                watts,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("CONCEPT2 transcription contains an invalid numeric row.") from error

        if row_index <= 0 or row_index in seen_indexes:
            raise ValueError("CONCEPT2 row indexes must be unique positive integers.")
        seen_indexes.add(row_index)
        if display_time_s <= 0 or display_distance_m < 0:
            raise ValueError("CONCEPT2 time must be positive and distance non-negative.")
        if pace_500m_s is not None and pace_500m_s <= 0:
            raise ValueError("CONCEPT2 pace must be positive when supplied.")
        if spm is not None and spm < 0:
            raise ValueError("CONCEPT2 SPM cannot be negative.")

        if workout_type == "FIXED_DISTANCE":
            if row_kind != "SPLIT":
                raise ValueError("Fixed-distance CONCEPT2 rows must be SPLIT rows.")
            if display_distance_m <= previous_display_distance_m:
                raise ValueError(
                    "Fixed-distance CONCEPT2 markers must use strictly increasing distance."
                )
            segment_elapsed_s = display_time_s
            cumulative_elapsed_s += segment_elapsed_s
            cumulative_distance_m = display_distance_m
            previous_display_distance_m = display_distance_m
            segment_kind = "WORK"
        elif workout_type == "FIXED_TIME":
            if row_kind != "SPLIT":
                raise ValueError("Fixed-time CONCEPT2 rows must be SPLIT rows.")
            if display_time_s <= previous_display_time_s:
                raise ValueError(
                    "Fixed-time CONCEPT2 markers must use strictly increasing time."
                )
            segment_elapsed_s = display_time_s - previous_display_time_s
            cumulative_elapsed_s = display_time_s
            cumulative_distance_m += display_distance_m
            previous_display_time_s = display_time_s
            segment_kind = "WORK"
        else:
            if row_kind not in {"WORK", "RECOVERY"}:
                raise ValueError("Interval CONCEPT2 rows must be WORK or RECOVERY rows.")
            segment_elapsed_s = display_time_s
            cumulative_elapsed_s += segment_elapsed_s
            cumulative_distance_m += display_distance_m
            segment_kind = row_kind
            recovery_present = recovery_present or row_kind == "RECOVERY"

        speed_m_s = (
            500 / pace_500m_s
            if pace_500m_s is not None
            else display_distance_m / segment_elapsed_s
        )
        heart_rate_present = heart_rate_present or heart_rate is not None
        power_present = power_present or watts is not None
        rows.append({
            "timestamp": "",
            "elapsed_s": _format(cumulative_elapsed_s, 3),
            "distance_m": _format(cumulative_distance_m, 3),
            "speed_m_s": _format(speed_m_s, 3),
            "stroke_rate_spm": "" if spm is None else _format(spm, 2),
            "latitude": "",
            "longitude": "",
            "segment_kind": segment_kind,
            "segment_index": str(row_index),
            "pace_500m_s": "" if pace_500m_s is None else _format(pace_500m_s, 3),
            "heart_rate_bpm": "" if heart_rate is None else _format(heart_rate, 1),
            "watts": "" if watts is None else _format(watts, 1),
        })

    flags = [
        "CONCEPT2_SUMMARY_LEVEL",
        f"TRANSCRIPTION_{transcription_provenance}",
        f"WORKOUT_TYPE_{workout_type}",
        "TIMESTAMP_ABSENT",
    ]
    if heart_rate_present:
        flags.append("HEART_RATE_PRESENT")
    if power_present:
        flags.append("POWER_PRESENT")
    if recovery_present:
        flags.append("RECOVERY_ROWS_PRESENT")
    return _result(
        source_ref=source_ref,
        source_format="CONCEPT2_PM5_TRANSCRIPTION_CSV",
        rows=rows,
        extra_flags=flags,
        fieldnames=CONCEPT2_NORMALIZED_COLUMNS,
    )


def _normalize_canonical(
    text: str,
    source_ref: str,
) -> NormalizationResult:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or not REQUIRED_NORMALIZED_COLUMNS.issubset(
        reader.fieldnames
    ):
        raise ValueError("Normalized telemetry is missing required columns.")
    rows: list[dict[str, str]] = []
    rejected_rows = 0
    for source_row in reader:
        try:
            elapsed_s = float(source_row["elapsed_s"])
            distance_m = float(source_row["distance_m"])
            speed_m_s = float(source_row["speed_m_s"])
            raw_spm = (source_row.get("stroke_rate_spm") or "").strip()
            spm = float(raw_spm) if raw_spm else None
            raw_latitude = (source_row.get("latitude") or "").strip()
            raw_longitude = (source_row.get("longitude") or "").strip()
            latitude = float(raw_latitude) if raw_latitude else None
            longitude = float(raw_longitude) if raw_longitude else None
            _require_finite(
                elapsed_s,
                distance_m,
                speed_m_s,
                spm,
                latitude,
                longitude,
            )
        except (TypeError, ValueError):
            rejected_rows += 1
            continue
        rows.append(
            {
                "timestamp": (source_row.get("timestamp") or "").strip(),
                "elapsed_s": _format(elapsed_s, 3),
                "distance_m": _format(distance_m, 3),
                "speed_m_s": _format(speed_m_s, 3),
                "stroke_rate_spm": "" if spm is None else _format(spm, 2),
                "latitude": "" if latitude is None else _format(latitude, 7),
                "longitude": "" if longitude is None else _format(longitude, 7),
            }
        )
    return _result(
        source_ref=source_ref,
        source_format="WAKE_NORMALIZED_TELEMETRY_CSV",
        rows=rows,
        rejected_rows=rejected_rows,
    )


def normalize_source(*, kind: str, content: bytes, source_ref: str) -> NormalizationResult:
    """Detect a supported format for the declared source kind and normalize it."""

    kind = kind.upper()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError(f"Unsupported {kind} CSV encoding.") from error
    if not text.strip():
        raise ValueError(f"Unsupported {kind} empty CSV.")

    header = next(csv.reader(io.StringIO(text)), [])
    columns = {column.strip() for column in header}
    if REQUIRED_NORMALIZED_COLUMNS.issubset(columns):
        result = _normalize_canonical(text, source_ref)
    elif kind == "SPEEDCOACH" and (
        "Per-Stroke Data:" in text or "Session Information:" in text
    ):
        result = _normalize_speedcoach_vendor(text, source_ref)
    elif kind == "MOBILE" and MOBILE_SENSOR_COLUMNS.issubset(columns):
        result = _normalize_mobile_sensor(text, source_ref)
    elif kind == "CONCEPT2" and CONCEPT2_TRANSCRIPTION_COLUMNS.issubset(columns):
        result = _normalize_concept2_transcription(text, source_ref)
    else:
        raise ValueError(f"Unsupported {kind} telemetry format or required columns.")
    return NormalizationResult(
        source_format=result.source_format,
        normalized_csv=result.normalized_csv,
        report={
            **result.report,
            "input_sha256": hashlib.sha256(content).hexdigest(),
        },
    )
