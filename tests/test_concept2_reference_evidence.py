from __future__ import annotations

import csv
import io
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import source_adapters  # noqa: E402


REFERENCE_ROOT = ROOT / "docs/evidence/concept2-real-reference"


class Concept2ReferenceEvidenceTests(unittest.TestCase):
    def test_confirmed_reference_transcriptions_normalize_without_ocr(self) -> None:
        transcription_paths = sorted((REFERENCE_ROOT / "transcriptions").glob("*.csv"))

        self.assertEqual(len(transcription_paths), 5)
        workout_types = set()
        for path in transcription_paths:
            source_rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
            workout_types.update(row["workout_type"] for row in source_rows)
            result = source_adapters.normalize_source(
                kind="CONCEPT2",
                content=path.read_bytes(),
                source_ref=f"reference/{path.name}",
            )
            self.assertEqual(result.source_format, "CONCEPT2_PM5_TRANSCRIPTION_CSV")
            self.assertIn("TRANSCRIPTION_HUMAN_CONFIRMED", result.report["quality_flags"])

        self.assertEqual(workout_types, {"FIXED_DISTANCE", "FIXED_TIME", "INTERVAL"})

    def test_public_reference_images_are_minimized_and_metadata_stripped(self) -> None:
        image_paths = sorted((REFERENCE_ROOT / "images").glob("*.jpg"))

        self.assertEqual(len(image_paths), 4)
        for path in image_paths:
            content = path.read_bytes()
            self.assertNotIn(b"Exif\x00\x00", content)
            self.assertNotIn(b"/Users/", content)

        readme = (REFERENCE_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("ANONYMIZED_REAL_REFERENCE", readme)
        self.assertIn("Automatic image OCR is not implemented", readme)
        self.assertIn("No athlete identity", readme)


if __name__ == "__main__":
    unittest.main()
