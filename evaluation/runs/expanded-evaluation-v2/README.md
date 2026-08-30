# Expanded evaluation v2

This directory preserves the ten-case comparison path before any paid model
execution. The `preflight/` directory contains exact request objects for:

- ten direct-call baseline requests using `baseline-inputs/v2`;
- ten bounded WAKE requests using agent config v2, prompt v2, and tool contract v2.

Both dry-run manifests declare `api_called: false`. The request hashes were
verified locally, and no request contains `ground-truth` or `ground_truth`.
This is reproducibility evidence only: it is not a model-quality result.

Reproduce from the repository root:

```bash
uv run python scripts/run_baseline.py \
  --inputs evaluation/baseline-inputs/v2 \
  --output evaluation/runs/expanded-evaluation-v2/preflight/baseline

uv run python scripts/wake_agent.py \
  --inputs evaluation/baseline-inputs/v2 \
  --config config/wake-agent-v2.json \
  --prompt prompts/wake-agent-v2.md \
  --output evaluation/runs/expanded-evaluation-v2/preflight/agent
```

Paid outputs, trajectories, costs, and grader reports must be written to a new
subdirectory. Do not replace this preflight or the historical v1 comparison.
