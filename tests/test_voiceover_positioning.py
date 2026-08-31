from __future__ import annotations

import unittest
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VOICEOVER_FILES = (
    ROOT / "docs" / "VIDEO_DEMO_SCRIPT.md",
    ROOT / "submission" / "video" / "VOICEOVER_ELEVENLABS_V3.md",
    ROOT / "submission" / "video" / "VOICEOVER_ELEVENLABS_V4_REGENERATE.md",
    ROOT / "submission" / "video" / "VOICEOVER_ELEVENLABS_V5_REGENERATE.md",
)


class VoiceoverPositioningTests(unittest.TestCase):
    def test_spm_source_copy_is_metric_and_session_specific(self) -> None:
        for path in VOICEOVER_FILES:
            copy = path.read_text(encoding="utf-8")
            normalized_copy = re.sub(r"\s+", " ", copy.replace("> ", ""))
            with self.subTest(path=path.name):
                self.assertNotIn(
                    "rejects the phone's zero-only stroke-rate signal",
                    normalized_copy,
                )
                self.assertIn(
                    "compares signal coverage and consistency",
                    normalized_copy,
                )
                self.assertIn("for that session", normalized_copy)
                self.assertIn("it could be mobile", normalized_copy)


if __name__ == "__main__":
    unittest.main()
