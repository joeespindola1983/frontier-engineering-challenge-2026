# Five-minute WAKE solution video

**Status:** recording script frozen; final owner rehearsal remains

This route is designed to satisfy the submission requirement without relying
on a live model call. The interface reopens committed, verified artifacts at
US$0.00. Keep the browser at 1280 × 800 or larger and use Node.js 22.13 or
newer when starting the dashboard.

## Before recording

1. Run `./scripts/reproduce_submission.sh --verify-only` once.
2. Start the replay with `./scripts/start_dashboard.sh`.
3. Open `http://localhost:3000/` and reset the post-regatta package if it is
   already loaded.
4. Close unrelated tabs, disable notifications, and use 125% browser zoom only
   if the recorded text is too small.
5. Keep this script and the repository Evaluation artifacts available, but do
   not show private inputs, `.env`, raw GPS, or evaluator ground truth.

## Timed route and narration

### 00:00–00:35 — Problem and simple baseline

**Screen:** Sessions / club overview.

**Say:**

> A rowing coach may receive a plan through WhatsApp, a personal SpeedCoach
> export from the athlete, optional phone telemetry, conditions, and human
> context. The simple baseline is a direct GPT call over a compact summary. A
> spreadsheet or dashboard can display these records, but the coach must still
> reconcile every source, athlete, boat, and missing answer manually.

Point to the club, crew, and athlete navigation. Do not open a technical
evaluation artifact yet.

### 00:35–01:15 — What makes WAKE agentic

**Screen:** Open the investigated session and its evidence review.

**Say:**

> WAKE first performs deterministic work: it normalizes telemetry, aligns
> recordings, reconstructs intervals, compares the plan, and assigns trust per
> metric. The bounded agent can then inspect four read-only tools, request
> missing context, and pass a verifier before a coach-facing briefing is saved.
> It never receives raw high-volume telemetry and it cannot turn an unsupported
> hypothesis into an observed fact.

Show the compact investigation trace, metric source explanation, and one
material deviation.

### 01:15–02:05 — Club scale and evolving memory

**Screen:** Return to Sessions. Show the original period, then select **Load
2-week package**.

**Say:**

> The first period contains 52 independently stored activities. The second
> package adds 50 more for the same fictional, real-informed club. WAKE now has
> 102 activities across 16 athletes and 10 crews. The records remain the source
> of truth; new evidence updates deterministic comparisons before the model is
> asked to synthesize anything.

Show the six outcomes: comparable faster, comparable slower, stable,
environment-confounded, participation review, and insufficient comparison.
Keep `NOT_ESTABLISHED` visible.

### 02:05–02:55 — Saved club intelligence

**Screen:** Open **Saved WAKE club memory**.

**Say:**

> One bounded GPT execution synthesized the complete 102-activity scope. It
> used all four investigation tools, passed strict verification, cost
> US$0.037384, and was saved by WAKE with provider storage disabled. Reopening
> it costs US$0.00. It preserves three narrow indoor observations, refuses a
> club performance trend, and gives the coach three priorities and four human
> questions instead of pretending missing context is a conclusion.

Show the briefing, the missing 4x plan, women's 8x context, Andre's record gap,
and Sofia's unmatched workout shape.

### 02:55–03:35 — Human checkpoint and memory approval

**Screen:** Open the hero session checkpoint.

**Say:**

> Device measurements and human knowledge remain separate. The athlete or
> coach can answer according to direct participation, observation, or a relayed
> report. The answer does not rewrite telemetry. Only after review and explicit
> approval does the briefing become club memory.

Show the human checkpoint, answer provenance, verified briefing, and approved
memory milestone.

### 03:35–04:05 — Training to competition context

**Screen:** Competition Review, then one boat report.

**Say:**

> Competition Review connects the same fictional athletes, exact lineup
> snapshot, physical boat, pre-race shared outings, and complete result field.
> It adds context without claiming that a training block or lineup caused the
> result and without automatically selecting a crew.

Show the full field, official order, lineup, and one non-completion requiring
human context.

### 04:05–04:35 — Measured improvement

**Screen:** Evaluation.

**Say:**

> On ten frozen cases with the same task and grader, the direct baseline scored
> 49.00 out of 100 and WAKE scored 83.76. Every case improved, but environmental
> interpretation fell from 80 to 76 percent, so that regression remains
> visible. These results establish workflow improvement on fixed cases, not
> superiority over a human coach or broad athletic-performance validation.

Show the aggregate result and one difficult case.

### 04:35–04:50 — Changelog, failure, and removed experiment

**Screen:** Improvement Changelog or the evaluation summary.

**Say:**

> The most important correction came from a failed progressive-evidence run.
> The removed experiment was the v1 behavior that treated reconstructed segment
> distance as proof of prescribed-distance completion. TDD added the boundary,
> the verifier rejected conflicting claims, and v2 passed every applicable
> capability check. A separate longitudinal pilot produced no demonstrated
> quality gain, and we preserved that neutral result as well.

### 04:50–05:00 — Reproduction and close

**Screen:** README reproduction command or final WAKE screen.

**Say:**

> Judges can reproduce tests, baseline requests, saved trajectories,
> evaluation, and the production interface from a clean checkout for US$0.00.
> Every row leaves a wake; WAKE turns that trail into evidence a coach can
> review and trust.

## Recording acceptance checklist

- The final edit is no longer than five minutes.
- The simple baseline appears before the agent solution.
- One realistic path runs from evidence to human checkpoint and saved memory.
- The 102 activities, 16 athletes, and 10 crews are visible.
- The 83.76 and 49.00 evaluation values are readable.
- One failure and one removed experiment are named.
- Costs are described as observed values, not provider caps.
- No private file, credential, raw GPS location, or real athlete identity is
  visible.
