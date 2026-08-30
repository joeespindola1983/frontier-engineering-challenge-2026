# WAKE Product Interface Contract

**Status:** accepted replay with a tested end-to-end local live workflow

## Purpose

The product interface helps a rowing coach understand one session without manually reconciling a plan, device exports, conditions, and verbal context. It remains a calm review instrument rather than an analytics command center. The hackathon build also contains a clearly separated, read-only Evaluation view for judges; that view is submission evidence, not part of the coaching workflow.

```text
Receive fragmented evidence
        -> reconstruct the session
        -> surface material findings and limitations
        -> ask one focused human question when needed
        -> produce a verified briefing
        -> add approved context to goal memory
```

## Implemented path

The `web/` application currently implements:

1. a persistent local session inbox that separates analysis, coach-view, human-answer, and approved-memory milestones;
2. role-aware evidence intake showing independent plan, SpeedCoach, mobile, environment, and session-context sources;
3. a session review with work intervals derived from the selected plan and analysis;
4. metric-level source selection through progressive disclosure;
5. one analysis-requested human checkpoint routed to its expected respondent, with explicit answer provenance or an unknown state;
6. a coach-facing briefing with findings and evidence references;
7. an explicit approval action before an in-memory goal update.
8. an optional historical-weather intake with explicit approximate-location consent, session-timezone confirmation, coordinate-free condition preview, and a no-model preparation path in replay mode.
9. a read-only Evaluation view generated from the committed official comparison, with one consolidated result, ten expandable individual case reports, case and dimension diagnostics, cost and trajectory observability, preserved limitations, and no agent invocation path. A visible Sessions-page action keeps this evidence reachable when the compact header navigation is hidden.
10. a separate two-week real-informed synthetic club pulse connecting 16 named fictional athletes, 10 recurring lineups, 11 physical boats, 38 planned crew outings, recorded alternatives, explicit participation gaps, and a source-derived validation funnel over 40 independent activity records; plus read-only crew and athlete drill-downs.

The hosted UI replays committed public case 002 and never accesses evaluator ground truth. During local development it can connect to the task-level product service, upload the core plan and SpeedCoach sources plus any optional mobile, environment, or context evidence, receive validation/normalization metadata, and prepare a compact agent input. When live mode is explicitly enabled, the page executes the prepared bundle, adapts the verified result, completes its server-owned human checkpoint, produces a bundle-specific briefing, and proposes an approval-gated memory update. Uploaded files with different bytes are never allowed to inherit the committed answer. Titles, intervals, targets, deviations, source labels, clocks, environmental absence, checkpoint copy, and memory copy come from the selected bundle rather than case-002 constants.

The club pulse is a committed deterministic frontend dataset, not a second persistence system and not an agent-generated multi-session conclusion. It is labelled **real-informed synthetic** because its workout patterns, source formats, plausible value ranges, and operational failure modes were modeled from real coach prescriptions, WhatsApp/PDF/spreadsheet-style material, SpeedCoach CSVs, pre-existing WAKE mobile export structures, and first-hand rowing-club context. Identities, the displayed club history, lineups, exact sessions, outcomes, aggregates, and physical-boat names are fictional. This provenance does not make the dataset statistically representative or evidence of real athletic performance.

The dataset models four 2x crews, four 4x crews, and two 8x crews across ten weekdays. Crew identity is a named lineup snapshot linked to athlete identities, ordered seats, category, and a physical boat; boat class and physical shell identity remain separate. Three full lineups do not launch. Alternative 1x and ergometer records remain attached to the participating athletes, while an expected day without any recorded activity becomes a context request rather than a performance, injury, or commitment verdict. The drill-downs count supported relationships only: crew outings, activity days, modalities, distance, physical boats, and explicit gaps.

`buildClubPeriodAnalysis` screens all 40 recorded activities and all 38 planned outings without a model call. It derives SPM, recovery, plan-link, and athlete-context findings from compact observations with evidence references; combines them with crew-unavailable and participation-gap signals; and routes each item to agent investigation, an athlete question, human context, or a source request. The current result contains ten attention signals, but only two were model candidates. Both complete bundles passed deterministic preflight, received explicit authorization, and produced verified v2 outputs. The UI now exposes `2/2`, US$0.194118 observed cost, and 60,094 tokens from preserved artifacts. The other eight dependencies remain outside paid triage; longitudinal synthesis remains `NOT_EXECUTED`, and clean records are never labelled executed according to plan.

The separate public batch gives every displayed activity an isolated source directory and hash manifest. Its verifier reports 40 data-validated records, 38 reconstructed water sessions, 37 plan comparisons, two agent-verified sessions, and zero human approvals. Thirty-one sessions have no material signal in available evidence, three are reconstructed alternatives, one needs a plan, one needs athlete context, and two indoor records remain outside the current Concept2 adapter. The interface exposes these levels as a funnel rather than collapsing them into one “homologated” state.

## Evidence boundaries

The frontend must not:

- choose trusted metrics from raw sensors;
- calculate final plan compliance;
- turn temporal environment association into causal attribution;
- treat any athlete or coach confirmation as telemetry;
- infer evidence authority from the person who uploaded a file;
- infer technique, synchronization, physiology, improvement, or regression from unsupported data;
- approve memory automatically;
- show private routes, identities, devices, or health data.
- present fictional club names or deterministic aggregates as real club history or agent-generated findings.

The current implementation therefore keeps work interval five as the material SPM deviation, rejects mobile SPM, uses SpeedCoach for distance and SPM, allows mobile route corroboration, and describes the wind shift only as time-aligned context.

## Product and evaluation separation

Sessions and Goal memory remain the operational coach workflow. The hackathon build exposes one additional Evaluation destination, explicitly labelled `Saved result · No model call`. It renders a consolidated public summary and expandable per-case score reports generated from committed manifests and grade reports; it cannot execute an investigation, access evaluator ground truth, expose raw evidence, or change saved workflow state. Evaluation fixtures do not appear in the coach inbox because they are benchmark scenarios, not club sessions. Full fixtures, structured outputs, grader controls, and trajectories remain repository artifacts rather than browser controls. A production club build may omit this submission-only destination.

## Task-level API

The local application service exposes:

```text
POST /api/sources
GET  /api/sources/:id
GET  /api/sessions
GET  /api/sessions/:id
POST /api/sessions/:id/view
POST /api/environment-enrichments
POST /api/source-bundles/prepare
POST /api/source-bundles/:id/execute
POST /api/source-batches/prepare
GET  /api/source-batches/:id
POST /api/source-batches/:id/execute
GET  /api/runtime/costs
POST /api/investigations
GET  /api/investigations/:id
POST /api/checkpoints/:id/answers
POST /api/briefings/:id/approve
GET  /api/goals/:id
```

`POST /api/sources` accepts one Base64-encoded typed file plus `uploaded_by_role` and `origin_role`. It returns metadata only: source id, kind, original name, detected format, SHA-256 hash, byte size, source provenance, and a versioned telemetry-normalization report when applicable. Either an athlete or coach may upload any source. Upload identity is kept separate from source authority: a plan defaults to coach origin, SpeedCoach and mobile telemetry remain device-origin evidence, environment defaults to service origin, and session context defaults to the contributor. Source-kind rules prevent device telemetry from being relabelled as human-origin evidence. The endpoint accepts at most 10 MiB per source, rejects path-bearing names, validates plan and environment schemas, validates minimum context fields, and normalizes canonical telemetry, SpeedCoach vendor, and WAKE mobile sensor CSV formats. `GET /api/sources/:id` returns the same safe metadata without raw or normalized rows.

`POST /api/environment-enrichments` is available only when the local service starts with `--allow-weather`. It requires an athlete or coach requester role and literal authorization for an approximate-location lookup. Telemetry timestamps must include an offset; a raw SpeedCoach vendor clock instead requires an explicit IANA `session_timezone`, which is preserved as a user-supplied time assumption. The service derives a two-decimal median coordinate and bounded UTC query window, calls the configured historical-weather provider, normalizes the result as a service-origin environment source, and caches the result for the process lifetime. It sends no route rows, identity, plan, or device metadata. Its safe response adds a coordinate-free preview containing wind, gust, temperature, humidity, sample count, and temporal resolution. Provider failure does not alter the uploaded SpeedCoach evidence or prevent core bundle preparation. The page exposes the consent and timezone controls, shows the preview and noncausal boundary, and lets replay-mode users prepare the enriched bundle without invoking the agent. See [Historical weather enrichment](WEATHER_ENRICHMENT.md).

`POST /api/source-bundles/prepare` requires exactly one plan and one SpeedCoach source and accepts at most one mobile, environment, and context source. It builds a deterministic, schema-validated compact summary; records source hashes, quality, and contribution provenance; computes cross-source findings only when the necessary optional evidence exists; preserves every unavailable capability as an evidence gap; retains the full summary in process memory; and returns safe preparation metadata including source coverage. Bundle identity includes the contribution identities, so byte-identical evidence submitted through different provenance paths does not overwrite the earlier contribution. It never calls the agent and explicitly returns `agent_called: false`.

`POST /api/source-bundles/:id/execute` accepts only `mode: live`, exists only when the local service starts with `--allow-live`, requires `OPENAI_API_KEY`, and requires `authorized_cost_usd` at or above the configured operational threshold. That value permits the run to start; it is not a provider billing cap. The endpoint explicitly loads the accepted v2 agent config and prompt, supplies the bounded runner with the prepared summary and normalized files in an isolated temporary directory, validates the returned analysis schema and case identity, and records the result in process memory. Repeating the same execution in that process returns the recorded result rather than issuing another paid call or duplicating the cost ledger. Its response includes a compact review bundle; process-local investigation, checkpoint, and goal identifiers; and observed token usage, runtime, approximate cost, authorization, and overrun status. It excludes input hashes and time-series windows. `GET /api/runtime/costs` aggregates each new execution once for the lifetime of the process. `HttpWakeClient.analyzeSourceBundle` implements the two-step prepare/execute call, refuses non-live mode or missing cost authorization before making a request, and carries those identifiers and observed cost into the page's review transition.

The source-batch endpoints wrap this per-session contract without creating a multi-session prompt. Preparation accepts up to 100 independently identified source groups, isolates invalid items, and is content-addressed and idempotent. Execution is sequential, converts explicit batch authorization into whole per-execution start gates, preserves item-level failures, resumes pending items after restart, and reuses existing bundle results. Responses contain compact status, coverage, gaps, and cost metadata only. See [Session batch processing](BATCH_PROCESSING.md).

`GET /api/sessions` returns safe session summaries and operational counts. It keeps analysis, coach view, human response, and club-memory approval as independent milestones rather than collapsing them into one ambiguous status. `GET /api/sessions/:id` restores the safe review, briefing, goal, or prepared-bundle metadata needed to continue that workflow; it never returns raw or normalized sensor rows. `POST /api/sessions/:id/view` records that a coach opened the session without implying that the human question was answered or that memory was approved.

`POST /api/investigations` accepts either the fixed public case id or the exact five-source public replay bundle. Source-based replay succeeds only when those five uploaded byte sequences exactly match public case 002. Progressive two-to-five-source bundles use the separate prepare/execute path and cannot inherit replay output. Preparation of a changed bundle does not authorize it to spend API budget. The service—not the browser—owns replay/live selection, checkpoints, and approval. Reopening the same investigation is idempotent and cannot reset an existing answer. The local service writes source bytes, normalized rows, prepared summaries, workflow state, and cost aggregates to `private-data/wake-product/product-state.json`, an ignored user-restricted prototype file. It survives refreshes and service restarts but is not encrypted, authenticated, multi-tenant, remotely backed up, or suitable for hosted private club data.

`POST /api/checkpoints/:id/answers` accepts `YES`, `NO`, or `UNKNOWN`. A confirmed answer must also identify `answered_by_role`, `recorded_by_role`, and `authority_basis`. The current authority router sends actual equipment-use, perceived-effort, and session-execution questions to the athlete; training-intent and prescription questions go to the coach; unclassified questions remain athlete-or-coach. The interface offers three explicit paths for a confirmed answer: athlete direct confirmation, athlete report recorded by a coach, or coach direct observation. This is product-level routing v1 over the existing string question contract, not authentication and not proof that a user holds the declared role.

## Acceptance boundary

The current slice is accepted when its Python and JavaScript behavioral tests, lint, production build, and dependency audit pass; all displayed replay data is synthetic; uncertainty is visible; contributor and answer provenance remain distinct from evidence authority; and a memory session appears only after coach approval. The Evaluation summary must be byte-reproducible from the official artifacts, contain no ground truth or evidence references, and remain incapable of paid execution. Generic new-bundle checkpoint/briefing transitions, local restart-safe state, and page invocation are implemented and tested. Encryption, authentication, verified role identity, club tenancy, hosted private uploads, backups, and distributed exactly-once execution remain separate work.
