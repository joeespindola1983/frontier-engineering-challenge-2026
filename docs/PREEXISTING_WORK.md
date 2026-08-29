# Pre-existing Work Boundary

This file distinguishes work that existed before the micro1 Agentic Workflows Hackathon from work created during the competition. It must be updated whenever an earlier component is reused.

## Existed before the competition

A separate mobile rowing application had already been developed independently of this hackathon. Its known capabilities include:

- mobile collection of GPS, speed, and distance;
- accelerometer, gyroscope, orientation, and related sensor capture;
- raw session export;
- an experimental stroke-rate/SPM detector;
- recordings produced on iOS and Android;
- some sessions recorded at approximately the same time as a SpeedCoach device.

The earlier application and its repository are not themselves hackathon output.

## Known limitations before the competition

- Mobile SPM estimation was experimental and sensitive to boat movement, waves, mounting position, device hardware, and crew synchronization.
- The detector could lose its state and remain at zero during a session.
- Mobile and SpeedCoach recordings were not reliably started or stopped together.
- Device exports did not reliably preserve the planned workout, boat type, physical boat, athletes, seats, goal, or coach observations.
- There was no agentic investigation, claim-level evidence model, cross-session memory, goal-readiness workflow, or reproducible agent evaluation.

## Hackathon work boundary

The following are candidates to be built and evaluated during the hackathon. They are not considered implemented until linked to code and evidence:

- deterministic adapters for approved SpeedCoach and mobile exports;
- recording matching and temporal alignment;
- metric-level source trust and sensor-quality assessment;
- a normalized evidence and session model;
- agent-driven missing-context investigation;
- planned-versus-performed reasoning with uncertainty;
- weather/route enrichment when evidence permits;
- athlete, crew, boat, and goal memory;
- a human-review checkpoint;
- baseline, evaluation cases, graders, trajectories, reproduction commands, and user-facing demo.

## Reuse record: first public fixture

The first public evaluation case uses exports captured before the competition by the existing mobile application and a SpeedCoach device. Only data formats and approved recordings are reused; no parser or application source code has been copied into this repository.

Created during the hackathon:

- the case selection and human-confirmed men's `2x` reference context;
- the deterministic privacy transformation;
- the minimized public fixture and its hashes;
- the evaluator-only ground truth and abstention requirements;
- the integrity, privacy, route-overlap, timing, and metric verifier.

The ignored local source manifest pins the seven private input files by SHA-256. The public repository contains no raw private export, original source path, real coordinate, real date, serial, phone model, or workout UUID.

## Reuse requirements

Before reusing any earlier code or component:

1. record its source repository and exact pre-competition commit or snapshot;
2. verify its license and any third-party terms;
3. explain what was reused without describing it as new work;
4. isolate the new integration or improvement in the hackathon repository;
5. connect new claims to hackathon evaluation evidence.

## Data boundary

Raw sessions may contain GPS routes, timestamps, device identifiers, and athlete context. They must remain outside the public repository unless explicitly approved and anonymized. Public evaluation should prefer synthetic or carefully minimized fixtures that preserve relevant failure modes without identifying people or private locations.

## Items to resolve before submission

- Record the exact pre-competition application repository and commit/snapshot.
- Inventory each real candidate session and its consent/provenance status.
- If earlier parser code is later reused, record its exact repository commit and license before copying it. The first fixture uses only exported data formats.
- Document licenses and service terms for every final dependency and external data provider.
