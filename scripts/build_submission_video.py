#!/usr/bin/env python3
"""Reframe the current WAKE interface captures over the accepted narration.

The source draft supplies the accepted audio, brand animation, agent-workflow
interlude, and closing. Current browser captures replace the product chapters.
No model call or network request is made by this script.
"""

from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import NamedTuple


CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
PRODUCT_WIDTH_RATIO = 0.76
TEXT_PANEL_WIDTH_RATIO = 0.24
CAPTURE_ASPECT_RATIO = 4 / 3
SOURCE_DURATION_SECONDS = 299.1
FRAME_RATE = 30
FONT_PATH = Path("/System/Library/Fonts/Helvetica.ttc")
MOTION_UI_DIR = Path(__file__).resolve().parents[1] / "submission" / "video" / "motion-ui"
AGENTIC_FLOW_SVG = MOTION_UI_DIR / "agentic-flow.svg"
CURSOR_SVG = MOTION_UI_DIR / "cursor.svg"
CLICK_RING_SVG = MOTION_UI_DIR / "click-ring.svg"
SHOW_CLICK_PULSE = False
MUX_TRIMS_TO_SOURCE_AUDIO = False


class Segment(NamedTuple):
    start: float
    end: float
    kind: str
    source: Path
    eyebrow: str = ""
    title_lines: tuple[str, ...] = ()
    description_lines: tuple[str, ...] = ()
    cursor_from: tuple[int, int] | None = None
    cursor_to: tuple[int, int] | None = None
    cursor_travel: float = 0.0
    click_at: float = 0.0


def build_timeline(capture_dir: Path) -> list[Segment]:
    source = Path("__source_video__")
    return [
        Segment(0, 47.5, "video", source),
        Segment(47.5, 50, "cursor", capture_dir / "overview-clean.jpg", "CLUB NAVIGATION", ("Open team", "and crew context"), ("Move from the club pulse", "to the recurring lineups", "behind the activity."), (1120, 470), (730, 108), 1.55, 1.75),
        Segment(50, 54, "cursor", capture_dir / "team-tucano-target.jpg", "ONE LINEUP", ("Crew: Tucano", "2x · Men"), ("The name, physical boat,", "athletes, and outings remain", "connected."), (1080, 280), (400, 666), 2.0, 2.3),
        Segment(54, 63, "image", capture_dir / "crew-tucano.jpg", "CREW MEMORY", ("Crew, boat,", "athletes, outings"), ("A recurring lineup keeps its", "shared work and individual", "training connected.")),
        Segment(63, 72.123, "image", capture_dir / "intake-selected-top.jpg", "SESSION INTAKE", ("Evidence from", "both roles"), ("Athletes and coaches can both", "contribute files. Source authority", "remains explicit.")),
        Segment(72.123, 82.661, "image", capture_dir / "intake-selected-bottom.jpg", "EVIDENCE READY", ("Core inputs", "stay clear"), ("Plan and SpeedCoach start the", "review. Optional evidence expands", "what WAKE can verify.")),
        Segment(82.661, 107.083, "agentic", AGENTIC_FLOW_SVG),
        Segment(107.083, 114.1, "image", capture_dir / "review-top.jpg", "INVESTIGATION", ("Reconstruct", "the session"), ("The agent aligns recordings,", "compares the plan, and isolates", "the interval needing review.")),
        Segment(114.1, 120.237, "image", capture_dir / "review-source-trust-tight.jpg", "SOURCE TRUST", ("One authority", "per claim"), ("Stroke rate, route, distance,", "and conditions can each trust", "a different source.")),
        Segment(120.237, 123.16, "image", capture_dir / "review-environment-boundary.jpg", "UNCERTAINTY", ("Keep missing", "context visible"), ("Conditions can contextualize", "a result without becoming", "an unsupported cause.")),
        Segment(123.16, 142.353, "image", capture_dir / "review-human-answer-full.jpg", "HUMAN CHECKPOINT", ("Ask the person", "who knows"), ("One attributed answer can change", "the briefing without rewriting", "the measured evidence.")),
        Segment(142.353, 146.676, "image", capture_dir / "briefing-top.jpg", "VERIFIED BRIEFING", ("Findings and", "boundaries"), ("The coach receives findings,", "limitations, and evidence names", "in one readable result.")),
        Segment(146.676, 151.415, "image", capture_dir / "memory-approved.jpg", "COACH APPROVAL", ("Save reviewed", "memory only"), ("A session enters club memory", "only after explicit human", "approval.")),
        Segment(151.415, 154.0, "image", capture_dir / "overview-clean.jpg", "CLUB SCALE", ("102 activities", "connected"), ("Deterministic processing handles", "the combined batch before paid", "investigations are selected.")),
        Segment(154.0, 157.377, "cursor", capture_dir / "overview-clean.jpg", "CLUB SCALE", ("Open team", "context"), ("Move from the club pulse", "to the recurring lineups", "behind the activity."), (1120, 470), (730, 108), 1.8, 2.1),
        Segment(157.377, 172.443, "image", capture_dir / "team-tucano-target.jpg", "TEAM CONTEXT", ("Ten recurring", "lineups"), ("WAKE links sixteen athletes,", "ten crews, and physical boats", "across both training periods.")),
        Segment(172.443, 175.5, "cursor", capture_dir / "team-tucano-target.jpg", "TEAM CONTEXT", ("Open Crew:", "Tucano"), ("Follow one recurring lineup", "into its shared outings and", "athlete links."), (1080, 280), (400, 666), 1.7, 2.0),
        Segment(175.5, 178.899, "cursor", capture_dir / "crew-tucano.jpg", "ATHLETE PATH", ("Open Lucas", "from the lineup"), ("The crew report keeps each", "athlete connected to their", "own training chronology."), (1110, 390), (850, 828), 1.8, 2.1),
        Segment(178.899, 187.0, "image", capture_dir / "athlete-lucas.jpg", "ATHLETE HISTORY", ("Water, crew,", "solo, indoor"), ("One chronology separates water", "and Concept2 evidence while", "preserving the full training day.")),
        Segment(187.0, 190.0, "cursor", capture_dir / "athlete-lucas.jpg", "ATHLETE HISTORY", ("Open Goal", "memory"), ("Move from one athlete's record", "to reviewed knowledge preserved", "for the club."), (1110, 470), (420, 38), 1.8, 2.1),
        Segment(190.0, 200.5, "image", capture_dir / "memory-approved.jpg", "LONGITUDINAL", ("Reopen at", "zero model cost"), ("Saved verified reports can be", "reviewed again without another", "model call.")),
        Segment(200.5, 203.921, "cursor", capture_dir / "memory-approved.jpg", "LONGITUDINAL", ("Open the", "competition"), ("Carry reviewed training context", "forward to the official race", "outcome."), (1110, 650), (300, 38), 1.8, 2.1),
        Segment(203.921, 206.374, "cursor", capture_dir / "competition-clean.jpg", "COMPETITION", ("Open one", "boat report"), ("Select Tucano to inspect the", "lineup, official result, field,", "and pre-race context."), (1050, 350), (955, 810), 1.4, 1.7),
        Segment(206.374, 228.0, "image", capture_dir / "competition-tucano.jpg", "BOAT REPORT", ("Crew, boat,", "and full field"), ("Each entry retains its lineup,", "official rank, opposition, and", "pre-race context.")),
        Segment(228.0, 231.245, "cursor", capture_dir / "competition-tucano.jpg", "BOAT REPORT", ("Open the", "evaluation"), ("Move from the product story", "to controlled evidence of how", "the workflow performed."), (1110, 450), (535, 38), 1.8, 2.1),
        Segment(231.245, 254.629, "image", capture_dir / "evaluation-clean.jpg", "MEASURED EVIDENCE", ("Same ten", "sessions"), ("Ten controlled cases compare", "the same model and evidence with", "and without WAKE's workflow.")),
        Segment(254.629, 263.271, "image", capture_dir / "evaluation-clean.jpg", "HONEST RESULT", ("Gains and", "regressions"), ("40 tool calls and 10 verified", "trajectories cost about US$1.14", "for the full comparison.")),
        Segment(263.271, 280.663, "motion", MOTION_UI_DIR / "removed-behavior.svg"),
        Segment(280.663, 291.414, "motion", MOTION_UI_DIR / "negative-experiment.svg"),
        Segment(291.414, SOURCE_DURATION_SECONDS, "video", source),
    ]


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def layout_widths() -> tuple[int, int]:
    product_width = int(CANVAS_WIDTH * PRODUCT_WIDTH_RATIO)
    if product_width % 2:
        product_width -= 1
    return product_width, CANVAS_WIDTH - product_width


def image_filter() -> str:
    product_width, _ = layout_widths()
    return ",".join(
        [
        f"scale={product_width}:{CANVAS_HEIGHT}:force_original_aspect_ratio=decrease",
        f"pad={product_width}:{CANVAS_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=0xf5f5f0",
        (
            "zoompan="
            "z='min(zoom+0.00006,1.018)':"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d=1:s={product_width}x{CANVAS_HEIGHT}:fps={FRAME_RATE}"
        ),
        "format=yuv420p",
        ]
    )


def render_panel_svg(segment: Segment) -> str:
    _, panel_width = layout_widths()
    title = "".join(
        f'<text x="34" y="{190 + index * 52}" class="title">{html.escape(line)}</text>'
        for index, line in enumerate(segment.title_lines)
    )
    description = "".join(
        f'<text x="34" y="{390 + index * 34}" class="description">{html.escape(line)}</text>'
        for index, line in enumerate(segment.description_lines)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{panel_width}" height="{CANVAS_HEIGHT}" viewBox="0 0 {panel_width} {CANVAS_HEIGHT}">
  <rect width="100%" height="100%" fill="#0b4540"/>
  <rect width="2" height="100%" fill="#5fb9ac"/>
  <style>
    .eyebrow {{ font: 600 18px Helvetica, Arial, sans-serif; letter-spacing: 3px; fill: #9ed8cf; }}
    .title {{ font: 400 38px Helvetica, Arial, sans-serif; fill: #ffffff; }}
    .description {{ font: 400 22px Helvetica, Arial, sans-serif; fill: #d4e7e3; }}
    .tagline {{ font: 600 15px Helvetica, Arial, sans-serif; letter-spacing: 2px; fill: #9ed8cf; }}
  </style>
  <text x="34" y="128" class="eyebrow">{html.escape(segment.eyebrow)}</text>
  {title}
  {description}
  <rect x="34" y="900" width="48" height="3" fill="#5fb9ac"/>
  <text x="34" y="950" class="tagline">EVERY ROW</text>
  <text x="34" y="976" class="tagline">LEAVES A WAKE.</text>
</svg>'''


def render_panel_png(segment: Segment, output: Path) -> None:
    svg = output.with_suffix(".svg")
    svg.write_text(render_panel_svg(segment), encoding="utf-8")
    run(["rsvg-convert", str(svg), "-o", str(output)])


def render_svg_png(source: Path, output: Path) -> None:
    run(
        [
            "rsvg-convert",
            "--width",
            str(CANVAS_WIDTH),
            "--height",
            str(CANVAS_HEIGHT),
            str(source),
            "-o",
            str(output),
        ]
    )


def hide_svg_elements(svg: str, element_ids: set[str]) -> str:
    for element_id in element_ids:
        pattern = rf'(<(?:g|path)\s+id="{re.escape(element_id)}")'
        svg, count = re.subn(
            pattern,
            rf'\1 style="display:none"',
            svg,
            count=1,
        )
        if count != 1:
            raise ValueError(f"Missing SVG element: {element_id}")
    return svg


def render_agentic_segment(segment: Segment, output: Path) -> None:
    duration = segment.end - segment.start
    timing_scale = duration / 16

    stages = [
        {
            "agent-to-tools",
            "tools",
            "tools-to-verifier",
            "verifier",
            "verifier-to-human",
            "human",
        },
        {"tools", "tools-to-verifier", "verifier", "verifier-to-human", "human"},
        {"tools-to-verifier", "verifier", "verifier-to-human", "human"},
        {"verifier", "verifier-to-human", "human"},
        {"verifier-to-human", "human"},
        {"human"},
        set(),
    ]
    stage_durations = [value * timing_scale for value in [2.5, 1.5, 3.0, 1.5, 3.0, 1.5, 4.5]]
    transition = 0.25 * timing_scale
    xfade_offsets = [value * timing_scale for value in [2.25, 3.5, 6.25, 7.5, 10.25, 11.5]]
    source_svg = segment.source.read_text(encoding="utf-8")
    stage_pngs: list[Path] = []
    for index, hidden in enumerate(stages):
        svg_path = output.with_name(f"{output.stem}.agentic-{index}.svg")
        png_path = svg_path.with_suffix(".png")
        svg_path.write_text(hide_svg_elements(source_svg, hidden), encoding="utf-8")
        render_svg_png(svg_path, png_path)
        stage_pngs.append(png_path)

    inputs: list[str] = []
    for stage_png, stage_duration in zip(stage_pngs, stage_durations):
        inputs.extend(
            [
                "-loop",
                "1",
                "-framerate",
                str(FRAME_RATE),
                "-t",
                str(stage_duration),
                "-i",
                str(stage_png),
            ]
        )

    filters: list[str] = []
    left = "[0:v]"
    for index, offset in enumerate(xfade_offsets, start=1):
        output_label = f"[stage{index}]"
        filters.append(
            f"{left}[{index}:v]xfade=transition=fade:duration={transition}:offset={offset}{output_label}"
        )
        left = output_label
    filters.append(f"{left}fps={FRAME_RATE},format=yuv420p[out]")
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[out]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "19",
            "-r",
            str(FRAME_RATE),
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
    )


def cursor_position_expression(start: int, end: int, travel: float) -> str:
    delta = end - start
    eased = f"(3*pow(t/{travel},2)-2*pow(t/{travel},3))"
    return f"if(lt(t\\,{travel})\\,{start}+{delta}*{eased}\\,{end})"


def render_cursor_segment(segment: Segment, output: Path) -> None:
    if segment.cursor_from is None or segment.cursor_to is None:
        raise ValueError("Cursor segments require start and destination coordinates")
    duration = segment.end - segment.start
    panel = output.with_suffix(".panel.png")
    cursor = output.with_suffix(".cursor.png")
    _, panel_width = layout_widths()
    render_panel_png(segment, panel)
    run(["rsvg-convert", str(CURSOR_SVG), "-o", str(cursor)])

    cursor_x = cursor_position_expression(
        segment.cursor_from[0], segment.cursor_to[0], segment.cursor_travel
    )
    cursor_y = cursor_position_expression(
        segment.cursor_from[1], segment.cursor_to[1], segment.cursor_travel
    )
    filter_complex = ";".join(
        [
            f"[0:v]{image_filter()}[product]",
            f"[1:v]scale={panel_width}:{CANVAS_HEIGHT}[panel]",
            "[product][panel]hstack=inputs=2[base]",
            f"[base][2:v]overlay=x='{cursor_x}':y='{cursor_y}':eval=frame,format=yuv420p[out]",
        ]
    )
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            str(FRAME_RATE),
            "-i",
            str(segment.source),
            "-loop",
            "1",
            "-framerate",
            str(FRAME_RATE),
            "-i",
            str(panel),
            "-loop",
            "1",
            "-framerate",
            str(FRAME_RATE),
            "-i",
            str(cursor),
            "-t",
            str(duration),
            "-filter_complex",
            filter_complex,
            "-map",
            "[out]",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "19",
            "-r",
            str(FRAME_RATE),
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
    )


def render_motion_segment(segment: Segment, output: Path) -> None:
    duration = segment.end - segment.start
    png = output.with_suffix(".motion.png")
    render_svg_png(segment.source, png)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            str(FRAME_RATE),
            "-i",
            str(png),
            "-t",
            str(duration),
            "-vf",
            (
                "zoompan=z='min(zoom+0.00004,1.012)':"
                "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d=1:s={CANVAS_WIDTH}x{CANVAS_HEIGHT}:fps={FRAME_RATE},"
                "format=yuv420p"
            ),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "19",
            "-r",
            str(FRAME_RATE),
            "-pix_fmt",
            "yuv420p",
            str(output),
        ]
    )


def render_segment(
    segment: Segment,
    source_video: Path,
    output: Path,
) -> None:
    duration = segment.end - segment.start
    common = [
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "19",
        "-r",
        str(FRAME_RATE),
        "-pix_fmt",
        "yuv420p",
    ]
    if segment.kind == "video":
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(segment.start),
                "-i",
                str(source_video),
                "-t",
                str(duration),
                "-vf",
                f"scale={CANVAS_WIDTH}:{CANVAS_HEIGHT},tpad=stop_mode=clone:stop_duration=2,fps={FRAME_RATE},format=yuv420p",
                *common,
                str(output),
            ]
        )
        return

    if segment.kind == "agentic":
        render_agentic_segment(segment, output)
        return

    if segment.kind == "cursor":
        render_cursor_segment(segment, output)
        return

    if segment.kind == "motion":
        render_motion_segment(segment, output)
        return

    panel = output.with_suffix(".panel.png")
    _, panel_width = layout_widths()
    render_panel_png(segment, panel)
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-loop",
            "1",
            "-framerate",
            str(FRAME_RATE),
            "-i",
            str(segment.source),
            "-loop",
            "1",
            "-framerate",
            str(FRAME_RATE),
            "-i",
            str(panel),
            "-t",
            str(duration),
            "-filter_complex",
            f"[0:v]{image_filter()}[product];[1:v]scale={panel_width}:{CANVAS_HEIGHT}[panel];[product][panel]hstack=inputs=2,format=yuv420p[out]",
            "-map",
            "[out]",
            *common,
            str(output),
        ]
    )


def build_video(source_video: Path, capture_dir: Path, output: Path) -> None:
    if not source_video.is_file():
        raise FileNotFoundError(source_video)
    timeline = build_timeline(capture_dir)
    missing = [
        segment.source
        for segment in timeline
        if segment.kind in {"image", "cursor", "agentic", "motion"}
        and not segment.source.is_file()
    ]
    if missing:
        raise FileNotFoundError("Missing captures: " + ", ".join(map(str, missing)))
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required")
    if shutil.which("rsvg-convert") is None:
        raise RuntimeError("rsvg-convert is required")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wake-video-current-") as temporary:
        work = Path(temporary)
        rendered: list[Path] = []
        for index, segment in enumerate(timeline):
            path = work / f"segment-{index:02d}.mp4"
            render_segment(segment, source_video, path)
            rendered.append(path)

        concat_file = work / "segments.txt"
        concat_file.write_text(
            "".join(f"file '{path}'\n" for path in rendered),
            encoding="utf-8",
        )
        visual = work / "visual.mp4"
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
                str(concat_file),
                "-c",
                "copy",
                str(visual),
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
                str(visual),
                "-i",
                str(source_video),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "copy",
                "-movflags",
                "+faststart",
                str(output),
            ]
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--captures", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_video(args.source, args.captures, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
