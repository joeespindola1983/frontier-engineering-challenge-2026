from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import wake_agent  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def function_call(name: str, call_id: str, arguments: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        type="function_call",
        name=name,
        call_id=call_id,
        arguments=json.dumps(arguments or {}),
    )


def response(
    response_id: str,
    *,
    output: list[object],
    output_text: str = "",
) -> SimpleNamespace:
    return SimpleNamespace(
        id=response_id,
        model="gpt-5.6-terra",
        status="completed",
        output=output,
        output_text=output_text,
        usage=SimpleNamespace(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            input_tokens_details=SimpleNamespace(cached_tokens=0),
            output_tokens_details=SimpleNamespace(reasoning_tokens=10),
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


class WakeAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.summary = read_json(
            ROOT
            / "evaluation/baseline-inputs/v1/case-002-wind-shift-plan-deviation.json"
        )
        self.schema = read_json(ROOT / "schemas/analysis-output.schema.json")
        self.config = {
            "workflow": "wake-agent-v1",
            "model": "gpt-5.6-terra",
            "reasoning_effort": "medium",
            "max_output_tokens": 12000,
            "service_tier": "default",
            "store": False,
            "max_rounds": 4,
            "max_verifier_retries": 1,
        }

    def valid_output(self) -> dict:
        return {
            "schema_version": "wake.analysis_output.v1.1",
            "case_id": self.summary["case_id"],
            "session_associations": [],
            "plan_summary": None,
            "segments": [],
            "source_policy": [],
            "claims": [],
            "deviations": [],
            "environment_assessment": None,
            "abstentions": ["Technique is not observable."],
            "follow_up_questions": [],
            "coach_briefing": "Verified briefing.",
        }

    def test_agent_executes_tools_then_returns_verified_output_and_trajectory(self) -> None:
        final = self.valid_output()
        client = FakeClient(
            [
                response(
                    "resp_tools",
                    output=[
                        function_call("assess_source_trust", "call_1"),
                        function_call("reconstruct_plan_execution", "call_2"),
                    ],
                ),
                response(
                    "resp_final",
                    output=[SimpleNamespace(type="message")],
                    output_text=json.dumps(final),
                ),
            ]
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            result = wake_agent.run_agent_case(
                client=client,
                config=self.config,
                prompt="Investigate the supplied rowing case.",
                summary=self.summary,
                input_dir=ROOT
                / "data/fixtures/case-002-wind-shift-plan-deviation/input",
                output_schema=self.schema,
                output_dir=Path(temporary_directory),
                run_id="wake-test-run",
                now=lambda: "2026-08-29T12:00:00+00:00",
                git_commit="abc123",
            )
            trajectory = read_json(result["trajectory_path"])
            saved_output = read_json(result["output_path"])

        self.assertEqual(saved_output, final)
        self.assertEqual([event["type"] for event in trajectory["events"]], [
            "MODEL_RESPONSE",
            "TOOL_CALL",
            "TOOL_RESULT",
            "TOOL_CALL",
            "TOOL_RESULT",
            "MODEL_RESPONSE",
            "VERIFICATION",
            "FINAL_OUTPUT",
        ])
        self.assertTrue(trajectory["verification"]["passed"])
        self.assertNotIn("reasoning", json.dumps(trajectory).lower())
        self.assertEqual(len(client.responses.requests), 2)
        self.assertEqual(client.responses.requests[0]["tool_choice"], "auto")
        self.assertEqual(client.responses.requests[0]["store"], False)

    def test_verifier_rejects_invented_evidence_reference(self) -> None:
        output = self.valid_output()
        output["claims"] = [
            {
                "claim_id": "invented",
                "statement": "Unsupported claim.",
                "status": "OBSERVED",
                "confidence": 0.9,
                "evidence_refs": ["input/not-a-real-file.csv"],
                "limitations": [],
            }
        ]

        verification = wake_agent.verify_output(
            output=output,
            output_schema=self.schema,
            summary=self.summary,
        )

        self.assertFalse(verification["passed"])
        self.assertIn("input/not-a-real-file.csv", verification["errors"][0])

    def test_verifier_rejects_material_claim_without_evidence(self) -> None:
        output = self.valid_output()
        output["claims"] = [
            {
                "claim_id": "unsupported-without-citation",
                "statement": "The fifth work interval missed the prescribed SPM.",
                "status": "DERIVED",
                "confidence": 0.9,
                "evidence_refs": [],
                "limitations": [],
            }
        ]

        verification = wake_agent.verify_output(
            output=output,
            output_schema=self.schema,
            summary=self.summary,
        )

        self.assertFalse(verification["passed"])
        self.assertTrue(
            any("has no evidence references" in error for error in verification["errors"])
        )

    def test_verifier_rejects_unknown_selected_source(self) -> None:
        output = self.valid_output()
        output["source_policy"] = [
            {
                "metric": "stroke_rate_spm",
                "selected_source_id": "invented-device",
                "confidence": 0.8,
                "reason": "Invented.",
                "evidence_refs": ["input/speedcoach.csv"],
            }
        ]

        verification = wake_agent.verify_output(
            output=output,
            output_schema=self.schema,
            summary=self.summary,
        )

        self.assertFalse(verification["passed"])
        self.assertTrue(
            any("Unknown selected source" in error for error in verification["errors"])
        )

    def test_agent_retries_once_after_verifier_rejection(self) -> None:
        invalid = self.valid_output()
        invalid["claims"] = [
            {
                "claim_id": "invented",
                "statement": "Invented.",
                "status": "OBSERVED",
                "confidence": 1.0,
                "evidence_refs": ["input/not-real.csv"],
                "limitations": [],
            }
        ]
        valid = self.valid_output()
        client = FakeClient(
            [
                response(
                    "resp_invalid",
                    output=[SimpleNamespace(type="message")],
                    output_text=json.dumps(invalid),
                ),
                response(
                    "resp_corrected",
                    output=[SimpleNamespace(type="message")],
                    output_text=json.dumps(valid),
                ),
            ]
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            result = wake_agent.run_agent_case(
                client=client,
                config=self.config,
                prompt="Investigate.",
                summary=self.summary,
                input_dir=ROOT
                / "data/fixtures/case-002-wind-shift-plan-deviation/input",
                output_schema=self.schema,
                output_dir=Path(temporary_directory),
                run_id="wake-retry-test",
                now=lambda: "2026-08-29T12:00:00+00:00",
                git_commit="abc123",
            )
            trajectory = read_json(result["trajectory_path"])

        self.assertEqual(len(client.responses.requests), 2)
        self.assertEqual(
            [event["type"] for event in trajectory["events"]].count(
                "RETRY_REQUESTED"
            ),
            1,
        )
        self.assertTrue(trajectory["verification"]["passed"])

    def test_agent_stops_when_model_exceeds_tool_round_limit(self) -> None:
        client = FakeClient(
            [
                response(
                    f"resp_{index}",
                    output=[function_call("assess_source_trust", f"call_{index}")],
                )
                for index in range(4)
            ]
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaisesRegex(RuntimeError, "maximum tool rounds"):
                wake_agent.run_agent_case(
                    client=client,
                    config=self.config,
                    prompt="Investigate.",
                    summary=self.summary,
                    input_dir=ROOT
                    / "data/fixtures/case-002-wind-shift-plan-deviation/input",
                    output_schema=self.schema,
                    output_dir=Path(temporary_directory),
                    run_id="wake-limit-test",
                    now=lambda: "2026-08-29T12:00:00+00:00",
                    git_commit="abc123",
                )

    def test_agent_config_is_comparable_to_frozen_baseline(self) -> None:
        baseline = read_json(ROOT / "config/baseline-v1.json")
        agent = read_json(ROOT / "config/wake-agent-v1.json")

        for field in [
            "provider",
            "api",
            "model",
            "reasoning_effort",
            "max_output_tokens",
            "service_tier",
            "store",
        ]:
            self.assertEqual(agent[field], baseline[field])
        self.assertEqual(agent["max_rounds"], 4)
        self.assertEqual(agent["max_verifier_retries"], 1)

    def test_dry_run_writes_requests_without_calling_api_or_ground_truth(self) -> None:
        client = FakeClient([])
        summaries = [self.summary]

        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory)
            manifest_path = wake_agent.write_agent_dry_run(
                config=self.config,
                prompt="Investigate.",
                summaries=summaries,
                output_schema=self.schema,
                output_dir=output_dir,
            )
            manifest = read_json(manifest_path)
            request = read_json(
                output_dir
                / manifest["requests"][self.summary["case_id"]]["path"]
            )

        self.assertEqual(client.responses.requests, [])
        self.assertFalse(manifest["api_called"])
        self.assertEqual(request["model"], self.config["model"])
        self.assertEqual(len(request["tools"]), 4)
        self.assertNotIn("ground-truth", json.dumps(request).lower())

    def test_public_case_input_resolution_never_returns_ground_truth(self) -> None:
        input_dir = wake_agent.public_case_input_dir(
            ROOT, self.summary["case_id"]
        )

        self.assertEqual(input_dir.name, "input")
        self.assertTrue((input_dir / "speedcoach.csv").is_file())
        self.assertFalse((input_dir / "ground-truth.json").exists())

        with self.assertRaisesRegex(ValueError, "Unknown public case"):
            wake_agent.public_case_input_dir(ROOT, "case-999-not-implemented")

    def test_agent_prompt_names_every_deterministic_investigation_tool(self) -> None:
        prompt = (ROOT / "prompts/wake-agent-v1.md").read_text(encoding="utf-8")

        for tool in wake_agent.TOOL_DEFINITIONS:
            self.assertIn(tool["name"], prompt)
        self.assertIn("Do not expose private chain-of-thought", prompt)
        self.assertIn("must call", prompt.lower())

    def test_default_cli_is_a_no_cost_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_dir = Path(temporary_directory) / "agent-dry-run"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/wake_agent.py"),
                    "--case",
                    self.summary["case_id"],
                    "--output",
                    str(output_dir),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            manifest = read_json(output_dir / "dry-run-manifest.json")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(manifest["api_called"])
        self.assertEqual(list(manifest["requests"]), [self.summary["case_id"]])


if __name__ == "__main__":
    unittest.main()
