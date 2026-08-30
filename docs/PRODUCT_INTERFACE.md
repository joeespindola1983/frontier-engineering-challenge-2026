# WAKE Product Interface Contract

**Status:** accepted replay with a tested end-to-end local live workflow

## Purpose

The product interface helps a rowing coach understand one session without manually reconciling a plan, device exports, conditions, and verbal context. It is a calm review instrument, not an analytics command center or an evaluation console.

```text
Receive fragmented evidence
        -> reconstruct the session
        -> surface material findings and limitations
        -> ask one focused human question when needed
        -> produce a verified briefing
        -> add approved context to goal memory
```

## Implemented path

The `web/` application currently implements:

1. a session inbox with one clearly labeled synthetic session;
2. evidence intake showing independent plan, SpeedCoach, mobile, environment, and session-context sources;
3. a session review with work intervals derived from the selected plan and analysis;
4. metric-level source selection through progressive disclosure;
5. one analysis-requested human checkpoint that may remain unknown;
6. a coach-facing briefing with findings and evidence references;
7. an explicit approval action before an in-memory goal update.

The hosted UI replays committed public case 002 and never accesses evaluator ground truth. During local development it can connect to the task-level product service, upload the core plan and SpeedCoach sources plus any optional mobile, environment, or context evidence, receive validation/normalization metadata, and prepare a compact agent input. When live mode is explicitly enabled, the page executes the prepared bundle, adapts the verified result, completes its server-owned human checkpoint, produces a bundle-specific briefing, and proposes an approval-gated memory update. Uploaded files with different bytes are never allowed to inherit the committed answer. Titles, intervals, targets, deviations, source labels, clocks, environmental absence, checkpoint copy, and memory copy come from the selected bundle rather than case-002 constants.

## Evidence boundaries

The frontend must not:

- choose trusted metrics from raw sensors;
- calculate final plan compliance;
- turn temporal environment association into causal attribution;
- treat coach confirmation as telemetry;
- infer technique, synchronization, physiology, improvement, or regression from unsupported data;
- approve memory automatically;
- show private routes, identities, devices, or health data.

The current implementation therefore keeps work interval five as the material SPM deviation, rejects mobile SPM, uses SpeedCoach for distance and SPM, allows mobile route corroboration, and describes the wind shift only as time-aligned context.

## Product and evaluation separation

Coach navigation contains only Sessions and Goal memory. Baseline comparisons, fixtures, grader scores, run trajectories, and replay controls remain repository or terminal evidence for the hackathon submission.

## Task-level API

The local application service exposes:

```text
POST /api/sources
GET  /api/sources/:id
POST /api/source-bundles/prepare
POST /api/source-bundles/:id/execute
GET  /api/runtime/costs
POST /api/investigations
GET  /api/investigations/:id
POST /api/checkpoints/:id/answers
POST /api/briefings/:id/approve
GET  /api/goals/:id
```

`POST /api/sources` accepts one Base64-encoded typed file and returns metadata only: source id, kind, original name, detected format, SHA-256 hash, byte size, and a versioned telemetry-normalization report when applicable. It accepts at most 10 MiB per source, rejects path-bearing names, validates plan and environment schemas, validates minimum context fields, and normalizes canonical telemetry, SpeedCoach vendor, and WAKE mobile sensor CSV formats. `GET /api/sources/:id` returns the same safe metadata without raw or normalized rows.

`POST /api/source-bundles/prepare` requires exactly one plan and one SpeedCoach source and accepts at most one mobile, environment, and context source. It builds a deterministic, schema-validated compact summary; records source hashes and quality; computes cross-source findings only when the necessary optional evidence exists; preserves every unavailable capability as an evidence gap; retains the full summary in process memory; and returns safe preparation metadata including source coverage. It never calls the agent and explicitly returns `agent_called: false`.

`POST /api/source-bundles/:id/execute` accepts only `mode: live`, exists only when the local service starts with `--allow-live`, requires `OPENAI_API_KEY`, and requires `authorized_cost_usd` at or above the configured operational threshold. That value permits the run to start; it is not a provider billing cap. The endpoint supplies the bounded runner with the prepared summary and normalized files in an isolated temporary directory, validates the returned analysis schema and case identity, and records the result in process memory. Repeating the same execution in that process returns the recorded result rather than issuing another paid call or duplicating the cost ledger. Its response includes a compact review bundle; process-local investigation, checkpoint, and goal identifiers; and observed token usage, runtime, approximate cost, authorization, and overrun status. It excludes input hashes and time-series windows. `GET /api/runtime/costs` aggregates each new execution once for the lifetime of the process. `HttpWakeClient.analyzeSourceBundle` implements the two-step prepare/execute call, refuses non-live mode or missing cost authorization before making a request, and carries those identifiers and observed cost into the page's review transition.

`POST /api/investigations` accepts either the fixed public case id or the exact five-source public replay bundle. Source-based replay succeeds only when those five uploaded byte sequences exactly match public case 002. Progressive two-to-five-source bundles use the separate prepare/execute path and cannot inherit replay output. Preparation of a changed bundle does not authorize it to spend API budget. The service—not the browser—owns replay/live selection, checkpoints, and approval. All source bytes, normalized rows, prepared summaries, workflow state, and cost aggregates remain process-local. A future hosted service must add authentication, durable persistence, club tenancy, and durable accounting before accepting private club data.

## Acceptance boundary

The current slice is accepted when its Python and JavaScript behavioral tests, lint, production build, and dependency audit pass; all displayed replay data is synthetic; uncertainty is visible; and a memory session appears only after coach approval. Generic new-bundle checkpoint/briefing transitions and page invocation are implemented and tested. Durable storage, authentication, club tenancy, hosted private uploads, and exactly-once execution remain separate work.
