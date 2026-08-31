from __future__ import annotations

import unittest
from pathlib import Path

from scripts.build_submission_pdfs import document_specs, report_visual_assets


ROOT = Path(__file__).resolve().parents[1]


class SubmissionPdfTests(unittest.TestCase):
    def test_two_distinct_submission_pdfs_are_declared(self) -> None:
        specs = document_specs(ROOT)

        self.assertEqual(
            [spec.output_name for spec in specs],
            [
                "wake-environment-setup-and-reproduction.pdf",
                "wake-detailed-solution-report.pdf",
            ],
        )
        self.assertEqual(len({spec.title for spec in specs}), 2)

    def test_reproduction_guide_covers_clean_replay_and_optional_live_mode(self) -> None:
        guide = document_specs(ROOT)[0]
        headings = {section.heading for section in guide.sections}
        text = "\n".join(
            paragraph
            for section in guide.sections
            for paragraph in section.paragraphs + section.bullets
        )

        self.assertIn("Clean-environment setup", headings)
        self.assertIn("Replay without an API key", headings)
        self.assertIn("Optional live investigation", headings)
        self.assertIn("Expected outputs and cost", headings)
        self.assertIn("Complete Git checkout status: READY", text)
        self.assertIn("Extracted source-only ZIP status: PENDING_FINAL_VIDEO", text)

    def test_solution_report_preserves_evidence_and_product_boundaries(self) -> None:
        report = document_specs(ROOT)[1]
        text = "\n".join(
            [report.subtitle]
            + [section.heading for section in report.sections]
            + [paragraph for section in report.sections for paragraph in section.paragraphs]
        )

        self.assertIn("83.76", text)
        self.assertIn("49.00", text)
        self.assertIn("metric-level trust", text.lower())
        self.assertIn("does not replace a qualified rowing coach", text.lower())
        self.assertIn("not established", text.lower())

    def test_solution_report_declares_a_complete_visual_product_story(self) -> None:
        assets = report_visual_assets(ROOT)

        self.assertEqual(
            [asset.role for asset in assets],
            [
                "club_overview",
                "team_memory",
                "session_investigation",
                "athlete_history",
                "competition_review",
                "evaluation_results",
            ],
        )
        self.assertTrue(all(asset.path.is_file() for asset in assets))
        self.assertTrue(all(asset.caption for asset in assets))

    def test_solution_report_covers_product_architecture_and_evidence_tables(self) -> None:
        report = document_specs(ROOT)[1]
        headings = {section.heading for section in report.sections}

        self.assertIn("System architecture", headings)
        self.assertIn("Product walkthrough", headings)
        self.assertIn("Measured results", headings)
        self.assertIn("What changed or failed", headings)


if __name__ == "__main__":
    unittest.main()
