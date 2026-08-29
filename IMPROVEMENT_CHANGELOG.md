# Improvement Changelog

This changelog will connect every meaningful experiment to evidence produced with a consistent evaluation method. It begins before implementation so the project does not reconstruct its development story after the fact.

## Current status

Two reproducible evaluation cases and evaluation specification version 1.0 now exist. There is still no runnable agent baseline or measured agent-quality result.

| Stage | What we tried and why | Evidence | Decision / learning |
| --- | --- | --- | --- |
| Discovery | Defined the rowing bottleneck and an initial evidence-backed workflow before selecting a stack. | Domain interview notes summarized in the product brief; no quantitative result yet. | Proceed to fixture audit and define the baseline and primary metric before implementing the final workflow. |
| Data audit and hero fixture | Audited the private export corpus and selected a three-device case that concentrates matching, clock, source-conflict, and missing-evidence failures. Built a minimized deterministic transformation rather than publishing raw files. | `python3 scripts/verify_hero_fixture.py` verifies public hashes, privacy invariants, 549 SpeedCoach strokes, mobile evidence availability, preserved clock offsets, and route-overlap p95 below 5 m. This is fixture evidence, not an agent improvement score. | Keep this as case 001. Define the rubric and freeze a simple baseline before adding agent behavior. |
| Evaluation contract and synthetic case 002 | Froze a 100-point rubric, registered 16 cases, created five versioned schemas, and generated a plan-versus-performance case with a wind shift, true SPM deviation, clock offset, distance bias, and failed mobile SPM. | `python3 scripts/verify_synthetic_case.py` verifies six work intervals, five valid recoveries, only `work-05` as a plan deviation, wind transition inside `work-04`, +37 s mobile clock offset, +1.2% mobile distance bias, and zero usable mobile SPM rows. This is deterministic fixture evidence, not an agent score. | Keep rubric v1.0 and case 002. Implement the frozen direct-call baseline next and do not count the fourteen planned cases until each is generated and verified. |

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
