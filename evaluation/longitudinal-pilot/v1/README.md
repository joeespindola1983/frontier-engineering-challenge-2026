# Longitudinal intelligence pilot v1

This directory freezes a two-case, ground-truth-free comparison before any paid
execution:

- `athlete-lucas`: an athlete-centered two-week briefing;
- `club-coach`: a club-level coach priority briefing.

Each case has one direct-baseline request and one bounded-WAKE request. Both use
the same compact input, `gpt-5.6-terra` at medium reasoning, and the same strict
output schema. WAKE can inspect four deterministic views; the baseline cannot.

`preflight/dry-run-manifest.json` records `api_called: false`, four request
hashes, zero saved reports, and a US$0.80 full-run start authorization. That
authorization is not a provider billing cap. The preflight is evidence of
reproducible preparation only—it is not a model result or quality score.

Rebuild and verify without network access:

```bash
uv run python scripts/longitudinal_pilot.py
uv run python scripts/verify_longitudinal_pilot.py
```

Future successful executions belong in a separate run directory with their
structured reports, response IDs, tool events, runtime, usage, approximate
cost, and evaluation. Saved reports can be reopened without another model call.
