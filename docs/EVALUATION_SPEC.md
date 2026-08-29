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

## Baseline protocol

The simple baseline will use one direct model call with:

- the same case input available to WAKE, converted only to a size-safe deterministic summary;
- a single versioned prompt;
- no iterative tool calls;
- no persistent memory;
- no claim verifier;
- no access to ground truth.

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
