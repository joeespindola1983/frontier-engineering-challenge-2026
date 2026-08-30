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

The expanded controlled model comparison is complete. Across ten implemented v2 cases, the bounded WAKE agent scored 83.76/100 versus 49.00/100 for the direct-call baseline using grader v1.2: +34.76 points at US$0.283344 incremental cost. Every case improved, but environmental interpretation regressed from 80% to 76%, and the single real anonymized case remains WAKE's weakest at 53.71. The historical two-case v1 result and progressive-evidence ablations remain preserved unchanged. Two authorized demo-club investigations are preserved: Bridge isolated `work-02` at 18 SPM and Atlas isolated `recovery-02` at 247 seconds for US$0.194118 combined. The reproducible two-week public batch now contains 52 isolated real-informed synthetic activity records: all 52 are data-validated and reconstructed, 51 are plan-compared, two are agent-verified, and zero are human-approved. Fourteen Concept2-shaped indoor records are athlete-owned and deterministically normalized from declared, confirmed transcription semantics. The authorized longitudinal pilot is complete: two direct-baseline and two bounded-WAKE reports all passed verification for US$0.110426 total. Both workflows passed the same non-scored capability checks, so the honest conclusion is `NO_DEMONSTRATED_QUALITY_GAIN`; WAKE used fewer tokens and cost 29.01% less, which is not presented as proof of better reasoning. A second public post-regatta package adds 50 real-informed synthetic activities for the same 16 athletes and 10 crews and demonstrates six deterministic longitudinal comparison outcomes with causation explicitly unestablished. Its combined 102-activity club screen now has one verified locally saved bounded-WAKE memory: US$0.037384, 6,322 tokens, `store: false`, and US$0.00 reopening. A clean-environment reproduction script verifies saved evidence without a key or new model call. The primary metric, versioned schemas and registries, public fixtures and verifiers, permanent TDD policy, comparable prompts, Python/uv runtime, bounded single-agent workflow, observable trajectories, coach-facing React/Vinext interface, deterministic adapters, explicit prepared-bundle and batch execution, approval-gated memory, per-execution cost authorization, restart-safe local inbox, Evaluation view, Competition Review, and post-regatta replay are accepted. Replay is the default; live execution requires explicit mode, positive finite cost authorization, and `OPENAI_API_KEY`. The authorization is a start gate, not a provider cap. Saved outputs can be reviewed and regraded offline without another model call. The results do not establish human-coach superiority, broad generalization, improved athletic performance, or durable billing control. The local state file is Git-ignored and user-restricted but not encrypted, authenticated, multi-tenant, backed up, or a production database. Record new stable choices in `docs/DECISIONS.md`.
