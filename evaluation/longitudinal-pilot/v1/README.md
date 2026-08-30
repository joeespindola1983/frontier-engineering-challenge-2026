# Longitudinal intelligence pilot v1

This directory freezes the two-case, ground-truth-free requests that preceded
the official paid execution:

- `athlete-lucas`: an athlete-centered two-week briefing;
- `club-coach`: a club-level coach priority briefing.

Each case has one direct-baseline request and one bounded-WAKE request. Both use
the same compact input, `gpt-5.6-terra` at medium reasoning, and the same strict
output schema. WAKE can inspect four deterministic views; the baseline cannot.

`preflight/dry-run-manifest.json` records `api_called: false`, four request
hashes, zero saved reports, and a US$0.80 full-run start authorization. That
authorization is not a provider billing cap. The official four-report run is
preserved separately under
`evaluation/runs/longitudinal-pilot-v1-20260830/`.

Rebuild and verify without network access:

```bash
uv run python scripts/longitudinal_pilot.py
uv run python scripts/verify_longitudinal_pilot.py
```

The official run observed US$0.110426 total approximate cost. Both workflows
passed the same non-scored post-run capability audit; no quality improvement is
claimed because a weighted rubric was not frozen before execution. Saved
reports and the audit can be reopened without another model call.
