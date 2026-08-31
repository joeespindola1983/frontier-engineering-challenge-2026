from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "rebuild_submission_audio.py"


def load_rebuilder():
    spec = importlib.util.spec_from_file_location("rebuild_submission_audio", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SubmissionAudioRebuildTests(unittest.TestCase):
    def test_chapter_two_finishes_before_the_original_human_checkpoint(self) -> None:
        rebuilder = load_rebuilder()

        self.assertEqual(rebuilder.CHAPTER_ONE_START_SECONDS, 3.85)
        self.assertEqual(rebuilder.CHAPTER_TWO_START_SECONDS, 63.0)
        self.assertEqual(rebuilder.CHAPTER_THREE_START_SECONDS, 122.967)
        self.assertEqual(rebuilder.CHAPTER_TRANSITION_GAP_SECONDS, 0.15)
        self.assertAlmostEqual(rebuilder.CHAPTER_TWO_TARGET_SECONDS, 59.817)

    def test_audio_graph_uses_original_chapters_and_preserves_a_tail(self) -> None:
        rebuilder = load_rebuilder()
        graph = rebuilder.audio_filter(
            chapter_one_duration=58.671,
            cleaned_chapter_two_duration=61.002,
        )

        self.assertIn("atrim=start=0:end=3.85", graph)
        self.assertIn("atrim=duration=59.817", graph)
        self.assertIn("anullsrc=r=48000:cl=mono", graph)
        self.assertIn("concat=n=11:v=0:a=1", graph)
        self.assertIn("atrim=duration=0.6", graph)
        self.assertNotIn("tpad", graph)
        self.assertFalse(rebuilder.TRIM_VIDEO_TO_AUDIO)

    def test_chapter_two_cleanup_is_bounded_and_does_not_remove_words(self) -> None:
        rebuilder = load_rebuilder()

        cleanup = rebuilder.chapter_two_cleanup_filter()
        self.assertIn("silenceremove", cleanup)
        self.assertIn("stop_duration=0.25", cleanup)
        self.assertIn("stop_silence=0.20", cleanup)
        self.assertGreater(rebuilder.tempo_for_chapter_two(61.002), 1.0)
        self.assertLess(rebuilder.tempo_for_chapter_two(61.002), 1.03)


if __name__ == "__main__":
    unittest.main()
