# Longitudinal pilot v1 — official run

This preserved run compares the direct baseline and bounded WAKE workflow on
the same two real-informed synthetic scopes:

- `athlete-lucas`: two-week athlete briefing;
- `club-coach`: club priority briefing over 52 activities.

All four reports use `gpt-5.6-terra`, medium reasoning, the same strict output
schema, and `store: false`. Every final report passed schema, evidence-reference,
modality-boundary, and unsupported-trend verification.

## Observed result

- Four completed reports: two direct baseline and two bounded WAKE.
- Total approximate API cost: **US$0.110426**.
- Direct baseline: **15,035 tokens**, **US$0.064580**.
- Bounded WAKE: **8,238 tokens**, **US$0.045846**, with 16 recorded tool events.
- WAKE cost 29.01% less in this two-case run.
- Both workflows passed the same post-run capability checks.
- **No quality improvement is claimed.** A weighted quality rubric was not
  frozen before execution, so the repository reports no post-hoc score.

The useful result is neutral: bounded investigation preserved the same required
attention and abstention behavior while using fewer resources on these scopes.
This does not establish broad generalization, human-coach superiority, or an
athletic-performance trend.

## Reproduce without another API call

```bash
uv run python scripts/score_longitudinal_pilot.py
```

The command rebuilds `capability-audit.json` from the four committed reports.
Opening the interface or rerunning this audit costs US$0.00.

## Pre-execution failures

`attempts.json` records two API schema rejections that occurred before any model
report was created. They exposed a gap between general JSON Schema validation
and the Structured Outputs subset. Regression tests now reject `uniqueItems`
and untyped `const` fields before a paid execution begins.

