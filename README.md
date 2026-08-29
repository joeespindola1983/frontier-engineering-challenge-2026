# WAKE - Agentic Rowing Intelligence

> Every row leaves a wake.

WAKE is an agentic intelligence layer for rowing clubs. It turns fragmented training plans, boat and crew context, environmental conditions, and telemetry from devices such as SpeedCoach and mobile phones into evidence-backed session briefings and long-term rowing memory.

**Hackathon status:** two reproducible evaluation fixtures, a frozen rubric, versioned evidence contracts, and the baseline v1 prompt/input bundle are complete. The baseline model runner and agent workflow are not implemented yet.

## The problem

In many non-elite rowing clubs, athletes train frequently while coaches cannot follow every boat on the water. Plans may arrive through WhatsApp or spreadsheets, telemetry stays in isolated CSV exports, and essential context - boat, crew, seat, route, conditions, intent, and coach observations - disappears within days.

A dashboard can store and display this information, but it still asks a human to inspect every chart and connect every variable. WAKE investigates each session, identifies missing context, reconciles conflicting sources, and presents only claims it can support with evidence and explicit uncertainty.

## Initial demo hypothesis

The first end-to-end workflow will:

1. ingest a planned workout and paired SpeedCoach/mobile telemetry;
2. align recordings even when devices were started or stopped at different times;
3. choose which source to trust for each metric instead of averaging every sensor;
4. ask focused questions for missing rowing context;
5. produce a verified planned-versus-performed session briefing;
6. connect the session to an athlete, crew, boat, and longer-term goal history.

The regatta is an important goal and evaluation milestone, not the boundary of the product.

## Product principles

- Evidence before confidence.
- Trust is assigned per metric and claim, not per device.
- Deterministic tools process raw telemetry; the agent receives compact evidence.
- Missing information is surfaced or requested, never silently invented.
- Coaches remain responsible for consequential training and crew decisions.
- Raw GPS, device identifiers, credentials, and private athlete data stay outside the public repository.
- Every measured improvement must be reproducible against the same evaluation cases as the baseline.

## Hackathon evidence

The repository will preserve:

- a simple baseline and the final workflow;
- a fixed evaluation set, including at least one difficult case;
- an [Improvement Changelog](IMPROVEMENT_CHANGELOG.md) tied to results;
- representative agent trajectories with tool responses, retries, and human checkpoints;
- exact clean-environment commands, runtime, versions, and approximate cost;
- a five-minute end-to-end demonstration.

## Documentation

- [Product brief](docs/PRODUCT_BRIEF.md)
- [Working context and discovery history](docs/WORKING_CONTEXT.md)
- [Pre-existing work boundary](docs/PREEXISTING_WORK.md)
- [Architecture hypothesis](docs/ARCHITECTURE.md)
- [Decision log](docs/DECISIONS.md)
- [Submission requirements](docs/SUBMISSION_REQUIREMENTS.md)
- [Private dataset audit](docs/DATASET_AUDIT.md)
- [Evaluation specification](docs/EVALUATION_SPEC.md)
- [Testing strategy](docs/TESTING_STRATEGY.md)
- [Rowing domain glossary](docs/DOMAIN_GLOSSARY.md)
- [Normalized data contracts](schemas/README.md)
- [Public evaluation fixtures](data/fixtures/README.md)

## Current repository state

The repository contains one difficult anonymized multi-device fixture, one deterministic plan-versus-performance fixture with a mid-session wind shift, a 16-case registry, versioned JSON Schemas, a ground-truth-free baseline input bundle, and public verifiers. The concrete baseline model/runner, application stack, and agent workflow still need to be implemented.

Run the deterministic tests and verify all current public artifacts with:

```bash
python3 scripts/test_all.py
```
