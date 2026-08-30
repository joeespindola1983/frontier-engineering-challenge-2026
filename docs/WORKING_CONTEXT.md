# Working Context and Discovery History

**Last updated:** 2026-08-29
**Status:** living handoff document, not a stable specification

## Purpose

This document preserves the useful context developed during the initial product conversation so a new collaborator or Codex task can continue without receiving the full chat history.

It is intentionally more narrative than `AGENTS.md`:

- `AGENTS.md` contains stable working instructions.
- `DECISIONS.md` is authoritative for accepted decisions.
- `PREEXISTING_WORK.md` is authoritative for the competition boundary.
- `IMPROVEMENT_CHANGELOG.md` is authoritative for experiments and measured results.
- This file preserves motivations, domain observations, candidate ideas, data findings, and unresolved questions.

When this file conflicts with a later accepted decision or measured result, the later source wins. Update this handoff rather than allowing stale context to survive silently.

## How the project arrived at rowing

The hackathon problem was open-ended: choose a meaningful task and demonstrate that agents improve how it is handled. Several domains were considered:

- biometric liveness and identity-document validation;
- astrophotography using accessible open-source images;
- software-development and mobile-development workflows;
- rowing training, telemetry, crews, and progression.

Biometrics offered realistic synthetic cases but risked becoming a familiar document-review workflow. Astrophotography had accessible data but a less direct user-value story for the judges. Software development was viable but crowded.

Rowing was selected because the project owner is a rower with direct access to athletes and coaches who participate in regional, national, and international regattas. The domain combines firsthand knowledge, representative telemetry, overlooked operational pain, technical depth, and an emotionally meaningful long-term history.

## Domain setting

The initial setting is not a fully funded Olympic program. It is an active rowing club where people train and compete seriously but also have jobs, families, and other obligations.

Important characteristics:

- Athletes may train almost daily, especially before a regatta.
- Regional regattas may occur approximately every quarter and become major checkpoints.
- A coach cannot accompany every athlete or boat on the water.
- Training plans commonly arrive as an Excel table or image through WhatsApp.
- An athlete may row alone, change physical boats, join different crews, occupy different seats, train indoors, and do strength work.
- Coaches and athletes tend to remember the latest session or regatta but lose detailed context after one or two weeks.
- A coach can inspect one good dashboard, but repeatedly correlating every athlete, boat, crew, condition, and sensor is the real scaling problem.

The project is therefore aimed at a chaotic longitudinal environment, not only elite performance optimization.

## User pain described during discovery

### Coaches lack visibility into complete training

The coach may prescribe a workout without observing its execution. The athlete may complete it incorrectly, partially, or under conditions that make a direct comparison misleading. Neither person receives a reliable reconstruction automatically.

The coach may not know:

- which days the athlete actually trained;
- total distance and workload;
- whether the requested segments and stroke rates were followed;
- which boat and crew were used;
- what conditions affected the result;
- whether a bad number reflects performance, environment, equipment, or sensor failure.

### Context disappears

Daily rowing generates details that are rarely stored together: training intent, boat, crew, seat, side, route, weather, coach observations, perceived effort, and device evidence. Without continuity, planning becomes anchored to current numbers and the latest race rather than the full season.

### Crew and boat combinations matter

Rowing includes individual and collective boats with different configurations. Weight, height, experience, seat, timing, and physical equipment can influence a crew. Discovery produced examples involving 2x and 4x boats, but these examples must be validated by a qualified coach before they become product rules.

For a 4x, synchronization propagates through the crew from the athlete setting the rhythm. Differences in hand height, timing, and movement can affect balance and cause blades to drag or catch. The current datasets cannot directly prove these visible technique failures.

### Athletes also want memory, not only optimization

The project owner would like to recover:

- every regatta and finishing position;
- total kilometers rowed;
- every athlete they have shared a boat with;
- progress across seasons, boats, and crews.

This led to the Rowing Passport idea: a personal and social history that preserves why people love rowing, not merely a performance score.

## Rowing knowledge relevant to the workflow

Rowing performance is often discussed through stroke rate (SPM), speed or pace, force/power, and their relationship. Interpretation is not reducible to “more force” or “more strokes.” It can be affected by:

- wind direction and strength;
- gusts;
- waves or lateral chop;
- route heading and turns;
- current where relevant;
- boat category and physical equipment;
- crew composition and synchronization;
- athlete weight, height, experience, and longitudinal changes;
- training intent and race distance.

Direction is especially important in a race because leaving alignment can cause a collision, a lane violation, or a penalty. During casual training, athletes may focus more on technique than strict directional performance.

Common race distances mentioned during discovery include:

- 2,000 m for senior official races;
- 500 m for some novice races;
- 1,000 m for some other categories.

Before a regatta, important coaching decisions include selecting crews and deciding which athletes fit which event or boat. The exact three-week planning process still needs a coach interview.

## What numeric telemetry cannot currently see

A coach can observe technique details that the proposed initial workflow cannot safely infer from ordinary phone and SpeedCoach data:

- hand position and hand height;
- body position and balance;
- blade extraction and transition;
- whether a blade dragged, buried, or stopped the boat;
- exact synchronization between athletes;
- how a shorter and taller athlete adapted their stroke length;
- causal explanations for a technical failure.

The product should allow a coach to attach concise observations to a session. These become human-provided evidence, not sensor-derived facts. A later video or specialized biomechanical system could extend this boundary, but it is not part of the weekend demo.

## Existing data and application knowledge

### SpeedCoach and Concept2

The project owner has approximately ten SpeedCoach workouts and can obtain some Concept2 indoor sessions. SpeedCoach exports may include timestamps, GPS, distance, speed/pace, and SPM. They generally do not preserve all rowing context, such as the planned workout, boat, crew, athlete identity, seats, or coach observation.

### Pre-existing mobile application

Before the hackathon, the project owner developed iOS and Android rowing capture functionality with GPS and phone sensors. The long-term idea was to explore whether a mobile app could complement or eventually replace parts of the SpeedCoach workflow.

GPS speed and distance were more reliable than the mobile SPM calculation. SPM was difficult because:

- the phone could be attached to a hook and mini tripod, placed under the sliding seat, or mounted in another position;
- waves and lateral movement could resemble a stroke;
- unsynchronized oars could create extra motion;
- phone hardware and sampling behavior varied;
- an algorithm failure could leave the detector at zero without recovering;
- SpeedCoach is mounted in a position better suited to detecting rowing motion.

This is why mobile and SpeedCoach measurements should not be treated as interchangeable sources.

### Representative session combinations found so far

The existing private workspace contains several potentially useful combinations. These descriptions deliberately omit private paths, device identifiers, and GPS coordinates:

- An early-April outing with two mobile captures starting only a few seconds apart, watch-related fields on one capture, and no useful GPS. This may become a difficult missing-evidence case.
- A following-day cross-platform pair with iOS and Android captures starting within a fraction of a second, useful GPS, and approximately the same total distance. This is the strongest candidate for testing cross-device reconciliation.
- A mid-April mobile sensor export paired with a SpeedCoach export and useful GPS, but with mobile SPM failure. This is a strong candidate for metric-level source trust.
- Older deleted session exports appear recoverable from the pre-existing application's Git history, but no recovery should be described as hackathon evidence until the data is restored, reviewed, and approved.

Raw data remains outside the public repository. Any public case must be minimized, anonymized, or synthesized while preserving the failure mode being tested.

### Private corpus audit and selected hero case

A read-only audit found a useful but uneven corpus: 18 SpeedCoach CSVs (17 unique), 39 mobile telemetry files (38 unique), 32 unique mobile workout summaries, and 23 watch CSVs. Thirty-seven unique mobile telemetry files contain GPS. Raw mobile SPM is present in only three sessions, and the available watch files contain no positive heart-rate or watch-SPM values. No Concept2 export was found in the audited folder. ZIP archives, generated reports, and databases are treated as derived packaging rather than primary evidence.

The selected first case is a three-device outing with SpeedCoach, iOS, and Android recordings. A human domain expert confirmed that all three represent one men's double scull (`2x`) session with two athletes. The evidence itself is deliberately contradictory:

- mobile start clocks are almost one hour later than SpeedCoach;
- route-overlap p95 is below 5 m for both phone-to-SpeedCoach comparisons;
- SpeedCoach reports 3,915.3 m, 25:25.8, 22.0 SPM, and 549 strokes;
- raw phone GPS distance is close to 4 km, while mobile summaries claim substantially longer distances;
- neither raw mobile sensor stream contains SPM values;
- iOS gyroscope data is present, while Android gyroscope values are zero;
- iOS reports `SINGLE_SCULL` and Android reports `OC1`, although the confirmed boat is `2x`;
- mobile metadata claims watch availability, but no watch evidence is supplied in the public case;
- no planned workout or coach technique observation exists for the outing.

The fixture is published at `data/fixtures/case-001-misaligned-double-scull`. Its coordinates, dates, serials, models, and workout IDs are transformed, and high-frequency phone rows are minimized. The private source manifest remains ignored. `scripts/verify_hero_fixture.py` provides the public integrity and behavior check.

### Coach plans and derived-synthetic evaluation

A real multi-week competition plan and ten daily WhatsApp crops were reviewed. The daily images reproduce individual dates from the master plan, showing that the coach maintains a longer periodization artifact while athletes consume a daily slice. The plans include distance- and duration-based work, SPM progressions, recovery ranges, resistance equipment, starts, race preparation, mobility, strength, and alternative prescriptions such as minimum/maximum repetitions.

The plan dates do not match the private April telemetry and must never be represented as the corresponding prescription. The accepted use is to preserve only anonymized plan patterns while generating entirely synthetic executions with exact ground truth.

Evaluation specification v1.0 now defines a 100-point rubric and a 16-case registry. Case 002 implements a six-by-one-kilometer prescription with a wind shift during work interval four, an actual SPM deviation in work interval five, a 37-second mobile clock offset, 1.2% mobile distance bias, and mobile SPM stuck at zero. The case requires abstention about resistance-band use, visible technique, and crew synchronization.

The project owner confirmed that `voga` in these plans means target stroke rate in SPM and that B0-B7/E1-E7 are standardized rowing training zones rather than coach-specific labels. Exact physiological or effort boundaries remain intentionally undefined until an authoritative mapping is recorded.

## Time alignment insight

Starting and stopping multiple devices at exactly the same time is unrealistic. Differences may be seconds or minutes, and a user may forget to stop one recording for much longer.

Exact matching timestamps are useful but must not be a hard requirement. Candidate alignment evidence includes:

- approximate clock window;
- GPS-route overlap;
- speed or pace pattern correlation;
- movement start and end;
- cumulative distance;
- turns and pauses;
- segment duration and shape.

The alignment component should report the overlapping window, estimated offset, quality score, and reasons for the match. It should preserve unmatched periods instead of silently trimming them.

## Product vision formed during discovery

The phrase “data science for rowing” captured the direction, but the product should not become a dense analytics dashboard. A human should not be required to cross-reference every athlete, boat, session, sensor, weather condition, and body measurement manually.

WAKE is envisioned as small pieces of focused intelligence working over an evidence model:

- reconstruct daily sessions;
- compare plan and execution;
- understand which sessions are actually comparable;
- cross-reference athletes, crews, boats, and conditions;
- preserve confirmed memory;
- explain progression toward goals;
- surface only the few findings and questions that deserve attention.

Potential long-term signals include athlete weight and height over time, indoor power, strength training, environment, boat combinations, and crew compatibility. These are research directions, not current product claims.

The four product layers are:

1. **Daily Intelligence** - reconstruct and verify one session.
2. **Team and Crew Memory** - preserve athlete, crew, seat, boat, and coach context.
3. **Goal Readiness** - relate current work to a race, technique block, attendance objective, or another goal.
4. **Rowing Passport** - preserve the athlete's personal progression and rowing history.

The navigation concepts discussed were Today, Sessions, Athletes, Crews, Boats, Progress, Goals, and Rowing Passport. They are product concepts, not a committed UI scope.

## Why agents are necessary

The differentiator must not be “an LLM reads a spreadsheet faster.” A capable dashboard and a coach can already analyze many isolated sessions.

The agent earns its place by managing an incomplete and changing investigation:

1. determine which files and records may belong together;
2. call deterministic tools to inspect compact evidence;
3. detect source failures and contradictions;
4. decide which metrics are supported by which sources;
5. ask targeted questions only when their answers change the conclusion;
6. distinguish facts, inferences, uncertainty, and recommendations;
7. verify every meaningful claim;
8. carry confirmed context into later sessions;
9. adapt the analysis to the athlete, crew, boat, conditions, and goal.

The current hot take is:

> Multi-sensor intelligence is not about averaging every number. It is about knowing which sensor deserves to be trusted for each claim - and knowing when no sensor is good enough.

## Candidate agent workflow

The current working flow is:

1. **Intake:** receive a plan, SpeedCoach export, mobile export, and any known athlete/boat context.
2. **Normalize:** deterministic adapters validate and convert each source.
3. **Match and align:** estimate which records describe the same outing and locate overlap.
4. **Assess trust:** score each source independently for distance, route, speed/pace, SPM, intervals, and motion.
5. **Investigate:** the agent selects tools and identifies missing information or conflicts.
6. **Ask:** request objective context such as boat, athletes, seats, intended workout, perceived effort, and coach observation.
7. **Brief:** compare planned versus performed and show claim-level evidence and uncertainty.
8. **Verify:** reject unsupported statements and require a human checkpoint for consequential conclusions.
9. **Remember:** update athlete, crew, boat, and goal history only with confirmed information.

Raw high-frequency sensor rows should not be dumped into the model context. Deterministic parsing, segmentation, alignment, and feature extraction should precede agent reasoning.

## Athlete and coach input

The athlete can answer several objective questions after training and occasional targeted descriptive questions. Fresh memory is valuable, so earlier input is preferable, but the system should not make immediate completion an absolute requirement.

The product should balance:

- asking while details are fresh;
- avoiding excessive post-workout burden;
- identifying which missing answers materially affect interpretation;
- marking late or uncertain recollections appropriately.

Coach observations should be attachable when the coach followed the session. They must remain clearly attributed human evidence.

## Weekend scope guardrail

The full vision is intentionally larger than the hackathon implementation. A strong weekend submission should demonstrate one narrow but convincing loop:

- import a planned workout and paired telemetry;
- tolerate recording misalignment;
- expose a broken or conflicting metric;
- select trustworthy evidence per metric;
- ask for missing rowing context;
- create a verified session briefing;
- update a small synthetic or anonymized longitudinal history;
- show how that evidence changes a goal-readiness conclusion.

The UI only needs enough polish to make that end-to-end execution understandable in a five-minute video.

### Implemented product-facing slice

The first web slice now follows the coach workflow rather than the hackathon evaluation workflow: session inbox, evidence intake, review, one focused human checkpoint, verified briefing, and approval-gated goal memory. The hosted version remains a clearly labeled synthetic replay of committed case 002. A local task-level HTTP service connects the same interface contract to replay or explicitly enabled live execution. Its tested process-local intake accepts five independently validated source types and returns only metadata to the browser. SpeedCoach vendor, WAKE mobile sensor, and canonical telemetry CSVs are normalized deterministically with versioned provenance and quality flags. Progressive preparation now requires only plan + SpeedCoach; mobile, environment, and context are independent enhancers whose absence becomes an explicit evidence gap. Source coverage is returned as core/enhancer and present/absent, and execution receives only the files that were actually supplied. A separate live-only endpoint executes that summary through the bounded agent with temporary normalized files and same-process idempotence. It also registers a process-local investigation so the page can continue the selected bundle through its own human confirmation, generic briefing, and explicit memory approval. The review, checkpoint, and memory transformations no longer insert case-002 work counts, deviations, wind markers, source IDs, boat labels, or resistance-band meaning into another session. Source-based replay remains restricted to the exact five-source public-bundle match. Durable storage, authentication, and tenancy remain unimplemented.

The supplied visual prototype was retained as a direction, but repository evidence changed three important details: wind is a time-aligned association rather than a causal explanation; only one reviewed session appears in memory; and coach confirmation is stored as human context without rewriting telemetry. Evaluation scores, fixture controls, and trajectories remain outside the product navigation.

## Evaluation direction

The accepted primary metric is macro-average weighted rubric score from 0 to 100 across implemented fixed cases. Its dimensions are plan interpretation, session association/alignment, segment reconstruction, metric-level source trust, deviation detection, environmental interpretation, evidence/abstention, and follow-up questions. Unsupported-claim rate, required-abstention recall, boundary error, runtime, cost, and later coach-rated usefulness remain secondary metrics.

The current 63.34 versus 38.86 comparison is an agent-versus-direct-model result, not a coach baseline and not proof of mobile value. The accepted next evaluation is a same-case evidence ablation: plan + SpeedCoach; plan + SpeedCoach + context/environment; and the full bundle with mobile. A separate small coach usability pilot may measure review time, omissions, corrections, usefulness, and confidence, but must not be described as broad human-superiority or athletic-performance evidence.

The three ground-truth-free ablation inputs are deterministically generated and frozen under `evaluation/ablation-inputs/v1/`. They preserve one synthetic base session while changing only available evidence and record content hashes and capability labels. They have now been used by the preserved official v1 run and remain unchanged for the v2 comparison.

The condition-aware runner and reporter are now implemented. The default runner creates three inspectable requests without an API call; explicit execution runs every condition and creates isolated temporary evidence directories containing only the files allowed for that condition. The reporter has no cross-condition overall score. It checks common plan/execution consistency and condition-specific behavior such as environmental abstention, noncausal association, mobile route corroboration, and broken-mobile-SPM rejection. A committed dry-run preflight and the first official live ablation result now exist.

The first official evidence-ablation run is now preserved. It used commit `d8aa3c8`, cost US$0.298604, consumed 94,427 total tokens, and ran for 92.650 seconds end to end. Core passed 7/8 applicable checks but falsely treated derived segment-boundary distance loss as a completed-distance deviation; it also required one verifier retry for evidence-less unavailable-source items. Context/environment passed 10/10, and full evidence passed 12/12 with mobile session/route corroboration and broken-mobile-SPM rejection. Cross-condition consistency therefore failed. The first reporter attempt crashed on the core deviation's null segment reference; a regression test fixed reporting without changing outputs or the frozen evaluation contract.

The v2 correction was developed with RED-GREEN cycles after preserving v1. It adds a structured `INSUFFICIENT` distance assessment to the versioned reconstruction result, exposes the same limitation in the tool description and prompt, and makes the v2 verifier reject prescribed-distance deviations based on boundary-derived segment values. The ablation runner and scorer select the workflow version explicitly. After the no-cost preflight, the official v2 repeat passed core 8/8, context/environment 10/10, full 12/12, and cross-condition consistency. It cost US$0.358676, consumed 114,338 tokens, and completed in 92.202 seconds. Every condition reported only the work-05 SPM deviation. Core and context/environment each used one bounded retry for unrelated evidence-less insufficient/unavailable items; full required no retry. This remains a one-case synthetic workflow result.

A likely evaluation will use ten or more fixed cases, including scenarios such as:

- clean paired recordings;
- delayed start or forgotten stop;
- partial overlap;
- mobile SPM stuck at zero;
- missing GPS;
- conflicting distance or pace;
- missing boat or crew context;
- environmental conditions affecting interpretation;
- a plan that was not followed;
- a request to infer technique that the evidence cannot support.

The baseline protocol is a direct model prompt over the same compact session summary without iterative tools, memory, or verification. The version 1 prompt, compact summary contract, and two-case input bundle are generated, hashed, and checked for ground-truth leakage. Comparable baseline and bounded-agent runners use Python, `uv`, the OpenAI Responses API, strict Structured Outputs, and `gpt-5.6-terra` at medium reasoning. Their safe default is a no-cost dry-run; a real call requires both `--execute` and `OPENAI_API_KEY`. A paid single-case baseline preflight exposed an API schema issue and generic grader representation gaps; it is retained but excluded from the official comparison. With deterministic grader v1.1 frozen, the official two-case result is 63.34/100 for WAKE versus 38.86/100 for the baseline at US$0.062338 incremental API cost. This is evidence for the implemented cases, not broad generalization. Future agent trajectories now record monotonic per-case runtime and future run manifests separately record end-to-end runtime and the sum of case runtimes; the historical comparison remains unchanged.

Deterministic development now follows red-green-refactor. Parsers, normalization, alignment, segmentation, metric trust, generators, schemas, and graders require behavioral or regression tests. Model output is evaluated with fixed cases, structured contracts, and the frozen rubric rather than exact prose snapshots.

## Demonstration story

A candidate five-minute narrative is:

1. Show the coach's current inputs: plan image, disconnected CSV exports, and missing context.
2. Run the simple baseline and show a plausible but incomplete or overconfident answer.
3. Run WAKE on the same case.
4. Show file matching, time alignment, metric-level trust, one focused human question, and evidence verification.
5. Show the finished coach briefing and the resulting memory/goal update.
6. Compare baseline and WAKE on the fixed evaluation.
7. Highlight the most impactful iteration and one removed experiment.

## Open domain questions

- How does the coach actually plan the final three weeks before a regatta?
- Which crew and boat decisions are most valuable to support without automating them?
- Which athlete/coach questions are essential immediately after a session?
- How should perceived effort, strength work, body weight, and height be represented responsibly?
- Which coach observations can become structured fields without losing nuance?
- Which comparisons remain meaningful across boat category, crew, route, and conditions?
- What environmental data is available historically and at sufficient resolution?

## Open product and engineering questions

- Which domain expert independently reviews each ground-truth answer before final scoring?
- Which schema revisions are justified by parser and grader implementation evidence?
- Which database and hosted runtime should replace the accepted process-local product service after the weekend?
- Is one orchestrating agent plus verifier enough, or does an evaluated failure justify another specialized agent?
- How should evidence, trajectories, cost, and runtime be packaged for judges?
- Which weather and mapping services have acceptable terms and reproducible historical data?

## Continuity protocol

At the end of a meaningful discovery or planning task:

1. add new domain observations to this file;
2. promote accepted decisions into `DECISIONS.md`;
3. record pre-existing components in `PREEXISTING_WORK.md`;
4. record actual experiments and results in `IMPROVEMENT_CHANGELOG.md`;
5. update `AGENTS.md` only when a stable working rule changes;
6. remove or revise stale hypotheses rather than accumulating contradictions.

This document may be moved to an archive before submission, but it should not be deleted until every useful decision, boundary, and learning has a stable home.
