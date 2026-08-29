# WAKE Product Interface Contract

**Status:** accepted and implemented as a synthetic replay

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
2. evidence intake showing independent plan, SpeedCoach, mobile, and environment sources;
3. a session review with six reconstructed work intervals;
4. metric-level source selection through progressive disclosure;
5. one resistance-band checkpoint that may remain unknown;
6. a coach-facing briefing with findings and evidence references;
7. an explicit approval action before an in-memory goal update.

The hosted UI replays committed public case 002 and never accesses evaluator ground truth. During local development it can connect to the task-level product service. The service may replay the same output or invoke the bounded agent when live execution is explicitly enabled. Source upload and durable persistence are not implemented.

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
POST /api/investigations
GET  /api/investigations/:id
POST /api/checkpoints/:id/answers
POST /api/briefings/:id/approve
GET  /api/goals/:id
```

The service—not the browser—selects replay versus explicitly enabled live agent execution and owns the checkpoint and approval transition. Current state is process-local. A future hosted service must add authentication, source validation, durable persistence, and club tenancy before accepting private data.

## Acceptance boundary

The current slice is accepted when its Python and JavaScript behavioral tests, lint, production build, and dependency audit pass; all displayed data is synthetic; uncertainty is visible; and a memory session appears only after coach approval. Live source ingestion and durable storage require separate TDD experiments.
