from __future__ import annotations

import importlib.util
import inspect
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_submission_captions.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_submission_captions", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SubmissionCaptionTests(unittest.TestCase):
    def test_captions_cover_the_spoken_story_and_accessibility_boundary(self) -> None:
        builder = load_builder()
        cues = builder.build_cues()

        self.assertGreaterEqual(len(cues), 40)
        self.assertGreaterEqual(cues[0].start, 4.4)
        self.assertGreater(cues[0].start, builder.BRAND_ONLY_END_SECONDS)
        self.assertLessEqual(cues[11].end, 62.5)
        self.assertGreaterEqual(cues[12].start, builder.CHAPTER_TWO_START_SECONDS)
        self.assertGreaterEqual(cues[-1].end, 293.0)
        self.assertTrue(all(left.end <= right.start for left, right in zip(cues, cues[1:])))
        self.assertTrue(all(cue.end > cue.start for cue in cues))
        self.assertTrue(all(cue.end - cue.start <= 8.0 for cue in cues))
        self.assertTrue(all(len(cue.lines) <= 2 for cue in cues))
        self.assertTrue(all(len(line) <= 48 for cue in cues for line in cue.lines))

        text = "\n".join(line for cue in cues for line in cue.lines)
        self.assertNotIn("[short pause]", text)
        self.assertIn("removed that behavior", text)
        self.assertIn("no quality gain", text)

    def test_srt_output_is_valid_and_names_the_negative_experiment(self) -> None:
        builder = load_builder()
        srt = builder.render_srt(builder.build_cues())

        self.assertTrue(srt.startswith("1\n00:00:04,490 -->"))
        self.assertIn("We also preserved a longitudinal experiment", srt)
        self.assertIn("that showed no quality gain.", srt)
        self.assertTrue(srt.endswith("\n"))

    def test_burned_caption_overlay_is_legible_and_does_not_require_libass(self) -> None:
        builder = load_builder()

        self.assertGreaterEqual(builder.CAPTION_FONT_SIZE, 40)
        self.assertGreaterEqual(builder.CAPTION_MARGIN_V, 34)
        svg = builder.render_caption_svg(("Evidence first.", "Questions stay questions."))
        self.assertIn('fill-opacity="0.82"', svg)
        self.assertIn(f'font-size="{builder.CAPTION_FONT_SIZE}"', svg)
        self.assertIn("Evidence first.", svg)

        events = builder.build_overlay_events(builder.build_cues())
        self.assertEqual(events[0], (0.0, ()))
        self.assertEqual(events[-1], (293.021, ()))
        self.assertNotIn("subtitles=", inspect.getsource(builder.burn_captions))


if __name__ == "__main__":
    unittest.main()
