# Successful product-bundle live retest

This directory preserves a successful retest of the exact five-source public
synthetic bundle through the same `build_bundle_live_runner` and
`execute_source_bundle` functions used by the local HTTP product service.

It was run after the earlier browser rehearsal recorded in Improvement
Changelog entry 29 returned `Agent runtime unavailable.` The retest establishes
that the current accepted v2 product-bundle runner can complete; it does not
retroactively explain the earlier failure and is not described as a browser
end-to-end result.

## Result

- Git commit: `9f952f66a254d2bb15a7c2feecd97724e99ff1c9`
- Workflow: `wake-agent-v2-tool-loop`
- Model: `gpt-5.6-terra`
- Case: `case-002-wind-shift-plan-deviation`
- Runtime: 22.522 seconds
- Input tokens: 31,610
- Output tokens: 2,680
- Total tokens: 34,290
- Approximate cost: US$0.095380
- Verifier: passed all eight v2 checks without a retry
- Tool calls: source trust, session alignment, plan reconstruction, and
  environment analysis
- Private chain of thought stored: no

The US$0.20 value supplied by the caller was an operational start
authorization, not a provider billing cap.

## Integrity

```text
ca4ef38374f1b8e4cd80ce2c7b0cf9e7c7d03cac257984968ffa38a51473d4f0  outputs/case-002-wind-shift-plan-deviation.json
ff8237fdd597773f370118bfbc8642207cd69bb33a4d2bc8234aa4636bb04ad2  trajectories/case-002-wind-shift-plan-deviation.trajectory.json
```
