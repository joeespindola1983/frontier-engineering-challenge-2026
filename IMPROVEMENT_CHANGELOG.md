# Improvement Changelog

This changelog will connect every meaningful experiment to evidence produced with a consistent evaluation method. It begins before implementation so the project does not reconstruct its development story after the fact.

## Current status

Two reproducible evaluation cases, evaluation specification version 1.0, a tested direct-call baseline, and the first tested agent tool loop now exist. No paid model call or measured agent-quality result has been produced.

## Experiments

### 1. Discovery — rowing workflow

- **Hypothesis:** A rowing-specific workflow can recover valuable daily training context that dashboards and isolated device exports leave for coaches to reconstruct manually.
- **Change:** Defined the rowing bottleneck and an initial evidence-backed workflow before selecting an implementation stack.
- **Evaluation:** Domain interview notes were consolidated in the product brief. No quantitative evaluation was available at this stage.
- **Result:** The problem was specific enough to support a testable workflow rather than a generic sports dashboard.
- **Decision:** Keep the rowing domain and proceed to a fixture audit.
- **Next step:** Define the baseline and primary metric before implementing the final workflow.

### 2. Data audit — real hero fixture

- **Hypothesis:** A real multi-device session with conflicting clocks and metrics can demonstrate why WAKE must investigate evidence instead of trusting one file or averaging every sensor.
- **Change:** Audited the private export corpus and selected a three-device session containing matching, clock-offset, source-conflict, and missing-evidence failure modes. Built a minimized deterministic transformation rather than publishing raw files.
- **Evaluation:** `python3 scripts/verify_hero_fixture.py` checks public hashes, privacy invariants, 549 SpeedCoach strokes, mobile evidence availability, preserved clock offsets, and route-overlap p95 below 5 m.
- **Result:** Case 001 preserves the intended conflicts while removing private location, date, device, and athlete information. This is fixture evidence, not an agent-improvement score.
- **Decision:** Keep the transformed session as `case-001-misaligned-double-scull`.
- **Next step:** Freeze the rubric and a simple baseline before adding agent behavior.

### 3. Evaluation contract — synthetic case 002

- **Hypothesis:** A deterministic synthetic execution can provide exact ground truth for plan compliance, environmental change, and sensor failure without fabricating real athlete history.
- **Change:** Froze a 100-point rubric, registered 16 cases, created five versioned schemas, and generated a plan-versus-performance case with a wind shift, true SPM deviation, clock offset, distance bias, and failed mobile SPM.
- **Evaluation:** `python3 scripts/verify_synthetic_case.py` checks six work intervals, five valid recoveries, only `work-05` as a plan deviation, a wind transition inside `work-04`, a +37 s mobile clock offset, +1.2% mobile distance bias, and zero usable mobile SPM rows.
- **Result:** Case 002 is byte-reproducible and contains the intended failure modes. This is deterministic fixture evidence, not an agent score.
- **Decision:** Keep rubric v1.0 and `case-002-wind-shift-plan-deviation`.
- **Next step:** Do not count the fourteen planned cases until each fixture and its ground truth are implemented and verified.

### 4. TDD foundation — frozen baseline input

- **Hypothesis:** Freezing a compact, ground-truth-free input before model selection will make later baseline and agent comparisons reproducible and resistant to answer leakage.
- **Change:** Adopted RED-GREEN-REFACTOR, added unit and contract tests, normalized confirmed rowing vocabulary, and froze the compact input plus direct-call prompt.
- **Evaluation:** `python3 scripts/test_all.py` ran six deterministic tests and three public artifact verifiers at this stage. The RED run exposed a stale zone fixture and two testability defects before the GREEN implementation.
- **Result:** The compact summary contract, vocabulary rules, hashes, and leakage checks passed. This is engineering evidence, not an agent score.
- **Decision:** Keep the permanent TDD policy and the baseline v1 input boundary.
- **Next step:** Select the comparison model without changing frozen inputs after inspecting its answers.

### 5. Direct-call baseline runner

- **Hypothesis:** A single structured model call without tools, memory, retries, or verification provides a fair minimum baseline for measuring workflow value.
- **Change:** Configured a one-call Responses API runner with GPT-5.6 Terra at medium reasoning, strict structured output, explicit cost metadata, `store: false`, and opt-in paid execution.
- **Evaluation:** `uv run python scripts/test_all.py` passed ten tests and three artifact verifiers at this stage. A two-case dry-run produced hashed request previews of 21,550 and 48,218 bytes with `api_called: false`; execution without an API key was rejected.
- **Result:** The baseline is reproducible and safe to preview, but no real model output or quality score exists yet.
- **Decision:** Keep baseline runner v1 unchanged for the first comparison.
- **Next step:** Score it against the same frozen cases and grader used for WAKE.

### 6. Bounded agent tool loop

- **Hypothesis:** Giving the same model deterministic investigation tools and a claim verifier should improve evidence selection, abstention, and correction over the direct-call baseline.
- **Change:** Used RED-GREEN-REFACTOR to add four ground-truth-free tools, a bounded Responses API function loop, strict output verification, one correction retry, public-only input resolution, round limits, and observable trajectories. The model and reasoning settings remain equal to the baseline.
- **Evaluation:** RED runs failed first on missing modules, then on absent runner contracts, and finally on missing-evidence and source-identity verifier gaps. The final `uv run python scripts/test_all.py` passes 26 tests and three public verifiers. A two-case dry-run produced 24,124-byte and 50,792-byte requests with `api_called: false` and no ground-truth reference. Fake-client tests cover tool continuation, retry, stopping, and trajectory behavior.
- **Result:** The agent workflow is executable and its deterministic boundaries are tested. This is workflow-engineering evidence, not a model-quality score.
- **Decision:** Keep agent workflow v1 for the first controlled comparison.
- **Next step:** Implement the deterministic rubric grader from frozen ground truth before inspecting model answers, then execute baseline and agent cases under an explicit budget.

## Entry template

### YYYY-MM-DD - Experiment name

- **Hypothesis:** What should improve and why?
- **Change:** What was added, removed, or revised?
- **Evaluation:** Which fixed cases, commands, and metric were used?
- **Result:** Include the complete result and a link to committed evidence.
- **Cost/runtime:** Record relevant model, tool, token, time, and cost information.
- **Decision:** Keep, revise, or remove.
- **Learning:** What failure mode or insight changes the next step?

The final version must include the simple baseline, every important iteration, the combined final workflow, the most impactful change, and at least one removed experiment.
