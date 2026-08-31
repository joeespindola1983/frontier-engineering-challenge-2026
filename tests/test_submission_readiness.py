from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.verify_submission_readiness import (
    _tracked_private_paths,
    audit_repository,
    readiness_status,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_submission_readiness.py"


class SubmissionReadinessTests(unittest.TestCase):
    def test_repository_evidence_is_complete_before_the_final_video(self) -> None:
        audit = audit_repository(ROOT)

        self.assertTrue(audit.repository_ready, audit.failures)
        self.assertEqual(audit.agent_output_count, 10)
        self.assertEqual(audit.baseline_output_count, 10)
        self.assertEqual(audit.trajectory_count, 10)
        self.assertEqual(audit.owner_live_qa_run_count, 3)
        self.assertEqual(audit.owner_live_qa_tokens, 90_562)
        self.assertEqual(audit.owner_live_qa_cost_usd, 0.283834)
        self.assertEqual(audit.agent_score, 83.76)
        self.assertEqual(audit.baseline_score, 49.00)
        self.assertEqual(
            audit.status,
            readiness_status(
                repository_ready=audit.repository_ready,
                final_video_ready=audit.final_video_ready,
            ),
        )

    def test_status_distinguishes_repository_failure_video_pending_and_ready(self) -> None:
        self.assertEqual(
            readiness_status(repository_ready=False, final_video_ready=False),
            "NOT_READY",
        )
        self.assertEqual(
            readiness_status(repository_ready=True, final_video_ready=False),
            "PENDING_FINAL_VIDEO",
        )
        self.assertEqual(
            readiness_status(repository_ready=True, final_video_ready=True),
            "READY",
        )

    def test_cli_reports_a_machine_readable_readiness_summary(self) -> None:
        result = subprocess.run(
            [str(SCRIPT), "--json"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn('"repository_ready": true', result.stdout)
        self.assertIn('"agent_output_count": 10', result.stdout)
        self.assertIn('"trajectory_count": 10', result.stdout)
        self.assertIn('"final_video_ready":', result.stdout)

    def test_private_path_audit_works_in_an_extracted_source_archive_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "README.md").write_text("WAKE\n", encoding="utf-8")
            (root / "private-data").mkdir()
            (root / "private-data" / "athlete.csv").write_text(
                "private\n", encoding="utf-8"
            )
            (root / ".env").write_text("OPENAI_API_KEY=secret\n", encoding="utf-8")

            self.assertEqual(
                _tracked_private_paths(root),
                [".env", "private-data/athlete.csv"],
            )


if __name__ == "__main__":
    unittest.main()
