# Product Brief

## Working identity

**WAKE - Agentic Rowing Intelligence**
**Tagline:** Every row leaves a wake.

## Intended users

WAKE is initially designed for:

- coaches who prescribe training but cannot follow every athlete or boat on the water;
- athletes who train across different boats, crews, indoor machines, and schedules;
- rowing clubs that need continuity across daily sessions, changing lineups, and quarterly competition goals.

The initial environment is an active but non-elite rowing club. Athletes care deeply about progression and competition but do not live exclusively for the sport. Coaches can understand a single athlete from a good dashboard, but the meaningful context generated across many athletes, sessions, boats, and conditions becomes too expensive to reconstruct repeatedly.

## Current bottleneck

The information required to understand a rowing session is fragmented:

- the planned workout may be an Excel image sent through WhatsApp;
- SpeedCoach and mobile applications export separate telemetry;
- recording clocks and start/stop behavior do not perfectly match;
- boat category, physical boat, crew, seat, side, route, and training intent may not be recorded;
- wind, gusts, temperature, waves, and route direction affect interpretation;
- coach observations about balance, hands, blade transitions, and synchronization remain verbal;
- sessions disappear from working memory within days or weeks.

This produces a longitudinal blind spot. The problem is not merely registering workouts; it is recovering enough trustworthy context to understand what happened, what can be compared, and what should be investigated next.

## Agentic value

A conventional dashboard waits for a human to find and correlate signals. WAKE should instead:

1. recognize and group evidence belonging to the same session;
2. align partially overlapping recordings;
3. use deterministic tools to extract compact features and segments;
4. decide which source is trustworthy for each metric;
5. detect contradictions and insufficient evidence;
6. ask the smallest useful set of follow-up questions;
7. produce a coach-reviewable briefing with claim-level provenance;
8. preserve confirmed context as memory for later sessions and goals.

## Product layers

### Daily Intelligence

Reconstruct and verify one session: plan, actual execution, source quality, environmental context, deviations, uncertainty, and follow-up questions.

### Team and Crew Memory

Preserve which athletes rowed together, in which seats and boat, under which conditions, and what observations were confirmed by athlete or coach.

### Goal Readiness

Relate recent work to an explicit goal such as a 2 km race, 500 m novice event, technique block, attendance target, or crew-selection checkpoint. A regatta is one goal type, not the product boundary.

### Rowing Passport

Give athletes a meaningful history of distance, progress, races, results, boats, and people they have rowed with. This is a long-term product layer, not required to be complete in the weekend demo.

## Weekend demo slice

The preferred demonstration is one self-contained investigation:

1. receive a planned session plus paired SpeedCoach and mobile exports;
2. identify or confirm that the recordings represent the same outing despite timing differences;
3. extract and reconcile distance, speed/pace, SPM, route, intervals, and sensor quality when available;
4. request missing boat, crew, intent, and perceived-effort context;
5. compare planned versus performed without inventing technique observations;
6. issue a verified briefing and update a small longitudinal history;
7. show how that history changes a goal-readiness conclusion.

Synthetic history may be used for repeatable evaluation. Approved anonymized real sessions may be used in the private demonstration, but public fixtures must not expose private GPS or identities.

## Success definition

A coach should receive a more complete, evidence-backed, and actionable reconstruction than a reasonable simple baseline while spending less manual effort. The primary metric and scoring rubric must be fixed before final implementation and applied to the same cases for baseline and agent.

## Non-goals for the hackathon

- Reliable visual technique assessment without video evidence.
- Medical or injury guidance.
- Fully autonomous training prescriptions or crew selection.
- Replacing dedicated rowing hardware.
- Building every historical dashboard and social feature.
- Claiming Olympic-level prediction from a small dataset.

## Candidate hot take

> Multi-sensor intelligence is not about averaging every number. It is about knowing which sensor deserves to be trusted for each claim - and knowing when no sensor is good enough.
