#!/usr/bin/env python3
"""Replace the chapter-two narration without shifting the accepted video edit."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


CHAPTER_START_SECONDS = 63.0
CHAPTER_END_SECONDS = 129.0
CHAPTER_TARGET_SECONDS = CHAPTER_END_SECONDS - CHAPTER_START_SECONDS
MIN_TEMPO = 0.95
MAX_TEMPO = 1.05


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


def tempo_for_duration(duration: float) -> float:
    if duration <= 0:
        raise ValueError("Narration duration must be positive")
    tempo = duration / CHAPTER_TARGET_SECONDS
    if not MIN_TEMPO <= tempo <= MAX_TEMPO:
        raise ValueError(
            f"Required tempo {tempo:.6f} is outside the accepted "
            f"{MIN_TEMPO:.2f}–{MAX_TEMPO:.2f} range"
        )
    return tempo


def audio_filter(chapter_duration: float) -> str:
    tempo = tempo_for_duration(chapter_duration)
    return ";".join(
        [
            (
                f"[0:a]atrim=start=0:end={CHAPTER_START_SECONDS},"
                "asetpts=PTS-STARTPTS,aresample=48000[pre]"
            ),
            (
                f"[1:a]aresample=48000,atempo={tempo:.6f},"
                f"atrim=duration={CHAPTER_TARGET_SECONDS},"
                "asetpts=PTS-STARTPTS[chapter]"
            ),
            (
                f"[0:a]atrim=start={CHAPTER_END_SECONDS},"
                "asetpts=PTS-STARTPTS,aresample=48000[post]"
            ),
            "[pre][chapter][post]concat=n=3:v=0:a=1[outa]",
        ]
    )


def replace_audio(source: Path, chapter_audio: Path, output: Path) -> None:
    if not source.is_file():
        raise FileNotFoundError(source)
    if not chapter_audio.is_file():
        raise FileNotFoundError(chapter_audio)
    output.parent.mkdir(parents=True, exist_ok=True)
    chapter_duration = probe_duration(chapter_audio)
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-i",
            str(chapter_audio),
            "-filter_complex",
            audio_filter(chapter_duration),
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
        ],
        check=True,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--chapter-audio", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    replace_audio(args.source, args.chapter_audio, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
