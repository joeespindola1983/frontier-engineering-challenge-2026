# WAKE captioned product walkthrough

`wake-product-walkthrough-captioned.mp4` is a 64-second, 1920 x 1080,
H.264 product-flow cut assembled from a real browser rehearsal on 29 August
2026. It has English on-screen captions and no narration or music.

The rehearsal used the five committed public synthetic inputs from
`data/fixtures/case-002-wind-shift-plan-deviation/input/`:

- `plan.json`
- `speedcoach.csv`
- `mobile.csv`
- `environment.json`
- `context.json`

The captured flow shows athlete-role contribution, independent source
authority, upload selection, explicit live-cost authorization, investigation,
plan-versus-performed review, non-causal environmental context, a routed
athlete question, an athlete answer recorded by a coach, a verified briefing,
and approval-gated memory.

## Live attempt and replay boundary

One explicitly authorized live execution was attempted with the US$0.20
operational start gate. The browser remained in `Investigating...` for about
90 seconds and then received `Agent runtime unavailable.` No result,
trajectory, token usage, approximate cost, or cost-ledger entry was produced,
so provider spend for the attempt is unknown and is not reported as a measured
cost. The service was then restarted in no-cost replay mode and the exact
byte-identical committed public bundle completed the captured product flow.
The video labels that transition rather than presenting the failed live call
as a success.

## Verification

```bash
ffprobe -v error \
  -show_entries format=duration,size:stream=codec_name,width,height,r_frame_rate \
  -of default=noprint_wrappers=1 \
  submission/video/wake-product-walkthrough-captioned.mp4
```

Expected essentials:

```text
codec_name=h264
width=1920
height=1080
r_frame_rate=30/1
duration=64.000000
```

This is a reusable product walkthrough segment, not the complete required
five-minute submission video. The final cut must also introduce the current
coach workflow and simple baseline, show the measured baseline-versus-WAKE
comparison, summarize the Improvement Changelog, and highlight the most
impactful correction plus one removed experiment.

`wake-final-submission-draft.mp4` is the first 04:42 animated assembly using the
owner-selected second ElevenLabs variations, the real walkthrough, fresh club
interface captures, and motion treatment. It remains a review artifact because
the supplied audio set omitted the `wake-vo-02-session-review` ElevenLabs file;
that chapter currently uses a local placeholder. Exact review notes and audio
mapping are in [`DRAFT_REVIEW_20260831.md`](DRAFT_REVIEW_20260831.md).

`wake-final-submission-draft-v2.mp4` is the preserved 04:49 opening comparison. It
preserves the full first assembly and adds a 7.5-second motion-design opening in
which the training plan, SpeedCoach evidence, and human context converge into
WAKE memory. The original vector layers are in [`motion-intro/`](motion-intro/).
The animation and its locally synthesized ambient bed use no third-party stock
media and required no additional model call. Version 1 remains available for a
direct editorial comparison.

`wake-final-submission-draft-v3.mp4` is a preserved 04:49 motion comparison.
It keeps the version 2 opening and replaces the static first chapter with a
narration-synchronized motion sequence. Evidence sources appear as they are
named; file storage and one-shot summarization are separated from accumulated
club memory; the sequence then moves into real Overview, Attention, and crew
screens. Original vector layers are preserved in
[`motion-problem/`](motion-problem/). Versions 1 and 2 remain untouched for
editorial comparison.

`wake-final-submission-draft-v5.mp4` is the preserved 04:46 fast-card comparison.
cut. It replaces the repeated evidence-convergence opening with a 4.5-second
brand-only signature and accelerates first-chapter card entrances to roughly
0.4 seconds while preserving their narration cues. The evidence story remains
inside the first narrated chapter, where it belongs. Versions 1–4 remain
untouched for comparison.

`wake-final-submission-draft-v6.mp4` is the preserved 04:46 interaction
comparison. It keeps the brand-only opening and fast card timing, then adds restrained
cursor, click, and scroll motion where it reveals otherwise cropped interface
context or explains a state change. The interaction overlays are original
assets in [`motion-ui/`](motion-ui/) and are explicitly editorial simulations,
not a claim that the draft contains a live agent run. Versions 1–5 remain
untouched for comparison.

`wake-final-submission-draft-v7.mp4` is a preserved 04:43 audio-and-cursor
intermediate. It first incorporated the supplied chapter-2 ElevenLabs audio and
more natural cursor targets, but its session visuals advanced into the human
checkpoint before the narration reached that subject.

`wake-final-submission-draft-v8.mp4` is the preserved 04:43 review
cut. It keeps the corrected eased cursor paths, replaces the chapter-2
placeholder with the supplied 41.953-second ElevenLabs recording, and remaps
that section to seven short narration-aligned movements. The visual story now
ends on non-causal environmental context; the human checkpoint begins only in
the following chapter. The old spoken `WhatsApp` sentence has been removed and
the visible source card now says `messaging apps`. One final chapter-1
ElevenLabs regeneration is still needed to restore that complete spoken
sentence in the same voice.

`wake-final-submission-draft-v9.mp4` is the preserved 04:59 first complete-audio
assembly. It uses both supplied `04_13` ElevenLabs replacements and introduces
the truthful single-agent workflow animation. Its 299.181-second duration left
less than one second of submission margin.

`wake-final-submission-draft-v10.mp4` is the preserved 04:58 review
cut. It retains every spoken claim from version 9, tightens only long chapter-2
silences, applies a subtle 8% speed increase to that narration, and shortens the
brand signature to 3.8 seconds. The original progressive motion interlude shows
one investigation agent, four deterministic evidence tools, a verifier, and
the athlete/coach decision boundary without falsely describing WAKE as a
multi-agent system. At 298.547 seconds, it remains under the five-minute limit.

`wake-final-submission-draft-v11.mp4` is the preserved 04:58 audio review
cut. It changes only chapter 1 from version 10, using the final supplied
`04_35_20` ElevenLabs recording. The narration now says `messaging app` and
describes the simple baseline without naming or spelling out GPT. All later
chapters, including the single-agent workflow animation, remain unchanged. At
298.469 seconds, it remains under the five-minute limit.

`wake-final-submission-draft-v13.mp4` is the preserved 04:58 visual
review cut. It preserves draft 12's accepted narration, brand motion,
single-agent interlude, learning sequence, and closing. Current 1440 × 900
browser captures replace the stale product chapters: corrected session intake,
session reconstruction, attributed human checkpoint, approval-gated memory,
Brazilian-bird crew labels, athlete history, Competition Review, and official
evaluation. Product footage occupies 82% of the frame and the former long
right-hand explanation is reduced to an 18% title rail. The `01:16` responsive
capture defect is no longer present. At 298.467 seconds and approximately
11.3 MB, it remains under the five-minute limit. It is still a review draft
until owner QA accepts the edit.

`wake-final-submission-draft-v14.mp4` is the preserved 04:58 visual review
cut. It recaptures current product screens through an isolated live-enabled
runtime in a 1200 × 900, 4:3 browser composition. No paid execution was started
for the recording itself. The green status indicator therefore means the
bounded live runtime was available, while the displayed review and evaluation
remain saved verified evidence. Scrollbars are hidden in the capture-only
build, deeper page context stays visible, the product occupies 76% of the
frame, and a 24% narrative rail restores concise explanation. The evaluation
rail identifies the stronger evidence of agentic work: ten controlled cases,
40 tool calls, ten verified trajectories, and approximately US$1.14 for the
complete official comparison. At 298.448 seconds and approximately 12.4 MiB,
the draft remains under five minutes.

`wake-final-submission-draft-v15.mp4` is the preserved 04:58 audio review
cut. It preserves draft 14's video stream byte-for-byte and replaces only
chapter 2 with the owner-supplied v5 narration. The corrected copy explains
that WAKE compares SPM coverage and consistency and selects the source per
metric and session; mobile can be selected in another session. The 66.351-
second recording is fitted to the existing 66.000-second chapter with a 0.53%
tempo adjustment. The complete video is 298.444 seconds and approximately
12.3 MiB. The separate, already documented chapter-1 crew-name correction
still remains before final acceptance.

`wake-final-submission-draft-v16.mp4` is the preserved 04:58 review
cut. It preserves draft 15's accepted narration while rebuilding the current
Team → `Crew: Tucano - 2x - Men` navigation with completed eased cursor moves
and visible click holds. The agentic interlude is rendered again from the
local SVG as a progressive sequence: every complete connector appears before
its destination block, eliminating the stale frame near 01:21 and the clipped
arrows near 01:22. The three session principles now use distinct close-ups of
metric-level source trust, the environmental non-causality boundary, and the
athlete answer with provenance instead of near-identical full-page captures.
It is 298.400 seconds, 1920 × 1080 at 30 fps, and approximately 12.0 MiB. The
chapter-1 recording still says the former crew name; the neutral line in
`VOICEOVER_ELEVENLABS_V4_REGENERATE.md` remains the final audio gate.

`wake-final-submission-draft-v17-captioned.mp4` is the preserved
04:58 accessibility and requirement-review cut. The learning chapter now
visibly distinguishes a removed behavior from a preserved negative experiment.
The first card shows the reconstructed-distance overclaim and its TDD evidence-
boundary correction. The second names the longitudinal result `NO DEMONSTRATED
QUALITY GAIN`, preserves the 29.01% cost reduction, and states that efficiency
did not prove better reasoning. Fifty-four English cues are burned into the
recommended file and are also available as
`wake-final-submission-draft-v17.en.srt`; the equivalent uncaptioned visual cut
is `wake-final-submission-draft-v17.mp4`. The captioned file is 298.384 seconds,
1920 × 1080 at 30 fps, and approximately 15.6 MiB. It remains a draft until the
neutral chapter-1 crew line is supplied and the matching cue is owner-checked.
Until then, the cue intentionally contains the final neutral phrase while the
draft audio still contains the former crew name; version 17 must not be treated
as the accepted accessibility master.

`wake-final-submission-draft-v18-captioned.mp4` is the preserved evidence-crop
review cut. It preserves draft 17's explicit removed-behavior and
negative-experiment cards plus all 54 open captions. The source-trust frame is
now cropped to the evidence-selection matrix only, with no chart or target-rate
text above it. The human-checkpoint frame shows the complete question, answer,
answer provenance, `Save attributed answer`, `Keep unknown`, and approval
boundary in one view. The equivalent uncaptioned cut and sidecar are
`wake-final-submission-draft-v18.mp4` and
`wake-final-submission-draft-v18.en.srt`. The captioned file is 298.256 seconds,
1920 × 1080 at 30 fps, and approximately 15.6 MiB. The neutral chapter-1 audio
replacement remains the final acceptance gate.

`wake-final-submission-draft-v19-captioned.mp4` is the preserved contextual-
navigation cut. It preserves draft 18's evidence crops, complete human
checkpoint, explicit learning cards, and 54 open captions. From 02:34 onward,
short eased cursor actions now make the actual product route visible:
Overview → Team → Crew: Tucano → Lucas → Goal memory → Competition → one boat
report → Evaluation. Every click completes before its destination appears, and
the cursor remains absent while the audience is meant to read results. The
equivalent uncaptioned cut and sidecar are
`wake-final-submission-draft-v19.mp4` and
`wake-final-submission-draft-v19.en.srt`. The captioned file is 298.256 seconds,
1920 × 1080 at 30 fps, and approximately 15.9 MiB. The neutral chapter-1 audio
replacement remains the final acceptance gate.

`wake-final-submission-draft-v20-captioned.mp4` is the preserved clean-
navigation review cut. It keeps draft 19's complete product path while removing the
accidental hovered Competition-review card at 02:36 and the browser-blue focus
outlines on Competition and Evaluation. Those destinations now use one clear
active-navigation treatment: green text, soft green background, and a green
underline. The equivalent uncaptioned cut and sidecar are
`wake-final-submission-draft-v20.mp4` and
`wake-final-submission-draft-v20.en.srt`. The captioned file is 298.128 seconds,
1920 × 1080 at 30 fps, and approximately 15.9 MiB. The neutral chapter-1 audio
replacement remains the final acceptance gate.

`wake-final-submission-draft-v21-captioned.mp4` is the preserved caption-timing
experiment. It preserves draft 20's clean navigation and corrects the
open-caption timing against the final assembled audio. The first 3.8 seconds
are now brand-only; chapter-one cues include the measured 3.85-second audio
placement, and the first chapter-two cue cannot begin before 01:03. The other
41 cues retain their existing final-audio pause alignment. The equivalent
uncaptioned cut and sidecar are `wake-final-submission-draft-v21.mp4` and
`wake-final-submission-draft-v21.en.srt`. The captioned file is 298.128 seconds,
1920 × 1080 at 30 fps, and approximately 15.7 MiB. The neutral chapter-1 audio
replacement remains the final acceptance gate.

`wake-final-submission-draft-v22.mp4` is the preserved first uncaptioned
timing pass. Owner QA removed open subtitles, and the product timeline was rebuilt
against the final narration cue boundaries. Each visual subject now begins with
the sentence that introduces it: optional evidence at 01:13, the bounded agent
at 01:18, source trust at 01:49, environmental uncertainty at 01:59, the human
checkpoint at 02:04, approval at 02:26, Competition at 03:26, the boat report
at 03:37, Evaluation at 03:56, and the negative experiment at 04:32. Cursor
travel may begin during the preceding idea, but the destination does not replace
the page until its matching spoken idea begins. The file is 298.128 seconds,
1920 x 1080 at 30 fps, and 13,150,782 bytes. Draft 21 and its sidecar remain
preserved as an experiment, not as the recommended delivery.

`wake-final-submission-draft-v23.mp4` is the preserved source of the accepted
04:59 cut. It rebuilds the complete audio track from the seven owner-supplied chapter
recordings instead of inheriting the faulty chapter-two splice. Chapter two now
shortens pauses only, ends before the original human-checkpoint recording, and
no longer overwrites its opening. The agentic workflow remains visible through
the verifier, reconstruction begins at 01:47, Source Trust remains visible
through the SpeedCoach sentence, and Environment begins with the wind sentence
at 02:00. All click pulses were removed while cursor travel remains. The final
image outlasts the audio by approximately 0.2 seconds. The file is 299.232
seconds, 1920 x 1080 at 30 fps, and 13,535,323 bytes.

`wake-final-submission.mp4` is the owner-approved delivery master, promoted
byte-for-byte from draft 23 on 2026-08-31. Its SHA-256 is
`1acf067120a5e4ed94baae685824ceeb97b0b86370f4cde66d27fa67bebd48c4`.

The complete generation-ready English narration for the final product-first cut is
split into seven Eleven v3 inputs in
[`VOICEOVER_ELEVENLABS_V3.md`](VOICEOVER_ELEVENLABS_V3.md). The sheet contains
only output filenames, target timing, and API-ready text with inline audio tags.
The strict submission readiness gate requires `wake-final-submission.mp4` and
now reports the final media deliverable as present.
