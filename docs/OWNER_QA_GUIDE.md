# WAKE owner interface QA guide

**Purpose:** validate WAKE as a rowing coach or athlete would experience it,
first through zero-cost replay and then through explicitly authorized live
investigation paths.

**QA URL:** [http://localhost:3000/](http://localhost:3000/)

**Upload data:** `data/qa-interface/full-replay-bundle/`

Record each step as `PASS`, `FAIL`, or `QUESTION`, with one screenshot and a
short note for every failure. Complete a test block before changing code so
related defects can be evaluated together.

## Before QA

1. Stop any existing WAKE dashboard with `Ctrl+C`.
2. From the repository root, start an isolated replay state:

   ```bash
   ./scripts/start_dashboard.sh \
     --state-store /private/tmp/wake-owner-qa-replay-state.json
   ```

3. Confirm the terminal prints `Mode: replay (no model call)` and the dashboard
   link `http://localhost:3000/`.
4. Confirm the runtime indicator describes a real-informed synthetic replay,
   not a live model runtime.
5. Keep `data/qa-interface/full-replay-bundle/` open for upload tests. Every
   file in this directory is public and synthetic.

If the interface shows live mode, stop and restart in replay mode. QA-01 through
QA-12 and QA-17 through QA-20 cost **US$0.00**. The isolated state path avoids
inheriting an earlier answer while preserving state throughout this run.

## Sequential replay checklist

### QA-01 — Product entry and plain-language value

**Action:** Open Sessions and read only the first viewport.

**Expected:** Within 15 seconds, a coach understands that WAKE connects club
activity, athletes, recurring crews, boats, and evidence so attention can be
directed without opening every chart. Evaluation, Competition Review, and
Review a session are reachable.

**Fail if:** the page looks like a single-session telemetry dashboard or the
real-informed synthetic boundary is unavailable.

### QA-02 — Club-scale workload

**Action:** Inspect Club training pulse and its validation funnel.

**Expected:** The page shows 52/52 records screened and reconstructed, 51
plan-compared, two agent-verified, zero human-approved, 16 athletes, 10 crews,
and separate water/indoor volume. Duration and date range come from the active
period rather than a fixed “two-week” title.

**Fail if:** reconstruction is presented as coach approval, all 52 sessions are
presented as GPT calls, or missing records become athlete judgments.

### QA-03 — Crew, lineup, and physical boat memory

**Action:** Under Team and crew memory, open **Crew: Tucano - 2x - Men**.

**Expected:** The detail identifies the 2x, named physical shell, recurring
lineup, planned versus launched outings, and unavailable-crew day. Athlete
links are actionable.

**Fail if:** crew, boat, and athletes are collapsed into one label or an
unavailable outing is described as athlete failure.

### QA-04 — Athlete Training Days

**Action:** Open **Lucas** and inspect Training Days.

**Expected:** Water, solo, and Concept2 records are connected chronologically.
Combined, water-only, and indoor-only days are distinguishable. Water and
indoor distance remain separate, and physical boats and crews are visible.

**Fail if:** ergometer distance is added to water distance as one performance
total or a PM5 result is treated as a crew result.

### QA-05 — Coach attention versus missing context

**Action:** Return to Sessions and open one crew-unavailable item and one
athlete-context item from the prioritized review list.

**Expected:** Numeric deviations, missing plans, crew availability, and athlete
context follow distinct routes and confidence levels.

**Fail if:** a missing activity becomes a medical, fitness, or commitment
conclusion or all alerts are presented with the same certainty.

### QA-06 — Add the second training period

**Action:** Select **Load 2-week package**.

**Expected:** WAKE adds 50 post-regatta activities for the same 16 athletes and
10 crews, reaches 102 activities, and shows six comparison routes: faster
comparable, slower comparable, stable, wind confounded, participation review,
and insufficient equivalent evidence. `No model call`, `US$0.00`, and
`NOT_ESTABLISHED` remain visible.

**Fail if:** faster automatically means improved fitness, wind is stated as a
cause, or loading the package silently triggers GPT.

### QA-07 — Saved club intelligence

**Action:** Open **Saved WAKE club memory**, leave it, and reopen it through
Goal memory.

**Expected:** The saved briefing remains reachable, covers 102 activities,
presents supported observations, three coach priorities, four human/source
questions, explicit limits, and costs US$0.00 to reopen.

**Fail if:** the loaded report disappears after navigation, unsupported context
becomes fact, or reopening starts a new analysis.

### QA-08 — Session inbox and workflow milestones

**Action:** Inspect Saved session reviews before and after QA-10. Reopen the
prepared, reviewed, answered, and approved session.

**Expected:** Needs action, awaiting analysis, viewed by coach, and in club
memory are separate, aligned states. Saved milestones survive navigation,
refresh, and service restart.

**Fail if:** opening resets a session or analysis, view, answer, and approval
are represented as one status.

### QA-09 — Minimum upload without optional evidence

**Action:** Open **Review a session**, keep Athlete as contributor, and choose
only `plan.json` and `speedcoach.csv`. Select **Validate and prepare · No agent call**.

**Expected:** WAKE saves a prepared local session, shows Plan + SpeedCoach
coverage, keeps mobile/environment/context missing, states that no agent call
occurred, confirms success clearly, and prevents duplicate preparation.

**Fail if:** optional evidence blocks preparation, a committed answer is
silently reused, or the action incurs cost.

### QA-10 — Complete five-source replay and human checkpoint

**Action:** Open a fresh Review a session form, select all five files, keep
historical weather disabled, and select **Validate and open replay**. Complete
the resistance-band checkpoint and approve the briefing for club memory.

**Expected:** The page reconstructs six 1 km work intervals, keeps SpeedCoach as
the usable SPM source, rejects zero-only mobile SPM, treats the wind change as
associated rather than causal, records answer provenance, and requires explicit
coach approval before memory changes. The global Review a session action always
opens a fresh intake.

**Fail if:** mobile zero becomes selected SPM, wind becomes proven cause, a
human answer is relabelled as device evidence, or approval is skipped.

### QA-11 — Competition Review

**Action:** Open Competition Review, one boat report, and the non-classified
entry.

**Expected:** Ten club entries connect lineup snapshots, athletes, physical
boats, shared pre-race outings, full fictional fields, official order, and one
missing-context result. Stable synthetic provenance is available through the
information control rather than a large permanent banner.

**Fail if:** WAKE selects crews, invents a result, or presents fictional
identities as real competitors.

### QA-12 — Evaluation, credibility, and responsive check

**Action:** Open Evaluation at desktop and mobile width. Activate the saved-
result information control and use all four primary navigation actions.

**Expected:** The ten-case comparison shows WAKE 83.76 and baseline 49.00,
including the environmental regression. The separate club-memory audit shows
**WAKE 7/7** and **direct baseline 3/7** while stating that it is **not a semantic coaching-quality score**. Content has no horizontal overflow, Review a
session stays in the header, and the disclosure closes after approximately six
seconds.

**Fail if:** results are framed as superiority over a human coach, a negative
result is hidden, navigation disappears, or values become unreadable.

## Live investigation checklist

Complete the replay block first. Stop services and start a clean live runtime:

```bash
./scripts/start_dashboard.sh --live \
  --state-store /private/tmp/wake-owner-qa-live-state.json
```

QA-14 through QA-16 use three separately authorized starts, each with a
US$0.20 operational start authorization, for a total authorization of
**US$0.60**. This authorizes each start and is not a provider billing cap.
Record observed tokens, runtime, and cost after every run.

### QA-13 — Input validation must fail before spend

**Action:** Try to continue with only `speedcoach.csv`. Then open a clean form,
select a complete bundle including `environment.json`, and inspect historical
weather.

**Expected:** A missing plan is rejected before any request. Supplied
environment disables historical-weather lookup. Both validations cost US$0.00.

**Fail if:** a model starts without the core source or two environmental paths
can be submitted together.

### QA-14 — Live core investigation

**Action:** As Athlete, upload only `plan.json` and `speedcoach.csv`, keep
historical weather disabled, and select **Validate and investigate** once.

**Expected:** One bounded investigation uses available evidence, keeps optional
gaps explicit, passes verification, enters the inbox, and displays tokens,
runtime, and cost.

**Fail if:** absent sources are cited, the full replay answer is reused, or
execution cost is hidden.

### QA-15 — Live five-source investigation

**Action:** As Coach, upload all five files, investigate once, answer the human
checkpoint with the matching provenance, and review the memory proposal.

**Expected:** SpeedCoach remains SPM authority, mobile supports route/timing,
zero-only SPM is rejected, environment remains associative, context identifies
the crew, answer provenance remains explicit, and memory requires approval.

**Fail if:** sensors are averaged, relayed evidence is called direct athlete
evidence, the answer rewrites telemetry, or approval is skipped.

### QA-16 — Live weather-enriched investigation

**Action:** Upload `plan.json` and `speedcoach.csv`, enable historical weather,
select the session timezone, authorize rounded-location lookup, and investigate
once.

**Expected:** The interface shows **Historical conditions added** with provider,
sample count, wind, gust, temperature, humidity, rounded-location precision,
and a non-causal boundary.
Route-relative wind uses an explicit context heading or a directionally
consistent GPS-derived heading; otherwise it abstains.

**Fail if:** lookup occurs without consent/timezone, route rows or identity are
sent to the provider, weather becomes causal, or an unreliable route direction
is presented as known.

## Final navigation and presentation checklist

### QA-17 — Bookmarkable navigation and location trail

**Action:** Open Sessions, Competition, Goal memory, and Evaluation directly by
their hash URLs. From each primary destination, open a detail page, then use
browser Back and Forward.

**Expected:** Primary destinations show no false Back control. Detail views show
a clear location trail and return action. Refresh and browser history restore
the same view.

**Fail if:** Back exits the application unexpectedly, a hash cannot be
bookmarked, or the user cannot identify their current context.

### QA-18 — Sessions workspace tabs and mobile layout

**Action:** At desktop and mobile width, move through Overview, Attention, Team,
and Reviews.

**Expected:** Secondary tabs sit below the primary navigation, remain visibly
discoverable without horizontal scrolling, and divide the Sessions workspace
into manageable sections.

**Fail if:** options disappear to the right, stack inside the primary header,
or a feature requires scrolling through unrelated long sections.

### QA-19 — Compact disclosures and readable typography

**Action:** Inspect runtime, saved-result, synthetic demo, and PM5 information
controls with mouse, keyboard, and touch-style click.

**Expected:** Stable technical/provenance explanations open on demand, remain
readable, close after approximately six seconds, and do not occupy permanent
hero cards. Evidence and decision limits that change the current interpretation
remain visible in the normal flow.

**Fail if:** essential evidence is hidden, descriptions dominate the page, or
body/metadata typography is too small to read comfortably.

### QA-20 — Workflow-state and PM5 presentation

**Action:** Open Saved session reviews and a crew or athlete page containing an
indoor result.

**Expected:** The four workflow state cards use an aligned responsive grid. PM5
results remain athlete-owned; the modality boundary is available through a
compact information control and does not claim on-water speed, visible
technique, or muscular strength.

**Fail if:** state counts and descriptions do not align, a PM5 result belongs to
a crew, or indoor numbers are presented as direct on-water measures.

## QA result table

| ID | Mode | Owner result | Current disposition | Evidence or note |
| --- | --- | --- | --- | --- |
| QA-01 | Replay | PASS | Accepted | Plain-language club value understood. |
| QA-02 | Replay | PASS | Accepted | Club-scale deterministic coverage and boundaries visible. |
| QA-03 | Replay | PASS | Accepted | Crew, lineup, athlete, and physical boat remained distinct. |
| QA-04 | Replay | PASS | Accepted | Training Days preserved water/indoor separation. |
| QA-05 | Replay | PASS | Accepted | Missing evidence was routed without athlete judgment. |
| QA-06 | Replay | PASS | Accepted | Second period loaded at US$0.00 with six comparison routes. |
| QA-07 | Replay | INITIAL FAIL | AUTOMATED PASS; owner visual confirmation recommended | Browser QA reopened the verified 102-activity memory through Goal memory, navigated away, returned with Back/Forward, refreshed the detail route, and retained US$0.00 reopen cost. |
| QA-08 | Replay | QUESTION | AUTOMATED PASS; owner visual confirmation recommended | Browser QA found 3 needs-action, 0 awaiting-analysis, 3 viewed, and 0 in-memory records; the four equal-height cards and counts survived refresh. Restart persistence remains covered by the deterministic state-store tests. |
| QA-09 | Replay | PASS WITH FINDING | Accepted after fix | Preparation now provides success feedback and prevents duplicate submission. |
| QA-10 | Replay | PASS WITH FINDINGS | Accepted after fixes | Global action now opens fresh intake; source naming and coach approval purpose were clarified. |
| QA-11 | Replay | PASS | Accepted | Competition field, non-classified result, and causal limits were correct. |
| QA-12 | Replay | INITIAL FAIL | AUTOMATED PASS; owner visual confirmation recommended | At 1440 x 900 and 390 x 844, all four primary actions and Review a session remained visible, no tested route overflowed horizontally, saved Evaluation values were present, and the runtime/saved-result disclosure closed after about six seconds. |
| QA-13 | Live validation | PASS | Accepted | Invalid input and environmental-source conflict failed before spend. |
| QA-14 | Live agent | PASS | Accepted | 34,675 tokens; 38.793 seconds; US$0.117390 observed. |
| QA-15 | Live agent | PASS | Accepted | 34,927 tokens; 26.056 seconds; US$0.099324 observed. |
| QA-16 | Live agent | PASS WITH FINDINGS | Accepted after deterministic fixes | 20,960 tokens; 21.241 seconds; US$0.067120 observed. Timezone became a selector and trustworthy route-heading derivation was added; original paid output remains unchanged. |
| QA-17 | Replay | NOT YET OWNER-RUN | AUTOMATED PASS; owner visual confirmation recommended | Direct hashes, primary/detail trail rules, browser Back/Forward, and refresh restoration passed on Sessions, Goal memory, Evaluation, Competition, crew, athlete, post-regatta, and competition-entry routes. |
| QA-18 | Replay | NOT YET OWNER-RUN | AUTOMATED PASS; owner visual confirmation recommended | Overview, Attention, Team, Intelligence, and Session reviews remained visible below the primary navigation at desktop and mobile widths, with no horizontal overflow. |
| QA-19 | Replay | NOT YET OWNER-RUN | AUTOMATED PASS with keyboard-simulation limitation | Runtime, saved-result, synthetic, and PM5 controls opened on click and auto-dismissed after about six seconds. Controls are native buttons with regression coverage; the browser automation layer did not synthesize Enter/Space activation reliably, so final keyboard feel remains a short human check. |
| QA-20 | Replay | NOT YET OWNER-RUN | AUTOMATED PASS; owner visual confirmation recommended | Workflow cards rendered as four equal 293.75 px columns on desktop, persisted after refresh, and the PM5 disclosure kept each result athlete-owned while rejecting direct on-water, visible-technique, and muscular-strength claims. |

## Final acceptance condition

Automatic closeout now passes QA-07, QA-08, QA-12, and QA-17 through QA-20.
Before recording, the owner should perform a short visual confirmation of the
same paths, with particular attention to keyboard feel and whether a coach can
understand the hierarchy without technical explanation. Any remaining failure
that blocks the five-minute story blocks the final video. Non-blocking polish
should be recorded rather than expanding scope on submission day.
