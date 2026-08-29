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


def _canonical_csv(rows: list[dict[str, str]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=CANONICAL_COLUMNS,
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
) -> NormalizationResult:
    if not rows:
        raise ValueError(f"{source_format} contains no usable telemetry rows.")
    normalized_csv = _canonical_csv(rows)
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
