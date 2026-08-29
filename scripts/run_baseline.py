#!/usr/bin/env python3
"""Run or preview WAKE's frozen one-call baseline over public case summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config/baseline-v1.json"
DEFAULT_INPUTS = ROOT / "evaluation/baseline-inputs/v1"
DEFAULT_SCHEMA = ROOT / "schemas/analysis-output.schema.json"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: object) -> str:
    return sha256_bytes(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    )


def build_request(
    *,
    config: dict,
    prompt: str,
    summary: dict,
    output_schema: dict,
) -> dict:
    return {
        "model": config["model"],
        "instructions": prompt,
        "input": json.dumps(summary, sort_keys=True, separators=(",", ":")),
        "reasoning": {"effort": config["reasoning_effort"]},
        "max_output_tokens": config["max_output_tokens"],
        "service_tier": config["service_tier"],
        "store": config["store"],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "wake_analysis_output_v1_1",
                "schema": output_schema,
                "strict": True,
            }
        },
    }


def object_value(value: object, key: str, default: object = None) -> object:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def normalize_usage(usage: object) -> dict[str, int]:
    input_details = object_value(usage, "input_tokens_details", {})
    output_details = object_value(usage, "output_tokens_details", {})
    return {
        "input_tokens": int(object_value(usage, "input_tokens", 0) or 0),
        "output_tokens": int(object_value(usage, "output_tokens", 0) or 0),
        "total_tokens": int(object_value(usage, "total_tokens", 0) or 0),
        "cached_input_tokens": int(
            object_value(input_details, "cached_tokens", 0) or 0
        ),
        "reasoning_output_tokens": int(
            object_value(output_details, "reasoning_tokens", 0) or 0
        ),
    }


def estimate_cost_usd(usage: dict[str, int], pricing: dict) -> float:
    input_cost = (
        usage["input_tokens"]
        * float(pricing["input_usd_per_million_tokens"])
        / 1_000_000
    )
    output_cost = (
        usage["output_tokens"]
        * float(pricing["output_usd_per_million_tokens"])
        / 1_000_000
    )
    return round(input_cost + output_cost, 6)


def validate_output(output: dict, output_schema: dict, case_id: str) -> None:
    try:
        import jsonschema
    except ImportError as error:
        raise RuntimeError(
            "Missing dependency 'jsonschema'. Run 'uv sync' before --execute."
        ) from error
    jsonschema.validate(instance=output, schema=output_schema)
    if output["case_id"] != case_id:
        raise ValueError(
            f"Response case_id {output['case_id']!r} does not match {case_id!r}"
        )


def current_git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def execute_case(
    *,
    client: object,
    config: dict,
    prompt: str,
    summary: dict,
    output_schema: dict,
    output_dir: Path,
    run_id: str,
    now: Callable[[], str] = utc_now,
    monotonic_values: Iterator[float] | None = None,
    git_commit: str | None = None,
) -> dict[str, Path]:
    request = build_request(
        config=config,
        prompt=prompt,
        summary=summary,
        output_schema=output_schema,
    )
    monotonic_values = monotonic_values or iter(time.monotonic, None)
    started_at = now()
    started = next(monotonic_values)
    response = client.responses.create(**request)
    finished = next(monotonic_values)
    finished_at = now()

    if object_value(response, "status") != "completed":
        raise RuntimeError(f"Incomplete model response: {object_value(response, 'status')}")
    output = json.loads(str(object_value(response, "output_text")))
    validate_output(output, output_schema, summary["case_id"])
    usage = normalize_usage(object_value(response, "usage", {}))

    case_id = summary["case_id"]
    output_path = output_dir / "outputs" / f"{case_id}.json"
    manifest_path = output_dir / "cases" / f"{case_id}.run.json"
    write_json(output_path, output)
    write_json(
        manifest_path,
        {
            "schema_version": "wake.evaluation_run_case.v1",
            "run_id": run_id,
            "workflow": config["workflow"],
            "case_id": case_id,
            "started_at": started_at,
            "finished_at": finished_at,
            "runtime_ms": round((finished - started) * 1000),
            "git_commit": git_commit or current_git_commit(),
            "configuration": {
                "provider": config["provider"],
                "api": config["api"],
                "model_requested": config["model"],
                "reasoning_effort": config["reasoning_effort"],
                "max_output_tokens": config["max_output_tokens"],
                "service_tier": config["service_tier"],
                "store": config["store"],
                "temperature": None,
                "config_sha256": sha256_json(config),
            },
            "inputs": {
                "summary_id": summary["summary_id"],
                "summary_request_sha256": sha256_bytes(request["input"].encode()),
                "prompt_sha256": sha256_bytes(prompt.encode()),
                "output_schema_sha256": sha256_json(output_schema),
            },
            "response": {
                "id": object_value(response, "id"),
                "model": object_value(response, "model"),
                "status": object_value(response, "status"),
            },
            "usage": usage,
            "pricing": config["pricing"],
            "approximate_cost_usd": estimate_cost_usd(usage, config["pricing"]),
        },
    )
    return {"output_path": output_path, "manifest_path": manifest_path}


def selected_summaries(bundle: Path, case_ids: list[str]) -> list[Path]:
    manifest = read_json(bundle / "manifest.json")
    available = manifest["summaries"]
    selected = case_ids or sorted(available)
    unknown = sorted(set(selected) - set(available))
    if unknown:
        raise ValueError(f"Unknown case IDs: {', '.join(unknown)}")
    return [bundle / available[case_id]["path"] for case_id in selected]


def write_dry_run(
    *,
    config: dict,
    prompt: str,
    summaries: list[dict],
    output_schema: dict,
    output_dir: Path,
) -> Path:
    entries = {}
    for summary in summaries:
        request = build_request(
            config=config,
            prompt=prompt,
            summary=summary,
            output_schema=output_schema,
        )
        path = output_dir / "requests" / f"{summary['case_id']}.json"
        write_json(path, request)
        entries[summary["case_id"]] = {
            "path": str(path.relative_to(output_dir)),
            "sha256": sha256_path(path),
            "bytes": path.stat().st_size,
        }
    manifest_path = output_dir / "dry-run-manifest.json"
    write_json(
        manifest_path,
        {
            "schema_version": "wake.baseline_dry_run.v1",
            "run_id": output_dir.name,
            "workflow": config["workflow"],
            "created_at": utc_now(),
            "api_called": False,
            "config_sha256": sha256_json(config),
            "requests": entries,
        },
    )
    return manifest_path


def default_output_dir(mode: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return ROOT / "evaluation/runs/baseline-v1" / f"{timestamp}-{mode}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="Call the OpenAI API.")
    parser.add_argument("--case", action="append", default=[], dest="case_ids")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()

    config = read_json(args.config)
    prompt = (ROOT / "prompts/baseline-v1.md").read_text(encoding="utf-8")
    output_schema = read_json(DEFAULT_SCHEMA)
    summary_paths = selected_summaries(DEFAULT_INPUTS, args.case_ids)
    summaries = [read_json(path) for path in summary_paths]
    mode = "execute" if args.execute else "dry-run"
    output_dir = args.output or default_output_dir(mode)

    if not args.execute:
        manifest = write_dry_run(
            config=config,
            prompt=prompt,
            summaries=summaries,
            output_schema=output_schema,
            output_dir=output_dir,
        )
        print(json.dumps({"mode": mode, "manifest": str(manifest)}, indent=2))
        return

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required with --execute.")
    try:
        from openai import OpenAI
    except ImportError as error:
        raise SystemExit("Missing dependency 'openai'. Run 'uv sync'.") from error

    client = OpenAI()
    run_id = output_dir.name
    artifacts = []
    for summary in summaries:
        result = execute_case(
            client=client,
            config=config,
            prompt=prompt,
            summary=summary,
            output_schema=output_schema,
            output_dir=output_dir,
            run_id=run_id,
        )
        artifacts.append({key: str(value) for key, value in result.items()})
    case_manifests = [read_json(Path(item["manifest_path"])) for item in artifacts]
    run_manifest = output_dir / "run-manifest.json"
    write_json(
        run_manifest,
        {
            "schema_version": "wake.evaluation_run.v1",
            "run_id": run_id,
            "workflow": config["workflow"],
            "created_at": utc_now(),
            "cases": [item["case_id"] for item in case_manifests],
            "total_usage": {
                key: sum(item["usage"][key] for item in case_manifests)
                for key in [
                    "input_tokens",
                    "output_tokens",
                    "total_tokens",
                    "cached_input_tokens",
                    "reasoning_output_tokens",
                ]
            },
            "approximate_total_cost_usd": round(
                sum(item["approximate_cost_usd"] for item in case_manifests), 6
            ),
            "case_manifests": [
                str(Path(item["manifest_path"]).relative_to(output_dir))
                for item in artifacts
            ],
        },
    )
    print(
        json.dumps(
            {"mode": mode, "run_manifest": str(run_manifest), "artifacts": artifacts},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
