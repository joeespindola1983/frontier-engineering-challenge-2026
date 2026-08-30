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

This is a reusable product walkthrough segment, not yet the complete required
five-minute submission video. The final cut must also introduce the current
coach workflow and simple baseline, show the measured baseline-versus-WAKE
comparison, summarize the Improvement Changelog, and highlight the most
impactful correction plus one removed experiment.

The generation-ready English narration for the final product-first cut is
split into seven Eleven v3 inputs in
[`VOICEOVER_ELEVENLABS_V3.md`](VOICEOVER_ELEVENLABS_V3.md). The sheet contains
only output filenames, target timing, and API-ready text with inline audio tags.
