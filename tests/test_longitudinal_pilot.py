from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import longitudinal_pilot  # noqa: E402
import verify_longitudinal_pilot  # noqa: E402


def response(response_id: str, *, output: list[object], output_text: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        id=response_id,
        model="gpt-5.6-terra",
        status="completed",
        output=output,
        output_text=output_text,
        usage=SimpleNamespace(
            input_tokens=200,
            output_tokens=100,
            total_tokens=300,
            input_tokens_details=SimpleNamespace(cached_tokens=0),
            output_tokens_details=SimpleNamespace(reasoning_tokens=20),
        ),
    )


class FakeResponses:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.pending = list(responses)
        self.requests: list[dict] = []

    def create(self, **request: object) -> SimpleNamespace:
        self.requests.append(request)
        return self.pending.pop(0)


class FakeClient:
    def __init__(self, responses: list[SimpleNamespace]) -> None:
        self.responses = FakeResponses(responses)


class LongitudinalPilotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.summaries = longitudinal_pilot.build_pilot_summaries()
        self.schema = json.loads(
            (ROOT / "schemas/longitudinal-intelligence-output.schema.json").read_text(
                encoding="utf-8"
            )
        )

    def test_builds_two_compact_ground_truth_free_pilot_inputs(self) -> None:
        self.assertEqual(set(self.summaries), {"athlete-lucas", "club-coach"})

        for pilot_id, summary in self.summaries.items():
            self.assertEqual(summary["schema_version"], "wake.longitudinal_summary.v1")
            self.assertEqual(summary["pilot_id"], pilot_id)
            self.assertEqual(summary["provenance"], "REAL_INFORMED_SYNTHETIC")
            self.assertFalse(summary["model_called"])
            self.assertLess(len(json.dumps(summary)), 30_000)
            serialized = json.dumps(summary).lower()
            self.assertNotIn("latitude", serialized)
            self.assertNotIn("longitude", serialized)
            self.assertNotIn("ground-truth", serialized)
            self.assertNotIn("merged_distance", serialized)
            self.assertTrue(summary["evidence_catalog"])
            self.assertTrue(summary["boundaries"])

        athlete = self.summaries["athlete-lucas"]
        self.assertEqual(athlete["scope"]["type"], "ATHLETE")
        self.assertEqual(athlete["scope"]["entity_id"], "athlete-lucas")
        self.assertGreater(athlete["coverage"]["activity_count"], 0)
        self.assertGreater(athlete["modality_totals"]["water_distance_m"], 0)
        self.assertGreater(athlete["modality_totals"]["indoor_distance_m"], 0)
        self.assertNotIn("total_distance_m", athlete["modality_totals"])
        self.assertFalse(athlete["comparison_readiness"]["performance_trend_supported"])

        club = self.summaries["club-coach"]
        self.assertEqual(club["scope"]["type"], "CLUB")
        self.assertEqual(club["coverage"]["activity_count"], 52)
        self.assertEqual(club["routing"]["AGENT_VERIFIED"], 2)
        self.assertEqual(club["routing"]["HUMAN_OR_SOURCE_REQUIRED"], 2)

    def test_verifier_rejects_invented_evidence_and_unsupported_trends(self) -> None:
        summary = self.summaries["athlete-lucas"]
        output = longitudinal_pilot.example_valid_output(summary)
        self.assertEqual(
            longitudinal_pilot.verify_longitudinal_output(
                output=output,
                output_schema=self.schema,
                summary=summary,
            ),
            [],
        )

        invented = json.loads(json.dumps(output))
        invented["observed_facts"][0]["evidence_refs"] = ["invented.csv"]
        self.assertTrue(any(
            "does not exist" in error
            for error in longitudinal_pilot.verify_longitudinal_output(
                output=invented,
                output_schema=self.schema,
                summary=summary,
            )
        ))

        unsupported = json.loads(json.dumps(output))
        unsupported["headline"] = "Lucas improved fitness across the period."
        self.assertTrue(any(
            "unsupported longitudinal" in error.lower()
            for error in longitudinal_pilot.verify_longitudinal_output(
                output=unsupported,
                output_schema=self.schema,
                summary=summary,
            )
        ))

    def test_dry_run_freezes_four_requests_without_calling_the_api(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            manifest_path = longitudinal_pilot.write_pilot_dry_run(
                summaries=self.summaries,
                output_dir=output_dir,
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        self.assertFalse(manifest["api_called"])
        self.assertEqual(manifest["request_count"], 4)
        self.assertEqual(manifest["authorization"]["required_total_usd"], 0.8)
        self.assertFalse(manifest["authorization"]["provider_cap"])
        self.assertEqual(
            {request["workflow"] for request in manifest["requests"]},
            {"DIRECT_BASELINE", "WAKE_BOUNDED_AGENT"},
        )
        self.assertTrue(all(len(request["sha256"]) == 64 for request in manifest["requests"]))

    def test_agent_request_uses_bounded_tools_and_strict_structured_output(self) -> None:
        request = longitudinal_pilot.build_agent_request(
            self.summaries["club-coach"], self.schema
        )
        self.assertEqual(request["model"], "gpt-5.6-terra")
        self.assertEqual(request["reasoning"], {"effort": "medium"})
        self.assertFalse(request["store"])
        self.assertEqual(request["tool_choice"], "auto")
        self.assertEqual(len(request["tools"]), 4)
        self.assertTrue(request["text"]["format"]["strict"])

    def test_paid_execution_requires_a_finite_gate_for_every_start(self) -> None:
        self.assertEqual(longitudinal_pilot.required_authorization_usd(4), 0.8)
        with self.assertRaisesRegex(ValueError, r"US\$0.80"):
            longitudinal_pilot.validate_authorization(0.79, 4)
        with self.assertRaisesRegex(ValueError, "finite"):
            longitudinal_pilot.validate_authorization(float("nan"), 4)
        longitudinal_pilot.validate_authorization(0.8, 4)

    def test_preflight_verifier_detects_request_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            longitudinal_pilot.write_pilot_dry_run(
                summaries=self.summaries,
                output_dir=output_dir,
            )
            self.assertEqual(
                verify_longitudinal_pilot.verify_pilot_directory(output_dir), []
            )
            request_path = next((output_dir / "requests").glob("*.json"))
            request_path.write_text("{}\n", encoding="utf-8")
            errors = verify_longitudinal_pilot.verify_pilot_directory(output_dir)
            self.assertTrue(any("hash" in error.lower() for error in errors))

    def test_executes_and_persists_baseline_and_bounded_agent_results(self) -> None:
        summary = self.summaries["athlete-lucas"]
        final = longitudinal_pilot.example_valid_output(summary)
        tool_calls = [
            SimpleNamespace(
                type="function_call",
                name=name,
                call_id=f"call-{index}",
                arguments="{}",
            )
            for index, name in enumerate(longitudinal_pilot.TOOL_NAMES, start=1)
        ]
        baseline_client = FakeClient([
            response("baseline-final", output=[SimpleNamespace(type="message")], output_text=json.dumps(final))
        ])
        agent_client = FakeClient([
            response("agent-tools", output=tool_calls),
            response("agent-final", output=[SimpleNamespace(type="message")], output_text=json.dumps(final)),
        ])

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            baseline = longitudinal_pilot.run_baseline_case(
                client=baseline_client,
                summary=summary,
                output_schema=self.schema,
                output_dir=output_dir,
                now=lambda: "2026-08-30T12:00:00+00:00",
                monotonic_values=iter([1.0, 1.25]),
            )
            agent = longitudinal_pilot.run_agent_case(
                client=agent_client,
                summary=summary,
                output_schema=self.schema,
                output_dir=output_dir,
                now=lambda: "2026-08-30T12:00:01+00:00",
                monotonic_values=iter([2.0, 2.5]),
            )
            saved_baseline = json.loads(baseline["artifact_path"].read_text(encoding="utf-8"))
            saved_agent = json.loads(agent["artifact_path"].read_text(encoding="utf-8"))

        self.assertTrue(saved_baseline["verification"]["passed"])
        self.assertTrue(saved_agent["verification"]["passed"])
        self.assertEqual(saved_baseline["workflow"], "DIRECT_BASELINE")
        self.assertEqual(saved_agent["workflow"], "WAKE_BOUNDED_AGENT")
        self.assertEqual(len(saved_agent["tool_events"]), 8)
        self.assertEqual(len(baseline_client.responses.requests), 1)
        self.assertEqual(len(agent_client.responses.requests), 2)
        self.assertGreater(saved_agent["observability"]["approximate_cost_usd"], 0)


if __name__ == "__main__":
    unittest.main()
