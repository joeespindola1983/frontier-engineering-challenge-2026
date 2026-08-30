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
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

import jsonschema

from bundle_assembler import assemble_case_summary
from run_baseline import current_git_commit, read_json, utc_now
from source_adapters import normalize_source
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
SOURCE_ORDER = ("PLAN", "SPEEDCOACH", "MOBILE", "ENVIRONMENT", "CONTEXT")
SOURCE_KINDS = set(SOURCE_ORDER)
CORE_SOURCE_KINDS = {"PLAN", "SPEEDCOACH"}
SOURCE_FILENAMES = {
    "PLAN": "plan.json",
    "SPEEDCOACH": "speedcoach.csv",
    "MOBILE": "mobile.csv",
    "ENVIRONMENT": "environment.json",
    "CONTEXT": "context.json",
}
MAX_SOURCE_BYTES = 10 * 1024 * 1024


def human_confirmation_from_answer(question: str, answer: str) -> dict:
    if answer in {"YES", "NO"}:
        label = "Yes" if answer == "YES" else "No"
        return {
            "status": "HUMAN_CONFIRMED",
            "answer": answer,
            "value": answer == "YES",
            "source": "Coach confirmation",
            "question": question,
            "statement": f'Coach answered "{label}" to: {question}',
        }
    return {
        "status": "UNKNOWN",
        "answer": "UNKNOWN",
        "value": None,
        "source": None,
        "question": question,
        "statement": f"No human confirmation was supplied for: {question}",
    }


class WakeProductService:
    """In-process application service with explicit checkpoint transitions."""

    def __init__(
        self,
        *,
        root: Path = ROOT,
        live_runner: Callable[[str], dict] | None = None,
        bundle_live_runner: Callable[[dict, dict[str, bytes]], dict] | None = None,
    ) -> None:
        self.root = root
        self.live_runner = live_runner
        self.bundle_live_runner = bundle_live_runner
        self.investigations: dict[str, dict] = {}
        self.briefings: dict[str, dict] = {}
        self.goals: dict[str, dict] = {}
        self.sources: dict[str, dict] = {}
        self.source_bundles: dict[str, dict] = {}
        self.bundle_results: dict[str, dict] = {}

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

        normalization = None
        normalized_content = None
        if kind in {"PLAN", "ENVIRONMENT", "CONTEXT"}:
            source_format = self._validate_json_source(kind, content)
        else:
            normalized = normalize_source(
                kind=kind,
                content=content,
                source_ref=f"upload/{name}",
            )
            source_format = normalized.source_format
            normalization = normalized.report
            normalized_content = normalized.normalized_csv
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
            **({"normalization": normalization} if normalization else {}),
            "_content": content,
            "_normalized_content": normalized_content,
        }
        self.sources[source_id] = stored
        return {key: value for key, value in stored.items() if not key.startswith("_")}

    def get_source(self, source_id: str) -> dict:
        if source_id not in self.sources:
            raise KeyError(f"Unknown source: {source_id}")
        return {
            key: value
            for key, value in self.sources[source_id].items()
            if not key.startswith("_")
        }

    def _source_group(
        self,
        source_ids: list[str],
        *,
        required_kinds: set[str] = CORE_SOURCE_KINDS,
    ) -> dict[str, dict]:
        try:
            sources = [self.sources[source_id] for source_id in source_ids]
        except KeyError as error:
            raise ValueError(f"Unknown source: {error.args[0]}") from error
        grouped = {source["kind"]: source for source in sources}
        if len(grouped) != len(sources):
            raise ValueError("A source bundle cannot contain duplicate source kinds.")
        if not required_kinds.issubset(grouped):
            if required_kinds == CORE_SOURCE_KINDS:
                raise ValueError(
                    "A source bundle requires one PLAN and SPEEDCOACH source; "
                    "MOBILE, ENVIRONMENT, and CONTEXT are optional."
                )
            raise ValueError(
                "A source bundle requires one PLAN, SPEEDCOACH, MOBILE, "
                "ENVIRONMENT, and CONTEXT source."
            )
        return grouped

    def prepare_source_bundle(self, source_ids: list[str]) -> dict:
        """Build and retain an agent-ready summary without executing an agent."""
        grouped = self._source_group(source_ids)
        plan = json.loads(grouped["PLAN"]["_content"].decode("utf-8"))
        environment = (
            json.loads(grouped["ENVIRONMENT"]["_content"].decode("utf-8"))
            if "ENVIRONMENT" in grouped
            else None
        )
        context = (
            json.loads(grouped["CONTEXT"]["_content"].decode("utf-8"))
            if "CONTEXT" in grouped
            else None
        )
        telemetry_sources = [
            {
                "source_id": grouped[kind]["source_id"],
                "kind": kind,
                "evidence_ref": f"input/{SOURCE_FILENAMES[kind]}",
                "normalized_csv": grouped[kind]["_normalized_content"],
                "normalization": grouped[kind]["normalization"],
            }
            for kind in ("SPEEDCOACH", "MOBILE")
            if kind in grouped
        ]
        summary = assemble_case_summary(
            plan=plan,
            context=context,
            environment=environment,
            telemetry_sources=telemetry_sources,
            input_hashes={
                SOURCE_FILENAMES[kind]: source["sha256"]
                for kind, source in grouped.items()
            },
        )
        jsonschema.validate(
            instance=summary,
            schema=read_json(self.root / "schemas/case-summary.schema.json"),
        )
        serialized_summary = json.dumps(
            summary,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        summary_digest = hashlib.sha256(serialized_summary).hexdigest()
        bundle_id = f"source-bundle-{summary_digest[:16]}"
        response = {
            "bundle_id": bundle_id,
            "case_id": summary["case_id"],
            "status": "READY_FOR_LIVE",
            "summary_sha256": summary_digest,
            "source_count": len(grouped),
            "source_coverage": [
                {
                    "kind": kind,
                    "role": "CORE" if kind in CORE_SOURCE_KINDS else "ENHANCER",
                    "status": "PRESENT" if kind in grouped else "ABSENT",
                }
                for kind in SOURCE_ORDER
            ],
            "finding_types": [
                finding["type"] for finding in summary["cross_source_findings"]
            ],
            "source_quality": [
                {
                    "kind": source["kind"],
                    "quality_flags": source["quality_flags"],
                    "row_count": grouped[source["kind"]]["normalization"]["row_count"],
                }
                for source in summary["sources"]
            ],
            "evidence_gaps": summary["evidence_gaps"],
            "agent_called": False,
        }
        self.source_bundles[bundle_id] = {
            "summary": summary,
            "source_ids": list(source_ids),
            "response": response,
        }
        return response

    def execute_source_bundle(self, bundle_id: str, *, mode: str) -> tuple[dict, bool]:
        """Execute one prepared bundle only after explicit live authorization.

        Returns the result and whether it was newly created. Repeated requests in
        the same process return the recorded result instead of spending twice.
        """
        if mode != "live":
            raise ValueError("Prepared bundle execution requires explicit live mode.")
        if bundle_id not in self.source_bundles:
            raise ValueError(f"Unknown source bundle: {bundle_id}")
        execution_id = f"execution-{bundle_id}"
        if execution_id in self.bundle_results:
            return self.bundle_results[execution_id], False
        if self.bundle_live_runner is None:
            raise ValueError("Live prepared-bundle execution is disabled for this service.")

        bundle = self.source_bundles[bundle_id]
        grouped = self._source_group(bundle["source_ids"])
        evidence = {}
        for kind in SOURCE_ORDER:
            if kind not in grouped:
                continue
            source = grouped[kind]
            evidence[SOURCE_FILENAMES[kind]] = (
                source["_normalized_content"]
                if kind in {"SPEEDCOACH", "MOBILE"}
                else source["_content"]
            )
        analysis = self.bundle_live_runner(bundle["summary"], evidence)
        jsonschema.validate(
            instance=analysis,
            schema=read_json(self.root / "schemas/analysis-output.schema.json"),
        )
        if analysis.get("case_id") != bundle["summary"]["case_id"]:
            raise ValueError("Agent output does not match the prepared bundle.")
        summary = bundle["summary"]
        known_context = summary.get("known_context", {})
        review = {
            "analysis": analysis,
            "summary": {
                "case_id": summary["case_id"],
                "plan": summary.get("plan"),
                "sources": [
                    {
                        "source_id": source["source_id"],
                        "kind": source["kind"],
                        "evidence_refs": source["evidence_refs"],
                        "quality_flags": source["quality_flags"],
                    }
                    for source in summary["sources"]
                ],
                "cross_source_findings": summary["cross_source_findings"],
                "environment": (
                    {
                        "timeline_id": summary["environment"].get("timeline_id"),
                        "source": summary["environment"].get("source"),
                    }
                    if summary.get("environment")
                    else None
                ),
            },
            "context": {
                "input_notice": known_context.get(
                    "input_notice", "Coach-uploaded local evidence."
                ),
                "session_candidate": known_context.get("session_candidate", {}),
            },
        }
        investigation = self._register_investigation(
            review,
            mode="live",
            identity=bundle_id,
        )
        result = {
            "execution_id": execution_id,
            "bundle_id": bundle_id,
            "case_id": bundle["summary"]["case_id"],
            "mode": "live",
            "status": "AGENT_COMPLETED",
            "agent_called": True,
            "investigation_id": investigation["investigation_id"],
            "checkpoint_id": investigation["checkpoint_id"],
            "goal_id": investigation["goal_id"],
            "investigation_status": investigation["status"],
            "analysis": analysis,
            "review": review,
        }
        self.bundle_results[execution_id] = result
        return result, True

    def create_investigation_from_sources(
        self,
        source_ids: list[str],
        *,
        mode: str = "replay",
    ) -> dict:
        grouped = self._source_group(source_ids, required_kinds=SOURCE_KINDS)

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
        return self._register_investigation(review, mode=mode, identity=case_id)

    def _register_investigation(
        self,
        review: dict,
        *,
        mode: str,
        identity: str,
    ) -> dict:
        case_id = review["analysis"]["case_id"]
        investigation_id = f"investigation-{identity}"
        checkpoint_id = f"checkpoint-{identity}"
        goal_id = f"goal-{case_id}"
        questions = review["analysis"].get("follow_up_questions", [])
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
        briefing = self._build_briefing(
            investigation["review"],
            answer,
            goal_id=investigation["goal_id"],
        )
        self.briefings[briefing["briefingId"]] = briefing
        investigation["status"] = "VERIFIED"
        investigation["briefing_id"] = briefing["briefingId"]
        return briefing

    def approve_briefing(self, briefing_id: str) -> dict:
        if briefing_id not in self.briefings:
            raise KeyError(f"Unknown briefing: {briefing_id}")
        briefing = self.briefings[briefing_id]
        goal_id = briefing["goalId"]
        goal = self._approved_goal(briefing)
        self.goals[goal_id] = goal
        briefing["pendingApproval"] = False
        return goal

    def get_goal(self, goal_id: str) -> dict:
        if goal_id not in self.goals:
            raise KeyError(f"Unknown goal: {goal_id}")
        return self.goals[goal_id]

    def _planned_work_targets(self, review: dict) -> list[dict]:
        targets = []
        plan = review.get("summary", {}).get("plan") or {}
        for block in plan.get("blocks", []):
            if block.get("kind") != "WORK":
                continue
            stroke_rate = block.get("stroke_rate") or {}
            for _ in range(int(block.get("repetitions", 1))):
                targets.append(
                    {
                        "distance": block.get("distance_m"),
                        "min_spm": stroke_rate.get("min_spm"),
                        "max_spm": stroke_rate.get("max_spm"),
                    }
                )
        return targets

    def _work_intervals(self, review: dict) -> list[dict]:
        intervals = []
        work_index = 0
        targets = self._planned_work_targets(review)
        deviations = {
            deviation.get("segment_ref")
            for deviation in review["analysis"].get("deviations", [])
        }
        for segment in review["analysis"].get("segments", []):
            if segment.get("kind") != "WORK":
                continue
            work_index += 1
            target = targets[work_index - 1] if work_index <= len(targets) else {}
            average_spm = float(segment["average_spm"])
            target_min = target.get("min_spm")
            target_max = target.get("max_spm")
            intervals.append(
                {
                    "segmentId": segment["segment_id"],
                    "index": work_index,
                    "plannedDistanceM": target.get("distance") or 0,
                    "durationS": round(
                        float(segment["end_offset_s"])
                        - float(segment["start_offset_s"]),
                        3,
                    ),
                    "averageSpm": average_spm,
                    "targetMinSpm": target_min or average_spm,
                    "targetMaxSpm": target_max or average_spm,
                    "status": "DEVIATION"
                    if segment["segment_id"] in deviations
                    else "WITHIN_RANGE",
                }
            )
        return intervals

    def _session_title(self, review: dict) -> str:
        targets = self._planned_work_targets(review)
        distances = {target["distance"] for target in targets if target["distance"]}
        if len(distances) == 1:
            distance = distances.pop()
            distance_label = (
                f"{distance / 1000:g} km"
                if distance >= 1000 and distance % 1000 == 0
                else f"{distance:g} m"
            )
        else:
            distance_label = "work intervals"
        candidate = review.get("context", {}).get("session_candidate") or {}
        boat = {
            "SINGLE_SCULL": "1x",
            "DOUBLE_SCULL": "2x",
            "QUADRUPLE_SCULL": "4x",
        }.get(candidate.get("boat_class"), candidate.get("world_rowing_code"))
        crew = {"MEN": "Men's", "WOMEN": "Women's", "MIXED": "Mixed"}.get(
            candidate.get("crew_category")
        )
        boat_label = " ".join(part for part in (crew, boat) if part)
        return f"{len(targets)} x {distance_label} · {boat_label or 'rowing session'}"

    def _build_briefing(self, review: dict, answer: str, *, goal_id: str) -> dict:
        analysis = review["analysis"]
        questions = analysis.get("follow_up_questions", [])
        question = questions[0] if questions else "Is there any coach context to add?"
        confirmation = human_confirmation_from_answer(question, answer)
        environment = analysis.get("environment_assessment") or {}
        intervals = self._work_intervals(review)
        deviations = analysis.get("deviations", [])
        deviation_count = len(deviations)
        interval_indexes = {
            interval["segmentId"]: interval["index"] for interval in intervals
        }
        findings = [
            {
                "status": "SUPPORTED",
                "title": f"{len(intervals)} prescribed work intervals were reconstructed.",
                "explanation": (
                    "The reconstruction uses the supplied training plan and "
                    "SpeedCoach evidence; it does not by itself establish technique."
                ),
                "evidenceRefs": ["input/plan.json", "input/speedcoach.csv"],
            }
        ]
        findings.extend(
            {
                "status": "ATTENTION",
                "title": (
                    "Session-level deviation needs attention."
                    if deviation.get("segment_ref") not in interval_indexes
                    else f"Work interval {interval_indexes[deviation['segment_ref']]} needs attention."
                ),
                "explanation": deviation["description"],
                "evidenceRefs": deviation.get("evidence_refs", []),
            }
            for deviation in deviations
        )
        if environment.get("summary"):
            findings.append(
                {
                    "status": "SUPPORTED_WITH_LIMITATION",
                    "title": "Environmental context retains a non-causal boundary.",
                    "explanation": environment["summary"],
                    "evidenceRefs": environment.get("evidence_refs", []),
                }
            )
        findings.append(
            {
                "status": confirmation["status"],
                "title": (
                    "Coach context remains unknown."
                    if confirmation["status"] == "UNKNOWN"
                    else "Coach context was human-confirmed."
                ),
                "explanation": confirmation["statement"],
                "evidenceRefs": (
                    []
                    if confirmation["status"] == "UNKNOWN"
                    else ["human-confirmation/checkpoint"]
                ),
            }
        )
        deviation_label = (
            "no plan deviations were reported"
            if not deviation_count
            else (
                f"{deviation_count} plan deviation"
                f"{'s need' if deviation_count != 1 else ' needs'} coach review"
            )
        )
        return {
            "briefingId": f"briefing-{analysis['case_id']}",
            "sessionId": analysis["case_id"],
            "goalId": goal_id,
            "scheduledDate": (review.get("summary", {}).get("plan") or {}).get(
                "scheduled_date"
            ),
            "title": self._session_title(review),
            "verificationStatus": "VERIFIED",
            "headline": f"{len(intervals)} work intervals reconstructed; {deviation_label}.",
            "summary": analysis["coach_briefing"],
            "workIntervals": intervals,
            "environment": environment,
            "humanConfirmation": confirmation,
            "findings": findings,
            "limitations": analysis.get("abstentions", []),
            "pendingApproval": True,
        }

    def _empty_goal(self, review: dict) -> dict:
        return {
            "goalId": f"goal-{review['analysis']['case_id']}",
            "title": f"Session learning · {self._session_title(review)}",
            "currentConclusion": (
                "No session evidence has been approved for this goal in the prototype."
            ),
            "approvedSessions": [],
            "unresolvedQuestions": [],
            "nextUsefulEvidence": [],
        }

    def _approved_goal(self, briefing: dict) -> dict:
        deviations = [
            finding["explanation"]
            for finding in briefing["findings"]
            if finding["status"] == "ATTENTION"
        ]
        confirmation = briefing["humanConfirmation"]
        return {
            "goalId": briefing["goalId"],
            "title": f"Session learning · {briefing['title']}",
            "currentConclusion": (
                f"One approved session preserves this result: {briefing['headline']} "
                "It does not establish a longitudinal trend."
            ),
            "approvedSessions": [
                {
                    "sessionId": briefing["sessionId"],
                    "scheduledDate": briefing["scheduledDate"],
                    "title": briefing["title"],
                    "approval": "COACH_APPROVED",
                    "summary": briefing["headline"],
                    "humanConfirmation": confirmation,
                }
            ],
            "unresolvedQuestions": [
                *deviations,
                *([confirmation["question"]] if confirmation["status"] == "UNKNOWN" else []),
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
        if method == "GET" and parts[:2] == ["api", "sources"] and len(parts) == 3:
            return 200, self.service.get_source(parts[2])
        if method == "POST" and parts == ["api", "source-bundles", "prepare"]:
            source_ids = body.get("source_ids")
            if not isinstance(source_ids, list) or not all(
                isinstance(source_id, str) for source_id in source_ids
            ):
                raise ValueError("source_ids must be a list of strings.")
            return 201, self.service.prepare_source_bundle(source_ids)
        if (
            method == "POST"
            and len(parts) == 4
            and parts[:2] == ["api", "source-bundles"]
            and parts[3] == "execute"
        ):
            result, created = self.service.execute_source_bundle(
                parts[2], mode=str(body.get("mode", ""))
            )
            return (201 if created else 200), result
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


def build_bundle_live_runner(
    root: Path,
) -> Callable[[dict, dict[str, bytes]], dict]:
    def execute(summary: dict, evidence: dict[str, bytes]) -> dict:
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is required for live mode.")
        from openai import OpenAI

        config = read_json(DEFAULT_CONFIG)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output_dir = root / "evaluation/runs/product-live-bundles" / timestamp
        with tempfile.TemporaryDirectory(prefix="wake-product-bundle-") as temporary:
            input_dir = Path(temporary)
            for filename, content in evidence.items():
                (input_dir / filename).write_bytes(content)
            result = run_agent_case(
                client=OpenAI(),
                config=config,
                prompt=DEFAULT_PROMPT.read_text(encoding="utf-8"),
                summary=summary,
                input_dir=input_dir,
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
        live_runner=build_live_runner(ROOT) if args.allow_live else None,
        bundle_live_runner=(
            build_bundle_live_runner(ROOT) if args.allow_live else None
        ),
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
