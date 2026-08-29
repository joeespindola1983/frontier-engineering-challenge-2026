#!/usr/bin/env python3
"""Task-level product service for the WAKE coach interface.

The default service replays committed public agent output. Live execution is
available only when the server is started with ``--allow-live`` and a caller
explicitly requests ``mode: live``.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import csv
import hashlib
import io
import json
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

import jsonschema

from run_baseline import current_git_commit, read_json, utc_now
from wake_agent import (
    DEFAULT_CONFIG,
    DEFAULT_INPUTS,
    DEFAULT_PROMPT,
    DEFAULT_SCHEMA,
    public_case_input_dir,
    run_agent_case,
)


ROOT = Path(__file__).resolve().parents[1]
REPLAY_OUTPUTS = ROOT / "evaluation/runs/comparison-v1-20260829/agent/outputs"
PUBLIC_REPLAY_CASE_ID = "case-002-wind-shift-plan-deviation"
VALID_ANSWERS = {"YES", "NO", "UNKNOWN"}
SOURCE_KINDS = {"PLAN", "SPEEDCOACH", "MOBILE", "ENVIRONMENT", "CONTEXT"}
SOURCE_FILENAMES = {
    "PLAN": "plan.json",
    "SPEEDCOACH": "speedcoach.csv",
    "MOBILE": "mobile.csv",
    "ENVIRONMENT": "environment.json",
    "CONTEXT": "context.json",
}
MAX_SOURCE_BYTES = 10 * 1024 * 1024
NORMALIZED_TELEMETRY_COLUMNS = {
    "elapsed_s",
    "distance_m",
    "speed_m_s",
    "stroke_rate_spm",
}


def equipment_from_answer(answer: str) -> dict:
    if answer == "YES":
        return {
            "status": "HUMAN_CONFIRMED",
            "value": True,
            "source": "Coach confirmation",
            "statement": (
                "The coach confirmed that the resistance band was used for "
                "repetitions 1–3 and removed before repetition 4."
            ),
        }
    if answer == "NO":
        return {
            "status": "HUMAN_CONFIRMED",
            "value": False,
            "source": "Coach confirmation",
            "statement": (
                "The coach confirmed that the prescribed resistance-band "
                "change was not completed as planned."
            ),
        }
    return {
        "status": "UNKNOWN",
        "value": None,
        "source": None,
        "statement": (
            "Resistance-band use and removal cannot be confirmed from the "
            "supplied telemetry or human context."
        ),
    }


class WakeProductService:
    """In-process application service with explicit checkpoint transitions."""

    def __init__(
        self,
        *,
        root: Path = ROOT,
        live_runner: Callable[[str], dict] | None = None,
    ) -> None:
        self.root = root
        self.live_runner = live_runner
        self.investigations: dict[str, dict] = {}
        self.briefings: dict[str, dict] = {}
        self.goals: dict[str, dict] = {}
        self.sources: dict[str, dict] = {}

    def _validate_json_source(self, kind: str, content: bytes) -> str:
        try:
            value = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid {kind.lower()} JSON.") from error

        schema_name = {
            "PLAN": "training-plan.schema.json",
            "ENVIRONMENT": "environment-timeline.schema.json",
        }.get(kind)
        if schema_name:
            schema = read_json(self.root / "schemas" / schema_name)
            try:
                jsonschema.validate(instance=value, schema=schema)
            except jsonschema.ValidationError as error:
                label = "training plan" if kind == "PLAN" else "environment timeline"
                raise ValueError(f"Invalid {label}: {error.message}") from error
        elif not isinstance(value, dict) or not {
            "schema_version",
            "case_id",
            "investigation_request",
        }.issubset(value):
            raise ValueError("Invalid context JSON: required fields are missing.")

        return {
            "PLAN": "WAKE_TRAINING_PLAN_JSON",
            "ENVIRONMENT": "WAKE_ENVIRONMENT_TIMELINE_JSON",
            "CONTEXT": "WAKE_SESSION_CONTEXT_JSON",
        }[kind]

    def _validate_csv_source(self, kind: str, content: bytes) -> str:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise ValueError(f"Invalid {kind.lower()} CSV encoding.") from error
        if not text.strip():
            raise ValueError(f"Empty {kind.lower()} CSV.")

        if kind == "SPEEDCOACH" and "\nPer-Stroke Data:\n" in f"\n{text}":
            return "SPEEDCOACH_VENDOR_CSV"

        rows = csv.reader(io.StringIO(text))
        header = next(rows, [])
        columns = {column.strip() for column in header}
        if NORMALIZED_TELEMETRY_COLUMNS.issubset(columns):
            return "WAKE_NORMALIZED_TELEMETRY_CSV"
        if kind == "MOBILE" and {
            "sampleType",
            "timestamp",
            "distance",
            "latitude",
            "longitude",
            "speed",
        }.issubset(columns):
            return "WAKE_MOBILE_SENSOR_CSV"
        raise ValueError(
            f"Invalid {kind.lower()} telemetry: required columns are missing."
        )

    def upload_source(self, *, kind: str, name: str, content: bytes) -> dict:
        kind = kind.upper()
        if kind not in SOURCE_KINDS:
            raise ValueError(f"Unsupported source kind: {kind}")
        if (
            not name
            or name in {".", ".."}
            or Path(name).name != name
            or "/" in name
            or "\\" in name
        ):
            raise ValueError("Source file name must not contain a path.")
        if not content:
            raise ValueError("Source content is empty.")
        if len(content) > MAX_SOURCE_BYTES:
            raise ValueError("Source exceeds the 10 MiB prototype limit.")

        source_format = (
            self._validate_json_source(kind, content)
            if kind in {"PLAN", "ENVIRONMENT", "CONTEXT"}
            else self._validate_csv_source(kind, content)
        )
        digest = hashlib.sha256(content).hexdigest()
        source_id = f"source-{kind.lower()}-{digest[:12]}"
        stored = {
            "source_id": source_id,
            "kind": kind,
            "name": name,
            "status": "READY",
            "format": source_format,
            "sha256": digest,
            "size_bytes": len(content),
            "_content": content,
        }
        self.sources[source_id] = stored
        return {key: value for key, value in stored.items() if not key.startswith("_")}

    def create_investigation_from_sources(
        self,
        source_ids: list[str],
        *,
        mode: str = "replay",
    ) -> dict:
        try:
            sources = [self.sources[source_id] for source_id in source_ids]
        except KeyError as error:
            raise ValueError(f"Unknown source: {error.args[0]}") from error
        grouped = {source["kind"]: source for source in sources}
        if len(sources) != len(SOURCE_KINDS) or set(grouped) != SOURCE_KINDS:
            raise ValueError(
                "An investigation requires one PLAN, SPEEDCOACH, MOBILE, "
                "ENVIRONMENT, and CONTEXT source."
            )

        if mode != "replay":
            raise ValueError(
                "New uploaded bundles are not connected to live execution yet."
            )
        public_input = self.root / "data/fixtures" / PUBLIC_REPLAY_CASE_ID / "input"
        exact_public_bundle = all(
            source["_content"]
            == (public_input / SOURCE_FILENAMES[kind]).read_bytes()
            for kind, source in grouped.items()
        )
        if not exact_public_bundle:
            raise ValueError(
                "Replay is available only for the committed public demonstration "
                "bundle; new uploaded evidence requires a future live source adapter."
            )
        return self.create_investigation(PUBLIC_REPLAY_CASE_ID, mode="replay")

    def _public_case_bundle(self, case_id: str, analysis: dict) -> dict:
        public_case_input_dir(self.root, case_id)
        summary_path = self.root / "evaluation/baseline-inputs/v1" / f"{case_id}.json"
        context_path = self.root / "data/fixtures" / case_id / "input/context.json"
        if not summary_path.is_file() or not context_path.is_file():
            raise ValueError(f"Unsupported product case: {case_id}")
        summary = read_json(summary_path)
        context = read_json(context_path)
        return {
            "analysis": analysis,
            "summary": {
                "case_id": summary["case_id"],
                "plan": summary.get("plan"),
                "cross_source_findings": summary.get("cross_source_findings", []),
            },
            "context": {
                "input_notice": context["input_notice"],
                "session_candidate": context["session_candidate"],
            },
        }

    def _replay_analysis(self, case_id: str) -> dict:
        path = self.root / REPLAY_OUTPUTS.relative_to(ROOT) / f"{case_id}.json"
        if not path.is_file():
            raise ValueError(f"No committed public replay exists for {case_id}")
        return read_json(path)

    def create_investigation(self, case_id: str, *, mode: str = "replay") -> dict:
        if mode not in {"replay", "live"}:
            raise ValueError(f"Unsupported investigation mode: {mode}")
        if mode == "live":
            if self.live_runner is None:
                raise ValueError("Live agent execution is disabled for this service.")
            analysis = self.live_runner(case_id)
        else:
            analysis = self._replay_analysis(case_id)
        if analysis.get("case_id") != case_id:
            raise ValueError("Agent output does not match the requested case.")

        review = self._public_case_bundle(case_id, analysis)
        investigation_id = f"investigation-{case_id}"
        checkpoint_id = f"checkpoint-{case_id}"
        goal_id = f"goal-{case_id}"
        questions = analysis.get("follow_up_questions", [])
        result = {
            "investigation_id": investigation_id,
            "checkpoint_id": checkpoint_id,
            "goal_id": goal_id,
            "case_id": case_id,
            "mode": mode,
            "status": "QUESTION_REQUIRED" if questions else "READY_FOR_REVIEW",
            "review": review,
        }
        self.investigations[investigation_id] = result
        self.goals.setdefault(goal_id, self._empty_goal(review))
        return result

    def get_investigation(self, investigation_id: str) -> dict:
        if investigation_id not in self.investigations:
            raise KeyError(f"Unknown investigation: {investigation_id}")
        return self.investigations[investigation_id]

    def answer_checkpoint(self, checkpoint_id: str, *, answer: str) -> dict:
        if answer not in VALID_ANSWERS:
            raise ValueError(f"Unsupported checkpoint answer: {answer}")
        investigation = next(
            (
                item
                for item in self.investigations.values()
                if item["checkpoint_id"] == checkpoint_id
            ),
            None,
        )
        if investigation is None:
            raise KeyError(f"Unknown checkpoint: {checkpoint_id}")
        briefing = self._build_briefing(investigation["review"], answer)
        self.briefings[briefing["briefingId"]] = briefing
        investigation["status"] = "VERIFIED"
        investigation["briefing_id"] = briefing["briefingId"]
        return briefing

    def approve_briefing(self, briefing_id: str) -> dict:
        if briefing_id not in self.briefings:
            raise KeyError(f"Unknown briefing: {briefing_id}")
        briefing = self.briefings[briefing_id]
        goal_id = f"goal-{briefing['sessionId']}"
        goal = self._approved_goal(briefing)
        self.goals[goal_id] = goal
        briefing["pendingApproval"] = False
        return goal

    def get_goal(self, goal_id: str) -> dict:
        if goal_id not in self.goals:
            raise KeyError(f"Unknown goal: {goal_id}")
        return self.goals[goal_id]

    def _work_intervals(self, review: dict) -> list[dict]:
        intervals = []
        work_index = 0
        for segment in review["analysis"].get("segments", []):
            if segment.get("kind") != "WORK":
                continue
            work_index += 1
            target = {"min": 19, "max": 21} if work_index <= 3 else {"min": 22, "max": 24}
            average_spm = float(segment["average_spm"])
            intervals.append(
                {
                    "segmentId": segment["segment_id"],
                    "index": work_index,
                    "plannedDistanceM": 1000,
                    "durationS": round(
                        float(segment["end_offset_s"])
                        - float(segment["start_offset_s"]),
                        3,
                    ),
                    "averageSpm": average_spm,
                    "targetMinSpm": target["min"],
                    "targetMaxSpm": target["max"],
                    "status": (
                        "WITHIN_RANGE"
                        if target["min"] <= average_spm <= target["max"]
                        else "DEVIATION"
                    ),
                }
            )
        return intervals

    def _build_briefing(self, review: dict, answer: str) -> dict:
        analysis = review["analysis"]
        equipment = equipment_from_answer(answer)
        environment = analysis.get("environment_assessment") or {}
        return {
            "briefingId": f"briefing-{analysis['case_id']}",
            "sessionId": analysis["case_id"],
            "title": "6 × 1 km · Men's 2x",
            "verificationStatus": "VERIFIED",
            "headline": (
                "Planned structure completed; one stroke-rate deviation needs "
                "coach review."
            ),
            "summary": analysis["coach_briefing"],
            "workIntervals": self._work_intervals(review),
            "environment": environment,
            "equipment": equipment,
            "findings": [
                {
                    "status": "SUPPORTED",
                    "title": "All six prescribed work intervals were reconstructed.",
                    "explanation": (
                        "The work/recovery structure and order are supported by "
                        "the plan and SpeedCoach evidence."
                    ),
                    "evidenceRefs": ["input/plan.json", "input/speedcoach.csv"],
                },
                {
                    "status": "ATTENTION",
                    "title": (
                        "Work interval five missed its prescribed stroke-rate range."
                    ),
                    "explanation": (
                        "It averaged 19.99 SPM against the prescribed 22–24 SPM range."
                    ),
                    "evidenceRefs": ["input/plan.json", "input/speedcoach.csv"],
                },
                {
                    "status": equipment["status"],
                    "title": (
                        "Resistance-band use remains unknown."
                        if equipment["status"] == "UNKNOWN"
                        else "Resistance-band context was confirmed by the coach."
                    ),
                    "explanation": equipment["statement"],
                    "evidenceRefs": (
                        []
                        if equipment["status"] == "UNKNOWN"
                        else ["human-confirmation/resistance-band"]
                    ),
                },
            ],
            "limitations": analysis.get("abstentions", []),
            "pendingApproval": True,
        }

    def _empty_goal(self, review: dict) -> dict:
        return {
            "goalId": f"goal-{review['analysis']['case_id']}",
            "title": "Regatta preparation · Men's 2x",
            "currentConclusion": (
                "No session evidence has been approved for this goal in the prototype."
            ),
            "approvedSessions": [],
            "unresolvedQuestions": [],
            "nextUsefulEvidence": [],
        }

    def _approved_goal(self, briefing: dict) -> dict:
        return {
            "goalId": f"goal-{briefing['sessionId']}",
            "title": "Regatta preparation · Men's 2x",
            "currentConclusion": (
                "One approved session supports completion of the planned structure "
                "and identifies a fifth-interval stroke-rate deviation; it does not "
                "establish a longitudinal trend."
            ),
            "approvedSessions": [
                {
                    "sessionId": briefing["sessionId"],
                    "title": briefing["title"],
                    "approval": "COACH_APPROVED",
                    "summary": (
                        "Six work intervals reconstructed; work five below target SPM; "
                        "environmental change limits pace interpretation."
                    ),
                    "equipment": briefing["equipment"],
                }
            ],
            "unresolvedQuestions": [
                "Why did work interval five fall below the prescribed stroke-rate range?",
                *(
                    ["Was the resistance-band change completed?"]
                    if briefing["equipment"]["status"] == "UNKNOWN"
                    else []
                ),
            ],
            "nextUsefulEvidence": [
                "A comparable session with the same plan and more stable conditions.",
                "Coach or athlete context recorded immediately after the outing.",
            ],
        }


class WakeProductApi:
    """Small route adapter kept independent from the HTTP server for tests."""

    def __init__(self, service: WakeProductService) -> None:
        self.service = service

    def handle(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        body = body or {}
        parts = [part for part in urlsplit(path).path.split("/") if part]
        if method == "POST" and parts == ["api", "sources"]:
            try:
                content = base64.b64decode(
                    str(body.get("content_base64", "")),
                    validate=True,
                )
            except (binascii.Error, ValueError) as error:
                raise ValueError("Source content_base64 is invalid.") from error
            return 201, self.service.upload_source(
                kind=str(body.get("kind", "")),
                name=str(body.get("name", "")),
                content=content,
            )
        if method == "POST" and parts == ["api", "investigations"]:
            if "source_ids" in body:
                source_ids = body["source_ids"]
                if not isinstance(source_ids, list) or not all(
                    isinstance(source_id, str) for source_id in source_ids
                ):
                    raise ValueError("source_ids must be a list of strings.")
                return 201, self.service.create_investigation_from_sources(
                    source_ids,
                    mode=str(body.get("mode", "replay")),
                )
            return 201, self.service.create_investigation(
                str(body.get("case_id", "")),
                mode=str(body.get("mode", "replay")),
            )
        if method == "GET" and parts[:2] == ["api", "investigations"] and len(parts) == 3:
            return 200, self.service.get_investigation(parts[2])
        if (
            method == "POST"
            and len(parts) == 4
            and parts[:2] == ["api", "checkpoints"]
            and parts[3:] == ["answers"]
        ):
            return 200, self.service.answer_checkpoint(
                parts[2], answer=str(body.get("answer", ""))
            )
        if (
            method == "POST"
            and len(parts) == 4
            and parts[:2] == ["api", "briefings"]
            and parts[3] == "approve"
        ):
            return 200, self.service.approve_briefing(parts[2])
        if method == "GET" and parts[:2] == ["api", "goals"] and len(parts) == 3:
            return 200, self.service.get_goal(parts[2])
        raise KeyError(f"Unknown product endpoint: {method} {path}")


def build_live_runner(root: Path) -> Callable[[str], dict]:
    def execute(case_id: str) -> dict:
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is required for live mode.")
        from openai import OpenAI

        config = read_json(DEFAULT_CONFIG)
        summary = read_json(DEFAULT_INPUTS / f"{case_id}.json")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_dir = root / "evaluation/runs/product-live" / timestamp
        result = run_agent_case(
            client=OpenAI(),
            config=config,
            prompt=DEFAULT_PROMPT.read_text(encoding="utf-8"),
            summary=summary,
            input_dir=public_case_input_dir(root, case_id),
            output_schema=read_json(DEFAULT_SCHEMA),
            output_dir=output_dir,
            run_id=output_dir.name,
            now=utc_now,
            git_commit=current_git_commit(),
        )
        return read_json(result["output_path"])

    return execute


def make_handler(api: WakeProductApi, *, allowed_origin: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _headers(self, status: int) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()

        def _dispatch(self, method: str) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            try:
                status, payload = api.handle(method, self.path, body)
            except KeyError as error:
                status, payload = 404, {"error": str(error)}
            except ValueError as error:
                status, payload = 400, {"error": str(error)}
            except Exception:
                status, payload = 500, {"error": "Agent runtime unavailable."}
            self._headers(status)
            self.wfile.write(json.dumps(payload).encode("utf-8"))

        def do_GET(self) -> None:  # noqa: N802
            self._dispatch("GET")

        def do_POST(self) -> None:  # noqa: N802
            self._dispatch("POST")

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._headers(204)

        def log_message(self, format: str, *args: object) -> None:
            return

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8788, type=int)
    parser.add_argument("--origin", default="http://localhost:3000")
    parser.add_argument("--allow-live", action="store_true")
    args = parser.parse_args()

    service = WakeProductService(
        live_runner=build_live_runner(ROOT) if args.allow_live else None
    )
    api = WakeProductApi(service)
    server = ThreadingHTTPServer(
        (args.host, args.port),
        make_handler(api, allowed_origin=args.origin),
    )
    print(f"WAKE product service listening on http://{args.host}:{args.port}")
    print(f"Live agent execution: {'enabled' if args.allow_live else 'disabled'}")
    server.serve_forever()


if __name__ == "__main__":
    main()
