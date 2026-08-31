# Owner live QA runs — 2026-08-30

These three bounded executions validate the live product path after the
zero-cost replay QA. They are supporting interface evidence and do not change
the frozen ten-case score, grader, denominator, or official comparison.

All inputs were drawn from the public synthetic owner QA bundle. Every run used
`gpt-5.6-terra`, the v2 tool loop, `store: false`, and the same deterministic
verification boundary. Outputs and observable trajectories retain no private
chain-of-thought.

| QA | Evidence scope | Tokens | Runtime | Approximate cost | Result |
| --- | --- | ---: | ---: | ---: | --- |
| QA-14 | Plan + SpeedCoach | 34,675 | 38.793 s | US$0.117390 | Verified |
| QA-15 | Five supplied sources | 34,927 | 26.056 s | US$0.099324 | Verified |
| QA-16 | Plan + SpeedCoach + historical weather | 20,960 | 21.241 s | US$0.067120 | Verified |
| **Total** | **Three separately authorized starts** | **90,562** | **86.090 s** | **US$0.283834** | **3/3 verified** |

The QA-16 saved output correctly abstained from boat-relative wind because the
then-current compact summary did not include a route heading. The subsequent
deterministic product fix derives a representative heading only from a
directionally consistent GPS track and otherwise continues to abstain. The paid
output remains unchanged as historical evidence.

The byte-level paths and SHA-256 hashes are frozen in
`owner-live-qa-20260830.run-manifest.json`.
