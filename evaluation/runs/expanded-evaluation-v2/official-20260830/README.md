# Expanded Controlled Comparison v2

This directory contains the official ten-case comparison between the direct
model baseline and the bounded WAKE investigation agent. Both arms used the
same committed `baseline-inputs/v2` summaries, `gpt-5.6-terra`, medium
reasoning effort, service tier, structured output schema, and deterministic
grader v1.2. The baseline received no tools. WAKE could call four deterministic
investigation tools and pass its candidate through the bounded verifier.

## Primary result

- Direct baseline macro-average: **49.00 / 100**.
- WAKE macro-average: **83.76 / 100**.
- Absolute improvement: **+34.76 points**.
- Relative improvement over baseline: **+70.94%**.
- Baseline API cost: **US$0.428172**.
- WAKE API cost: **US$0.711516**.
- Incremental agent cost: **US$0.283344**.
- Total comparison cost: **US$1.139688**.
- Baseline tokens: **80,686**; WAKE tokens: **200,893**.
- Baseline summed case runtime: **241.503 seconds**.
- WAKE end-to-end runtime: **234.812 seconds**.

All ten cases improved:

| Case | Direct baseline | WAKE | Delta |
| --- | ---: | ---: | ---: |
| 001 - misaligned double scull | 48.89 | 53.71 | +4.82 |
| 002 - wind shift and plan deviation | 47.50 | 82.14 | +34.64 |
| 003 - calm expert compliant | 57.69 | 89.68 | +31.99 |
| 004 - steady headwind compliant | 65.38 | 87.69 | +22.31 |
| 005 - tailwind speed is not improvement | 63.46 | 85.06 | +21.60 |
| 006 - crosswind and gusts | 64.11 | 85.06 | +20.95 |
| 007 - incomplete intervals | 25.00 | 86.38 | +61.38 |
| 008 - correct distance, wrong SPM | 27.27 | 92.35 | +65.08 |
| 009 - excessive recovery | 33.33 | 87.80 | +54.47 |
| 010 - mobile SPM stuck at zero | 57.35 | 87.69 | +30.34 |

## What improved and what did not

WAKE reached 100% deviation detection versus 55.56% for the baseline and
88.41% segment reconstruction versus 0%. Metric-level source trust improved
from 15.00% to 61.67%. The largest case gains came from finding a low-SPM work
interval, a missing interval, and an excessive recovery without treating
boundary-derived segment distance as proof of prescribed-distance completion.

The result is not uniformly better in every dimension. Environmental
interpretation fell from 80.00% for the direct baseline to 76.00% for WAKE.
Case 001 remains the weakest WAKE case at 53.71 because source selection,
abstention phrasing, and follow-up-question precision are still incomplete.
These failures are retained rather than optimized after seeing the official
outputs.

WAKE made 40 deterministic tool calls, four per case. Five first candidates
failed deterministic verification and passed after one bounded correction.
Trajectories record tool calls, tool results, verification events, usage,
runtime, cost, and final output; they do not store private chain-of-thought.

## Validity boundary

This comparison establishes that the current bounded workflow outperformed one
direct call on these ten fixed, mostly synthetic cases. It does not establish
superiority over a human rowing coach, broad generalization to clubs or water
conditions, improved athlete performance, medical validity, or production
reliability. Eight cases are synthetic or derived synthetic; case 001 is the
only real anonymized source case. The deterministic grader is reproducible but
still uses bounded text and structured-field matching rather than human expert
judgment.

## Saved evidence and no-cost review

- `baseline/outputs/` and `agent/outputs/` contain the final structured answers.
- `baseline/run-manifest.json` and `agent/run-manifest.json` contain model,
  token, cost, runtime, and artifact metadata.
- `baseline/cases/` contains per-case direct-call manifests.
- `agent/trajectories/` contains the observable agent execution history.
- Each arm's `grade-report-v1.2.json` contains offline per-case and
  per-dimension scoring reasons.

These artifacts can be reopened, rendered, compared, and graded again without
calling a model. A new answer or a materially changed prompt/input still
requires a new paid execution.
