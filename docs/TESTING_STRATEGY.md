# Testing Strategy

WAKE uses test-driven development for deterministic behavior and fixed-case evaluation for model behavior. The goal is not merely high test coverage. The goal is to make evidence processing, uncertainty, and agent improvements reproducible.

## Development loop

For parsers, normalization, alignment, segmentation, metric trust, derived metrics, source and human-answer provenance, question routing, synthetic-data generation, schemas, and graders:

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

Runtime contracts use injected monotonic clock values in tests. Production
artifacts retain UTC start/finish timestamps for audit, while elapsed
milliseconds come from a monotonic clock and are tested independently of API
latency.

## Test layers

1. **Unit tests:** transformations and calculations with small controlled inputs.
2. **Contract tests:** schemas, normalized vocabulary, manifests, and evidence-reference rules.
3. **Fixture tests:** public cases, deterministic generation, privacy invariants, and expected failure modes.
4. **Evaluation tests:** baseline and WAKE outputs against fixed cases and the rubric.
5. **End-to-end tests:** the complete investigation workflow, including tool traces and final structured output.

Role-aware product behavior is tested at three boundaries: the service rejects invalid uploader/origin combinations and unattributed confirmed answers; the client preserves uploader, answerer, recorder, and authority-basis fields; and the interface keeps the expected respondent visible without treating a coach or athlete statement as telemetry. These tests establish contract behavior only. Authentication and verified role identity remain outside the current process-local MVP.

The local dashboard launcher is also a deterministic product boundary. Its
tests require valid shell syntax, replay/no-model startup by default, explicit
live opt-in with an API key, visible cost authorization, enabled weather, and
secret-free output. Runtime smoke testing then verifies readiness of both the
session API and coach page; `Ctrl+C` must terminate both child processes.

The session inbox has restart and lifecycle regression coverage. Tests require prepared evidence to appear as awaiting analysis; completed analysis, coach view, human response, and memory approval to remain separate milestones; reopening to preserve an answered investigation; state to restore from a temporary local store; and session endpoints to omit raw and normalized sensor bytes. The browser rehearsal additionally refreshes the page and restarts the service after approval. This proves local prototype persistence, not encryption, multi-club isolation, backup, or distributed exactly-once execution.

The synthetic-fixture privacy verifier scans only declared textual fixture formats. A regression test preserves the `/Users/` leak check while ensuring binary operating-system metadata such as `.DS_Store` cannot crash the verifier after a web build or Finder visit.

Historical-weather enrichment is tested at four deterministic boundaries: a
timezone-aware telemetry stream or a local clock with an explicit IANA timezone produces a rounded, bounded lookup request; the
provider adapter sends no raw route or identity data; a provider response
normalizes to the versioned environment schema and is filtered to the query
window; and provider absence or failure leaves the core plan plus SpeedCoach
bundle usable. A live smoke test may verify provider compatibility only with a
public synthetic coordinate and must not be described as an accuracy result.
The web boundary additionally tests consent and timezone validation before
upload side effects, generated-source ordering, uploaded/provider environment
exclusivity, coordinate-free preview formatting, fallback preparation, and the
no-agent-call replay path.

The submission-only Evaluation view is built from a deterministic public
summary generator. Tests require exact official scores, cost and observable
trajectory counts, all ten case deltas, the preserved environmental regression,
byte-stable generation, and the absence of evaluator ground truth, material
output prose, or evidence references. The browser surface is read-only and has
no client method that can execute or regrade a run.

The demo-club period screen is tested independently from model behavior. Tests
require all recorded activities to be classified, session findings to be
derived from observations rather than prefilled labels, every attention signal
to carry evidence references, human/source gaps to remain outside the paid
queue, clean screens not to imply full plan compliance, complete source bundles
to be counted only when linked to the paid queue, and cost projections to retain
their observed, planning, and authorization meanings. A separate public
verifier checks the two demo-club bundles for reproducible generation, input
hashes, privacy invariants, schema validity, and exact deterministic deviation
identities without invoking a model. A second verifier freezes the two paid
candidate outputs: it checks artifact hashes, output schema, v2 trajectory and
verification status, absence of private chain-of-thought, exact isolated
deviation identities, per-run usage/cost, authorization compliance, and summed
totals. Neither verifier can invoke the model.

Source-batch tests begin RED on the missing batch boundary and require
content-addressed idempotence, invalid-item isolation, sequential start-gate
execution, resume without duplicate calls, one runner failure not blocking a
later item, restart-safe state, and compact responses without telemetry rows.
The forty-record public-batch verifier independently checks every source hash,
plan schema, Concept2-shaped column contract, SpeedCoach normalization,
deterministic v2 water-session reconstruction, exact two paid-result links,
routing totals, cost totals, and the zero-human-approval and no-synthesis
boundaries. Generated files must rebuild byte-for-byte.

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

Safe baseline and agent dry-runs are available as `scripts/run_baseline.py` and `scripts/wake_agent.py`. Paid execution remains opt-in through `--execute`. Until real outputs are scored by the frozen grader, request generation, fake-client loop tests, and fixture verification must not be described as an agent-quality score.

Grade a complete baseline or agent output directory offline:

```bash
uv run python scripts/grade_outputs.py \
  --outputs /path/to/run/outputs \
  --output /path/to/run/grade-report.json
```

The grader validates every output against the frozen schema, scores only implemented cases and applicable dimensions, and records its version and configuration hash. Passing grader calibration tests establishes scoring behavior; only grading real model outputs produces a measured workflow-quality score.
