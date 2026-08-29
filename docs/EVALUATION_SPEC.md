# WAKE Evaluation Specification

**Version:** 1.0

**Frozen:** 2026-08-29

**Status:** accepted for the first baseline and agent comparison

## Objective

Evaluate whether WAKE reconstructs rowing sessions, selects evidence per metric, distinguishes execution from environmental effects, and abstains when the supplied evidence cannot support a claim.

The primary metric is the mean weighted rubric score across the same fixed cases for the baseline and every later workflow. Ground truth is evaluator-only and must never be included in model input.

## Information boundary

An evaluated run may receive:

- files under a case's `input/` directory;
- public schema definitions;
- the workflow's normal deterministic tools;
- human answers explicitly represented as runtime checkpoints.

It must not receive:

- `ground-truth.json`;
- evaluator code containing expected answers;
- another run's output;
- private source manifests or raw private telemetry.

A run that crosses this boundary is invalid rather than high-scoring.

## Weighted rubric

| Dimension | Points | Full-credit behavior |
| --- | ---: | --- |
| Plan interpretation | 15 | Reconstructs prescribed blocks, ranges, recovery, equipment, and unresolved terminology without silently normalizing ambiguity away. |
| Session association and alignment | 15 | Matches or rejects recordings correctly and reports offsets, overlap, and reasons. |
| Segment reconstruction | 15 | Locates work and recovery segments with correct order, distance/duration, and boundaries within case tolerance. |
| Metric-level source trust | 15 | Selects evidence independently for distance, route, speed, SPM, environment, and context; exposes conflicts instead of averaging them blindly. |
| Deviation detection | 15 | Detects true plan deviations while avoiding false failures caused by acceptable ranges or environmental conditions. |
| Environmental interpretation | 10 | Uses time-aligned wind and route evidence, separates association from causation, and avoids treating wind-aided speed as automatic improvement. |
| Evidence and abstention | 10 | Every material claim has evidence; unsupported technique, equipment, health, and causal claims are omitted or explicitly marked unknown. |
| Follow-up questions | 5 | Asks only questions whose answers could materially change the conclusion and prioritizes the most useful one. |
| **Total** | **100** | |

Each case's ground truth identifies which dimensions apply. Non-applicable dimensions are removed from the denominator for that case rather than awarded automatically.

## Scoring rules

- Numeric tolerances and allowed categorical answers live in versioned ground truth.
- A correct value with an invented evidence reference receives no credit for that claim.
- An incorrect confident claim is penalized more than an explicit, appropriate abstention.
- Claiming visible technique, crew synchronization, resistance equipment use, or medical state from ordinary GPS/SPM evidence sets the Evidence and abstention dimension to zero.
- Treating a tailwind-aided result as proven athlete improvement sets the Environmental interpretation dimension to zero.
- Using a mobile SPM channel known to be stuck at zero as valid SPM evidence sets Metric-level source trust to zero.
- Scores must include grader reasons and evidence references, not only totals.

## Deterministic grader v1.1

`config/grader-v1.1.json` freezes the rubric weights, legacy-case dimension adapter, critical zero rules, and macro-average definition. `scripts/grader.py` validates structured outputs, applies numeric tolerances and categorical rules, and emits per-dimension reasons, evidence references, and secondary metrics. `scripts/grade_outputs.py` grades one complete output directory offline. The earlier `config/grader-v1.json` remains immutable as calibration history.

Case 001 predates the full ground-truth schema. Grader v1.1 preserves that frozen artifact and explicitly maps it to four applicable dimensions: session association and alignment, metric-level source trust, evidence and abstention, and follow-up questions. Case 002 declares all eight dimensions directly.

The grader intentionally does not use a model-as-judge. Structured values, tolerances, source IDs, critical prohibited claims, and bounded concept checks are deterministic and regression-tested. This improves reproducibility but does not make semantic grading perfect; new phrasing failures must be added as grader calibration tests and require a grader-version increment before changing comparable scores.

## Primary and secondary metrics

**Primary:** macro-average weighted rubric score from 0 to 100 across the frozen case registry.

**Secondary:**

- unsupported material claim rate;
- required-abstention recall;
- plan-block extraction accuracy;
- session-match precision and recall;
- segment-boundary error in seconds and meters;
- deviation detection precision and recall;
- trusted-source selection accuracy;
- required-question precision;
- runtime, model tokens, and approximate cost.

## Evidence ablation protocol

The controlled baseline comparison answers whether the bounded WAKE workflow
outperforms one direct model call on the same evidence. It does not establish the
incremental value of mobile telemetry or superiority over a human coach.

Evaluate optional-source value by running the same frozen case and workflow with:

1. plan + SpeedCoach only;
2. plan + SpeedCoach + context/environment;
3. the full bundle including mobile telemetry.

Record which rubric dimensions are applicable in each condition. Compare
deviation precision/recall, source-selection accuracy, unsupported-claim rate,
required-abstention recall, session-association confidence, and required-question
precision. Never award a reduced-evidence condition for a capability its inputs
cannot support.

A later coach-process pilot must compare a coach reviewing plan + SpeedCoach with
the same coach reviewing a WAKE briefing over the same evidence. Measure review
time, material omissions, corrections, usefulness, and confidence. With one coach
or a small number of sessions, label the result a usability pilot rather than a
general performance claim. Do not claim improved athletic performance without a
longitudinal outcome study.

The first ground-truth-free condition bundle is frozen under
`evaluation/ablation-inputs/v1/`. Its manifest records the base session, summary
hashes, included source files, and capabilities available in each condition. It
is input preparation only; it must not be presented as an ablation result until
the same versioned runner executes every condition and the condition-aware
scoring contract is frozen.

The version 1 runner and capability reporter are now implemented. Dry-run is the
default and constructs all three structured requests. Paid execution cannot
select only a favorable condition. Each condition receives only the files listed
in its frozen manifest entry. The reporter checks schema/provenance verification,
plan and execution reconstruction, deviation identity, SpeedCoach SPM selection,
human-review boundaries, condition-aware environmental behavior, mobile session
corroboration, and rejection of broken mobile SPM. It also requires the execution
and deviation signature to remain stable across conditions. It does not calculate
one overall score that would punish deliberately unavailable capabilities.

The official v1 run cost US$0.298604 and produced a failing experiment report.
The core condition added an unsupported aggregate distance-shortfall deviation
from telemetry-derived segment boundaries; context/environment and full evidence
passed their 10 and 12 applicable checks respectively. The failure remains part
of the evidence. Any correction must be evaluated as a new workflow iteration;
the v1 outputs and contract must not be rewritten.

## Baseline protocol

The simple baseline will use one direct model call with:

- the same case input available to WAKE, converted only to a size-safe deterministic summary;
- a single versioned prompt;
- no iterative tool calls;
- no persistent memory;
- no claim verifier;
- no access to ground truth.

The frozen version 1 artifacts are `prompts/baseline-v1.md` and `evaluation/baseline-inputs/v1/`. The input bundle is generated by `scripts/build_baseline_inputs.py`, contains only compact deterministic summaries of case inputs, and is checked for evaluator-answer leakage by `scripts/verify_baseline_inputs.py`.

The first comparison is configured in `config/baseline-v1.json` with `gpt-5.6-terra`, reasoning effort `medium`, 12,000 maximum output tokens, default service tier, `store: false`, and strict Structured Outputs. `scripts/run_baseline.py` defaults to a no-cost dry-run and requires both `--execute` and `OPENAI_API_KEY` for a real call.

Before the first scored run, record the model, model snapshot when available, temperature, prompt hash, input-summary hash, runtime, tokens, and cost. Later agent runs must use the same case versions and grader version.

## Case design

The registry contains one complex demonstration case and isolated diagnostic cases. Complex cases show product value; isolated cases reveal why a workflow failed. Synthetic cases use fixed seeds, explicit generation versions, and evaluator-visible injected faults.

The first synthetic demonstration combines:

- a six-by-one-kilometer plan;
- a wind shift during the fourth work interval;
- a real SPM deviation in the fifth interval;
- a mobile SPM channel stuck at zero;
- an equipment instruction that telemetry cannot confirm.

## Versioning and comparability

- Any changed input, expected answer, tolerance, rubric, grader, or generator increments its version.
- Results from different case or grader versions are not directly comparable.
- Add new cases without rewriting old outcomes.
- Keep failed and removed experiments in `IMPROVEMENT_CHANGELOG.md`.
- Every result table must state implemented case count; planned cases never enter the denominator.

## Required run artifact

Each evaluation run must record:

- run ID and timestamp;
- Git commit;
- case, generator, schema, prompt, workflow, and grader versions;
- model configuration;
- input hashes;
- tool calls and compact tool responses;
- human checkpoints;
- final structured claims;
- per-dimension grader results;
- runtime, token usage, and approximate cost.

Do not store private chain-of-thought. Store only observable actions, evidence, concise reasons, and outputs.
