# Baseline Runner v1

The baseline is one direct OpenAI Responses API call per case. It receives the same compact, deterministic, ground-truth-free summary that WAKE will receive, but it has no tools, memory, retries, claim verifier, or human checkpoint.

## Frozen configuration

- Model: `gpt-5.6-terra`
- Reasoning effort: `medium`
- API: Responses API
- Output: strict Structured Outputs using `wake.analysis_output.v1.1` in `schemas/analysis-output.schema.json`
- Service tier: `default`
- Server-side response storage: disabled
- Maximum output: 12,000 tokens per case
- Temperature: not set; recorded as `null`

The final WAKE comparison should use the same model and reasoning effort unless a separately recorded experiment explicitly studies model choice. This keeps the measured difference focused on workflow design.

The model and pinned price assumptions live in `config/baseline-v1.json`. The source is the [official OpenAI model documentation](https://developers.openai.com/api/docs/models). Account availability and actual billing remain controlled by the OpenAI project used for the run.

## Setup

```bash
uv sync
```

This creates an ignored `.venv/` and installs the exact versions in `uv.lock`.

## Safe dry-run

The safe default does not call the API:

```bash
uv run python scripts/run_baseline.py
```

It writes the exact request objects and a manifest with `api_called: false`. Select one case or another output directory when needed:

```bash
uv run python scripts/run_baseline.py \
  --case case-002-wind-shift-plan-deviation \
  --output /tmp/wake-baseline-preview
```

The historical default remains the frozen two-case v1 bundle. Preview the
ten-case v2 expansion explicitly:

```bash
uv run python scripts/run_baseline.py \
  --inputs evaluation/baseline-inputs/v2 \
  --output /tmp/wake-baseline-v2-preview
```

## Paid execution

Set `OPENAI_API_KEY` in the process environment without committing it, then explicitly add `--execute`:

```bash
uv run python scripts/run_baseline.py --execute
```

The runner refuses `--execute` when the key is absent. It records only public observables: prompt/input/schema hashes, Git commit, model requested and returned, response ID/status, structured output, latency, token usage, and approximate cost. It does not request or store private chain-of-thought.

At the pinned prices, the configured maximum output alone is up to USD 0.144 per case; actual total cost also includes input tokens and is calculated from returned API usage. A two-case run therefore has a configured output-token ceiling of USD 0.288, before input cost. Typical output may be substantially smaller, but no estimate should be represented as actual billing.

## Verification

```bash
uv run python scripts/test_all.py
```

Passing tests establish request and artifact behavior. They do not establish model quality. A baseline quality score exists only after real outputs are graded against the frozen rubric.
