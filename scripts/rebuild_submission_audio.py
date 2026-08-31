#!/usr/bin/env python3
"""Rebuild the final narration from the supplied chapter recordings.

The previous replacement stretched chapter two across the first seconds of the
human-checkpoint recording. This builder keeps every chapter discrete, shortens
only pauses in chapter two, and preserves a quiet tail after the final word.
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path


CHAPTER_ONE_START_SECONDS = 3.85
CHAPTER_TWO_START_SECONDS = 63.0
CHAPTER_THREE_START_SECONDS = 122.967
CHAPTER_TRANSITION_GAP_SECONDS = 0.15
CHAPTER_TWO_TARGET_SECONDS = (
    CHAPTER_THREE_START_SECONDS
    - CHAPTER_TRANSITION_GAP_SECONDS
    - CHAPTER_TWO_START_SECONDS
)
FINAL_TAIL_SECONDS = 0.6
TRIM_VIDEO_TO_AUDIO = False


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def probe_duration(path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def chapter_two_cleanup_filter() -> str:
    return (
        "silenceremove=stop_periods=-1:stop_duration=0.25:"
        "stop_threshold=-38dB:stop_silence=0.20"
    )


def tempo_for_chapter_two(cleaned_duration: float) -> float:
    if cleaned_duration <= 0:
        raise ValueError("Cleaned chapter-two duration must be positive")
    tempo = cleaned_duration / CHAPTER_TWO_TARGET_SECONDS
    if not 1.0 <= tempo < 1.03:
        raise ValueError(f"Unexpected chapter-two tempo: {tempo:.6f}")
    return tempo


def audio_filter(
    chapter_one_duration: float,
    cleaned_chapter_two_duration: float,
) -> str:
    first_gap = (
        CHAPTER_TWO_START_SECONDS
        - CHAPTER_ONE_START_SECONDS
        - chapter_one_duration
    )
    if first_gap < 0:
        raise ValueError("Chapter one overlaps chapter two")
    tempo = tempo_for_chapter_two(cleaned_chapter_two_duration)
    mono = "aresample=48000,aformat=channel_layouts=mono,asetpts=PTS-STARTPTS"
    return ";".join(
        [
            f"[0:a]atrim=start=0:end={CHAPTER_ONE_START_SECONDS},{mono}[intro]",
            f"[1:a]{mono}[chapter1]",
            f"anullsrc=r=48000:cl=mono,atrim=duration={first_gap:.6f}[gap1]",
            (
                f"[2:a]{mono},atempo={tempo:.6f},"
                f"atrim=duration={CHAPTER_TWO_TARGET_SECONDS:.3f}[chapter2]"
            ),
            (
                "anullsrc=r=48000:cl=mono,"
                f"atrim=duration={CHAPTER_TRANSITION_GAP_SECONDS}[gap2]"
            ),
            f"[3:a]{mono}[chapter3]",
            f"[4:a]{mono}[chapter4]",
            f"[5:a]{mono}[chapter5]",
            f"[6:a]{mono}[chapter6]",
            f"[7:a]{mono}[chapter7]",
            f"anullsrc=r=48000:cl=mono,atrim=duration={FINAL_TAIL_SECONDS}[tail]",
            (
                "[intro][chapter1][gap1][chapter2][gap2][chapter3][chapter4]"
                "[chapter5][chapter6][chapter7][tail]"
                "concat=n=11:v=0:a=1[outa]"
            ),
        ]
    )


def rebuild_audio(
    source_video: Path,
    chapters: list[Path],
    output: Path,
) -> None:
    if len(chapters) != 7:
        raise ValueError("Exactly seven narration chapters are required")
    for path in [source_video, *chapters]:
        if not path.is_file():
            raise FileNotFoundError(path)

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="wake-final-audio-") as temporary:
        cleaned_chapter_two = Path(temporary) / "chapter-two-clean.wav"
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(chapters[1]),
                "-af",
                chapter_two_cleanup_filter(),
                "-c:a",
                "pcm_s16le",
                str(cleaned_chapter_two),
            ]
        )
        graph = audio_filter(
            probe_duration(chapters[0]),
            probe_duration(cleaned_chapter_two),
        )
        inputs: list[str] = ["-i", str(source_video), "-i", str(chapters[0]), "-i", str(cleaned_chapter_two)]
        for chapter in chapters[2:]:
            inputs.extend(["-i", str(chapter)])
        run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                *inputs,
                "-filter_complex",
                graph,
                "-map",
                "0:v:0",
                "-map",
                "[outa]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-ar",
                "48000",
                "-ac",
                "1",
                "-movflags",
                "+faststart",
                str(output),
            ]
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--chapter", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rebuild_audio(args.source, args.chapter, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
