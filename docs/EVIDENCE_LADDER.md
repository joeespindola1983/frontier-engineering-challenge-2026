# WAKE Progressive Evidence Contract

**Status:** implemented for local source preparation and explicit live execution

WAKE must work with evidence already available in a rowing club and become more
capable as additional sources are supplied. Optional evidence may increase
confidence or unlock a new type of interpretation, but its absence must never be
silently converted into a fact.

## Source roles

### Core evidence

- **Training plan:** defines the intended work, recovery, SPM ranges, and known
  instructions.
- **SpeedCoach:** supplies the primary water-session execution stream for the MVP.

Both are required for the current plan-versus-performed workflow. Without a plan,
WAKE could only summarize a recording; without SpeedCoach, the current MVP cannot
verify water-session execution.

### Evidence enhancers

- **Mobile telemetry:** independently corroborates route and distance, helps
  associate recordings whose clocks differ, and exposes cross-device conflicts.
  Mobile SPM is trusted only when its quality report supports it.
- **Environment:** enables time-aligned condition interpretation. It does not
  establish that wind caused a performance change.
- **Session context:** supplies boat, crew, goal, equipment confirmation, perceived
  effort, and coach observations as human evidence.

## Graceful degradation

| Available evidence | Supported conclusion | Explicit limitation |
| --- | --- | --- |
| Plan + SpeedCoach | Reconstruct planned versus performed work, SPM, distance, pace, and deviations | Route and distance have no independent corroboration |
| + Mobile | Compare clocks, routes, and cumulative distance; detect source conflicts | Mobile does not automatically replace SpeedCoach for SPM |
| + Environment | Associate time-aligned conditions with session changes | Association is not causation |
| + Context | Interpret boat, crew, goal, and human observations | Human confirmation remains distinct from telemetry |

The preparation response exposes every source as `CORE` or `ENHANCER` and as
`PRESENT` or `ABSENT`. The compact case summary records the consequences of each
absence in `evidence_gaps`.

## Evaluation implication

Mobile value must be measured, not assumed. Use the same fixed case in at least
three evidence conditions:

1. plan + SpeedCoach;
2. plan + SpeedCoach + context/environment;
3. the full bundle including mobile.

Compare deviation precision/recall, source-selection accuracy, unsupported-claim
rate, required-abstention recall, session-association confidence, and required
question precision. This ablation is separate from the existing direct-model
baseline and from any future coach usability pilot.

The deterministic version 1 inputs are frozen at
`evaluation/ablation-inputs/v1/manifest.json`. They contain no evaluator answers
and can be rebuilt with `scripts/build_evidence_ablation.py`.
`scripts/run_evidence_ablation.py` generates all three requests by default and
requires explicit `--execute` plus an API key
for a paid run. `scripts/score_evidence_ablation.py` verifies each output against
its available capabilities and checks that the core execution result remains
stable as evidence is added.

The report intentionally omits an overall score across conditions. Missing
mobile or environment is not a failure when that source was deliberately removed;
false corroboration, unsupported environmental claims, or selection of broken
mobile SPM are failures.

The first official v1 run is preserved under
`evaluation/runs/evidence-ablation-v1/official-20260829/`. Core passed 7/8 checks
but failed by converting segment-boundary distance loss into an unsupported
distance shortfall. Context/environment passed 10/10, and full evidence passed
12/12 while demonstrating route corroboration and mobile-SPM rejection. Because
the core deviation signature changed, the overall experiment status is `FAIL`.

Workflow v2 keeps those inputs frozen and changes only the failure boundary:
segment distances produced by SPM classification are explicitly insufficient for
prescribed-distance completion or shortfall. The prompt and tool description
state the same rule, and the verifier rejects a conflicting deviation. The
committed v2 preflight contains no model call or quality result.

The separate official v2 run is preserved under
`evaluation/runs/evidence-ablation-v2/official-20260829/`. Core passed 8/8,
context/environment 10/10, and full evidence 12/12; work-05 remained the only
plan deviation across all three conditions, so execution consistency passed.
This supports the progressive-evidence workflow for the frozen synthetic case
without making mobile mandatory or claiming broad generalization.
