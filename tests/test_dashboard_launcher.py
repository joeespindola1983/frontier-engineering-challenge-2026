from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts" / "start_dashboard.sh"


def run_launcher(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    launcher_env = os.environ.copy()
    launcher_env["WAKE_SKIP_ENV_FILE"] = "1"
    if env:
        launcher_env.update(env)
    return subprocess.run(
        ["bash", str(LAUNCHER), *args],
        cwd=ROOT,
        env=launcher_env,
        capture_output=True,
        text=True,
        check=False,
    )


class DashboardLauncherTests(unittest.TestCase):
    def test_script_has_valid_shell_syntax(self) -> None:
        completed = subprocess.run(
            ["bash", "-n", str(LAUNCHER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_help_explains_safe_default_and_paid_opt_in(self) -> None:
        completed = run_launcher("--help")

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Replay mode is the default", completed.stdout)
        self.assertIn("--live", completed.stdout)
        self.assertIn("Ctrl+C", completed.stdout)

    def test_replay_plan_enables_weather_without_exposing_secret(self) -> None:
        secret = "launcher-test-secret"
        completed = run_launcher(
            "--print-plan",
            env={"OPENAI_API_KEY": secret},
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Mode: replay (no model call)", completed.stdout)
        self.assertIn("Weather: enabled", completed.stdout)
        self.assertIn("Dashboard: http://localhost:3000/", completed.stdout)
        self.assertIn("API: http://127.0.0.1:8788/", completed.stdout)
        self.assertNotIn(secret, completed.stdout + completed.stderr)

    def test_live_plan_requires_explicit_api_key(self) -> None:
        completed = run_launcher(
            "--live",
            "--print-plan",
            env={"OPENAI_API_KEY": ""},
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("OPENAI_API_KEY", completed.stderr)

    def test_live_plan_discloses_paid_mode_without_exposing_key(self) -> None:
        secret = "launcher-test-secret"
        completed = run_launcher(
            "--live",
            "--print-plan",
            env={"OPENAI_API_KEY": secret},
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Mode: live (model calls can incur cost)", completed.stdout)
        self.assertIn("Cost authorization: US$0.20", completed.stdout)
        self.assertNotIn(secret, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
