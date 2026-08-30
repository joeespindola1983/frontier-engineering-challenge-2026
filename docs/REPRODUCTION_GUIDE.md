# Clean-environment reproduction

This guide reproduces the public WAKE submission from a clean checkout without
private rowing data, the project owner's credentials, or a new model call. The
default path verifies committed inputs, reports, trajectories, hashes, tests,
and the production interface for **US$0.00**.

## Required versions

- Git 2.39 or newer.
- Python 3.11 or newer; the final verification was run with Python 3.14.6.
- [uv](https://docs.astral.sh/uv/) 0.5.9 or newer.
- Node.js 22.13.0 or newer, as declared by `web/package.json`.
- npm 10 or newer.

The repository locks Python dependencies in `uv.lock` and web dependencies in
`web/package-lock.json`.

## Included public data

No external dataset is required for replay or evaluation. The repository
contains:

- one difficult anonymized multi-device fixture and nine synthetic evaluation
  fixtures under `data/fixtures/`;
- 52 isolated real-informed synthetic training activities under
  `data/demo-club-batch/`;
- a second 50-activity post-regatta package under
  `data/demo-club-post-regatta/v1/`, loaded locally at US$0.00;
- sanitized Concept2 PM5 reference crops and confirmed transcriptions;
- a fictional two-week club, athlete, crew, boat, and competition history;
- committed direct-baseline and WAKE outputs, run manifests, observable
  trajectories, grades, costs, and capability audits under `evaluation/`.

The original private GPS, identifiable athlete records, raw photographs,
WhatsApp files, official named result sheets, `.env`, and local session store
are not required and are intentionally excluded.

## Install and verify

Clone the repository and run the safe reproduction script:

```bash
git clone https://github.com/joeespindola1983/frontier-engineering-challenge-2026.git
cd frontier-engineering-challenge-2026
./scripts/reproduce_submission.sh
```

The script runs `uv sync --frozen`, `npm ci`,  Python tests and public artifact
verifiers, the web tests and linter, and a production build. It unsets
`OPENAI_API_KEY` and contains no paid execution path.

If dependencies are already installed:

```bash
./scripts/reproduce_submission.sh --verify-only
```

## Run the solution

Start the local product service and interface together in replay mode:

```bash
./scripts/start_dashboard.sh
```

Expected output includes readiness messages for the local service and web app.
Open [http://localhost:3000/](http://localhost:3000/). The full replay includes
session intake, evidence review, a human checkpoint, saved briefing and memory,
the two-week club, athlete Training Days, the saved longitudinal comparison,
Competition Review, the loadable post-regatta comparison, and the official
evaluation view.

Replay does not require `OPENAI_API_KEY`, does not call a model, and can reopen
committed reports at US$0.00.

## Reproduce the baseline

Rebuild the exact direct-call requests without network access:

```bash
uv run python scripts/build_baseline_inputs.py
uv run python scripts/run_baseline.py
```

Expected output is a dry-run manifest and request material with `api_called`
set to `false`. The ten official direct-baseline answers and their costs are
already preserved under
`evaluation/runs/expanded-evaluation-v2/official-20260830/baseline/`.

## Reproduce the solution workflow

Preview the bounded WAKE requests and four deterministic investigation tools
without calling the API:

```bash
uv run python scripts/wake_agent.py
```

The official WAKE outputs and observable trajectories are preserved under
`evaluation/runs/expanded-evaluation-v2/official-20260830/agent/`. Trajectories
contain public tool events, verifier decisions, retries, runtime, tokens, and
cost; they do not contain private chain-of-thought.

## Reproduce the evaluation

Run every deterministic test and public verifier:

```bash
uv run python scripts/test_all.py
```

Expected output ends with the Python suite passing and all public fixture and
artifact verifiers succeeding. Rebuild the read-only web evaluation summary:

```bash
uv run python scripts/build_evaluation_results.py
```

The fixed ten-case comparison must report:

- direct baseline: **49.00 / 100**;
- bounded WAKE: **83.76 / 100**;
- absolute gain: **+34.76 points**;
- incremental WAKE cost: **US$0.283344**;
- environmental interpretation regression: **80% to 76%**.

Rebuild the separate, non-scored longitudinal capability audit:

```bash
uv run python scripts/score_longitudinal_pilot.py
```

Expected output reports four verified saved reports, total approximate cost
US$0.110426, and `NO_DEMONSTRATED_QUALITY_GAIN`. WAKE used fewer tokens and
cost 29.01% less, but both workflows passed the same capability checks.

## Expected output

A successful zero-cost reproduction provides:

1. passing Python and web test suites;
2. eight or more public fixture/artifact verifier confirmations;
3. a successful production web build;
4. regenerated evaluation and longitudinal audit artifacts identical in
   meaning to the committed results;
5. a replay interface at `http://localhost:3000/` with no API call.

In the Sessions page, use **Load 2-week package** to add the post-regatta demo
period. The loaded comparison must show 50 activities, 16 athletes, 10 crews,
six evidence-ranked scenarios, `No model call`, `US$0.00`, and a
`NOT_ESTABLISHED` causal conclusion.

## Approximate runtime

On the development Apple Silicon machine, deterministic Python verification
took about 19 seconds, and web tests took under one second before lint/build.
Allow approximately 2–5 minutes for a clean reproduction, primarily for
dependency downloads and the production build. Runtime varies with network,
CPU, package cache, and filesystem performance.

## Approximate cost

| Path | Key required | Expected cost |
| --- | --- | ---: |
| Install, verify, build, and replay | No | US$0.00 |
| Reopen committed baseline, WAKE, or longitudinal reports | No | US$0.00 |
| Official ten-case comparison already preserved | Historical only | US$1.139688 observed |
| Four-report longitudinal pilot already preserved | Historical only | US$0.110426 observed |
| New live execution | Yes | Variable and separately authorized |

## Optional live execution and secrets

The official OpenAI guidance requires API keys to remain secret and be loaded
from a server-side environment variable. Never commit `.env` or put a key in
browser code. The repository contains only `.env.example` with an empty
`OPENAI_API_KEY` placeholder.

A new live run is not required to judge or reproduce the submitted evidence.
If a reviewer deliberately chooses to create a new result, they must supply
their own `OPENAI_API_KEY`, use the explicit live command documented by the
relevant runner, accept the displayed start authorization, and understand that
the authorization gate is not a provider billing cap. New outputs are not
expected to match saved model prose exactly.
