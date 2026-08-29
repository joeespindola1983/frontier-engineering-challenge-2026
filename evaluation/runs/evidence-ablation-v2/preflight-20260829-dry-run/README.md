# Evidence Ablation v2 — Dry-run Preflight

This preflight applies the versioned WAKE v2 distance boundary to the same three
frozen evidence conditions used by the official v1 experiment.

- `api_called` is `false`; this directory contains no model output or quality
  result.
- Input summaries and evidence hashes remain the frozen ablation v1 values.
- Model, reasoning effort, output schema, tool count, and round limits remain
  comparable with v1.
- The v2 prompt, reconstruction-tool description, tool result, and verifier all
  state that SPM-boundary segment distances cannot establish prescribed-distance
  completion or shortfall.

The three committed request files make the proposed paid comparison inspectable
before any API budget is spent.
