# Five-minute WAKE product story

**Status:** product-first draft; owner QA and final rehearsal remain

Generation-ready ElevenLabs copy is separated into seven clips in
[`submission/video/VOICEOVER_ELEVENLABS_V3.md`](../submission/video/VOICEOVER_ELEVENLABS_V3.md).

**Primary audience: coaches and athletes.** The judges should first understand
why WAKE matters inside a rowing club. The technical material exists to prove
that the visible product is credible, not to become the main character.

- **Product story: 85%** — people, daily rowing work, decisions, and continuity.
- **Technical proof: 15%** — measured comparison, one failure, and reproduction.

The architecture, schemas, trajectories, tests, and exact commands remain in the repository.
The video only exposes the minimum technical evidence needed to support the
product claim.

## Story in one sentence

WAKE helps a coach understand what happened across athletes, crews, boats, and
training days without pretending that incomplete evidence is certainty.

## Before recording

1. Complete the sequential owner QA in `docs/OWNER_QA_GUIDE.md` and fix only
   comprehension or functional blockers that affect this route.
2. Run `./scripts/reproduce_submission.sh --verify-only` once.
3. Start the no-cost replay with `./scripts/start_dashboard.sh`.
4. Open `http://localhost:3000/` at 1280 × 800 or larger and reset the second
   training period if it is already loaded.
5. Close unrelated tabs and notifications. Keep the cursor still while speaking
   and use it only to direct attention.
6. Do not show `.env`, private inputs, raw GPS, evaluator ground truth, or real
   athlete identity.

## Presentation rules

- Speak as a rower explaining a real club problem, not as an engineer reading a
  system diagram.
- Show a consequence before explaining the mechanism behind it.
- Do not narrate every card, status, or number on screen.
- Use `WAKE found`, `WAKE still needs to know`, and `the coach decides` as the
  recurring language.
- Mention implementation details only when they establish trust or satisfy the
  hackathon evidence requirements.
- Never claim that WAKE replaces a coach, diagnoses an athlete, evaluates
  visible technique, or proves why a performance changed.

## Timed route and narration

### 00:00–00:35 — The human problem and simple baseline

**Screen:** Begin on Sessions / club overview. If useful, start with a very
short title card: `One coach. Many athletes. Fragmented evidence.`

**Say:**

> In a rowing club, the plan may arrive through WhatsApp. The SpeedCoach file
> usually stays with the athlete. Another phone may record the route. The coach
> knows the crew and the conditions, but cannot follow every boat every day.
> A spreadsheet organizes the files, and a simple baseline can ask GPT to
> summarize one session. Neither one preserves the questions, relationships,
> and decisions that accumulate across the club. That is the problem WAKE was
> built to solve.

**Show, do not explain:** the 52 recorded activities, 16 athletes, 10 crews,
and the coach-attention area.

### 00:35–01:05 — Start with what needs attention

**Screen:** Sessions / club pulse, then Harbor Men 2x.

**Say:**

> WAKE begins at club scale. The coach sees which sessions were reconstructed,
> which crews went out, which records need a source, and which questions need a
> person. Here, Harbor Men 2x is connected to its physical boat, lineup, and
> outings. Missing training is shown as something to investigate, not as a
> judgment about commitment, fitness, or injury.

Open the crew and point briefly to its athletes and boat. Do not read all the
statistics.

### 01:05–02:00 — One realistic session, from evidence to useful review

**Screen:** Open the investigated six-by-one-kilometre session. Briefly show the
upload/source coverage, then move to the decision-first review.

**Say:**

> Now the coach opens one real rowing question: did the crew execute the six
> one-kilometre pieces at the prescribed stroke rates? The training plan and
> SpeedCoach are enough to begin. Mobile telemetry, weather, and human context
> can improve the review when they exist, but they are not mandatory.
>
> WAKE reconstructs the six work pieces and finds that most followed the plan,
> while one interval needs attention. It trusts the SpeedCoach for stroke rate,
> rejects the phone's zero-only stroke-rate signal, and can still use the phone
> for route or timing support. The wind changed during the row, but WAKE does
> not call that the cause of the result.

**Show:** what matched, what needs attention, what remains unknown, selected
metric sources, and the material SPM deviation. Let the screen carry the
details; do not describe parsers, schemas, or tool names.

### 02:00–02:35 — Athlete and coach complete different parts of the truth

**Screen:** Human checkpoint, answer provenance, briefing, and memory approval.

**Say:**

> Devices cannot tell us whether the resistance band was removed after the
> third repetition. That question belongs to the athlete or to someone who
> directly observed the session. WAKE records who answered, who entered the
> answer, and why that person has authority to say it. The answer adds context;
> it never rewrites the telemetry. The coach reviews the briefing, and only an
> explicit approval turns it into club memory.

This is the emotional center of the demo: WAKE connects human expertise with
device evidence without confusing the two.

### 02:35–03:25 — The value appears when training keeps arriving

**Screen:** Return to Sessions, select **Load 2-week package**, then open Lucas
and Saved WAKE club memory.

**Say:**

> One session is manageable. The real problem appears when another two weeks
> arrive. WAKE now connects 102 activities for the same 16 athletes and 10
> crews. It can distinguish comparable progress, slower comparable work,
> stable execution, weather-confounded sessions, missing participation, and
> cases that simply cannot be compared yet.
>
> For Lucas, Training Days connect crew outings, solo rows, and Concept2 work
> without adding indoor metres to water distance as if they were the same
> thing. At club level, the saved briefing gives the coach priorities and
> focused questions. It does not invent a performance trend just because more
> data exists. Reopening this verified memory costs US$0.00.

**Show:** the increase from 52 to 102, `NOT_ESTABLISHED`, Lucas's modality
history, then the three priorities and human/source questions. Avoid reading
all six comparison categories aloud.

### 03:25–03:55 — Training history reaches the regatta without inventing cause

**Screen:** Competition Review, then one boat report and the unclassified
entry.

**Say:**

> Training eventually meets competition. Competition Review connects the same
> athletes, exact crew snapshot, physical boat, shared outings, and full race
> field. A coach can review the path to the regatta and the result together.
> WAKE still does not claim that one workout or lineup caused the finish, and it
> does not select crews automatically. When a result is missing, it asks for
> context instead of inventing one.

### 03:55–04:25 — Prove that this is more than a polished dashboard

**Screen:** Evaluation.

**Say:**

> We tested the workflow against the same simple baseline on ten frozen cases.
> The direct GPT baseline scored 49.00 out of 100; WAKE scored 83.76. Every case
> improved overall, while environmental interpretation regressed from 80 to 76
> percent, and we kept that limitation visible. This demonstrates a stronger
> evidence workflow on these fixed cases. It is not a comparison with a human
> coach and not proof of athletic improvement.

Show the two large scores and the environmental regression. Do not open schema,
token, or trajectory detail during this segment.

### 04:25–04:50 — Show how failure improved the product

**Screen:** Improvement Changelog summary or the corresponding evaluation
block.

**Say:**

> The most useful change came from a failure. Early WAKE treated reconstructed
> distance as proof that the prescribed distance was completed. We removed that
> behavior, wrote a failing test, changed the evidence boundary, and reran the
> fixed evaluation. We also preserved a longitudinal experiment that showed no
> quality gain. Our history includes what did not work, not only the wins.

The phrase **removed experiment** should appear on screen or in a caption so the
submission requirement is unmistakable.

### 04:50–05:00 — Close on the user value

**Screen:** Return to the strongest club-memory or coach-priority screen, with a
small reproduction caption.

**Say:**

> Every row leaves a wake. WAKE turns fragmented training into memory a coach
> and athlete can use together.

## Optional on-screen captions

Use these only when the corresponding value is visible:

- `One coach cannot watch every boat.`
- `Evidence first. Questions stay questions.`
- `Athlete input + coach review + device evidence.`
- `52 → 102 activities without losing the history.`
- `Water, crew, solo, and Concept2 remain connected — not conflated.`
- `Training context reaches competition; causation is not invented.`
- `Fixed-case evaluation: WAKE 83.76 | simple baseline 49.00.`
- `One regression preserved. One failed experiment removed.`
- `Every row leaves a wake.`

## Recording acceptance checklist

- The final edit is no longer than five minutes.
- The simple baseline appears before the WAKE solution.
- The first minute is understandable without AI or software vocabulary.
- One realistic path runs from supplied evidence to human checkpoint and saved
  memory.
- Coach and athlete have distinct, complementary responsibilities.
- SpeedCoach is core; mobile, weather, and context are clearly optional
  enhancers.
- The 102 activities, 16 athletes, 10 crews, Lucas Training Days, Concept2, and
  Competition Review are visible.
- The 83.76 and 49.00 values and environmental regression are readable.
- One failure and one removed experiment are named.
- Architecture is not narrated beyond what is needed to establish credibility.
- Costs are observed values or replay values, never described as provider caps.
- No private file, credential, raw GPS location, or real athlete identity is
  visible.
- The ending returns to coach/athlete value rather than finishing on a terminal
  or technical document.

## Material deliberately left to the repository

The video does not need to walk through the JSON schemas, metric-level trust
contract, deterministic parsers, agent loop, verifier implementation, TDD
suite, saved trajectories, token accounting, or clean-environment commands.
Those remain essential judging evidence in the source code and documentation;
links can appear in the submission description and final reproduction caption.
