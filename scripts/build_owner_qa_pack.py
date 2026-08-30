#!/usr/bin/env python3
"""Build the public, upload-ready owner QA evidence pack."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = (
    ROOT
    / "data"
    / "fixtures"
    / "case-002-wind-shift-plan-deviation"
    / "input"
)
DEFAULT_OUTPUT = ROOT / "data" / "qa-interface"
UPLOAD_FILES = (
    "plan.json",
    "speedcoach.csv",
    "mobile.csv",
    "environment.json",
    "context.json",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_pack(output_root: Path = DEFAULT_OUTPUT) -> Path:
    bundle = output_root / "full-replay-bundle"
    bundle.mkdir(parents=True, exist_ok=True)

    hashes: dict[str, str] = {}
    for name in UPLOAD_FILES:
        source = SOURCE_ROOT / name
        destination = bundle / name
        shutil.copyfile(source, destination)
        hashes[name] = sha256(destination)

    manifest = {
        "schema_version": "wake.owner_qa_pack.v1",
        "provenance": "DERIVED_SYNTHETIC",
        "privacy": "PUBLIC_SYNTHETIC_ONLY",
        "source_case": "case-002-wind-shift-plan-deviation",
        "full_replay": {
            "directory": "full-replay-bundle",
            "file_count": len(UPLOAD_FILES),
            "files": list(UPLOAD_FILES),
            "sha256": hashes,
            "expected_action": "Validate and open replay",
            "expected_cost_usd": 0,
        },
        "minimum_preparation": {
            "directory": "full-replay-bundle",
            "files": ["plan.json", "speedcoach.csv"],
            "expected_action": "Validate and prepare · No agent call",
            "expected_cost_usd": 0,
        },
        "live_validation": {
            "start_count": 3,
            "authorization_per_start_usd": 0.20,
            "authorization_total_usd": 0.60,
            "authorization_is_provider_cap": False,
            "scenarios": [
                "plan_speedcoach_core",
                "five_source_complete_bundle",
                "plan_speedcoach_historical_weather",
            ],
        },
        "exclusions": [
            "ground-truth.json",
            "fixture-manifest.json",
            "private telemetry",
            "credentials",
        ],
    }
    (output_root / "qa-pack-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    readme = """# WAKE owner QA upload pack

This directory contains only public, derived-synthetic evidence prepared for
interface QA. It includes no evaluator ground truth, private GPS, real athlete
identity, credential, or hidden expected answer.

## Full replay bundle

Open `full-replay-bundle/` in the file chooser and map the files in this order:

1. Training plan — `plan.json`
2. SpeedCoach recording — `speedcoach.csv`
3. Mobile recording — `mobile.csv`
4. Environmental timeline — `environment.json`
5. Session context — `context.json`

In replay mode, all five byte-identical sources should enable **Validate and
open replay** and reopen the committed verified investigation at US$0.00.

## Minimum evidence preparation

From the same folder, select only `plan.json` and `speedcoach.csv`. The
interface should enable **Validate and prepare · No agent call**, save a local
prepared session, and keep mobile, environment, and human context visibly
missing. It must not inherit the answer from the complete replay bundle.

See `docs/OWNER_QA_GUIDE.md` for the complete sequential checklist.

The live QA section deliberately runs three separate investigation starts. It
requires an explicit US$0.60 total operational authorization before execution;
the authorization is a start gate, not a provider billing cap.
"""
    (output_root / "README.md").write_text(readme, encoding="utf-8")
    return output_root


if __name__ == "__main__":
    print(build_pack())
