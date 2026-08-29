# Architecture Hypothesis

**Status:** provisional. Two fixtures, the first normalized contracts, and their verifiers are implemented; the product architecture remains a hypothesis until evaluated.

## Proposed flow

```text
Training plan      SpeedCoach CSV      Mobile telemetry      Human context
      |                   |                    |                    |
      +-------------------+--------------------+--------------------+
                                  |
                        Deterministic adapters
                                  |
                   Session matching and time alignment
                                  |
                  Metric-level quality and trust policy
                                  |
                    Evidence store with provenance
                                  |
                       Investigation orchestrator
                         /        |         \
                context tool  analysis tool  memory tool
                         \        |         /
                           evidence verifier
                                  |
                     coach-reviewable briefing
                                  |
                         approved memory update
```

## Why this is agentic

The agent is responsible for choosing what evidence to inspect, identifying contradictions, deciding which targeted tools to call, asking for missing context, revising after tool feedback, and stopping when the available evidence is insufficient. Deterministic components remain responsible for numerical parsing, alignment, segmentation, aggregation, and validation.

The project should begin with one orchestrating agent. A second specialized agent is justified only if the fixed evaluation demonstrates a meaningful quality or reliability gain.

## Proposed components

### Source adapters

Convert each supported input into a versioned normalized schema while preserving source rows or references. Parsing must be deterministic and testable.

### Session matcher and aligner

Estimate whether recordings refer to the same outing using timestamp windows, GPS overlap, movement patterns, distance, and duration. Alignment must tolerate late starts, forgotten stops, clock offsets, and partial overlap. It must produce a score and supporting evidence, not only a boolean.

### Metric trust policy

Assign confidence independently for distance, GPS route, speed/pace, SPM, motion features, intervals, and environmental context. The policy should allow one device to support distance while another supports SPM.

### Evidence store

Represent at least:

- observed values and their source references;
- deterministic derived metrics and method versions;
- user- or coach-confirmed context;
- unresolved hypotheses and conflicts;
- recommendations requiring human review.

### Investigation orchestrator

Select tools, ask focused questions, and assemble a result that clearly separates facts, inferences, missing data, and suggested next actions.

### Verifier

Reject or mark unsupported claims, check that evidence references exist, and require a human checkpoint before consequential recommendations or memory updates.

### Trajectory recorder

Capture structured runtime events without private chain-of-thought: run identifier, input hash, model and prompt versions, tool calls and responses, evidence references, retries, human checkpoints, output, runtime, and approximate cost.

## Baseline hypothesis

The baseline should represent a reasonable simple approach to the same task, such as a direct model prompt receiving a compact session summary without investigation tools, persistent memory, or evidence verification. The exact baseline must be fixed before implementing optimizations and must use the same evaluation cases as the final workflow.

The evaluation protocol is now frozen in `docs/EVALUATION_SPEC.md`. The next architecture checkpoint is a deterministic input summarizer plus one versioned direct-call baseline prompt.

## Open decisions

- Application/runtime stack.
- Model and agent SDK.
- Local versus hosted execution.
- Data store and memory representation.
- Weather provider and historical-data availability.
- Concrete grader implementation and calibration.
- User interface scope for the five-minute demonstration.
