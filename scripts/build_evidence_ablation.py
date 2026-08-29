#!/usr/bin/env python3
"""Build frozen progressive-evidence inputs for WAKE ablation runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import jsonschema

from bundle_assembler import assemble_case_summary
from source_adapters import normalize_source


ROOT = Path(__file__).resolve().parents[1]
BASE_CASE_ID = "case-002-wind-shift-plan-deviation"
CASE_INPUT = ROOT / "data" / "fixtures" / BASE_CASE_ID / "input"
DEFAULT_OUTPUT = ROOT / "evaluation" / "ablation-inputs" / "v1"
GENERATOR_VERSION = "scripts/build_evidence_ablation.py@1.0"
CONDITIONS = (
    {
        "condition_id": "core",
        "include_mobile": False,
        "include_environment": False,
        "include_context": False,
        "capabilities": ["PLAN_EXECUTION", "SINGLE_SOURCE_METRIC_TRUST"],
    },
    {
        "condition_id": "context-environment",
        "include_mobile": False,
        "include_environment": True,
        "include_context": True,
        "capabilities": [
            "PLAN_EXECUTION",
            "SINGLE_SOURCE_METRIC_TRUST",
            "ENVIRONMENT_ASSOCIATION",
            "HUMAN_CONTEXT",
        ],
    },
    {
        "condition_id": "full",
        "include_mobile": True,
        "include_environment": True,
        "include_context": True,
        "capabilities": [
            "PLAN_EXECUTION",
            "CROSS_SOURCE_METRIC_TRUST",
            "SESSION_CORROBORATION",
            "ENVIRONMENT_ASSOCIATION",
            "HUMAN_CONTEXT",
        ],
    },
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _condition_summary(condition: dict) -> tuple[dict, list[str]]:
    filenames = ["plan.json", "speedcoach.csv"]
    if condition["include_mobile"]:
        filenames.append("mobile.csv")
    if condition["include_environment"]:
        filenames.append("environment.json")
    if condition["include_context"]:
        filenames.append("context.json")

    telemetry_sources = []
    for kind, filename in (("SPEEDCOACH", "speedcoach.csv"), ("MOBILE", "mobile.csv")):
        if filename not in filenames:
            continue
        normalized = normalize_source(
            kind=kind,
            content=(CASE_INPUT / filename).read_bytes(),
            source_ref=f"input/{filename}",
        )
        telemetry_sources.append(
            {
                "kind": kind,
                "evidence_ref": f"input/{filename}",
                "normalized_csv": normalized.normalized_csv,
                "normalization": normalized.report,
            }
        )

    summary = assemble_case_summary(
        plan=read_json(CASE_INPUT / "plan.json"),
        context=(
            read_json(CASE_INPUT / "context.json")
            if condition["include_context"]
            else None
        ),
        environment=(
            read_json(CASE_INPUT / "environment.json")
            if condition["include_environment"]
            else None
        ),
        telemetry_sources=telemetry_sources,
        input_hashes={
            filename: sha256_path(CASE_INPUT / filename)
            for filename in filenames
        },
    )
    condition_id = condition["condition_id"]
    summary["summary_id"] = f"evidence-ablation-v1-{condition_id}"
    summary["case_id"] = f"ablation-{BASE_CASE_ID}-{condition_id}"
    summary["generated_by"] = GENERATOR_VERSION
    jsonschema.validate(
        instance=summary,
        schema=read_json(ROOT / "schemas" / "case-summary.schema.json"),
    )
    return summary, filenames


def build(output: Path = DEFAULT_OUTPUT) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    entries = {}
    for condition in CONDITIONS:
        condition_id = condition["condition_id"]
        summary, filenames = _condition_summary(condition)
        path = output / f"{condition_id}.json"
        write_json(path, summary)
        entries[condition_id] = {
            "path": path.name,
            "sha256": sha256_path(path),
            "bytes": path.stat().st_size,
            "summary_case_id": summary["case_id"],
            "source_files": filenames,
            "capabilities": condition["capabilities"],
        }

    manifest = {
        "schema": "wake.evidence_ablation_manifest.v1",
        "version": "1.0",
        "generator": GENERATOR_VERSION,
        "base_case_id": BASE_CASE_ID,
        "purpose": (
            "Measure the marginal behavior enabled by context, environment, and "
            "mobile evidence while preserving the same underlying synthetic session."
        ),
        "conditions": entries,
    }
    manifest_path = output / "manifest.json"
    write_json(manifest_path, manifest)
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    manifest = build(args.output)
    print(f"Built {len(CONDITIONS)} evidence-ablation inputs in {manifest.parent}")


if __name__ == "__main__":
    main()
