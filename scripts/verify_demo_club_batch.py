#!/usr/bin/env python3
"""Verify the complete two-week demo-club batch without a model call."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import jsonschema

import bundle_assembler
import source_adapters
import verify_demo_club_investigation_run
import wake_tools


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BATCH_ROOT = ROOT / "data" / "demo-club-batch"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_concept2(path: Path) -> None:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required = {
            "interval",
            "distance_m",
            "elapsed_s",
            "pace_500m_s",
            "stroke_rate_spm",
            "watts",
        }
        assert required.issubset(reader.fieldnames or []), "Concept2-shaped columns missing"
        rows = list(reader)
    assert rows, "Concept2-shaped export is empty"
    assert all(float(row["distance_m"]) > 0 for row in rows)


def verify_batch(batch_root: Path = DEFAULT_BATCH_ROOT) -> dict:
    manifest = read_json(batch_root / "manifest.json")
    assert manifest["schema_version"] == "wake.demo_club_batch_manifest.v1"
    assert len(manifest["sessions"]) == 40
    assert len({item["session_id"] for item in manifest["sessions"]}) == 40
    plan_schema = read_json(ROOT / "schemas" / "training-plan.schema.json")
    routes = Counter()
    data_validated = reconstructed = plan_compared = 0

    for item in manifest["sessions"]:
        assert item["provenance"] == "REAL_INFORMED_SYNTHETIC"
        session_dir = batch_root / "sessions" / item["session_id"]
        assert session_dir.is_dir()
        for name, expected_hash in item["source_sha256"].items():
            source_path = (session_dir / name).resolve()
            assert source_path.is_relative_to(batch_root.resolve())
            assert sha256(source_path) == expected_hash

        plan_path = session_dir / "plan.json"
        context_path = session_dir / "context.json"
        if plan_path.is_file():
            jsonschema.validate(read_json(plan_path), plan_schema)
        if context_path.is_file():
            context = read_json(context_path)
            assert context["schema_version"] == "wake.synthetic_case_context.v1"
            assert context["case_id"] == item["session_id"]

        if item["modality"] == "ERG":
            validate_concept2(session_dir / "concept2.csv")
            assert item["expected_route"] == "SOURCE_ADAPTER_REQUIRED"
            data_validated += 1
            routes[item["expected_route"]] += 1
            continue

        normalized = source_adapters.normalize_source(
            kind="SPEEDCOACH",
            content=(session_dir / "speedcoach.csv").read_bytes(),
            source_ref="input/speedcoach.csv",
        )
        assert normalized.report["row_count"] > 0
        data_validated += 1
        reconstructed += 1
        routes[item["expected_route"]] += 1

        if not plan_path.is_file():
            assert item["expected_route"] == "SOURCE_REQUIRED"
            continue
        plan_compared += 1
        summary = bundle_assembler.assemble_case_summary(
            plan=read_json(plan_path),
            context=read_json(context_path) if context_path.is_file() else None,
            environment=None,
            telemetry_sources=[{
                "kind": "SPEEDCOACH",
                "evidence_ref": "input/speedcoach.csv",
                "normalized_csv": normalized.normalized_csv,
                "normalization": normalized.report,
            }],
            input_hashes={
                name: digest for name, digest in item["source_sha256"].items()
            },
        )
        result = wake_tools.reconstruct_plan_execution(
            summary,
            session_dir,
            contract_version="v2",
        )
        deviation_segments = [
            deviation["segment_ref"] for deviation in result["plan_deviations"]
        ]
        if item["session_id"] == "club-bridge-mixed-20260820-spm":
            assert deviation_segments == ["work-02"]
        elif item["session_id"] == "club-atlas-men-20260828-recovery":
            assert deviation_segments == ["recovery-02"]
        else:
            assert deviation_segments == [], (
                item["session_id"], deviation_segments
            )
        if item["expected_route"] == "HUMAN_CONTEXT_REQUIRED":
            assert not context_path.exists()
            assert any("context" in gap.lower() for gap in summary["evidence_gaps"])

    investigation = verify_demo_club_investigation_run.verify_run()
    deviations = Counter()
    for result in investigation["results"].values():
        deviations.update(result["deviation_types"])
    assert routes == Counter({
        "RECONSTRUCTED_NO_MATERIAL_SIGNAL": 31,
        "RECONSTRUCTED_ALTERNATIVE": 3,
        "AGENT_VERIFIED": 2,
        "SOURCE_REQUIRED": 1,
        "HUMAN_CONTEXT_REQUIRED": 1,
        "SOURCE_ADAPTER_REQUIRED": 2,
    })
    assert data_validated == 40
    assert reconstructed == 38
    assert plan_compared == 37
    return {
        "status": "verified",
        "schema_version": "wake.demo_club_batch_report.v1",
        "counts": {
            "records_received": 40,
            "data_validated": data_validated,
            "sessions_reconstructed": reconstructed,
            "plan_compared": plan_compared,
            "agent_verified": investigation["execution_count"],
            "human_approved": 0,
        },
        "routing": dict(routes),
        "deviations": dict(deviations),
        "agent_cost": {
            "approximate_total_cost_usd": investigation[
                "approximate_total_cost_usd"
            ],
            "total_tokens": investigation["total_tokens"],
        },
        "longitudinal_synthesis_executed": False,
        "boundary": (
            "All records are real-informed synthetic. Deterministic reconstruction "
            "is not equivalent to agent verification or human approval."
        ),
    }


def main() -> None:
    print(json.dumps(verify_batch(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
