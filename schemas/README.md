# WAKE Data Contracts

These JSON Schemas define the first normalized boundary between deterministic tools, the agent, and the evaluator.

- `training-plan.schema.json`: normalized coach prescription, including ranges and unresolved terms;
- `recorded-session.schema.json`: matched sources, series references, and reconstructed segments;
- `source-normalization-report.schema.json`: deterministic parser provenance, row counts, timing, coverage, and quality flags;
- `environment-timeline.schema.json`: backward-compatible v1 synthetic and v2 provider-normalized environmental evidence, including provenance, session window, humidity, and an explicit wind-direction convention;
- `evidence-claim.schema.json`: observed, derived, confirmed, inferred, conflicted, unknown, or unsupported claims;
- `ground-truth.schema.json`: evaluator-only expected matches, segments, claims, abstentions, questions, and tolerances;
- `case-summary.schema.json`: compact deterministic input shared by the baseline and WAKE;
- `analysis-output.schema.json`: common structured output required from the baseline and WAKE; current contract is `wake.analysis_output.v1.1` after a pre-run strict-schema refinement.

Raw vendor exports do not need to conform to these schemas. The implemented adapters preserve raw and normalized SHA-256 provenance and produce a normalized CSV plus `wake.source_normalization.v1`. SpeedCoach local clock values remain timezone-unknown, and missing mobile SPM remains empty rather than being synthesized as zero. Concept2 PM5 transcriptions must declare `HUMAN_CONFIRMED` or `SYNTHETIC`; they add segment kind/index, pace, optional heart rate, and optional watts to the shared telemetry columns and are explicitly marked summary-level and timestamp-absent. In case 002, `input/plan.json` and `input/environment.json` are normalized inputs; `recorded-session` and `evidence-claim` describe later workflow outputs.

Schema versions are independent of generator and grader versions. Any incompatible contract change requires a new schema version and an evaluation comparability note.
