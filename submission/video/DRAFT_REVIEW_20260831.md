# WAKE final video — animated draft review

**Accepted source artifact:** `wake-final-submission-draft-v23.mp4`

**Promoted delivery artifact:** `wake-final-submission.mp4`

**Open subtitles:** removed after owner QA

**Preserved caption experiment:** `wake-final-submission-draft-v21-captioned.mp4`

**Preserved comparison artifacts:** draft versions 1–22

**Status:** accepted by the project owner on 2026-08-31 and promoted without
content changes. SHA-256:
`1acf067120a5e4ed94baae685824ceeb97b0b86370f4cde66d27fa67bebd48c4`.

**Capture and context correction in draft 14:** current product chapters use a
1200 × 900, 4:3 browser composition without visible scrollbars. This preserves
more vertical product context and avoids the bottom-scrollbar crop in earlier
screens. The product occupies 76% of the 1920 × 1080 frame; a 24% narrative
rail restores one short contextual paragraph without returning to transcript
panels. The isolated capture runtime was genuinely live-enabled, so the status
indicator is green. No paid execution was triggered merely to record footage;
the review and evaluation views retain already verified evidence and costs.

## Technical profile

- Duration: 299.232 seconds (`04:59.232`)
- Frame: 1920 × 1080
- Frame rate: 30 fps
- Video: H.264
- Audio: AAC, mono, 48 kHz
- Size: 13,535,323 bytes (approximately 12.9 MiB)

## Clean chapter assembly and final-audio timing in draft 23

Draft 23 fixes a structural audio edit discovered in owner QA. The former
chapter-two replacement occupied seconds 63–129 even though the original human
checkpoint began at 122.967. That overwrite removed the opening of chapter
three and made the visual timing derived from the old cue sheet unreliable.
The final track is now assembled from all seven original recordings. Chapter
two shortens pauses longer than 250 ms and uses a bounded 1.98% tempo adjustment
to end at 122.817, followed by a 150 ms transition before the complete human
chapter. No spoken sentence is removed.

The visual edit follows the resulting audio: the bounded-agent sequence begins
at 01:22.661 and stays through the verifier; reconstruction begins at
01:47.083; Source Trust begins at 01:54.100; Environment begins with the wind
sentence at 02:00.237; and the human checkpoint begins at 02:03.160. All click
pulses are removed while cursor travel still explains navigation. The final
video stream is 299.232 seconds, the audio stream is 299.032 seconds, and the
last frame therefore remains visible after the final word.

## Narration-aligned visual sequence in draft 22

Draft 22 removes open subtitles and treats the final assembled narration as the
edit authority. The former cut changed subject while a sentence was still
describing the previous screen. The corrected timeline starts optional evidence
at 01:13.385, the agentic workflow at 01:18.890, reconstruction at 01:37.900,
source trust at 01:49.120, environmental uncertainty at 01:59.278, the human
checkpoint at 02:04.445, the verified briefing at 02:22.353, approval at
02:26.676, club scale at 02:33.396, athlete history at 02:58.919, Competition at
03:26.388, the boat report at 03:37.096, Evaluation at 03:56.708, and the
negative experiment at 04:32.812. Route changes use the cursor as a bridge; the
destination appears only when the corresponding spoken idea begins.

The captioned draft 21 and `.srt` remain preserved as evidence of the removed
caption experiment. They are no longer recommended for submission.

## Final-audio caption synchronization in draft 21

Draft 21 corrects a timing regression introduced when raw ElevenLabs cue times
were used after a 3.8-second brand signature had been added to the assembled
video. Cross-correlation against the final chapter-one recording measured its
actual placement at 3.85 seconds. All twelve chapter-one cues now include that
offset, and the first chapter-two cue is bounded to the 01:03 chapter cut. The
remaining 41 cues were left unchanged because their boundaries already match
the final audio's detected pauses. Frame checks at 00:03.7, 00:04.3, 00:04.6,
01:02.8, and 01:03.1 confirm the empty brand hold, first spoken cue, clean
chapter gap, and chapter-two entry.

## Contextual product navigation in draft 19

Draft 19 adds cursor motion only where the narration changes product path. At
02:34 the club pulse opens Team, Team opens Crew: Tucano, and the lineup opens
Lucas. The same restrained pattern then moves from Lucas to Goal memory, Goal
memory to Competition, the competition list to Tucano's boat report, and the
boat report to Evaluation. Each eased movement reaches its real visible target,
shows a short click pulse, and holds before the destination replaces the page.
No cursor is added during data-reading holds.

## Clean and explicit active navigation in draft 20

Draft 20 removes two capture-only artifacts: the hovered Competition-review
card visible around 02:36 and browser-blue focus outlines around Competition
and Evaluation. The active global destination is now shown with green text, a
soft green surface, and a green underline. Overview and the Sessions subtabs
continue to show their existing active state. The product implementation also
sets `aria-current="page"` on the four global destinations and keeps an
explicit green keyboard-focus outline, so cleaning the video does not remove
accessible focus from the interface.

## Evidence and human-checkpoint reframing in draft 18

Draft 18 removes the remaining chart and target-rate text above `Evidence
selection`; the source-trust chapter now contains only Stroke rate, Distance,
Route, Environment, their selected authorities, and the source-explanation
actions. The human-checkpoint chapter now shows the complete form in one
editorial frame: question, Yes/No answer, all three provenance choices, `Save
attributed answer`, `Keep unknown`, the telemetry boundary, and the coach-
approval boundary. The complete form is assembled from two adjacent states of
the same current interface so the action is visible without shrinking the
entire long session page.

## Explicit negative evidence and accessibility in draft 17

The final learning chapter no longer relies on narration over a general
Evaluation screen. From 04:19, a dedicated `PRODUCT LESSON · REMOVED BEHAVIOR`
card names the incorrect inference that reconstructed distance proved
prescribed-distance completion and shows the TDD boundary correction. It is
followed by `NEGATIVE EXPERIMENT · KEPT`, which names the longitudinal result
`NO DEMONSTRATED QUALITY GAIN`. The card preserves the measured 29.01% cost
reduction while stating that lower cost did not prove better reasoning. This
makes the submission requirement visible and avoids presenting a negative
experiment as a hidden footnote or a win.

Draft 17 also adds 54 English sentence-level caption cues. The `.srt` is kept
as a reusable sidecar and the recommended review file contains open captions,
so accessibility does not depend on the playback portal supporting subtitle
tracks. Captions use no more than two lines, a 42 px type size, and a dark
translucent lower safe-area panel. The local FFmpeg build lacked libass, so the
first subtitle-filter attempt failed. A regression test now requires a
reproducible SVG/alpha-overlay path that uses the same local vector tooling as
the rest of the video.

One cue uses the intended final phrase `one men's double`, while the current
chapter-1 draft audio still says the former crew name. This is deliberately
visible as an acceptance blocker: replace that audio first, then verify the cue
against the regenerated sentence before calling the captions accessible and
final.

## Focused product storytelling in draft 16

Draft 16 replaces the three near-duplicate full-page session frames with
three subject-focused crops. `One authority per claim` now isolates the
metric-level evidence-selection matrix; `Keep missing context visible`
isolates the environmental boundary and its non-causal language; and `Ask the
person who knows` isolates the athlete question, answer, and answer
provenance. The product remains a real current interface capture, but the
editorial camera now shows the evidence being discussed rather than a lightly
scrolled copy of the same page.

The 47.5–54.0 second crew sequence was also rebuilt against the current bird-
named product. A cursor now completes its eased move to Team, holds through a
visible click, then completes the move to `Crew: Tucano - 2x - Men` before the
crew detail opens. The visual no longer waits for a stale `Harbor` label that
does not exist in the current interface. The chapter-1 narration still says
the former crew name and remains explicitly gated on the neutral regeneration
sheet before final acceptance.

The 81.0–97.0 second agentic interlude is newly rendered from the local vector
source instead of reusing the old draft's video frames. The investigation
agent appears first; each complete arrow appears before its destination tools,
verifier, or human-decision block. This removes the residual pre-interlude
frame around 01:21 and prevents arrowheads from being clipped by card
transitions.

## Brand-only opening

Version 10 uses a 3.8-second brand signature before the first narration: symbol,
WAKE name, product category, tagline, and the visual wake. It deliberately does
not introduce evidence sources because the first narrated chapter now performs
that job in synchronization with the voice.

The artwork in `motion-intro/` is original, locally created vector material.
Its quiet ambient bed is synthesized locally from filtered noise and tones;
the opening contains no stock footage, third-party music, or additional model
call. The superseded 7.5-second evidence-convergence
opening remains preserved in version 2 as an editorial comparison.

## Animated first narration

Versions 3–5 extend the motion language through the complete first narration.
The training plan, athlete-owned SpeedCoach file, optional phone route, and
coach context appear in sequence as the voice names them. The next movement
separates file storage and one-shot summarization from the missing questions,
relationships, and decisions. The animation then enters real interface views
for club overview, attention routing, and one men's double context.

The timing preserves approximately the final third of the chapter for the
actual product interface. Labels reinforce the narration instead of repeating
it as a transcript. Source artwork is preserved in `motion-problem/`; it is
original vector material and contains no stock media.

Version 5 shortens each card entrance to approximately 0.4 seconds while
keeping the appearance time aligned with the spoken source. The faster motion
reduces visual drift without crowding the narration.

## Interface interaction motion

Versions 6–10 use a consistent cursor, short click pulse, and restrained scroll
cue only where an action explains the following view. Version 8 replaces the
linear cursor moves with eased short paths, corrects the Attention, crew,
post-regatta-package, and boat-report targets, and removes clicks that did not
clearly explain a state change. Later chapters retain the athlete chronology
and evaluation scrolls without pretending that every camera move is a user
interaction.

The cursor disappears during result-reading holds. These interactions are
editorial simulations over real interface captures; they do not present the
draft as a live agent execution. Original overlays are preserved in
`motion-ui/`.

The cut uses the real animated product walkthrough for session intake,
investigation, the human checkpoint, and approval-gated memory. Version 10
adds an original progressive motion interlude between intake and
reconstruction: one bounded investigation agent chooses among four
deterministic tools, a verifier checks the output, and the athlete/coach retain
the human decision boundary. It does not claim a multi-agent implementation.
The section then returns to the material deviation, metric trust, and
non-causal environmental context before the separate human-checkpoint chapter.

## Narration mapping

The second ElevenLabs variation (`-2.mp3`) was selected whenever it was
provided.

| Chapter | Narration source | Status |
| --- | --- | --- |
| 1. Problem and club attention | `2026-08-31T04_35_20...v3.mp3` | Supplied final ElevenLabs recording; says `messaging app` and describes a simple baseline without naming GPT |
| 2. Session investigation | `2026-08-31T12_13_41...v3.mp3` | Supplied v5 narration in draft 15; source trust is described per metric and session |
| 3. Human checkpoint | `2026-08-30T23_33_04...v3-2.mp3` | ElevenLabs variation 2 |
| 4. Longitudinal memory | `2026-08-30T23_34_51...v3-2.mp3` | ElevenLabs variation 2 |
| 5. Competition Review | `2026-08-30T23_36_08...v3-2.mp3` | ElevenLabs variation 2 |
| 6. Measured evidence | `2026-08-30T23_36_54...v3-2.mp3` | ElevenLabs variation 2 |
| 7. Learning and close | `2026-08-31T02_49_33...v3-2.mp3` | ElevenLabs variation 2 |

The final `04_35_20` chapter-1 recording and the supplied `04_13_42` chapter-2
recording remove the last narration placeholders. Chapter 1 now contains the
complete `messaging app` sentence and describes the baseline without naming a
model. Chapter 2 was
74.998 seconds as generated; its long silent gaps were tightened and the result
was accelerated by 8% to 60.435 seconds so the complete five-minute story fits.
No spoken word or claim was removed.

Draft 15 replaces the superseded chapter-2 wording. It now says that WAKE
compares signal coverage and consistency and selects the most reliable
stroke-rate source for that session. In the demonstrated session this is
SpeedCoach; in another it could be mobile. The video stream is identical to
draft 14; only the AAC narration track was rebuilt.

Version 12 removes the repository URL from the closing card because the source
code is delivered separately. It preserves the duration, narration, and all
other closing-card content. The chapter-1 recording still says the former
crew name; regenerate the revised neutral sentence in
`VOICEOVER_ELEVENLABS_V4_REGENERATE.md` before accepting the final cut.

## Owner review order

1. Review uncaptioned version 23 and confirm the current Overview → Team → Tucano
   → Lucas → Goal memory → Competition → boat report → Evaluation route,
   focused session close-ups, progressive agentic interlude, natural cursor
   targets, and scroll pacing.
2. Confirm that the new chapter-2 narration describes SPM trust per session and
   ends on preserved uncertainty before chapter 3 opens the human checkpoint.
3. Check pronunciation, joins, audio level, and whether any chapter feels too
   long.
4. Confirm that no screen changes subject before the matching spoken sentence
   finishes.
5. Complete the targeted interface QA before accepting the video.
6. Confirm the corrected `01:16` frame, absent stale frame at `01:21`, complete
   agentic arrows around `01:22`, green live-enabled status, 4:3 product
   captures, absent scrollbars, and contextual rail at normal playback size.
7. Confirm that `REMOVED BEHAVIOR` and `NEGATIVE EXPERIMENT · KEPT` are
   readable during the final learning chapter.
8. Export the accepted cut as `wake-final-submission.mp4`, verify that it is no
   longer than five minutes, and run the strict readiness gate.

## Verification command

```bash
ffprobe -v error \
  -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of default=noprint_wrappers=1 \
  submission/video/wake-final-submission-draft-v23.mp4
```
