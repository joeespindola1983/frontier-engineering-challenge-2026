# Deterministic Grader v1.1

WAKE's first grader is an offline, versioned implementation of the frozen
100-point rubric. It must be fixed before paid baseline or agent answers are
inspected.

## Inputs

The grader reads:

- one structured `wake.analysis_output.v1.1` JSON file per implemented case;
- the corresponding evaluator-only `ground-truth.json`;
- the public case summary for evidence-reference validation;
- `evaluation/cases.json` to exclude planned cases from the denominator;
- `config/grader-v1.1.json` for weights, versions, critical rules, and legacy
  dimension mapping.

Ground truth is available only to the grader. Neither the baseline nor the WAKE
agent can read it.

## Scoring

Each applicable dimension receives its frozen point weight. Non-applicable
dimensions are removed from that case's denominator, and the earned applicable
points are normalized to a 0–100 case score. The primary run metric is the
macro-average of implemented case scores.

The report includes:

- per-dimension weight, ratio, earned points, reasons, and evidence references;
- segment boundary and distance errors;
- session-match precision and recall;
- deviation precision and recall;
- trusted-source selection accuracy;
- unsupported-claim rate and required-abstention recall;
- required-question precision;
- rubric/grader versions and the grader configuration hash.

Critical rules set the relevant dimension to zero when an output selects a
known broken mobile SPM channel, asserts wind causality from associative data,
or confidently invents unsupported technique, equipment use, or medical state.

## Command

Provide a directory containing one `<case-id>.json` output for every implemented
case. Files for planned cases do not enter the denominator:

```bash
uv run python scripts/grade_outputs.py \
  --outputs /path/to/run/outputs \
  --output /path/to/run/grade-report.json
```

The command performs no network calls.

## Calibration boundary

Grader v1.1 uses structured comparisons, frozen tolerances, and bounded text
concept checks. It does not use an LLM judge. The calibration suite contains
perfect profiles and injected critical failures, but real model phrasing may
expose blind spots. Any scoring change must begin with a failing calibration
test and must increment the grader version when it changes comparable results.

Version 1.1 was frozen after one explicitly excluded, single-case baseline
preflight. Three RED regression tests captured generic representation gaps:
common metric-name aliases, connected pairwise matches that identify the same
multi-source session, and “unassessable” as abstention language. Rubric weights,
ground truth, tolerances, and model outputs were not changed. Version 1.0 remains
committed for auditability; no official baseline-versus-agent result uses it.
