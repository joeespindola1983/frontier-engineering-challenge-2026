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

### 16. Explicit prepared-bundle execution boundary

- **Hypothesis:** A prepared bundle can reuse WAKE's evaluated bounded agent safely if paid execution is a separate explicit action, normalized evidence is isolated from uploads, and repeated requests do not silently spend twice.
- **Change:** Added an injected prepared-bundle runner, `POST /api/source-bundles/:id/execute`, analysis-schema and case-identity validation, isolated temporary evidence files, normal output/trajectory persistence, and same-process idempotence. The route rejects every mode except literal `live`; the production runner is absent unless the service starts with `--allow-live` and still requires `OPENAI_API_KEY`. It does not alter the committed replay path or teach the browser to invoke the new route.
- **Evaluation:** RED failed across the product-service suite because the new runner injection did not exist. The new behavior test then required a refused implicit execution, zero calls before explicit authorization, canonical five-file evidence passed to the runner, a validated final analysis, no use of the legacy case runner, and a second request returning HTTP 200 with the same result and no second runner call. The product-service suite passes 19 tests; the full Python suite passes 76 tests and three public verifiers.
- **Result:** A novel valid local bundle now has a complete technical path from typed upload to normalized compact evidence to bounded agent execution. The path is callable but deliberately not wired into the current coach UI, and no live model request was made during this experiment.
- **Cost/runtime:** No model call and no API cost. The execution boundary was exercised with an injected deterministic fake; real latency and cost remain unmeasured for new bundles.
- **Decision:** Keep explicit live-only execution and same-process idempotence. Do not expose the action in the coach interface until a generic analysis-to-review adapter removes case-002 assumptions.
- **Learning:** The paid-action boundary is part of agent reliability. A correct agent loop is insufficient if upload identity, normalized evidence lifetime, output validation, and duplicate-request behavior are ambiguous.
- **Next step:** Build a generic coach review adapter from prepared summary plus verified analysis, then connect prepare/execute/review in the local interface while keeping replay as the hosted default.

### 17. Generic verified-analysis review adapter

- **Hypothesis:** A live new-bundle result becomes product functionality only when the coach review is derived from that bundle rather than restyled as the six-by-one-kilometer demonstration.
- **Change:** Prepared execution now returns a compact review bundle with verified analysis, plan, authenticated source identities and quality, cross-source findings, minimal environment identity, and session context while excluding hashes and time-series windows. The HTTP client adds an explicit `analyzeSourceBundle` prepare/execute/adapt operation and refuses non-live mode before network access. The review adapter now derives work count and distance, boat and crew label, provenance, source display names, clock visibility, environment fallback, status, checkpoint question, and reconstruction copy. The page consumes reconstruction and state from the review, hides absent clock data, removes the fixed fourth-interval wind marker, and no longer labels every live run synthetic.
- **Evaluation:** RED failed on the missing backend review, absent client operation, environment-policy assumption, and case-002-only page narration. GREEN tests add a women's `1x` plan with four 500 m repetitions, uploaded source IDs, one different deviation, no clock finding, and no environment; verify compact backend output; verify the exact two-request live client sequence and zero requests for replay mode; and scan the page boundary for adapter-driven reconstruction with no fixed work-count or wind-marker text. The Python suite remains at 76 tests; the web suite passes 18 tests, ESLint, and the production build.
- **Result:** WAKE can transform a prepared verified result into a truthful generic review model without leaking telemetry rows or replay assumptions. The callable client path is complete through review adaptation, but the page deliberately does not invoke it until generic checkpoint and briefing transitions exist.
- **Cost/runtime:** No model call and no API cost. Client execution used deterministic fake responses.
- **Decision:** Keep the generic review adapter and compact response. Do not connect custom live uploads to the page while its completion and memory stages still assume resistance-band case 002.
- **Learning:** UI hard-coding is an evidence failure, not merely a design limitation: it can convert a correct agent result into a false coach-facing claim after verification has already passed.
- **Next step:** Generalize checkpoint answers, verified briefing findings, and goal-memory proposals from the adapted review; then enable the page's custom live path under its existing local-runtime and live-mode opt-ins.

### 18. Progressive evidence instead of mandatory mobile telemetry

- **Hypothesis:** Plan + SpeedCoach should support the core planned-versus-performed workflow, while mobile, environment, and context should add measurable capabilities without becoming adoption blockers.
- **Change:** Replaced exact five-source preparation with a progressive evidence contract. Plan and SpeedCoach are core; mobile, environment, and context are optional enhancers. The assembler creates neutral missing context, computes cross-source findings only when prerequisites exist, records capability gaps, and never invents route corroboration. Preparation returns ordered source coverage, live execution receives only supplied evidence, and the intake labels core versus optional sources. Exact five-source identity remains mandatory only for committed replay reuse.
- **Evaluation:** RED tests first failed because the assembler and service required all five sources and the browser rejected partial bundles. A second RED caught misleading single-source route language. GREEN tests cover schema-valid minimum preparation, deterministic generated context, explicit missing mobile/environment/context gaps, single-source route confidence without false corroboration, rejection when either core source is absent, optional-file upload order, and minimum-bundle execution with only `plan.json` and `speedcoach.csv`. The final repository verification passes 81 Python tests, three public verifiers, 19 web tests, ESLint, and the Vinext production build.
- **Result:** The runtime now matches the product thesis: WAKE works with common club evidence and becomes more capable as corroborating sources arrive. The existing full public case and replay isolation remain intact. This change does not yet measure the marginal model-quality gain from mobile evidence.
- **Cost/runtime:** No model call and no API cost. The complete Python test and verifier command completed locally in 12.777 seconds of unittest runtime; web tests completed in 0.215 seconds. Build time is not used as a product-performance claim.
- **Decision:** Keep the progressive evidence contract. Evaluate it with a same-case evidence ablation before claiming mobile value in the final submission.
- **Learning:** A source can be important without being mandatory. Product confidence should degrade explicitly by capability rather than collapsing into an all-or-nothing upload requirement.
- **Next step:** Generate frozen reduced-evidence variants of the implemented case and run the same bounded workflow to quantify the marginal value of context, environment, and mobile evidence.

### 19. Frozen progressive-evidence ablation inputs

- **Hypothesis:** Freezing three inputs over the same synthetic session can isolate the evidence variable before any model call and prevent later prompt, case, or source changes from being mistaken for mobile value.
- **Change:** Added a deterministic ablation generator and committed `core`, `context-environment`, and `full` compact summaries plus a versioned manifest. Every condition records its summary hash, source files, available capabilities, and distinct run-safe case identity. The generator uses public fixtures and production normalizers/assembler without reading evaluator answers.
- **Evaluation:** RED failed on the missing generator module. GREEN tests rebuild two directories byte-for-byte, scan generated JSON for evaluator-answer leakage, validate the condition order and shared base-session identity, assert the expected source/environment/cross-source boundaries, and verify every manifest hash. Final verification passes 83 Python tests, three public verifiers, 19 web tests, ESLint, and the Vinext production build.
- **Result:** Reproducible no-cost inputs now exist for the next ablation run. They demonstrate evidence removal correctly but do not yet constitute a model-quality result.
- **Cost/runtime:** No model call and no API cost. Generation uses only deterministic local adapters and schema validation.
- **Decision:** Keep ablation input version 1 frozen. Do not edit it after outputs are visible; create a new version instead.
- **Learning:** A fair source-value experiment begins with immutable evidence conditions, not with comparing whichever outputs happen to be available.
- **Next step:** Implement one versioned runner and condition-aware scorer, dry-run all three requests, then explicitly authorize a paid run before reporting mobile value.

### 20. All-condition ablation runner and capability reporter

- **Hypothesis:** Running every frozen condition through the same bounded workflow and scoring only applicable capabilities will measure progressive-evidence behavior without rewarding extra files automatically or penalizing deliberate source removal.
- **Change:** Added a default-no-cost ablation runner, exact manifest/summary/evidence hash validation, per-condition temporary evidence isolation, an all-or-nothing explicit execution path, normal trajectories and cost manifests, and a condition-aware deterministic reporter. The reporter verifies common execution, provenance, human boundaries, appropriate environmental abstention/association, noncausal language, mobile session/route corroboration, and broken mobile SPM rejection. It also compares execution/deviation signatures across conditions and intentionally emits no overall score.
- **Evaluation:** RED first failed on the absent runner, then on the absent reporter. GREEN tests cover three-request dry-run with no client, exact two/four/five-file isolation, frozen-hash rejection, aggregate runtime/token manifests, a passing capability report, rejection of a mobile citation in the core condition, rejection of causal wind language, and rejection of mobile as the SPM source. Final verification passes 89 Python tests, three public verifiers, 19 web tests, ESLint, and the Vinext production build.
- **Result:** The complete experiment path exists from immutable inputs to inspectable requests, explicit execution, and a capability-level report. A committed dry-run preflight makes the exact requests auditable. No live result exists yet.
- **Cost/runtime:** No model call and no API cost during implementation or preflight. Final deterministic verification is recorded with the completing commit.
- **Decision:** Keep the all-condition runner and capability report. Do not publish an ablation conclusion until the paid run completes and the report passes or documents failures.
- **Learning:** Evidence value is best expressed as reliable capabilities unlocked while core conclusions remain stable, not as a score that rises simply because the model received more data.
- **Next step:** Commit this frozen runner/reporter milestone, explicitly execute all three requests once, score the outputs, and preserve failures without changing the v1 contract.

### 21. Official evidence ablation v1 and preserved core failure

- **Hypothesis:** Core plan + SpeedCoach should preserve the correct plan-execution result, while environment/context and mobile should unlock additional supported capabilities without changing the core deviation identity.
- **Change:** Executed all three frozen conditions once at commit `d8aa3c8` and generated the offline capability report. After the first scorer attempt crashed on a null `segment_ref`, added a failing regression test and changed only signature normalization so the unexpected deviation is reported rather than hidden. Refined two reporter predicates to distinguish explicit absence of mobile corroboration from false positive corroboration and negated causal warnings from causal assertions. Frozen inputs, model outputs, trajectories, prompt, and capability checks were not altered.
- **Evaluation:** Core passed 7/8 checks and failed `DEVIATION_DETECTION`; context/environment passed 10/10; full passed 12/12. Core added `RECONSTRUCTED_WORK_DISTANCE_SHORTFALL` with a null segment reference based on telemetry-derived segmentation margins, so cross-condition execution consistency failed. The full condition correctly matched mobile with SpeedCoach, corroborated the route, and rejected zero-only mobile SPM. All three agent outputs passed the normal schema/provenance verifier; core required one bounded retry after its first draft emitted evidence-less unavailable-source items. The scorer regression and repository verification pass 90 Python tests, three public verifiers, 19 web tests, ESLint, and the Vinext production build.
- **Result:** Overall ablation status is `FAIL`. The run supports the intended environment and mobile capabilities in this one synthetic session, but it also proves that the minimum evidence path can overinterpret derived segment distance. It does not support a human-coach comparison or athletic-performance claim.
- **Cost/runtime:** GPT-5.6 Terra medium; 83,452 input tokens, 10,975 output tokens, 94,427 total tokens; US$0.298604 total; 92.650 seconds end to end. Per condition: core US$0.121974 / 40.957 s, context-environment US$0.088216 / 26.301 s, full US$0.088414 / 25.369 s.
- **Decision:** Preserve the failing v1 run. Create a new workflow iteration that explicitly labels segment distances as boundary-derived and not sufficient evidence of completed-distance shortfall.
- **Learning:** Less evidence did not merely reduce confidence; it changed the model's interpretation of a deterministic intermediate value. Tool outputs must encode what a derived metric is not allowed to prove, not only its numeric value.
- **Next step:** Add a failing tool/prompt regression for distance-assessment scope, implement the smallest boundary change, and dry-run a v2 ablation before deciding whether a second paid run is justified.

### 22. Versioned v2 distance-assessment boundary

- **Hypothesis:** The core workflow will stop converting SPM-segmentation margins into a completed-distance shortfall if the limitation is encoded consistently in deterministic evidence, agent instructions, and output verification.
- **Change:** Preserved v1 and added a selectable v2 tool contract, config, and prompt. The v2 reconstruction result marks prescribed-distance completion `INSUFFICIENT`, explains that segment distances exclude transition samples, and cites the plan and SpeedCoach. The tool description and prompt prohibit summing those values. The verifier rejects any v2 distance-completion deviation from this boundary, and the ablation runner/scorer record and apply the selected workflow version.
- **Evaluation:** RED first failed because the reconstruction tool did not accept v2; the request still exposed the v1 description; the runner did not accept `workflow_version`; the verifier accepted the original distance-shortfall shape and then accepted the same claim with a segment reference; and the scorer applied v1 verification to a v2 run. Each boundary received the smallest passing change. The committed preflight contains the exact three v2 requests over unchanged frozen inputs with `api_called: false`; a compatibility regeneration produced byte-identical v1 request hashes. Final verification passes 96 Python tests in 10.348 seconds, three public verifiers, 19 web tests, ESLint, and the Vinext production build.
- **Result:** The deterministic candidate now prevents the observed failure before, during, and after model generation while leaving v1 selectable. This is request and contract evidence only; no paid v2 output or quality result exists.
- **Cost/runtime:** No model call and no API cost. Local test runtime is recorded by the completing commit, not presented as product performance.
- **Decision:** Keep the v2 candidate and no-cost preflight. Do not claim that it fixes model behavior until the same three-condition paid comparison is executed and scored.
- **Learning:** A limitation discovered in a tool-derived number should be machine-readable and verifier-enforced, not left as a prompt-only caution.
- **Next step:** Run the full repository suite, commit the v2 candidate, then decide whether the expected roughly US$0.30 repeat experiment is justified.

### 23. Official v2 ablation repeat

- **Hypothesis:** The versioned distance boundary will remove the unsupported core shortfall while preserving the same correct SPM deviation and the optional capabilities demonstrated by context/environment and mobile evidence.
- **Change:** Executed all three frozen conditions once at commit `3bc0cbd` with workflow v2, then generated the same condition-aware capability report offline. Added a committed-artifact regression test that recalculates the official report and requires the passing workflow version, condition counts, and cross-condition consistency.
- **Evaluation:** Core passed 8/8, context/environment passed 10/10, and full passed 12/12. Every condition reconstructed six work intervals and reported work-05 as its only plan deviation. Cross-condition consistency passed. Context/environment retained noncausal wind association and the human equipment boundary; full retained SpeedCoach/mobile matching, route corroboration, and zero-only mobile-SPM rejection. Core and context/environment each required one verifier retry for evidence-less unavailable/insufficient items unrelated to distance; full required no retry. Final verification passes 97 Python tests in 10.247 seconds, three public verifiers, 19 web tests, ESLint, and the Vinext production build.
- **Result:** Overall v2 ablation status is `PASS`, compared with v1 `FAIL` on the same frozen evidence conditions and capability checks. The result supports the specific distance-boundary correction and progressive-evidence workflow in this one synthetic session. It does not establish broad generalization, human-coach superiority, or improved athletic performance.
- **Cost/runtime:** GPT-5.6 Terra medium; 101,338 input tokens, 13,000 output tokens, 114,338 total tokens; US$0.358676 total; 92.202 seconds end to end. Per condition: core US$0.119132 / 34.677 s, context-environment US$0.151718 / 38.289 s, full US$0.087826 / 19.219 s. V2 cost US$0.060072 more and used 19,911 more tokens than v1; this difference is observational and not attributed solely to the workflow change.
- **Decision:** Accept v2 for the demonstrated workflow and preserve both official runs. Continue presenting mobile as an optional capability enhancer rather than a core requirement.
- **Learning:** The strongest improvement was not more evidence or more agents; it was making a deterministic limitation explicit at the tool, prompt, and verifier boundaries, then testing that correction against the failure that exposed it.
- **Next step:** Finish the generic checkpoint/briefing product path or prepare the submission narrative and video around the measured v1-to-v2 improvement, depending on remaining hackathon time.

### 24. Generic live product completion path

- **Hypothesis:** A custom live bundle is not a functional product path unless its verified analysis can continue through a bundle-specific human checkpoint, briefing, and approval-gated memory proposal without inheriting the demonstration story.
- **Change:** Prepared execution now registers a process-local investigation and returns investigation, checkpoint, and goal identifiers with its compact review. The service derives planned targets, session title, work findings, deviations, environmental boundary, human confirmation, and memory proposal from the new bundle. The generic `humanConfirmation` contract replaces the resistance-band-specific `equipment` field. The web live-upload path now invokes prepare/execute, retains the returned checkpoint, completes the server-owned transition, and renders the approved session date and confirmation from that result. Hosted replay remains the default.
- **Evaluation:** RED first failed because prepared execution returned no investigation identifiers and the service hard-coded six 1 km repetitions, the fifth interval, and resistance-band wording. A new behavioral case uses a two-by-500 m plan at 25–27 SPM with a different equipment-malfunction question and rejects every case-002 phrase. Diff review added another RED that caught a deviation numbered by list position instead of its real work interval. Separate web RED tests required the live page invocation, returned runtime identifiers, generic checkpoint copy, generic memory, and correct singular wording. GREEN passes 98 Python tests, three public verifiers, 21 web tests, ESLint, the Vinext production build, and an npm audit with zero vulnerabilities.
- **Result:** A locally selected plan + SpeedCoach bundle, with optional enhancers, can now travel through the complete coach-facing live workflow after explicit authorization. The synthetic hosted replay still works. State, uploaded bytes, briefings, and memory remain process-local and disappear when the service or browser restarts.
- **Cost/runtime:** No model call and no API cost. The live product transition was exercised with an injected deterministic agent result; no latency or quality claim is made for a real custom-bundle model run.
- **Decision:** Keep generic human confirmation and enable the page path only under the existing local runtime plus live-mode opt-ins. Do not describe process-local approval state as durable club memory.
- **Learning:** Agent correctness can be lost after model verification if downstream product state inserts fixture-specific meaning. Checkpoint and memory transformations therefore need the same evidence-driven tests as tools and prompts.
- **Next step:** Define and document the per-session cost envelope and execution-budget observability, then prepare the submission narrative and demonstration using replay for reliability and one explicitly authorized live path only if needed.

### 25. Live cost authorization and observable execution ledger

- **Hypothesis:** A deliberate per-session authorization plus post-run usage evidence will prevent silent live spend and make the solution's scaling trade-off legible without falsely presenting an application-side value as a provider billing cap.
- **Change:** Added a configurable positive finite US$0.20 operational start gate to prepared-bundle execution; trajectory-derived token, runtime, and approximate-cost output; an explicit authorization-overrun status; a same-process ledger that counts idempotent repeats once; and a cost summary endpoint. The HTTP client refuses missing authorization before network access. The intake explains the gate, and the review shows actual approximate cost and token use. `docs/COST_MODEL.md` records official price sources, observed references, projections, limitations, and a quality-preserving optimization order.
- **Evaluation:** RED tests first showed that a prepared bundle could reach the runner without a dollar authorization, production artifacts lost their trajectory cost at the product boundary, repeated requests could not be audited, the client issued a request without authorization, and the review hid spend. Later REDs rejected `NaN`/infinite configuration and required an overrun warning. GREEN covers service configuration, pre-run rejection, runner envelopes, idempotent aggregation, HTTP input/output, production artifact loading, client refusal, and UI disclosure. Final verification passes 103 Python tests, three public verifiers, 23 web tests, ESLint, the Vinext production build, and an npm audit with zero vulnerabilities.
- **Result:** A new live upload cannot start without deliberate cost authorization, and a completed run carries auditable spend evidence from the trajectory into the coach review and process ledger. The gate does not stop a request at an exact dollar value, and the ledger is not durable accounting.
- **Cost/runtime:** No model call and no API cost. Tests use an injected trajectory matching the preserved full-evidence v2 observation (US$0.087826, 30,583 tokens, 19.219 seconds) without claiming it as novel-upload performance.
- **Decision:** Keep the US$0.20 operational authorization and US$0.15 planning reference. Preserve replay and deterministic preparation as free defaults. Evaluate cost optimizations only against frozen quality and abstention checks.
- **Learning:** Product cost safety requires two separate truths: permission before execution and provider-reported usage after execution. Conflating them would turn a UI setting into a false hard-cap guarantee.
- **Next step:** Run complete repository verification, then assemble the submission narrative and five-minute demonstration around the measured workflow improvement, transparent cost, and one reliable replay path.

### 26. Product live runtime alignment with accepted workflow v2

- **Hypothesis:** The live product path must load the accepted v2 assets explicitly or it can reintroduce the boundary-derived distance failure already fixed and measured in the evaluation workflow.
- **Change:** Added one product-workflow asset loader and made both fixed-case and prepared-bundle live runners use `wake-agent-v2.json` with `wake-agent-v2.md`. The historical v1 artifacts and generic agent CLI defaults remain unchanged for reproducibility.
- **Evaluation:** RED failed because the product service exposed no accepted-workflow loader and still imported the v1 defaults. GREEN requires config version v2, tool contract v2, and the v2 distance-boundary instruction before either live runner is constructed. Final verification passes 104 Python tests and three public verifiers; the prior 23 web tests, ESLint, production build, and zero-vulnerability audit remain valid because this correction changes only the Python runner asset selection.
- **Result:** A product live execution now uses the same versioned distance boundary that passed the official v2 ablation instead of silently falling back to v1.
- **Cost/runtime:** No model call and no API cost. This is a deterministic runtime-selection correction.
- **Decision:** Keep explicit v2 product assets and preserve v1 only where historical compatibility is intentional.
- **Learning:** Accepting a workflow version in evaluation is insufficient unless every production entry point names that version rather than inheriting a generic default.
- **Next step:** Prepare the submission narrative and demonstration, then run a final rehearsal without relying on an unmeasured novel-upload call.

### 27. Browser rehearsal and truthful SPM chart geometry

- **Hypothesis:** The interface is demonstration-ready only if the real browser can complete the public upload workflow and the primary chart encodes different prescribed SPM ranges at different positions on one declared scale.
- **Change:** Rehearsed the exact five-source public bundle through the local replay service. Wrapped the default browser fetch so it retains the required global receiver, stopped the session row from forwarding a click event as evidence files, and replaced the fixed target-band geometry with a tested 16–26 SPM scale computed per interval. Added a safe-bundle rehearsal guide and a prioritized visual evidence plan.
- **Evaluation:** The first browser run failed during upload with an illegal fetch invocation. After its RED/GREEN regression, the five sources reached review, checkpoint, briefing, and approved memory. A second navigation run exposed the click-event/file-bundle bug and received its own RED/GREEN boundary test. Visual inspection then exposed identical target-band positions for 19–21 and 22–24 SPM; scale tests now require 30–50% and 60–80% positions respectively and clamp out-of-domain geometry. Final verification passes 104 Python tests, three public verifiers, 27 web tests, ESLint, and the Vinext production build.
- **Result:** The no-cost local demonstration completes from both selected uploads and the session row. The graph now places each prescription truthfully, making the work-05 miss visually meaningful rather than label-only. Broader visual storytelling remains a separate refinement milestone.
- **Cost/runtime:** No model call and no API cost. Browser testing used only the public synthetic bundle and process-local replay service.
- **Decision:** Keep the browser regressions and shared SPM scale. Treat the functional hackathon MVP as complete, while distinguishing it from production readiness and presentation refinement.
- **Learning:** Mocked HTTP success and visually plausible labels did not prove browser operability or chart truthfulness. End-to-end rehearsal and data-geometry tests are both required for a credible demonstration.
- **Next step:** Build the decision-first synopsis, concise agentic investigation trace, and one combined evidence timeline; validate whether a coach or judge can identify value in under 30 seconds.

### 28. Role-aware evidence contribution and human authority

- **Hypothesis:** WAKE will preserve more truthful club context if athletes and coaches can both contribute evidence without the uploader being treated as the source authority, and if each human question identifies who is expected to answer and how the answer was obtained.
- **Change:** Added source provenance that separates `uploaded_by_role`, `origin_role`, and `authority_scope`; source-kind origin guards; distinct source and bundle identities for identical bytes contributed by different roles; deterministic product-level question routing; and a structured checkpoint answer containing answerer, recorder, and authority basis. The interface now lets an athlete or coach contribute the bundle, labels source authority independently, routes resistance-band use to the athlete, and offers athlete-direct, athlete-relayed-through-coach, coach-observed, and unknown answer paths.
- **Evaluation:** RED first failed because upload metadata had no roles, same-byte contributions overwrote each other, checkpoint answers accepted unattributed booleans, the band question had no expected respondent, the client dropped provenance, and the page described every answer as coach context. Further REDs proved that device telemetry could be relabelled as human-origin evidence, that two same-content plan contributions collapsed into one bundle identity, that the first intake design showed authority and uploader without showing the distinct source origin, and that an unattributed review still fell back to "coach-uploaded" copy. GREEN tests cover service, HTTP, replay, live-review adaptation, client serialization, evidence intake, memory preservation, and interface copy. Final verification passes 112 Python tests, three public verifiers, 30 web tests, ESLint, and the Vinext production build.
- **Result:** A coach can upload an athlete's SpeedCoach file and an athlete can upload a coach-authored plan without changing the authority of either source. The band-use answer is now explicitly expected from the athlete, while a coach may preserve a relayed athlete answer or a direct observation without mislabelling it as athlete testimony. The current role values are declared metadata, not authenticated identity.
- **Cost/runtime:** No model call and no API cost. The change is deterministic product-contract and interface behavior.
- **Decision:** Keep uploads role-flexible and authority explicit. Do not introduce role-gated uploads. Require provenance for confirmed human answers and retain `UNKNOWN` when no authoritative response is available.
- **Learning:** Contribution, authorship, measurement, subject, and authority are different relationships. Collapsing them into one "coach upload" or "coach confirmation" label loses exactly the context WAKE is intended to reconstruct.
- **Next step:** Decide whether evaluation evidence justifies promoting expected respondent and authority scope into the versioned agent output schema rather than routing the existing string question at the product boundary.

### 29. Captioned browser walkthrough and live-runtime fallback

- **Hypothesis:** A short horizontal walkthrough assembled from the real browser flow will make the implemented product value legible enough to reuse inside the required five-minute submission video, while an explicitly authorized live attempt will test whether the recording can rely on the paid path.
- **Change:** Rehearsed the five committed public synthetic inputs from athlete-role selection through upload, investigation, review, attributed human checkpoint, verified briefing, and approval-gated memory. Produced a 64-second 1920 x 1080 H.264 walkthrough with English captions under `submission/video/`. The cut distinguishes the failed live attempt from the byte-identical replay fallback instead of editing them into one implied successful call.
- **Evaluation:** The live interface showed the US$0.20 operational start authorization, accepted all five inputs, remained in `Investigating...` for about 90 seconds, and returned `Agent runtime unavailable.` No trajectory, usage result, approximate cost, or ledger entry was created. After restarting the service and interface in replay mode, the same exact public files reached review, the athlete question, the attributed athlete-report-recorded-by-coach answer, briefing, and approved memory. `ffprobe` verifies H.264, 1920 x 1080, 30 fps, 64.000 seconds, and a fast-start MP4; a frame extracted at 31 seconds was visually inspected for readable product content and captions.
- **Result:** A judge-ready product walkthrough segment now exists and honestly demonstrates real input handling plus the complete reproducible interface loop. It is not yet the complete submission video because it omits the initial baseline demonstration, final measured comparison, changelog summary, most impactful correction, and removed experiment required by the official brief.
- **Cost/runtime:** The live attempt was authorized but returned no provider usage evidence, so its actual cost is unknown and is not presented as measured spend. Replay completion had no API cost. The captioned video is 64 seconds and approximately 2.1 MB.
- **Decision:** Keep the walkthrough as a reliable product segment and retain the live-runtime failure as submission evidence. Do not depend on a new paid browser call for the final recording until the failure is diagnosed or a successful run is captured with trajectory and cost observability.
- **Learning:** Video rehearsal is an end-to-end reliability test. A configured live path is not demonstrated merely because its deterministic boundaries pass tests; the recording needs an explicit fallback and must never imply that a failed paid call produced a replayed answer.
- **Next step:** Diagnose the live runtime separately, then assemble the final five-minute narrative around this product segment, the frozen baseline comparison, the v1-to-v2 distance-boundary correction, and one removed experiment.

### 30. Opt-in historical weather enrichment

- **Hypothesis:** A privacy-bounded historical-weather adapter can add useful wind, gust, temperature, and humidity evidence to uploaded SpeedCoach sessions without making mobile telemetry or an environment file mandatory, while explicit provenance and temporal-resolution limits prevent the agent from overstating local or causal effects.
- **Change:** Added an Open-Meteo Historical Forecast adapter, a versioned weather-lookup request, backward-compatible `wake.environment_timeline.v2`, two-decimal median-coordinate minimization, UTC session/query windows, explicit consent and service enablement, user-confirmed IANA timezone support for raw SpeedCoach local clocks, provider and grid provenance, query-window filtering, process-local caching, bundle integration, humidity plus signed headwind/crosswind summaries, in-session environment analysis, and an insufficient-temporal-resolution outcome. Added an HTTP endpoint and client boundary; the visible page control is intentionally deferred to the interface revision.
- **Evaluation:** RED tests first exposed missing provider/schema/service/client behavior. A live connectivity smoke test using only a public synthetic coordinate then exposed that the provider returned a full day for a date-bounded request; a regression test required storage to retain only the requested UTC window. Review exposed that real raw SpeedCoach files carry timezone-unknown local timestamps, so additional RED tests required rejection without a timezone and successful normalization with an explicit IANA timezone. Full verification passes 130 Python tests, three public artifact verifiers, 31 web tests, ESLint, the Vinext production build, and an npm audit with zero vulnerabilities.
- **Result:** The local service can turn an uploaded SpeedCoach source into a provenance-rich optional environment source and include it in a new prepared bundle. Plan plus SpeedCoach remains usable when weather is disabled, unauthorized, unavailable, or too coarse. The smoke test establishes API compatibility and normalization behavior only; it does not establish provider accuracy, broad session quality, or improved athletic outcomes.
- **Cost/runtime:** No LLM call and no model cost. The provider smoke used Open-Meteo's no-key noncommercial endpoint once with a public synthetic coordinate. No production availability, latency, quota, or commercial-price claim is made.
- **Decision:** Keep the deterministic, consented adapter and v2 contract. Preserve SI units internally and defer locale conversion to display. Do not expose automatic lookup in the page until its consent, timezone confirmation, source provenance, and coarse-resolution limitations can be shown clearly.
- **Learning:** External adapters need end-to-end smoke tests in addition to mocks: the real response shape exposed a full-day overfetch that unit fixtures initially hid. Raw SpeedCoach time also proved that geographic matching alone is insufficient; a user-supplied timezone must remain visible as an assumption rather than being silently inferred.
- **Next step:** Add the weather opt-in and timezone confirmation to the evidence-intake interface, then present the resulting conditions in a concise session card without turning the product into another dense dashboard.

### 31. Consent-first weather intake and no-model preparation

- **Hypothesis:** Coaches and athletes can understand and safely use historical weather if the intake makes location authorization, timezone assumptions, modeled-data resolution, and noncausal limits visible before agent execution; replay-mode preparation should make this flow testable without model cost.
- **Change:** Added a historical-conditions panel to the evidence intake, mutually exclusive provider/uploaded environment selection, explicit location consent, IANA timezone entry, weather-aware source ordering, coordinate-free provider preview, provider-failure fallback, source-coverage confirmation, and a replay-mode `prepareSourceBundle` path. Sample sessions now always use committed replay even when a developer starts the page with live support; changed bundles reach the agent only in explicit live mode. Browser QA also produced tested display-format corrections for percent spacing and the `SpeedCoach` product name.
- **Evaluation:** RED tests first required preview output, consent and timezone validation before upload side effects, generated-environment ordering, provider-failure fallback, mutually exclusive environment sources, task-level no-model preparation, and visible interface boundaries. GREEN passes 130 Python tests, three public verifiers, 39 web tests, ESLint, the Vinext production build, and an npm audit with zero vulnerabilities. A real browser rehearsal uploaded only the public synthetic plan and SpeedCoach fixture, queried the provider through the local service, displayed three modeled samples, prepared `Plan + SpeedCoach + Environment`, and then reopened the existing synthetic review. Browser console inspection returned no warnings or errors.
- **Result:** A user can now QA the complete deterministic weather path without a paid agent call. The preview exposes wind range, peak gust, temperature, humidity, cadence, provider, coordinate precision, and the noncausal boundary. The resulting prepared bundle remains process-local and is not analyzed until live mode and cost authorization are explicit.
- **Cost/runtime:** No LLM call and no model cost. Browser rehearsal made one historical-weather lookup using the committed public synthetic fixture; it does not establish real-location accuracy or provider performance.
- **Decision:** Keep the consent-first preparation flow and compact conditions card. Preserve SI analysis values and do not add locale conversion during the hackathon unless interface evaluation shows it materially improves comprehension.
- **Learning:** Weather integration is easier to trust when the deterministic work is visible before the agent. Separating “retrieve and validate evidence” from “interpret with a paid model” improves QA, cost control, and failure diagnosis at the same time.
- **Next step:** Let the project owner QA the full interface, collect usability findings, and prioritize only changes that strengthen the five-minute demonstration.

### 32. Restart-safe session inbox and explicit coaching workflow milestones

- **Hypothesis:** A coach cannot operationally trust WAKE if a refresh appears to erase the session or if one status conflates evidence receipt, agent analysis, coach viewing, human response, and approval into club memory. A local persistent inbox with independent milestones should make unfinished work and completed work immediately distinguishable.
- **Change:** Added a versioned user-restricted state store under the ignored private-data boundary; restoration of sources, normalized evidence, prepared bundles, investigations, answers, briefings, memory, weather metadata, and cost observations; idempotent investigation reopening; safe session list/detail/view endpoints; a client-side inbox loader; four independent lifecycle milestones; state-aware reopening of evidence, review, briefing, and memory; and dynamic operational counts. Raw and normalized telemetry never leave the session-detail API. The interface explicitly states that the local file is not encrypted, authenticated, multi-tenant, or production storage.
- **Evaluation:** RED first showed missing session methods/endpoints, no state-store constructor, an answered investigation resetting to `QUESTION_REQUIRED`, a missing web inbox model, no client session methods, and absent lifecycle copy. Later REDs exposed binary Finder metadata crashing the fixture privacy verifier, an existing `0644` state file not being tightened on load, and the new-review button reopening an already answered sample at its old question. GREEN passes 135 Python tests, three public verifiers, 44 web tests, ESLint, and the Vinext production build. Browser rehearsal opened the synthetic review, returned to an inbox showing analysed/viewed/awaiting-answer/not-in-memory, refreshed the page, recorded an attributed athlete answer, observed ready-for-coach-approval, approved memory, restarted the Python service, and recovered the same in-club-memory session. No model call was made.
- **Result:** The coach can now see whether each session is awaiting analysis, unseen or viewed, awaiting or carrying a human answer, awaiting approval, or already in club memory. Page refresh and local service restart preserve the state. Reopening the same session does not duplicate it or erase an answer.
- **Cost/runtime:** No LLM call and no model cost. Persistence is synchronous local JSON intended only for a small single-user demonstration dataset; scaling, encryption, backups, retention, and concurrent writers were not measured.
- **Decision:** Keep the local inbox for the hackathon demonstration. Do not describe it as a production database or durable hosted club system. A hosted version requires authenticated identity, club tenancy, encryption, retention controls, backups, migrations, concurrency control, and distributed idempotency.
- **Learning:** “Analysed,” “seen,” “answered,” and “accepted into memory” are different product facts. Treating them as one review status created both a usability failure and a data-loss illusion. The final verifier also exposed that scanning every fixture file as UTF-8 crashes on Finder metadata; the privacy regression now scans only declared text formats while preserving the private-path check.
- **Next step:** Let the project owner QA the inbox wording and information density, then decide whether a production-storage architecture belongs in the submission roadmap or distracts from the demonstrated agentic workflow.

### 33. One-command, replay-safe local product startup

- **Hypothesis:** A demonstration launcher can reduce environment and cost-mode mistakes if it owns API/dashboard coordination while preserving replay as the safe default.
- **Change:** Added a portable shell launcher that starts the task-level Python service with historical weather, waits for its session endpoint, starts Vinext with the matching API URL and runtime mode, waits for the coach page, monitors both processes, and stops both through one `Ctrl+C`. It discovers a compatible Homebrew Node executable when an older Node is earlier on `PATH`, rejects occupied or conflicting ports, and offers a secret-free `--print-plan`. Paid execution remains behind `--live`, repository-local `.env` loading, `OPENAI_API_KEY`, and the existing visible cost authorization.
- **Evaluation:** RED first produced five failures because no launcher existed. GREEN passes five launcher contract tests covering shell syntax, replay/no-model disclosure, weather and endpoint configuration, missing-key rejection, paid-mode disclosure, cost authorization, and secret hygiene. The complete deterministic suite passes 140 Python tests, three public verifiers, 44 web tests, ESLint, and the Vinext production build. A real replay smoke rehearsal started both services, restored the saved session inbox through `GET /api/sessions`, returned HTTP 200 for the coach page, and released both ports after one `Ctrl+C`.
- **Result:** The documented local startup is now one command, while the original per-process commands remain available for debugging. No live model execution is enabled by default. The launcher handled the host's Node-version mismatch and terminated without leaving the API or dashboard listening.
- **Cost/runtime:** No LLM call and no model cost. The launcher reported readiness after the initial development compile; exact startup latency was not instrumented as a product metric.
- **Decision:** Keep the launcher as the recommended development and demonstration entry point. Do not use it to hide whether the runtime is replay or live.
- **Learning:** Reproducibility includes operational configuration, not only fixtures and prompts. The host had Node 20 first on `PATH` while the compatible Homebrew Node was installed elsewhere, which is exactly the kind of rehearsal failure a single checked entry point should handle.
- **Next step:** Use the launcher for the owner-led interface QA and record any usability failures separately from startup reliability.

### 34. Successful current product-bundle live retest

- **Hypothesis:** The earlier browser failure may not represent the current accepted v2 bundle runner; executing the exact public bundle through the same service functions should either expose the real exception or preserve a successful verified trajectory.
- **Change:** Reconstructed the public five-source upload through the normal source adapters and compact bundle preparation, then invoked the current `build_bundle_live_runner` through `execute_source_bundle` with the existing US$0.20 operational start authorization. Preserved the output, complete observable trajectory, hashes, and an explicit statement that this was a service-function retest rather than a browser end-to-end result.
- **Evaluation:** The bundle prepared with all five sources and the expected clock-offset, distance-conflict, and route-overlap findings. The bounded v2 agent called all four deterministic tools, produced a final result on round two, and passed schema, case identity, evidence reference, material evidence, derived-distance, source identity, unsupported-claim, and broken-SPM checks without a verifier retry.
- **Result:** The current live bundle runner completed successfully in 22.522 seconds with 31,610 input tokens, 2,680 output tokens, and 34,290 total tokens. Approximate cost was US$0.095380. The earlier `Agent runtime unavailable` remains preserved and unexplained; this result narrows it to a prior or transient full-path failure rather than a deterministic incompatibility in the current bundle runner.
- **Cost/runtime:** US$0.095380 and 22.522 seconds, recorded from the committed trajectory. The authorization was a start gate, not a hard cap.
- **Decision:** Keep both results. Use the successful current trajectory as live-run evidence, retain replay as the dependable video fallback, and do not claim browser-path reliability until a separate browser rehearsal succeeds.
- **Learning:** A generic user-safe error is not enough for diagnosis. The next runtime hardening change should preserve a sanitized local failure artifact or correlation id while keeping internal exception details out of the browser response.
- **Next step:** Complete a browser-path rehearsal with the public synthetic files, then expand the fixed evaluation beyond two implemented cases.

### 35. Eight isolated diagnostic fixtures and immutable evaluation input v2

- **Hypothesis:** Eight small cases that each isolate one rowing evidence failure will reveal where WAKE generalizes or fails more clearly than adding another complex hero scenario.
- **Change:** Added a seeded deterministic generator for cases 003-010, with synthetic plans, SpeedCoach telemetry, optional environment/mobile evidence, evaluator-only ground truth, per-fixture hashes, privacy-safe coordinates, compact ground-truth-free summaries, and a public verifier. The scenarios cover calm compliance, steady headwind, tailwind without an improvement claim, crosswind gusts without causal overreach, an omitted work interval, correct distance with low SPM, excessive recovery, and zero-only mobile SPM. Published the ten-case summaries as `baseline-inputs/v2` while keeping the official two-case v1 bundle byte-stable.
- **Evaluation:** RED began with the missing generator, then required byte reproducibility, schema validity, no ground-truth leakage, isolated expected deviations, correct mobile-zero behavior, ten compact summaries, a corruption-sensitive public verifier, and an immutable-v1/expanded-v2 boundary. An attempted early `IMPLEMENTED` label caused the full regression to fail because grader v1.1 correctly required outputs for every implemented case; the labels were returned to `PLANNED`. A second review caught that the first builder draft had expanded the already frozen v1 manifest; a new RED required v1 to retain two entries and v2 to retain those exact entries plus eight. Final repository verification passes 148 deterministic Python tests and all four public fixture/artifact checks.
- **Result:** Ten public case inputs now exist, and the eight new fixtures are reproducible and ready for no-cost agent request generation. They have no baseline or WAKE model outputs and do not change the published two-case score. Grader v1.1 is known to contain case-002-specific environmental and source-policy checks, so it is not yet valid for this expansion.
- **Cost/runtime:** No model call and no API cost. Only deterministic local generation, tests, schema checks, and hash verification ran.
- **Decision:** Keep the eight fixtures and the v2 input bundle. Keep cases 003-010 out of the denominator until grader v1.2 and their required outputs exist. Preserve the failed status-label attempt and v1-overwrite attempt as evidence of why artifact state and version identity are part of evaluation correctness.
- **Learning:** A fixture can be complete before an evaluation case is complete. Registry status, input-bundle version, grader coverage, and model-output availability must advance together or reproducibility becomes misleading.
- **Next step:** Add generalized grader v1.2 behavior with RED tests for dynamic source policy, scenario-specific environmental interpretation, abstention, missing intervals, low SPM, and excess recovery; then create a no-cost ten-case baseline/agent preflight before authorizing paid calls.

### 36. Generalized grader v1.2 and twenty-request no-cost preflight

- **Hypothesis:** The ten-case expansion can be scored fairly without changing the rubric if case-specific expectations are derived from each versioned contract rather than inherited from the wind-shift hero case.
- **Change:** Added grader v1.2 beside unchanged v1.1. It derives plan checks from normalized blocks, source checks from each expected policy, environmental categories from projected wind timelines, abstention concepts from required evaluator boundaries, and deviation accuracy from segment identity. Added an offline v1.2 CLI and explicit `--inputs` support to both runners plus explicit `--prompt` selection for the agent. Preserved 20 hashed preflight requests under `evaluation/runs/expanded-evaluation-v2/preflight/`.
- **Evaluation:** RED began with the missing versioned module/config. Calibration then required perfect 100/100 profiles for cases 003-010, preserved perfect scores for 001-002, dynamic rejection of zero-only mobile SPM, case-specific crosswind/gust recognition, zero environmental score for causal language, and exact detection of `work-04`, `work-03`, and `recovery-02`. CLI REDs required all ten baseline and agent requests without network plus explicit offline case-set grading. Final verification passes 157 deterministic Python tests and all four public fixture/artifact checks. The committed preflight contains 10 baseline requests totaling 264,576 bytes and 10 WAKE requests totaling 295,886 bytes; both manifests declare `api_called: false` and contain no evaluator ground truth.
- **Result:** The expanded comparison is now reproducible through request construction and deterministic scoring. Calibration outputs score 100, but no real baseline or agent answer exists for the eight new cases, so there is no expanded model-quality score.
- **Cost/runtime:** No model call and no API cost. Request generation and offline scoring only.
- **Decision:** Keep grader v1.2 and the explicit runner selectors. Preserve v1.1 and historical runner defaults. Do not move cases 003-010 to `IMPLEMENTED` or publish a ten-case score until paid outputs and trajectories are complete.
- **Learning:** A generalized grader should encode invariants from case data, not prose unique to the first demonstration. A passing request preflight proves reproducibility and safety boundaries, not agent quality.
- **Next step:** Review estimated cost for 20 paid calls, execute baseline and WAKE once on the exact committed preflight inputs with explicit authorization, preserve any failures, then score with grader v1.2.

### 37. No-cost tool audit before expanded paid execution

- **Hypothesis:** The deterministic tools should expose each diagnostic fault cleanly before model quality is measured; otherwise a paid failure could be caused by the instrument rather than the agent.
- **Change:** Added v2-only planned/observed work counts, missing interval identities, recovery-duration targets and compliance, structured plan deviations, and calm/headwind/tailwind/crosswind/gust profiles. Added a v2-only work classification boundary two SPM below the lowest work target while preserving v1's one-SPM boundary. Regenerated the ten WAKE preflight requests with the revised tool descriptions; the new agent request total is 297,066 bytes and still declares `api_called: false`.
- **Evaluation:** RED showed case 007 had no explicit missing-work result, case 009 marked every recovery compliant, and the environment tool did not expose crosswind or gusts. After the first GREEN, a direct all-case audit revealed a second failure: case 008's noisy 19-SPM work interval crossed the 19-SPM threshold repeatedly and became 12 work fragments. A regression test required exactly four work intervals and only `work-03` as the deviation. The final deterministic audit reconstructs the expected deviation identities for cases 002-010 and produces no deviations for compliant cases.
- **Result:** The tools now present the new fault classes directly and preserve the central distance-abstention boundary. No model was called, so this does not show that the agent will use those facts correctly.
- **Cost/runtime:** No API call and no model cost.
- **Decision:** Keep the v2-only enhancement and preserve the original v1 tool behavior. Do not start the expanded paid run from the earlier preflight revision.
- **Learning:** A fixed evaluation can diagnose the evaluator and tools before it diagnoses the model. Low-SPM deviation detection requires maintaining interval continuity, not simply applying a pointwise target threshold.
- **Next step:** Run the complete regression suite, freeze the updated preflight, then request explicit owner authorization for the estimated paid comparison cost.

### 38. Official ten-case comparison and versioned evaluation promotion

- **Hypothesis:** The bounded WAKE workflow should generalize beyond the two hero cases and outperform one direct model call on isolated rowing failures involving environment, interval completion, SPM compliance, recovery duration, and broken mobile telemetry.
- **Change:** Executed the exact committed `baseline-inputs/v2` bundle once through each comparison arm, preserved all outputs and observable WAKE trajectories, scored both arms offline with grader v1.2, and added a separate `cases-v2.json` registry. A RED test first required grader v1.2 to see ten implemented cases while grader v1.1 continued to see two; GREEN made v1.2 resolve its own versioned registry without changing the historical grader.
- **Evaluation:** Both arms used `gpt-5.6-terra`, medium reasoning, the same ten summaries, strict output schema, and grader v1.2. Baseline scored 49.00/100 and WAKE scored 83.76/100: +34.76 absolute points and +70.94% relative. Every case improved. WAKE reached 100% deviation detection versus 55.56%, 88.41% segment reconstruction versus 0%, and 61.67% metric-source trust versus 15%. Environmental interpretation regressed from 80% to 76%; case 001 remained the weakest WAKE case at 53.71.
- **Result:** Keep the bounded agent as the evaluated final workflow. Its largest gains were on missing intervals (+61.38), low-SPM work (+65.08), and excessive recovery (+54.47). Do not hide the environmental regression or the remaining real-case weakness. The outputs are saved and can be reopened or regraded with no model call.
- **Cost/runtime:** Baseline cost US$0.428172, used 80,686 tokens, and accumulated 241.503 seconds across ten sequential calls. WAKE cost US$0.711516, used 200,893 tokens, and completed in 234.812 seconds. Incremental agent cost was US$0.283344; total paid comparison cost was US$1.139688. WAKE made 40 tool calls and five first candidates required one bounded verifier correction.
- **Decision:** Promote cases 001-010 only in the v2 registry and publish the ten-case result as the primary hackathon comparison. Preserve the two-case v1 registry, inputs, grader, outputs, and score as historical evidence.
- **Learning:** Deterministic tools produced large gains on structural deviations, but more orchestration does not guarantee every dimension improves. Environmental phrasing and human-context abstention remain specific targets for a future version; changing them after seeing official outputs would require a new prompt/grader version and a fresh comparison.
- **Next step:** Expose the saved comparison in submission materials, review the environmental failures without rewriting v2, and conduct a small coach usability evaluation if time permits.

### 39. Read-only visual evidence for the official comparison

- **Hypothesis:** Judges and the project owner can understand the measured value more quickly if the saved comparison is visible in the product language, provided the surface cannot invoke the agent, expose evaluator-only data, or blur benchmark machinery into the coach workflow.
- **Change:** Added a deterministic public-summary generator over the official manifests, v1.2 grade reports, v2 registry, per-case baseline manifests, and WAKE trajectories. Added a separate Evaluation destination showing macro scores, every case delta, dimension comparisons, cost, tokens, runtime, tool calls, verifier retries, saved-output status, and validity boundaries. Preserved the existing WAKE typography, palette, density, native semantic markup, and responsive behavior. The screen is explicitly labelled `Saved result · No model call` and contains no execution control.
- **Evaluation:** RED first failed because neither the generator/module nor the Evaluation screen existed. GREEN tests require exact official values, all ten positive case deltas, the -4.00 environmental regression, byte-stable module generation, and absence of `ground_truth`, `coach_briefing`, or `input/` evidence references. The web suite passes 46 tests, ESLint, and the Vinext production build. Browser QA at desktop and 390 × 844 mobile viewports confirmed the first-viewport score hierarchy, navigation, responsive stacking, complete semantic content, and no console warnings or errors.
- **Result:** Keep the view for the hackathon build. The first viewport now communicates 83.76 versus 49.00 and +34.76 points; deeper sections show that all ten cases improved while environmental interpretation regressed from 80.00 to 76.00. The view can be reopened without API cost because it renders committed aggregates only.
- **Cost/runtime:** No model call and no API cost. Summary generation, tests, lint, build, and local browser rendering were deterministic. The existing paid run values are displayed but were not recomputed through the provider.
- **Decision:** Keep Sessions and Goal memory as the operational coach workflow and treat Evaluation as submission-only evidence. Do not add grader controls, raw outputs, ground truth, or rerun buttons to the browser.
- **Learning:** Visual proof is strongest when it includes the failure beside the headline gain. Showing the environmental regression and real-case limitation makes the 83.76 score more credible than a celebratory aggregate alone.
- **Next step:** Use this page in the final five-minute video, then decide whether the remaining time is better spent on the submission narrative or on a small coach usability rehearsal.

### 40. Discoverable consolidated and individual evaluation reports

- **Hypothesis:** The saved evaluation cannot support the demonstration if compact layouts hide its only navigation entry or if the ten case rows look like non-interactive bars. A visible Sessions-page action plus expandable reports should make both the aggregate claim and its case-level evidence discoverable without mixing benchmarks into club operations.
- **Change:** Added a persistent `View evaluation results` action to the Sessions header, labelled the destination `Consolidated official evaluation`, and converted every case row into a native expandable report. A deterministic generator now adds a public scenario description and baseline-versus-WAKE rubric scores for each applicable dimension. It intentionally excludes grader reasons, evidence references, ground truth, raw output, and execution controls. Evaluation fixtures remain outside the coach inbox.
- **Evaluation:** RED first failed because generated cases had no `scenario` or `dimensions` and the interface had no required main-page action, consolidated label, or expandable report. GREEN passes 163 Python tests, four public fixture/artifact verifiers, 46 web tests, ESLint, and the Vinext production build. The privacy regression now also rejects `evidence_refs` and grader `reasons` in the browser module. Browser QA followed the home action into the consolidated report, opened case 001, verified its scenario and four dimension rows, and confirmed all ten case identifiers at both the default layout and 390 × 844.
- **Result:** Keep the new navigation and report hierarchy. The home now reaches the evaluation at compact widths; the evaluation opens with the official consolidated score and lets a judge inspect all ten cases individually.
- **Cost/runtime:** No model call and no API cost. The change reads only frozen official grade artifacts and regenerates a deterministic JavaScript module.
- **Decision:** Keep synthetic evaluation evidence separate from real session state and operational counts. Per-case reports belong under Evaluation, not Sessions.
- **Learning:** A report can exist technically and still be absent from the user journey. Discoverability and truthful data classification are both part of evaluation evidence quality.
- **Next step:** Use the consolidated-to-individual drill-down in the final demo recording.

### 41. Two-week relational club pulse

- **Hypothesis:** A single deep session can show that WAKE reconstructs evidence, but it cannot show why a coach needs agentic triage across a club. Two weeks of relational activity across named athletes, recurring lineups, and physical boats should make the scaling problem and Team and Crew Memory layer visible without adding another chart-heavy dashboard.
- **Change:** Added a deterministic `wake.demo_club.v1` dataset with sixteen fictional athletes, four 2x crews, four 4x crews, two 8x crews, ten crew-assigned physical boats, one shared 1x, 38 planned outings, 35 completed crew outings, three unavailable crews, five alternate solo/ergometer activities, and three expected days with no activity record. Added pure club, crew, athlete, and attention aggregations; a two-week club pulse; prioritized coach-review items; crew cards grouped by boat class; an athlete roster; and read-only crew and athlete drill-downs. Kept the synthetic club, operational session inbox, and technical Evaluation surface explicitly separate.
- **Evaluation:** RED began with a missing module, then required the exact crew-class distribution, lineup size and seat uniqueness, matching physical boats, alternate modalities, gap integrity, relational summaries, safe attention language, and visible drill-down components. GREEN passes 51 web tests, ESLint, and the Vinext production build. Browser QA confirmed all ten crews and sixteen athletes in the default layout, opened Harbor Men 2x to inspect its two-person lineup, Aurora shell, and four planned outings, opened Lucas to inspect three recurring lineups, four physical boats, crew/solo/ergometer activity, and validated the complete home at 390 × 844.
- **Result:** Keep the relational demo layer. The first club view now communicates 35/38 completed crew outings, 40 recorded activities, 511.5 km, ten review items, three crew-unavailable events, and three participation gaps. Missing participation remains a question requiring context rather than a claim about commitment, health, or fitness.
- **Cost/runtime:** No model call and no API cost. Dataset construction, aggregation, rendering, tests, and browser QA are deterministic.
- **Decision:** Use fictional names and explicit synthetic labelling in the public demo. Do not expose private athlete identities or GPS, and do not call this frontend aggregate an agent-generated club briefing until the longitudinal agent path is implemented and evaluated.
- **Learning:** The unit of rowing memory is not only a session. Athlete, ordered lineup, physical shell, modality, and date must remain separately addressable or useful longitudinal questions become impossible to answer safely.
- **Next step:** Rehearse the demo from club pulse to crew to athlete to the existing evidence-backed session, then decide whether real-derived anonymized summaries can be prepared without weakening privacy or submission focus.

### 42. Real-informed synthetic data provenance

- **Hypothesis:** Labelling the club pulse only as synthetic protects privacy but obscures the real rowing material that informed its source shapes, plausible values, workout patterns, and failure modes. Showing both the grounding and the fictional boundary should improve credibility without fabricating athlete history.
- **Change:** Added structured `REAL_INFORMED_SYNTHETIC` provenance to the demo-club contract; identified the real material classes that informed the demonstration; separated fictional elements; and added an explicit non-representativeness boundary. Revised the Sessions, crew, and athlete surfaces to use `Real-informed synthetic data`, with a visible two-column explanation of what is grounded and what remains fictional. Updated product documentation and the stable decision record.
- **Evaluation:** RED first failed because the dataset had no provenance contract and the page contained none of the required grounding or fictional-boundary language. GREEN tests require the provenance classification, four real input classes, the statistical boundary, and visible interface copy. Full verification passes 163 Python tests, four public fixture/artifact verifiers, 51 web tests, ESLint, and the Vinext production build. Browser QA confirmed the grounding and fictional-boundary copy in the default layout and at 390 × 844.
- **Result:** The public interface now states that its people and exact history are fictional while its structures, formats, plausible ranges, and operational situations are modeled from supplied real rowing material. It does not call those fictional outcomes observed sessions or claim statistical calibration.
- **Cost/runtime:** No model call and no API cost. The change is deterministic metadata, interface copy, styling, tests, and documentation.
- **Decision:** Keep the combined classification. Do not shorten it back to `synthetic` on the club surface, and do not use `real data` for fictional records.
- **Learning:** Data credibility has two independent dimensions: whether a record describes a real person and whether its structure and scenario are grounded in real domain material. A trustworthy demo must expose both.
- **Next step:** Use the provenance explanation in the demo narration before opening crew and athlete drill-downs.

### 43. Cost-aware club-period screening

- **Hypothesis:** The two-week club layer gains credible intelligence only if alerts are derived from evidence rather than stored as outcomes, every activity is screened, and the system routes human/source dependencies away from paid model calls.
- **Change:** Replaced four prewritten findings with compact plan, SpeedCoach, and athlete-context observations. Added `wake.club_period_analysis.v1`, which screens 40 recorded activities and 38 planned outings, produces evidence-referenced outing and activity assessments, derives low-SPM and excessive-recovery findings, identifies a missing plan and missing athlete context, combines them with disruptions and participation gaps, and routes ten attention signals. Two numeric candidates require complete source bundles before bounded investigation; eight route to a human or missing source. Added observed, planning, and authorization cost projections plus explicit zero-call and no-synthesis boundaries. The interface now shows 40/40 screened, 0/2 deep investigations, eight human/source routes, and a US$0.45 planning projection.
- **Evaluation:** RED first failed on the absent analyzer. Later RED cycles required derivation from observations, evidence references, exact routing, full activity coverage, no positive plan-compliance claim, removal of prefilled findings, visible interface status, and an explicit zero-source-bundle boundary. GREEN passes 163 Python tests, four public fixture/artifact verifiers, 57 web tests, ESLint, and the Vinext production build. Browser QA confirmed 40/40 coverage, the 0/2 queue, eight dependency routes, the US$0.45 projection, and the source-bundle boundary in the default layout and at 390 × 844; crew drill-down showed the derived 18-SPM finding and no `Executed as planned` label.
- **Result:** The club pulse is no longer only relational or a list of hand-authored alerts: it performs a reproducible zero-cost screen over the complete displayed period. It still does not claim a longitudinal agent result. The two deep candidates cannot execute until complete synthetic source bundles exist.
- **Cost/runtime:** No model call and no API cost. Three future paid executions—two investigations plus one synthesis—project to US$0.213455 at the observed ten-case average, US$0.45 at the planning reference, and US$0.60 in start authorizations. These are forecasts, not observed charges.
- **Decision:** Keep deterministic full-period screening and dependency-aware routing. Do not execute the candidate queue from compact observations alone, and do not spend model budget on a missing plan or human answer.
- **Learning:** Agentic value includes deciding when not to call the model. Full coverage can be deterministic while ambiguity, source selection, and longitudinal synthesis remain bounded agent work.
- **Next step:** Generate complete public synthetic plan and SpeedCoach bundles for the two numeric candidates, run a no-cost preflight, and request explicit authorization before paid execution.

### 44. Reproducible club-candidate evidence preflight

- **Hypothesis:** The two queued club anomalies should not consume model budget or be labelled ready until complete, privacy-safe source bundles reproduce the compact screen findings through the real deterministic preparation path.
- **Change:** Added a deterministic generator for two complete public real-informed synthetic plan + SpeedCoach + context bundles, their input hashes and `agent_executed: false` boundary, and a fifth public verifier. The Bridge Mixed 2x bundle models two 4 km intervals with only `work-02` below 20 SPM; the Atlas Men 4x bundle models four 2 km intervals with only `recovery-02` above the allowed recovery. Each paid-queue signal now links to its bundle. Once both pass preflight, the period analysis reports two complete bundles and `READY_FOR_AUTHORIZATION` while retaining `0/2` completed and `NOT_EXECUTED` synthesis.
- **Evaluation:** RED first rejected the unregistered `REAL_INFORMED_SYNTHETIC` value inside the training-plan schema; the fix kept plan provenance `SYNTHETIC` while preserving the richer narrative provenance in the manifest. An earlier generator attempt stalled because floating-point subtraction left a microscopic positive distance residual; it was stopped before completion, a bounded-row regression test was added, and the final step now assigns the remaining distance explicitly. Final review also exposed that a manually expanded fixture README would be overwritten by regeneration, so the byte-reproducibility test forced the generator to own the complete documentation. Further RED cycles required the public verifier and interface readiness state. GREEN passes 169 Python tests, five public fixture/artifact verifiers, 57 web tests, ESLint, and the Vinext production build.
- **Result:** Both candidate inputs are now complete, reproducible, schema-valid, privacy-checked, and deterministically reconstruct the expected isolated anomaly. This proves source/tool readiness, not model quality: no candidate has been sent to the model and no club synthesis exists.
- **Cost/runtime:** No model call and no API cost. The existing forecast remains three future calls: approximately US$0.213455 at the observed ten-case average, US$0.45 at the planning reference, and US$0.60 in start authorizations.
- **Decision:** Keep the generated bundles and public preflight. Require explicit owner authorization before executing either candidate, and execute longitudinal synthesis only after candidate results and human/source dependencies are represented honestly.
- **Learning:** “Real-informed synthetic” belongs in dataset provenance, while schema-level plan provenance must use the stable `SYNTHETIC` enum. Deterministic generation also needs explicit termination invariants; plausible telemetry is not reproducible evidence if a floating-point residual can stall fixture creation.
- **Next step:** Obtain explicit authorization for the two bounded candidate calls, preserve their trajectories and actual cost, then decide whether evidence is sufficient for a separately authorized longitudinal synthesis.

### 45. Authorized club-candidate investigations

- **Hypothesis:** The two preflighted numeric candidates should survive the real bounded agent workflow, preserve exactly the deterministic anomaly, and demonstrate selective paid reasoning without spending on all 40 records or the eight human/source dependencies.
- **Change:** After explicit owner authorization for two calls with a US$0.20 start gate each, executed Bridge Mixed 2x and Atlas Men 4x through the accepted v2 product runtime. Preserved both structured outputs and full observable trajectories, added a versioned aggregate run manifest with artifact hashes and totals, added a sixth public verifier, changed input-fixture metadata from the stale `agent_executed: false` boolean to a separate result reference, and updated the club interface from `0/2` ready to `2/2` verified with observed cost and token use. Longitudinal synthesis remains a separate unexecuted action.
- **Evaluation:** Bridge produced only `SPM_OUTSIDE_TARGET` on `work-02` at 18 SPM and asked whether the change was intentional plus whether environmental evidence exists. Atlas produced only `RECOVERY_DURATION_OUTSIDE_TARGET` on `recovery-02` at 247 seconds and required no follow-up. Both output schemas and trajectories passed the deterministic verifier with no stored private chain-of-thought. A temporary post-run summary initially inspected the nonexistent `plan_deviations` output key and displayed an empty list; artifact inspection found the correct schema key `deviations` before the second call, so no retry or extra model cost occurred. RED tests then required artifact hashes, exact deviation identities, totals, `2/2` interface state, and honest separation of synthesis.
- **Result:** Selective triage now has observed evidence: the system paid for two supported numeric ambiguities, preserved both expected isolated deviations, and did not spend on the eight items requiring people or sources. This still covers two synthetic sessions, not a longitudinal club conclusion or human-coach comparison.
- **Cost/runtime:** Bridge used 27,963 tokens, 26.693 seconds, and US$0.089806. Atlas used 32,131 tokens, 29.308 seconds, and US$0.104312. Combined: 60,094 tokens, 56.001 summed case seconds, and US$0.194118. Both remained within their individual US$0.20 start authorizations; those gates were not provider caps.
- **Decision:** Keep both verified outputs and expose their aggregate status/cost. Do not authorize or imply a third synthesis call from the two-call approval. Preserve human/source routes as dependencies rather than model tasks.
- **Learning:** The observed average for these two minimal three-source bundles was US$0.097059, above the earlier ten-case WAKE average of US$0.071152 but below the US$0.15 planning reference. Operational observability must use the final analysis schema, not a convenience-field assumption.
- **Next step:** Review the two candidate briefings in the interface, decide how to represent the Bridge athlete question, and request separate authorization only if a bounded longitudinal synthesis is still valuable.

### 46. Session-isolated bulk processing and complete two-week evidence batch

- **Hypothesis:** A club-scale demonstration needs complete period evidence and efficient submission, but putting many sessions into one prompt would weaken provenance, retries, cost control, and human approval. A batch envelope over independent session units should provide scale without sacrificing auditability.
- **Change:** Added content-addressed source-batch preparation for up to 100 session groups, item-level preparation failures, restart-safe persistence, sequential paid execution through whole per-execution start gates, resumable pending work, item-level execution failure isolation, compact batch status/cost responses, HTTP endpoints, and client methods. Added a deterministic generator for 40 independent real-informed synthetic activity directories plus a seventh public verifier. The committed set contains 38 SpeedCoach-shaped water records and two Concept2-shaped indoor alternatives; every source has a per-session hash. Added a validation funnel to the club interface and documented the distinction between data validation, reconstruction, plan comparison, agent verification, and human approval.
- **Evaluation:** RED first failed on missing batch service methods and endpoints, then required idempotent repeat preparation, invalid-item isolation, one authorized start per US$0.20 gate, resume without duplicate calls, continuation after an injected runner failure, restart-safe batch restoration, compact responses, and explicit browser-client live authorization. A separate RED began with missing public-batch generator/verifier modules; GREEN requires exactly 40 unique records, 38 water and two indoor modalities, byte-for-byte regeneration, every source hash, plan schema validity, Concept2-shaped columns, water normalization and v2 reconstruction, exact candidate deviation links, and privacy boundaries. Browser tests require the six-level validation funnel and explicit Concept2 limitation. No model call occurred.
- **Result:** The public report now verifies 40 records received and data-validated, 38 water sessions reconstructed, 37 plan-compared, two agent-verified, and zero human-approved. Routing preserves 31 no-material-signal water sessions, three reconstructed alternatives, two verified exceptions, one missing plan, one missing athlete context, and two indoor records requiring a Concept2 adapter. The two existing paid results remain US$0.194118 and 60,094 tokens; longitudinal synthesis remains `NOT_EXECUTED`.
- **Cost/runtime:** No new API call and no new model cost. The 40-record public batch occupies approximately 2.3 MiB. Deterministic runtime is verified locally but is not presented as a performance benchmark.
- **Decision:** Keep bulk submission as an outer envelope and session execution as the atomic unit. Do not concatenate telemetry across sessions, call the model on clean records, promote deterministic reconstruction to agent verification, or mark any session human-approved without the explicit review transition.
- **Learning:** Club scale is not demonstrated by making one prompt larger. It is demonstrated by complete intake, isolated evidence, selective reasoning, honest unresolved states, and a consolidated view whose claims retain their validation level.
- **Next step:** Rehearse the validation funnel, decide whether the two indoor records should remain an honest unsupported-adapter boundary for submission, and design a separately authorized longitudinal synthesis only after its input and evaluation contract are frozen.

### 47. Human-confirmed Concept2 PM5 normalization and real-reference evidence

- **Hypothesis:** Real PM5 detail screens can close the two indoor-record adapter gap and strengthen submission credibility if their workout-dependent column semantics are normalized deterministically, while a minimized reference packet can show judges the source material without exposing athlete identity or implying automatic OCR.
- **Change:** Added RED-first coverage for fixed-distance, fixed-time, and interval PM5 transcriptions. Implemented `CONCEPT2_PM5_TRANSCRIPTION_CSV` normalization with explicit cumulative-axis rules, work/recovery identity, summary-level provenance, input/normalized hashes, optional heart-rate and watts fields, and strict numeric/cumulative validation. A final provenance review made `HUMAN_CONFIRMED` versus `SYNTHETIC` mandatory so generated records cannot inherit human authority. Regenerated the two real-informed synthetic indoor batch records as synthetic PM5 transcription-format inputs and moved them from `SOURCE_ADAPTER_REQUIRED` to deterministic `RECONSTRUCTED_ALTERNATIVE`. Added four metadata-stripped, identity-free real PM5 screen crops and five human-confirmed transcriptions under `ANONYMIZED_REAL_REFERENCE`. The first local evidence selection included a screen with heart-rate values; privacy review rejected it before commit and replaced it with a non-heart-rate low-SPM reference.
- **Evaluation:** RED first failed because `CONCEPT2` was unsupported, fixed-distance marker validation did not exist, the public batch remained at 38 reconstructed/37 compared, and the evidence README/transcriptions were absent. GREEN adapter tests prove cumulative distance for fixed-distance screens, cumulative time plus summed split distance for fixed-time screens, interval work/recovery preservation, invalid-marker rejection, report-schema validity, and byte-deterministic public references. The public verifier now reports 40 received, 40 validated, 40 reconstructed, 39 plan-compared, two agent-verified, and zero human-approved. The web suite passes 59 tests with the revised funnel and explicit no-OCR language.
- **Result:** Keep the confirmed-transcription adapter and sanitized evidence packet. The two indoor records now contribute to the club-scale validation funnel without a model call, while the repository shows the real PM5 shapes that informed the implementation. This is deterministic summary reconstruction, not native device integration, photo understanding, per-stroke analysis, agent verification, or proof of athlete improvement.
- **Cost/runtime:** No model or external API call and no model cost. All new behavior is deterministic; four public image crops were stripped of EXIF metadata and checked for private local paths.
- **Decision:** Publish only the minimized crops and human-confirmed transcriptions. Keep all raw photographs, any heart-rate-bearing references, surrounding environments, and source filenames outside the repository. Keep operational photo upload, confidence-scored OCR, native ErgData ingestion, and an indoor agent workflow as separately testable future work.
- **Learning:** PM5 columns cannot be normalized by header name alone: fixed-distance and fixed-time screens reverse which axis is cumulative. Source credibility improves when judges can inspect sanitized real inputs, but that evidence must remain visibly separate from synthetic fixtures and executed agent results.
- **Next step:** Rehearse the validation funnel and PM5 evidence packet in the submission video; only add OCR or native exports if a fixed evaluation proves they improve the workflow before the deadline.

### 48. Athlete-owned Concept2 records and cross-modality Training Days

- **Hypothesis:** Concept2 evidence becomes materially more useful to coaches when every PM5 result belongs to one athlete and water, pre/post-water ergometer work, indoor alternatives, and indoor-only days can be read in one chronology without collapsing modality-specific metrics.
- **Change:** Added RED-first tests requiring individual PM5 ownership, three indoor workout shapes, separate water/indoor aggregation, combined and indoor-only classification, and visible interface boundaries. Replaced the two group-like Concept2 records with fourteen individual synthetic PM5 transcription-format records across fixed-distance, fixed-time, and interval sessions. Added plan-declared `PRIMARY`, `PRE_WATER`, `POST_WATER`, and `ALTERNATIVE` roles plus `PLAN_CONFIRMED` or `STANDALONE` link status. Added deterministic `Training Day` aggregation and athlete drill-down cards for water-only, indoor-only, combined, and expected-missing days. The club batch expanded from 40 to 52 activities; all remain source-isolated and content-hashed.
- **Evaluation:** RED failed on the absent Training Day module, 40-record batch, group-owned PM5 records, merged modality distance, and missing UI copy. GREEN passes 185 Python tests, 61 web tests, ESLint, and the Vinext production build. The public batch verifier reports 52 received, validated, and reconstructed; 51 plan-compared; two agent-verified; and zero human-approved. Browser QA verified the 52/52 funnel, seven combined athlete-days, seven indoor-only athlete-days, separated 489.5 km water versus 106.1 km indoor, Lucas combined-day cards, Sofia's standalone 30-minute indoor card, and the 390 × 844 responsive layout. A fresh browser tab produced no warning or error logs.
- **Result:** Keep the athlete-owned activity model and Training Day interface. Coaches can now see indoor training as valid work, distinguish it from water, inspect Concept2 pace/SPM/watts, and recognize combined or indoor-only days without opening every source record. This is deterministic reconstruction over real-informed synthetic data, not longitudinal agent synthesis or proof of strength, stamina, technique, fitness, or performance improvement.
- **Cost/runtime:** No model or external API call and no new model cost. All new analysis is deterministic. The two previously authorized water investigations remain US$0.194118 combined; the optional longitudinal synthesis remains unexecuted.
- **Decision:** Never assign one PM5 result to multiple athletes. Shared prescriptions may produce multiple individual results. Never add water and indoor meters into a single performance total. Require compatible workout shape and supported context before comparing indoor results over time.
- **Learning:** The useful longitudinal unit is an athlete-day composed of independently evidenced activities, not a forced choice between “water session” and “erg session.” Grouping should improve navigation while source identity and metric meaning remain intact.
- **Next step:** Add an explicitly evaluated indoor comparison rule only after two compatible athlete-owned tests exist; otherwise use the current chronology and modality-specific summaries in the submission demo.

### 49. Frozen two-case longitudinal GPT pilot

- **Hypothesis:** Period-level GPT intelligence should be tested only where synthesis may add value: one athlete chronology and one club-priority queue. A bounded tool workflow should outperform a direct call on evidence coverage, prioritization, and abstention without merging modalities or inventing athletic trends.
- **Change:** Added RED-first contracts for two compact ground-truth-free summaries, a shared strict longitudinal output schema, direct-baseline and bounded-agent prompts, four read-only investigation tools, output verification, runtime/usage/cost observability, saved reports, and finite per-start authorization. Added a four-request zero-cost preflight with hashes and an independent tamper verifier. The Sessions interface now links to a dedicated pilot page that explains both scopes, why GPT is considered, same-input comparison, forecast versus authorization, zero current calls, boundaries, and zero-cost report reopening. Added an explicit CLI execution path, but kept `--execute`, `OPENAI_API_KEY`, and sufficient authorization mandatory.
- **Evaluation:** RED failed on missing pilot modules, UI route and copy, runtime entry points, and preflight verifier. GREEN passes seven longitudinal Python tests, 63 web tests, ESLint, the Vinext production build, and the committed preflight verifier. Fake Responses clients prove one-call baseline persistence and a two-response four-tool agent loop; tampering with any frozen request is detected. Browser QA verified the main-page entry point, both scope cards, all cost/no-spend disclosures, a 390 × 844 layout with no horizontal overflow, and zero warning/error logs. These deterministic tests establish readiness, not model quality.
- **Result:** Keep the two-case design and frozen requests. `athlete-lucas` and `club-coach` each have baseline and WAKE requests using `gpt-5.6-terra`, medium reasoning, `store: false`, and the same strict schema. No longitudinal report, score, or period-level model conclusion exists yet.
- **Cost/runtime:** No OpenAI request occurred and new API cost is US$0.00. Four future starts project to US$0.388236 at the observed reference or US$0.60 at the planning reference. Full execution requires a US$0.80 start authorization; this is not a provider cap. Saved results reopen at US$0.00.
- **Decision:** Freeze before spending. Do not call GPT for all 52 activities, hide deterministic screening inside the model, or claim that a prepared request is intelligence. Execute and score all four requests only after separate explicit authorization.
- **Learning:** “Use GPT” is not one undifferentiated feature. The defensible experiment first decides which decisions need synthesis, what deterministic evidence the model may inspect, which claims remain impossible, and how the baseline will make agentic value measurable.
- **Next step:** Request explicit authorization only if the owner wants the four paid comparison starts now; then preserve and score all four outputs before changing the frozen contract.

### 50. Real-informed synthetic Competition Review

- **Hypothesis:** The product story becomes materially stronger when a coach can follow the same fictional athletes and exact crew snapshots from two weeks of training into a complete competitive field, while official source patterns improve realism without attaching real identities to fabricated history.
- **Change:** Added `wake.competition_review.v1`, a deterministic synthetic regatta, category-distance references, composite event identities, ten internal entries across eight events, three fictional opponent clubs, full athlete lineups, official rank/time, a preserved displayed-time tie, and one N/C context route. The report derives pace, winner gap, field median, multi-start load, and shared pre-race outings while marking stage distance confirmation and performance cause as unestablished. Added a consolidated Competition Review, ten boat reports, full-field ordering, distance provenance, athlete start history, compact-navigation access, and transition scroll reset. The supplied official programme/result remain private reference inputs; every public identity and outcome is fictional.
- **Evaluation:** RED first failed on the missing competition module. GREEN then required the official-reference boundary, category rather than boat-class distance, repeated race-number safety, exact crew/athlete links, all 16 athletes, full fields, official-tie preservation, N/C abstention, and interface content. Browser QA exposed two navigation defects after the data tests passed: compact navigation hid the destination, and screen/boat transitions retained the previous scroll position. Each received a failing regression test before the main-page entry point and both scroll resets were implemented. Final web validation passes 70 tests, ESLint, and the Vinext production build. QA at the default compact viewport and 1280 × 800 confirmed the synthetic notice, consolidated scoreboard, full field, official tie, distance reference, lineup, and training-context boundary.
- **Result:** WAKE now demonstrates the complete deterministic path from club training memory to competition review. A coach can inspect the club result, then open any boat to see athletes, physical boat, preceding shared work, the whole field, official outcome, and missing human context. This is not a real regatta reconstruction, race prediction, human-coach comparison, or evidence that training caused the result.
- **Cost/runtime:** No model or external API call and US$0.00 new model cost. All competition assembly and derived metrics are deterministic. The two prior session investigations remain US$0.194118 combined; the longitudinal GPT pilot remains unexecuted.
- **Decision:** Keep the synthetic competition layer and private-reference boundary. Never connect real athlete names to the fictional club history. Treat an earlier-stage programme distance as reference-only until the exact stage programme or rulebook confirms it, and preserve official rank when displayed times tie.
- **Learning:** Race number alone is not an event identity, boat class alone is not a distance rule, and a result without training context is incomplete. Conversely, joining the records does not create causation: the product earns trust by showing the connection and its limits together.
- **Next step:** Rehearse the competition segment in the submission video, then decide whether the separately frozen longitudinal GPT comparison adds enough evaluated value to justify its four authorized starts.

### 51. Authorized longitudinal pilot with a neutral quality result

- **Hypothesis:** The bounded WAKE workflow should improve the quality of one athlete briefing and one club-priority briefing over a direct GPT call while preserving evidence and abstention boundaries.
- **Change:** After explicit US$0.80 start authorization, executed the four frozen requests with `gpt-5.6-terra`, medium reasoning, and `store: false`. The first two execution attempts were rejected before reports were produced because the strict Responses schema used unsupported `uniqueItems`, then `const` without an explicit `type`. Added regression tests before removing `uniqueItems`, enforcing explicit types, and moving duplicate-evidence rejection into deterministic verification. Preserved both rejected attempts, all successful requests, outputs, tool events, hashes, runtime, tokens, costs, and a non-scored capability audit.
- **Evaluation:** All four final reports passed the existing strict verifier. Direct baseline used 15,035 tokens and US$0.064580; bounded WAKE used 8,238 tokens, 16 tool events, and US$0.045846. Both workflows passed the same post-run capability checks for evidence coverage, trend abstention, water/indoor separation, and human review. No weighted quality rubric had been frozen before execution, so no post-hoc score was created.
- **Result:** `NO_DEMONSTRATED_QUALITY_GAIN`. Keep the reports as an honest neutral experiment. WAKE used fewer tokens and cost 29.01% less on these two scopes, but the pilot does not establish better longitudinal reasoning.
- **Cost/runtime:** Four successful reports cost US$0.110426 combined. Athlete baseline: 5,840 tokens, US$0.029740, 14.762 s. Athlete WAKE: 3,339 tokens, US$0.017008, 10.952 s. Club baseline: 9,195 tokens, US$0.034840, 12.381 s. Club WAKE: 4,899 tokens, US$0.028838, 15.777 s. Provider billing for the two schema-rejected requests is unknown and is not asserted as zero.
- **Decision:** Preserve the frozen pilot, neutral conclusion, and schema failures. Do not optimize the prompt against these two outputs or present lower cost as proof of better coaching intelligence.
- **Learning:** Strict provider schemas need API-compatibility tests in addition to local JSON Schema validation. More importantly, a negative experiment is still useful when the contract was frozen first and the result is reported without moving the goalposts.

### 52. Clean-environment, zero-cost submission reproduction

- **Hypothesis:** A reviewer should be able to reproduce WAKE's code, baseline requests, saved outputs, public verifiers, evaluation, and interface without the owner's credentials or new model spend.
- **Change:** Added `docs/REPRODUCTION_GUIDE.md`, `scripts/reproduce_submission.sh`, and RED-first contract tests. The script installs locked Python and web dependencies, explicitly unsets live credentials, runs the complete deterministic verification path, rebuilds the longitudinal capability audit, lints the interface, and builds production assets. `--verify-only` reuses installed dependencies. No paid execution flag exists.
- **Evaluation:** Contract tests verify the documented commands, credential removal, absence of `--execute`, expected US$0.00 behavior, and required outputs. The script composes existing public artifact verifiers rather than creating a second evaluation implementation.
- **Result:** Keep the zero-cost path as the primary judge workflow. Saved baseline, WAKE, investigation, evaluation, longitudinal, and competition artifacts can be inspected offline; new live prose is optional and not required for reproduction.
- **Cost/runtime:** US$0.00 model cost. Expected clean runtime is approximately 2–5 minutes, dominated by dependency download and production build; installed verification is faster.
- **Decision:** Never distribute `.env` or the owner's key. Reproduction uses committed reports; new execution requires the reviewer's key and explicit authorization.
- **Learning:** Reproducibility is not equivalent to rerunning an LLM. For a stochastic paid system, hashes, inputs, outputs, trajectories, deterministic verifiers, and offline grading are the more useful submission contract.

### 53. Loadable two-week post-regatta evolution package

- **Hypothesis:** The club-scale value becomes easier to see when the same fictional athletes and crews receive a second period whose records produce different evidence-supported outcomes without claiming that training caused them.
- **Change:** Added RED-first tests, a public manifest, and an executable 50-activity post-regatta package for the same 16 athletes and 10 crews. Added an explicit Sessions-page package entry and load state, period coverage, six evidence-ranked comparison cards, causal boundaries, and reset behavior. The comparison distinguishes faster/slower equivalent Concept2 observations, a stable range, a high-wind water confounder, a missing-participation question, and a workout with no equivalent benchmark.
- **Evaluation:** RED failed on the missing package module and UI route. GREEN verifies all athlete/crew coverage, ten weekdays, 30 water and 20 athlete-owned Concept2 records, all six scenarios, evidence references, absence of fitness/performance causation language, manifest consistency, US$0.00 load cost, no model call, ESLint, and the production build.
- **Result:** Keep the package as a replayable future-period demonstration, not as additional training data for a hidden model. It shows how WAKE gains useful club memory through new evidence and deterministic comparison while routing ambiguity explicitly.
- **Cost/runtime:** No external API or model call; US$0.00. Package load and comparison are local and deterministic.
- **Decision:** Use observed-direction labels only for compatible indoor workout shapes. Treat water changes with weather as confounded, missing records as questions, and unmatched workouts as insufficient evidence. Keep `causal_conclusion: NOT_ESTABLISHED` visible.
- **Learning:** Product evolution does not require continual fine-tuning. A trustworthy first step is accumulating structured evidence, preserving provenance, and recomputing supported comparisons while the agent is reserved for ambiguous synthesis.

### 54. Final five-minute coach-path and clean-reproduction QA

- **Hypothesis:** The submission path should communicate club scale, individual chronology, unresolved human context, session memory, competition context, and measured evaluation in under five minutes without contradictory state or a fragile local setup.
- **Change:** Rehearsed the complete route in the in-app browser, including the loaded post-regatta state and 390 × 844 responsive breakpoint. QA found a stale club message saying longitudinal synthesis had not run directly above the completed pilot; a RED copy-state regression test was added before correcting it. The clean-reproduction rehearsal also found that Node 20 reached the Vinext build despite the documented Node 22.13 requirement, and that a double-quoted shell echo expanded `$0` inside `US$0.110426`. Added fail-fast Node version validation, a repository-local ignored uv cache, and a regression test requiring literal cost output.
- **Evaluation:** Browser checks confirmed 52/52 club coverage, 10 crews, 16 athletes, Lucas Training Days, an athlete-context-pending crew, approved session memory, Competition Review, official 83.76-versus-49.00 evaluation, completed neutral longitudinal pilot, and the six-card post-regatta comparison. Mobile width had no horizontal overflow and application console logs contained no warnings or errors. With Node 24, `./scripts/reproduce_submission.sh --verify-only` passed 198 Python tests, eight public fixture/artifact verifiers, the longitudinal audit, 74 web tests, ESLint, and the Vinext production build.
- **Result:** Keep the route and the two regression fixes. The dashboard is ready for owner QA and video rehearsal at `http://localhost:3000/`.
- **Cost/runtime:** No model or external API call. The complete installed-dependency reproduction took about 28 seconds on the development machine; browser QA cost US$0.00.
- **Decision:** Correct only comprehension and reproduction blockers at this stage. Do not broaden the MVP before recording unless owner QA finds another material obstacle.
- **Learning:** A correct artifact can still tell a false story if neighboring status copy is stale. Reproduction scripts also need to validate the runtime before long tests and protect currency strings from shell expansion.

### 55. Frozen combined-club GPT memory request

- **Hypothesis:** One bounded longitudinal synthesis over the deterministic pre/post-regatta screen can preserve useful coach memory more efficiently than narrating each activity independently, while evidence references and abstention rules prevent unsupported athletic or causal conclusions.
- **Change:** Added RED-first contracts, `scripts/post_regatta_memory.py`, a six-comparison evidence packet, a compact 102-activity combined-club summary, one strict `store: false` WAKE request, hash verification, local report persistence, and a one-start CLI execution boundary. The compact input covers 16 fictional athletes, 10 crews, 68 water activities, 34 individual Concept2 activities, prior verified investigations, and the supported/conflicted/insufficient period routes without transmitting raw telemetry or private source files.
- **Evaluation:** RED failed because the post-regatta memory module did not exist. GREEN first passed three focused preflight tests for coverage, privacy fields, evidence-catalog closure, strict bounded request configuration, finite US$0.20 start authorization, zero-cost reopening, and tamper detection. After owner authorization, the committed artifact test independently revalidates the output schema, evidence catalog, frozen input hash, all four tool calls, `store: false`, cost, and persistence. A second RED-GREEN interface cycle requires the displayed headline, briefing, three priorities, and four questions to match the saved artifact exactly. The focused suites pass four Python and five web tests.
- **Result:** `VERIFIED_AND_SAVED`. The report contains six observed facts, five comparisons, three human-review priorities, four unresolved questions, and two recommendations. It preserves the three narrow comparable indoor observations, explicitly abstains from a club performance or causal trend, and treats the Atlas water result as wind-confounded. The post-regatta interface now displays the saved briefing and review queue without another call.
- **Cost/runtime:** One successful `gpt-5.6-terra` medium execution used 3,848 input tokens, 2,474 output tokens, 6,322 total tokens, two Responses calls, four tool calls, and 22.507 seconds. Approximate cost was US$0.037384 under the explicit US$0.20 start authorization; the gate was not a provider cap. Reopening costs US$0.00.
- **Decision:** Keep `store: false` and the verified structured result in WAKE. Do not expand this into one call per athlete, crew, or activity without a separate evaluated need. Present “controlled” in the model headline through the stricter interface boundary “narrow comparable observations only,” because intent, effort, recovery, equipment, environment, and physiology were not experimentally controlled.
- **Learning:** “Guardar no GPT” should not mean making provider retention the product database. Deterministic records remain the source of truth; the model creates a versioned, evidence-bound memory that the application owns and can reopen without another call. Manual review also matters after schema verification: domain wording can remain technically valid yet require a narrower presentation boundary.

### 56. Same-input combined-club baseline and final video contract

- **Hypothesis:** The most useful remaining paid validation is one direct baseline over the exact 102-activity input already analyzed by WAKE, while a timed replay script reduces delivery risk more than generating independent prose for every athlete and crew.
- **Change:** Added RED-first tests, `scripts/post_regatta_baseline.py`, a semantic input-hash equality check, one no-tool `store: false` request, tamper verification, and a seven-check capability contract frozen before execution. Added `scripts/score_post_regatta_comparison.py` before seeing the baseline result; it reports exact capability coverage and neutral, gain, regression, or mixed conclusions without weights. Added a five-minute recording script covering the simple baseline, club scale, saved intelligence, human checkpoint, competition context, measured evaluation, removed v1 behavior, neutral longitudinal result, and zero-cost reproduction.
- **Evaluation:** RED first failed because the baseline module, auditor, and video guide did not exist. GREEN verifies that the new request uses the exact semantic input hash from the saved WAKE run, receives the same schema with no tools, requires one finite US$0.20 start gate, and detects request or contract tampering. Three auditor tests prove the saved WAKE artifact passes all seven frozen checks, missing trend abstention fails exactly that check, and equal coverage produces `NO_DEMONSTRATED_CAPABILITY_GAIN`. The recording contract test requires every submission-critical segment and result value.
- **Result:** `READY_FOR_AUTHORIZATION`. The baseline input, request, capability contract, and hashes are frozen under `evaluation/post-regatta-baseline/v1/preflight/`. No new model output or quality conclusion exists yet. The video route is frozen under `docs/VIDEO_DEMO_SCRIPT.md`.
- **Cost/runtime:** Preflight and script preparation used no external API and cost US$0.00. One future direct baseline start requires a separate finite US$0.20 authorization; this gate is not a provider cap.
- **Decision:** Execute only the one discriminating baseline before considering any athlete/crew report expansion. Do not use a 24-hour asynchronous batch for this deadline-sensitive single call, and do not change the non-scored capability contract after output.
- **Learning:** Cost optimization and product evidence align here: selective calls keep provenance clearer and make each spend answer a concrete evaluation question. The strongest final story is complete deterministic coverage, bounded reasoning where ambiguity exists, and honest preservation of both positive and neutral results.

### 57. Executed club baseline and construct-validity review

- **Hypothesis:** On the exact same compact 102-activity input, the bounded WAKE workflow should preserve more of the pre-frozen machine-readable capability contract than a direct model call without tools or verification.
- **Change:** After explicit US$0.20 authorization, executed exactly one `gpt-5.6-terra` medium direct baseline with no tools and `store: false`; preserved its strict verified output, manifest, and frozen capability audit. RED-first tests now lock the authorization, input hash, cost, runtime, tokens, and a separate manual construct-validity review. The read-only Evaluation interface exposes the result and its claim boundary.
- **Evaluation:** The frozen auditor reported WAKE 7/7 and direct baseline 3/7 with `DEMONSTRATED_CAPABILITY_COVERAGE_GAIN`. Manual output review found construct sensitivity in all four failed checks: the baseline contained the three supported comparisons under different IDs, abstained from club trend outside the canonical comparison object, preserved a non-causal Atlas wind boundary under a different ID/status, and routed both verified deviations through priorities rather than recommendations. The frozen audit was not edited or rescored.
- **Result:** Accept `STRUCTURAL_FIDELITY_GAIN_ONLY`. WAKE better preserved canonical identifiers, statuses, placement, and deterministic review routes. Do not claim that this 7/7 versus 3/7 result proves semantically better coaching advice; the direct baseline expressed much of the same content. The official frozen ten-case 83.76 versus 49.00 rubric remains the primary measured quality evidence.
- **Cost/runtime:** The direct baseline used 5,236 input tokens, 2,769 output tokens, 8,005 total tokens, one Responses call, no tools, and 19.640 seconds for US$0.043700. WAKE used 6,322 tokens, 22.507 seconds, and US$0.037384. WAKE was 14.45% cheaper and used 21.02% fewer tokens, while taking 14.60% longer. Both outputs passed strict verification and reopen for US$0.00.
- **Decision:** Preserve both the positive structural result and its construct limitation. Do not spend on mass athlete/crew prose before a new fixed decision question and evaluation contract justify it.
- **Learning:** Exact schemas make product memory automatable, but an exact-contract audit can mistake equivalent prose in a different location for missing capability. Structural fidelity and semantic coaching quality are distinct outcomes and must be reported separately.

### 58. Owner QA pack and isolated end-to-end validation plan

- **Hypothesis:** A coach-facing QA run needs fixed upload data, isolated state, explicit expected outcomes, and both replay and live paths; otherwise visual inspection can miss stale-state reuse, unsupported optional-source claims, or a broken paid workflow.
- **Change:** Added a deterministic public QA-pack builder, a five-source upload directory, manifest, byte-reproducibility and privacy tests, and a 16-step owner checklist. Added `--state-store` to the dashboard launcher so QA can preserve or isolate state without deleting the normal store. The checklist covers club/crew/athlete value, post-regatta evolution, saved memory, inbox milestones, minimum and full replay uploads, competition, evaluation, validation failures, core live analysis, complete live analysis, and historical-weather live analysis.
- **Evaluation:** RED tests first failed on the absent pack, guide, live-scope manifest, and launcher option. GREEN verifies that every upload file is byte-identical to the public derived-synthetic source, no evaluator ground truth or credential is present, the pack rebuilds byte-for-byte, all 16 QA stages and claim boundaries are documented, and an isolated state path appears in the launch plan. Ten focused tests pass. A second local replay server could not be opened concurrently because Vinext correctly detected the existing dashboard; no user process was stopped and no live or external API call occurred.
- **Result:** The owner can now perform one sequential product QA run from public files. Replay QA is expected to cost US$0.00. Three live starts are deliberately pending a separate US$0.60 total operational authorization; this is not a provider cap.
- **Cost/runtime:** Pack generation and focused tests are local and cost US$0.00. No model or weather-provider request occurred in this change.
- **Decision:** Finish the product QA before rewriting the demonstration video. Treat every owner finding as one of comprehension, rowing-language, functional, evidence-boundary, or visual issues before deciding what to fix.
- **Learning:** Saved outputs make demonstrations reliable, but only fresh isolated state and real file selection reveal whether ingestion and workflow transitions still work. Replay credibility and live operability must be tested separately.

### 59. Product-first five-minute story

- **Hypothesis:** A video organized around a coach, athlete, crew, and accumulating club memory will communicate WAKE's value more clearly than a narration organized around parsers, tools, schemas, and verification stages, while a short evidence segment can still satisfy the technical judging requirements.
- **Change:** Added a RED-first recording-contract test for explicit coach/athlete audience, an 85/15 product-to-technical split, the club-to-session-to-human-to-longitudinal-to-competition route, and the boundary that detailed architecture remains in the repository. Rewrote the five-minute script around the human problem, Harbor Men 2x, the investigated session, complementary athlete/coach authority, Lucas Training Days and Concept2, 102 club activities, Competition Review, then the fixed-case result and failed experiment. Removed the former forty-second narration of deterministic processing and four tools from the primary story.
- **Evaluation:** The new contract initially failed against the technical-first script and passed after the rewrite. The script still contains the required simple baseline, one end-to-end path, 83.76 versus 49.00 comparison, visible regression, removed experiment, changelog learning, and zero-cost reproduction boundary. The timed narration is approximately 630 spoken words before owner rehearsal.
- **Result:** `READY_FOR_OWNER_QA`, not recording-frozen. The first minute is now understandable without software vocabulary, implementation detail supports credibility rather than leading the pitch, and the close returns to joint coach/athlete value.
- **Cost/runtime:** Documentation and local tests only; US$0.00 and no model or weather request.
- **Decision:** Sell the product outcome in the video and let the repository sell the implementation depth. Do not remove technical evidence; relocate it to the final evaluation/failure segment and submission documentation.
- **Learning:** Judges need both emotional clarity and reproducible evidence, but those do not need equal screen time. Showing the user's decision first makes the later technical proof easier to interpret.

### 60. Eleven v3 generation-ready voiceover sheet

- **Hypothesis:** Seven context-rich, independently generated clips with sparse delivery tags will be easier to time and selectively regenerate than either one five-minute request or nine short prompts, without mixing recording directions into spoken output.
- **Change:** Added a RED-first submission test and `submission/video/VOICEOVER_ELEVENLABS_V3.md`. The sheet maps the complete product-first narration to seven named MP3 outputs, uses `eleven_v3` inline tags for thoughtfulness, confidence, warmth, measured delivery, reflection, and short pauses, and writes ambiguous figures such as 83.76 and 49.00 as spoken English. Screen and editing directions remain exclusively in the master video script.
- **Evaluation:** RED failed because no generation sheet existed. GREEN verifies seven text prompts, required delivery tags, spoken evaluation values and closing tagline, absence of SSML and screen instructions, and at least 250 characters of context in every prompt. The sheet follows the current ElevenLabs distinction: Eleven v3 uses audio tags and does not support SSML break tags.
- **Result:** `READY_TO_GENERATE`; no audio has been generated or reviewed yet. The seven target windows cover the complete five-minute timeline.
- **Cost/runtime:** Documentation and local tests only; US$0.00. ElevenLabs generation cost and duration remain unmeasured until the owner executes the API calls.
- **Decision:** Generate each clip separately with one consistent voice and the `eleven_v3` model. Regenerate only clips that miss tone, pronunciation, or target duration; do not alter the evidence claims during voice tuning.
- **Learning:** TTS input is a production artifact, not a copy-paste of the recording document. Segment size, spoken-number normalization, and model-specific pause syntax materially affect reproducibility.

## Entry template

### 61. Owner replay QA remediation before paid validation

- **Hypothesis:** Fixing the owner-observed replay blockers before live execution will prevent stale intake state, inaccessible saved intelligence, and missing mobile navigation from contaminating the paid QA results.
- **Change:** Preserved the owner notes and consolidated QA-01 through QA-12 in `docs/OWNER_QA_GUIDE.md`. Added RED-first regression tests for reopening saved club memory, starting a genuinely fresh review, preventing duplicate preparation, consistent `Environment timeline` naming, and keeping primary navigation reachable at mobile width. Hoisted the post-regatta demonstration state, added a permanent Goal memory entry for the saved 102-activity report, added explicit preparation success and start-over actions, reset intake-local state through a versioned remount, and converted the narrow header into a horizontally scrollable navigation row.
- **Evaluation:** The four new behavioral tests initially failed against the owner-reported behavior and passed after the smallest implementation changes. The focused suite passes 27/27, the complete web suite passes 79/79, ESLint passes, the Vinext production build passes, and the owner QA-pack suite passes 4/4. The complete Python suite runs 217 tests with one known failure caused by the separately edited two-character first voice-over prompt; that user-owned draft was preserved rather than silently rewritten. Browser DOM inspection confirms all four primary navigation actions are present in the running interface. The owner still needs to repeat the four visual fix checks and the deferred non-empty QA-08 persistence check before live QA.
- **Result:** `READY_FOR_OWNER_FIX_VERIFICATION`. QA-07 and QA-12 remain historically recorded as failures from the first run; the guide now separates those observations from the required recheck. No live model or weather request occurred.
- **Cost/runtime:** Local tests, lint, build, and browser inspection only; US$0.00.
- **Decision:** Do not proceed to the three paid live starts until the owner verifies saved-memory navigation, fresh intake state, preparation completion feedback, mobile navigation, and saved-session persistence. A passed code regression test does not overwrite a failed human QA observation.
- **Learning:** Interface state is part of product evidence. A correct saved artifact is not useful if users cannot find it again, and a technically responsive layout still fails when navigation disappears. Human QA results should remain immutable evidence with remediation recorded separately.

### 62. Owner live QA, route-bearing recovery, and coach-readable reconstruction

- **Hypothesis:** The final owner run should validate not only that paid paths
  execute, but also whether their evidence and presentation are usable by a
  coach. GPS-derived direction, constrained timezone entry, stable mobile
  actions, and scannable reconstruction should address the observed problems
  without changing historical model outputs or weakening abstention.
- **Change:** Preserved three synthetic live trajectories from QA-14 through
  QA-16 and consolidated their exact cost, token, runtime, and verification
  results. Added RED-first regressions for the mobile review action, timezone
  selector, readable reconstruction, human-readable evidence labels, and
  SpeedCoach GPS heading derivation. The assembler now calculates a circular
  representative bearing only for directionally consistent GPS tracks;
  session-context heading still wins, and turning or out-and-back tracks remain
  unresolved. `Current reconstruction` now renders as separate bullets and
  translates internal references into `Training plan`, `SpeedCoach recording`,
  `Mobile recording`, `Environment timeline`, and `Session context`; verified
  finding tags use the same product vocabulary.
- **Evaluation:** RED reproduced the action wrapping below the mobile header,
  free-form timezone input, absent reconstruction formatter, exposed
  `input/*.json` references, and missing heading in a Plan + SpeedCoach weather
  bundle. Browser review then found that the six-interval chart widened the
  complete 390 px page; a second RED requires the grid child to shrink and the
  chart to own its horizontal scroll. GREEN passes 17 focused web tests and 11
  bundle-assembler tests. A 390 × 844 browser check confirms no document-level
  overflow while the header action remains on its first row. The complete web
  suite passes 84/84 with lint and production build. All three saved
  trajectories independently report `verification.passed: true`.
  The original QA-16 output remains unchanged and still records the limitation
  that triggered the correction.
- **Result:** QA-13 passed before spend. QA-14 used 34,675 tokens, 38.793 seconds,
  and US$0.117390. QA-15 used 34,927 tokens, 26.056 seconds, and US$0.099324.
  QA-16 used 20,960 tokens, 21.241 seconds, and US$0.067120. The observed live
  total was 90,562 tokens and US$0.283834 under the US$0.60 total operational
  authorization. Keep the deterministic corrections; visual owner recheck of
  the revised header and reconstruction remains useful.
- **Cost/runtime:** No additional model or weather call was made while fixing
  the findings. The three owner-authorized executions above are the complete
  new cost. Reopening their saved output costs US$0.00.
- **Decision:** Treat the owner findings as product evidence, not cosmetic
  feedback. Keep provenance internally exact while presenting source names in
  rowing language. Never infer boat-relative wind from an inconsistent route,
  and do not regenerate a paid historical report merely to erase a discovered
  limitation.
- **Learning:** Passing schema verification is necessary but not sufficient.
  Human QA exposed both a real evidence-flow omission and a reading burden that
  isolated tests had missed. The strongest audit trail preserves the original
  failure, adds a deterministic regression, and records the correction
  separately.

### 63. Visible product location and restorable internal navigation

- **Hypothesis:** One consistent back action plus a breadcrumb should let a
  coach understand whether they are reviewing a session, athlete, crew, boat,
  or product result, while browser Back should restore the preceding WAKE
  context instead of leaving the single-page application.
- **Change:** Added RED-first history-state and interface contracts, one shared
  `LocationTrail`, and internal `pushState`/`popstate` navigation. History
  entries retain selected crew, athlete, and competition-entry identifiers.
  Removed inconsistent `Back to club`, `Back to sessions`, `Back to
  competition`, and `Review evidence` header actions. Competition boat reports
  now participate in the same history as primary screens.
- **Evaluation:** RED failed on the absent history module, location trail,
  native Back integration, and inconsistent screen-specific labels. GREEN
  passes two pure history tests and the expanded interface contract. The full
  web suite passes 87/87 with lint and production build. Browser rehearsal
  verified `Harbor Men 2x → Lucas → Back` and `Competition Review → Harbor Men
  2x → Back`, restoring both heading and breadcrumb. A 390 × 844 check found no
  document-level overflow and kept the arrow and current item visible.
- **Result:** Keep the unified navigation. Detail screens now state the product
  area and selected object in one predictable place, and both the visible arrow
  and browser Back follow the same internal path.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Treat location and return behavior as part of the workflow
  contract, not cosmetic navigation. Preserve selected relational context in
  history and avoid adding screen-specific back controls.
- **Learning:** A technically reachable page can still feel like a dead end.
  Navigation state must preserve the human object being investigated, not only
  a generic screen name.

### 64. Task-based Sessions workspace

- **Hypothesis:** Separating the Sessions root by coaching task will make every
  existing feature directly reachable without removing evidence or forcing a
  coach to scan one long mixed-purpose page.
- **Change:** Added RED-first contracts for five Sessions areas, mobile-contained
  horizontal selection, and restoration of the selected area through browser
  history. Reorganized the existing club content into Overview, Attention,
  Team, Intelligence, and Session reviews. No data, analysis, or feature was
  removed.
- **Evaluation:** RED failed because Sessions rendered one complete sequence and
  history stored only the primary screen and relational selection. GREEN passes
  the complete 91-test web suite and ESLint. The Vinext production build passes
  with the repository-required Node runtime. Browser rehearsal confirmed Team
  → Harbor Men 2x → Back restores Team, Session reviews exposes its inbox in a
  1,337 px page at the tested desktop viewport, and a 390 × 844 viewport has no
  document overflow while all five choices remain reachable in the selector.
- **Result:** Keep the task workspace. The long product inventory is now five
  explicit destinations, and each drill-down returns to the coach's preceding
  task context.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Use progressive disclosure for club-scale information. Preserve
  one Sessions destination in primary navigation, but do not require page
  length to communicate product breadth.
- **Learning:** Content completeness and navigability are separate qualities.
  A coach can understand every section and still fail to use the product if
  unrelated tasks stand between the current question and the relevant view.

### 65. Visible mobile Sessions choices

- **Hypothesis:** Showing every Sessions area simultaneously on a narrow screen
  will make the workspace structure discoverable without increasing the
  desktop navigation burden.
- **Change:** After owner review rejected the horizontally scrolling mobile
  selector, added a RED-first contract for a two-column mobile button grid.
  Overview, Attention, Team, and Intelligence occupy two rows; Session reviews
  spans the final row. Desktop distribution and navigation history are
  unchanged.
- **Evaluation:** RED proved the former CSS still required horizontal scrolling
  and hid later choices outside the viewport. GREEN passes the focused
  Sessions workspace tests. Browser checks at 390-class and 320 px widths found
  all five button rectangles inside the selector, equal selector client and
  scroll widths, and equal document client and scroll widths.
- **Result:** Keep the fully visible mobile grid and remove horizontal discovery
  from the QA instructions.
- **Cost/runtime:** Deterministic CSS and test work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Primary workspace destinations must remain visible on small
  screens. Horizontal scrolling is acceptable for dense data, not for a short
  set of five primary task choices.
- **Learning:** Reachable is not the same as discoverable. A hidden navigation
  item without an explicit overflow cue behaves like a missing feature for a
  user who does not already know it exists.

### 66. Sessions secondary-tab hierarchy

- **Hypothesis:** Placing the five Sessions areas directly below the primary
  menu will communicate their parent-child relationship more clearly than a
  selector embedded after the page notice and heading.
- **Change:** Added a dedicated `SessionsSubnavigation` between the global
  header and Sessions content. Restyled the five destinations as compact tabs
  with an active underline, removed the duplicated selector from the page body,
  and retained the fully visible two-column mobile grid.
- **Evaluation:** A RED-first contract failed because no secondary-navigation
  component existed and the selector still lived inside `SessionsScreen`.
  GREEN passes all four focused workspace tests. Browser checks at 1,280 px and
  390 px found the secondary bar beginning exactly at the primary-header edge,
  all five tabs visible, no document or selector overflow, and Team updating
  both the active tab and page heading. The responsive override was reset after
  inspection.
- **Result:** Keep the two-level navigation. Global product destinations and
  Sessions-specific coaching tasks are now visually distinct before any page
  content begins.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Treat Sessions areas as navigation, not content. Preserve the
  mobile grid because a tab hierarchy does not justify hiding choices.
- **Learning:** Progressive disclosure also needs visible information
  architecture. Moving the same controls a few hundred pixels can change
  whether users understand them as destinations or as another dashboard card.

### 67. Compact live/replay status disclosure

- **Hypothesis:** A persistent status icon with details on demand will preserve
  the live/replay safety boundary while reducing repeated text before the
  coach's task content.
- **Change:** Replaced the generic `PrototypeNotice` component with a global
  `RuntimeStatusIndicator` immediately before Review a session. The indicator
  distinguishes local live from replay/not-live, opens on hover, keyboard
  focus, or click, and retains the full former explanation in an accessible
  pop-up. Dataset-specific provenance notices were not removed.
- **Evaluation:** A RED-first interface contract failed on the absent status
  component, repeated prototype notices, and missing mobile pop-up boundary.
  GREEN passes all 18 focused product-interface tests. Browser inspection
  confirmed the icon appears before the review action, the closed pop-up is
  absent from layout, click exposes the complete live description, and the
  pop-up remains inside a 320 px viewport with equal document client and scroll
  widths.
- **Result:** Keep the compact global status. Runtime awareness remains visible
  on every primary screen without forcing users to reread the same paragraph.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Runtime mode belongs beside the action that may execute work.
  Preserve the full wording in the disclosure rather than abbreviating the
  safety boundary.
- **Learning:** Important context does not need permanent visual dominance.
  Consistent placement plus explicit interaction can improve both safety and
  reading flow.

### 68. Explicit-only runtime disclosure

- **Hypothesis:** Removing automatic hover/focus opening and instructional copy
  will make the compact runtime control feel calmer and more intentional.
- **Change:** Revised the status pop-up to open only from click, tap, or keyboard
  button activation and close on the next activation. Removed the `Hover,
  focus, or click` footer and the CSS hover/focus triggers. The runtime label and
  complete material boundary remain unchanged.
- **Evaluation:** RED-first assertions failed against the retained footer and
  automatic CSS triggers. GREEN passes all 18 focused product-interface tests.
  Browser inspection confirmed the pop-up is hidden initially, opens with
  `aria-expanded=true` after activation, and contains no interaction
  instruction.
- **Result:** Keep the explicit-only behavior. Entry 67 remains the historical
  first compact implementation but its hover/focus behavior is superseded.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Do not explain obvious control mechanics inside the content
  being disclosed. Preserve keyboard operation through native button
  activation rather than automatic focus behavior.
- **Learning:** Progressive disclosure should reduce noise, including the noise
  created by explaining the disclosure itself.

### 69. Timed runtime pop-up dismissal

- **Hypothesis:** Automatically closing the runtime explanation after six
  seconds will prevent a transient safety disclosure from obscuring navigation
  or content when the user does not manually close it.
- **Change:** Added a six-second dismissal timer whenever the runtime pop-up is
  opened. The effect clears its pending timeout on early close or component
  cleanup, while the existing second-click behavior remains available.
- **Evaluation:** A RED-first contract failed on the absent timeout and cleanup.
  GREEN passes all 18 focused product-interface tests. Browser validation
  observed `aria-expanded=true` immediately after click and
  `aria-expanded=false` with `display:none` after 6.25 seconds.
- **Result:** Keep the timed dismissal at six seconds.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** The pop-up may disappear automatically, but its status icon
  remains persistent and can reopen the explanation at any time.
- **Learning:** Compact overlays need an exit path even when their content is
  important; persistence belongs to the status indicator, not the overlay.

### 70. Evaluation saved-artifact information indicator

- **Hypothesis:** Moving the permanent Evaluation no-model banner into a small
  on-demand control will preserve submission credibility while giving the
  measured result more visual priority.
- **Change:** Removed the full-width Evaluation notice and added a small
  information indicator at the right of the page heading. It preserves the
  complete `Saved result · No model call` explanation, supports click/tap and
  keyboard activation, closes on a second activation, and dismisses after six
  seconds.
- **Evaluation:** A RED-first Evaluation contract failed on the absent
  indicator, retained banner, and missing right-aligned pop-up styles. GREEN
  passes both focused Evaluation tests. Browser inspection confirmed the old
  notice count is zero, the icon is visible on the right half of the header,
  the closed pop-up does not occupy layout, click exposes the complete boundary,
  the document has no horizontal overflow, and the pop-up closes after 6.25
  seconds.
- **Result:** Keep the compact Evaluation disclosure and the full text inside
  it. The underlying read-only/no-cost behavior is unchanged.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Stable, non-actionable page boundaries should be available on
  demand rather than repeated as permanent banners.
- **Learning:** Safety copy remains credible when visually quiet, provided the
  indicator is consistently placed, accessible, and explicit when opened.

### 71. Accessible typography and shared card system

- **Hypothesis:** Replacing scattered 6–72 px declarations with a bounded
  semantic scale will make dense rowing evidence easier to scan without
  flattening the hierarchy or creating mobile overflow. Subtle shared card
  surfaces should clarify actionable groups without turning every table row
  into a decorative container.
- **Change:** Added reusable typography, line-height, radius, and elevation
  tokens. Descriptive copy now resolves to at least 14 px, captions to 12 px,
  compact metadata to 11 px, and primary display headings are capped at 58 px.
  Added late compatibility rules for older feature-specific selectors, shared
  surface treatment for prominent evidence cards, consistent interactive-row
  hover/focus states, and reduced-motion handling.
- **Evaluation:** Three RED-first design-system contracts failed before the
  tokens and shared rules existed. GREEN passes the complete 96-test web suite,
  lint, and production build. Before the change, the Evaluation page exposed
  344 visible leaf labels between 7 and 10 px and a 60.78 px title at the
  inspected desktop width. After the change, Evaluation and Sessions have no
  visible text below 11 px; the title computes to 50.65 px. Browser checks of
  Sessions areas, intake, goal memory, crew and athlete details, competition
  overview and boat detail, longitudinal reports, and post-regatta memory found
  no text below 11 px or document overflow. The 390 × 844 mobile checks also
  found zero overflow and zero sub-11 px text.
- **Result:** Keep the bounded scale and shared surface language. This is an
  accessibility-oriented legibility baseline, not a claim of formal WCAG
  conformance; keyboard, contrast, zoom, and assistive-technology audits remain
  separate verification work.
- **Cost/runtime:** Deterministic CSS, tests, and browser inspection only; no
  model, weather, or external API call and US$0.00 incremental cost.
- **Decision:** Product descriptions and evidence explanations must never rely
  on microtype. Reserve 11 px for terse metadata, keep normal copy at 14 px or
  above, and use elevation only for meaningful groups or interactive rows.
- **Learning:** Dense operational software becomes harder to understand when
  hierarchy is created mainly by making secondary text tiny. A constrained
  scale preserves density more effectively than isolated font-size fixes.

### 72. Single global session-review action

- **Hypothesis:** Removing the second `Review a session` button from the
  Sessions page heading will eliminate a redundant choice without making the
  evidence-intake workflow harder to reach.
- **Change:** Removed the content-level review button from `SessionsScreen` and
  kept the persistent global action beside the runtime indicator. Removed its
  now-unused narrow-screen width override.
- **Evaluation:** A RED-first regression test found two rendered source actions
  before the change. GREEN leaves exactly one action in the application source
  and none inside `sessions-workspace-heading`. Browser checks found one visible
  global action and zero heading actions across all five Sessions areas on
  desktop; at 390 x 844 the global action remained visible, the heading action
  remained absent, and document overflow was zero.
- **Result:** Keep one global session-review entry point.
- **Cost/runtime:** Deterministic interface, test, and browser inspection only;
  no model, weather, or external API call and US$0.00 incremental cost.
- **Decision:** Session review begins from the global header action. Sessions
  area headings provide location and purpose, not a duplicate workflow action.
- **Learning:** A persistent action does not become more discoverable when it is
  repeated immediately below the navigation; repetition instead makes the
  interface hierarchy look accidental.

### 73. Period-aware club pulse heading

- **Hypothesis:** Replacing the fixed two-week title and date with a neutral
  heading plus dataset-derived coverage will keep the club pulse truthful as
  new training periods are loaded. Moving the scan label below the introduction
  should restore a clear vertical reading order.
- **Change:** Renamed the heading to `Club training pulse`, renamed the lower
  funnel to `Activity validation funnel`, and added `formatAnalysisPeriod` to
  derive training-day count and date range from the active dataset period. The
  deterministic status is now inside the heading copy, below its description,
  and its verified-investigation count is data-derived.
- **Evaluation:** RED-first tests failed on the missing period formatter, fixed
  two-week labels, and old heading structure. GREEN passes all 19 focused
  display, club, and intelligence tests. Browser inspection rendered
  `10 training days · 17–28 Aug 2026`, found the status below and left-aligned
  with the introduction, and found no overflow at desktop or 390 x 844.
- **Result:** Keep a period-neutral title and make coverage metadata dynamic.
- **Cost/runtime:** Deterministic interface, formatting, tests, and browser
  inspection only; no model, weather, or external API call and US$0.00 cost.
- **Decision:** Dataset duration belongs in derived metadata, not in a fixed
  product heading. Status labels follow the explanatory copy they qualify.
- **Learning:** A demo-specific duration presented as a product title silently
  becomes false as soon as the product accepts a longer or shorter history.

### 74. Bookmarkable product routes and nested-only Back

- **Hypothesis:** Giving every primary destination and detail a readable hash
  route will make browser Back/Forward and bookmarks reliable. Hiding the WAKE
  Back trail on primary destinations will remove a false parent relationship.
- **Change:** Added deterministic hash serialization and restoration for
  Sessions areas, crew and athlete detail, club intelligence, Competition and
  boat reports, session-review steps, Goal memory, and Evaluation. The shared
  location trail now renders only for nested views. Directly bookmarked details
  receive a meaningful parent fallback when no in-app history exists.
- **Evaluation:** RED-first navigation tests failed on missing hash functions,
  missing bookmark restoration, and unconditional non-Sessions trail rendering.
  GREEN passes 30 focused navigation and interface tests. Browser rehearsal
  confirmed `#competition`, `#goal-memory`, and `#evaluation` render without a
  trail; a boat report receives its encoded entry route and Back returns to
  Competition; browser Back restored Goal memory from Evaluation; and a direct
  `#sessions/team/athlete/athlete-sofia` bookmark survived reload. At 390 x 844,
  top-level and nested views had zero document overflow.
- **Result:** Keep readable hash routes and nested-only location trails.
- **Cost/runtime:** Deterministic navigation, tests, and browser inspection
  only; no model, weather, or external API call and US$0.00 cost.
- **Decision:** Primary destinations do not display an in-product Back control.
  Their nested objects do. The URL must identify the current product state.
- **Learning:** History state without a URL can make Back work during one visit,
  but it cannot support bookmarks, reloads, shared QA paths, or visible location.

### 75. On-demand competition provenance

- **Hypothesis:** Replacing the permanent synthetic-regatta banner with a
  compact disclosure will keep the evidence boundary available without making
  implementation context compete with the coach's competition review.
- **Change:** Removed the two full-width competition provenance notices and
  added one accessible information control at the right of the Competition
  heading. Overview and boat detail receive context-specific wording. The
  disclosure supports click, tap, and keyboard activation, closes on a second
  activation, and dismisses automatically after six seconds.
- **Evaluation:** A RED-first competition contract failed on the missing
  component, retained banners, and absent compact styles. GREEN passes all
  eight focused competition tests. Browser rehearsal found zero legacy notices,
  one indicator inside each relevant header, the expected overview and boat
  disclosure text, automatic dismissal after 6.25 seconds, and no mobile
  horizontal overflow.
- **Result:** Keep competition provenance on demand while leaving race evidence,
  context, uncertainty, and coaching value visible in the main page.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Main product surfaces explain what a coach can learn and which
  conclusions remain unsupported. Stable implementation and fixture provenance
  belongs in accessible disclosures and documentation unless it directly
  changes the user's current decision.
- **Learning:** Transparency does not require every technical boundary to be a
  permanent card. Progressive disclosure can preserve trust while returning
  the visual hierarchy to the rowing task.

### 76. Compact club-fixture context

- **Hypothesis:** Removing repeated processing and fixture explanations from
  the top of the club pulse will make the first screen read as a coaching tool
  while preserving the synthetic-data boundary on demand.
- **Change:** Replaced the permanent deterministic-status label, two-column
  provenance block, and repeated investigation boundary with one `Synthetic
  demo` control beside the period-aware club heading. Its six-second disclosure
  states which rowing structures and source formats are real-informed and which
  identities and outcomes are fictional. Existing coverage, investigation,
  routing, and observed-cost metrics remain visible in their operational cards.
- **Evaluation:** RED-first club contracts failed on the absent disclosure and
  retained legacy blocks. GREEN passes all 16 focused club and intelligence
  tests. Browser rehearsal found zero legacy blocks, one accessible control,
  the complete provenance text, automatic dismissal after 6.25 seconds, and no
  horizontal overflow with both control and pop-up inside a 390 px viewport.
- **Result:** Keep fixture provenance available through the compact club label;
  do not repeat deterministic implementation narration above the club metrics.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Put club-scale progress in operational metrics and put stable
  demonstration provenance in an on-demand disclosure. Main-page copy should
  describe the coach's task and the rowing evidence, not the implementation.
- **Learning:** A business rule can be transparent without becoming a content
  section. Repeating the same assurance as a label, a card, and a boundary
  weakens rather than strengthens the hierarchy.

### 77. Interface copy audit and visible product shortcuts

- **Hypothesis:** Separating coach-facing guidance from stable implementation
  context will make the product faster to scan. Replacing two visually weak
  header buttons with icon-based shortcut cards should make Evaluation and
  Competition recognizable as intentional destinations.
- **Change:** Audited permanent notes and descriptions across the product.
  Removed the repeated Sessions navigation instruction, the duplicate Session
  reviews introduction, full-width local-storage note, validation-fixture block,
  and repeated crew/athlete synthetic-data banners. Storage, validation source
  context, and club-fixture provenance now use six-second disclosures. Replaced
  the two generic Overview buttons with accessible Evaluation and Competition
  shortcut cards containing distinct icons, purpose labels, strong titles, and
  directional affordances. Interpretation boundaries that change a coaching
  conclusion remain visible.
- **Evaluation:** RED-first contracts covered shortcut semantics and styling,
  storage and validation disclosures, removal of legacy blocks, and reuse of
  the club disclosure on crew and athlete pages. GREEN passes all 42 focused
  workspace, club, intelligence, and product-boundary tests. Browser rehearsal
  confirmed both shortcuts navigate to their bookmarkable destinations, the
  legacy blocks are absent, disclosures expose their complete text, crew and
  athlete headers retain provenance, and desktop/mobile layouts have no
  horizontal overflow. At 390 px both shortcuts are full-width single-column
  controls.
- **Result:** Keep the cleaner product hierarchy. Evaluation remains the home
  of model comparison, scores, cost, and technical claim boundaries; those
  details are not repeated on the operational club screens.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Use three copy layers: visible operational content for the
  coach's task and interpretation; on-demand disclosures for stable provenance,
  storage, and runtime context; Evaluation or documentation for model and
  experimental methodology.
- **Learning:** Removing text indiscriminately would hide necessary uncertainty.
  The useful dividing line is whether the information changes the current
  coaching interpretation or merely explains how the prototype was built.

### 78. Aligned review-state cards and compact PM5 context

- **Hypothesis:** Equal card insets and shared metric rows will make the four
  session-review states easier to compare. Moving the stable Concept2
  interpretation boundary into a labeled disclosure will reduce visual weight
  without hiding a material cross-modality limitation.
- **Change:** Rebuilt the four review-state cells as an explicit surfaced grid
  with uniform padding, aligned label/value/description rows, and equal mobile
  card heights. Replaced the permanent PM5 boundary block with a `PM5 context`
  control beside the Training days heading. Its six-second disclosure preserves
  athlete ownership, equivalent-workout comparison, and the limits on inferring
  on-water speed, visible technique, or muscular strength.
- **Evaluation:** RED-first contracts failed for the missing aligned grid and
  PM5 disclosure, then passed after the smallest implementation. Browser
  rehearsal measured four equal 134 px cards at 390 px, zero horizontal
  overflow, zero legacy PM5 blocks, and one accessible disclosure containing
  all three interpretation bullets.
- **Result:** Keep the aligned state grid and compact PM5 context control.
- **Cost/runtime:** Deterministic interface work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** Stable modality rules may use a labeled disclosure when the
  surrounding UI already states the active modalities and the complete limit
  remains available in one action.
- **Learning:** CSS subgrid aligns metric rows well on wide layouts, but its
  spanning tracks can ignore a child's minimum height at narrow widths. The
  mobile override must leave the subgrid and define local rows to guarantee
  equal card geometry.

### 79. Submission readiness audit and representative human-gated trajectory

- **Hypothesis:** A deterministic readiness gate and one literal end-to-end
  checkpoint trace will expose submission drift that feature tests cannot,
  while keeping the intentionally deferred final video separate from code and
  evidence readiness.
- **Change:** Consolidated owner comments and historical findings into one QA
  result table; added a requirement-to-evidence compliance matrix, direct
  dependency/service/data-rights inventory, owner live-QA manifest with hashes,
  and a no-key readiness verifier. Restored the incomplete first ElevenLabs
  prompt and removed QA annotations from the generation sheet. Added a
  deterministic public replay trajectory that links the official agent tool
  trace to a synthetic human answer, briefing verification, and coach-approved
  memory transition. Updated stale architecture, interface, batch, cost, and
  reproduction statuses to the completed results.
- **Evaluation:** RED-first submission tests failed on the missing readiness
  module, absent reproduction command, `- OK` annotations, and the two-character
  voice prompt. A second RED-first contract failed on the absent product
  trajectory builder. The first full reproduction then caught one broken
  literal QA contract introduced by the documentation cleanup; restoring the
  exact button, cost, and result language made it GREEN. The final reproduction
  passes 223 Python tests, nine public verifiers, 110 web tests, lint, and the
  production build. The readiness CLI reports 10 WAKE outputs, 10 baseline
  outputs, 10 official trajectories, 3/3 verified owner live-QA runs, and
  `PENDING_FINAL_VIDEO` with repository evidence ready.
- **Result:** Keep a two-gate closeout: deterministic repository readiness now,
  then a strict final-video gate after recording. The final manual QA rechecks
  remain visible rather than being relabelled as owner passes.
- **Cost/runtime:** Deterministic repository work only; no model, weather, or
  external API call and US$0.00 incremental cost.
- **Decision:** The final submission is not called fully ready until the video
  exists, the targeted owner rechecks pass, the clean reproduction succeeds,
  and the strict readiness command passes from the final checkout.
- **Learning:** Submission compliance is a product contract of its own. Tests
  can prove saved evidence and artifact completeness, but they must not
  substitute for the owner's visual acceptance or the final editorial review.

### 80. Made clean-environment reproduction side-effect free

- **Hypothesis:** A judge should be able to reproduce the submission without a
  paid call and without changing any frozen evidence in the checkout.
- **Change:** Redirected the timestamped post-regatta capability-audit rebuild
  to an isolated temporary directory that is removed when the reproduction
  exits. Documented the no-mutation contract in the reproduction guide and
  decisions log.
- **Evaluation:** A RED-first regression test proved the script still wrote to
  the tracked official audit. The test requires an isolated temporary path and
  rejects the tracked output destination; shell syntax, focused tests, and the
  full zero-cost reproduction verify the corrected behavior.
- **Result:** Keep. Public verification now inspects the frozen result while
  treating its rebuilt timestamped audit as disposable evidence.
- **Cost/runtime:** Deterministic repository verification only; no model,
  weather, or external API call and US$0.00 incremental cost.
- **Decision:** Reproduction commands must be idempotent with respect to frozen
  tracked evaluation artifacts.
- **Learning:** Content-equivalent generated JSON can still dirty a submission
  through timestamps. Reproducibility includes filesystem side effects, not
  only numerical equality.

### 81. Migrated crew labels and added a bounded source package

- **Hypothesis:** Familiar Brazilian bird names will make the fictional club
  easier to remember, while a source-only upload will reduce submission risk
  without changing any rowing evidence or paid evaluation result.
- **Change:** Renamed the physical boats Tucano, Arara, Bem-te-vi, Sabiá,
  Gavião, Garça, Canário, Seriema, Carcará, Tuiuiú, plus spare 1x Biguá, and
  renders every crew as `Crew: boat name - class - category`. Preserved all
  stable IDs, lineups, sessions, metrics, and frozen paid artifacts. Updated
  current QA and narration guidance. Added a deterministic
  ZIP builder that excludes credentials, private data, dependencies, runtime
  state, build output, and MP4 files, applies a conservative 50 MiB ceiling,
  and reports a SHA-256 digest. Removed the personal repository URL from video
  draft 12's closing card.
- **Evaluation:** The crew-name contract failed first against the former
  labels, then 25 focused club, competition, and post-regatta tests passed.
  Two source-package tests failed before the builder existed and now verify
  exclusions and byte reproducibility. Two documentation-contract tests also
  passed. The first full run also caught a stray Finder `.DS_Store` in the
  public QA pack; moving that recoverable metadata out restored byte
  reproducibility. The final verification passes 226 Python tests, nine public
  verifiers, 111 web tests, lint, and the production build. The generated
  working-tree package contains 680 files and measures 7.23 MiB.
- **Result:** Keep. The interface gains a coherent fictional identity without
  invalidating evidence hashes, and the source upload remains far below the
  local conservative ceiling.
- **Cost/runtime:** Deterministic code, tests, packaging, and video editing
  only; no model, weather, or external API call and US$0.00 incremental cost.
- **Decision:** Treat crew names as presentation data over stable IDs; keep
  frozen model artifacts immutable. Deliver source and video separately and
  verify the organizer portal's actual size rule before upload.
- **Learning:** Cosmetic labels can still cross model evidence, QA, narration,
  and packaging. The safe migration boundary is the stable entity ID, not a
  global search-and-replace over historical artifacts.

### 82. Corrected the intermediate-width intake capture layout

- **Hypothesis:** The session-intake shot will remain understandable when the
  global action retains a readable label and each file-state control stays
  attached to the evidence description at intermediate responsive widths.
- **Change:** Removed the mobile-only replacement of `Review a session` with an
  ambiguous plus sign, tightened the mobile header spacing, and explicitly
  placed `Choose` or `Selected` in the evidence-content column below its file
  description. Added a capture rule for 1440 × 900 desktop footage plus a 600
  px breakpoint check before export. Recorded draft 12's `01:16` frame as a
  known defect that must be replaced rather than hidden by cropping.
- **Evaluation:** A RED-first interface contract reproduced the plus-only CTA
  and absent mobile grid placement. GREEN passes all 20 focused interface
  boundary tests. Browser QA at 600 × 900 confirmed a 108 px-wide
  `Review a session` action, zero document overflow, and five file controls
  sharing the same left edge as their evidence descriptions rather than their
  numeric indexes. A second 320 × 844 check retained the full action label and
  equal document client and scroll widths. The complete 112-test web suite,
  lint, and production build pass.
- **Result:** Keep the responsive correction and recapture the affected video
  shot before final export. Draft 12 remains review-only evidence.
- **Cost/runtime:** Deterministic CSS, tests, browser inspection, and recording
  guidance only; no model, weather, or external API call and US$0.00.
- **Decision:** Do not treat an intermediate responsive layout as acceptable
  desktop footage merely because it fits the canvas. Capture viewport and
  component alignment are part of video acceptance.
- **Learning:** A breakpoint can pass narrow mobile and wide desktop QA while
  still producing a poor editorial frame between them. Video QA needs one
  explicit intermediate-width check for screens with multi-column controls.

### 83. Reframed the final video around the current product interface

- **Hypothesis:** Enlarging the interface and reducing explanatory copy will
  make the five-minute story easier to follow than a near-even split between a
  small product capture and a long text column.
- **Change:** Captured the current interface at a 1440 × 900 composition in an
  isolated replay runtime, including corrected evidence intake, session
  reconstruction, attributed human checkpoint, approval-gated memory,
  Brazilian-bird crews, athlete history, Competition Review, and evaluation.
  Rebuilt draft 13 with the product occupying 82% of each reframed product
  chapter and a short 18% title rail. Preserved the accepted narration, brand
  motion, bounded-agent interlude, learning sequence, and closing from draft
  12. Added a deterministic video builder and layout contracts.
- **Evaluation:** RED-first tests required a product share of at least 80%, a
  narrative rail no larger than 20%, a continuous 298.468875-second timeline,
  current capture filenames, and short rail copy. A render regression exposed
  that the installed FFmpeg lacks `drawtext`; a failing test now prohibits that
  dependency, and the rail is rendered from a local SVG instead. Four focused
  tests pass. The exported H.264/AAC draft is 1920 × 1080 at 30 fps,
  298.467 seconds, and 11.85 MB. Visual frame inspection confirms the corrected
  `01:16` intake state and the 82/18 composition across the main chapters.
- **Result:** Keep draft 13 as the recommended owner-review artifact. Preserve
  drafts 1–12 for editorial comparison; do not rename draft 13 to the final
  submission until owner video QA accepts it.
- **Cost/runtime:** Deterministic browser replay, local capture, and FFmpeg
  rendering only; no model, weather, or external API call and US$0.00.
- **Decision:** Product UI, rather than explanatory prose, must dominate each
  walkthrough frame. Use short chapter labels instead of transcript panels.
- **Learning:** A video can show a correct interface and still undersell it by
  shrinking the product to make room for explanation. Editorial hierarchy is
  part of product QA, and the media toolchain itself needs regression coverage.

### 84. Rebalanced product depth, narrative context, and runtime truthfulness

- **Hypothesis:** A 4:3 product capture with a modest explanatory rail will
  show more useful page depth than the 16:10 capture, while remaining easier to
  understand than draft 13's title-only rail.
- **Change:** Recaptured all product chapters at 1200 × 900 through an isolated
  live-enabled runtime. Used capture-only CSS to hide horizontal and vertical
  scrollbars without changing the product source. Rebalanced the frame from
  82/18 to 76/24 and added two-to-four concise contextual lines per product
  chapter. Kept the green runtime indicator only because the API and dashboard
  were actually live-enabled; no paid call was made to manufacture that state.
  Added the official experiment scale to the evaluation rail: ten controlled
  cases, 40 deterministic tool calls, ten verified trajectories, and about
  US$1.14 total comparison cost.
- **Evaluation:** RED-first contracts required a 74–78% product region, 22–26%
  contextual rail, exact 4:3 capture assumption, bounded description length,
  and an even 1920-pixel H.264 layout. The first render exposed a one-pixel
  mismatch between product and rail widths; the regression test failed before
  a shared width calculation restored the 1920 × 1080 output. Five focused
  tests pass. Every current capture is 1200 × 900, visual inspection finds no
  scrollbars, and the `01:16` frame shows the live-enabled status, aligned
  selected evidence, explicit US$0.20 start authorization, and the complete
  `Validate and investigate` action. Draft 14 is H.264/AAC, 30 fps,
  298.448 seconds, and 13.03 MB.
- **Result:** Keep draft 14 as the recommended owner-review artifact. It
  provides more product depth and enough explanation without reverting to the
  original text-heavy split.
- **Cost/runtime:** Live capability was enabled locally, but no model, weather,
  or external API execution was triggered for capture; US$0.00 incremental
  cost. Previously verified costs remain unchanged.
- **Decision:** Demonstrate runtime availability truthfully; never spend merely
  to color an icon or imply that a saved result is a new execution. Prove the
  agentic workflow through fixed evaluations, tool traces, and verified costs.
- **Learning:** Credibility comes from visible capability plus reproducible
  evidence, not from maximizing token spend. Capture aspect ratio and browser
  chrome can materially change how much product value fits in one frame.

### 85. Corrected mobile SPM positioning in the product story

- **Hypothesis:** Describing one rejected zero-only channel as a phone problem
  can make a case-specific data-quality decision sound like an inherent mobile
  limitation.
- **Change:** Rewrote the chapter-2 narration so WAKE compares stroke-rate
  signal coverage and consistency and selects a source per metric and session.
  The example still identifies SpeedCoach as the selected source, while making
  clear that another session may select mobile. Isolated the full replacement
  narration in `VOICEOVER_ELEVENLABS_V5_REGENERATE.md`.
- **Evaluation:** A RED-first documentation regression test failed against all
  three existing scripts containing the phone-rejection phrase. After the copy
  change, the new positioning test and five video-builder tests pass. Frozen
  evaluation inputs and the valid rejection of zero-only data remain unchanged.
- **Result:** Keep the source-neutral wording. Draft 14 remains a visual review
  artifact until its chapter-2 audio is regenerated and replaced.
- **Cost/runtime:** Documentation and deterministic tests only; no model,
  weather, audio-generation, or external API call and US$0.00.
- **Decision:** Present source trust as metric-specific and session-specific,
  never as a permanent ranking of device categories.
- **Learning:** A technically correct sentence can still teach the wrong
  product rule. The product story must distinguish an invalid observation from
  the capability of the device that produced it.

### 86. Replaced chapter-two narration without shifting the accepted edit

- **Hypothesis:** The corrected SPM wording can replace the old narration
  without recapturing screens or moving any later chapter.
- **Change:** Added a deterministic audio-replacement script that preserves the
  video stream, replaces only seconds 63–129, resamples the supplied mono audio
  to 48 kHz, and fits it to the existing chapter window. Generated draft 15
  from the owner-supplied 66.351-second ElevenLabs recording.
- **Evaluation:** RED-first tests fixed the chapter boundaries, constrained the
  permitted tempo adjustment to ±5%, and verified the audio graph. Nine focused
  tests pass. The applied factor is 1.005318, or 0.53%. Drafts 14 and 15 have
  the same encoded-video SHA-256, confirming no visual change. Draft 15 is
  H.264/AAC, 1920 × 1080, 30 fps, 48 kHz mono, 298.444 seconds, and 12.92 MB;
  chapter-2 peak audio is -1.7 dB.
- **Result:** Keep draft 15 as the recommended owner-review artifact. The
  source-neutral SPM narration is now present in the video.
- **Cost/runtime:** Local FFmpeg remux and deterministic tests only; no model,
  weather, or external API call by WAKE and US$0.00 incremental project cost.
  The supplied ElevenLabs recording was generated externally by the owner.
- **Decision:** Preserve accepted visuals when correcting isolated narration;
  keep the edit operation reproducible and boundary-limited.
- **Learning:** Chapter-level audio replacement avoids reintroducing visual QA
  defects and provides stronger evidence than an undocumented manual edit.

### 87. Re-audited the complete submission against the original brief

- **Hypothesis:** A final evidence and packaging audit will expose remaining
  delivery blockers more reliably than treating a successful product build as
  submission readiness.
- **Change:** Re-read the original 10-page organizer PDF, visually checked its
  final-deliverables page, ran the machine-readable readiness audit, executed
  the complete no-key reproduction, and built the source-only ZIP.
- **Evaluation:** Readiness reports 10 WAKE outputs, 10 baseline outputs, and 10
  trajectories with the accepted 83.76 versus 49.00 result. With Node.js
  24.19.0 and npm 10.8.2, 235 Python tests, nine public verifiers, 112 web
  tests, lint, and the production build pass. The first attempt on Node.js
  20.19.4 stopped at the declared version gate. The ZIP contains 686 files,
  is 7.24 MiB, and excludes MP4 drafts, private state, credentials, installed
  dependencies, and build output.
- **Result:** Repository evidence is ready, while final submission remains
  gated on owner video acceptance, the chapter-1 crew-name correction, the
  final video filename, final Git review/push, and confirmation of two PDF
  fields reported in the current portal. The supplied brief lists four
  deliverables but does not define two required PDFs.
- **Cost/runtime:** Local verification, PDF inspection, and ZIP construction
  only; no model, weather, or external API call and US$0.00.
- **Decision:** Do not invent the two PDF formats. Confirm their portal labels,
  page limits, and size limits before authoring, then rebuild the final ZIP.
- **Learning:** Delivery readiness is a separate engineering surface. Version
  gates, portal-only fields, filenames, and archive boundaries can block an
  otherwise working project.

### 88. Automated the remaining interface QA and created the PDF companion package

- **Hypothesis:** Browser-level closeout plus rendered PDF inspection can turn
  the remaining review checklist and portal PDF uncertainty into reproducible
  submission evidence without spending model budget.
- **Change:** Re-ran QA-07, QA-08, QA-12, and QA-17 through QA-20 at desktop
  and 390-pixel mobile widths. Verified saved-memory reopening, workflow-state
  persistence, fixed Evaluation values, hash history, responsive tabs,
  six-second disclosures, aligned workflow cards, and athlete-owned PM5
  boundaries. Added a TDD-covered ReportLab builder and generated a five-page
  environment/reproduction guide plus a seven-page detailed solution report.
- **Evaluation:** Three RED-first PDF content contracts pass. Both PDFs were
  rendered to PNG page by page and visually inspected; the first report render
  exposed joined bullets and an almost empty page, so list layout and manual
  page breaks were corrected before a second complete inspection. Extracted
  text, metadata, page counts, scores, replay cost, and live-key instructions
  were checked with `pypdf`. Browser QA found no horizontal overflow on tested
  primary routes and preserved the 83.76 versus 49.00 Evaluation evidence. The
  full no-key reproduction passed 238 Python tests, nine public verifiers, 112
  web tests, lint, and a production build. Rebuilding the ZIP exposed temporary
  PDF render images in the archive; a new failing package test reproduced the
  leak before `tmp/` was excluded.
- **Result:** Keep both PDFs under `output/pdf/`. Treat the remaining owner QA
  as visual/semantic confirmation rather than an untested functional blocker.
  The browser automation layer did not reliably synthesize Enter/Space for a
  native disclosure button, so keyboard feel remains explicitly human-reviewed.
  The cleaned source archive contains 667 files, is 4.17 MiB, includes both
  final PDFs, excludes temporary renders, and has SHA-256
  `84a83d40990bbbf0a578923ae3356a5f94b257b9d4956f0433fb56e92b4620e4`.
- **Cost/runtime:** Local browser automation, deterministic tests, ReportLab,
  Poppler rendering, and visual inspection only; no model, weather, or external
  API call and US$0.00.
- **Decision:** Include both owner-requested PDF companions while retaining the
  disclosure that the supplied brief does not define the portal's PDF fields.
- **Learning:** Artifact generation needs the same RED-GREEN-REFACTOR loop as
  application code. A valid PDF file can still fail visually, and automated QA
  should narrow rather than erase the boundary between functional evidence and
  human comprehension.

### 89. Rebuilt the solution PDF as a visual product and architecture dossier

- **Hypothesis:** A report that follows the video's human product story while
  adding architecture, tables, evidence boundaries, and measured results will
  communicate WAKE more effectively than a text-only technical companion.
- **Change:** Added six current interface captures as stable submission assets,
  declared their roles and captions in the tested PDF content model, and
  replaced the seven-page text report with an eleven-page visual dossier. The
  new sequence covers the club problem, coach/athlete authority, layered
  architecture, metric-level source trust, club and athlete memory, session
  investigation, competition context, controlled evaluation, TDD failures,
  costs, reproduction, privacy, and honest product limits.
- **Evaluation:** RED first failed because the visual-asset contract and the
  `System architecture` and `Product walkthrough` sections did not exist.
  GREEN passes five focused PDF tests. The generated A4 report is 11 pages,
  approximately 623 KiB, and contains about 2,003 extracted words. Every page
  was rendered at 120 DPI and visually inspected for clipping, overlap,
  alignment, screenshot legibility, table wrapping, headers, footers, and page
  numbering; one narrow table heading was shortened after the first render.
- **Result:** Keep the visual report as the judge-facing solution PDF and keep
  the separate setup/reproduction PDF as the exact clean-environment guide.
- **Cost/runtime:** Local ReportLab generation, Poppler rendering, and focused
  deterministic tests only; no model, weather, audio, or external API call and
  US$0.00.
- **Decision:** Use the video for paced narrative and the PDF for deeper,
  self-contained inspection of the same value story and its architecture.
- **Learning:** A solution report should not repeat a README in paginated form.
  Screens establish product reality; tables establish comparability; and a
  layered diagram makes the agentic control boundaries auditable at a glance.

### 90. Reframed repeated session screens and rebuilt fragile video transitions

- **Hypothesis:** Subject-focused crops and fully completed transition actions
  will communicate evidence authority, uncertainty, and human provenance more
  clearly than near-duplicate page captures with small scroll differences.
- **Change:** Replaced three full-page session frames with distinct close-ups
  of source selection, the environmental boundary, and the athlete answer with
  provenance. Rebuilt the current Overview → Team → Tucano sequence with eased
  cursor travel and visible click holds. Re-rendered the agentic interlude from
  staged SVG states so every connector precedes its destination block.
- **Evaluation:** Three RED-first video-builder regressions fixed the cursor
  timing, prohibited the old source-video interlude at seconds 81–97, required
  complete connector IDs, and fixed the three unique crop names. Twelve focused
  video and narration tests pass. The complete H.264/AAC file decodes without
  error; contact sheets were inspected across seconds 47–54, 81–97, and
  109–135.
- **Result:** Keep draft 16 as the recommended owner-review artifact. It removes
  the residual frame around 01:21, prevents clipped arrows around 01:22, and
  gives the three session principles visibly different subjects.
- **Cost/runtime:** Local browser capture, SVG rendering, FFmpeg assembly, and
  deterministic tests only; no model, weather, audio-generation, or external
  API call and US$0.00 incremental project cost.
- **Decision:** Use whole-page captures for orientation and focused crops for
  a specific claim. A simulated interaction must finish its travel and click
  before the destination view appears.
- **Learning:** Editorial continuity is part of product credibility. Reusing a
  nearly identical page can hide the very evidence the narration is explaining,
  while a connector that materializes under a card reads as a rendering defect.

### 91. Made the removed behavior and negative experiment explicit with accessible captions

- **Hypothesis:** Naming the negative evidence in narration is insufficient if
  the screen remains a generic evaluation page; dedicated learning cards and
  open captions will make the hackathon requirement unmistakable and improve
  accessibility without turning the video into a technical presentation.
- **Change:** Added two original vector cards: `PRODUCT LESSON · REMOVED
  BEHAVIOR` explains the reconstructed-distance overclaim and TDD correction;
  `NEGATIVE EXPERIMENT · KEPT` names the longitudinal `NO DEMONSTRATED QUALITY
  GAIN` result and preserves its honest cost boundary. Added 54 sentence-level
  English cues, a reusable SRT, and a deterministic open-caption compositor.
- **Evaluation:** RED-first tests required both learning segments and exact
  labels, at least 40 ordered caption cues covering the spoken story, no more
  than two 48-character lines, and legible lower-safe-area typography. The
  first burn attempt exposed that the installed FFmpeg lacked the libass
  `subtitles` filter. A second RED reproduced that portability failure before
  the implementation moved to locally rendered SVG alpha overlays. Sixteen
  focused video, caption, audio, and positioning tests pass. The complete
  captioned H.264/AAC file decodes without error and was visually inspected at
  the opening, investigation, removed behavior, negative experiment, and close.
- **Result:** Keep the captioned draft 17 as the recommended owner-review cut
  and retain both the uncaptioned equivalent and SRT sidecar. The requirement
  is now visible, not inferred from a sentence over an unrelated screen.
- **Cost/runtime:** Local SVG rendering, FFmpeg composition, and deterministic
  tests only; no model, weather, audio-generation, or external API call and
  US$0.00 incremental project cost.
- **Decision:** Use open captions for the submitted video unless owner QA finds
  a product interaction they materially obscure. Preserve negative experiments
  with direct labels and conclusions, not marketing euphemisms such as a win or
  unexplained hot take.
- **Learning:** Accessibility and evidence clarity reinforce each other. A
  negative result becomes credible when the audience can hear it, read it, and
  see the exact product decision it changed.

### 92. Isolated source trust and restored the complete human confirmation action

- **Hypothesis:** The source-trust concept will read faster without chart
  fragments above it, while the human checkpoint requires its complete action
  and provenance choices to explain how confirmation enters the workflow.
- **Change:** Re-cropped `Evidence selection` to the four metric-authority rows
  only. Reconstructed one complete current-interface human form from adjacent
  scroll states, preserving the question, Yes/No choice, three provenance
  routes, save action, unknown action, telemetry boundary, and coach-approval
  boundary. Rebuilt captioned and uncaptioned draft 18.
- **Evaluation:** A RED-first timeline regression rejected both former crop
  filenames. GREEN passes nine focused video-builder tests and 16 complete
  video/caption/audio positioning tests. The two framed scenes were inspected
  before assembly and again with open captions in the complete cut. The final
  H.264/AAC file decodes without error and remains below five minutes and 50 MB.
- **Result:** Keep the evidence-only matrix and complete human form. The source-
  trust scene no longer competes with preceding chart labels, and the human
  checkpoint visibly explains what is saved and what may remain unknown.
- **Cost/runtime:** Local cropping, FFmpeg composition, and deterministic tests
  only; no model, weather, audio-generation, or external API call and US$0.00.
- **Decision:** Crop tightly when one visual concept is being explained, but
  preserve the complete decision surface when an action and its consequences
  define the workflow.
- **Learning:** A close-up can remove too much as easily as it can reveal too
  little. Evidence matrices benefit from isolation; human decisions need their
  choices, action, and boundary together.

### 93. Made product-path changes visible with restrained cursor actions

- **Hypothesis:** A static cut between valid pages can still make the product
  feel like disconnected screenshots. Short cursor actions at route changes
  should explain how the coach reached the next view without distracting from
  the evidence being read.
- **Change:** Rebuilt the 02:34–03:51 product sequence around the real route:
  Overview → Team → Crew: Tucano → Lucas → Goal memory → Competition → Tucano
  boat report → Evaluation. Added eased cursor travel, visible click pulses,
  and post-click holds only before those route changes. Kept result-reading
  intervals cursor-free and rebuilt captioned and uncaptioned draft 19.
- **Evaluation:** A RED-first regression required all nine cursor segments,
  their exact source views, minimum eased travel, click-after-travel ordering,
  a post-click hold, and the correct destination at every segment boundary.
  GREEN passes nine video-builder tests and 16 complete video/caption/audio
  positioning tests. A 14-frame contact sheet across 02:34–03:51 confirmed the
  Overview, Team, crew, athlete, memory, competition, boat-report, and
  evaluation targets. The captioned H.264/AAC file is 298.256 seconds, 1920 ×
  1080 at 30 fps, and approximately 15.9 MiB.
- **Result:** Keep draft 19 as the recommended owner-review cut. Navigation is
  now demonstrated as a coherent coach journey rather than implied by edits.
- **Cost/runtime:** Local FFmpeg assembly and deterministic tests only; no
  model, weather, audio-generation, or external API call and US$0.00.
- **Decision:** Show the cursor only when it explains a product path. Do not
  simulate continuous mouse movement while the audience is reading evidence.
- **Learning:** Motion earns its place when it explains causality in the UI:
  this click produced that view. Decorative cursor motion adds noise; bounded
  navigation motion adds orientation.

### 94. Replaced captured focus artifacts with an explicit current-location state

- **Hypothesis:** Browser-blue focus outlines and an accidental hovered card
  make otherwise valid screens look unfinished. A product-owned active state
  should improve orientation while keyboard focus remains independently
  accessible.
- **Change:** Added `aria-current="page"` to all four global destinations and
  styled the active destination with green text, a soft green surface, and a
  green underline. Kept a separate green `:focus-visible` outline. Neutralized
  the hovered Competition-review card in the Overview capture and replaced the
  captured blue Competition and Evaluation outlines with the active treatment.
  Rebuilt captioned and uncaptioned draft 20.
- **Evaluation:** RED-first design-system tests required all four current-page
  attributes, active-state tokens, and the accessible focus rule. A second RED
  required focus-clean Overview, Competition, and Evaluation captures in the
  video timeline. GREEN passes ten video-builder tests and 24 focused design-
  system/interface tests. Frames at 02:36, 03:26, and 03:56 were visually
  inspected in the captioned render; no blue outline or accidental card hover
  remains.
- **Result:** Keep draft 20 as the recommended owner-review cut. The current
  product location is more visible and the two capture artifacts are removed.
- **Cost/runtime:** Deterministic CSS, local vector overlays, FFmpeg assembly,
  and tests only; no model, weather, audio-generation, or external API call and
  US$0.00.
- **Decision:** Use persistent product styling to explain location and reserve
  focus outlines for keyboard interaction. Never encode a transient hover or
  browser-default focus artifact into a submission screenshot.
- **Learning:** A visible state needs a name and a purpose. Current location is
  durable; hover and focus are transient. Mixing them makes navigation look
  accidental.

### 95. Realigned open captions to the final assembled narration

- **Hypothesis:** Caption timings copied from raw chapter audio will lead the
  spoken narration after editorial intro or chapter placement changes. Aligning
  them to the final audio track should restore accessibility without shifting
  cues that already match.
- **Change:** Measured the final chapter-one placement against its supplied
  ElevenLabs recording at 3.85 seconds. Applied that offset to its twelve cues,
  prohibited captions during the 3.8-second brand-only signature, and bounded
  the first chapter-two cue to the 01:03 cut. Preserved the other 41 cues because
  their starts and ends already coincide with final-audio pauses. Rebuilt the
  SRT and open-captioned draft 21.
- **Evaluation:** RED-first tests failed while the first cue still began at
  00:00.640. GREEN requires the first cue at 00:04.490, no caption during the
  brand-only hold, chapter one ending before 01:02.5, and chapter two beginning
  no earlier than 01:03. Seventeen focused caption/video/audio tests pass. Frame
  checks at 00:03.7, 00:04.3, 00:04.6, 01:02.8, and 01:03.1 verify the expected
  visual states, and the complete H.264/AAC file decodes without error.
- **Result:** Keep draft 21 as the recommended owner-review cut. The opening
  captions no longer precede the narration.
- **Cost/runtime:** Local audio correlation, silence analysis, SVG caption
  composition, FFmpeg rendering, and deterministic tests only; no model,
  transcription service, or external API call and US$0.00.
- **Decision:** Version caption timing against the final assembled audio, not
  only the raw narration files. Recheck chapter boundaries whenever an intro,
  replacement clip, tempo fit, or edit changes placement.
- **Learning:** Correct text is not accessible when its timing describes an
  earlier edit. Caption QA must test silence, onset, chapter cuts, and the close
  in the actual delivery file.

### 96. Removed subtitles and aligned every subject change to the final narration

- **Hypothesis:** A caption can be textually correct and still weaken the edit
  when its timing or visual weight competes with the interface. The remaining
  perception of mismatch came from product screens changing before the audio
  finished the preceding idea, not only from subtitle timing.
- **Change:** Removed open subtitles from the recommended cut. Rebuilt the
  product timeline against the final narration cues so optional evidence, the
  bounded agent, reconstruction, source trust, environment, human checkpoint,
  briefing, approval, club scale, athlete history, Competition, boat report,
  Evaluation, removed behavior, and negative experiment each begin with their
  corresponding spoken idea. Cursor movement may bridge two ideas, but the
  destination cannot replace the source before the next idea begins.
- **Evaluation:** Added a RED-first semantic-timeline regression covering 16
  subject boundaries and updated all nine route-destination assertions. Eighteen
  focused video, caption-history, audio, and positioning tests pass. The final
  H.264/AAC file decodes without error, is 298.128 seconds at 1920 x 1080 and
  30 fps, and is 13,150,782 bytes. Boundary frames were inspected at optional
  evidence, agentic workflow, approval, Competition, Evaluation, removed
  behavior, and negative-experiment transitions.
- **Result:** Keep uncaptioned draft 22 as the recommended owner-review cut.
  Preserve draft 21 and its SRT as an experiment, not as the delivery master.
- **Cost/runtime:** Local deterministic timeline editing, FFmpeg rendering, and
  tests only; no model, transcription, weather, or external API call and
  US$0.00 incremental project cost.
- **Decision:** Remove open subtitles from this submission cut. Treat the final
  assembled narration as the timing authority and bind subject changes to
  complete spoken ideas.
- **Learning:** A subtitle problem can expose a deeper edit problem. Correcting
  only the words leaves the audience disoriented when the picture has already
  moved to the next claim.

### 97. Rebuilt the chapter audio, removed click pulses, and aligned visuals to the real recording

- **Hypothesis:** The remaining drift was not a small caption offset. A later
  chapter-two replacement had overwritten the beginning of chapter three, so
  any timeline based on the earlier cue sheet would advance before the final
  recording finished its idea.
- **Change:** Reassembled the narration from the seven original owner-supplied
  chapter files. Shortened only chapter-two pauses longer than 250 ms, applied
  a bounded 1.98% tempo adjustment, ended it at 122.817 seconds, preserved a
  150 ms transition, and restored the complete human-checkpoint recording at
  122.967. Retimed the agentic workflow, reconstruction, source trust,
  environment, human checkpoint, later chapters, removed behavior, negative
  experiment, and close from the actual recordings. Removed every click pulse
  while preserving cursor movement. Extended the last visual beyond the audio.
- **Evaluation:** RED-first tests cover the chapter boundary, pause-only cleanup,
  bounded tempo, full seven-chapter concat, quiet ending tail, absent click
  pulse, non-trimming mux, and revised visual subjects. Twenty-one focused
  video, audio, caption-history, and positioning tests pass. The H.264/AAC file
  decodes without error; frames at 01:36, 01:46, 01:47, 01:59, 02:00, 02:02,
  02:03, 04:40, 04:51, and 04:58 were inspected. Video duration is 299.232
  seconds versus 299.032 seconds of audio, so the final image remains after the
  last word. Size is 13,535,323 bytes.
- **Result:** Keep uncaptioned draft 23 as the recommended owner-review cut.
- **Cost/runtime:** Local silence analysis, deterministic audio composition,
  FFmpeg rendering, and tests only; no model, transcription, weather, or
  external API call and US$0.00 incremental project cost.
- **Decision:** Never replace a narration window without first checking where
  the next chapter actually begins. Cursor travel may explain navigation, but
  the submission uses no simulated click pulse.
- **Learning:** A plausible-looking timeline can conceal destructive audio
  overlap. The assembled recordings, not the script or obsolete captions, are
  the timing authority.

### 98. Promoted the accepted video and hardened the source-only delivery boundary

- **Hypothesis:** Treating the final video, public PDFs, and executable source
  as explicit deliverables will make the judge package smaller, safer, and
  easier to reproduce than archiving the development workspace as-is.
- **Change:** Promoted owner-approved draft 23 byte-for-byte to the final video
  filename, recorded its media profile and SHA-256, excluded all draft media
  and captions from the deterministic source ZIP, retained the final video as
  a separate deliverable, and changed the PDF/reproduction language from
  pending media QA to final readiness. The first extracted-package check also
  removed the hidden `.git` dependency from the privacy audit and preserved
  executable script permissions through ZIP extraction.
- **Evaluation:** RED-first package tests rejected a draft SRT that previously
  entered the source archive, and PDF tests rejected the obsolete
  `PENDING_FINAL_VIDEO` instruction. The first clean extraction then exposed a
  `NOT_READY` result without `.git` and a `0644` launcher. Two additional RED
  regressions now require archive-safe privacy scanning and `0755` executable
  scripts. GREEN excludes every named draft artifact, includes public PDFs,
  and expects `READY`. The final MP4 is 299.232 seconds, 1920 x 1080 at 30 fps,
  13,535,323 bytes, and decodes as H.264/AAC.
- **Result:** Keep the accepted MP4, source ZIP, two public PDFs, and Git
  snapshot as separate but cross-referenced submission artifacts. A fresh ZIP
  extraction installed both locked dependency sets and passed 253 Python tests,
  nine public verifiers, 113 web tests, lint, and the production build without
  an API key or model call.
- **Cost/runtime:** Local file promotion, deterministic packaging, media
  probing, tests, and documentation only; no model or external API call and
  US$0.00 incremental project cost.
- **Decision:** Never submit the complete working directory. Build from an
  allowlisted/excluded package contract, test it in a new directory, and retain
  exact hashes for the uploaded files.
- **Learning:** Reproducibility includes what is deliberately absent. A small
  source package with no key, private state, dependencies, or editing drafts is
  stronger evidence than a large archive that happens to contain the code.

### YYYY-MM-DD - Experiment name

- **Hypothesis:** What should improve and why?
- **Change:** What was added, removed, or revised?
- **Evaluation:** Which fixed cases, commands, and metric were used?
- **Result:** Include the complete result and a link to committed evidence.
- **Cost/runtime:** Record relevant model, tool, token, time, and cost information.
- **Decision:** Keep, revise, or remove.
- **Learning:** What failure mode or insight changes the next step?

The final version must include the simple baseline, every important iteration, the combined final workflow, the most impactful change, and at least one removed experiment.
