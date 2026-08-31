from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "replace_submission_video_audio.py"


def load_audio_replacer():
    spec = importlib.util.spec_from_file_location(
        "replace_submission_video_audio",
        MODULE_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SubmissionVideoAudioTests(unittest.TestCase):
    def test_chapter_two_replacement_preserves_the_video_timeline(self) -> None:
        replacer = load_audio_replacer()

        self.assertEqual(replacer.CHAPTER_START_SECONDS, 63.0)
        self.assertEqual(replacer.CHAPTER_END_SECONDS, 129.0)
        self.assertEqual(replacer.CHAPTER_TARGET_SECONDS, 66.0)

    def test_tempo_adjustment_is_bounded_and_nearly_imperceptible(self) -> None:
        replacer = load_audio_replacer()

        tempo = replacer.tempo_for_duration(66.351)

        self.assertAlmostEqual(tempo, 66.351 / 66.0, places=6)
        self.assertGreaterEqual(tempo, 0.95)
        self.assertLessEqual(tempo, 1.05)

    def test_filter_replaces_only_chapter_two_and_normalizes_audio_shape(self) -> None:
        replacer = load_audio_replacer()

        graph = replacer.audio_filter(66.351)

        self.assertIn("atrim=start=0:end=63.0", graph)
        self.assertIn("atrim=start=129.0", graph)
        self.assertIn("aresample=48000", graph)
        self.assertIn("atempo=1.005318", graph)
        self.assertIn("concat=n=3:v=0:a=1", graph)


if __name__ == "__main__":
    unittest.main()
