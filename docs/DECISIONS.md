# Decision Log

This log records product and engineering decisions as they are made. Accepted decisions may still be revised, but revisions must preserve the earlier rationale and link to new evidence.

## 2026-08-28 - Select rowing as the problem domain

- **Status:** accepted.
- **Decision:** Build for the fragmented daily training workflow experienced by rowing coaches and athletes.
- **Rationale:** The project owner has direct domain knowledge, access to representative device exports, and firsthand understanding of the missing context that generic fitness products overlook.

## 2026-08-28 - Use WAKE as the product identity

- **Status:** accepted working identity.
- **Decision:** Use **WAKE - Agentic Rowing Intelligence** with the tagline **Every row leaves a wake.**
- **Rationale:** The name supports both analytical progression and the emotional history of rowing without limiting the product to competitions.

## 2026-08-28 - Treat regattas as goals, not product boundaries

- **Status:** accepted.
- **Decision:** Model a regatta as one high-value goal and evaluation milestone inside continuous rowing intelligence.
- **Rationale:** Daily sessions, crew changes, boats, indoor work, conditions, and athlete history remain valuable between events.

## 2026-08-28 - Keep the hackathon repository separate

- **Status:** accepted.
- **Decision:** Build in a new repository and document the earlier mobile rowing application as pre-existing work.
- **Rationale:** This creates an honest competition boundary, protects a working application with unrelated changes, and makes reproduction simpler.

## 2026-08-28 - Preserve private telemetry outside Git

- **Status:** accepted.
- **Decision:** Commit only public, synthetic, or explicitly anonymized fixtures. Ignore raw private data by default.
- **Rationale:** Rowing exports may reveal location, time, device, and identity information.

## 2026-08-28 - Prefer metric-level sensor trust

- **Status:** accepted as the central hypothesis; evaluation pending.
- **Decision:** Do not merge devices by blindly averaging values. Select or reject evidence independently for each metric and claim.
- **Rationale:** A dedicated SpeedCoach may provide reliable SPM while a phone may still provide useful GPS, motion, or redundancy. Device quality varies by mounting, hardware, conditions, and failure mode.

## 2026-08-28 - Start with a minimal evidence scaffold

- **Status:** accepted.
- **Decision:** Commit the problem definition, pre-existing boundary, requirements, architecture hypothesis, and changelog before choosing an implementation stack.
- **Rationale:** The hackathon requires a genuine improvement story. Recording assumptions before experiments makes later results auditable and avoids rewriting the history after the solution exists.

## 2026-08-29 - Select the misaligned men's 2x session as the hero case

- **Status:** accepted.
- **Decision:** Use one real, three-device outing as the first end-to-end evaluation case. A human domain expert confirmed that the recordings describe the same men's double scull (`2x`) session with two athletes.
- **Rationale:** The case contains several valuable failure modes at once: device clocks differ by almost one hour, route evidence strongly matches, source summaries disagree, mobile raw SPM is absent, Android gyroscope readings are zero, and both mobile boat defaults are wrong.

## 2026-08-29 - Preserve conflicts and require abstention in the hero case

- **Status:** accepted.
- **Decision:** Keep the incorrect `SINGLE_SCULL` and `OC1` source values and conflicting distance/SPM summaries. The reference answer must prefer the confirmed `2x` context, choose evidence per metric, expose disagreements, and abstain from plan-compliance and technique claims.
- **Rationale:** Cleaning away contradictions would remove the agentic work. No planned workout or direct technique observation exists for this outing.

## 2026-08-29 - Publish a transformed, minimized fixture

- **Status:** accepted.
- **Decision:** Translate the route to a synthetic origin, shift all dates by one shared deterministic delta, replace identifiers, and retain only one mobile sensor row per distinct GPS position plus the final row. Keep original schemas and metric failure modes.
- **Rationale:** The transformation preserves matching, timing, source-quality, and reconciliation behavior while removing the real route, date, serials, device models, workout IDs, and unnecessary high-frequency motion data.

## 2026-08-29 - Keep raw-data regeneration local and verification public

- **Status:** accepted.
- **Decision:** Store private paths and source hashes only in ignored `private-data/`. Commit the generated fixture, public content hashes, generator, and a standalone verifier.
- **Rationale:** Maintainers with approved raw data can reproduce the transformation, while judges can verify the published artifact without private access.

## 2026-08-29 - Freeze the first evaluation rubric before the baseline

- **Status:** accepted as evaluation specification version 1.0.
- **Decision:** Use macro-average weighted rubric score from 0 to 100 as the primary metric across implemented fixed cases. Score plan interpretation, session alignment, segmentation, metric-level trust, deviation detection, environmental interpretation, evidence/abstention, and follow-up questions.
- **Rationale:** A fixed rubric prevents the baseline or final workflow from redefining success after outputs are visible. Secondary metrics retain diagnostic detail, especially unsupported-claim rate and required-abstention recall.

## 2026-08-29 - Register sixteen cases and separate demonstration from diagnosis

- **Status:** accepted; two cases implemented and fourteen planned.
- **Decision:** Keep complex cases for the product demonstration and add isolated synthetic cases for individual failure modes. Planned cases do not enter the evaluation denominator until their fixtures and ground truth are committed.
- **Rationale:** Three examples can tell the story but cannot characterize the full workflow. Isolated cases make regressions attributable, while a complex hero case demonstrates why the components matter together.

## 2026-08-29 - Use derived-synthetic plans without fabricating real history

- **Status:** accepted.
- **Decision:** Use the structure of approved real coach prescriptions to create anonymized synthetic plans and entirely synthetic athletes, dates, routes, weather, and telemetry. Never attach an unrelated real session to a plan or imply that a synthetic execution occurred.
- **Rationale:** Real prescriptions provide domain realism; deterministic synthetic execution provides exact ground truth and privacy-safe adversarial cases.

## 2026-08-29 - Accept the first normalized evidence contracts

- **Status:** accepted as version 1; revision expected through implementation evidence.
- **Decision:** Version JSON Schemas for training plans, recorded sessions, environment timelines, evidence claims, and evaluation ground truth.
- **Rationale:** The contracts separate observed evidence, derived values, human confirmation, conflicts, and unsupported claims before agent prompting begins.

## 2026-08-29 - Normalize voga and standardized rowing zones

- **Status:** accepted from human domain confirmation.
- **Decision:** Normalize `voga` in the supplied plans to target stroke rate in SPM. Treat B0-B7 and E1-E7 as standardized rowing-zone codes, preserving the code and marking the zone system without inventing physiological thresholds.
- **Rationale:** This resolves parsing ambiguity while keeping scientific boundaries separate until an authoritative definition is recorded.

## 2026-08-29 - Adopt TDD for deterministic behavior

- **Status:** accepted.
- **Decision:** Use red-green-refactor for parsers, normalization, alignment, segmentation, trust policies, generators, schemas, and graders. Add a regression test before fixing a reproducible bug. Evaluate LLM behavior with fixed cases and rubrics rather than exact prose snapshots.
- **Rationale:** WAKE's value depends on reproducible evidence handling and defensible uncertainty. TDD protects deterministic contracts, while case-based evaluation accommodates nondeterministic language without weakening behavioral requirements.

## 2026-08-29 - Freeze baseline prompt and compact input contract v1

- **Status:** accepted; no model result yet.
- **Decision:** Give both the direct-call baseline and WAKE the same ground-truth-free compact case summary. Freeze `wake.case_summary.v1`, `wake.analysis_output.v1.1`, `prompts/baseline-v1.md`, and the generated `evaluation/baseline-inputs/v1/` bundle before running the baseline model. Output v1.1 is the pre-run strict-schema refinement of the earlier unexecuted v1 draft.
- **Rationale:** Raw telemetry is unnecessarily large for an LLM, and showing different evidence to the baseline would make the comparison invalid. Hashes and leakage checks make the boundary auditable.

## 2026-08-29 - Use Python, uv, and the OpenAI Responses API for evaluation runs

- **Status:** accepted for the evaluation runner.
- **Decision:** Use Python 3.11 or newer, dependencies locked by `uv`, the official OpenAI Python SDK, Responses API, and strict Structured Outputs. Keep API execution opt-in and reject paid execution when `OPENAI_API_KEY` is absent.
- **Rationale:** The existing deterministic evidence tools are Python, and the Responses API exposes structured JSON output plus observable usage metadata without requiring an orchestration framework for the simple baseline.

## 2026-08-29 - Select GPT-5.6 Terra medium for the first comparison

- **Status:** accepted; availability and first real run pending.
- **Decision:** Configure both the direct baseline and the initial WAKE workflow with `gpt-5.6-terra`, reasoning effort `medium`, default service tier, no server-side response storage, and no explicit temperature. Pin the price assumption independently from actual returned usage.
- **Rationale:** Official OpenAI documentation positions Terra as the balance between intelligence and cost. Holding model and reasoning effort constant makes workflow improvement the independent variable.

## 2026-08-29 - Implement one bounded agent with direct deterministic tools

- **Status:** accepted for evaluation workflow v1; quality result pending.
- **Decision:** Use one custom Responses API loop with four direct function tools: metric-level source trust, session alignment, plan-versus-execution reconstruction, and environmental association. Limit the loop to four model rounds and one verifier retry, keep `store: false`, and record observable events without private chain-of-thought.
- **Rationale:** The workflow makes evidence selection, tool use, correction, and stopping behavior inspectable while keeping the same model, reasoning effort, inputs, and output schema as the frozen direct-call baseline. A framework or multiple agents would add complexity before fixed-case evidence shows that it improves quality.

## 2026-08-29 - Make TDD a permanent project constraint

- **Status:** accepted and recorded in repository instructions.
- **Decision:** Every new deterministic tool, verifier rule, runner behavior, grader, and memory policy begins with a failing behavioral test, followed by the smallest passing implementation and a green-suite refactor.
- **Rationale:** The project owner explicitly requires TDD throughout the project, and evidence-sensitive rowing conclusions need regression protection rather than retrospective tests.

## 2026-08-29 - Freeze deterministic grader v1 before model inspection

- **Status:** accepted; real-output calibration pending.
- **Decision:** Use a versioned offline grader with the frozen 100-point weights, case-applicable normalization, numeric tolerances, source-selection rules, deviation precision/recall, evidence checks, bounded concept matching, and critical zero rules. Record the grader configuration hash in run reports and do not use an LLM judge for v1.
- **Rationale:** Implementing and testing scoring before inspecting paid model answers reduces evaluator drift. Deterministic scoring is reproducible and inexpensive; any discovered phrasing blind spot must enter through a RED calibration test rather than an ad hoc score adjustment.

## 2026-08-29 - Calibrate and freeze deterministic grader v1.1

- **Status:** accepted before the official comparison.
- **Decision:** Treat the first paid, single-case baseline execution as a calibration preflight and exclude it from official results. Preserve grader v1.0, add RED regression tests for connected pairwise source matches, common metric aliases, and explicit “unassessable” language, then freeze grader v1.1 without changing rubric weights, ground truth, or model configuration.
- **Rationale:** The preflight showed that v1.0 scored equivalent structured representations as incorrect. Versioning the generic corrections before either official arm is run prevents a model-specific score patch while keeping the calibration history auditable.

## 2026-08-29 - Keep the bounded single-agent workflow after comparison v1

- **Status:** accepted for the hackathon demonstration; broader validation pending.
- **Decision:** Keep the four-tool bounded WAKE loop as the primary demonstrated workflow. It scored 63.34/100 versus 38.86/100 for the direct-call baseline on the two implemented cases at an incremental API cost of US$0.062338. Do not add a multi-agent architecture until a fixed-case failure demonstrates that it is necessary.
- **Rationale:** The measured gain came primarily from deterministic reconstruction and deviation analysis, while the remaining failures concern missing human context, follow-up precision, and abstention expression. More orchestration would not directly address those observed bottlenecks.

## 2026-08-29 - Measure agent runtime at case and run levels

- **Status:** accepted for future executions; historical artifacts remain immutable.
- **Decision:** Record UTC start/finish timestamps and monotonic `runtime_ms` in every successful case trajectory. Record end-to-end `runtime_ms` and `case_runtime_ms_total` separately in the run manifest, along with per-case and total approximate cost.
- **Rationale:** A single duration is ambiguous in a tool loop. Separating wall-clock execution from summed investigation time makes runner overhead visible, while monotonic elapsed time remains reliable if the system clock changes. Existing comparison-v1 artifacts are evidence and must not be retroactively rewritten.

## 2026-08-29 - Separate the coach product from evaluation surfaces

- **Status:** accepted for the hackathon product slice.
- **Decision:** Use a React, TypeScript, Vinext, and native-CSS web application for the coach-facing flow. Keep fixtures, baseline scores, trajectories, and grader controls in repository and terminal artifacts rather than primary product navigation.
- **Rationale:** A coach needs a calm session review, one material question, and an approvable briefing. Exposing benchmark machinery in that path would optimize the interface for judges instead of the user.

## 2026-08-29 - Demonstrate the interface through a faithful synthetic replay

- **Status:** accepted; live ingestion remains pending.
- **Decision:** Derive the first UI view model from committed public case-002 agent output and test it against that artifact. Label the replay as synthetic, preserve metric-level source policy and unsupported unknowns, describe wind only as time-aligned association, and create in-memory goal history only after explicit coach approval.
- **Rationale:** The replay makes the complete product value legible without inventing athletes, sessions, causal claims, or a weekend-scale persistence system. Its adapter boundary can later be replaced by a task-level API without moving reasoning into the browser.

## Pending decisions

- Live agent API deployment target and application-service boundary.
- Schema revisions justified by parser and grader implementation evidence.
