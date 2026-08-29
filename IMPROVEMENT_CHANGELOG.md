# Improvement Changelog

This changelog will connect every meaningful experiment to evidence produced with a consistent evaluation method. It begins before implementation so the project does not reconstruct its development story after the fact.

## Current status

Two reproducible evaluation cases, evaluation specification version 1.0, a tested direct-call baseline, and the first tested agent tool loop now exist. No paid model call or measured agent-quality result has been produced.

| Stage | What we tried and why | Evidence | Decision / learning |
| --- | --- | --- | --- |
| Discovery | Defined the rowing bottleneck and an initial evidence-backed workflow before selecting a stack. | Domain interview notes summarized in the product brief; no quantitative result yet. | Proceed to fixture audit and define the baseline and primary metric before implementing the final workflow. |
| Data audit and hero fixture | Audited the private export corpus and selected a three-device case that concentrates matching, clock, source-conflict, and missing-evidence failures. Built a minimized deterministic transformation rather than publishing raw files. | `python3 scripts/verify_hero_fixture.py` verifies public hashes, privacy invariants, 549 SpeedCoach strokes, mobile evidence availability, preserved clock offsets, and route-overlap p95 below 5 m. This is fixture evidence, not an agent improvement score. | Keep this as case 001. Define the rubric and freeze a simple baseline before adding agent behavior. |
| Evaluation contract and synthetic case 002 | Froze a 100-point rubric, registered 16 cases, created five versioned schemas, and generated a plan-versus-performance case with a wind shift, true SPM deviation, clock offset, distance bias, and failed mobile SPM. | `python3 scripts/verify_synthetic_case.py` verifies six work intervals, five valid recoveries, only `work-05` as a plan deviation, wind transition inside `work-04`, +37 s mobile clock offset, +1.2% mobile distance bias, and zero usable mobile SPM rows. This is deterministic fixture evidence, not an agent score. | Keep rubric v1.0 and case 002. Implement the frozen direct-call baseline next and do not count the fourteen planned cases until each is generated and verified. |
| TDD foundation and baseline input contract | Adopted red-green-refactor, added unit and contract tests, normalized confirmed rowing vocabulary, and froze a compact ground-truth-free input plus direct-call prompt before choosing a model. | `python3 scripts/test_all.py` runs six deterministic tests and three public artifact verifiers. The initial red run caught the stale zone fixture plus two testability defects; the green run passes. This is engineering evidence, not an agent score. | Keep the TDD policy and baseline v1 boundary. Select and run the concrete baseline model next without changing the frozen input after inspecting its answers. |
| Direct-call baseline runner | Configured a one-call Responses API baseline with GPT-5.6 Terra at medium reasoning, strict structured output, explicit cost metadata, no tools, `store: false`, and opt-in paid execution. | `uv run python scripts/test_all.py` passes ten tests and three artifact verifiers. A two-case dry-run produced hashed request previews of 21,550 and 48,218 bytes with `api_called: false`; the no-key execution guard also rejected the call. This is runner evidence, not a model score. | Keep the runner. Obtain explicit API-key/budget authorization, execute both frozen cases, and grade the outputs without revising the inputs after inspection. |
| Bounded agent tool loop | Followed RED-GREEN-REFACTOR to implement four deterministic, ground-truth-free tools, a single Responses API function loop, strict output verification, one correction retry, round limits, public-only input resolution, and observable trajectories. Held the model and reasoning configuration equal to the baseline. | The RED runs failed first on missing modules, then missing runner contracts, then missing-evidence/source-identity verifier gaps. The final `uv run python scripts/test_all.py` passes 26 tests and three public verifiers. A two-case no-cost dry-run produced 24,124-byte and 50,792-byte requests with `api_called: false` and no ground-truth reference. Fake-client tests prove tool continuation, retry, stopping, and trajectory behavior. This is workflow engineering evidence, not a quality score. | Keep agent workflow v1. Implement the deterministic rubric grader from frozen ground truth before inspecting model answers, then execute baseline and agent cases under an explicit budget. |

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
