# WAKE Product Interface Contract

**Status:** accepted replay with tested local source intake and bundle preparation

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
3. a session review with six reconstructed work intervals;
4. metric-level source selection through progressive disclosure;
5. one resistance-band checkpoint that may remain unknown;
6. a coach-facing briefing with findings and evidence references;
7. an explicit approval action before an in-memory goal update.

The hosted UI replays committed public case 002 and never accesses evaluator ground truth. During local development it can connect to the task-level product service, upload a complete typed source bundle, receive validation/normalization metadata, and prepare a compact agent input. The service may replay the committed case or invoke the bounded agent for its existing case-level live path when explicitly enabled. Uploaded files with different bytes are never allowed to inherit the committed answer. New-bundle execution and durable persistence are not implemented.

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
POST /api/investigations
GET  /api/investigations/:id
POST /api/checkpoints/:id/answers
POST /api/briefings/:id/approve
GET  /api/goals/:id
```

`POST /api/sources` accepts one Base64-encoded typed file and returns metadata only: source id, kind, original name, detected format, SHA-256 hash, byte size, and a versioned telemetry-normalization report when applicable. It accepts at most 10 MiB per source, rejects path-bearing names, validates plan and environment schemas, validates minimum context fields, and normalizes canonical telemetry, SpeedCoach vendor, and WAKE mobile sensor CSV formats. `GET /api/sources/:id` returns the same safe metadata without raw or normalized rows.

`POST /api/source-bundles/prepare` accepts exactly one source of each type. It builds a deterministic, schema-validated compact summary; records source hashes and quality; computes compatible clock offset, distance conflict, and bidirectional route overlap; projects wind only when route heading is known; preserves human-only evidence gaps; retains the full summary in process memory; and returns only safe preparation metadata. It never calls the agent and explicitly returns `agent_called: false`.

`POST /api/investigations` accepts either the fixed public case id or five source ids. Source-based replay succeeds only when the five uploaded byte sequences exactly match public case 002. Preparation of a changed bundle does not authorize it to inherit replay output or spend API budget. The service—not the browser—owns replay/live selection, checkpoints, and approval. All source bytes, normalized rows, prepared summaries, and workflow state remain process-local. A future hosted service must add authentication, durable persistence, club tenancy, and a tested prepared-bundle live runner before accepting private club data.

## Acceptance boundary

The current slice is accepted when its Python and JavaScript behavioral tests, lint, production build, and dependency audit pass; all displayed data is synthetic; uncertainty is visible; and a memory session appears only after coach approval. New-bundle live execution and durable storage require separate TDD experiments.
