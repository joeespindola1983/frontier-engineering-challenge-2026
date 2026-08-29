from __future__ import annotations

import csv
import io
import json
import sys
import unittest
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import source_adapters  # noqa: E402


SOURCES = (
    ROOT
    / "data/fixtures/case-001-misaligned-double-scull/input/sources"
)


def normalized_rows(content: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(content.decode("utf-8"))))


class SourceAdapterTests(unittest.TestCase):
    def test_speedcoach_vendor_export_becomes_canonical_telemetry(self) -> None:
        result = source_adapters.normalize_source(
            kind="SPEEDCOACH",
            content=(SOURCES / "speedcoach.csv").read_bytes(),
            source_ref="upload/speedcoach.csv",
        )
        rows = normalized_rows(result.normalized_csv)

        self.assertEqual(result.source_format, "SPEEDCOACH_VENDOR_CSV")
        self.assertEqual(len(rows), 549)
        self.assertEqual(
            list(rows[0]),
            [
                "timestamp",
                "elapsed_s",
                "distance_m",
                "speed_m_s",
                "stroke_rate_spm",
                "latitude",
                "longitude",
            ],
        )
        self.assertEqual(float(rows[0]["elapsed_s"]), 3.1)
        self.assertEqual(float(rows[0]["distance_m"]), 4.5)
        self.assertEqual(float(rows[0]["stroke_rate_spm"]), 19.0)
        self.assertEqual(result.report["row_count"], 549)
        self.assertEqual(result.report["positive_spm_rows"], 549)
        self.assertIn("SPM_PRESENT", result.report["quality_flags"])
        self.assertIn("GPS_PRESENT", result.report["quality_flags"])
        self.assertIn("TIMEZONE_UNKNOWN", result.report["quality_flags"])
        self.assertEqual(result.report["source_ref"], "upload/speedcoach.csv")
        self.assertEqual(len(result.report["input_sha256"]), 64)
        self.assertEqual(len(result.report["normalized_sha256"]), 64)

        schema = json.loads(
            (ROOT / "schemas/source-normalization-report.schema.json").read_text()
        )
        jsonschema.validate(instance=result.report, schema=schema)

    def test_mobile_sensor_export_preserves_missing_spm_as_missing(self) -> None:
        result = source_adapters.normalize_source(
            kind="MOBILE",
            content=(SOURCES / "mobile-ios-sensor.csv").read_bytes(),
            source_ref="upload/mobile.csv",
        )
        rows = normalized_rows(result.normalized_csv)

        self.assertEqual(result.source_format, "WAKE_MOBILE_SENSOR_CSV")
        self.assertEqual(len(rows), 923)
        self.assertEqual(float(rows[0]["elapsed_s"]), 0.0)
        self.assertTrue(rows[0]["timestamp"].endswith("+00:00"))
        self.assertEqual(rows[0]["stroke_rate_spm"], "")
        self.assertTrue(all(row["stroke_rate_spm"] == "" for row in rows))
        self.assertEqual(result.report["positive_spm_rows"], 0)
        self.assertIn("RAW_SPM_ABSENT", result.report["quality_flags"])
        self.assertNotIn("SPM_PRESENT", result.report["quality_flags"])
        self.assertEqual(result.report["gps_rows"], 923)

    def test_normalization_is_byte_deterministic(self) -> None:
        content = (SOURCES / "speedcoach.csv").read_bytes()

        first = source_adapters.normalize_source(
            kind="SPEEDCOACH", content=content, source_ref="speedcoach.csv"
        )
        second = source_adapters.normalize_source(
            kind="SPEEDCOACH", content=content, source_ref="speedcoach.csv"
        )

        self.assertEqual(first.normalized_csv, second.normalized_csv)
        self.assertEqual(first.report, second.report)

    def test_vendor_file_without_per_stroke_rows_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "per-stroke telemetry"):
            source_adapters.normalize_source(
                kind="SPEEDCOACH",
                content=b"Session Information:\nStart Time:,01/15/2026 06:59:50\n",
                source_ref="broken.csv",
            )

    def test_wrong_source_kind_is_not_reinterpreted(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported SPEEDCOACH"):
            source_adapters.normalize_source(
                kind="SPEEDCOACH",
                content=(SOURCES / "mobile-ios-sensor.csv").read_bytes(),
                source_ref="wrong.csv",
            )

    def test_non_finite_metrics_are_rejected_instead_of_poisoning_quality(self) -> None:
        content = (
            b"timestamp,elapsed_s,distance_m,speed_m_s,stroke_rate_spm\n"
            b"2026-01-15T07:00:00+00:00,0,NaN,2.5,20\n"
        )

        with self.assertRaisesRegex(ValueError, "no usable telemetry rows"):
            source_adapters.normalize_source(
                kind="SPEEDCOACH",
                content=content,
                source_ref="non-finite.csv",
            )


if __name__ == "__main__":
    unittest.main()
