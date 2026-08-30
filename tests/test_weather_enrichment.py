from __future__ import annotations

import sys
import unittest
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import weather_enrichment  # noqa: E402
import verify_synthetic_case  # noqa: E402


TELEMETRY = b"""timestamp,elapsed_s,distance_m,speed_m_s,stroke_rate_spm,latitude,longitude,heading_deg
2026-01-20T06:00:00-03:00,0,0,0,0,10.001,20.001,0
2026-01-20T06:30:00-03:00,1800,4000,3.2,20,10.041,20.041,0
2026-01-20T07:00:00-03:00,3600,8000,3.1,22,10.081,20.081,180
"""


PROVIDER_RESPONSE = {
    "latitude": 10.0,
    "longitude": 20.0,
    "utc_offset_seconds": 0,
    "timezone": "GMT",
    "hourly_units": {
        "time": "iso8601",
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
        "wind_speed_10m": "m/s",
        "wind_direction_10m": "°",
        "wind_gusts_10m": "m/s",
    },
    "hourly": {
        "time": [
            "2026-01-20T08:00",
            "2026-01-20T09:00",
            "2026-01-20T10:00",
            "2026-01-20T11:00",
        ],
        "temperature_2m": [18.0, 19.0, 20.0, 21.0],
        "relative_humidity_2m": [88, 84, 80, 76],
        "wind_speed_10m": [1.0, 2.0, 4.0, 3.0],
        "wind_direction_10m": [180, 170, 20, 10],
        "wind_gusts_10m": [1.5, 2.8, 6.5, 4.2],
    },
}


class WeatherEnrichmentTests(unittest.TestCase):
    def test_contract_verifier_discovers_both_environment_schema_versions(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/environment-timeline.schema.json").read_text()
        )

        self.assertEqual(
            verify_synthetic_case.declared_schema_versions(schema),
            {
                "wake.environment_timeline.v1",
                "wake.environment_timeline.v2",
            },
        )

    def test_lookup_uses_rounded_location_and_aware_utc_window(self) -> None:
        request = weather_enrichment.build_weather_lookup(TELEMETRY)

        self.assertEqual(request["latitude"], 10.04)
        self.assertEqual(request["longitude"], 20.04)
        self.assertEqual(request["location_precision_decimals"], 2)
        self.assertEqual(request["session_start_utc"], "2026-01-20T09:00:00Z")
        self.assertEqual(request["session_end_utc"], "2026-01-20T10:00:00Z")
        self.assertEqual(request["query_start_date"], "2026-01-20")
        self.assertEqual(request["query_end_date"], "2026-01-20")

    def test_lookup_rejects_timezone_unknown_before_external_access(self) -> None:
        naive = TELEMETRY.replace(b"-03:00", b"")

        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            weather_enrichment.build_weather_lookup(naive)

    def test_lookup_accepts_an_explicit_iana_timezone_for_local_device_time(self) -> None:
        naive = TELEMETRY.replace(b"-03:00", b"")

        request = weather_enrichment.build_weather_lookup(
            naive,
            assumed_timezone="America/Sao_Paulo",
        )

        self.assertEqual(request["session_start_utc"], "2026-01-20T09:00:00Z")
        self.assertEqual(request["session_end_utc"], "2026-01-20T10:00:00Z")
        self.assertEqual(request["time_zone_source"], "USER_SUPPLIED_IANA")
        self.assertEqual(request["assumed_timezone"], "America/Sao_Paulo")

    def test_lookup_rejects_an_invalid_assumed_timezone_before_external_access(self) -> None:
        naive = TELEMETRY.replace(b"-03:00", b"")

        with self.assertRaisesRegex(ValueError, "IANA timezone"):
            weather_enrichment.build_weather_lookup(
                naive,
                assumed_timezone="Brazil/Not-A-Timezone",
            )

    def test_open_meteo_url_uses_only_canonical_variables_and_rounded_location(self) -> None:
        request = weather_enrichment.build_weather_lookup(TELEMETRY)
        url = weather_enrichment.OpenMeteoHistoricalForecastProvider.build_url(request)
        query = parse_qs(urlsplit(url).query)

        self.assertEqual(urlsplit(url).hostname, "historical-forecast-api.open-meteo.com")
        self.assertEqual(query["latitude"], ["10.04"])
        self.assertEqual(query["longitude"], ["20.04"])
        self.assertEqual(query["wind_speed_unit"], ["ms"])
        self.assertEqual(query["timezone"], ["GMT"])
        self.assertEqual(
            query["hourly"],
            [
                "temperature_2m,relative_humidity_2m,wind_speed_10m,"
                "wind_direction_10m,wind_gusts_10m"
            ],
        )
        self.assertNotIn("10.081", url)
        self.assertNotIn("20.081", url)

    def test_provider_response_normalizes_to_v2_with_provenance_and_si_units(self) -> None:
        request = weather_enrichment.build_weather_lookup(TELEMETRY)
        timeline = weather_enrichment.normalize_open_meteo_response(
            request=request,
            response=PROVIDER_RESPONSE,
            retrieved_at=datetime(2026, 8, 29, 12, 0, tzinfo=timezone.utc),
        )

        self.assertEqual(timeline["schema_version"], "wake.environment_timeline.v2")
        self.assertEqual(timeline["source"]["kind"], "WEATHER_API")
        self.assertEqual(timeline["source"]["provider"], "Open-Meteo")
        self.assertEqual(timeline["source"]["dataset"], "Historical Forecast API")
        self.assertEqual(timeline["source"]["quality"], "MEDIUM")
        self.assertEqual(timeline["units"]["wind_speed"], "m/s")
        self.assertEqual(timeline["units"]["temperature"], "celsius")
        self.assertEqual(timeline["units"]["relative_humidity"], "percent")
        self.assertEqual(
            timeline["session_window"],
            {
                "start_utc": "2026-01-20T09:00:00Z",
                "end_utc": "2026-01-20T10:00:00Z",
            },
        )
        self.assertEqual(
            timeline["location"]["requested_coordinate_rounded"],
            {"latitude": 10.04, "longitude": 20.04},
        )
        self.assertEqual(timeline["samples"][1]["relative_humidity_pct"], 84.0)
        self.assertEqual(timeline["samples"][1]["timestamp"], "2026-01-20T09:00:00Z")

        schema = json.loads(
            (ROOT / "schemas/environment-timeline.schema.json").read_text(
                encoding="utf-8"
            )
        )
        jsonschema.validate(instance=timeline, schema=schema)

    def test_environment_schema_keeps_the_committed_v1_fixture_valid(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/environment-timeline.schema.json").read_text(
                encoding="utf-8"
            )
        )
        fixture = json.loads(
            (
                ROOT
                / "data/fixtures/case-002-wind-shift-plan-deviation/input/environment.json"
            ).read_text(encoding="utf-8")
        )

        jsonschema.validate(instance=fixture, schema=schema)

    def test_day_response_is_filtered_to_the_requested_utc_window(self) -> None:
        response = {
            "latitude": 10.0,
            "longitude": 20.0,
            "utc_offset_seconds": 0,
            "timezone": "GMT",
            "hourly": {
                "time": [f"2026-01-20T{hour:02d}:00" for hour in range(24)],
                "temperature_2m": [18.0] * 24,
                "relative_humidity_2m": [80] * 24,
                "wind_speed_10m": [2.0] * 24,
                "wind_direction_10m": [180] * 24,
                "wind_gusts_10m": [3.0] * 24,
            },
        }

        timeline = weather_enrichment.normalize_open_meteo_response(
            request=weather_enrichment.build_weather_lookup(TELEMETRY),
            response=response,
            retrieved_at=datetime.now(timezone.utc),
        )

        self.assertEqual(
            [sample["timestamp"] for sample in timeline["samples"]],
            [
                "2026-01-20T08:00:00Z",
                "2026-01-20T09:00:00Z",
                "2026-01-20T10:00:00Z",
                "2026-01-20T11:00:00Z",
            ],
        )

    def test_mismatched_provider_arrays_are_rejected(self) -> None:
        response = {
            **PROVIDER_RESPONSE,
            "hourly": {
                **PROVIDER_RESPONSE["hourly"],
                "relative_humidity_2m": [88],
            },
        }

        with self.assertRaisesRegex(ValueError, "same length"):
            weather_enrichment.normalize_open_meteo_response(
                request=weather_enrichment.build_weather_lookup(TELEMETRY),
                response=response,
                retrieved_at=datetime.now(timezone.utc),
            )


if __name__ == "__main__":
    unittest.main()
