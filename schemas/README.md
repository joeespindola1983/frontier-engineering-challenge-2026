# WAKE Data Contracts

These JSON Schemas define the first normalized boundary between deterministic tools, the agent, and the evaluator.

- `training-plan.schema.json`: normalized coach prescription, including ranges and unresolved terms;
- `recorded-session.schema.json`: matched sources, series references, and reconstructed segments;
- `environment-timeline.schema.json`: timestamped environmental evidence with an explicit wind-direction convention;
- `evidence-claim.schema.json`: observed, derived, confirmed, inferred, conflicted, unknown, or unsupported claims;
- `ground-truth.schema.json`: evaluator-only expected matches, segments, claims, abstentions, questions, and tolerances;
- `case-summary.schema.json`: compact deterministic input shared by the baseline and WAKE;
- `analysis-output.schema.json`: common structured output required from the baseline and WAKE.

Raw vendor exports do not need to conform to these schemas. Deterministic adapters will preserve raw provenance and produce normalized objects. In case 002, `input/plan.json` and `input/environment.json` are normalized inputs; `recorded-session` and `evidence-claim` describe future workflow outputs.

Schema versions are independent of generator and grader versions. Any incompatible contract change requires a new schema version and an evaluation comparability note.
