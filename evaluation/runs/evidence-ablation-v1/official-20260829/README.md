# Evidence Ablation v1 — Official Run

This run executed all three frozen progressive-evidence conditions with the same
`gpt-5.6-terra` model, medium reasoning effort, WAKE agent v1 prompt, Structured
Outputs schema, and bounded four-tool workflow at Git commit `d8aa3c8`.

## Result

- **Core — plan + SpeedCoach:** 7/8 applicable checks, **FAIL**.
- **Context/environment enrichment:** 10/10 checks, **PASS**.
- **Full bundle with mobile:** 12/12 checks, **PASS**.
- **Cross-condition execution consistency:** **FAIL**.
- **Total API cost:** **US$0.298604**.
- **End-to-end runtime:** **92.650 seconds**.
- **Tokens:** 83,452 input; 10,975 output; 94,427 total.

The core condition reconstructed the plan, six work intervals, the true work-05
SPM deviation, SpeedCoach source trust, human-review boundaries, and correct
environmental abstention. It also promoted telemetry-derived segment-boundary
distance loss into an additional `RECONSTRUCTED_WORK_DISTANCE_SHORTFALL` deviation.
That claim is not supported as a plan-execution failure, so the core condition and
cross-condition consistency failed.

The context/environment condition preserved the correct work-05 deviation and
added a noncausal time-aligned environmental association. The full condition also
matched the mobile and SpeedCoach recordings, used mobile GPS as route
corroboration, and rejected the mobile SPM channel that was stuck at zero.

This run supports a narrow conclusion: WAKE's full evidence path demonstrated the
intended mobile capabilities in this synthetic case, while the minimum core path
still needs a stronger deterministic boundary around derived segment distance.
It does not compare WAKE with a coach and does not establish improved athletic
performance.

## Preserved failure and scorer regression

The first offline scoring attempt crashed because the unexpected extra deviation
had `segment_ref: null`. A regression test was added and the reporter was corrected
to treat that value as an observable failure rather than failing to produce a
report. Model outputs, trajectories, frozen inputs, prompt, and scoring checks were
not changed after the run.

## Evidence map

- `run-manifest.json`: model configuration hash, prompt hash, Git commit, runtime,
  tokens, and cost.
- `outputs/`: three verified structured analyses.
- `trajectories/`: observable tool, verifier, retry, usage, and timing events.
- `ablation-report.json`: condition-aware checks and marginal capabilities.
