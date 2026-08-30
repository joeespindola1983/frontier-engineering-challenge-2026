# Session batch processing

**Status:** implemented local prototype; no new paid execution performed

WAKE accepts a batch as an operational envelope while preserving every rowing
session as an independent evidence and execution unit. Multiple sessions are
never concatenated into one model prompt.

```text
source batch
    -> prepare each session independently
    -> preserve failures without aborting the batch
    -> execute eligible bundles sequentially
    -> persist per-session cost, result, and review state
    -> aggregate only explicit validation levels
```

## API

```text
POST /api/source-batches/prepare
GET  /api/source-batches/:id
POST /api/source-batches/:id/execute
```

Preparation accepts up to 100 items. Each item contains a caller-owned
`client_session_id` and the source ids already uploaded through
`POST /api/sources`. The service validates and prepares each item separately,
returns compact metadata only, and records `FAILED_PREPARATION` on a bad item
without discarding valid siblings. Repeating the same ordered request returns
the same content-addressed batch.

Execution requires literal `mode: live` and an explicit batch authorization.
The authorization is converted into a whole number of per-execution start
gates. Execution is sequential; a failed item is isolated, later items may
continue, completed source bundles reuse their saved result, and an unfinished
batch can resume after restart. Neither the batch authorization nor an
individual start gate is a hard provider billing cap.

## Validation levels

WAKE keeps these states distinct:

1. **Data validated** - source shape, hash, and provenance checks passed.
2. **Session reconstructed** - telemetry was deterministically normalized and
   reconstructed.
3. **Plan compared** - a compatible training prescription was available.
4. **Agent verified** - a selected exception passed the bounded agent and
   deterministic verifier.
5. **Human approved** - a qualified human resolved required context and
   approved the result into memory.

No lower level is displayed as a higher one. In particular, no material signal
in available telemetry is not proof that a session was executed as planned.

## Two-week public batch

`data/demo-club-batch/` contains forty independent real-informed synthetic
activity records generated with fixed definitions:

- 38 water records with SpeedCoach-shaped telemetry;
- 37 water records with a comparable plan;
- 31 reconstructed records with no material signal in available evidence;
- three reconstructed alternate solo sessions;
- two separately authorized and preserved agent-verified exceptions;
- one missing-plan route and one missing-athlete-context route;
- two Concept2-shaped indoor records that deliberately remain
  `SOURCE_ADAPTER_REQUIRED`.

The public verifier recomputes the batch from source files, checks every hash,
validates plans, normalizes and reconstructs water telemetry, verifies the two
preserved paid artifacts, and reports 40 data-validated records, 38 reconstructed
water sessions, 37 plan comparisons, two agent-verified sessions, and zero human
approvals. Longitudinal synthesis remains unexecuted.

```bash
uv run python scripts/generate_demo_club_batch.py
uv run python scripts/verify_demo_club_batch.py
```

## Prototype boundaries

- The state store is a user-restricted local JSON file, not an encrypted,
  authenticated, multi-tenant database.
- The batch API groups previously uploaded sources; the browser does not yet
  provide folder or ZIP mapping.
- Concept2-shaped data is preserved but is not normalized by the accepted
  rowing telemetry adapter.
- Batch execution is sequential and resumable, not a distributed queue.
- Longitudinal synthesis requires a separate experiment, acceptance contract,
  and explicit authorization.
