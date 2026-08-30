# Agent Runner v1

WAKE's first agent workflow is one bounded OpenAI Responses API loop with four
deterministic function tools and a deterministic verifier. It receives the same
frozen, ground-truth-free case summaries and uses the same model, reasoning
effort, service tier, output token limit, and structured output schema as the
direct-call baseline.

## Investigation tools

- `assess_source_trust` selects or rejects evidence independently for SPM,
  distance, and route.
- `assess_session_alignment` combines preserved clock disagreement with route
  overlap instead of requiring equal start times.
- `reconstruct_plan_execution` reconstructs work/recovery segments and compares
  SPM with the planned target when compatible telemetry exists.
- `analyze_environment` reports time-aligned environmental association while
  explicitly refusing a causal conclusion.

The tools inspect only public case inputs and compact summaries. They never read
`ground-truth.json`.

## Safety and stopping behavior

- maximum of four model rounds;
- maximum of one verifier-driven correction;
- strict JSON Schema output;
- rejection of nonexistent evidence references and source IDs;
- rejection of material claims without citations;
- rejection of broken mobile SPM as selected SPM evidence;
- abstention boundary for visible technique, crew synchronization, medical
  state, and other unsupported conclusions;
- `store: false` and no private chain-of-thought in trajectories.

## Safe dry-run

The default command does not call the API. It writes exact initial request
objects plus a hashed manifest marked `api_called: false`:

```bash
uv run python scripts/wake_agent.py
```

Select one case or an explicit output directory when needed:

```bash
uv run python scripts/wake_agent.py \
  --case case-002-wind-shift-plan-deviation \
  --output /tmp/wake-agent-preview
```

## Paid execution

Paid execution requires both an environment-provided `OPENAI_API_KEY` and the
explicit flag:

```bash
uv run python scripts/wake_agent.py --execute
```

Each successful case writes the structured final output and an observable event
trajectory containing request hashes, tool calls/results, verifier decisions,
retry events, model identifiers, start/finish timestamps, monotonic runtime,
usage, approximate cost, and the Git commit. It does not record private
chain-of-thought.

The run manifest records two intentionally different duration fields:

- `runtime_ms` is the end-to-end wall-clock duration of the sequential run,
  including per-case execution and runner overhead before manifest writing;
- `case_runtime_ms_total` is the sum of each successful case investigation,
  measured from immediately before its first request until verified output.

Monotonic clocks calculate durations so operating-system clock corrections do
not produce invalid elapsed time. UTC timestamps remain available for audit and
human inspection. Historical comparison-v1 artifacts predate these fields and
are not rewritten retrospectively.

## Evidence status

Unit and contract tests use a fake Responses client and injected monotonic clock
values to prove loop, runtime, cost, and manifest behavior without network cost.
A passing dry-run proves request construction and data boundaries, not model
quality. Quality can be claimed only after real baseline and agent outputs are
scored by the frozen rubric grader.

## Versioned distance boundary in v2

Workflow v2 keeps the model, reasoning effort, Structured Output schema, four
tools, round limit, and frozen ablation inputs comparable with v1. It changes one
failure boundary discovered by the official v1 run:

- `reconstruct_plan_execution` emits a structured `distance_assessment` with
  `INSUFFICIENT` status for prescribed-distance completion;
- v2 also reports planned-versus-observed work counts, missing work interval
  identities, and recovery-duration deviations;
- v2 environment results classify calm, steady headwind, steady tailwind,
  crosswind, and crosswind-with-gust profiles while retaining the causal boundary;
- the tool description and prompt identify segment distances as boundary-derived
  from SPM classification and exclude them from total-distance conclusions;
- the v2 verifier rejects prescribed-distance deviations built from those
  segment values, even if the candidate output cites valid files.

The v1 tool contract remains selectable for historical requests. The committed
v2 preflight is request evidence only. A separate official paid execution passed
all 8, 10, and 12 applicable condition checks and cross-condition consistency;
that result remains limited to the single frozen synthetic session.

For the ten-case expansion, the generic CLI now accepts explicit input and
prompt paths while preserving its historical v1 defaults:

```bash
uv run python scripts/wake_agent.py \
  --inputs evaluation/baseline-inputs/v2 \
  --config config/wake-agent-v2.json \
  --prompt prompts/wake-agent-v2.md \
  --output /tmp/wake-agent-v2-preview
```

Without `--execute`, this remains a zero-cost dry-run.

## Product-service entry point

`scripts/wake_product_service.py` wraps the runner behind task-level product operations. Its safe default is a committed public replay:

```bash
uv run python scripts/wake_product_service.py
```

Live mode is available only through all three conditions:

1. the server is started with `--allow-live`;
2. the investigation request explicitly uses `mode: live`;
3. `OPENAI_API_KEY` exists.

Prepared-bundle execution adds a fourth condition: the request must explicitly
authorize at least the configured operational amount, US$0.20 by default. This
is a start gate rather than a provider-enforced dollar cap. The response carries
the trajectory's usage, runtime, and approximate cost; the process-local ledger
counts an idempotent execution only once and is available through
`GET /api/runtime/costs`.

Every live product execution loads `config/wake-agent-v2.json` and
`prompts/wake-agent-v2.md` explicitly, then uses `run_agent_case`, preserving
the accepted distance boundary, verifier, bounded rounds, trajectory, runtime,
token, and cost evidence. Historical v1 evaluation artifacts and the generic
agent CLI default remain unchanged. The HTTP service never exposes low-level
tool names to the product client. See `docs/COST_MODEL.md` for the measured
reference, projections, limitations, and optimization policy.
