from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/reproduce_submission.sh"
GUIDE = ROOT / "docs/REPRODUCTION_GUIDE.md"
VIDEO_GUIDE = ROOT / "docs/VIDEO_DEMO_SCRIPT.md"


class SubmissionReproductionTests(unittest.TestCase):
    def test_reproduction_script_is_safe_and_explains_zero_cost_default(self) -> None:
        self.assertTrue(SCRIPT.is_file())
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)
        help_result = subprocess.run(
            [str(SCRIPT), "--help"],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("US$0.00", help_result.stdout)
        self.assertIn("--verify-only", help_result.stdout)
        self.assertIn("never calls the OpenAI API", help_result.stdout)

        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("unset OPENAI_API_KEY", script)
        self.assertIn("uv sync --frozen", script)
        self.assertIn("npm ci", script)
        self.assertIn("scripts/test_all.py", script)
        self.assertIn("scripts/score_longitudinal_pilot.py", script)
        self.assertIn("Node.js 22.13.0 or newer is required", script)
        self.assertIn("node_major", script)
        self.assertIn("'Longitudinal pilot: 4 saved reports, US$0.110426 observed", script)
        self.assertNotIn("--execute", script)

    def test_clean_environment_guide_covers_every_required_submission_detail(self) -> None:
        self.assertTrue(GUIDE.is_file())
        guide = GUIDE.read_text(encoding="utf-8")
        for required in (
            "Clean-environment reproduction",
            "Required versions",
            "Included public data",
            "Install and verify",
            "Run the solution",
            "Reproduce the baseline",
            "Reproduce the evaluation",
            "Expected output",
            "Approximate runtime",
            "Approximate cost",
            "OPENAI_API_KEY",
            "US$0.00",
        ):
            self.assertIn(required, guide)
        self.assertIn("scripts/reproduce_submission.sh", guide)
        self.assertIn("scripts/start_dashboard.sh", guide)
        self.assertIn("83.76", guide)
        self.assertIn("49.00", guide)
        self.assertIn("scripts/post_regatta_baseline.py", guide)
        self.assertIn("US$0.20", guide)

    def test_video_script_covers_the_required_five_minute_submission_story(self) -> None:
        self.assertTrue(VIDEO_GUIDE.is_file())
        script = VIDEO_GUIDE.read_text(encoding="utf-8")
        for required in (
            "00:00",
            "04:50",
            "simple baseline",
            "102 activities",
            "human checkpoint",
            "83.76",
            "49.00",
            "removed experiment",
            "US$0.00",
        ):
            self.assertIn(required, script)


if __name__ == "__main__":
    unittest.main()
