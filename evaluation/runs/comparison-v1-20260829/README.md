# Controlled Comparison v1

This directory contains the first official, two-case comparison between the
direct-call baseline and the bounded WAKE agent. Both arms used the same
`gpt-5.6-terra` model, medium reasoning effort, public input bundle, structured
output schema, and frozen deterministic grader v1.1 at commit `b1d9a46`.

The earlier `baseline-case001-preflight` directory is calibration evidence. It
is explicitly excluded from the comparison below.

## Result

- Baseline macro-average: **38.86 / 100**.
- WAKE macro-average: **63.34 / 100**.
- Absolute improvement: **+24.48 points**.
- Relative improvement over baseline: **+63.0%**.
- Baseline API cost: **US$0.109940**.
- WAKE API cost: **US$0.172278**.
- Incremental agent cost: **US$0.062338**.
- Total official comparison cost: **US$0.282218**.

Case 001 improved from 38.71 to 47.04. Case 002 improved from 39.00 to
79.64. The largest measured gains came from deterministic segment
reconstruction, exact plan-deviation detection, and better metric-level source
selection in the planned wind-shift case.

The agent invoked all four deterministic tools for both cases. Its verifier
rejected the first case-001 draft because two material items lacked evidence
references; one bounded retry corrected both errors. Case 002 passed on its
first verification attempt. Trajectories store observable events and explicitly
record that private chain-of-thought was not stored.

## Remaining failures and validity boundary

- Only two of the sixteen registered cases are implemented, so this result is
  evidence for the current workflow, not a broad claim about all rowing data.
- Case 001 still missed human-confirmed boat/crew context and asked unnecessary
  questions.
- Case 002 still selected only three of five expected metric sources, omitted
  the expected follow-up decision, and did not express every required
  abstention in the grader's expected form.
- After the grader was frozen, both case-001 outputs exposed a remaining bounded
  text-classification blind spot: “cannot be evaluated” / “remain unevaluated”
  was treated as a confident technique claim. The grader was not changed after
  seeing official results. This underestimates both case-001 arms and remains a
  documented limitation for a future grader version.
- The baseline records per-case runtime. Agent v1 records token/cost usage and
  event trajectories but not a reliable end-to-end runtime field; no runtime is
  inferred retrospectively.

## Evidence map

- `baseline/run-manifest.json`: baseline configuration, usage, and cost.
- `baseline/grade-report.json`: baseline per-case and per-dimension scores.
- `agent/run-manifest.json`: agent configuration, usage, cost, and trajectories.
- `agent/grade-report.json`: agent per-case and per-dimension scores.
- `agent/trajectories/`: tool calls, tool results, verification, retry, and final
  output events.
- `baseline-case001-preflight/`: excluded calibration output and cost manifest.

All grading was offline. Both reports carry grader configuration hash
`a3f3d526124d0c5b7687ef38b48dfc52a82f0291af7a718884540b0dcbc32d87`.
