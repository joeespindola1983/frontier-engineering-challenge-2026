#!/usr/bin/env python3
"""Build a deterministic source-only WAKE submission archive."""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path


EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    ".vinext",
    ".wrangler",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "private-data",
    "tmp",
}

EXCLUDED_SUFFIXES = {".mp4", ".pyc", ".pyo"}
FIXED_ZIP_TIMESTAMP = (2026, 8, 31, 0, 0, 0)


@dataclass(frozen=True)
class SourceZipResult:
    output_path: Path
    file_count: int
    size_bytes: int
    sha256: str


def _is_excluded(relative_path: Path, output_relative_path: Path | None) -> bool:
    if output_relative_path is not None and relative_path == output_relative_path:
        return True
    if any(part in EXCLUDED_DIRECTORIES for part in relative_path.parts[:-1]):
        return True
    if relative_path.name == ".DS_Store":
        return True
    if relative_path.name == ".env" or (
        relative_path.name.startswith(".env.") and relative_path.name != ".env.example"
    ):
        return True
    if relative_path.name.startswith("wake-final-submission-draft"):
        return True
    return relative_path.suffix.lower() in EXCLUDED_SUFFIXES


def _included_files(root: Path, output_path: Path) -> list[Path]:
    try:
        output_relative_path = output_path.resolve().relative_to(root)
    except ValueError:
        output_relative_path = None

    files: list[Path] = []
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        directory_names[:] = sorted(
            name
            for name in directory_names
            if name not in EXCLUDED_DIRECTORIES and not (directory_path / name).is_symlink()
        )
        for file_name in sorted(file_names):
            path = directory_path / file_name
            relative_path = path.relative_to(root)
            if path.is_symlink() or _is_excluded(relative_path, output_relative_path):
                continue
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def build_source_zip(root: Path, output_path: Path, *, max_bytes: int) -> SourceZipResult:
    root = root.resolve()
    output_path = output_path.resolve()
    if not (root / "README.md").is_file():
        raise ValueError(f"Not a WAKE repository root: {root}")
    if max_bytes <= 0:
        raise ValueError("max_bytes must be positive")

    files = _included_files(root, output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    archive_prefix = root.name
    with zipfile.ZipFile(
        output_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in files:
            relative_path = path.relative_to(root)
            archive_name = f"{archive_prefix}/{relative_path.as_posix()}"
            info = zipfile.ZipInfo(archive_name, date_time=FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            normalized_mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            info.external_attr = (stat.S_IFREG | normalized_mode) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    size_bytes = output_path.stat().st_size
    if size_bytes > max_bytes:
        output_path.unlink()
        raise ValueError(
            f"Source archive exceeded the configured limit: {size_bytes} bytes > {max_bytes} bytes"
        )
    digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
    return SourceZipResult(
        output_path=output_path,
        file_count=len(files),
        size_bytes=size_bytes,
        sha256=digest,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (default: current WAKE repository).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dist/wake-source-submission.zip"),
        help="Archive path, relative to the repository root unless absolute.",
    )
    parser.add_argument(
        "--max-mb",
        type=float,
        default=50.0,
        help="Maximum archive size in MiB (default: 50).",
    )
    args = parser.parse_args()
    output_path = args.output if args.output.is_absolute() else args.root / args.output
    result = build_source_zip(
        args.root,
        output_path,
        max_bytes=int(args.max_mb * 1024 * 1024),
    )
    print(f"Archive: {result.output_path}")
    print(f"Files: {result.file_count}")
    print(f"Size: {result.size_bytes / (1024 * 1024):.2f} MiB")
    print(f"SHA-256: {result.sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
