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
