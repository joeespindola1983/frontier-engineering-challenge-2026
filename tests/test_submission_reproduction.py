from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/reproduce_submission.sh"
READINESS_SCRIPT = ROOT / "scripts/verify_submission_readiness.py"
PACKAGE_SCRIPT = ROOT / "scripts/build_submission_zip.py"
GUIDE = ROOT / "docs/REPRODUCTION_GUIDE.md"
VIDEO_GUIDE = ROOT / "docs/VIDEO_DEMO_SCRIPT.md"
VOICEOVER_GUIDE = ROOT / "submission" / "video" / "VOICEOVER_ELEVENLABS_V3.md"


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
        self.assertIn("scripts/score_post_regatta_comparison.py", script)
        self.assertIn("scripts/verify_submission_readiness.py", script)
        self.assertIn("mktemp -d", script)
        self.assertIn("wake_reproduction_tmp_dir", script)
        self.assertNotIn(
            "--output evaluation/runs/post-regatta-baseline-v1-20260830/capability-audit.json",
            script,
        )
        self.assertIn("post-regatta-baseline-v1-20260830", script)
        self.assertIn("Node.js 22.13.0 or newer is required", script)
        self.assertIn("node_major", script)
        self.assertIn("'Longitudinal pilot: 4 saved reports, US$0.110426 observed", script)
        self.assertIn("'Club memory contract: WAKE 7/7, baseline 3/7", script)
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
        self.assertIn("scripts/verify_submission_readiness.py", guide)
        self.assertIn("scripts/build_submission_zip.py", guide)
        self.assertIn("source-only ZIP", guide)
        self.assertIn("83.76", guide)
        self.assertIn("49.00", guide)
        self.assertIn("scripts/post_regatta_baseline.py", guide)
        self.assertIn("US$0.20", guide)

    def test_source_package_builder_is_documented_as_a_separate_upload_artifact(self) -> None:
        self.assertTrue(PACKAGE_SCRIPT.is_file())
        guide = GUIDE.read_text(encoding="utf-8")
        self.assertIn("dist/wake-source-submission.zip", guide)
        self.assertIn("50 MiB", guide)
        self.assertIn("final portal", guide)

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
            "Primary audience: coaches and athletes",
            "Product story: 85%",
            "Technical proof: 15%",
            "Lucas",
            "SpeedCoach",
            "Concept2",
            "Competition Review",
            "Every row leaves a wake",
            "The architecture, schemas, trajectories, tests, and exact commands remain in the repository",
        ):
            self.assertIn(required, script)

        self.assertNotIn(
            "The bounded agent can then inspect four read-only tools",
            script,
        )

    def test_elevenlabs_voiceover_sheet_contains_only_generation_ready_audio(self) -> None:
        self.assertTrue(VOICEOVER_GUIDE.is_file())
        sheet = VOICEOVER_GUIDE.read_text(encoding="utf-8")

        self.assertIn("model_id: `eleven_v3`", sheet)
        self.assertEqual(sheet.count("## wake-vo-"), 7)
        self.assertIn("[short pause]", sheet)
        self.assertIn("[confidently]", sheet)
        self.assertIn("[thoughtfully]", sheet)
        self.assertIn("eighty-three point seven six", sheet)
        self.assertIn("forty-nine point zero zero", sheet)
        self.assertIn("Every row leaves a wake", sheet)
        self.assertNotIn("<break", sheet)
        self.assertNotIn("**Screen:**", sheet)
        self.assertNotIn("**Show:**", sheet)
        self.assertNotIn("- OK", sheet)

        prompts = sheet.split("```text\n")[1:]
        self.assertEqual(len(prompts), 7)
        for prompt_with_suffix in prompts:
            prompt = prompt_with_suffix.split("\n```", 1)[0]
            self.assertGreaterEqual(len(prompt), 250)


if __name__ == "__main__":
    unittest.main()
