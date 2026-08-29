#!/usr/bin/env python3
"""Run every implemented public fixture verifier."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIERS = [
    ROOT / "scripts/verify_hero_fixture.py",
    ROOT / "scripts/verify_synthetic_case.py"
]


def main() -> None:
    for verifier in VERIFIERS:
        print(f"==> {verifier.name}", flush=True)
        subprocess.run([sys.executable, str(verifier)], cwd=ROOT, check=True)
    print(f"Verified {len(VERIFIERS)} implemented fixtures.")


if __name__ == "__main__":
    main()
