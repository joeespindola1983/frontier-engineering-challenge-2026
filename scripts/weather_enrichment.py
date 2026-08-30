#!/usr/bin/env python3
"""Deterministic historical-weather enrichment for WAKE telemetry.

The module keeps raw telemetry out of the weather provider. It derives one
rounded representative coordinate and an aware UTC session window, requests a
small canonical set of hourly variables, and normalizes the provider response
into WAKE's environment timeline contract.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import statistics
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


LOOKUP_VERSION = "wake.weather_lookup_request.v1"
TIMELINE_VERSION = "wake.environment_timeline.v2"
LOCATION_PRECISION_DECIMALS = 2
QUERY_BUFFER = timedelta(hours=1)
OPEN_METEO_ENDPOINT = (
    "https://historical-forecast-api.open-meteo.com/v1/forecast"
)
OPEN_METEO_HOURLY_VARIABLES = (
    "temperature_2m",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m",
)


def _parse_aware_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Telemetry contains an invalid timestamp.") from error
    if parsed.utcoffset() is None:
        raise ValueError(
            "Historical weather enrichment requires timezone-aware telemetry timestamps."
        )
    return parsed.astimezone(timezone.utc)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_weather_lookup(
    normalized_telemetry_csv: bytes,
    *,
    assumed_timezone: str | None = None,
) -> dict:
    """Create a privacy-bounded weather lookup from normalized telemetry."""
    try:
        rows = list(
            csv.DictReader(io.StringIO(normalized_telemetry_csv.decode("utf-8")))
        )
    except UnicodeDecodeError as error:
        raise ValueError("Telemetry must be UTF-8 CSV.") from error
    if not rows:
        raise ValueError("Weather enrichment requires telemetry rows.")

    assumed_zone = None
    if assumed_timezone:
        try:
            assumed_zone = ZoneInfo(assumed_timezone)
        except ZoneInfoNotFoundError as error:
            raise ValueError("session_timezone must be a valid IANA timezone.") from error

    timestamps = []
    used_assumed_timezone = False
    for row in rows:
        raw_timestamp = (row.get("timestamp") or "").strip()
        if not raw_timestamp:
            continue
        try:
            parsed = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("Telemetry contains an invalid timestamp.") from error
        if parsed.utcoffset() is None:
            if assumed_zone is None:
                raise ValueError(
                    "Historical weather enrichment requires timezone-aware telemetry "
                    "timestamps or a confirmed IANA session_timezone."
                )
            parsed = parsed.replace(tzinfo=assumed_zone)
            used_assumed_timezone = True
        timestamps.append(parsed.astimezone(timezone.utc))
    coordinates = [
        (float(row["latitude"]), float(row["longitude"]))
        for row in rows
        if (row.get("latitude") or "").strip()
        and (row.get("longitude") or "").strip()
    ]
    if not timestamps:
        raise ValueError(
            "Historical weather enrichment requires timezone-aware telemetry timestamps."
        )
    if not coordinates:
        raise ValueError("Historical weather enrichment requires GPS coordinates.")

    session_start = min(timestamps)
    session_end = max(timestamps)
    query_start = session_start - QUERY_BUFFER
    query_end = session_end + QUERY_BUFFER
    latitude = round(
        statistics.median(point[0] for point in coordinates),
        LOCATION_PRECISION_DECIMALS,
    )
    longitude = round(
        statistics.median(point[1] for point in coordinates),
        LOCATION_PRECISION_DECIMALS,
    )
    request = {
        "schema_version": LOOKUP_VERSION,
        "provider": "Open-Meteo",
        "dataset": "Historical Forecast API",
        "latitude": latitude,
        "longitude": longitude,
        "location_precision_decimals": LOCATION_PRECISION_DECIMALS,
        "session_start_utc": _iso_utc(session_start),
        "session_end_utc": _iso_utc(session_end),
        "query_start_utc": _iso_utc(query_start),
        "query_end_utc": _iso_utc(query_end),
        "query_start_date": query_start.date().isoformat(),
        "query_end_date": query_end.date().isoformat(),
        "hourly_variables": list(OPEN_METEO_HOURLY_VARIABLES),
        "time_zone_source": (
            "USER_SUPPLIED_IANA" if used_assumed_timezone else "TELEMETRY_OFFSET"
        ),
        "assumed_timezone": assumed_timezone if used_assumed_timezone else None,
    }
    request["lookup_id"] = "weather-lookup-" + hashlib.sha256(
        json.dumps(request, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return request


class OpenMeteoHistoricalForecastProvider:
    """Small provider adapter with an injectable network boundary."""

    def __init__(self, *, timeout_s: float = 15.0) -> None:
        self.timeout_s = timeout_s

    @staticmethod
    def build_url(lookup: dict) -> str:
        query = urlencode(
            {
                "latitude": lookup["latitude"],
                "longitude": lookup["longitude"],
                "start_date": lookup["query_start_date"],
                "end_date": lookup["query_end_date"],
                "hourly": ",".join(OPEN_METEO_HOURLY_VARIABLES),
                "wind_speed_unit": "ms",
                "timezone": "GMT",
            }
        )
        return f"{OPEN_METEO_ENDPOINT}?{query}"

    def __call__(self, lookup: dict) -> dict:
        request = Request(
            self.build_url(lookup),
            headers={"User-Agent": "WAKE-Agentic-Rowing-Intelligence/1.0"},
        )
        with urlopen(request, timeout=self.timeout_s) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Weather provider returned a non-object response.")
        if payload.get("error"):
            raise ValueError(
                f"Weather provider rejected the request: {payload.get('reason', 'unknown error')}"
            )
        return payload


def _provider_timestamp_utc(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise ValueError("Weather provider returned an invalid timestamp.") from error
    if parsed.utcoffset() is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return _iso_utc(parsed)


def _nullable_number(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def normalize_open_meteo_response(
    *,
    request: dict,
    response: dict,
    retrieved_at: datetime,
) -> dict:
    """Normalize a provider response without inventing sub-hourly precision."""
    hourly = response.get("hourly")
    if not isinstance(hourly, dict):
        raise ValueError("Weather provider response has no hourly data.")
    required = ("time", *OPEN_METEO_HOURLY_VARIABLES)
    arrays = {key: hourly.get(key) for key in required}
    if not all(isinstance(value, list) for value in arrays.values()):
        raise ValueError("Weather provider response is missing required hourly arrays.")
    lengths = {len(value) for value in arrays.values()}
    if len(lengths) != 1:
        raise ValueError("Weather provider hourly arrays must have the same length.")
    if lengths == {0}:
        raise ValueError("Weather provider returned no hourly samples.")

    samples = []
    query_start = _parse_aware_timestamp(request["query_start_utc"])
    query_end = _parse_aware_timestamp(request["query_end_utc"])
    for index, timestamp in enumerate(arrays["time"]):
        normalized_timestamp = _provider_timestamp_utc(str(timestamp))
        timestamp_utc = _parse_aware_timestamp(normalized_timestamp)
        if timestamp_utc < query_start or timestamp_utc > query_end:
            continue
        humidity = _nullable_number(arrays["relative_humidity_2m"][index])
        if humidity is not None and not 0 <= humidity <= 100:
            raise ValueError("Weather provider returned invalid relative humidity.")
        direction = float(arrays["wind_direction_10m"][index]) % 360
        wind_speed = float(arrays["wind_speed_10m"][index])
        if wind_speed < 0:
            raise ValueError("Weather provider returned negative wind speed.")
        samples.append(
            {
                "timestamp": normalized_timestamp,
                "wind_speed_m_s": wind_speed,
                "wind_direction_deg": direction,
                "gust_speed_m_s": _nullable_number(
                    arrays["wind_gusts_10m"][index]
                ),
                "temperature_c": _nullable_number(
                    arrays["temperature_2m"][index]
                ),
                "relative_humidity_pct": humidity,
            }
        )
    if not samples:
        raise ValueError("Weather provider returned no samples in the requested window.")

    retrieved_at = retrieved_at.astimezone(timezone.utc)
    return {
        "schema_version": TIMELINE_VERSION,
        "timeline_id": f"environment-{request['lookup_id']}",
        "source": {
            "kind": "WEATHER_API",
            "source_ref": f"open-meteo:{request['lookup_id']}",
            "quality": "MEDIUM",
            "provider": "Open-Meteo",
            "dataset": "Historical Forecast API",
            "model": "best_match (provider-selected)",
            "spatial_resolution_km": None,
            "temporal_resolution_minutes": 60,
            "retrieved_at": _iso_utc(retrieved_at),
            "attribution": "Weather data by Open-Meteo.com under CC BY 4.0",
        },
        "location": {
            "requested_coordinate_rounded": {
                "latitude": request["latitude"],
                "longitude": request["longitude"],
            },
            "returned_grid_coordinate": {
                "latitude": float(response["latitude"]),
                "longitude": float(response["longitude"]),
            },
            "precision_decimals": request["location_precision_decimals"],
        },
        "session_window": {
            "start_utc": request["session_start_utc"],
            "end_utc": request["session_end_utc"],
        },
        "direction_convention": "METEOROLOGICAL_FROM_DEGREES_TRUE_NORTH",
        "units": {
            "wind_speed": "m/s",
            "temperature": "celsius",
            "relative_humidity": "percent",
        },
        "time_basis": {
            "provider_timezone": str(response.get("timezone", "GMT")),
            "provider_utc_offset_seconds": int(
                response.get("utc_offset_seconds", 0)
            ),
            "temporal_resolution_minutes": 60,
            "interpolation": "NONE",
            "session_timezone_source": request["time_zone_source"],
            "assumed_session_timezone": request["assumed_timezone"],
        },
        "samples": samples,
        "limitations": [
            "Provider values are modeled hourly conditions, not on-boat measurements.",
            "Local gusts, chop, shoreline effects, and causal performance effects are not established.",
        ],
    }
