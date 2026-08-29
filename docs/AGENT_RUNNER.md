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
retry events, model identifiers, usage, and the Git commit. It does not record
private chain-of-thought.

## Evidence status

Unit and contract tests use a fake Responses client to prove loop behavior
without cost or network dependence. A passing dry-run proves request construction
and data boundaries, not model quality. Quality can be claimed only after real
baseline and agent outputs are scored by the frozen rubric grader.
