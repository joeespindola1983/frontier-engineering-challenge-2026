from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run_baseline  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class FakeResponses:
    def __init__(self, output: dict) -> None:
        self.output = output
        self.requests: list[dict] = []

    def create(self, **request: object) -> SimpleNamespace:
        self.requests.append(request)
        return SimpleNamespace(
            id="resp_test_001",
            model=request["model"],
            status="completed",
            output_text=json.dumps(self.output),
            usage=SimpleNamespace(
                input_tokens=1000,
                output_tokens=500,
                total_tokens=1500,
                input_tokens_details=SimpleNamespace(cached_tokens=250),
                output_tokens_details=SimpleNamespace(reasoning_tokens=100),
            ),
        )


class FakeClient:
    def __init__(self, output: dict) -> None:
        self.responses = FakeResponses(output)


class BaselineRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = read_json(ROOT / "config/baseline-v1.json")
        self.summary = read_json(
            ROOT
            / "evaluation/baseline-inputs/v1/case-001-misaligned-double-scull.json"
        )
        self.schema = read_json(ROOT / "schemas/analysis-output.schema.json")
        self.prompt = (ROOT / "prompts/baseline-v1.md").read_text(encoding="utf-8")

    def test_build_request_is_direct_structured_call_without_tools(self) -> None:
        request = run_baseline.build_request(
            config=self.config,
            prompt=self.prompt,
            summary=self.summary,
            output_schema=self.schema,
        )

        self.assertEqual(request["model"], "gpt-5.6-terra")
        self.assertEqual(request["reasoning"], {"effort": "medium"})
        self.assertEqual(request["instructions"], self.prompt)
        self.assertEqual(json.loads(request["input"]), self.summary)
        self.assertEqual(request["store"], False)
        self.assertEqual(request["service_tier"], "default")
        self.assertNotIn("tools", request)
        self.assertEqual(request["text"]["format"]["type"], "json_schema")
        self.assertEqual(request["text"]["format"]["strict"], True)
        self.assertEqual(request["text"]["format"]["schema"], self.schema)

    def test_cost_uses_pinned_pricing_and_all_output_tokens(self) -> None:
        usage = {
            "input_tokens": 1_000_000,
            "output_tokens": 1_000_000,
            "total_tokens": 2_000_000,
            "cached_input_tokens": 250_000,
            "reasoning_output_tokens": 100_000,
        }
        cost = run_baseline.estimate_cost_usd(usage, self.config["pricing"])
        self.assertEqual(cost, 14.0)

    def test_output_schema_is_valid_draft_2020_12(self) -> None:
        jsonschema.Draft202012Validator.check_schema(self.schema)

    def test_structured_output_const_fields_declare_an_explicit_type(self) -> None:
        schema_version = self.schema["properties"]["schema_version"]

        self.assertEqual(schema_version["const"], "wake.analysis_output.v1.1")
        self.assertEqual(schema_version["type"], "string")

    def test_execute_case_records_public_observables_without_secret(self) -> None:
        output = {
            "schema_version": "wake.analysis_output.v1.1",
            "case_id": self.summary["case_id"],
            "session_associations": [],
            "plan_summary": None,
            "segments": [],
            "source_policy": [],
            "claims": [],
            "deviations": [],
            "environment_assessment": None,
            "abstentions": [],
            "follow_up_questions": [],
            "coach_briefing": "Insufficient evidence.",
        }
        client = FakeClient(output)

        with tempfile.TemporaryDirectory() as temporary_directory:
            artifact = run_baseline.execute_case(
                client=client,
                config=self.config,
                prompt=self.prompt,
                summary=self.summary,
                output_schema=self.schema,
                output_dir=Path(temporary_directory),
                now=lambda: "2026-08-29T12:00:00+00:00",
                monotonic_values=iter([10.0, 10.25]),
                git_commit="abc123",
                run_id="baseline-v1-test-run",
            )

            manifest = read_json(artifact["manifest_path"])
            saved_output = read_json(artifact["output_path"])

        self.assertEqual(saved_output, output)
        self.assertEqual(manifest["workflow"], "baseline-v1-direct-call")
        self.assertEqual(manifest["run_id"], "baseline-v1-test-run")
        self.assertEqual(manifest["response"]["id"], "resp_test_001")
        self.assertEqual(manifest["runtime_ms"], 250)
        self.assertEqual(manifest["usage"]["total_tokens"], 1500)
        self.assertEqual(manifest["approximate_cost_usd"], 0.008)
        self.assertEqual(manifest["git_commit"], "abc123")
        self.assertNotIn("api_key", json.dumps(manifest).lower())


if __name__ == "__main__":
    unittest.main()
