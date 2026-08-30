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
import copy
import hashlib
import json
import math
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
from weather_enrichment import (
    OpenMeteoHistoricalForecastProvider,
    build_weather_preview,
    build_weather_lookup,
    normalize_open_meteo_response,
)
from wake_agent import (
    DEFAULT_INPUTS,
    DEFAULT_SCHEMA,
    public_case_input_dir,
    run_agent_case,
)


ROOT = Path(__file__).resolve().parents[1]
REPLAY_OUTPUTS = ROOT / "evaluation/runs/comparison-v1-20260829/agent/outputs"
PUBLIC_REPLAY_CASE_ID = "case-002-wind-shift-plan-deviation"
VALID_ANSWERS = {"YES", "NO", "UNKNOWN"}
HUMAN_ROLES = {"ATHLETE", "COACH"}
SOURCE_ORIGIN_ROLES = {"ATHLETE", "COACH", "DEVICE", "SERVICE"}
AUTHORITY_BASES = {
    "DIRECT_PARTICIPANT",
    "DIRECT_OBSERVATION",
    "RELAYED_REPORT",
    "UNKNOWN",
}
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
DEFAULT_REQUIRED_COST_AUTHORIZATION_USD = 0.20
DEFAULT_STATE_STORE = ROOT / "private-data/wake-product/product-state.json"
DEFAULT_SOURCE_ORIGIN = {
    "PLAN": "COACH",
    "SPEEDCOACH": "DEVICE",
    "MOBILE": "DEVICE",
    "ENVIRONMENT": "SERVICE",
}
SOURCE_AUTHORITY_SCOPE = {
    "PLAN": "TRAINING_PRESCRIPTION",
    "SPEEDCOACH": "MEASURED_TELEMETRY",
    "MOBILE": "MEASURED_TELEMETRY",
    "ENVIRONMENT": "ENVIRONMENT_OBSERVATION",
    "CONTEXT": "HUMAN_CONTEXT",
}
ALLOWED_SOURCE_ORIGINS = {
    "PLAN": {"ATHLETE", "COACH"},
    "SPEEDCOACH": {"DEVICE"},
    "MOBILE": {"DEVICE"},
    "ENVIRONMENT": {"ATHLETE", "COACH", "SERVICE"},
    "CONTEXT": {"ATHLETE", "COACH"},
}


def load_product_workflow_assets(root: Path = ROOT) -> tuple[dict, str]:
    return (
        read_json(root / "config/wake-agent-v2.json"),
        (root / "prompts/wake-agent-v2.md").read_text(encoding="utf-8"),
    )


def validate_required_cost_authorization(value: float) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Cost authorization must be a positive finite USD value.")
    return value


def checkpoint_authority(question: str) -> dict:
    normalized = question.casefold()
    athlete_signals = (
        "was the resistance band used",
        "equipment used",
        "equipment malfunction",
        "perceived effort",
        "discomfort",
        "what happened",
    )
    coach_signals = (
        "official prescription",
        "coach observation",
        "training intent",
        "was prescribed",
    )
    if any(signal in normalized for signal in athlete_signals):
        expected_role = "ATHLETE"
        scope = "SESSION_EXECUTION"
    elif any(signal in normalized for signal in coach_signals):
        expected_role = "COACH"
        scope = "TRAINING_INTENT"
    else:
        expected_role = "ATHLETE_OR_COACH"
        scope = "HUMAN_CONTEXT"
    return {
        "expected_respondent_role": expected_role,
        "authority_scope": scope,
    }


def validate_answer_provenance(
    *,
    answer: str,
    answered_by_role: str | None,
    recorded_by_role: str | None,
    authority_basis: str | None,
) -> None:
    if answer == "UNKNOWN":
        return
    if (
        answered_by_role not in HUMAN_ROLES
        or recorded_by_role not in HUMAN_ROLES
        or authority_basis not in AUTHORITY_BASES - {"UNKNOWN"}
    ):
        raise ValueError(
            "Confirmed checkpoint answers require answer provenance: valid "
            "answerer, recorder, and authority basis."
        )
    if authority_basis == "DIRECT_PARTICIPANT" and answered_by_role != "ATHLETE":
        raise ValueError("DIRECT_PARTICIPANT requires an athlete answerer.")
    if authority_basis == "RELAYED_REPORT" and answered_by_role == recorded_by_role:
        raise ValueError("RELAYED_REPORT requires different answerer and recorder roles.")
    if authority_basis == "DIRECT_OBSERVATION" and answered_by_role != recorded_by_role:
        raise ValueError("DIRECT_OBSERVATION must be recorded by the observer.")


def human_confirmation_from_answer(
    question: str,
    answer: str,
    *,
    expected_respondent_role: str,
    answered_by_role: str | None = None,
    recorded_by_role: str | None = None,
    authority_basis: str | None = None,
) -> dict:
    validate_answer_provenance(
        answer=answer,
        answered_by_role=answered_by_role,
        recorded_by_role=recorded_by_role,
        authority_basis=authority_basis,
    )
    if answer in {"YES", "NO"}:
        label = "Yes" if answer == "YES" else "No"
        source = {
            ("ATHLETE", "ATHLETE", "DIRECT_PARTICIPANT"): "Athlete direct confirmation",
            ("ATHLETE", "COACH", "RELAYED_REPORT"): "Athlete report recorded by coach",
            ("COACH", "COACH", "DIRECT_OBSERVATION"): "Coach direct observation",
        }.get(
            (answered_by_role, recorded_by_role, authority_basis),
            "Attributed human confirmation",
        )
        role_label = "Athlete" if answered_by_role == "ATHLETE" else "Coach"
        return {
            "status": "HUMAN_CONFIRMED",
            "answer": answer,
            "value": answer == "YES",
            "source": source,
            "question": question,
            "expectedRespondentRole": expected_respondent_role,
            "answeredByRole": answered_by_role,
            "recordedByRole": recorded_by_role,
            "authorityBasis": authority_basis,
            "matchesExpectedRespondent": expected_respondent_role
            in {answered_by_role, "ATHLETE_OR_COACH"},
            "statement": f'{role_label} answered "{label}" to: {question} ({source}).',
        }
    return {
        "status": "UNKNOWN",
        "answer": "UNKNOWN",
        "value": None,
        "source": None,
        "question": question,
        "expectedRespondentRole": expected_respondent_role,
        "answeredByRole": None,
        "recordedByRole": recorded_by_role,
        "authorityBasis": "UNKNOWN",
        "matchesExpectedRespondent": False,
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
        weather_provider: Callable[[dict], dict] | None = None,
        weather_now: Callable[[], datetime] | None = None,
        product_now: Callable[[], datetime] | None = None,
        state_store_path: Path | None = None,
        required_cost_authorization_usd: float = DEFAULT_REQUIRED_COST_AUTHORIZATION_USD,
    ) -> None:
        self.root = root
        self.live_runner = live_runner
        self.bundle_live_runner = bundle_live_runner
        self.weather_provider = weather_provider
        self.weather_now = weather_now or (lambda: datetime.now(timezone.utc))
        self.product_now = product_now or (lambda: datetime.now(timezone.utc))
        self.state_store_path = state_store_path
        self.required_cost_authorization_usd = validate_required_cost_authorization(
            required_cost_authorization_usd
        )
        self.investigations: dict[str, dict] = {}
        self.briefings: dict[str, dict] = {}
        self.goals: dict[str, dict] = {}
        self.sources: dict[str, dict] = {}
        self.source_bundles: dict[str, dict] = {}
        self.source_batches: dict[str, dict] = {}
        self.bundle_results: dict[str, dict] = {}
        self.cost_executions: dict[str, dict] = {}
        self.weather_enrichments: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self._load_state()

    def _timestamp(self) -> str:
        return self.product_now().astimezone(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        )

    def _state_snapshot(self) -> dict:
        sources = {}
        for source_id, source in self.sources.items():
            stored = {
                key: copy.deepcopy(value)
                for key, value in source.items()
                if key not in {"_content", "_normalized_content"}
            }
            stored["content_base64"] = base64.b64encode(source["_content"]).decode(
                "ascii"
            )
            normalized = source.get("_normalized_content")
            stored["normalized_content_base64"] = (
                base64.b64encode(normalized).decode("ascii")
                if normalized is not None
                else None
            )
            sources[source_id] = stored
        return {
            "schema_version": "wake.product_state.v1",
            "sources": sources,
            "source_bundles": self.source_bundles,
            "source_batches": self.source_batches,
            "bundle_results": self.bundle_results,
            "investigations": self.investigations,
            "briefings": self.briefings,
            "goals": self.goals,
            "cost_executions": self.cost_executions,
            "weather_enrichments": self.weather_enrichments,
            "sessions": self.sessions,
        }

    def _persist_state(self) -> None:
        if self.state_store_path is None:
            return
        self.state_store_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_store_path.with_suffix(
            f"{self.state_store_path.suffix}.tmp"
        )
        temporary.write_text(
            json.dumps(self._state_snapshot(), sort_keys=True, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, self.state_store_path)
        os.chmod(self.state_store_path, 0o600)

    def _load_state(self) -> None:
        if self.state_store_path is None or not self.state_store_path.is_file():
            return
        os.chmod(self.state_store_path, 0o600)
        stored = read_json(self.state_store_path)
        if stored.get("schema_version") != "wake.product_state.v1":
            raise ValueError("Unsupported WAKE product state version.")
        sources = {}
        for source_id, source in stored.get("sources", {}).items():
            restored = {
                key: copy.deepcopy(value)
                for key, value in source.items()
                if key not in {"content_base64", "normalized_content_base64"}
            }
            restored["_content"] = base64.b64decode(source["content_base64"])
            normalized = source.get("normalized_content_base64")
            restored["_normalized_content"] = (
                base64.b64decode(normalized) if normalized is not None else None
            )
            sources[source_id] = restored
        self.sources = sources
        for name in (
            "source_bundles",
            "source_batches",
            "bundle_results",
            "investigations",
            "briefings",
            "goals",
            "cost_executions",
            "weather_enrichments",
            "sessions",
        ):
            setattr(self, name, copy.deepcopy(stored.get(name, {})))

    @staticmethod
    def _session_list_item(session: dict) -> dict:
        hidden = {"review", "briefing", "goal", "bundle"}
        return {
            key: copy.deepcopy(value)
            for key, value in session.items()
            if key not in hidden
        }

    def list_sessions(self) -> dict:
        sessions = sorted(
            (self._session_list_item(item) for item in self.sessions.values()),
            key=lambda item: item["timestamps"]["updated_at"],
            reverse=True,
        )
        return {
            "schema_version": "wake.session_inbox.v1",
            "storage": {
                "status": "SAVED_LOCALLY" if self.state_store_path else "PROCESS_ONLY",
                "raw_evidence_scope": "PRIVATE_LOCAL_ONLY",
            },
            "counts": {
                "needs_action": sum(
                    item["status"]
                    in {"NEEDS_HUMAN_RESPONSE", "READY_FOR_COACH_APPROVAL"}
                    for item in sessions
                ),
                "awaiting_analysis": sum(
                    item["analysis_status"] == "NOT_STARTED" for item in sessions
                ),
                "viewed": sum(
                    item["coach_view_status"] == "VIEWED" for item in sessions
                ),
                "in_club_memory": sum(
                    item["memory_status"] == "APPROVED" for item in sessions
                ),
            },
            "sessions": sessions,
        }

    def get_session(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            raise KeyError(f"Unknown session: {session_id}")
        return copy.deepcopy(self.sessions[session_id])

    def mark_session_viewed(self, session_id: str) -> dict:
        if session_id not in self.sessions:
            raise KeyError(f"Unknown session: {session_id}")
        now = self._timestamp()
        session = self.sessions[session_id]
        session["coach_view_status"] = "VIEWED"
        session["timestamps"]["last_viewed_at"] = now
        session["timestamps"]["updated_at"] = now
        self._persist_state()
        return self.get_session(session_id)

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

    def upload_source(
        self,
        *,
        kind: str,
        name: str,
        content: bytes,
        uploaded_by_role: str = "COACH",
        origin_role: str | None = None,
    ) -> dict:
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
        uploaded_by_role = uploaded_by_role.upper()
        if uploaded_by_role not in HUMAN_ROLES:
            raise ValueError("Unsupported source uploader role.")
        origin_role = (origin_role or DEFAULT_SOURCE_ORIGIN.get(kind) or uploaded_by_role).upper()
        if origin_role not in SOURCE_ORIGIN_ROLES:
            raise ValueError("Unsupported source origin role.")
        if origin_role not in ALLOWED_SOURCE_ORIGINS[kind]:
            raise ValueError(f"Unsupported source origin role for {kind}.")

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
        identity_digest = hashlib.sha256(
            f"{digest}:{uploaded_by_role}:{origin_role}".encode("utf-8")
        ).hexdigest()
        source_id = f"source-{kind.lower()}-{identity_digest[:12]}"
        stored = {
            "source_id": source_id,
            "kind": kind,
            "name": name,
            "status": "READY",
            "format": source_format,
            "sha256": digest,
            "size_bytes": len(content),
            "provenance": {
                "uploaded_by_role": uploaded_by_role,
                "origin_role": origin_role,
                "authority_scope": SOURCE_AUTHORITY_SCOPE[kind],
            },
            **({"normalization": normalization} if normalization else {}),
            "_content": content,
            "_normalized_content": normalized_content,
        }
        self.sources[source_id] = stored
        self._persist_state()
        return {key: value for key, value in stored.items() if not key.startswith("_")}

    def get_source(self, source_id: str) -> dict:
        if source_id not in self.sources:
            raise KeyError(f"Unknown source: {source_id}")
        return {
            key: value
            for key, value in self.sources[source_id].items()
            if not key.startswith("_")
        }

    def enrich_environment_from_speedcoach(
        self,
        speedcoach_source_id: str,
        *,
        requested_by_role: str,
        authorized_location_lookup: bool,
        session_timezone: str | None = None,
    ) -> dict:
        """Create one cached weather-API source from a SpeedCoach recording."""
        if authorized_location_lookup is not True:
            raise ValueError(
                "Explicit external location lookup authorization is required."
            )
        requested_by_role = requested_by_role.upper()
        if requested_by_role not in HUMAN_ROLES:
            raise ValueError("Unsupported weather enrichment requester role.")
        if self.weather_provider is None:
            raise ValueError("Historical weather enrichment is disabled for this service.")
        try:
            speedcoach = self.sources[speedcoach_source_id]
        except KeyError as error:
            raise ValueError(f"Unknown source: {speedcoach_source_id}") from error
        if speedcoach["kind"] != "SPEEDCOACH":
            raise ValueError("Weather enrichment requires a SPEEDCOACH source.")

        lookup = build_weather_lookup(
            speedcoach["_normalized_content"],
            assumed_timezone=session_timezone,
        )
        cache_identity = json.dumps(
            {
                "lookup_id": lookup["lookup_id"],
                "requested_by_role": requested_by_role,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        cache_key = hashlib.sha256(cache_identity.encode("utf-8")).hexdigest()
        safe_lookup = {
            key: lookup[key]
            for key in (
                "lookup_id",
                "provider",
                "dataset",
                "location_precision_decimals",
                "session_start_utc",
                "session_end_utc",
                "query_start_utc",
                "query_end_utc",
                "time_zone_source",
                "assumed_timezone",
            )
        }
        if cache_key in self.weather_enrichments:
            cached = self.weather_enrichments[cache_key]
            return {
                "source": self.get_source(cached["source_id"]),
                "lookup": {**safe_lookup, "cache_hit": True},
                "preview": cached["preview"],
            }

        provider_response = self.weather_provider(lookup)
        timeline = normalize_open_meteo_response(
            request=lookup,
            response=provider_response,
            retrieved_at=self.weather_now(),
        )
        preview = build_weather_preview(timeline)
        content = json.dumps(
            timeline,
            sort_keys=True,
            indent=2,
        ).encode("utf-8")
        source = self.upload_source(
            kind="ENVIRONMENT",
            name=f"environment-{lookup['lookup_id']}.json",
            content=content,
            uploaded_by_role=requested_by_role,
            origin_role="SERVICE",
        )
        self.weather_enrichments[cache_key] = {
            "source_id": source["source_id"],
            "preview": preview,
        }
        self._persist_state()
        return {
            "source": source,
            "lookup": {**safe_lookup, "cache_hit": False},
            "preview": preview,
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
        contribution_identity = json.dumps(
            [grouped[kind]["source_id"] for kind in SOURCE_ORDER if kind in grouped],
            separators=(",", ":"),
        ).encode("utf-8")
        bundle_digest = hashlib.sha256(
            serialized_summary + b"\0" + contribution_identity
        ).hexdigest()
        bundle_id = f"source-bundle-{bundle_digest[:16]}"
        response = {
            "bundle_id": bundle_id,
            "session_id": bundle_id,
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
            "source_contributions": [
                {
                    "kind": kind,
                    "provenance": grouped[kind]["provenance"],
                }
                for kind in SOURCE_ORDER
                if kind in grouped
            ],
            "evidence_gaps": summary["evidence_gaps"],
            "cost_authorization": {
                "currency": "USD",
                "required_authorization_usd": self.required_cost_authorization_usd,
                "hard_provider_cap": False,
                "basis": "START_GATE_WITH_POST_RUN_USAGE",
            },
            "agent_called": False,
        }
        self.source_bundles[bundle_id] = {
            "summary": summary,
            "source_ids": list(source_ids),
            "response": response,
        }
        now = self._timestamp()
        existing = self.sessions.get(bundle_id, {})
        session_review = {
            "analysis": {"case_id": summary["case_id"]},
            "summary": {"plan": summary.get("plan")},
            "context": {
                "session_candidate": summary.get("known_context", {}).get(
                    "session_candidate", {}
                )
            },
        }
        self.sessions[bundle_id] = {
            "session_id": bundle_id,
            "case_id": summary["case_id"],
            "title": self._session_title(session_review),
            "scheduled_date": (summary.get("plan") or {}).get("scheduled_date"),
            "status": existing.get("status", "READY_FOR_INVESTIGATION"),
            "analysis_status": existing.get("analysis_status", "NOT_STARTED"),
            "coach_view_status": existing.get("coach_view_status", "UNSEEN"),
            "human_context_status": existing.get(
                "human_context_status", "NOT_REQUESTED"
            ),
            "memory_status": existing.get("memory_status", "NOT_READY"),
            "storage_status": (
                "SAVED_LOCALLY" if self.state_store_path else "PROCESS_ONLY"
            ),
            "source_coverage": copy.deepcopy(response["source_coverage"]),
            "bundle_id": bundle_id,
            "investigation_id": existing.get("investigation_id"),
            "checkpoint_id": existing.get("checkpoint_id"),
            "briefing_id": existing.get("briefing_id"),
            "goal_id": existing.get("goal_id"),
            "timestamps": {
                "received_at": existing.get("timestamps", {}).get("received_at", now),
                "analysis_completed_at": existing.get("timestamps", {}).get(
                    "analysis_completed_at"
                ),
                "last_viewed_at": existing.get("timestamps", {}).get(
                    "last_viewed_at"
                ),
                "human_answered_at": existing.get("timestamps", {}).get(
                    "human_answered_at"
                ),
                "approved_at": existing.get("timestamps", {}).get("approved_at"),
                "updated_at": now,
            },
            "bundle": copy.deepcopy(response),
            **({"review": existing["review"]} if "review" in existing else {}),
            **({"briefing": existing["briefing"]} if "briefing" in existing else {}),
            **({"goal": existing["goal"]} if "goal" in existing else {}),
        }
        self._persist_state()
        return response

    @staticmethod
    def _source_batch_counts(items: list[dict]) -> dict:
        statuses = [item["status"] for item in items]
        return {
            "total": len(items),
            "prepared": sum(status != "FAILED_PREPARATION" for status in statuses),
            "failed_preparation": statuses.count("FAILED_PREPARATION"),
            "pending_execution": statuses.count("READY_FOR_EXECUTION"),
            "agent_completed": statuses.count("AGENT_COMPLETED"),
            "execution_failed": statuses.count("EXECUTION_FAILED"),
        }

    def _source_batch_response(self, batch: dict) -> dict:
        items = copy.deepcopy(batch["items"])
        completed_costs = [
            item["cost"] for item in items if item.get("cost") is not None
        ]
        return {
            "schema_version": "wake.source_batch.v1",
            "batch_id": batch["batch_id"],
            "status": batch["status"],
            "counts": self._source_batch_counts(items),
            "items": items,
            "observed_cost": {
                "currency": "USD",
                "execution_count": len(completed_costs),
                "approximate_total_cost_usd": round(
                    sum(item["approximate_cost_usd"] for item in completed_costs),
                    6,
                ),
                "total_tokens": sum(
                    item["usage"]["total_tokens"] for item in completed_costs
                ),
                "hard_provider_cap": False,
            },
            "authorization_policy": {
                "required_start_gate_per_execution_usd": (
                    self.required_cost_authorization_usd
                ),
                "batch_authorization_is_provider_cap": False,
                "execution_order": "SEQUENTIAL",
            },
            "attempts": copy.deepcopy(batch["attempts"]),
        }

    def prepare_source_batch(self, items: list[dict]) -> tuple[dict, bool]:
        """Prepare multiple independent sessions while isolating item failures."""
        if not isinstance(items, list) or not items:
            raise ValueError("A source batch requires at least one item.")
        if len(items) > 100:
            raise ValueError("A source batch accepts at most 100 items.")

        normalized_items = []
        client_ids = set()
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError("Every source batch item must be an object.")
            client_session_id = item.get("client_session_id")
            source_ids = item.get("source_ids")
            if not isinstance(client_session_id, str) or not client_session_id.strip():
                raise ValueError("Every source batch item requires client_session_id.")
            if client_session_id in client_ids:
                raise ValueError("A source batch cannot repeat client_session_id.")
            if not isinstance(source_ids, list) or not source_ids or not all(
                isinstance(source_id, str) for source_id in source_ids
            ):
                raise ValueError("Every source batch item requires source_ids.")
            client_ids.add(client_session_id)
            normalized_items.append(
                {
                    "position": index,
                    "client_session_id": client_session_id,
                    "source_ids": list(source_ids),
                }
            )

        identity = json.dumps(
            normalized_items,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        batch_id = f"source-batch-{hashlib.sha256(identity).hexdigest()[:16]}"
        if batch_id in self.source_batches:
            return self.get_source_batch(batch_id), False

        prepared_items = []
        for item in normalized_items:
            safe_item = {
                "position": item["position"],
                "client_session_id": item["client_session_id"],
                "status": "READY_FOR_EXECUTION",
                "bundle_id": None,
                "case_id": None,
                "error": None,
                "cost": None,
            }
            try:
                prepared = self.prepare_source_bundle(item["source_ids"])
                safe_item.update(
                    {
                        "bundle_id": prepared["bundle_id"],
                        "case_id": prepared["case_id"],
                        "source_count": prepared["source_count"],
                        "source_coverage": prepared["source_coverage"],
                        "evidence_gaps": prepared["evidence_gaps"],
                    }
                )
            except (KeyError, TypeError, ValueError, jsonschema.ValidationError) as error:
                safe_item.update(
                    {
                        "status": "FAILED_PREPARATION",
                        "error": str(error),
                    }
                )
            prepared_items.append(safe_item)

        batch = {
            "batch_id": batch_id,
            "status": (
                "READY_FOR_EXECUTION"
                if any(item["status"] == "READY_FOR_EXECUTION" for item in prepared_items)
                else "COMPLETED_WITH_FAILURES"
            ),
            "items": prepared_items,
            "attempts": [],
        }
        self.source_batches[batch_id] = batch
        self._persist_state()
        return self._source_batch_response(batch), True

    def get_source_batch(self, batch_id: str) -> dict:
        if batch_id not in self.source_batches:
            raise KeyError(f"Unknown source batch: {batch_id}")
        return self._source_batch_response(self.source_batches[batch_id])

    def execute_source_batch(
        self,
        batch_id: str,
        *,
        mode: str,
        authorized_batch_cost_usd: float | None,
    ) -> dict:
        """Sequentially execute prepared items within explicit start-gate slots."""
        if mode != "live":
            raise ValueError("Source batch execution requires explicit live mode.")
        if batch_id not in self.source_batches:
            raise ValueError(f"Unknown source batch: {batch_id}")
        batch = self.source_batches[batch_id]
        pending = [
            item for item in batch["items"] if item["status"] == "READY_FOR_EXECUTION"
        ]
        if not pending:
            return self._source_batch_response(batch)
        if (
            authorized_batch_cost_usd is None
            or not math.isfinite(authorized_batch_cost_usd)
            or authorized_batch_cost_usd < self.required_cost_authorization_usd
        ):
            raise ValueError(
                "Explicit batch cost authorization must fund at least one "
                f"US${self.required_cost_authorization_usd:.2f} start gate."
            )
        start_slots = int(
            math.floor(
                (authorized_batch_cost_usd + 1e-12)
                / self.required_cost_authorization_usd
            )
        )
        attempted = 0
        completed = 0
        failed = 0
        for item in pending[:start_slots]:
            attempted += 1
            try:
                result, _ = self.execute_source_bundle(
                    item["bundle_id"],
                    mode="live",
                    authorized_cost_usd=self.required_cost_authorization_usd,
                )
                item.update(
                    {
                        "status": "AGENT_COMPLETED",
                        "execution_id": result["execution_id"],
                        "investigation_id": result["investigation_id"],
                        "investigation_status": result["investigation_status"],
                        "cost": copy.deepcopy(result["cost"]),
                        "error": None,
                    }
                )
                completed += 1
            except Exception as error:  # item-level isolation is the batch contract
                item.update(
                    {
                        "status": "EXECUTION_FAILED",
                        "error": f"{type(error).__name__}: {error}",
                    }
                )
                failed += 1

        remaining = any(
            item["status"] == "READY_FOR_EXECUTION" for item in batch["items"]
        )
        if remaining:
            batch["status"] = "PAUSED_AUTHORIZATION"
        elif any(item["status"].endswith("FAILED") or item["status"] == "FAILED_PREPARATION" for item in batch["items"]):
            batch["status"] = "COMPLETED_WITH_FAILURES"
        else:
            batch["status"] = "COMPLETED"
        batch["attempts"].append(
            {
                "authorized_batch_cost_usd": float(authorized_batch_cost_usd),
                "start_slots": start_slots,
                "attempted": attempted,
                "completed": completed,
                "failed": failed,
                "timestamp": self._timestamp(),
            }
        )
        self._persist_state()
        return self._source_batch_response(batch)

    def execute_source_bundle(
        self,
        bundle_id: str,
        *,
        mode: str,
        authorized_cost_usd: float | None = None,
    ) -> tuple[dict, bool]:
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
        if (
            authorized_cost_usd is None
            or not math.isfinite(authorized_cost_usd)
            or authorized_cost_usd < self.required_cost_authorization_usd
        ):
            raise ValueError(
                "Explicit cost authorization of at least "
                f"US${self.required_cost_authorization_usd:.2f} is required."
            )
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
        runner_result = self.bundle_live_runner(bundle["summary"], evidence)
        if not isinstance(runner_result, dict) or not isinstance(
            runner_result.get("analysis"), dict
        ):
            raise ValueError("Prepared-bundle runner omitted its analysis envelope.")
        analysis = runner_result["analysis"]
        observability = runner_result.get("observability")
        if not isinstance(observability, dict):
            raise ValueError("Prepared-bundle runner omitted cost observability.")
        usage = observability.get("usage")
        if not isinstance(usage, dict) or not all(
            isinstance(usage.get(key), int)
            for key in ("input_tokens", "output_tokens", "total_tokens")
        ):
            raise ValueError("Prepared-bundle runner returned invalid token usage.")
        approximate_cost_usd = float(observability["approximate_cost_usd"])
        runtime_ms = int(observability["runtime_ms"])
        cost = {
            "currency": "USD",
            "authorized_cost_usd": authorized_cost_usd,
            "approximate_cost_usd": approximate_cost_usd,
            "status": (
                "WITHIN_AUTHORIZATION"
                if approximate_cost_usd <= authorized_cost_usd
                else "AUTHORIZATION_EXCEEDED"
            ),
            "hard_provider_cap": False,
            "usage": {
                key: usage[key]
                for key in ("input_tokens", "output_tokens", "total_tokens")
            },
            "runtime_ms": runtime_ms,
        }
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
                        "provenance": grouped[source["kind"]]["provenance"],
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
                    "input_notice", "Locally uploaded evidence."
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
            "session_id": investigation["session_id"],
            "case_id": bundle["summary"]["case_id"],
            "mode": "live",
            "status": "AGENT_COMPLETED",
            "agent_called": True,
            "investigation_id": investigation["investigation_id"],
            "checkpoint_id": investigation["checkpoint_id"],
            "goal_id": investigation["goal_id"],
            "investigation_status": investigation["status"],
            "cost": cost,
            "analysis": analysis,
            "review": review,
        }
        self.bundle_results[execution_id] = result
        self.cost_executions[execution_id] = cost
        self._persist_state()
        return result, True

    def get_cost_summary(self) -> dict:
        usage_keys = ("input_tokens", "output_tokens", "total_tokens")
        return {
            "schema_version": "wake.product_cost_summary.v1",
            "currency": "USD",
            "execution_count": len(self.cost_executions),
            "approximate_total_cost_usd": round(
                sum(
                    item["approximate_cost_usd"]
                    for item in self.cost_executions.values()
                ),
                6,
            ),
            "total_usage": {
                key: sum(item["usage"][key] for item in self.cost_executions.values())
                for key in usage_keys
            },
            "hard_provider_cap": False,
        }

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
        existing_id = f"investigation-{case_id}"
        if existing_id in self.investigations:
            return self.investigations[existing_id]
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
        if investigation_id in self.investigations:
            return self.investigations[investigation_id]
        checkpoint_id = f"checkpoint-{identity}"
        goal_id = f"goal-{case_id}"
        questions = review["analysis"].get("follow_up_questions", [])
        question = questions[0] if questions else "Is there any human context to add?"
        review["checkpoint"] = {
            "checkpoint_id": checkpoint_id,
            "question": question,
            **checkpoint_authority(question),
        }
        result = {
            "investigation_id": investigation_id,
            "checkpoint_id": checkpoint_id,
            "goal_id": goal_id,
            "session_id": identity,
            "case_id": case_id,
            "mode": mode,
            "status": "QUESTION_REQUIRED" if questions else "READY_FOR_REVIEW",
            "review": review,
        }
        self.investigations[investigation_id] = result
        self.goals.setdefault(goal_id, self._empty_goal(review))
        now = self._timestamp()
        existing = self.sessions.get(identity, {})
        self.sessions[identity] = {
            "session_id": identity,
            "case_id": case_id,
            "title": self._session_title(review),
            "scheduled_date": (review.get("summary", {}).get("plan") or {}).get(
                "scheduled_date"
            ),
            "status": (
                "NEEDS_HUMAN_RESPONSE" if questions else "READY_FOR_COACH_REVIEW"
            ),
            "analysis_status": "COMPLETED",
            "coach_view_status": existing.get("coach_view_status", "UNSEEN"),
            "human_context_status": (
                "AWAITING_RESPONSE" if questions else "NOT_REQUESTED"
            ),
            "memory_status": "NOT_READY",
            "storage_status": (
                "SAVED_LOCALLY" if self.state_store_path else "PROCESS_ONLY"
            ),
            "source_coverage": existing.get("source_coverage", []),
            "bundle_id": existing.get("bundle_id"),
            "investigation_id": investigation_id,
            "checkpoint_id": checkpoint_id,
            "briefing_id": None,
            "goal_id": goal_id,
            "timestamps": {
                "received_at": existing.get("timestamps", {}).get("received_at", now),
                "analysis_completed_at": now,
                "last_viewed_at": existing.get("timestamps", {}).get(
                    "last_viewed_at"
                ),
                "human_answered_at": None,
                "approved_at": None,
                "updated_at": now,
            },
            "review": copy.deepcopy(review),
            **({"bundle": existing["bundle"]} if "bundle" in existing else {}),
        }
        self._persist_state()
        return result

    def get_investigation(self, investigation_id: str) -> dict:
        if investigation_id not in self.investigations:
            raise KeyError(f"Unknown investigation: {investigation_id}")
        return self.investigations[investigation_id]

    def answer_checkpoint(
        self,
        checkpoint_id: str,
        *,
        answer: str,
        answered_by_role: str | None = None,
        recorded_by_role: str | None = None,
        authority_basis: str | None = None,
    ) -> dict:
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
            answered_by_role=answered_by_role,
            recorded_by_role=recorded_by_role,
            authority_basis=authority_basis,
        )
        self.briefings[briefing["briefingId"]] = briefing
        investigation["status"] = "VERIFIED"
        investigation["briefing_id"] = briefing["briefingId"]
        session = self.sessions[investigation["session_id"]]
        now = self._timestamp()
        session["status"] = "READY_FOR_COACH_APPROVAL"
        session["coach_view_status"] = "VIEWED"
        session["human_context_status"] = "RESPONDED"
        session["memory_status"] = "AWAITING_APPROVAL"
        session["briefing_id"] = briefing["briefingId"]
        session["briefing"] = copy.deepcopy(briefing)
        session["timestamps"]["last_viewed_at"] = (
            session["timestamps"]["last_viewed_at"] or now
        )
        session["timestamps"]["human_answered_at"] = now
        session["timestamps"]["updated_at"] = now
        self._persist_state()
        return briefing

    def approve_briefing(self, briefing_id: str) -> dict:
        if briefing_id not in self.briefings:
            raise KeyError(f"Unknown briefing: {briefing_id}")
        briefing = self.briefings[briefing_id]
        goal_id = briefing["goalId"]
        goal = self._approved_goal(briefing)
        self.goals[goal_id] = goal
        briefing["pendingApproval"] = False
        session = next(
            (
                item
                for item in self.sessions.values()
                if item.get("briefing_id") == briefing_id
            ),
            None,
        )
        if session is not None:
            now = self._timestamp()
            session["status"] = "IN_CLUB_MEMORY"
            session["memory_status"] = "APPROVED"
            session["goal"] = copy.deepcopy(goal)
            session["briefing"] = copy.deepcopy(briefing)
            session["timestamps"]["approved_at"] = now
            session["timestamps"]["updated_at"] = now
        self._persist_state()
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

    def _build_briefing(
        self,
        review: dict,
        answer: str,
        *,
        goal_id: str,
        answered_by_role: str | None = None,
        recorded_by_role: str | None = None,
        authority_basis: str | None = None,
    ) -> dict:
        analysis = review["analysis"]
        questions = analysis.get("follow_up_questions", [])
        question = questions[0] if questions else "Is there any human context to add?"
        checkpoint = review.get("checkpoint") or checkpoint_authority(question)
        confirmation = human_confirmation_from_answer(
            question,
            answer,
            expected_respondent_role=checkpoint["expected_respondent_role"],
            answered_by_role=answered_by_role,
            recorded_by_role=recorded_by_role,
            authority_basis=authority_basis,
        )
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
                    "Human context remains unknown."
                    if confirmation["status"] == "UNKNOWN"
                    else "Attributed human context was confirmed."
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
        if method == "GET" and parts == ["api", "sessions"]:
            return 200, self.service.list_sessions()
        if method == "GET" and parts[:2] == ["api", "sessions"] and len(parts) == 3:
            return 200, self.service.get_session(parts[2])
        if (
            method == "POST"
            and len(parts) == 4
            and parts[:2] == ["api", "sessions"]
            and parts[3] == "view"
        ):
            return 200, self.service.mark_session_viewed(parts[2])
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
                uploaded_by_role=str(body.get("uploaded_by_role", "COACH")),
                origin_role=(
                    str(body["origin_role"])
                    if body.get("origin_role") is not None
                    else None
                ),
            )
        if method == "GET" and parts[:2] == ["api", "sources"] and len(parts) == 3:
            return 200, self.service.get_source(parts[2])
        if method == "POST" and parts == ["api", "environment-enrichments"]:
            return 201, self.service.enrich_environment_from_speedcoach(
                str(body.get("speedcoach_source_id", "")),
                requested_by_role=str(body.get("requested_by_role", "")),
                authorized_location_lookup=(
                    body.get("authorized_location_lookup") is True
                ),
                session_timezone=(
                    str(body["session_timezone"])
                    if body.get("session_timezone")
                    else None
                ),
            )
        if method == "POST" and parts == ["api", "source-bundles", "prepare"]:
            source_ids = body.get("source_ids")
            if not isinstance(source_ids, list) or not all(
                isinstance(source_id, str) for source_id in source_ids
            ):
                raise ValueError("source_ids must be a list of strings.")
            return 201, self.service.prepare_source_bundle(source_ids)
        if method == "POST" and parts == ["api", "source-batches", "prepare"]:
            items = body.get("items")
            if not isinstance(items, list):
                raise ValueError("items must be a list of source batch items.")
            result, created = self.service.prepare_source_batch(items)
            return (201 if created else 200), result
        if (
            method == "GET"
            and len(parts) == 3
            and parts[:2] == ["api", "source-batches"]
        ):
            return 200, self.service.get_source_batch(parts[2])
        if (
            method == "POST"
            and len(parts) == 4
            and parts[:2] == ["api", "source-batches"]
            and parts[3] == "execute"
        ):
            authorized_cost = body.get("authorized_batch_cost_usd")
            if not isinstance(authorized_cost, (int, float)) or isinstance(
                authorized_cost, bool
            ):
                authorized_cost = None
            return 200, self.service.execute_source_batch(
                parts[2],
                mode=str(body.get("mode", "")),
                authorized_batch_cost_usd=authorized_cost,
            )
        if (
            method == "POST"
            and len(parts) == 4
            and parts[:2] == ["api", "source-bundles"]
            and parts[3] == "execute"
        ):
            authorized_cost = body.get("authorized_cost_usd")
            if not isinstance(authorized_cost, (int, float)) or isinstance(
                authorized_cost, bool
            ):
                authorized_cost = None
            result, created = self.service.execute_source_bundle(
                parts[2],
                mode=str(body.get("mode", "")),
                authorized_cost_usd=authorized_cost,
            )
            return (201 if created else 200), result
        if method == "GET" and parts == ["api", "runtime", "costs"]:
            return 200, self.service.get_cost_summary()
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
                parts[2],
                answer=str(body.get("answer", "")),
                answered_by_role=(
                    str(body["answered_by_role"])
                    if body.get("answered_by_role") is not None
                    else None
                ),
                recorded_by_role=(
                    str(body["recorded_by_role"])
                    if body.get("recorded_by_role") is not None
                    else None
                ),
                authority_basis=(
                    str(body["authority_basis"])
                    if body.get("authority_basis") is not None
                    else None
                ),
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
    config, prompt = load_product_workflow_assets(root)

    def execute(case_id: str) -> dict:
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is required for live mode.")
        from openai import OpenAI

        summary = read_json(DEFAULT_INPUTS / f"{case_id}.json")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_dir = root / "evaluation/runs/product-live" / timestamp
        result = run_agent_case(
            client=OpenAI(),
            config=config,
            prompt=prompt,
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


def load_product_run_envelope(artifacts: dict[str, Path]) -> dict:
    trajectory = read_json(artifacts["trajectory_path"])
    return {
        "analysis": read_json(artifacts["output_path"]),
        "observability": {
            "usage": trajectory["usage"],
            "approximate_cost_usd": trajectory["approximate_cost_usd"],
            "runtime_ms": trajectory["runtime_ms"],
        },
    }


def build_bundle_live_runner(
    root: Path,
) -> Callable[[dict, dict[str, bytes]], dict]:
    config, prompt = load_product_workflow_assets(root)

    def execute(summary: dict, evidence: dict[str, bytes]) -> dict:
        if not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is required for live mode.")
        from openai import OpenAI

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output_dir = root / "evaluation/runs/product-live-bundles" / timestamp
        with tempfile.TemporaryDirectory(prefix="wake-product-bundle-") as temporary:
            input_dir = Path(temporary)
            for filename, content in evidence.items():
                (input_dir / filename).write_bytes(content)
            result = run_agent_case(
                client=OpenAI(),
                config=config,
                prompt=prompt,
                summary=summary,
                input_dir=input_dir,
                output_schema=read_json(DEFAULT_SCHEMA),
                output_dir=output_dir,
                run_id=output_dir.name,
                now=utc_now,
                git_commit=current_git_commit(),
            )
        return load_product_run_envelope(result)

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
    parser.add_argument("--allow-weather", action="store_true")
    parser.add_argument(
        "--state-store",
        type=Path,
        default=DEFAULT_STATE_STORE,
        help=(
            "Ignored local JSON state store. Contains private uploaded evidence; "
            "keep it outside version control."
        ),
    )
    parser.add_argument(
        "--required-cost-authorization-usd",
        type=float,
        default=DEFAULT_REQUIRED_COST_AUTHORIZATION_USD,
    )
    args = parser.parse_args()

    try:
        required_cost_authorization_usd = validate_required_cost_authorization(
            args.required_cost_authorization_usd
        )
    except ValueError as error:
        parser.error(str(error))

    service = WakeProductService(
        live_runner=build_live_runner(ROOT) if args.allow_live else None,
        bundle_live_runner=(
            build_bundle_live_runner(ROOT) if args.allow_live else None
        ),
        weather_provider=(
            OpenMeteoHistoricalForecastProvider() if args.allow_weather else None
        ),
        state_store_path=args.state_store,
        required_cost_authorization_usd=required_cost_authorization_usd,
    )
    api = WakeProductApi(service)
    server = ThreadingHTTPServer(
        (args.host, args.port),
        make_handler(api, allowed_origin=args.origin),
    )
    print(f"WAKE product service listening on http://{args.host}:{args.port}")
    print(f"Live agent execution: {'enabled' if args.allow_live else 'disabled'}")
    print(
        "Historical weather enrichment: "
        f"{'enabled' if args.allow_weather else 'disabled'}"
    )
    print(
        "Required live cost authorization: "
        f"US${required_cost_authorization_usd:.2f} (operational start gate)"
    )
    print(f"Local session state: {args.state_store}")
    server.serve_forever()


if __name__ == "__main__":
    main()
