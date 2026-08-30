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
    def test_concept2_fixed_distance_transcription_uses_cumulative_distance(self) -> None:
        content = (
            b"transcription_provenance,workout_type,row_kind,row_index,display_time_s,display_distance_m,pace_500m_s,stroke_rate_spm,heart_rate_bpm,watts\n"
            b"HUMAN_CONFIRMED,FIXED_DISTANCE,SPLIT,1,49.8,200,124.5,24,,\n"
            b"HUMAN_CONFIRMED,FIXED_DISTANCE,SPLIT,2,49.0,400,122.5,24,,\n"
            b"HUMAN_CONFIRMED,FIXED_DISTANCE,SPLIT,3,48.9,600,122.2,26,,\n"
        )

        result = source_adapters.normalize_source(
            kind="CONCEPT2",
            content=content,
            source_ref="upload/concept2-confirmed.csv",
        )
        rows = normalized_rows(result.normalized_csv)

        self.assertEqual(result.source_format, "CONCEPT2_PM5_TRANSCRIPTION_CSV")
        self.assertEqual([float(row["elapsed_s"]) for row in rows], [0.0, 49.8, 98.8, 147.7])
        self.assertEqual([float(row["distance_m"]) for row in rows], [0.0, 200.0, 400.0, 600.0])
        self.assertEqual([row["segment_kind"] for row in rows], ["ORIGIN", "WORK", "WORK", "WORK"])
        self.assertEqual(result.report["duration_s"], 147.7)
        self.assertEqual(result.report["max_distance_m"], 600.0)
        self.assertIn("CONCEPT2_SUMMARY_LEVEL", result.report["quality_flags"])
        self.assertIn("TRANSCRIPTION_HUMAN_CONFIRMED", result.report["quality_flags"])

        schema = json.loads(
            (ROOT / "schemas/source-normalization-report.schema.json").read_text()
        )
        jsonschema.validate(instance=result.report, schema=schema)

    def test_concept2_fixed_time_transcription_sums_split_distance(self) -> None:
        content = (
            b"transcription_provenance,workout_type,row_kind,row_index,display_time_s,display_distance_m,pace_500m_s,stroke_rate_spm,heart_rate_bpm,watts\n"
            b"HUMAN_CONFIRMED,FIXED_TIME,SPLIT,1,300,1011,148.3,20,,\n"
            b"HUMAN_CONFIRMED,FIXED_TIME,SPLIT,2,600,1005,149.2,20,,\n"
            b"HUMAN_CONFIRMED,FIXED_TIME,SPLIT,3,900,993,151.0,20,,\n"
        )

        result = source_adapters.normalize_source(
            kind="CONCEPT2",
            content=content,
            source_ref="upload/concept2-confirmed.csv",
        )
        rows = normalized_rows(result.normalized_csv)

        self.assertEqual([float(row["elapsed_s"]) for row in rows], [0.0, 300.0, 600.0, 900.0])
        self.assertEqual([float(row["distance_m"]) for row in rows], [0.0, 1011.0, 2016.0, 3009.0])
        self.assertAlmostEqual(float(rows[-1]["speed_m_s"]), 500 / 151.0, places=3)

    def test_concept2_interval_transcription_preserves_work_and_recovery(self) -> None:
        content = (
            b"transcription_provenance,workout_type,row_kind,row_index,display_time_s,display_distance_m,pace_500m_s,stroke_rate_spm,heart_rate_bpm,watts\n"
            b"HUMAN_CONFIRMED,INTERVAL,WORK,1,240,838,143.1,16,,\n"
            b"HUMAN_CONFIRMED,INTERVAL,RECOVERY,2,60,0,,,,\n"
            b"HUMAN_CONFIRMED,INTERVAL,WORK,3,180,643,139.9,18,,\n"
        )

        result = source_adapters.normalize_source(
            kind="CONCEPT2",
            content=content,
            source_ref="upload/concept2-confirmed.csv",
        )
        rows = normalized_rows(result.normalized_csv)

        self.assertEqual([row["segment_kind"] for row in rows], ["ORIGIN", "WORK", "RECOVERY", "WORK"])
        self.assertEqual(float(rows[-1]["elapsed_s"]), 480.0)
        self.assertEqual(float(rows[-1]["distance_m"]), 1481.0)
        self.assertIn("RECOVERY_ROWS_PRESENT", result.report["quality_flags"])

    def test_concept2_rejects_non_increasing_fixed_distance_markers(self) -> None:
        content = (
            b"transcription_provenance,workout_type,row_kind,row_index,display_time_s,display_distance_m,pace_500m_s,stroke_rate_spm,heart_rate_bpm,watts\n"
            b"HUMAN_CONFIRMED,FIXED_DISTANCE,SPLIT,1,60,200,150,20,,\n"
            b"HUMAN_CONFIRMED,FIXED_DISTANCE,SPLIT,2,60,200,150,20,,\n"
        )

        with self.assertRaisesRegex(ValueError, "strictly increasing distance"):
            source_adapters.normalize_source(
                kind="CONCEPT2",
                content=content,
                source_ref="broken.csv",
            )

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
