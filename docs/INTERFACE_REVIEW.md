# Interface review and visual evidence plan

**Status:** interface remediation complete; targeted owner recheck and final recording remain

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
crews, Lucas and his Training Days, Crew: Tuiuiú - 8x - Women with athlete context pending,
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

The timed recording route now prioritizes coach and athlete value, with the
technical comparison and experiment history kept as a short credibility layer.
It remains subject to owner QA before recording and lives in
[`VIDEO_DEMO_SCRIPT.md`](VIDEO_DEMO_SCRIPT.md).

## Owner replay QA remediation — 2026-08-30

The owner completed QA-01 through QA-12. Ten checks passed, QA-07 failed
because the loaded post-regatta memory had no route after leaving its page,
QA-12 failed because the header removed primary navigation at mobile width,
and QA-08 required a non-empty inbox recheck. QA-09 and QA-10 also exposed
state and comprehension issues: completed preparation remained actionable,
Review a session did not start a fresh intake, and `Environmental timeline`
did not match the supplied `environment.json` language.

The remediation keeps the saved 102-activity artifact permanently reachable
through Goal memory, changes the club entry to **Open loaded package** after
loading, resets intake-local state for every new review, shows **Preparation
complete**, disables the completed action, provides **Start another session
review**, uses **Environment timeline**, and keeps the four primary navigation
actions in a horizontally reachable mobile row. These code changes pass the
new regression tests, but the original owner failures remain preserved in the
QA guide until the visual fix-verification sequence is repeated.

## Owner live QA findings — 2026-08-30

QA-13 through QA-16 completed successfully. The three live investigations all
passed verification and together cost US$0.283834, within the US$0.60 total
operational start authorization. The run also exposed four presentation and
evidence-preparation issues that are now covered by deterministic regressions:

- keep the mobile review action on the first header row and contain the wide
  interval chart inside its own mobile scroller;
- constrain historical-weather timezone selection;
- derive a representative heading from SpeedCoach GPS only for a directionally
  consistent route, with human-confirmed context taking precedence;
- render `Current reconstruction` as short bullets and translate internal
  evidence references into coach-readable source names.

The saved QA-16 output remains unchanged. Its route-heading abstention is useful
historical evidence of the limitation found by owner review; the correction is
recorded separately rather than rewriting the earlier model response.

## Consistent location and return path — 2026-08-30

Owner review found that detail screens depended on inconsistent header actions
such as `Back to club`, while browser Back could leave the single-page product.
WAKE now displays one location bar below the primary navigation on every detail
screen. It combines a prominent back arrow with a breadcrumb for sessions,
crews, athletes, longitudinal reports, competition entries, goal memory, and
evaluation.

Internal history entries retain the selected crew, athlete, and competition
boat. Browser rehearsal confirmed the path `Crew: Tucano - 2x - Men → Lucas → Back` and
`Competition Review → Crew: Tucano - 2x - Men → Back`, including restored headings and
breadcrumbs. At 390 × 844, the location bar remains within the viewport and
does not reintroduce horizontal overflow.

## Sessions task workspace — 2026-08-30

Owner review found that Sessions had become a complete but excessively long
product inventory. WAKE now separates the same content into five coaching
areas: Overview for the club pulse and validation coverage, Attention for
decision candidates, Team for training days and relational crew/athlete/boat
memory, Intelligence for preserved WAKE analyses, and Session reviews for the
operational inbox.

Only one area renders at a time. The selector remains at the top, the current
area is visually explicit, and the primary **Review a session** action remains
available without searching below the fold. Browser validation confirmed that
opening Crew: Tucano - 2x - Men from Team and returning restores Team. Session reviews
now opens the saved inbox in a 1,337 px document at the tested desktop size,
instead of placing it after the full club history. At 390 × 844, the selector
scrolls internally (794 px content inside a 360 px control) while the document
itself remains exactly 390 px wide.

### Mobile discovery correction

The first mobile implementation contained horizontal scrolling but did not
make the hidden choices discoverable. Owner review correctly identified that
technical reachability was not enough: Intelligence and Session reviews could
disappear to the right without a visible cue. The mobile selector now renders
all five areas at once as a two-column grid, with Session reviews spanning the
last row. Browser checks confirmed that every button stays inside the selector
at both 390 px and the 320 px minimum, with no document or selector overflow.

### Secondary-navigation hierarchy correction

The fully visible selector solved mobile discovery but still appeared inside
the Sessions content, after the prototype notice and page heading. Owner review
identified the hierarchy mismatch: Overview, Attention, Team, Intelligence,
and Session reviews are destinations below Sessions, not content cards.

The selector is now a dedicated secondary tab bar immediately below the primary
navigation. The current page heading and action follow it inside the page. On
desktop, the active destination uses an accent underline and restrained
background; on narrow screens the same navigation remains a complete two-column
grid rather than becoming a hidden horizontal row. Browser checks confirmed the
tab bar begins exactly where the primary header ends at desktop and mobile
widths, all five destinations remain visible, and selecting Team updates both
the active tab and page heading without document overflow.

## Compact runtime disclosure — 2026-08-30

The full-width `Local live runtime` notice repeated execution details before
the user reached the selected Sessions content. Owner review requested a status
pattern instead: persistent awareness with detail on demand.

WAKE now places a circular live/replay indicator immediately before the global
**Review a session** action. Hover, keyboard focus, and click expose the full
runtime boundary; clicking again closes it. Live uses the product accent and
replay/not-live uses the warning color. The pop-up replaces the repeated generic
notice across product screens, while dataset-specific synthetic disclosures
remain where their provenance matters.

Browser validation confirmed that the indicator precedes the review action,
the pop-up contains the complete live explanation, and both controls remain
visible without horizontal overflow. At 320 px, the fixed mobile pop-up stayed
between 14 px page gutters and the document remained exactly 320 px wide.

### Owner refinement

The first compact version opened on hover, focus, or click and included an
instructional footer explaining those interactions. Owner review found both
the automatic behavior and the footer unnecessary. The retained version opens
only after click, tap, or keyboard activation and closes on the next activation.
The pop-up now contains only the runtime label and material execution boundary.
If left open, it dismisses itself after six seconds so it does not cover the
Sessions tabs or page content indefinitely.

## Evaluation saved-artifact disclosure — 2026-08-30

The Evaluation page repeated a permanent `Saved result · No model call` banner
even though that boundary never changes while viewing the committed artifacts.
It now uses a small information indicator at the right of the Evaluation
heading. Click or keyboard activation opens the complete no-agent/no-cost
explanation; a second activation or the same six-second timeout closes it.

Browser validation found the old notice absent, the information control on the
right half of the header, the full disclosure visible after click, no document
overflow, and automatic dismissal after 6.25 seconds.

## Accessible typography and card hierarchy — 2026-08-30

Owner review identified the opposite ends of the same hierarchy problem:
primary headings were oversized while most descriptions and metadata were too
small to scan comfortably. The accumulated stylesheet included visible 7, 8,
9, and 10 px text throughout Evaluation, crew, athlete, and competition
surfaces.

WAKE now uses one bounded semantic scale. Compact metadata is 11 px, captions
are 12 px, normal explanatory copy is 14 px, ledes are 17 px, and the primary
display scale stops at 58 px. Promoted briefing copy remains intentionally
larger. Prominent evidence groups share a restrained 8 px radius and subtle
shadow, while interactive crew, athlete, attention, and session rows receive
consistent hover and keyboard-focus treatment. Reduced-motion preferences
disable those transitions.

The RED-first design-system tests now cover the tokens, readable-copy rules,
and shared card states. The full 96-test web suite, lint, and production build
pass. Browser inspection at the current desktop width and at 390 × 844 covered
all Sessions areas, intake, goal memory, crew and athlete details, competition,
longitudinal comparison, and post-regatta memory. No inspected screen retained
visible text below 11 px or horizontal document overflow. This establishes a
legibility baseline; it does not replace a dedicated WCAG contrast, zoom,
screen-reader, and assistive-technology audit.

## Single session-review action — 2026-08-30

Owner review identified two identical **Review a session** actions on Sessions
pages: the persistent global action and a second button inside the current area
heading. WAKE now keeps only the global action beside the runtime indicator.
All five Sessions areas share that same entry point instead of repeating it in
their content.

A RED-first regression test protects the single-action contract. Browser checks
confirmed one visible global action and no heading-level duplicate across the
five desktop areas. At 390 x 844, the global action remains present, the removed
button does not return, and the document has no horizontal overflow.

## Period-aware club pulse heading — 2026-08-30

Owner review identified that `Two-week club pulse` described the current demo
fixture as if two weeks were a permanent product boundary. The same header also
placed its deterministic scan status at the far right of the introduction,
breaking the reading sequence.

The screen now uses the stable title **Club training pulse**. Coverage is
derived from the dataset and displayed as **10 training days · 17–28 Aug 2026**
for the current fixture; changing the period changes this metadata without a
copy edit. The scan status appears directly below the description and derives
its verified-investigation count from the analysis. The lower validation title
is now period-neutral as well. Desktop and 390 x 844 browser checks confirmed
the status is below and left-aligned with the copy and produces no overflow.

## Bookmarkable navigation and nested-only Back — 2026-08-30

Owner review identified that Competition, Goal memory, and Evaluation displayed
the same Back trail as their detail pages even though they are primary product
destinations. The prior `pushState` implementation also left the address bar at
the root URL, so browser history worked only inside the current visit and a
specific athlete, crew, or result could not be bookmarked.

Primary destinations now render without an in-product Back control. Opening a
boat report, crew, athlete, intelligence report, or session-review step adds the
shared trail. Readable hash routes identify every state, including
`#competition`, `#goal-memory`, `#evaluation`, and nested paths such as
`#sessions/team/athlete/athlete-sofia`. Browser Back/Forward restores the route,
and a direct detail bookmark survives reload. Desktop and 390 x 844 checks found
the expected trail boundary and no horizontal overflow.

## Compact competition provenance — 2026-08-30

Owner review identified that the permanent **Real-informed synthetic regatta**
card used prime header space to repeat a stable fixture boundary. Competition
overview and boat reports now place a small information control at the right of
their heading. Opening it explains exactly which competition structure came
from supplied official material and that every displayed identity, outcome,
and training history remains fictional. The boat version explicitly states
that no real athlete is attached to the report.

The visible page now prioritizes the club result, athletes, boats, competitive
field, preceding work, and unsupported conclusions. Stable implementation
explanations remain available through progressive disclosure instead of
competing with the rowing story. The focused eight-test suite passes. Browser
rehearsal confirmed one control per page, zero legacy notices, automatic closure
after six seconds, and no horizontal overflow on the inspected mobile layout.

## Compact club-fixture context — 2026-08-30

Owner review identified that the top of **Club training pulse** repeated three
implementation-facing explanations before presenting the operational club
metrics: deterministic scan status, a two-column real-versus-fictional block,
and a second investigation boundary. These were accurate but made the product
read like technical documentation.

The heading now shows only the dataset-derived period, the coaching purpose,
and a compact **Synthetic demo** label. Its disclosure distinguishes the real
rowing structures and source formats from the fictional people, boats,
sessions, outcomes, and club history. Coverage, selected investigations,
routed questions, and cost remain visible in the metric row below because they
change with the evidence and support an operational decision.

The 16 focused club tests pass. Browser rehearsal found no legacy explanatory
blocks, confirmed the disclosure closes after six seconds, and kept both label
and pop-up within a 390 px viewport without horizontal overflow.

## Product-wide copy audit and Overview shortcuts — 2026-08-30

The next owner review expanded the cleanup beyond the club heading. The audit
classified copy by whether it changes the user's present rowing interpretation.
Visible workflow copy now retains alerts, missing evidence, modality boundaries,
causation limits, consent, and cost authorization. Stable fixture construction,
prototype storage, and validation-source mechanics moved behind accessible
six-second disclosures. Model scores, tool behavior, cost comparisons, and
experimental claims remain centralized in Evaluation and documentation.

The audit removed the repeated navigation instruction in Sessions, the second
Session reviews introduction, the full-width local-storage note, the validation
fixture block, and synthetic-data banners repeated above crew and athlete
details. Crew and athlete headers now reuse the same compact club-data control.

The former loose **View evaluation results** and **Open competition review**
buttons are now two surfaced shortcut cards. Each has an icon, a short purpose
label, a strong destination title, and a directional arrow. Browser rehearsal
confirmed both routes, zero legacy blocks on the inspected screens, and no
horizontal overflow. At 390 px the shortcuts stack as two full-width 76 px
controls. The 42 focused tests pass before the complete suite.

## Review-state alignment and PM5 context — 2026-08-30

Owner review found that the four Session reviews states read as one metric row
but used unequal cell insets and independently sized internal rows. The revised
surface gives every cell the same padding and aligns the label, value, and
description tracks. At the small breakpoint, all four cards are 134 px high in
a two-by-two grid and the page has no horizontal overflow.

The permanent `One PM5 result, one athlete` block also repeated a stable rule
below Training days. It is now a labeled `PM5 context` disclosure beside the
section heading. Its three bullets retain the athlete-owned record boundary,
equivalent Concept2 workout comparison, and the prohibition on treating indoor
pace, SPM, or watts as direct evidence of on-water speed, visible technique, or
muscular strength. The disclosure closes after six seconds.
