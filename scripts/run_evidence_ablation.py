#!/usr/bin/env python3
"""Dry-run or explicitly execute the frozen WAKE evidence ablation."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import jsonschema

from run_baseline import current_git_commit, read_json, sha256_path, utc_now, write_json
from wake_agent import (
    DEFAULT_CONFIG,
    DEFAULT_PROMPT,
    DEFAULT_SCHEMA,
    build_agent_run_manifest,
    run_agent_case,
    write_agent_dry_run,
)


ROOT = Path(__file__).resolve().parents[1]
BASE_CASE_ID = "case-002-wind-shift-plan-deviation"
PUBLIC_INPUT = ROOT / "data" / "fixtures" / BASE_CASE_ID / "input"
DEFAULT_INPUTS = ROOT / "evaluation" / "ablation-inputs" / "v1"
CONDITION_ORDER = ["core", "context-environment", "full"]
ALLOWED_EVIDENCE_FILES = {
    "plan.json",
    "speedcoach.csv",
    "mobile.csv",
    "environment.json",
    "context.json",
}


def load_experiment(input_dir: Path = DEFAULT_INPUTS) -> tuple[dict, list[dict]]:
    manifest_path = input_dir / "manifest.json"
    manifest = read_json(manifest_path)
    if manifest.get("schema") != "wake.evidence_ablation_manifest.v1":
        raise ValueError("Unsupported evidence ablation manifest.")
    if manifest.get("base_case_id") != BASE_CASE_ID:
        raise ValueError("Evidence ablation base case does not match the runner.")
    if list(manifest.get("conditions", {})) != CONDITION_ORDER:
        raise ValueError("Evidence ablation conditions or order changed after freeze.")

    summary_schema = read_json(ROOT / "schemas" / "case-summary.schema.json")
    summaries = []
    for condition_id in CONDITION_ORDER:
        entry = manifest["conditions"][condition_id]
        relative_path = Path(entry["path"])
        if relative_path.name != entry["path"] or relative_path.suffix != ".json":
            raise ValueError(f"Unsafe summary path for condition {condition_id}.")
        path = input_dir / relative_path
        if sha256_path(path) != entry["sha256"]:
            raise ValueError(f"Frozen summary hash mismatch for condition {condition_id}.")
        summary = read_json(path)
        jsonschema.validate(instance=summary, schema=summary_schema)
        if summary["case_id"] != entry["summary_case_id"]:
            raise ValueError(f"Summary identity mismatch for condition {condition_id}.")
        source_files = entry.get("source_files", [])
        if (
            len(source_files) != len(set(source_files))
            or not set(source_files).issubset(ALLOWED_EVIDENCE_FILES)
            or set(summary["input_hashes"]) != set(source_files)
        ):
            raise ValueError(f"Invalid evidence file set for condition {condition_id}.")
        for filename in source_files:
            if summary["input_hashes"].get(filename) != sha256_path(
                PUBLIC_INPUT / filename
            ):
                raise ValueError(
                    f"Evidence hash mismatch for {filename} in condition {condition_id}."
                )
        summaries.append(summary)
    return manifest, summaries


def experiment_metadata(
    manifest: dict,
    input_dir: Path = DEFAULT_INPUTS,
) -> dict:
    return {
        "schema_version": "wake.evidence_ablation_run.v1",
        "base_case_id": manifest["base_case_id"],
        "input_version": manifest["version"],
        "condition_order": CONDITION_ORDER,
        "input_manifest_sha256": sha256_path(input_dir / "manifest.json"),
        "scoring_status": "NOT_SCORED",
    }


def default_output_dir(mode: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ROOT / "evaluation" / "runs" / "evidence-ablation-v1" / f"{timestamp}-{mode}"


def dry_run(*, output_dir: Path, input_dir: Path = DEFAULT_INPUTS) -> Path:
    manifest, summaries = load_experiment(input_dir)
    path = write_agent_dry_run(
        config=read_json(DEFAULT_CONFIG),
        prompt=DEFAULT_PROMPT.read_text(encoding="utf-8"),
        summaries=summaries,
        output_schema=read_json(DEFAULT_SCHEMA),
        output_dir=output_dir,
    )
    run_manifest = read_json(path)
    run_manifest["experiment"] = experiment_metadata(manifest, input_dir)
    write_json(path, run_manifest)
    return path


def _copy_condition_evidence(entry: dict, destination: Path) -> None:
    for filename in entry["source_files"]:
        (destination / filename).write_bytes((PUBLIC_INPUT / filename).read_bytes())


def execute(
    *,
    client: object,
    output_dir: Path,
    input_dir: Path = DEFAULT_INPUTS,
    case_runner: Callable[..., dict] = run_agent_case,
    now: Callable[[], str] = utc_now,
    monotonic: Callable[[], float] = time.monotonic,
    git_commit: str | None = None,
) -> Path:
    manifest, summaries = load_experiment(input_dir)
    config = read_json(DEFAULT_CONFIG)
    prompt = DEFAULT_PROMPT.read_text(encoding="utf-8")
    output_schema = read_json(DEFAULT_SCHEMA)
    run_id = output_dir.name
    commit = git_commit or current_git_commit()
    started_at = now()
    started = monotonic()
    artifacts = []
    trajectories = []

    for condition_id, summary in zip(CONDITION_ORDER, summaries, strict=True):
        entry = manifest["conditions"][condition_id]
        with tempfile.TemporaryDirectory(prefix=f"wake-ablation-{condition_id}-") as temporary:
            evidence_dir = Path(temporary)
            _copy_condition_evidence(entry, evidence_dir)
            result = case_runner(
                client=client,
                config=config,
                prompt=prompt,
                summary=summary,
                input_dir=evidence_dir,
                output_schema=output_schema,
                output_dir=output_dir,
                run_id=run_id,
                now=now,
                git_commit=commit,
            )
        artifacts.append(result)
        trajectories.append(read_json(result["trajectory_path"]))

    finished = monotonic()
    finished_at = now()
    run_manifest = build_agent_run_manifest(
        config=config,
        prompt=prompt,
        output_dir=output_dir,
        run_id=run_id,
        git_commit=commit,
        artifacts=artifacts,
        trajectories=trajectories,
        started_at=started_at,
        finished_at=finished_at,
        runtime_ms=round((finished - started) * 1000),
    )
    run_manifest["experiment"] = experiment_metadata(manifest, input_dir)
    manifest_path = output_dir / "run-manifest.json"
    write_json(manifest_path, run_manifest)
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Call the OpenAI API.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    mode = "execute" if args.execute else "dry-run"
    output_dir = args.output or default_output_dir(mode)

    if not args.execute:
        path = dry_run(output_dir=output_dir)
        print(json.dumps({"mode": mode, "manifest": str(path)}, indent=2))
        return

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required with --execute.")
    from openai import OpenAI

    path = execute(client=OpenAI(), output_dir=output_dir)
    print(json.dumps({"mode": mode, "manifest": str(path)}, indent=2))


if __name__ == "__main__":
    main()
