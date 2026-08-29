#!/usr/bin/env python3
"""Build WAKE's public hero fixture from private rowing exports.

The script preserves the source schemas and failure modes while replacing dates,
coordinates, device identifiers, and workout identifiers. Private source paths and
hashes live in an ignored manifest and are never copied into the public fixture.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


EARTH_RADIUS_M = 6_371_008.8
SYNTHETIC_ORIGIN = (10.0, 10.0)
SYNTHETIC_SPEEDCOACH_START = datetime(2026, 1, 15, 6, 59, 50)

PUBLIC_FILENAMES = {
    "speedcoach": "speedcoach.csv",
    "ios_sensor": "mobile-ios-sensor.csv",
    "ios_workout": "mobile-ios-workout.csv",
    "ios_metadata": "mobile-ios-metadata.json",
    "android_sensor": "mobile-android-sensor.csv",
    "android_workout": "mobile-android-workout.csv",
    "android_metadata": "mobile-android-metadata.json",
}

PUBLIC_IDENTIFIERS = {
    "ios": {
        "workout_id": "fixture-session-ios",
        "device_model": "fixture-mobile-ios",
    },
    "android": {
        "workout_id": "fixture-session-android",
        "device_model": "fixture-mobile-android",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def format_iso(value: datetime, original: str, time_shift) -> str:
    shifted = value + time_shift
    if original.endswith("Z"):
        return shifted.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace(
            "+00:00", "Z"
        )
    return shifted.isoformat(timespec="milliseconds")


class CoordinateTransformer:
    """Move a small route to a synthetic origin while preserving local geometry."""

    def __init__(self, source_lat: float, source_lon: float) -> None:
        self.source_lat = source_lat
        self.source_lon = source_lon
        self.synthetic_lat, self.synthetic_lon = SYNTHETIC_ORIGIN

    def transform(self, latitude: str, longitude: str) -> tuple[str, str]:
        lat = float(latitude)
        lon = float(longitude)
        north_m = math.radians(lat - self.source_lat) * EARTH_RADIUS_M
        east_m = (
            math.radians(lon - self.source_lon)
            * EARTH_RADIUS_M
            * math.cos(math.radians(self.source_lat))
        )
        synthetic_lat = self.synthetic_lat + math.degrees(north_m / EARTH_RADIUS_M)
        synthetic_lon = self.synthetic_lon + math.degrees(
            east_m
            / (EARTH_RADIUS_M * math.cos(math.radians(self.synthetic_lat)))
        )
        return f"{synthetic_lat:.7f}", f"{synthetic_lon:.7f}"


def load_private_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    required = set(PUBLIC_FILENAMES)
    if set(manifest.get("sources", {})) != required:
        missing = sorted(required - set(manifest.get("sources", {})))
        extra = sorted(set(manifest.get("sources", {})) - required)
        raise ValueError(f"Private manifest keys mismatch; missing={missing}, extra={extra}")

    for source_name, source in manifest["sources"].items():
        source_path = Path(source["path"])
        if not source_path.is_file():
            raise FileNotFoundError(f"Missing private source for {source_name}: {source_path}")
        actual_hash = sha256(source_path)
        if actual_hash != source["sha256"]:
            raise ValueError(
                f"Private source hash mismatch for {source_name}: {actual_hash}"
            )
    return manifest


def find_speedcoach_anchor(path: Path) -> tuple[float, float]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            if len(row) < 2:
                continue
            try:
                lat, lon = float(row[-2]), float(row[-1])
            except ValueError:
                continue
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
    raise ValueError("No SpeedCoach GPS coordinate was found")


def find_speedcoach_start(path: Path) -> datetime:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            if row and row[0] == "Start Time:" and len(row) > 1:
                return datetime.strptime(row[1], "%m/%d/%Y %H:%M:%S")
    raise ValueError("No SpeedCoach start time was found")


def transform_speedcoach(
    source: Path,
    destination: Path,
    coordinates: CoordinateTransformer,
    redactions: dict[str, str],
) -> int:
    output: list[list[str]] = []
    with source.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            scrubbed = list(row)
            for index, value in enumerate(scrubbed):
                for private_value, public_value in redactions.items():
                    value = value.replace(private_value, public_value)
                scrubbed[index] = value
            if scrubbed and scrubbed[0] == "Start Time:" and len(scrubbed) > 1:
                scrubbed[1] = SYNTHETIC_SPEEDCOACH_START.strftime("%m/%d/%Y %H:%M:%S")
            if len(scrubbed) >= 2:
                try:
                    float(scrubbed[-2])
                    float(scrubbed[-1])
                except ValueError:
                    pass
                else:
                    scrubbed[-2], scrubbed[-1] = coordinates.transform(
                        scrubbed[-2], scrubbed[-1]
                    )
            output.append(scrubbed)

    with destination.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle, lineterminator="\n").writerows(output)
    return len(output)


def should_keep_sensor_row(row: dict[str, str], previous_gps: tuple[str, str] | None) -> bool:
    gps = (row.get("latitude", ""), row.get("longitude", ""))
    return previous_gps is None or gps != previous_gps


def transform_sensor(
    source: Path, destination: Path, coordinates: CoordinateTransformer, time_shift
) -> int:
    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"Sensor file has no header: {source}")
        rows = list(reader)

    kept: list[dict[str, str]] = []
    previous_gps: tuple[str, str] | None = None
    for index, row in enumerate(rows):
        keep = should_keep_sensor_row(row, previous_gps) or index == len(rows) - 1
        current_gps = (row.get("latitude", ""), row.get("longitude", ""))
        if keep:
            transformed = dict(row)
            transformed["timestamp"] = str(int(row["timestamp"]) + int(time_shift.total_seconds() * 1000))
            if row.get("latitude") and row.get("longitude"):
                transformed["latitude"], transformed["longitude"] = coordinates.transform(
                    row["latitude"], row["longitude"]
                )
            kept.append(transformed)
        previous_gps = current_gps

    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=reader.fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(kept)
    return len(kept)


def transform_workout(
    source: Path,
    destination: Path,
    coordinates: CoordinateTransformer,
    platform: str,
    time_shift,
) -> int:
    identity = PUBLIC_IDENTIFIERS[platform]
    output: list[list[str]] = []
    in_workout_logs = False

    with source.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            transformed = list(row)
            if transformed == [
                "timestamp",
                "latitude",
                "longitude",
                "speed",
                "split_seconds",
                "spm",
                "stroke_count",
                "heart_rate",
                "accelx",
                "accely",
                "accelz",
            ]:
                in_workout_logs = True
            elif len(transformed) >= 2 and transformed[0] == "session_id":
                transformed[1] = identity["workout_id"]
            elif len(transformed) >= 2 and transformed[0] == "device_model":
                transformed[1] = identity["device_model"]
            elif len(transformed) >= 2 and transformed[0] in {"start_time", "end_time"}:
                transformed[1] = format_iso(parse_iso(transformed[1]), transformed[1], time_shift)
            elif in_workout_logs and len(transformed) >= 3 and transformed[0]:
                transformed[0] = format_iso(parse_iso(transformed[0]), transformed[0], time_shift)
                transformed[1], transformed[2] = coordinates.transform(
                    transformed[1], transformed[2]
                )
            output.append(transformed)

    with destination.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle, lineterminator="\n").writerows(output)
    return len(output)


def transform_metadata(source: Path, destination: Path, platform: str, time_shift) -> int:
    metadata = json.loads(source.read_text(encoding="utf-8"))
    identity = PUBLIC_IDENTIFIERS[platform]
    metadata["workoutId"] = identity["workout_id"]
    metadata["deviceModel"] = identity["device_model"]
    metadata["startTime"] = format_iso(
        parse_iso(metadata["startTime"]), metadata["startTime"], time_shift
    )
    destination.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return len(metadata)


def iter_generated_files(source_dir: Path) -> Iterable[Path]:
    for filename in PUBLIC_FILENAMES.values():
        yield source_dir / filename


def verify_private_values_removed(source_dir: Path, forbidden_values: list[str]) -> None:
    for path in iter_generated_files(source_dir):
        text = path.read_text(encoding="utf-8")
        for value in forbidden_values:
            if value and value in text:
                raise ValueError(f"Private value remained in generated file: {path.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/fixtures/case-001-misaligned-double-scull"),
    )
    args = parser.parse_args()

    manifest = load_private_manifest(args.source_manifest)
    source_paths = {
        name: Path(value["path"]) for name, value in manifest["sources"].items()
    }
    source_dir = args.output / "input" / "sources"
    source_dir.mkdir(parents=True, exist_ok=True)

    anchor = find_speedcoach_anchor(source_paths["speedcoach"])
    coordinates = CoordinateTransformer(*anchor)
    time_shift = SYNTHETIC_SPEEDCOACH_START - find_speedcoach_start(
        source_paths["speedcoach"]
    )
    row_counts: dict[str, int] = {}

    row_counts["speedcoach"] = transform_speedcoach(
        source_paths["speedcoach"],
        source_dir / PUBLIC_FILENAMES["speedcoach"],
        coordinates,
        manifest["speedcoach_redactions"],
    )
    for platform in ("ios", "android"):
        sensor_key = f"{platform}_sensor"
        workout_key = f"{platform}_workout"
        metadata_key = f"{platform}_metadata"
        row_counts[sensor_key] = transform_sensor(
            source_paths[sensor_key],
            source_dir / PUBLIC_FILENAMES[sensor_key],
            coordinates,
            time_shift,
        )
        row_counts[workout_key] = transform_workout(
            source_paths[workout_key],
            source_dir / PUBLIC_FILENAMES[workout_key],
            coordinates,
            platform,
            time_shift,
        )
        row_counts[metadata_key] = transform_metadata(
            source_paths[metadata_key],
            source_dir / PUBLIC_FILENAMES[metadata_key],
            platform,
            time_shift,
        )

    verify_private_values_removed(source_dir, manifest["forbidden_public_values"])

    public_manifest = {
        "schema": "wake.fixture_source_manifest.v1",
        "fixture_id": "case-001-misaligned-double-scull",
        "generator": "scripts/build_hero_fixture.py",
        "transformation": {
            "version": 1,
            "synthetic_speedcoach_start": "2026-01-15T06:59:50-03:00",
            "synthetic_coordinate_origin": {"latitude": 10.0, "longitude": 10.0},
            "mobile_sensor_sampling": "first row of each distinct GPS position plus final row",
        },
        "files": {},
    }
    for source_name, path in zip(PUBLIC_FILENAMES, iter_generated_files(source_dir)):
        public_manifest["files"][str(path.relative_to(args.output))] = {
            "source_role": source_name,
            "sha256": sha256(path),
            "rows_or_fields": row_counts[source_name],
            "bytes": path.stat().st_size,
        }

    manifest_path = args.output / "source-manifest.json"
    manifest_path.write_text(json.dumps(public_manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Built {args.output} with {len(public_manifest['files'])} source files")


if __name__ == "__main__":
    main()
