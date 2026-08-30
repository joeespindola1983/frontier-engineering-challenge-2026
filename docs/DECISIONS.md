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

- **Status:** accepted; two cases scored, eight more fixture-ready, and six still fixture-planned.
- **Decision:** Keep complex cases for the product demonstration and add isolated synthetic cases for individual failure modes. A planned case does not enter the evaluation denominator until its fixtures, ground truth, public verification, compatible grader behavior, and required model outputs are committed.
- **Rationale:** Three examples can tell the story but cannot characterize the full workflow. Isolated cases make regressions attributable, while a complex hero case demonstrates why the components matter together.

## 2026-08-30 - Version expanded evaluation inputs without rewriting v1

- **Status:** accepted; v2 inputs are fixture-ready and unscored.
- **Decision:** Preserve `evaluation/baseline-inputs/v1/` byte-for-byte for the published two-case comparison. Put the ten-case expansion in `evaluation/baseline-inputs/v2/`, retaining the exact v1 entries for cases 001-002 and adding cases 003-010. Keep new registry entries `PLANNED` until evaluation execution is complete.
- **Rationale:** Adding inputs to a directory already used by an official run would make its manifest non-reproducible and could silently change runner defaults or grader denominators.

## 2026-08-30 - Calibrate a separate generalized grader v1.2

- **Status:** accepted; official ten-case outputs and scores committed.
- **Decision:** Preserve grader v1.1 for the published two-case comparison. Use grader v1.2 for the ten-case expansion, with case-derived plan, source-policy, environment, abstention, and deviation checks. Keep the same 100-point rubric weights and critical-zero rules.
- **Rationale:** Grader v1.1 intentionally contained case-002-specific expectations. Reusing it would make new environmental conditions and source IDs fail for representation rather than behavior.

## 2026-08-30 - Promote cases through a separate v2 registry

- **Status:** accepted after official execution and offline scoring.
- **Decision:** Preserve `evaluation/cases.json` as the historical v1 denominator with two implemented cases. Add `evaluation/cases-v2.json` for grader v1.2 and promote cases 001-010 only after both comparison arms produced complete saved outputs. Keep cases 011-016 planned.
- **Rationale:** Updating the shared registry would silently change grader v1.1 and break reproduction of the published two-case comparison. A versioned registry makes implementation status honest without rewriting historical evaluation state.

## 2026-08-30 - Expose diagnostic plan and environment facts in tool contract v2

- **Status:** accepted after deterministic preflight; paid result pending.
- **Decision:** Keep tool contract v1 unchanged. In v2, expose planned-versus-observed work counts, missing work IDs, recovery-duration compliance, and wind/crosswind/gust profiles. Use a v2 work threshold two SPM below the lowest prescribed work target so a slightly under-target interval remains contiguous rather than becoming alternating false work/recovery groups.
- **Rationale:** The no-cost audit showed that asking the model to infer these facts from fragmented segments would confound agent quality with a deterministic tool failure. The two-SPM gap still separates the synthetic 19-SPM work interval from 16-SPM recovery while preserving the deviation itself.

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

## 2026-08-30 - Add a bounded submission-only Evaluation view

- **Status:** accepted for the hackathon build; the coach workflow remains separate.
- **Decision:** Add one read-only Evaluation destination beside the operational navigation. Generate its public aggregate deterministically from the official manifests and grade reports. Show the common protocol, macro scores, every case delta, dimension diagnostics, cost, tool/retry observability, and validity boundaries. Do not expose ground truth, raw evidence, full model prose, grader controls, replay controls, or any execution action.
- **Rationale:** The completed ten-case comparison is central submission evidence and benefits from a visual explanation, but turning the product into a benchmark console would weaken its user story. A visibly labelled `Saved result · No model call` surface makes the evidence legible to judges while keeping coaching actions, evaluation machinery, and paid execution distinct.

## 2026-08-29 - Demonstrate the interface through a faithful synthetic replay

- **Status:** accepted; live ingestion remains pending.
- **Decision:** Derive the first UI view model from committed public case-002 agent output and test it against that artifact. Label the replay as synthetic, preserve metric-level source policy and unsupported unknowns, describe wind only as time-aligned association, and create in-memory goal history only after explicit coach approval.
- **Rationale:** The replay makes the complete product value legible without inventing athletes, sessions, causal claims, or a weekend-scale persistence system. Its adapter boundary can later be replaced by a task-level API without moving reasoning into the browser.

## 2026-08-29 - Add a local task-level product service with explicit live opt-in

- **Status:** accepted for the demonstration runtime.
- **Decision:** Expose investigation creation, checkpoint answers, briefing approval, and goal retrieval through a small local Python HTTP service. Replay committed public output by default. Permit the existing bounded OpenAI runner only when the server is started with `--allow-live`, the browser is configured for `live`, and `OPENAI_API_KEY` exists.
- **Rationale:** This connects the product flow to the real agent runtime without teaching the browser about low-level tools or making a normal page click silently spend API budget. A standard-library server avoids a new framework dependency during the hackathon; hosted execution and durable state remain separate decisions.

## 2026-08-29 - Isolate uploaded evidence from committed replay output

- **Status:** accepted for the local demonstration runtime.
- **Decision:** Accept five typed process-local sources—plan, SpeedCoach, mobile, environment, and context—only after deterministic filename, size, schema/column, and format validation. Return metadata and SHA-256 provenance to the browser, never source bytes. Permit source-based replay only when every uploaded byte sequence exactly matches public case 002.
- **Rationale:** An upload control is dangerous if arbitrary evidence can inherit a canned answer. Exact bundle identity lets the interface demonstrate real independent intake without overstating raw parsing or letting a modified workout receive unrelated conclusions. Durable private uploads and new-bundle live normalization remain separate TDD decisions.

## 2026-08-29 - Normalize telemetry without repairing missing measurements

- **Status:** accepted as source normalization version 1.
- **Decision:** Deterministically convert SpeedCoach vendor per-stroke CSV, pre-existing WAKE mobile sensor CSV, and canonical telemetry CSV into the same seven-column stream. Emit a versioned quality report with original and normalized hashes. Preserve blank mobile SPM as blank, classify zero-only and absent SPM separately, derive SpeedCoach timestamps from its local clock while marking the timezone unknown, and normalize mobile epoch timestamps to UTC.
- **Rationale:** Normalization should make sources comparable without making them falsely equivalent. Synthesizing SPM or silently assigning a timezone would convert missing context into fabricated evidence precisely where WAKE is supposed to abstain.

## 2026-08-29 - Prepare new source bundles without executing them

- **Status:** superseded for new bundles by the progressive evidence contract below; retained as the official full-bundle history.
- **Decision:** Assemble exactly one validated plan, SpeedCoach stream, mobile stream, environment timeline, and context document into `wake.case_summary.v1` deterministically. Record input hashes, preserve source quality and missing SPM, compare clocks only when timezone representations are compatible, compute distance conflict and bidirectional GPS overlap, project wind only with a known route heading, and keep human-only facts as evidence gaps. Store the full summary in process memory and return compact preparation metadata with `agent_called: false`.
- **Rationale:** Parsing and analysis are different authority boundaries. A novel upload must receive its own traceable input before it can ever reach a model, but preparation must neither spend budget nor let changed evidence inherit the public replay. Explicit abstention on missing route heading also prevents an environmental projection from becoming fabricated evidence.

## 2026-08-29 - Require explicit, idempotent live execution for prepared bundles

- **Status:** accepted for the local demonstration runtime; no paid execution performed during implementation.
- **Decision:** Expose prepared-bundle execution only through `POST /api/source-bundles/:id/execute` with `mode: live`, a service started with `--allow-live`, and `OPENAI_API_KEY`. Pass the compact summary and canonical evidence through an isolated temporary directory to the existing bounded runner, validate the final schema and case identity, preserve normal output/trajectory artifacts, and return the same recorded result on a repeated same-process request.
- **Rationale:** Preparation should remain free and safe, while execution must be a deliberate budget boundary. Reusing the evaluated runner preserves its tool limits, verifier, provenance, and observability. Same-process idempotence reduces accidental duplicate charges without pretending to provide durable exactly-once semantics.

## 2026-08-29 - Adapt verified analysis without case-specific UI claims

- **Status:** accepted for the coach-review boundary.
- **Decision:** Return a compact review bundle after prepared execution and adapt it from plan, context, verified segments, deviations, source policy, environmental assessment, and follow-up questions. Derive work count, distance label, boat/crew label, provenance, source names, clock visibility, and environmental absence from those values. Remove case-002-only reconstruction prose and the fixed fourth-interval wind marker from the page. Keep new-bundle execution unavailable from the page until checkpoint and briefing state are equally generic.
- **Rationale:** A technically live agent is not a functional product if its UI silently rewrites every result into the demonstration story. Testing with a women's `1x`, four 500 m repetitions, authenticated upload IDs, and no environment proves that the adapter responds to evidence rather than fixture identity. Delaying page invocation avoids a half-working flow after the review screen.

## 2026-08-29 - Adopt a progressive evidence contract

- **Status:** accepted for product preparation and explicit live execution; the official replay remains unchanged.
- **Decision:** Require a training plan and SpeedCoach recording for the MVP plan-versus-performed workflow. Treat mobile telemetry, environment, and session context as independent evidence enhancers. Mark every source as core/enhancer and present/absent, compute cross-source claims only when their prerequisites exist, and preserve missing capabilities as evidence gaps. Keep the exact five-source requirement only for byte-identical public replay eligibility.
- **Rationale:** SpeedCoach already supports the central execution analysis. Making the pre-existing experimental mobile application mandatory would reduce adoption and overstate hackathon scope. Optional mobile evidence still adds measurable value through route/distance corroboration, clock alignment, and conflict detection. An evidence-ablation experiment must quantify that marginal value before the final submission claims it.

## 2026-08-29 - Evaluate progressive evidence by capability, not one ablation score

- **Status:** accepted for evidence-ablation version 1.
- **Decision:** Execute all three frozen conditions with the same prompt, model configuration, output schema, and bounded runner. Isolate the evidence directory per condition. Report common execution consistency and capability-specific checks rather than a single score across unequal inputs. Treat false mobile corroboration in reduced conditions, causal wind language, and selection of broken mobile SPM as explicit failures. Keep paid execution behind literal `--execute` and `OPENAI_API_KEY`.
- **Rationale:** Removing a source intentionally makes some rubric dimensions inapplicable. A single aggregate would confuse unavailable capability with poor reasoning and could falsely make the full bundle look better merely because it contains more information. Capability reporting answers the actual product question: what remains reliable with core evidence, and what becomes supportable when an enhancer is added.

## 2026-08-29 - Preserve the failed v1 ablation and version the correction

- **Status:** accepted after the official evidence-ablation run.
- **Decision:** Preserve the frozen v1 inputs, prompt, outputs, trajectories, and failing capability report unchanged. Treat telemetry-derived segment distance as insufficient evidence of prescribed-distance completion until a new workflow version states and tests that boundary explicitly.
- **Rationale:** The core condition added an unsupported distance-shortfall deviation while the richer conditions did not. Rewriting v1 would hide the most useful experimental finding; a versioned TDD correction keeps both the improvement history and the next comparison auditable.

## 2026-08-29 - Enforce the v2 distance boundary in three layers

- **Status:** accepted as a candidate workflow; paid evaluation pending.
- **Decision:** Keep the v1 tool contract selectable and introduce v2 through a versioned config and prompt. In v2, the reconstruction tool returns an `INSUFFICIENT` prescribed-distance assessment, the instructions prohibit summing boundary-derived segment distances, and the verifier rejects a conflicting distance-completion deviation.
- **Rationale:** Prompt wording alone cannot guarantee the boundary. Encoding the same rule in deterministic evidence and output verification makes the failure observable, correctable through the bounded retry, and regression-tested without rewriting the official v1 experiment.

## 2026-08-29 - Accept workflow v2 after the official ablation repeat

- **Status:** accepted for the demonstrated progressive-evidence workflow; broader validation pending.
- **Decision:** Use the v2 distance boundary for the hackathon demonstration while preserving v1 as failure evidence. Report the official repeat as 8/8 core, 10/10 context/environment, 12/12 full, and stable execution across conditions at US$0.358676.
- **Rationale:** With the same frozen inputs and capability checks, v2 removed the unsupported distance-shortfall deviation without losing environmental association, route/session corroboration, or broken-mobile-SPM rejection. One synthetic repeated case supports this workflow choice but not broad model reliability or athlete-performance claims.

## 2026-08-29 - Complete custom live sessions with generic human confirmation

- **Status:** accepted for the local demonstration runtime; persistence remains pending.
- **Decision:** Register every successfully executed prepared bundle as a process-local investigation and derive its checkpoint, briefing, and memory proposal from that bundle's plan, verified analysis, and follow-up question. Use a generic `humanConfirmation` object rather than an equipment-specific field. Let the page invoke this path only when both a local service URL and explicit live mode are configured; keep hosted replay as the default.
- **Rationale:** A generic review followed by a hard-coded six-by-one-kilometer briefing would turn a correct agent result into a false product claim. The complete transition is now tested with a different plan and question, while explicit live authorization preserves the existing paid-action boundary. Durable club memory still requires authentication, tenancy, and storage.

## 2026-08-29 - Separate live cost authorization from observed API cost

- **Status:** accepted for the local demonstration runtime.
- **Decision:** Require an explicit positive finite `authorized_cost_usd` of at least US$0.20 before a new prepared-bundle execution may start. Treat it as an operational gate, not a provider-enforced cap. Return trajectory-derived token usage, runtime, approximate cost, and overrun status; show the result in the coach review; and aggregate each new execution once in a process-local ledger. Use US$0.15 only as a planning reference derived from the observed v2 conditions, not as a guarantee.
- **Rationale:** Silent paid actions are unacceptable, but the Responses API does not provide a dollar cap for an individual request. Separating authorization from observed usage makes that limitation honest, prevents missing or invalid client values from reaching the runner, and gives the hackathon demonstration auditable scaling evidence without claiming durable billing controls.

## 2026-08-29 - Separate contributors from evidence and answer authority

- **Status:** accepted for the process-local demonstration runtime; verified identity remains pending.
- **Decision:** Allow an athlete or coach to upload any supported source while recording the uploader independently from the source origin and authority scope. Route each human checkpoint to an expected respondent and require confirmed answers to preserve the answerer, recorder, and authority basis. Treat athlete-direct answers, athlete reports recorded by coaches, and coach direct observations as distinct provenance paths; keep `UNKNOWN` valid.
- **Rationale:** SpeedCoach files commonly remain with athletes while training plans originate with coaches, yet either person may forward either artifact. Restricting upload by role would block real club workflows, while assigning authority to the uploader would make forwarded evidence misleading. The same distinction is required for human answers: actual equipment use belongs primarily to the participant, while plan intent belongs to the coach.

## 2026-08-29 - Keep historical weather opt-in, approximate, and noncausal

- **Status:** accepted for the local product service and evidence intake; broader accuracy evaluation remains pending.
- **Decision:** Use Open-Meteo Historical Forecast as the first historical-weather adapter. Require both the `--allow-weather` service flag and explicit per-request approximate-location authorization. Send only a two-decimal median coordinate and bounded date range, never route rows or identity. Require an observed timestamp offset or a user-confirmed IANA timezone for raw SpeedCoach local clocks, and preserve that time assumption in `wake.environment_timeline.v2`. Keep weather optional: lookup failure must not block a plan plus SpeedCoach bundle. Analyze values in SI units, restrict them to the session window, and return insufficient temporal resolution rather than infer an intra-session change from coarse hourly data.
- **Rationale:** Historical wind, gust, temperature, and humidity can add material context without making the pre-existing mobile app mandatory. The provider data is modeled grid evidence rather than an on-boat measurement, so it can support time association and cross-session learning but cannot establish a causal performance effect or a local gust. Explicit consent, coordinate minimization, provenance, and abstention preserve that distinction.

## 2026-08-30 - Separate weather preparation from paid agent execution

- **Status:** accepted for local interface QA.
- **Decision:** Let replay-mode users upload the core sources, retrieve authorized historical conditions, inspect a coordinate-free preview, and prepare the resulting bundle without invoking the agent. Preserve the exact five-source public replay separately. Require explicit live runtime configuration and the existing cost authorization before a changed prepared bundle can reach the bounded agent.
- **Rationale:** Weather lookup and input validation can be tested without spending model budget. Conflating enrichment with paid investigation would make interface QA expensive, hide provider failures behind agent execution, and weaken the product's existing separation between deterministic preparation and agent analysis.

## 2026-08-30 - Persist a local session inbox with independent workflow milestones

- **Status:** accepted for the single-user local demonstration runtime; production storage remains pending.
- **Decision:** Persist validated source bytes, normalized telemetry, prepared bundles, investigations, checkpoint answers, briefings, approved goal memory, weather-cache metadata, and cost observations in a versioned JSON state file under the Git-ignored `private-data/wake-product/` boundary. Restrict the file to the current OS user. Represent analysis completion, coach view, human response, and coach approval as independent session milestones; make investigation creation idempotent so reopening cannot erase an existing answer. Expose safe list/detail/view session endpoints that never return raw or normalized telemetry rows.
- **Rationale:** A reset form and one aggregate status cannot tell a coach whether evidence was merely received, analysed, seen, answered, or accepted into club memory. A local restart-safe state file makes the weekend workflow functional and demonstrable without claiming a production database. The boundary must remain explicit: this store is not encrypted, authenticated, multi-tenant, backed up, or distributed exactly-once storage.

## 2026-08-30 - Use one safe launcher for the local product stack

- **Status:** accepted for development and demonstration rehearsal.
- **Decision:** Start the Python product service and Vinext dashboard through `scripts/start_dashboard.sh`. Keep replay with no model call as the default, enable the optional weather adapter, wait for both readiness endpoints, restore the existing ignored state store, and terminate both child processes from one `Ctrl+C`. Require `--live` plus `OPENAI_API_KEY` for paid execution, preserve the explicit US$0.20 start authorization, and never print the key. Allow separate manual commands to remain available for process-level debugging.
- **Rationale:** The product depends on matching API origin, browser runtime mode, service capabilities, ports, Node version, and paid-execution gates. Re-entering those independently makes demo startup error-prone and can accidentally create a mismatch between a live browser and replay-only service. A tested launcher improves reproducibility without weakening the cost boundary.

## 2026-08-30 - Keep evaluation fixtures outside the coach inbox

- **Status:** accepted for the hackathon interface.
- **Decision:** Expose the saved official evaluation through a visible Sessions-page action and a separate read-only destination. Present one consolidated comparison plus ten expandable individual case reports. Do not register benchmark fixtures as operational club sessions.
- **Rationale:** The compact header hides primary navigation at narrower widths, so a submission-critical report needs an in-content entry point. At the same time, placing synthetic and derived-synthetic fixtures in the coach inbox would misrepresent them as athlete sessions and distort operational counts. Separate per-case reports provide the requested depth without compromising product truthfulness.

## 2026-08-30 - Demonstrate club scale with a separate relational synthetic dataset

- **Status:** accepted for the hackathon interface; live multi-session ingestion remains pending.
- **Decision:** Add a clearly labelled two-week `WAKE Demo Club` dataset with four 2x lineups, four 4x lineups, two 8x lineups, sixteen fictional named athletes, named physical boats, planned crew outings, recorded solo/ergometer alternatives, and explicit participation gaps. Model a crew as an ordered lineup snapshot linked to a physical boat. Keep this dataset separate from the persistent session inbox and technical evaluation fixtures.
- **Rationale:** One deep session demonstrates reconstruction quality but does not make the club-scale problem visible. The relational dataset lets the interface answer how often a crew launched, which lineups and physical boats an athlete rowed, and where expected activity lacks a record. Using fictional deterministic data avoids exposing the owner's private GPS and athlete identities. It also prevents a frontend aggregation from being misrepresented as an agent-generated longitudinal conclusion.

## 2026-08-30 - Label demo data by privacy status and domain provenance

- **Status:** accepted for the hackathon interface and documentation.
- **Decision:** Label the two-week club dataset `real-informed synthetic`, and show both halves of that classification in the interface. State that workout patterns, source formats, plausible value ranges, and operational failure modes were modeled from supplied real coach prescriptions, SpeedCoach CSVs, pre-existing WAKE mobile exports, and first-hand rowing-club context. Separately state that identities, the displayed club history, lineups, exact sessions, outcomes, aggregates, and physical-boat names are fictional. Preserve the boundary that this is not a statistically representative sample or evidence of real athletic performance.
- **Rationale:** `Synthetic` alone protects privacy but hides the domain grounding that makes the demo credible. Calling the records `real` would fabricate athlete history and overstate validation. The combined label communicates both provenance and limitation without exposing private inputs.

## 2026-08-30 - Screen the full club period before paid investigation

- **Status:** accepted for the deterministic demo-club layer; source-bundle generation is complete and paid longitudinal execution remains pending.
- **Decision:** Replace prewritten demo-club findings with compact plan, SpeedCoach, and context observations and derive attention through `wake.club_period_analysis.v1`. Screen every recorded activity at zero model cost. Route supported numeric anomalies to a future bounded investigation, but route crew availability, participation gaps, missing plans, and missing athlete context to their human or source dependency first. Show complete-source-bundle coverage, deep-investigation progress, synthesis status, and the three distinct cost projections in the interface.
- **Rationale:** Paying a model to repeat a stored answer is circular, while calling it on every record wastes budget and hides orchestration value. Deterministic screening can cover the club consistently; the agent should spend reasoning only where evidence is complete and ambiguity remains. The two numeric candidates now become ready for authorization only because their complete public bundles pass deterministic preflight; readiness is not the same as execution.

## 2026-08-30 - Preflight public club candidates before paid execution

- **Status:** accepted; no model call has been made for either candidate.
- **Decision:** Generate two complete real-informed synthetic plan + SpeedCoach + context bundles from a deterministic script, preserve their input hashes and fictional boundary in a manifest, and require the public verifier to reproduce the expected `work-02` SPM and `recovery-02` duration deviations before showing `READY_FOR_AUTHORIZATION`. Keep `agent_executed: false`, `0/2` completed, and longitudinal synthesis `NOT_EXECUTED` until an explicit paid run is authorized.
- **Rationale:** Compact UI observations are sufficient for cheap triage but not a defensible agent input. Complete source artifacts make the next paid comparison reproducible, while preflight separates parser/tool correctness from model behavior and prevents the interface from implying that a prepared case was already analysed.

## 2026-08-30 - Preserve two authorized club-candidate investigations separately from synthesis

- **Status:** accepted and executed for the two public synthetic candidates; longitudinal synthesis remains unauthorized.
- **Decision:** Run exactly the Bridge Mixed 2x and Atlas Men 4x source bundles with the accepted v2 bounded workflow and a US$0.20 start authorization for each. Preserve outputs, trajectories, hashes, verification status, token use, runtime, and cost in a dedicated versioned run manifest. Show `2/2` and the observed total in the club interface, but keep the eight human/source routes outside the paid queue and keep longitudinal synthesis `NOT_EXECUTED` until separately authorized.
- **Rationale:** Candidate-level reasoning is now evidence rather than a forecast. Separating the still-optional synthesis prevents the earlier two-call authorization from silently expanding into a third paid action and prevents two synthetic sessions from being presented as a full-club conclusion.

## 2026-08-30 - Submit in bulk while preserving session-level execution

- **Status:** accepted for the local prototype and public two-week demonstration.
- **Decision:** Treat a batch as an upload, progress, and authorization envelope only. Keep every session content-addressed, prepared, executed, costed, reviewed, and persisted independently. Permit up to 100 prepared items; isolate invalid items and runner failures; execute paid candidates sequentially through whole per-execution start gates; resume pending work after restart; and never concatenate multiple sessions into one model prompt. Display data validation, reconstruction, plan comparison, agent verification, and human approval as separate levels.
- **Rationale:** Manual one-by-one intake does not demonstrate club scale, while a single multi-session prompt would mix evidence, weaken provenance, complicate retries, and make cost or human approval impossible to audit. Bulk orchestration over independent units provides speed without sacrificing history. After individual Concept2 expansion, the fifty-two-record public batch makes current coverage honest: 52 validated and reconstructed, 51 plan-compared, two agent-verified, and zero human-approved.

## 2026-08-30 - Normalize confirmed PM5 transcriptions without claiming photo OCR

- **Status:** accepted for the deterministic public-batch path and judge evidence packet; operational photo upload and native export ingestion remain pending.
- **Decision:** Normalize human-confirmed Concept2 PM5 screen transcriptions by declared workout type. Fixed-distance rows treat displayed meters as cumulative and displayed time as per-split; fixed-time rows treat displayed time as cumulative and meters as per-split; interval rows preserve work/recovery identity. Publish only minimized, metadata-stripped, identity-free screen crops and confirmed transcriptions under `ANONYMIZED_REAL_REFERENCE`. Keep heart-rate-bearing originals private. Do not call this automatic OCR, native ErgData support, per-stroke telemetry, or agent verification.
- **Rationale:** Real PM5 material improves source credibility, but copying raw photographs would retain unnecessary environment, metadata, and potentially physiological values. Declared semantics plus human confirmation avoid silently mis-summing PM5 columns, while the sanitized evidence packet lets judges inspect the real source shapes that informed the synthetic demo.

## 2026-08-30 - Make indoor results athlete-owned and group them through Training Day

- **Status:** accepted for the deterministic demo-club layer and public batch.
- **Decision:** Treat every Concept2 PM5 result as an individual athlete activity even when several athletes share one prescription. Group activities by athlete and date only after preserving source identity. Use declared roles (`PRE_WATER`, `POST_WATER`, `PRIMARY`, or `ALTERNATIVE`) and link status to classify water-only, indoor-only, combined, and expected-missing Training Days. Keep water and indoor distance separate; compare Concept2 pace, SPM, and watts only within compatible workout shapes and plan context.
- **Rationale:** A PM5 measures one machine and athlete, not a crew. A day can legitimately contain water plus indoor work or indoor-only training, especially during weather or seasonal constraints. Athlete-centered chronology makes that workload visible without converting ergometer meters into on-water performance or inferring muscular strength, technique, or fitness from unsupported metrics.

## 2026-08-30 - Evaluate longitudinal intelligence through two selective scopes

- **Status:** accepted and executed; the observed result does not demonstrate a quality gain.
- **Decision:** Freeze one athlete briefing and one club-priority briefing after the deterministic 52-activity screen. Compare a direct baseline with the bounded WAKE workflow for each scope using the same compact input, `gpt-5.6-terra` at medium reasoning, and one strict output schema. Keep water and indoor volumes separate; forbid unsupported technique, physiology, fitness, or performance-trend conclusions; require evidence references and human review. Persist verified reports so reopening costs nothing. Require a new US$0.20 start gate for each of the four planned calls, US$0.80 total, while disclosing that the gate is not a provider cap.
- **Rationale:** Two preserved session exceptions demonstrate selective investigation but not period-level value. A small controlled longitudinal comparison can test whether agentic investigation improves prioritization without spending on every activity or silently turning deterministic aggregates into model conclusions. Freezing inputs, costs, and evaluation boundaries before execution prevents post-result redesign.

## 2026-08-30 - Preserve the neutral longitudinal result without a post-hoc score

- **Status:** accepted for the submission evidence.
- **Decision:** Preserve all four verified reports and the two provider schema-rejection attempts. Report the observed US$0.110426 total, 15,035 direct-baseline tokens, 8,238 WAKE tokens, and 29.01% lower WAKE cost. Do not invent a weighted quality score after seeing the outputs. Use a clearly labelled, non-scored capability audit only: both workflows covered the required evidence, abstained from unsupported trend claims, kept water and indoor boundaries, and required human review; therefore the result is `NO_DEMONSTRATED_QUALITY_GAIN`.
- **Rationale:** A negative or neutral experiment is more credible than retrofitting a rubric to manufacture a win. The result still provides useful evidence about resource use and schema compatibility, while keeping the official pre-registered ten-case evaluation separate.

## 2026-08-30 - Reproduce the submission without credentials or a new model call

- **Status:** accepted for clean-environment judging.
- **Decision:** Make `scripts/reproduce_submission.sh` the safe clean-checkout verifier. It installs locked dependencies unless `--verify-only` is supplied, unsets live credentials, runs deterministic tests and public verifiers, rebuilds the longitudinal audit, lints the interface, and creates a production build. It contains no `--execute` path and costs US$0.00.
- **Rationale:** Judges should be able to verify the solution, baseline, evaluation, and saved outputs without receiving the owner's API key or paying to recreate stochastic prose. Live execution remains a separate opt-in path with a new key and authorization.

## 2026-08-30 - Demonstrate new club evidence through a second post-regatta package

- **Status:** accepted for the deterministic replay and interface.
- **Decision:** Add a second public real-informed synthetic period for the same 16 athletes and 10 crews: 50 compact activities across ten weekdays, with 30 crew-water records and 20 individual Concept2 records. Load it explicitly from the Sessions page and compare it deterministically at US$0.00. Include six supported product scenarios: observed faster comparable, observed slower comparable, stable range, environment-confounded water, participation review, and insufficient equivalent evidence. Every comparison must preserve evidence references and `causal_conclusion: NOT_ESTABLISHED`.
- **Rationale:** A second period demonstrates that WAKE memory can evolve when new training arrives without paying GPT to restate deterministic facts. Varied observations make the product value visible while preventing a faster time, slower time, windy outing, or missing record from becoming an unsupported fitness or performance conclusion.

## 2026-08-30 - Add a synthetic competition review without attaching real identities to fictional history

- **Status:** accepted for the deterministic hackathon interface; direct second-stage distance confirmation and longitudinal race learning remain pending.
- **Decision:** Add `wake.competition_review.v1` over the existing fictional club. Model event identity as competition, stage, race number, boat class, gender, category, and distance rather than race number alone. Link every internal entry to an exact crew snapshot, its athletes, physical boat, and pre-race shared outings; retain the complete fictional competitive field and published rank, including displayed-time ties and non-completions. Use the earlier same-federation programme only as a category-distance reference: 500 m for Beginner/Juvenile, 1,000 m for Aspirant/Junior/Master/Para-rowing, and 2,000 m for Senior. Mark stage-specific confirmation as unobserved. Keep every public identity, time, rank, and outcome fictional while the supplied official documents remain private reference material.
- **Rationale:** A regatta can close the training-to-outcome loop and make club-scale value visible, but copying real names into a synthetic training history would fabricate evidence and create a privacy problem. Category controls distance more reliably than boat size, repeated race numbers require a composite identity, and official order must remain authoritative when displayed times tie. Training history is useful context but does not establish that training, a lineup, or an athlete caused the result.

## 2026-08-30 - Save one bounded GPT memory over the combined club periods

- **Status:** accepted and executed once after explicit US$0.20 authorization.
- **Decision:** Preserve all 102 activity records through deterministic storage, then send one compact combined-club scope to the bounded WAKE agent instead of calling GPT once per activity. Include the complete two-period coverage, the six deterministic comparison routes, the prior verified investigations, evidence references, and explicit causal and modality boundaries. Use `gpt-5.6-terra` at medium reasoning with `store: false`, strict structured output, four read-only tools, deterministic verification, and local artifact persistence. Require one new finite US$0.20 operational start authorization; this is not a provider billing cap.
- **Rationale:** Raw records and supported numeric transformations should remain deterministic. GPT adds value by producing a coach-facing synthesis and priority memory across the period, while a single bounded call minimizes cost and prevents duplicated narratives from becoming the source of truth. The verified execution used all four tools, cost US$0.037384, and saved a 6,322-token report locally. Local persistence allows it to reopen without another paid request and avoids relying on provider-side application-state retention.

## 2026-08-30 - Validate the combined memory with one same-input direct baseline

- **Status:** accepted and frozen; direct baseline execution awaits a new finite authorization.
- **Decision:** Compare the saved bounded WAKE memory with one direct call over the byte-equivalent semantic 102-activity summary, same model configuration, and same strict output schema. Give the baseline no tools. Freeze a seven-check non-scored capability contract before execution and preserve a neutral or unfavorable outcome without changing the contract. Keep per-athlete and per-crew mass generation outside the submission unless this comparison exposes a specific missing product capability.
- **Rationale:** More generated prose does not itself validate club intelligence. One same-input comparison isolates whether tool-backed investigation changes supported-comparison coverage, abstention, environmental boundaries, priorities, questions, and deviation review. It adds stronger evidence at one paid start while retaining the selective-reasoning and deterministic-source-of-truth architecture.

## 2026-08-30 - Accept the same-input club result as structural fidelity evidence only

- **Status:** accepted and executed once after explicit US$0.20 authorization.
- **Decision:** Preserve the frozen 7/7 WAKE versus 3/7 direct-baseline capability audit unchanged, together with a separate manual construct-validity review. Accept only the claim that WAKE more reliably preserves canonical IDs, statuses, output placement, and review routes. Do not present this audit as a semantic coaching-quality score or human-coach comparison, and do not rescore it after inspecting the output.
- **Rationale:** The direct baseline expressed much of the same coaching content but used different identifiers, statuses, or sections for four checks. That makes the frozen audit valid evidence of machine-stable contract fidelity while limiting its validity as a broad measure of coaching quality. Keeping the original audit plus the limitation is more credible than changing the contract after seeing the result.

## 2026-08-30 - Separate owner QA data and isolate its local state

- **Status:** accepted; replay package and checklist implemented, live executions pending explicit finite authorization.
- **Decision:** Publish one upload-ready five-source derived-synthetic QA bundle and use the same folder for the two-source minimum-evidence path. Add an explicit dashboard `--state-store` option so owner QA can use isolated replay and live state without deleting or changing the normal local club state. Validate the interface in replay first, then run three separately authorized live starts: core Plan + SpeedCoach, complete five-source evidence, and core evidence with historical weather.
- **Rationale:** A visual walkthrough cannot prove ingestion, evidence gaps, persistence, live verification, or weather enrichment. A fixed public pack makes the file chooser reproducible, while isolated state prevents old answers from masking first-run behavior. Separate start gates keep the paid scope auditable.

## 2026-08-30 - Make the submission video product-first

- **Status:** accepted; rewritten script pending owner QA and rehearsal.
- **Decision:** Aim the five-minute video primarily at coaches and athletes: 85% product story and 15% technical proof. Lead with the operational problem, follow one session through athlete and coach collaboration, demonstrate value across the club and competition, and use the final minute for measured evaluation, one failure, and reproduction. Leave architecture, schemas, trajectories, tests, and exact commands in the repository rather than narrating them in the main product path.
- **Rationale:** The solution video must make the practical value understandable before asking judges to interpret implementation detail. Technical judges can inspect the source and documentation; the recording should establish why the workflow matters, then present only enough evidence to make its claims credible and satisfy the hackathon requirements.

## Pending decisions

- Live agent API deployment target and application-service boundary.
- Production database, encryption, backup, retention, authentication, and club tenancy.
- Schema revisions justified by parser and grader implementation evidence.
- Historical-weather commercial plan, reanalysis fallback, and precedence for station or on-boat measurements.
