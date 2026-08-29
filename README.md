# WAKE - Agentic Rowing Intelligence

> Every row leaves a wake.

WAKE is an agentic intelligence layer for rowing clubs. It turns fragmented training plans, boat and crew context, environmental conditions, and telemetry from devices such as SpeedCoach and mobile phones into evidence-backed session briefings and long-term rowing memory.

**Hackathon status:** the first controlled comparison is complete. On two implemented cases, WAKE scored **63.34/100** against **38.86/100** for the direct-call baseline: **+24.48 points** (**+63.0% relative**) for US$0.062338 incremental API cost. The single-case calibration preflight remains explicitly excluded.

## The problem

In many non-elite rowing clubs, athletes train frequently while coaches cannot follow every boat on the water. Plans may arrive through WhatsApp or spreadsheets, telemetry stays in isolated CSV exports, and essential context - boat, crew, seat, route, conditions, intent, and coach observations - disappears within days.

A dashboard can store and display this information, but it still asks a human to inspect every chart and connect every variable. WAKE investigates each session, identifies missing context, reconciles conflicting sources, and presents only claims it can support with evidence and explicit uncertainty.

## Initial demo hypothesis

The first end-to-end workflow will:

1. ingest a planned workout and SpeedCoach telemetry, with mobile, environment, and context when available;
2. align and corroborate recordings when multiple devices exist, or expose the single-source limitation;
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
- [Progressive evidence contract](docs/EVIDENCE_LADDER.md)
- [Baseline runner](docs/BASELINE_RUNNER.md)
- [Agent runner](docs/AGENT_RUNNER.md)
- [Deterministic grader](docs/GRADER.md)
- [Testing strategy](docs/TESTING_STRATEGY.md)
- [Rowing domain glossary](docs/DOMAIN_GLOSSARY.md)
- [Normalized data contracts](schemas/README.md)
- [Public evaluation fixtures](data/fixtures/README.md)

## Current repository state

The repository contains one difficult anonymized multi-device fixture, one deterministic plan-versus-performance fixture with a mid-session wind shift, a 16-case registry, versioned JSON Schemas, deterministic raw telemetry adapters, progressive two-to-five-source compact-summary preparation, an explicit prepared-bundle runner, a generic coach-review adapter, a ground-truth-free baseline input bundle, comparable baseline and agentic OpenAI Responses API runners, monotonic per-case/run observability, an offline grader, the [first controlled comparison](evaluation/runs/comparison-v1-20260829/README.md), and a coach-facing product replay. Only two evaluation cases are implemented, so the result supports the current workflow without claiming broad generalization.

Install the locked dependencies, then run the deterministic tests and public verifiers:

```bash
uv sync
uv run python scripts/test_all.py
```

Preview the exact baseline requests without calling the API:

```bash
uv run python scripts/run_baseline.py
```

Preview the agent requests and its four deterministic tools without calling the API:

```bash
uv run python scripts/wake_agent.py
```

Grade a complete directory of structured outputs without network access:

```bash
uv run python scripts/grade_outputs.py \
  --outputs /path/to/run/outputs \
  --output /path/to/run/grade-report.json
```

Rebuild the frozen progressive-evidence ablation inputs without calling a model:

```bash
uv run python scripts/build_evidence_ablation.py
```

The three conditions are committed under `evaluation/ablation-inputs/v1/`: core
plan + SpeedCoach, context/environment enrichment, and the full bundle with
mobile corroboration. They are experimental inputs, not scored results.

## Product interface

The `web/` application demonstrates the smallest truthful coach workflow over the committed synthetic case 002:

```text
session inbox -> evidence intake -> review -> human checkpoint
              -> verified briefing -> approved goal memory
```

The hosted product remains a safe replay. When connected to the local product service, its intake requires a plan and SpeedCoach recording and accepts mobile, environment, and context as optional evidence enhancers. The service prepares a new ground-truth-free compact summary containing source coverage, quality, supported cross-source findings, and explicit evidence gaps. Only the byte-identical five-source public demonstration bundle can use committed replay output; different evidence cannot inherit that answer, and prepared new bundles are not executed automatically. Display data is adapted from committed public agent output, source selection remains metric-specific, environmental language remains associative rather than causal, and memory changes only after explicit coach approval.

```bash
cd web
npm install
npm test
npm run dev
```

Node.js 22.13 or newer is required. See [Product interface contract](docs/PRODUCT_INTERFACE.md) and [web implementation notes](web/README.md).

Run the task-level product service locally in no-cost replay mode:

```bash
uv run python scripts/wake_product_service.py
```

Then connect the web development server to it:

```bash
cd web
NEXT_PUBLIC_WAKE_API_URL=http://127.0.0.1:8788 npm run dev
```

Live agent execution is deliberately opt-in: start the service with `--allow-live`, provide `mode: live` on the requested execution, and configure `OPENAI_API_KEY`. Existing case-level browser live mode also requires `NEXT_PUBLIC_WAKE_RUNTIME_MODE=live`. Live execution incurs API cost and writes normal agent output and trajectory artifacts under `evaluation/runs/product-live/` or `evaluation/runs/product-live-bundles/`.

Uploaded source bytes, prepared summaries, and workflow state are process-local and non-durable. The current source boundary validates normalized plan/environment/context JSON and deterministically normalizes normalized telemetry CSV, raw SpeedCoach vendor CSV, and pre-existing WAKE mobile sensor CSV. Every telemetry result includes input/normalized hashes, row counts, timing, distance, GPS/SPM availability, rejected-row counts, and quality flags. Missing mobile SPM remains missing. `POST /api/source-bundles/prepare` assembles the required plan and SpeedCoach plus zero to three optional enhancers into a schema-validated compact summary and returns metadata only, with `agent_called: false`. `POST /api/source-bundles/:id/execute` requires explicit live mode, sends only the evidence actually supplied to the bounded agent, validates the final output, avoids a duplicate call when the same execution is repeated within one process, and returns a compact review payload. The web client can adapt that payload across different plan lengths, distances, boats, source IDs, clock availability, and missing environment. The page renders review findings generically but does not start this new-bundle path until generic checkpoint and briefing state exist. No paid call was made while implementing it.
