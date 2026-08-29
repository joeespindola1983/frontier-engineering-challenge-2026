# WAKE Repository Instructions

## Project mission

Build **WAKE - Agentic Rowing Intelligence** for the micro1 Agentic Workflows Hackathon 2026. WAKE helps rowing coaches and athletes reconstruct, verify, and learn from daily training that is currently fragmented across plans, telemetry, environment, equipment, crew composition, and human observations.

The core value is not another dashboard. The agent should actively investigate sessions, request missing context, reconcile sources, expose uncertainty, and preserve useful rowing memory across time.

## Start every task here

Before proposing or changing implementation:

1. Read `README.md`, `docs/WORKING_CONTEXT.md`, and every file in `docs/` relevant to the task.
2. Inspect `git status` and preserve unrelated user work.
3. Check `docs/PREEXISTING_WORK.md` before describing something as hackathon work.
4. Check `IMPROVEMENT_CHANGELOG.md` before changing the baseline, evaluation, prompts, tools, or orchestration.
5. Never infer that a planned feature is implemented. Keep status labels honest.

## Stable product decisions

- Product name: **WAKE - Agentic Rowing Intelligence**.
- Tagline: **Every row leaves a wake.**
- Primary users: coaches and athletes in active rowing clubs, especially non-elite environments where training context is operationally chaotic.
- Regattas are goals and high-value evaluation milestones, not the scope or name of the product.
- Product layers: Daily Intelligence, Team and Crew Memory, Goal Readiness, and Rowing Passport.
- Initial evidence sources: planned workouts, SpeedCoach exports, mobile telemetry, user-supplied session context, and environmental data when available.
- Central technical insight: multi-sensor intelligence is not about averaging every number; it is about knowing which source deserves trust for each claim.

## Scope discipline

The weekend demo must prioritize one polished, reproducible workflow over a broad but shallow product. Start with a single orchestrating agent plus deterministic tools and a verification step. Add specialized agents only when evaluation evidence shows that separation improves the result.

Do not position WAKE as:

- a replacement for a qualified rowing coach;
- an automatic selector of athletes or crews;
- a medical, injury, or physiological diagnosis system;
- a reliable evaluator of visible rowing technique without appropriate video or biomechanical evidence;
- a replacement for SpeedCoach hardware during this hackathon.

## Data and privacy

- Never commit raw private GPS, device identifiers, credentials, health data, or identifiable athlete records.
- Keep private inputs under ignored paths such as `private-data/`.
- Commit only public, synthetic, or explicitly anonymized fixtures.
- Preserve provenance and an evidence reference for every claim shown to users.
- Use human review for consequential coaching or crew decisions.

## Engineering and evidence rules

- Keep user-facing artifacts, code, prompts, and submission materials in English.
- Conversation with the project owner may be in Portuguese.
- Process high-volume sensor rows with deterministic parsers and feature extraction; do not send raw telemetry dumps directly to an LLM.
- Treat recording start/end mismatch as an alignment problem, not as proof that sessions are unrelated.
- Assign trust at metric level. For example, GPS distance and SPM may come from different sources.
- Separate observed facts, derived metrics, user-provided context, hypotheses, and recommendations in schemas and output.
- Capture representative trajectories as structured events: instructions/version, inputs, tool calls and responses, evidence references, retries, checkpoints, output, runtime, and approximate cost. Do not store private chain-of-thought.
- Define expected behavior and the primary metric before optimizing against it.
- Develop deterministic behavior with test-driven development: add a failing test, implement the smallest change that passes, then refactor while the suite stays green.
- Add a regression test before fixing a reproducible deterministic bug.
- Evaluate model and agent behavior with fixed cases, schemas, and rubrics; do not use exact prose snapshots as a substitute for behavioral evaluation.
- Run the same fixed cases against the baseline and final solution.
- Add or update tests whenever deterministic behavior changes.
- Link every meaningful experiment to evidence in `IMPROVEMENT_CHANGELOG.md`, including experiments that are later removed.
- Prefer small, meaningful commits that leave the repository runnable or clearly labeled as documentation-only.

## Pre-existing boundary

A separate mobile rowing application existed before the hackathon. It captured mobile telemetry and experimented with SPM detection. Do not modify or silently copy that application into this repository. Reuse only approved exports or components with clear attribution, license review, and documentation of what existed before the competition.

## Current phase

The project is ready for the first controlled model comparison. The primary metric, first schema versions, 16-case registry, two public fixtures, permanent TDD policy, compact baseline bundle, comparable baseline/agent prompts, Python/uv evaluation runtime, GPT-5.6 Terra medium configuration, four deterministic investigation tools, bounded single-agent loop, verifier, observable trajectory format, and deterministic grader v1 are accepted. No paid model result, database, persistent memory, UI framework, or product deployment target has been accepted yet. Record those choices in `docs/DECISIONS.md` before treating them as stable.
