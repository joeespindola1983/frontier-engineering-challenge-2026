from __future__ import annotations

import tempfile
import unittest
import zipfile
import stat
from pathlib import Path

from scripts.build_submission_zip import build_source_zip


class SubmissionPackageTests(unittest.TestCase):
    def test_source_zip_excludes_secrets_dependencies_runtime_state_and_video_drafts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "wake"
            root.mkdir()
            (root / "README.md").write_text("WAKE\n", encoding="utf-8")
            (root / ".env.example").write_text("OPENAI_API_KEY=\n", encoding="utf-8")
            (root / ".env").write_text("OPENAI_API_KEY=secret\n", encoding="utf-8")
            (root / "web" / "app").mkdir(parents=True)
            (root / "web" / "app" / "page.tsx").write_text("export default null;\n", encoding="utf-8")
            (root / "scripts").mkdir()
            reproduction_script = root / "scripts" / "reproduce_submission.sh"
            reproduction_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            reproduction_script.chmod(0o755)
            (root / "web" / "node_modules").mkdir()
            (root / "web" / "node_modules" / "package.js").write_text("dependency\n", encoding="utf-8")
            (root / "web" / ".wrangler").mkdir()
            (root / "web" / ".wrangler" / "state.sqlite").write_bytes(b"runtime")
            (root / "private-data").mkdir()
            (root / "private-data" / "athlete.csv").write_text("private\n", encoding="utf-8")
            (root / "tmp" / "pdfs").mkdir(parents=True)
            (root / "tmp" / "pdfs" / "rendered-page.png").write_bytes(b"temporary-render")
            (root / "submission" / "video").mkdir(parents=True)
            (root / "submission" / "video" / "wake-final-submission-draft-v11.mp4").write_bytes(b"draft")
            (root / "submission" / "video" / "wake-final-submission-draft-v11.en.srt").write_text(
                "draft captions\n", encoding="utf-8"
            )
            (root / "output" / "pdf").mkdir(parents=True)
            (root / "output" / "pdf" / "wake-detailed-solution-report.pdf").write_bytes(
                b"public-pdf"
            )

            output = Path(temporary_directory) / "wake-source.zip"
            result = build_source_zip(root, output, max_bytes=50 * 1024 * 1024)

            self.assertEqual(result.output_path, output.resolve())
            self.assertLess(result.size_bytes, 50 * 1024 * 1024)
            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                script_mode = archive.getinfo(
                    "wake/scripts/reproduce_submission.sh"
                ).external_attr >> 16

            self.assertIn("wake/README.md", names)
            self.assertIn("wake/.env.example", names)
            self.assertIn("wake/web/app/page.tsx", names)
            self.assertIn(
                "wake/output/pdf/wake-detailed-solution-report.pdf", names
            )
            self.assertNotIn("wake/.env", names)
            self.assertFalse(any("node_modules" in name for name in names))
            self.assertFalse(any(".wrangler" in name for name in names))
            self.assertFalse(any("private-data" in name for name in names))
            self.assertFalse(any("tmp" in Path(name).parts for name in names))
            self.assertFalse(any(name.endswith(".mp4") for name in names))
            self.assertFalse(any("wake-final-submission-draft" in name for name in names))
            self.assertEqual(stat.S_IMODE(script_mode), 0o755)

    def test_source_zip_is_byte_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory) / "wake"
            root.mkdir()
            (root / "README.md").write_text("WAKE\n", encoding="utf-8")
            first = Path(temporary_directory) / "first.zip"
            second = Path(temporary_directory) / "second.zip"

            build_source_zip(root, first, max_bytes=50 * 1024 * 1024)
            build_source_zip(root, second, max_bytes=50 * 1024 * 1024)

            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
