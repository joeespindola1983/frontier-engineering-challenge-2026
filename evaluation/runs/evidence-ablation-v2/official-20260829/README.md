# Evidence Ablation v2 — Official Run

This run evaluates the versioned WAKE v2 distance boundary against the same
three frozen summaries and source files as the preserved v1 experiment. It ran
at Git commit `3bc0cbd` with `gpt-5.6-terra`, medium reasoning effort, the same
Structured Output schema, and the same bounded four-tool workflow.

## Result

- **Core — plan + SpeedCoach:** 8/8 applicable checks, **PASS**.
- **Context/environment enrichment:** 10/10 checks, **PASS**.
- **Full bundle with mobile:** 12/12 checks, **PASS**.
- **Cross-condition execution consistency:** **PASS**.
- **Total API cost:** **US$0.358676**.
- **End-to-end runtime:** **92.202 seconds**.
- **Tokens:** 101,338 input; 13,000 output; 114,338 total.

Every condition reconstructed the six planned work intervals and reported only
the real work-05 SPM deviation. The unsupported aggregate distance-shortfall
deviation seen in v1 did not recur. Context/environment preserved the noncausal
time-aligned wind association. Full evidence continued to match mobile with
SpeedCoach, corroborate the route, and reject zero-only mobile SPM.

Core and context/environment each required one bounded verifier retry for
evidence-less unavailable/insufficient items. Neither retry involved a distance
claim: the v2 prompt and tool result prevented that candidate from appearing.
Full evidence required no retry.

## v1 to v2 interpretation

The controlled result changed from overall **FAIL** to **PASS** while the frozen
inputs and applicable capability checks remained the same. This supports the
narrow hypothesis that encoding the distance limitation at tool, prompt, and
verifier boundaries restored stable plan-execution behavior for this synthetic
session. It remains one repeated case and does not prove broad generalization,
human-coach superiority, or improved athletic performance.

The v2 run cost US$0.060072 more than v1 and consumed 19,911 more tokens. The
additional cost is observational, not attributed solely to the v2 change,
because model generation and verifier retries are nondeterministic.

## Evidence map

- `run-manifest.json`: workflow version, model/config/prompt hashes, Git commit,
  runtime, tokens, and cost.
- `outputs/`: three verified structured analyses.
- `trajectories/`: observable tool, verifier, retry, usage, and timing events.
- `ablation-report.json`: condition-aware checks and marginal capabilities.
