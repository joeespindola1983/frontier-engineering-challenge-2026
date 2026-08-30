# Post-regatta direct baseline preflight

This experiment compares a direct model call with the already-saved bounded
WAKE memory over the exact same compact 102-activity club input and strict
output schema.

The baseline receives no deterministic investigation tools. Its request uses
`gpt-5.6-terra`, medium reasoning, and `store: false`. The non-scored capability
contract was frozen before baseline execution and checks only observable
coverage: supported comparisons, trend abstention, environmental noncausality,
missing-context priorities, unresolved questions, verified deviations, and
evidence/human-review boundaries.

Freeze and verify the request without an API call:

```bash
uv run python scripts/post_regatta_baseline.py
```

The safe command writes the compact input, direct request, capability contract,
hashes, and dry-run manifest under `preflight/`. It reports
`READY_FOR_AUTHORIZATION` and costs US$0.00.

A live run is deliberately separate:

```bash
uv run python scripts/post_regatta_baseline.py \
  --execute \
  --authorized-cost-usd 0.20 \
  --output evaluation/runs/post-regatta-baseline-v1-YYYYMMDD
```

Live execution requires `OPENAI_API_KEY` and a new explicit finite US$0.20
start authorization. The gate is not a provider billing cap. Do not change the
contract after seeing the baseline output; preserve a neutral result if both
workflows cover the same capabilities.

After a verified baseline run, build the frozen non-scored comparison:

```bash
uv run python scripts/score_post_regatta_comparison.py \
  --baseline-artifact evaluation/runs/post-regatta-baseline-v1-YYYYMMDD/reports/club-post-regatta-memory.direct_baseline.json \
  --output evaluation/runs/post-regatta-baseline-v1-YYYYMMDD/capability-audit.json
```

The preserved 2026-08-30 run is under
`evaluation/runs/post-regatta-baseline-v1-20260830/`. It made one verified call,
used `store: false`, cost US$0.043700, used 8,005 tokens, and completed in
19.640 seconds. The frozen audit reports WAKE 7/7 and the direct baseline 3/7.

Read `construct-validity-review.json` with that audit. Manual review found that
four failures were sensitive to canonical IDs, statuses, or output-section
placement even though the baseline expressed much of the same content. The
accepted result is therefore an exact structural-fidelity gain only. It is not
a semantic coaching-quality score, and the frozen audit was not rescored after
review.
