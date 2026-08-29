#!/usr/bin/env python3
"""Grade a complete directory of WAKE structured outputs without network access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from grader import ROOT, grade_output_directory
from run_baseline import write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outputs",
        required=True,
        type=Path,
        help="Directory containing one <case-id>.json file per implemented case.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path for the versioned JSON grade report.",
    )
    args = parser.parse_args()

    report = grade_output_directory(args.outputs, ROOT)
    write_json(args.output, report)
    print(
        json.dumps(
            {
                "grader_version": report["grader_version"],
                "graded_case_count": report["graded_case_count"],
                "macro_average_score": report["macro_average_score"],
                "report": str(args.output),
                "network_called": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
