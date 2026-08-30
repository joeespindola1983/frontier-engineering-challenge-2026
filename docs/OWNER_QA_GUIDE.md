# WAKE owner interface QA guide

**Purpose:** validate the product as a rowing coach or athlete would experience
it, first through zero-cost replay and then through explicitly authorized live
investigation paths.

**QA URL:** [http://localhost:3000/](http://localhost:3000/)

**Upload data:** `data/qa-interface/full-replay-bundle/`

**Live execution scope:** three separately authorized agent starts, with a
US$0.60 total operational authorization. The weather provider lookup itself
does not call the model; the third model start evaluates the weather-enriched
bundle.

Record each step as `PASS`, `FAIL`, or `QUESTION`, with one screenshot and a
short note for every failure. Do not change code during the run; finish the
sequence first so related problems can be evaluated together.

## Before QA

1. Stop any existing WAKE dashboard with `Ctrl+C`.
2. From the repository root, run the following command with no `--live` flag:

   ```bash
   ./scripts/start_dashboard.sh \
     --state-store /private/tmp/wake-owner-qa-replay-state.json
   ```
3. Confirm the terminal prints `Mode: replay (no model call)` and the dashboard
   link `http://localhost:3000/`.
4. Open the link and confirm the top notice says `Real-informed synthetic demo`,
   not `Local live runtime`.
5. Keep `data/qa-interface/full-replay-bundle/` open in Finder for the upload
   steps. Every file is public and synthetic.

If the interface shows live mode, do not perform the upload QA. Restart in
replay mode first. The complete sequence should cost **US$0.00**.

The isolated QA state path avoids inheriting an earlier answer while preserving
state throughout this run. It does not delete or modify the normal local club
state.

## Sequential checklist

### QA-01 — Product entry and plain-language value

**Action:** Open the Sessions page and read only the first screen before
scrolling.

**Expected:** Within 15 seconds, a coach should understand that WAKE connects
club activity, athletes, recurring crews, boats, and evidence so attention can
be directed without opening every chart. `View evaluation results`, `Open
competition review`, and `Review a session` must be reachable.

**Fail if:** the first screen looks like a single-session telemetry dashboard,
or the real-informed synthetic boundary is not visible.

### QA-02 — Club-scale workload

**Action:** Inspect the Two-week club pulse and validation funnel.

**Expected:** `52/52` records screened and reconstructed, 51 plan-compared,
two agent-verified, zero human-approved, 16 athletes, 10 crews, and separated
water/indoor volume. Missing records must be questions, not judgments about
fitness, injury, commitment, or discipline.

**Fail if:** deterministic reconstruction is presented as coach approval or
all 52 sessions are presented as GPT calls.

### QA-03 — Crew, lineup, and physical boat memory

**Action:** Under Team and crew memory, open **Harbor Men 2x**.

**Expected:** The page identifies the 2x, its named physical shell, recurring
lineup, planned versus launched outings, and the unavailable-crew day. Athlete
links must be actionable.

**Fail if:** crew, boat, and athletes are collapsed into one label, or an
unavailable outing is described as athlete failure.

### QA-04 — Athlete Training Days

**Action:** Open **Lucas** from the crew or athlete roster and inspect Training
Days.

**Expected:** Water, solo, and Concept2 records are connected chronologically.
Combined, water-only, and indoor-only days are distinguishable. Water and
indoor distance remain separate, and the physical boats and crews used by the
athlete are visible.

**Fail if:** ergometer distance is added to water distance as one performance
total, or a PM5 result is treated as a crew result.

### QA-05 — Coach attention versus missing context

**Action:** Return to Sessions and inspect the prioritized review list.

**Expected:** Numeric deviations, missing plans, crew availability, and athlete
context are routed differently. Open one crew-unavailable item and one athlete
context item.

**Fail if:** a missing activity becomes a medical, fitness, or commitment
conclusion, or all alerts are presented with the same confidence.

### QA-06 — Add the second training period

**Action:** Select **Load 2-week package**.

**Expected:** The interface adds 50 post-regatta activities for the same 16
athletes and 10 crews, reaches a 102-activity combined history, and shows six
comparison routes: faster comparable, slower comparable, stable, wind
confounded, participation review, and insufficient equivalent evidence.
`No model call`, `US$0.00`, and `NOT_ESTABLISHED` must remain visible.

**Fail if:** faster automatically means improved fitness, wind is stated as a
cause, or the package silently triggers GPT.

### QA-07 — Saved club intelligence

**Action:** Open **Saved WAKE club memory** after loading the second period.

**Expected:** The saved briefing covers 102 activities and presents supported
observations, three coach priorities, four human/source questions, and explicit
limits on performance trend and causation. Reopening must cost `US$0.00`.

**Fail if:** missing context is written as fact, the report claims broad club
performance improvement, or reopening starts another analysis.

### QA-08 — Session inbox and workflow milestones

**Action:** Return to Sessions and inspect the operational session list.

**Expected:** Analysis, coach view, human answer, and club-memory approval are
separate milestones. Previously answered or approved sessions remain in their
saved state after reopening.

**Fail if:** opening a session resets it, or `analysed`, `viewed`, `answered`,
and `approved` are represented as one status.

### QA-09 — Minimum upload without optional evidence

**Action:** Select **Review a session**. Keep `Athlete` as contributor. From
`data/qa-interface/full-replay-bundle/`, choose only:

- Training plan — `plan.json`
- SpeedCoach recording — `speedcoach.csv`

Do not select mobile, environment, or context. Select
**Validate and prepare · No agent call**.

**Expected:** WAKE validates and saves a prepared local session, explicitly
shows Plan + SpeedCoach coverage, keeps the three optional sources missing, and
states that no agent call occurred. The session appears in the inbox.

**Fail if:** optional evidence blocks preparation, a committed answer is reused,
or the action incurs cost.

### QA-10 — Complete five-source replay and human checkpoint

**Action:** Open a fresh **Review a session** form and choose all files from
`data/qa-interface/full-replay-bundle/` in the displayed order. Keep historical
weather disabled because `environment.json` is supplied. Select
**Validate and open replay**.

**Expected:** The review reconstructs six 1 km work intervals, keeps SpeedCoach
as the usable SPM source, rejects mobile SPM stuck at zero, shows the real low-
SPM deviation, and treats the wind change as associated rather than causal.
The resistance-band question is a human checkpoint for the athlete or an
appropriately sourced observer; answering it must not rewrite telemetry.

If the exact session was answered during an earlier QA run, reopening its saved
answer is a persistence PASS, not a reset failure.

**Fail if:** mobile zero becomes the selected SPM, wind becomes proven cause,
or a human answer is relabelled as device evidence.

### QA-11 — Competition Review

**Action:** Open **Competition Review**, then one boat report and the entry that
was not classified.

**Expected:** Ten club entries connect exact lineup snapshots, athletes,
physical boats, shared pre-race outings, full fictional fields, official order,
and one missing-context result. Training history is context, not proof that a
lineup or workout caused the result.

**Fail if:** the product automatically selects crews, invents a result for the
non-classified entry, or presents fictional identities as real competitors.

### QA-12 — Evaluation, credibility, and responsive check

**Action:** Open **Evaluation**. Then narrow the browser to approximately mobile
width and scroll through the top comparison blocks.

**Expected:** The fixed ten-case score shows 83.76 for WAKE and 49.00 for the
direct baseline, including the visible environmental regression. The separate
club-memory experiment shows **WAKE 7/7** and **direct baseline 3/7** while
stating that it is **not a semantic coaching-quality score**. Content must not
overflow horizontally at mobile width.

**Fail if:** the structural audit is presented as superiority over a human
coach, the negative result/regression is hidden, or values become unreadable.

## Live investigation checklist

Complete QA-01 through QA-12 first. Then stop the replay services with `Ctrl+C`.
The three tests below use **three separately authorized starts**, each with a
US$0.20 operational start authorization, for a total authorization of
**US$0.60**. This authorization allows each execution to start; it is not a
provider billing cap. Record the observed cost shown by WAKE after every run.

Start a clean live dashboard:

```bash
./scripts/start_dashboard.sh --live \
  --state-store /private/tmp/wake-owner-qa-live-state.json
```

Confirm both the terminal and interface say live mode before proceeding.

### QA-13 — Input validation must fail before spend

**Action:** Open **Review a session**, select only `speedcoach.csv`, and try to
continue. Then return to a clean form, select the complete bundle including
`environment.json`, and inspect the historical-weather control.

**Expected:** Missing `plan.json` is rejected before any request. When an
environment timeline is uploaded, historical-weather lookup is disabled so the
two environmental sources cannot be requested together. No model cost is
created in either validation check.

**Fail if:** a model starts with a missing core source or both environmental
paths can be submitted together.

### QA-14 — Live core investigation: Plan + SpeedCoach

**Action:** Open a fresh form, select `Athlete`, and upload only `plan.json` and
`speedcoach.csv`. Keep historical weather disabled. Select **Validate and
investigate** once.

**Expected:** One bounded live investigation runs under a US$0.20 operational
start authorization. The output uses the available plan and SpeedCoach, keeps
mobile, environmental, and human-context gaps explicit, passes verification,
appears in the session inbox, and displays observed tokens, runtime, and cost.

**Fail if:** the result cites absent optional sources, silently reuses the full
replay answer, or hides execution cost.

### QA-15 — Live complete investigation: five supplied sources

**Action:** Open a fresh form, select `Coach`, upload all five files, and select
**Validate and investigate** once. Complete the resistance-band checkpoint
using the answer provenance that matches the scenario being tested.

**Expected:** A second bounded start analyses all five sources. SpeedCoach
remains the SPM authority; mobile supports route/timing but its zero-only SPM is
rejected; environment remains associative; context identifies the men's 2x;
the answer records who answered, who entered it, and the authority basis. The
briefing requires explicit approval before club memory changes.

**Fail if:** all sensors are averaged, a coach-entered relay is recorded as
direct athlete evidence, the answer rewrites telemetry, or approval is skipped.

### QA-16 — Live weather-enriched investigation

**Action:** Open a fresh form, upload only `plan.json` and `speedcoach.csv`,
enable **Use historical weather**, enter `America/Sao_Paulo`, authorize the
rounded location lookup, and select **Validate and investigate** once.

**Expected:** The interface shows **Historical conditions added**, including
provider, sample count, wind, gust, temperature, humidity, rounded-location
precision, and the non-causal boundary. A third bounded investigation runs and
keeps weather as contextual evidence rather than proof of performance cause.

**Fail if:** the lookup occurs without consent/timezone, precise route rows or
athlete identity are sent to the provider, weather becomes causal, or the core
bundle is lost when weather is unavailable.

## Final owner questions

After the sequence, answer these from rowing experience:

1. Can a coach identify the three most important next actions in under one
   minute?
2. Is it always clear whether a claim comes from the plan, SpeedCoach, mobile,
   environment, deterministic derivation, or a person?
3. Are missing participation and crew availability phrased as questions rather
   than judgments?
4. Does the athlete view tell a useful story across crew, solo, and indoor work?
5. Does Competition Review add context without pretending to explain the race?
6. Would the saved memory reduce repeated manual comparison work for a coach?
7. Which screen or phrase still feels technically correct but unnatural to a
   rowing practitioner?

## QA result template

```text
Date/time:
Browser and viewport:
Mode confirmed: replay / live

QA-01 PASS | FAIL | QUESTION — note
QA-02 PASS | FAIL | QUESTION — note
QA-03 PASS | FAIL | QUESTION — note
QA-04 PASS | FAIL | QUESTION — note
QA-05 PASS | FAIL | QUESTION — note
QA-06 PASS | FAIL | QUESTION — note
QA-07 PASS | FAIL | QUESTION — note
QA-08 PASS | FAIL | QUESTION — note
QA-09 PASS | FAIL | QUESTION — note
QA-10 PASS | FAIL | QUESTION — note
QA-11 PASS | FAIL | QUESTION — note
QA-12 PASS | FAIL | QUESTION — note
QA-13 PASS | FAIL | QUESTION — note
QA-14 PASS | FAIL | QUESTION — observed cost / note
QA-15 PASS | FAIL | QUESTION — observed cost / note
QA-16 PASS | FAIL | QUESTION — observed cost / note

Top three comprehension problems:
1.
2.
3.

Rowing-language corrections:
1.
2.
3.
```
