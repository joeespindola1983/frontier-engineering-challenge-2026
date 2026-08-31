#!/usr/bin/env python3
"""Audit the public WAKE submission package without calling a model.

The repository and final video are separate gates. Before recording, a healthy
checkout reports ``PENDING_FINAL_VIDEO`` with a zero exit code. The final manual
gate uses ``--require-final-video`` and fails until the named submission video
exists.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
FINAL_VIDEO = Path("submission/video/wake-final-submission.mp4")

REQUIRED_FILES = (
    Path("README.md"),
    Path("IMPROVEMENT_CHANGELOG.md"),
    Path("docs/PREEXISTING_WORK.md"),
    Path("docs/SUBMISSION_REQUIREMENTS.md"),
    Path("docs/SUBMISSION_AUDIT.md"),
    Path("docs/REPRODUCTION_GUIDE.md"),
    Path("docs/VIDEO_DEMO_SCRIPT.md"),
    Path("docs/THIRD_PARTY_AND_DATA_RIGHTS.md"),
    Path("submission/video/VOICEOVER_ELEVENLABS_V3.md"),
    Path("prompts/baseline-v1.md"),
    Path("prompts/wake-agent-v2.md"),
    Path("scripts/reproduce_submission.sh"),
    Path("scripts/start_dashboard.sh"),
    Path("scripts/build_representative_product_trajectory.py"),
    Path("evaluation/trajectories/representative-product-replay-v1.json"),
    Path("evaluation/runs/expanded-evaluation-v2/official-20260830/agent/run-manifest.json"),
    Path("evaluation/runs/expanded-evaluation-v2/official-20260830/agent/grade-report-v1.2.json"),
    Path("evaluation/runs/expanded-evaluation-v2/official-20260830/baseline/run-manifest.json"),
    Path("evaluation/runs/expanded-evaluation-v2/official-20260830/baseline/grade-report-v1.2.json"),
    Path("evaluation/runs/longitudinal-pilot-v1-20260830/run-manifest.json"),
    Path("evaluation/runs/post-regatta-memory-v1-20260830/run-manifest.json"),
    Path("evaluation/runs/post-regatta-baseline-v1-20260830/run-manifest.json"),
    Path("evaluation/runs/product-live-bundles/owner-live-qa-20260830.run-manifest.json"),
    Path("evaluation/runs/product-live-bundles/OWNER_LIVE_QA_20260830.md"),
)


@dataclass(frozen=True)
class SubmissionAudit:
    status: str
    repository_ready: bool
    final_video_ready: bool
    agent_output_count: int
    baseline_output_count: int
    trajectory_count: int
    agent_score: float | None
    baseline_score: float | None
    owner_live_qa_run_count: int
    owner_live_qa_tokens: int
    owner_live_qa_cost_usd: float | None
    failures: tuple[str, ...]


def readiness_status(*, repository_ready: bool, final_video_ready: bool) -> str:
    if not repository_ready:
        return "NOT_READY"
    if not final_video_ready:
        return "PENDING_FINAL_VIDEO"
    return "READY"


def _read_score(path: Path, failures: list[str], expected: float) -> float | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        score = float(payload["macro_average_score"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"Cannot read score from {path}: {exc}")
        return None
    if score != expected:
        failures.append(f"Unexpected score in {path}: {score} != {expected}")
    if payload.get("graded_case_count") != 10:
        failures.append(f"Expected 10 graded cases in {path}")
    return score


def _tracked_private_paths(root: Path) -> list[str]:
    def is_private(path: str) -> bool:
        name = Path(path).name
        return (
            name == ".env"
            or (name.startswith(".env.") and name != ".env.example")
            or path.startswith("private-data/")
            or path.endswith("/local-state.json")
        )

    result = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        candidates = result.stdout.splitlines()
    else:
        candidates = [
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and not path.is_symlink()
        ]
    return sorted(path for path in candidates if is_private(path))


def _validate_voiceover(path: Path, failures: list[str]) -> None:
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    prompts = content.split("```text\n")[1:]
    if len(prompts) != 7:
        failures.append("Voiceover sheet must contain seven text prompts")
        return
    for index, prompt_with_suffix in enumerate(prompts, start=1):
        prompt = prompt_with_suffix.split("\n```", 1)[0].strip()
        if len(prompt) < 250:
            failures.append(f"Voiceover prompt {index} is incomplete ({len(prompt)} chars)")
    if "- OK" in content:
        failures.append("Voiceover sheet contains owner QA comments")


def _read_owner_live_qa(
    root: Path, failures: list[str]
) -> tuple[int, int, float | None]:
    manifest_path = (
        root
        / "evaluation/runs/product-live-bundles/owner-live-qa-20260830.run-manifest.json"
    )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        run_count = int(payload["execution_count"])
        tokens = int(payload["total_usage"]["total_tokens"])
        cost = float(payload["total_approximate_cost_usd"])
        runs = payload["runs"]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        failures.append(f"Cannot read owner live QA manifest: {exc}")
        return 0, 0, None

    if run_count != 3 or len(runs) != 3:
        failures.append(f"Expected 3 owner live QA runs; found {run_count}")
    if tokens != 90_562:
        failures.append(f"Unexpected owner live QA token total: {tokens}")
    if cost != 0.283834:
        failures.append(f"Unexpected owner live QA cost total: {cost}")
    if payload.get("all_verified") is not True:
        failures.append("Owner live QA manifest is not fully verified")

    manifest_root = manifest_path.parent
    for run in runs:
        for path_key, hash_key in (
            ("output", "output_sha256"),
            ("trajectory", "trajectory_sha256"),
        ):
            artifact = manifest_root / run[path_key]
            if not artifact.is_file():
                failures.append(f"Missing owner live QA artifact: {artifact}")
                continue
            actual_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
            if actual_hash != run[hash_key]:
                failures.append(f"Hash mismatch for owner live QA artifact: {artifact}")
    return run_count, tokens, cost


def audit_repository(root: Path = ROOT) -> SubmissionAudit:
    root = root.resolve()
    failures: list[str] = []

    for relative_path in REQUIRED_FILES:
        if not (root / relative_path).is_file():
            failures.append(f"Missing required file: {relative_path}")

    official = root / "evaluation/runs/expanded-evaluation-v2/official-20260830"
    agent_outputs = tuple((official / "agent/outputs").glob("case-*.json"))
    baseline_outputs = tuple((official / "baseline/outputs").glob("case-*.json"))
    trajectories = tuple((official / "agent/trajectories").glob("case-*.trajectory.json"))
    for label, count in (
        ("agent outputs", len(agent_outputs)),
        ("baseline outputs", len(baseline_outputs)),
        ("agent trajectories", len(trajectories)),
    ):
        if count != 10:
            failures.append(f"Expected 10 {label}; found {count}")

    agent_score = _read_score(
        official / "agent/grade-report-v1.2.json", failures, 83.76
    )
    baseline_score = _read_score(
        official / "baseline/grade-report-v1.2.json", failures, 49.00
    )

    _validate_voiceover(
        root / "submission/video/VOICEOVER_ELEVENLABS_V3.md", failures
    )
    owner_live_qa_run_count, owner_live_qa_tokens, owner_live_qa_cost_usd = (
        _read_owner_live_qa(root, failures)
    )

    try:
        tracked_private = _tracked_private_paths(root)
    except (OSError, subprocess.CalledProcessError) as exc:
        failures.append(f"Cannot inspect tracked paths: {exc}")
    else:
        if tracked_private:
            failures.append(
                "Private or local-state paths are tracked: " + ", ".join(tracked_private)
            )

    repository_ready = not failures
    final_video_ready = (root / FINAL_VIDEO).is_file()
    return SubmissionAudit(
        status=readiness_status(
            repository_ready=repository_ready,
            final_video_ready=final_video_ready,
        ),
        repository_ready=repository_ready,
        final_video_ready=final_video_ready,
        agent_output_count=len(agent_outputs),
        baseline_output_count=len(baseline_outputs),
        trajectory_count=len(trajectories),
        agent_score=agent_score,
        baseline_score=baseline_score,
        owner_live_qa_run_count=owner_live_qa_run_count,
        owner_live_qa_tokens=owner_live_qa_tokens,
        owner_live_qa_cost_usd=owner_live_qa_cost_usd,
        failures=tuple(failures),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    parser.add_argument(
        "--require-final-video",
        action="store_true",
        help=f"Fail unless {FINAL_VIDEO} exists",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    audit = audit_repository(ROOT)
    if args.json:
        print(json.dumps(asdict(audit), indent=2, sort_keys=True))
    else:
        print(f"Submission status: {audit.status}")
        print(
            "Official comparison: "
            f"{audit.agent_output_count} WAKE outputs, "
            f"{audit.baseline_output_count} baseline outputs, "
            f"{audit.trajectory_count} trajectories"
        )
        print(f"Scores: WAKE {audit.agent_score} / baseline {audit.baseline_score}")
        owner_live_qa_cost = (
            f"US${audit.owner_live_qa_cost_usd:.6f}"
            if audit.owner_live_qa_cost_usd is not None
            else "unavailable"
        )
        print(
            "Owner live QA: "
            f"{audit.owner_live_qa_run_count} runs, "
            f"{audit.owner_live_qa_tokens} tokens, "
            f"{owner_live_qa_cost}"
        )
        if audit.failures:
            for failure in audit.failures:
                print(f"ERROR: {failure}")
        elif not audit.final_video_ready:
            print(f"Pending manual deliverable: {FINAL_VIDEO}")

    if not audit.repository_ready:
        return 1
    if args.require_final_video and not audit.final_video_ready:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
