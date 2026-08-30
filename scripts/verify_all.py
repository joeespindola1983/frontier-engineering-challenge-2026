#!/usr/bin/env python3
"""Run every implemented public fixture verifier."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFIERS = [
    ROOT / "scripts/verify_hero_fixture.py",
    ROOT / "scripts/verify_synthetic_case.py",
    ROOT / "scripts/verify_diagnostic_cases.py",
    ROOT / "scripts/verify_baseline_inputs.py",
    ROOT / "scripts/verify_demo_club_evidence.py",
    ROOT / "scripts/verify_demo_club_investigation_run.py",
    ROOT / "scripts/verify_demo_club_batch.py",
    ROOT / "scripts/verify_longitudinal_pilot.py",
]


def main() -> None:
    for verifier in VERIFIERS:
        print(f"==> {verifier.name}", flush=True)
        subprocess.run([sys.executable, str(verifier)], cwd=ROOT, check=True)
    print(f"Verified {len(VERIFIERS)} public fixture and artifact checks.")


if __name__ == "__main__":
    main()
