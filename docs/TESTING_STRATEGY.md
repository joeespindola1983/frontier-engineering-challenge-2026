# Testing Strategy

WAKE uses test-driven development for deterministic behavior and fixed-case evaluation for model behavior. The goal is not merely high test coverage. The goal is to make evidence processing, uncertainty, and agent improvements reproducible.

## Development loop

For parsers, normalization, alignment, segmentation, metric trust, derived metrics, synthetic-data generation, schemas, and graders:

1. **Red:** write the smallest test that describes the next behavior or reproduces a bug, then confirm it fails for the expected reason.
2. **Green:** implement the smallest production change that makes the test pass.
3. **Refactor:** improve names, structure, and duplication while the suite remains green.

A deterministic bug fix is incomplete without a regression test. Generated fixtures must remain reproducible from a fixed seed and must be verified by content hashes and semantic invariants.

## Model and agent behavior

LLM output is nondeterministic, so WAKE does not treat an exact paragraph or JSON string snapshot as the expected answer. Instead, the baseline and final workflow receive the same frozen case summaries and are assessed against:

- versioned output schemas;
- required and prohibited claims;
- evidence references;
- required abstentions;
- case-specific ground truth;
- the frozen weighted rubric in `docs/EVALUATION_SPEC.md`.

Prompts, model settings, input-summary versions, outputs, runtime, and cost must be recorded for every scored experiment.

## Test layers

1. **Unit tests:** transformations and calculations with small controlled inputs.
2. **Contract tests:** schemas, normalized vocabulary, manifests, and evidence-reference rules.
3. **Fixture tests:** public cases, deterministic generation, privacy invariants, and expected failure modes.
4. **Evaluation tests:** baseline and WAKE outputs against fixed cases and the rubric.
5. **End-to-end tests:** the complete investigation workflow, including tool traces and final structured output.

## Commands

Run the fast behavioral suite:

```bash
uv run python -m unittest discover -s tests -v
```

Run every public fixture and generated-artifact verifier:

```bash
uv run python scripts/verify_all.py
```

Run both layers before committing an implementation change:

```bash
uv run python scripts/test_all.py
```

Safe baseline and agent dry-runs are available as `scripts/run_baseline.py` and `scripts/wake_agent.py`. Paid execution remains opt-in through `--execute`. Until real outputs pass the future grader, request generation, fake-client loop tests, and fixture verification must not be described as an agent-quality score.
