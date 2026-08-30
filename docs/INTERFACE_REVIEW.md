# Interface review and visual evidence plan

**Status:** final five-minute coach-path QA and recording script complete; owner rehearsal remains

The local browser rehearsal completed the full synthetic workflow: independent
source selection, upload, replay-safe investigation, review, human checkpoint,
verified briefing, and approval-gated memory. This establishes a working demo
slice, not a production club application.

## What the interface already proves

- Plan and SpeedCoach are the core inputs; mobile, environment, and context are
  visibly optional.
- One material SPM deviation is distinguishable from compliant intervals.
- Metric-level source trust is inspectable instead of hidden behind one device
  score.
- Environmental context is associated in time without being shown as a causal
  verdict.
- A missing human fact becomes one focused question and remains separate from
  telemetry.
- Memory changes only after coach approval.

## Browser rehearsal findings

The first real upload rehearsal found two runtime defects that isolated mocks
had not exposed: the default browser `fetch` receiver was lost, and the session
row forwarded its click event as if it were an evidence bundle. Both now have
regression tests.

The visual review also found that every prescribed SPM range was drawn at one
fixed height. The chart now uses one explicit 16–26 SPM scale, calculates each
target band from its own minimum and maximum, and clamps only the geometry while
retaining the original labels.

## Final coach-path QA — 2026-08-30

The final in-app browser rehearsal covered the club pulse and all ten recurring
crews, Lucas and his Training Days, South Women 8x with athlete context pending,
the approved hero-session memory, Competition Review, the official ten-case
WAKE-versus-baseline view, the completed neutral longitudinal pilot, and the
new post-regatta package before and after loading.

One comprehension defect was found: the club status still said longitudinal
synthesis had not run while the completed four-report pilot appeared directly
below it. A RED regression test was added, then the copy was corrected to state
that the separate pilot is complete and did not demonstrate a quality gain.

The post-regatta screen showed 50 activities, 16 athletes, 10 crews, no model
call, US$0.00, six evidence-ranked outcomes, and `NOT_ESTABLISHED` causation. At
390 × 844 it had no horizontal overflow; cards remained legible and the compact
header retained an app action. Application console review found no warnings or
errors. The final tab was restored to the Sessions page for owner QA.

## Highest-value presentation improvements

### 1. Decision-first session synopsis

Make the first review viewport answer three questions within seconds:

1. What matched the plan?
2. What needs attention?
3. What cannot be concluded yet?

The existing prose is evidence-correct but too dense for a five-minute judge
demonstration. A compact three-state synopsis should precede the detail.

### 2. Agentic investigation trace

Show a concise, product-level trace such as `recordings matched -> intervals
reconstructed -> trust assigned -> claims verified -> one question requested`.
This should expose work performed and verification status without exposing
chain-of-thought or turning tools into user controls.

### 3. One combined session timeline

Add one deliberately bounded timeline that aligns prescribed SPM, measured SPM,
speed change, and the environmental phase. It should annotate the material
work-05 deviation and wind transition while retaining the non-causal boundary.
Avoid a general dashboard or a collection of unrelated charts.

### 4. Evidence value comparison

Make optional evidence value visible: SpeedCoach establishes plan execution;
context/environment supports human and condition association; mobile adds route
and session corroboration but is rejected for broken SPM. This is the strongest
visual bridge from the progressive-evidence evaluation to product value.

### 5. Demonstration legibility

Increase the visual prominence of the key decision, evidence status, and
verification result. Keep the quiet rowing-inspired palette, but reduce long
paragraphs and tiny metadata in the primary video path. Validate the final
screens at presentation resolution and at the existing mobile breakpoint.

## Deliberate exclusions

- Do not add a broad analytics dashboard merely to look data-rich.
- Do not add route maps that expose private coordinates or imply that a map is
  required for the core workflow.
- Do not infer technique, synchronization, physiology, or coaching prescriptions
  from ordinary telemetry.
- Do not visualize a longitudinal trend from one approved session.

## Next acceptance check

The next interface milestone should be accepted only when a coach or judge can
identify the material deviation, the selected evidence, the unresolved human
question, and the agentic work performed in under 30 seconds without reading the
full briefing.

The timed recording route, narration, and privacy checklist are frozen in
[`VIDEO_DEMO_SCRIPT.md`](VIDEO_DEMO_SCRIPT.md).
