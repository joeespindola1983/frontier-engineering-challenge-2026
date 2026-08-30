#!/usr/bin/env python3
"""Verify the zero-cost longitudinal pilot preflight and frozen requests."""

from __future__ import annotations

import json
from pathlib import Path

from run_baseline import sha256_path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "evaluation" / "longitudinal-pilot" / "v1" / "preflight"


def verify_pilot_directory(directory: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = directory / "dry-run-manifest.json"
    if not manifest_path.is_file():
        return ["Missing longitudinal pilot dry-run manifest."]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        return [f"Unreadable longitudinal pilot manifest: {error}"]
    if manifest.get("schema_version") != "wake.longitudinal_pilot_dry_run.v1":
        errors.append("Unexpected longitudinal pilot manifest schema.")
    if manifest.get("api_called") is not False:
        errors.append("Preflight must explicitly record api_called=false.")
    requests = manifest.get("requests", [])
    if manifest.get("request_count") != 4 or len(requests) != 4:
        errors.append("Preflight must freeze exactly four requests.")
    if manifest.get("authorization", {}).get("required_total_usd") != 0.8:
        errors.append("Preflight authorization gate must total US$0.80.")
    if manifest.get("saved_reports", {}).get("count") != 0:
        errors.append("An unexecuted preflight cannot claim saved model reports.")
    seen: set[tuple[str, str]] = set()
    for item in requests:
        key = (str(item.get("pilot_id")), str(item.get("workflow")))
        if key in seen:
            errors.append(f"Duplicate frozen request: {key[0]} {key[1]}.")
        seen.add(key)
        path = directory / str(item.get("path", ""))
        if not path.is_file():
            errors.append(f"Missing frozen request: {item.get('path')}.")
            continue
        if sha256_path(path) != item.get("sha256"):
            errors.append(f"Frozen request hash mismatch: {item.get('path')}.")
        try:
            request = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append(f"Frozen request is not valid JSON: {item.get('path')}.")
            continue
        if request.get("store") is not False:
            errors.append(f"Frozen request must use store=false: {item.get('path')}.")
        if request.get("model") != "gpt-5.6-terra":
            errors.append(f"Frozen request model changed: {item.get('path')}.")
        if request.get("reasoning") != {"effort": "medium"}:
            errors.append(f"Frozen request reasoning effort changed: {item.get('path')}.")
    expected = {
        (pilot_id, workflow)
        for pilot_id in ("athlete-lucas", "club-coach")
        for workflow in ("DIRECT_BASELINE", "WAKE_BOUNDED_AGENT")
    }
    if seen != expected:
        errors.append("Frozen request matrix does not match the two-case comparison.")
    return errors


def main() -> None:
    errors = verify_pilot_directory(DEFAULT_DIRECTORY)
    if errors:
        raise SystemExit("\n".join(errors))
    print("Verified longitudinal pilot preflight: 2 cases, 4 zero-cost frozen requests.")


if __name__ == "__main__":
    main()
