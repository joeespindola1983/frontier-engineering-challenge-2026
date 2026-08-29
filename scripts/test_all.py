#!/usr/bin/env python3
"""Run deterministic tests followed by public artifact verification."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_all.py")],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
