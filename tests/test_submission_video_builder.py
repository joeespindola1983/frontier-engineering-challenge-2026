from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "build_submission_video.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_submission_video", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SubmissionVideoBuilderTests(unittest.TestCase):
    def test_product_capture_dominates_the_reframed_video(self) -> None:
        builder = load_builder()

        self.assertGreaterEqual(builder.PRODUCT_WIDTH_RATIO, 0.74)
        self.assertLessEqual(builder.PRODUCT_WIDTH_RATIO, 0.78)
        self.assertGreaterEqual(builder.TEXT_PANEL_WIDTH_RATIO, 0.22)
        self.assertLessEqual(builder.TEXT_PANEL_WIDTH_RATIO, 0.26)
        self.assertEqual(
            builder.PRODUCT_WIDTH_RATIO + builder.TEXT_PANEL_WIDTH_RATIO,
            1.0,
        )
        self.assertEqual(builder.CAPTURE_ASPECT_RATIO, 4 / 3)
        self.assertFalse(builder.MUX_TRIMS_TO_SOURCE_AUDIO)

    def test_replacement_timeline_is_complete_and_uses_current_captures(self) -> None:
        builder = load_builder()
        timeline = builder.build_timeline(Path("/captures"))

        self.assertEqual(timeline[0].start, 0)
        self.assertEqual(timeline[-1].end, builder.SOURCE_DURATION_SECONDS)
        self.assertTrue(
            all(left.end == right.start for left, right in zip(timeline, timeline[1:]))
        )

        image_names = {
            segment.source.name for segment in timeline if segment.kind == "image"
        }
        self.assertIn("intake-selected-bottom.jpg", image_names)
        self.assertIn("crew-tucano.jpg", image_names)
        self.assertIn("competition-tucano.jpg", image_names)
        self.assertIn("evaluation-clean.jpg", image_names)

    def test_contextual_navigation_finishes_each_cursor_action_before_the_destination(self) -> None:
        builder = load_builder()
        timeline = builder.build_timeline(Path("/captures"))
        cursor_segments = [segment for segment in timeline if segment.kind == "cursor"]

        self.assertEqual(
            [segment.source.name for segment in cursor_segments],
            [
                "overview-clean.jpg",
                "team-tucano-target.jpg",
                "overview-clean.jpg",
                "team-tucano-target.jpg",
                "crew-tucano.jpg",
                "athlete-lucas.jpg",
                "memory-approved.jpg",
                "competition-clean.jpg",
                "competition-tucano.jpg",
            ],
        )
        for segment in cursor_segments:
            duration = segment.end - segment.start
            self.assertIsNotNone(segment.cursor_from)
            self.assertIsNotNone(segment.cursor_to)
            self.assertGreaterEqual(segment.cursor_travel, 1.25)
            self.assertGreater(duration, segment.cursor_travel)

        self.assertFalse(builder.SHOW_CLICK_PULSE)

        destinations = {
            50.0: "team-tucano-target.jpg",
            54.0: "crew-tucano.jpg",
            157.377: "team-tucano-target.jpg",
            175.5: "crew-tucano.jpg",
            178.899: "athlete-lucas.jpg",
            190.0: "memory-approved.jpg",
            203.921: "competition-clean.jpg",
            206.374: "competition-tucano.jpg",
            231.245: "evaluation-clean.jpg",
        }
        for cursor_segment in cursor_segments:
            destination = next(
                segment for segment in timeline if segment.start == cursor_segment.end
            )
            self.assertEqual(destination.source.name, destinations[cursor_segment.end])

    def test_agentic_interlude_has_no_legacy_source_frame_or_clipped_connections(self) -> None:
        builder = load_builder()
        timeline = builder.build_timeline(Path("/captures"))
        agentic = [segment for segment in timeline if segment.kind == "agentic"]

        self.assertEqual(len(agentic), 1)
        self.assertEqual((agentic[0].start, agentic[0].end), (82.661, 107.083))
        self.assertEqual(agentic[0].source.name, "agentic-flow.svg")

        svg = (ROOT / "submission" / "video" / "motion-ui" / "agentic-flow.svg").read_text(
            encoding="utf-8"
        )
        for connection_id in (
            "agent-to-tools",
            "tools-to-verifier",
            "verifier-to-human",
        ):
            self.assertIn(f'id="{connection_id}"', svg)

    def test_review_story_uses_three_distinct_subject_focused_captures(self) -> None:
        builder = load_builder()
        timeline = builder.build_timeline(Path("/captures"))
        focused = [
            segment.source.name
            for segment in timeline
            if 109.0 <= segment.start < 135.0
        ]

        self.assertEqual(
            focused,
            [
                "review-source-trust-tight.jpg",
                "review-environment-boundary.jpg",
                "review-human-answer-full.jpg",
            ],
        )
        self.assertEqual(len(focused), len(set(focused)))

    def test_submission_timeline_uses_focus_clean_navigation_captures(self) -> None:
        builder = load_builder()
        timeline = builder.build_timeline(Path("/captures"))
        source_names = [segment.source.name for segment in timeline]

        self.assertIn("overview-clean.jpg", source_names)
        self.assertIn("competition-clean.jpg", source_names)
        self.assertIn("evaluation-clean.jpg", source_names)
        self.assertNotIn("overview-1440.jpg", source_names)
        self.assertNotIn("competition-top.jpg", source_names)
        self.assertNotIn("evaluation-top.jpg", source_names)

    def test_ending_visibly_names_removed_and_negative_experiments(self) -> None:
        builder = load_builder()
        timeline = builder.build_timeline(Path("/captures"))
        learning = [segment for segment in timeline if segment.kind == "motion"]

        self.assertEqual(
            [(segment.start, segment.end, segment.source.name) for segment in learning],
            [
                (263.271, 280.663, "removed-behavior.svg"),
                (280.663, 291.414, "negative-experiment.svg"),
            ],
        )
        final_source = timeline[-1]
        self.assertEqual((final_source.start, final_source.end), (291.414, builder.SOURCE_DURATION_SECONDS))

        removed = (builder.MOTION_UI_DIR / "removed-behavior.svg").read_text(
            encoding="utf-8"
        )
        negative = (builder.MOTION_UI_DIR / "negative-experiment.svg").read_text(
            encoding="utf-8"
        )
        self.assertIn("REMOVED BEHAVIOR", removed)
        self.assertIn("NEGATIVE EXPERIMENT", negative)
        self.assertIn("NO DEMONSTRATED QUALITY GAIN", negative)

    def test_visual_subject_changes_follow_complete_spoken_ideas(self) -> None:
        builder = load_builder()
        timeline = builder.build_timeline(Path("/captures"))

        expected_subject_starts = {
            "intake-selected-top.jpg": 63.0,
            "intake-selected-bottom.jpg": 72.123,
            "agentic-flow.svg": 82.661,
            "review-top.jpg": 107.083,
            "review-source-trust-tight.jpg": 114.1,
            "review-environment-boundary.jpg": 120.237,
            "review-human-answer-full.jpg": 123.16,
            "briefing-top.jpg": 142.353,
            "memory-approved.jpg": 146.676,
            "overview-clean.jpg": 151.415,
            "athlete-lucas.jpg": 178.899,
            "competition-clean.jpg": 203.921,
            "competition-tucano.jpg": 206.374,
            "evaluation-clean.jpg": 231.245,
            "removed-behavior.svg": 263.271,
            "negative-experiment.svg": 280.663,
        }

        for source_name, expected_start in expected_subject_starts.items():
            matching = [
                segment
                for segment in timeline
                if segment.source.name == source_name and segment.start == expected_start
            ]
            self.assertTrue(
                matching,
                f"{source_name} must begin with its matching spoken idea at {expected_start}",
            )

    def test_narrative_panel_copy_is_short(self) -> None:
        builder = load_builder()

        for segment in builder.build_timeline(Path("/captures")):
            self.assertLessEqual(len(segment.eyebrow), 24)
            self.assertLessEqual(len(segment.title_lines), 3)
            self.assertTrue(all(len(line) <= 22 for line in segment.title_lines))
            if segment.kind == "image":
                self.assertGreaterEqual(len(segment.description_lines), 2)
                self.assertLessEqual(len(segment.description_lines), 4)
                self.assertTrue(
                    all(len(line) <= 34 for line in segment.description_lines)
                )

    def test_panel_does_not_depend_on_unavailable_ffmpeg_drawtext(self) -> None:
        builder = load_builder()
        segment = builder.build_timeline(Path("/captures"))[1]

        self.assertNotIn("drawtext", builder.image_filter())
        svg = builder.render_panel_svg(segment)
        self.assertIn(segment.eyebrow, svg)
        self.assertIn(segment.title_lines[0], svg)

    def test_product_and_panel_widths_fill_an_even_h264_canvas(self) -> None:
        builder = load_builder()
        product_width, panel_width = builder.layout_widths()

        self.assertEqual(product_width + panel_width, builder.CANVAS_WIDTH)
        self.assertEqual(product_width % 2, 0)
        self.assertEqual(panel_width % 2, 0)


if __name__ == "__main__":
    unittest.main()
