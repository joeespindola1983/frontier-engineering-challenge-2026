#!/usr/bin/env python3
"""Grade an explicit expanded WAKE case set with frozen grader v1.2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from grader_v1_2 import ROOT, grade_output_directory
from run_baseline import write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--outputs",
        required=True,
        type=Path,
        help="Directory containing one <case-id>.json file per selected case.",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path for the versioned JSON grade report.",
    )
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        dest="case_ids",
        help="Explicit case to grade; repeat for a pre-implementation calibration set.",
    )
    args = parser.parse_args()

    report = grade_output_directory(
        args.outputs,
        ROOT,
        case_ids=args.case_ids or None,
    )
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
