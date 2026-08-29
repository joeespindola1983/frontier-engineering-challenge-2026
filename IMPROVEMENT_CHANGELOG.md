# Improvement Changelog

This changelog will connect every meaningful experiment to evidence produced with a consistent evaluation method. It begins before implementation so the project does not reconstruct its development story after the fact.

## Current status

Two reproducible evaluation cases, evaluation specification version 1.0, comparable baseline and agent runners, and deterministic grader v1.1 now exist. The first official comparison measured WAKE at 63.34/100 versus 38.86/100 for the direct baseline. The earlier paid single-case preflight remains excluded.

## Experiments

### 1. Discovery — rowing workflow

- **Hypothesis:** A rowing-specific workflow can recover valuable daily training context that dashboards and isolated device exports leave for coaches to reconstruct manually.
- **Change:** Defined the rowing bottleneck and an initial evidence-backed workflow before selecting an implementation stack.
- **Evaluation:** Domain interview notes were consolidated in the product brief. No quantitative evaluation was available at this stage.
- **Result:** The problem was specific enough to support a testable workflow rather than a generic sports dashboard.
- **Decision:** Keep the rowing domain and proceed to a fixture audit.
- **Next step:** Define the baseline and primary metric before implementing the final workflow.

### 2. Data audit — real hero fixture

- **Hypothesis:** A real multi-device session with conflicting clocks and metrics can demonstrate why WAKE must investigate evidence instead of trusting one file or averaging every sensor.
- **Change:** Audited the private export corpus and selected a three-device session containing matching, clock-offset, source-conflict, and missing-evidence failure modes. Built a minimized deterministic transformation rather than publishing raw files.
- **Evaluation:** `python3 scripts/verify_hero_fixture.py` checks public hashes, privacy invariants, 549 SpeedCoach strokes, mobile evidence availability, preserved clock offsets, and route-overlap p95 below 5 m.
- **Result:** Case 001 preserves the intended conflicts while removing private location, date, device, and athlete information. This is fixture evidence, not an agent-improvement score.
- **Decision:** Keep the transformed session as `case-001-misaligned-double-scull`.
- **Next step:** Freeze the rubric and a simple baseline before adding agent behavior.

### 3. Evaluation contract — synthetic case 002

- **Hypothesis:** A deterministic synthetic execution can provide exact ground truth for plan compliance, environmental change, and sensor failure without fabricating real athlete history.
- **Change:** Froze a 100-point rubric, registered 16 cases, created five versioned schemas, and generated a plan-versus-performance case with a wind shift, true SPM deviation, clock offset, distance bias, and failed mobile SPM.
- **Evaluation:** `python3 scripts/verify_synthetic_case.py` checks six work intervals, five valid recoveries, only `work-05` as a plan deviation, a wind transition inside `work-04`, a +37 s mobile clock offset, +1.2% mobile distance bias, and zero usable mobile SPM rows.
- **Result:** Case 002 is byte-reproducible and contains the intended failure modes. This is deterministic fixture evidence, not an agent score.
- **Decision:** Keep rubric v1.0 and `case-002-wind-shift-plan-deviation`.
- **Next step:** Do not count the fourteen planned cases until each fixture and its ground truth are implemented and verified.

### 4. TDD foundation — frozen baseline input

- **Hypothesis:** Freezing a compact, ground-truth-free input before model selection will make later baseline and agent comparisons reproducible and resistant to answer leakage.
- **Change:** Adopted RED-GREEN-REFACTOR, added unit and contract tests, normalized confirmed rowing vocabulary, and froze the compact input plus direct-call prompt.
- **Evaluation:** `python3 scripts/test_all.py` ran six deterministic tests and three public artifact verifiers at this stage. The RED run exposed a stale zone fixture and two testability defects before the GREEN implementation.
- **Result:** The compact summary contract, vocabulary rules, hashes, and leakage checks passed. This is engineering evidence, not an agent score.
- **Decision:** Keep the permanent TDD policy and the baseline v1 input boundary.
- **Next step:** Select the comparison model without changing frozen inputs after inspecting its answers.

### 5. Direct-call baseline runner

- **Hypothesis:** A single structured model call without tools, memory, retries, or verification provides a fair minimum baseline for measuring workflow value.
- **Change:** Configured a one-call Responses API runner with GPT-5.6 Terra at medium reasoning, strict structured output, explicit cost metadata, `store: false`, and opt-in paid execution.
- **Evaluation:** `uv run python scripts/test_all.py` passed ten tests and three artifact verifiers at this stage. A two-case dry-run produced hashed request previews of 21,550 and 48,218 bytes with `api_called: false`; execution without an API key was rejected.
- **Result:** The baseline is reproducible and safe to preview, but no real model output or quality score exists yet.
- **Decision:** Keep baseline runner v1 unchanged for the first comparison.
- **Next step:** Score it against the same frozen cases and grader used for WAKE.

### 6. Bounded agent tool loop

- **Hypothesis:** Giving the same model deterministic investigation tools and a claim verifier should improve evidence selection, abstention, and correction over the direct-call baseline.
- **Change:** Used RED-GREEN-REFACTOR to add four ground-truth-free tools, a bounded Responses API function loop, strict output verification, one correction retry, public-only input resolution, round limits, and observable trajectories. The model and reasoning settings remain equal to the baseline.
- **Evaluation:** RED runs failed first on missing modules, then on absent runner contracts, and finally on missing-evidence and source-identity verifier gaps. The final `uv run python scripts/test_all.py` passes 26 tests and three public verifiers. A two-case dry-run produced 24,124-byte and 50,792-byte requests with `api_called: false` and no ground-truth reference. Fake-client tests cover tool continuation, retry, stopping, and trajectory behavior.
- **Result:** The agent workflow is executable and its deterministic boundaries are tested. This is workflow-engineering evidence, not a model-quality score.
- **Decision:** Keep agent workflow v1 for the first controlled comparison.
- **Next step:** Implement the deterministic rubric grader from frozen ground truth before inspecting model answers, then execute baseline and agent cases under an explicit budget.

### 7. Deterministic rubric grader

- **Hypothesis:** A grader frozen before model inspection can measure baseline-versus-agent workflow value without adapting success criteria to whichever answer looks better.
- **Change:** Added a versioned 100-point grader configuration, output-schema validation, per-case applicable-dimension normalization, numeric tolerance checks, source selection, segment and deviation metrics, evidence and abstention checks, critical zero rules, macro-averaging, and an offline CLI. Added an explicit adapter for the legacy case 001 ground truth without rewriting that frozen artifact.
- **Evaluation:** RED runs first failed on the missing grader, exposed overly rigid clock-number parsing, then failed on missing schema/CLI contracts, the valid environment source rejected by the agent verifier, hard-coded rubric weights, and prohibited claims hidden in the coach briefing. The final `uv run python scripts/test_all.py` passes 39 tests and three public verifiers. Calibration outputs score 100 for both perfect case profiles; injected broken mobile SPM, causal wind, and visible-technique claims trigger the required zero rules; a false-positive deviation reduces precision to 0.5.
- **Result:** Grader v1 can score a complete two-case output directory offline and reports macro-average score, per-dimension points/reasons/evidence, secondary metrics, rubric version, and configuration hash. No real model score exists yet.
- **Decision:** Freeze grader v1 for the first controlled comparison.
- **Next step:** Run one paid preflight before the official two-arm comparison.

### 8. Paid preflight and grader calibration

- **Hypothesis:** A single excluded real-output preflight can reveal API-contract or generic evaluator failures before they invalidate the official baseline-versus-agent comparison.
- **Change:** The first request exposed a Structured Outputs incompatibility, so a RED regression test required an explicit `type` beside the constant schema version. One successful case-001 baseline output then exposed three representation gaps in grader v1.0. RED tests added support for connected pairwise source matches, common metric aliases, and explicit “unassessable” language; grader v1.1 records those changes while preserving v1.0.
- **Evaluation:** The invalid-schema request returned HTTP 400 before generation. The successful preflight used case 001 only and cost US$0.039722 for 3,835 input and 2,671 output tokens. Its unchanged answer scored 3.71 under v1.0 and 73.71 under v1.1; the difference came from generic equivalence handling, while missed human-confirmed boat context and unnecessary questions remained penalized. The final suite passes 43 tests and three public verifiers.
- **Result:** The schema is accepted by the live API, calibration history is auditable, and grader v1.1 is frozen before either official comparison arm. The preflight output and cost manifest are retained but excluded from the official score.
- **Cost/runtime:** US$0.039722 and 24,187 ms for the successful preflight; the rejected schema request generated no model output.
- **Decision:** Keep the schema correction and grader v1.1; remove the preflight from official comparison membership.
- **Learning:** Deterministic grading still needs semantic-equivalence calibration, but corrections must be versioned and made before inspecting official results rather than patched after seeing a winner.
- **Next step:** Execute fresh two-case baseline and agent runs, then grade both without changing v1.1.

### 9. Official baseline versus bounded WAKE agent

- **Hypothesis:** Deterministic investigation tools plus evidence verification will improve session reconstruction, metric-level trust, deviation detection, and abstention over a direct structured call with the same model.
- **Change:** No code, prompt, fixture, ground truth, or grader change was made between arms. The direct baseline and bounded WAKE agent each processed the same two public summaries using GPT-5.6 Terra at medium reasoning. Both output directories were scored offline with grader v1.1 and configuration hash `a3f3d526124d0c5b7687ef38b48dfc52a82f0291af7a718884540b0dcbc32d87`.
- **Evaluation:** Baseline scored 38.86/100 macro-average (case 001: 38.71; case 002: 39.00). WAKE scored 63.34/100 (case 001: 47.04; case 002: 79.64), an absolute gain of 24.48 points and a 63.0% relative gain. In case 002, WAKE achieved perfect deviation precision/recall, reconstructed all 11 segments with 2.5 s mean boundary error, and improved trusted-source accuracy from 0.0 to 0.6. All eight tool calls completed; the verifier rejected case 001 once for missing evidence references and the bounded retry passed.
- **Result:** The agentic workflow materially outperformed the direct-call baseline on the fixed implemented cases, with the strongest evidence in the plan-versus-execution case. Case 001 remained weak because it missed confirmed human context, over-asked questions, and received no evidence/abstention credit.
- **Cost/runtime:** Baseline used 22,735 tokens and cost US$0.109940. WAKE used 50,694 tokens and cost US$0.172278. Incremental agent cost was US$0.062338; total official comparison cost was US$0.282218. Baseline per-case runtimes were recorded (22,429 ms and 35,771 ms); agent v1 did not record a reliable end-to-end runtime and none is inferred.
- **Decision:** Keep the bounded single-agent tool loop as the demonstrated workflow. Do not add more agents until a fixed-case experiment justifies their complexity.
- **Learning:** Deterministic segmentation and source-selection tools created the largest measurable gain. The next quality bottlenecks are context recovery, compact required questions, and explicit abstention phrasing—not additional dashboard surface area.
- **Validity note:** Only two cases are implemented. After the freeze, both case-001 outputs also exposed that grader v1.1 treats some negative phrases such as “cannot be evaluated” as a technique assertion. The grader was not changed after official results; this limitation is documented for a future version and affects the absolute case-001 scores.
- **Next step:** Add runtime observability through TDD, improve human-context handling without leaking evaluator truth, and implement additional fixed cases before claiming broader generalization.

### 10. Agent runtime observability

- **Hypothesis:** Separating per-case investigation time from end-to-end run time will make latency and orchestration overhead reproducible without altering model behavior or historical evidence.
- **Change:** Added UTC start/finish timestamps, monotonic `runtime_ms`, and approximate cost to each successful trajectory. Added end-to-end `runtime_ms` and `case_runtime_ms_total` to future run manifests through a pure manifest builder. Historical comparison-v1 artifacts were not modified.
- **Evaluation:** RED tests first failed because `run_agent_case` had no injectable monotonic clock and no run-manifest builder existed. GREEN tests use fixed timestamps and monotonic values to verify 750 ms case duration, 1,250 ms total duration, 1,000 ms summed case duration, token aggregation, and exact pinned-cost calculation without network calls. The complete suite passes 44 tests and three public verifiers.
- **Result:** Future paid runs will expose auditable case latency, total elapsed time, runner overhead, tokens, and cost in their native artifacts.
- **Cost/runtime:** No API calls and no model cost were required for this instrumentation experiment.
- **Decision:** Keep the two-level runtime contract and preserve the earlier official run unchanged.
- **Learning:** Runtime is an observable workflow property and should be designed like any other evidence contract, not inferred later from terminal duration.
- **Next step:** Validate the complete suite, then use the prepared interface direction as the basis for the first product-facing slice.

### 11. Coach-facing product replay

- **Hypothesis:** A minimal coach-first flow can make the agentic value understandable without turning benchmark controls into the product or inventing longitudinal data.
- **Change:** Integrated the supplied interface direction as a React/Vinext product slice: inbox, intake, session review, metric-trust disclosure, one human equipment checkpoint, verified briefing, and approval-gated goal memory. Added a compact replay adapter derived from committed case-002 output. Corrected the prototype's causal wind language, removed fabricated session history, and kept evaluation ground truth outside the browser.
- **Evaluation:** RED tests first failed on the absent replay adapter, compact-data mismatch, and missing workflow state. GREEN tests verify exact fidelity to the committed six work intervals, work-05 deviation, metric-level trust, noncausal environmental wording, preservation of unknown equipment, human-confirmation provenance, and explicit approval before memory. Six web tests, ESLint, and the production build pass. A dependency audit initially reported 13 vulnerabilities; compatible upgrades reduced the final audit to zero.
- **Result:** The complete product path is demonstrable with truthful synthetic evidence and without exposing fixture, baseline, grader, or trajectory concepts in normal navigation. It remains a replay: uploads, backend checkpoint persistence, authentication, and durable goal memory are not implemented.
- **Cost/runtime:** No model or API call was required. The final deterministic web test suite completes locally in under one second; build time is environment-dependent and not used as a product-latency claim.
- **Decision:** Keep the coach-first interface and replay boundary for the five-minute demonstration. Replace the adapter with a task-level service only after its API and persistence policy are tested.
- **Learning:** The interface itself is an evidence boundary. Claims become more trustworthy when source choice, unknowns, human confirmation, and approval are visible without forcing the coach to inspect the full agent trace.
- **Next step:** Record the five-minute demonstration, then replace the replay adapter with a tested task-level service only if the remaining hackathon time permits.

### 12. Task-level product runtime boundary

- **Hypothesis:** Connecting the coach interface to task-level operations can demonstrate a real agent runtime without exposing tools in the browser or turning an ordinary click into an implicit paid call.
- **Change:** Added a process-local Python product service for investigation creation, checkpoint answers, briefing approval, and goal retrieval. Added an asynchronous web client with replay and HTTP adapters. Replay remains the default; live execution requires server `--allow-live`, client `live` mode, and `OPENAI_API_KEY`. The service reuses the bounded runner and preserves its normal trajectory output.
- **Evaluation:** RED began with missing Python service and JavaScript client modules. A second RED caught an incorrect checkpoint route, and a third converted an oversized HTTP response into a compact product contract. Seven Python service tests and four new client tests now cover replay/live boundaries, task-level routes, checkpoint provenance, preserved telemetry, unknowns, approval-gated memory, compact context, and visible HTTP errors. A real localhost sequence completed investigation, `UNKNOWN` checkpoint, and approval without an API call.
- **Result:** The interface can use the same asynchronous contract for free hosted replay or a local live WAKE investigation. The browser never receives evaluator ground truth or low-level tool controls. Hosted Python execution, uploads, authentication, and durable state remain unimplemented.
- **Cost/runtime:** No model call and no API cost. HTTP replay latency was checked only as functional local behavior and is not presented as a benchmark.
- **Decision:** Keep the task-level service and explicit three-part live opt-in. Do not enable live calls by default or move evidence reasoning into the frontend.
- **Learning:** A product API should compress agent evidence for the user task just as deterministic tools compress raw sensor data for the model.
- **Next step:** Validate the complete repository, publish the replay-compatible interface update, and prepare the live local demonstration command for the video.

### 13. Independent source intake with replay isolation

- **Hypothesis:** A real intake boundary can make the product workflow more functional while preventing a novel file from receiving a canned analysis that belongs to the public demonstration case.
- **Change:** Added five typed process-local source uploads for plan, SpeedCoach, mobile, environment, and context. The service validates filenames, a 10 MiB size limit, JSON schemas or minimum fields, telemetry columns, and recognized SpeedCoach/WAKE mobile formats; records SHA-256 provenance; returns metadata only; and accepts five source ids for investigation creation. The web intake can replace the ready sample files when a local runtime is configured. Source-based replay requires an exact byte match to public case 002.
- **Evaluation:** RED first failed on missing `upload_source`, `POST /api/sources`, client upload behavior, and the evidence-intake module. GREEN now includes seven new Python ingestion/API tests and three new JavaScript intake tests covering the exact public bundle, malformed plans, incomplete telemetry, path traversal, raw vendor/mobile detection, modified-bundle rejection, Base64 upload, stable source order, and all-or-nothing browser submission. The product-service suite has 14 tests and the web suite has 14 tests; final repository verification is recorded with the completing commit.
- **Result:** WAKE now receives evidence as independent typed inputs through a task-level boundary instead of merely drawing four filenames. A changed file cannot inherit committed conclusions. Recognition of a raw format is deliberately not presented as end-to-end parsing or live analysis.
- **Cost/runtime:** No model call and no API cost. Runtime was exercised only as deterministic local behavior and is not reported as a performance benchmark.
- **Decision:** Keep process-local intake and exact replay isolation. Do not accept private hosted uploads or claim arbitrary-bundle investigation until normalization, storage, identity, and tenancy are separately tested.
- **Learning:** Provenance begins before agent reasoning. File identity, format validation, and replay eligibility are part of the evidence model, not generic upload plumbing.
- **Next step:** Build the deterministic raw-to-normalized adapter for a new bundle, beginning with SpeedCoach vendor and WAKE mobile sensor CSVs, then assemble a ground-truth-free compact case summary for explicitly enabled live execution.

### 14. Raw telemetry normalization with preserved missingness

- **Hypothesis:** Converting device-specific telemetry into one deterministic representation will enable later cross-source reasoning, but only if the adapter preserves missing measurements and clock uncertainty instead of smoothing them away.
- **Change:** Added a raw source adapter for SpeedCoach vendor per-stroke CSV, pre-existing WAKE mobile sensor CSV, and already canonical telemetry. Each accepted file produces a deterministic seven-column CSV and a `wake.source_normalization.v1` report containing source reference, input/normalized hashes, row counts, rejected rows, timing, duration, maximum distance, GPS rows, positive SPM rows, and quality flags. The product service normalizes telemetry at upload time and exposes only safe metadata through `GET /api/sources/:id`.
- **Evaluation:** RED failed first because `source_adapters` did not exist, raw upload metadata had no normalization report, and the source metadata endpoint was absent. Later REDs required input hash provenance, a versioned report schema, and rejection of non-finite numeric values. Six adapter tests and one new product-service test now cover 549 SpeedCoach strokes, 923 mobile samples, canonical columns, deterministic bytes, malformed vendor rejection, declared-kind enforcement, metadata-only HTTP output, UTC mobile timestamps, unknown SpeedCoach timezone, blank mobile SPM preservation, and `NaN` rejection. Final repository verification is recorded with the completing commit.
- **Result:** WAKE can now parse the two public raw telemetry formats into a comparable internal stream without sending raw rows to a model or browser. It correctly distinguishes present, zero-only, and absent SPM. This does not yet match sources, infer a timezone, build a new compact case summary, or execute a new uploaded bundle.
- **Cost/runtime:** No model call and no API cost. Parser runtime was tested only as deterministic local behavior and is not presented as a benchmark.
- **Decision:** Keep source normalization v1 and the quality-report schema. Do not repair missing SPM, infer local timezone, or claim live new-bundle support.
- **Learning:** The most important parser output is sometimes not a metric but a boundary: which values exist, which were rejected, and which clock assumptions remain unresolved.
- **Next step:** Assemble plan, normalized telemetry, environment, and context into a ground-truth-free compact case summary, including candidate alignment evidence, before enabling explicitly paid live investigation for new uploads.

### 15. Deterministic five-source compact-summary preparation

- **Hypothesis:** A new upload can become safe agent input without a canned result or a model call if deterministic assembly preserves conflicts, uncertainty, and provenance instead of collapsing the sources into one assumed truth.
- **Change:** Added `bundle_assembler.py` and `POST /api/source-bundles/prepare`. The assembler joins one plan, SpeedCoach stream, mobile stream, environment timeline, and context document into `wake.case_summary.v1`; records original and normalized hashes, keeps service-authenticated upload identities ahead of context labels, preserves missing or zero-only SPM; computes compatible clock offset, cumulative-distance conflict, and bidirectional GPS overlap; projects environmental wind against a known route heading; aggregates only the SpeedCoach stream into compact 30-second windows; and emits human-only evidence gaps. The service validates the result, stores it in process memory, and returns metadata rather than rows or the full summary. Unknown route heading now makes the environment tool abstain instead of failing or inventing boat-relative wind.
- **Evaluation:** RED began with missing assembler and preparation-service methods. Six initial assembler tests and three product-service tests required schema validity, no evaluation-answer leakage, deterministic output, a 37-second clock offset, 1.2% distance conflict, route p95 below 25 m in both directions, preserved broken mobile SPM, changing summary hashes for changed evidence, metadata-only HTTP output, and zero live-runner calls. A later RED exposed the missing-route-heading crash and added explicit abstention. The final Python suite passes 75 tests and all three public verifiers.
- **Result:** Any valid five-source local bundle can now receive its own agent-ready summary and content identity without inheriting the public replay or spending API budget. This is preparation, not new-bundle agent execution, durable storage, or proof of broad source matching.
- **Cost/runtime:** No model call and no API cost. Deterministic execution was verified locally but is not reported as a performance benchmark.
- **Decision:** Keep assembly version 1 as an explicit no-cost checkpoint. Require a separate explicit execution path before a prepared bundle may reach the paid bounded agent.
- **Learning:** The safe bridge from sensors to an agent is itself an intelligence layer: it must know when clocks are comparable, when GPS can corroborate identity, which measurement is broken, and which rowing facts still require a human.
- **Next step:** Add an explicitly authorized prepared-bundle live runner with isolated temporary evidence files and the same trajectory/verifier guarantees, then expose it to the local interface only behind deliberate paid opt-in.

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
