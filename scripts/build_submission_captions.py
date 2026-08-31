#!/usr/bin/env python3
"""Create English accessibility captions and optionally burn them into WAKE video."""

from __future__ import annotations

import argparse
import html
import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple


CAPTION_FONT_SIZE = 42
CAPTION_MARGIN_V = 38
VIDEO_DURATION_SECONDS = 298.4
BRAND_ONLY_END_SECONDS = 3.8
CHAPTER_ONE_AUDIO_START_SECONDS = 3.85
CHAPTER_TWO_START_SECONDS = 63.0


class CaptionCue(NamedTuple):
    start: float
    end: float
    lines: tuple[str, ...]


def cue(start: float, end: float, *lines: str) -> CaptionCue:
    return CaptionCue(start, end, tuple(lines))


def chapter_one_cue(start: float, end: float, *lines: str) -> CaptionCue:
    return cue(
        start + CHAPTER_ONE_AUDIO_START_SECONDS,
        end + CHAPTER_ONE_AUDIO_START_SECONDS,
        *lines,
    )


def build_cues() -> list[CaptionCue]:
    return [
        chapter_one_cue(0.640, 3.075, "In a rowing club, the plan may arrive", "through a messaging app."),
        chapter_one_cue(3.978, 7.011, "The SpeedCoach file usually stays", "with the athlete."),
        chapter_one_cue(7.887, 10.470, "Another phone may record the route."),
        chapter_one_cue(11.599, 16.574, "The coach knows the crew and conditions,", "but cannot follow every boat every day."),
        chapter_one_cue(16.872, 22.419, "A spreadsheet organizes the files,", "and a simple baseline summarizes one session."),
        chapter_one_cue(22.669, 28.694, "Neither preserves the questions, relationships,", "and decisions that accumulate across the club."),
        chapter_one_cue(28.904, 32.558, "That is the problem WAKE was built to solve.", "WAKE begins at club scale."),
        chapter_one_cue(34.865, 39.978, "The coach sees reconstructed sessions", "and which crews went out."),
        chapter_one_cue(40.480, 42.990, "Which records need a source,", "and which questions need a person."),
        chapter_one_cue(43.444, 48.660, "Here, one men's double is connected", "to its physical boat, lineup, and outings."),
        chapter_one_cue(49.767, 55.102, "Missing training is something to investigate,", "not a judgment about commitment,"),
        chapter_one_cue(56.058, 58.515, "fitness, or injury."),
        cue(CHAPTER_TWO_START_SECONDS, 65.920, "Did the crew execute the six one-kilometer", "pieces at the prescribed stroke rates?"),
        cue(66.815, 72.291, "The training plan and SpeedCoach", "are enough to begin."),
        cue(73.385, 78.616, "Mobile telemetry, weather, and human context", "can improve the review, but are optional."),
        cue(78.890, 83.934, "WAKE uses one bounded investigation agent.", "It chooses the next useful action."),
        cue(85.051, 92.113, "Four deterministic tools handle source trust,", "alignment, reconstruction, and environment."),
        cue(92.495, 97.139, "A verifier checks every claim and source", "before the coach sees it."),
        cue(97.900, 102.243, "WAKE reconstructs all six work pieces", "and finds that most followed the plan."),
        cue(103.784, 108.652, "One interval still needs attention."),
        cue(109.120, 114.424, "WAKE compares coverage and consistency", "to select stroke-rate authority."),
        cue(114.901, 118.542, "Here, that is SpeedCoach;", "in another session, it could be mobile."),
        cue(119.278, 123.215, "The wind changed during the row,", "but WAKE does not call it the cause."),
        cue(124.445, 128.798, "Devices cannot tell whether the resistance band", "was removed after repetition three."),
        cue(129.057, 133.722, "That question belongs to the athlete", "or someone who directly observed the session."),
        cue(134.292, 139.616, "WAKE records who answered, who entered it,", "and why that person has authority."),
        cue(142.353, 146.064, "The answer adds context.", "It never rewrites the telemetry."),
        cue(146.676, 152.973, "Only explicit coach approval", "turns the briefing into club memory."),
        cue(153.396, 157.397, "One session is manageable.", "The real problem appears when more data arrives."),
        cue(157.397, 163.426, "WAKE connects 102 activities", "for the same 16 athletes and 10 crews."),
        cue(164.166, 170.410, "It separates comparable progress, slower work,", "stable execution, and weather-confounded rows."),
        cue(170.410, 176.883, "It also keeps missing participation", "and non-comparable cases visible."),
        cue(178.919, 184.551, "For Lucas, Training Days connect", "crew outings, solo rows, and Concept2 work."),
        cue(184.551, 190.357, "Indoor meters never become water distance", "as if they were the same thing."),
        cue(190.751, 196.909, "The saved briefing gives the coach", "priorities and focused questions."),
        cue(197.254, 202.295, "It does not invent a trend", "just because more data exists."),
        cue(202.295, 205.868, "Reopening verified memory costs zero dollars."),
        cue(206.388, 211.527, "Training eventually meets competition.", "Competition Review connects the same athletes,"),
        cue(211.881, 216.881, "crew snapshot, physical boat, shared outings,", "and the complete race field."),
        cue(217.096, 224.255, "The coach sees the path and result together,", "without claiming one workout caused the finish."),
        cue(224.664, 227.298, "WAKE does not select crews automatically."),
        cue(227.298, 231.600, "When a result is missing,", "WAKE asks for context"),
        cue(231.600, 236.126, "instead of inventing one."),
        cue(236.708, 241.321, "We tested WAKE against the same baseline", "on ten frozen cases."),
        cue(242.117, 246.751, "The baseline scored 49.00.", "WAKE scored 83.76."),
        cue(247.058, 253.231, "Every case improved overall, while environmental", "interpretation regressed from 80 to 76 percent."),
        cue(254.652, 258.324, "This supports a stronger fixed-case workflow,", "not superiority to a coach or athletic gains."),
        cue(258.977, 261.063, "The most useful change came from a failure."),
        cue(261.403, 265.828, "Early WAKE treated reconstructed distance", "as proof that prescribed distance was completed."),
        cue(266.438, 272.082, "We removed that behavior, wrote a failing test,", "changed the boundary, and reran evaluation."),
        cue(272.812, 277.645, "We also preserved a longitudinal experiment", "that showed no quality gain."),
        cue(278.001, 283.311, "Our history includes what did not work,", "not only the wins."),
        cue(283.679, 285.373, "Every row leaves a wake."),
        cue(285.972, 293.021, "WAKE turns fragmented training into memory", "a coach and athlete can use together."),
    ]


def format_srt_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def render_srt(cues: list[CaptionCue]) -> str:
    blocks = []
    for index, item in enumerate(cues, start=1):
        blocks.append(
            f"{index}\n{format_srt_timestamp(item.start)} --> "
            f"{format_srt_timestamp(item.end)}\n" + "\n".join(item.lines)
        )
    return "\n\n".join(blocks) + "\n"


def render_caption_svg(lines: tuple[str, ...]) -> str:
    if not lines:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080"/>'
    box_height = 92 if len(lines) == 1 else 148
    box_y = 1080 - CAPTION_MARGIN_V - box_height
    text_start = box_y + 58
    rendered_lines = "".join(
        (
            f'<text x="960" y="{text_start + index * 54}" '
            'text-anchor="middle" font-family="Helvetica, Arial, sans-serif" '
            f'font-size="{CAPTION_FONT_SIZE}" font-weight="600" fill="#ffffff">'
            f"{html.escape(line)}</text>"
        )
        for index, line in enumerate(lines)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <rect x="150" y="{box_y}" width="1620" height="{box_height}" rx="18" fill="#071d1a" fill-opacity="0.82"/>
  {rendered_lines}
</svg>'''


def build_overlay_events(cues: list[CaptionCue]) -> list[tuple[float, tuple[str, ...]]]:
    events: list[tuple[float, tuple[str, ...]]] = [(0.0, ())]
    for item in cues:
        events.append((item.start, item.lines))
        events.append((item.end, ()))
    return events


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def burn_captions(source: Path, srt: Path, output: Path) -> None:
    cues = build_cues()
    if render_srt(cues) != srt.read_text(encoding="utf-8"):
        raise ValueError("The SRT does not match the versioned WAKE caption cues")
    with tempfile.TemporaryDirectory(prefix="wake-caption-overlay-") as temporary:
        work = Path(temporary)
        events = build_overlay_events(cues)
        images: list[Path] = []
        for index, (_, lines) in enumerate(events):
            svg = work / f"caption-{index:03d}.svg"
            png = svg.with_suffix(".png")
            svg.write_text(render_caption_svg(lines), encoding="utf-8")
            run(["rsvg-convert", str(svg), "-o", str(png)])
            images.append(png)

        concat_lines: list[str] = []
        for index, ((timestamp, _), image) in enumerate(zip(events, images)):
            next_timestamp = (
                events[index + 1][0]
                if index + 1 < len(events)
                else VIDEO_DURATION_SECONDS
            )
            concat_lines.append(f"file '{image}'")
            concat_lines.append(f"duration {next_timestamp - timestamp:.6f}")
        concat_lines.append(f"file '{images[-1]}'")
        concat = work / "caption-states.txt"
        concat.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

        overlay_video = work / "caption-overlay.mov"
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat),
                "-fps_mode",
                "vfr",
                "-c:v",
                "qtrle",
                "-pix_fmt",
                "argb",
                str(overlay_video),
            ]
        )
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(source),
                "-i",
                str(overlay_video),
                "-filter_complex",
                "[0:v][1:v]overlay=0:0:format=auto[out]",
                "-map",
                "[out]",
                "-map",
                "0:a:0",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-c:a",
                "copy",
                "-shortest",
                "-movflags",
                "+faststart",
                str(output),
            ]
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--srt", required=True, type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.srt.parent.mkdir(parents=True, exist_ok=True)
    args.srt.write_text(render_srt(build_cues()), encoding="utf-8")
    if (args.source is None) != (args.output is None):
        raise SystemExit("--source and --output must be provided together")
    if args.source is not None and args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        burn_captions(args.source, args.srt, args.output)
        print(args.output)
    else:
        print(args.srt)


if __name__ == "__main__":
    main()
