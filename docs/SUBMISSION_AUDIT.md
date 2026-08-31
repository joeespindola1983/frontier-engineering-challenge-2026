# WAKE submission compliance audit

**Audit date:** 2026-08-31

**Working brief:** [`SUBMISSION_REQUIREMENTS.md`](SUBMISSION_REQUIREMENTS.md),
which summarizes the organizer brief supplied to the team. The final portal and
source brief must be checked once more before upload in case the organizer has
published a newer requirement.

**Current gate:** `READY`. The code, evaluation, public evidence, reproduction
path, documentation package, and accepted final video pass their respective
gates. The owner approved draft 23 on 2026-08-31; it was promoted byte-for-byte
to `submission/video/wake-final-submission.mp4`. The H.264/AAC artifact is
299.232 seconds, 1920 x 1080 at 30 fps, 13,535,323 bytes, and has SHA-256
`1acf067120a5e4ed94baae685824ceeb97b0b86370f4cde66d27fa67bebd48c4`.

**Latest full verification:** 253 Python tests, nine public artifact verifiers,
113 web tests, lint, and the production build passed on 2026-08-31. A fresh
source-ZIP extraction also installed locked dependencies and passed the same
reproduction with Python 3.14.6, uv 0.5.9, Node.js 24.19.0, and npm 11.12.1.
The project minimum remains
Python 3.11 and Node.js 22.13. The first audit attempt correctly stopped on the
shell's Node.js 20.19.4; repeating with the declared Node.js 24.19.0 runtime
passed, confirming that the version gate is active rather than silently
accepting an unsupported environment.

**Source-package audit:** `scripts/build_submission_zip.py` produces 684 public
source and evidence files at approximately 7.29 MiB compressed. The archive
excludes every MP4, draft caption, installed dependency, build output, private
state, credential, `.env`, and temporary render directory; the empty
`.env.example` and both final PDFs are intentionally included. The final
SHA-256 is generated beside the ZIP after the last documentation change rather
than embedded in the archive whose bytes it describes.

**PDF companion package:** the original 10-page organizer brief created on
2026-08-27 names four deliverables but does not define two PDF fields. At the
owner's direction, the repository now includes a five-page clean-environment
setup/reproduction PDF and an eleven-page visual solution report under
`output/pdf/`. Both were generated from a tested builder, rendered page by
page, and visually inspected. Portal labels and upload limits still require a
final check because they are absent from the supplied brief.

Run the machine-readable repository audit at any time:

```bash
uv run python scripts/verify_submission_readiness.py
```

The accepted final video is saved as
`submission/video/wake-final-submission.mp4`; run the strict gate with:

```bash
uv run python scripts/verify_submission_readiness.py --require-final-video
```

## Deliverable compliance

| Requirement | Submitted evidence | Status |
| --- | --- | --- |
| Complete solution code | Python runtime, deterministic tools, React/Vinext interface, locked Python and npm dependencies | READY |
| Agent instructions | `prompts/wake-agent-v2.md`, output schemas, tool loop, verifier, cost gate | READY |
| Reasonable simple baseline | `prompts/baseline-v1.md`, `scripts/run_baseline.py`, preserved direct-call outputs | READY |
| Same cases for baseline and WAKE | Registry v2 and official 10-case manifests under `evaluation/runs/expanded-evaluation-v2/official-20260830/` | READY |
| Primary metric defined before optimization | `docs/EVALUATION_SPEC.md` and grader v1.2; macro score over frozen rubric | READY |
| At least ten cases | Ten implemented official cases, including one anonymized real difficult case and nine deterministic synthetic cases | READY |
| Complete comparison | Baseline 49.00/100; WAKE 83.76/100; +34.76 points; every case and dimension retained | READY |
| Unfavorable evidence retained | Environmental interpretation regression 80% to 76%; weakest real case 53.71; neutral longitudinal pilot | READY |
| Cost reported | Official comparison, longitudinal pilot, combined-club memory, direct baseline, and owner live QA all retain observed usage and cost | READY |
| Human time reported where relevant | No measured human-time saving is claimed; time-saving remains a product hypothesis | COMPLIANT LIMITATION |
| Improvement Changelog | Iterations, failures, evidence, decisions, and removed ideas in `IMPROVEMENT_CHANGELOG.md` | READY |
| Main failure and hot take | Unsupported reconstructed-distance claim, regression test, corrected evidence boundary, and final lesson | READY |
| Removed/negative experiment | Neutral longitudinal comparison preserved as `NO_DEMONSTRATED_QUALITY_GAIN` | READY |
| Clean-environment reproduction | Exact versions, data, install, baseline, solution, evaluation, output, runtime, and cost in `docs/REPRODUCTION_GUIDE.md` | READY |
| Judge access without a key | Replay, saved outputs, regrading, and production build cost US$0.00 | READY |
| Representative trajectories | Ten official bounded-agent trajectories with instructions hash, tool calls/results, retries, verification, runtime, tokens, and cost; plus one deterministic end-to-end replay trace with human answer and coach approval | READY |
| Every agent represented | The submission uses one bounded orchestrating agent; all ten official executions have trajectories. The direct baseline is preserved separately and is not presented as an agent | READY |
| Human checkpoint | `evaluation/trajectories/representative-product-replay-v1.json` links the official tool trace to a synthetic human answer, provenance, briefing verification, and coach memory approval | READY |
| Five-minute video | Owner-approved draft 23 was promoted byte-for-byte; 04:59.232, H.264/AAC, 1920 x 1080, full decode checked | READY |

## Rubric coverage

| Rubric area | WAKE evidence | Residual risk |
| --- | --- | --- |
| Problem and User Value — 15 | README, product brief, club-scale 102-activity workflow, coach/athlete roles, Competition Review, accepted product-first video | Do not overstate measured coach-time or performance gains. |
| Agent Solution and Engineering — 30 | Single bounded agent, four read-only tools, deterministic telemetry processing, metric-level trust, strict schema, verifier, cost authorization, approval-gated memory | Do not imply multi-agent sophistication or production durability. |
| End-to-End Quality — 20 | Five-source intake, optional evidence, investigation, human checkpoint, briefing, memory, crews, athletes, PM5, longitudinal package, competition, owner-approved demo | Production authentication and durable storage remain explicitly out of scope. |
| Measured Improvement — 15 | Frozen 10-case WAKE-versus-baseline comparison and complete dimension/case reports | Keep the environmental regression and weakest real case visible. |
| Reproducibility — 15 | Safe no-key script, lockfiles, public fixtures, saved artifacts, exact expected output, deterministic source ZIP | Re-run from the final ZIP and record its final digest. |
| Hot Take / Insights — 5 | Changelog and video show why reconstructed data cannot prove prescribed distance and why extra agent calls do not guarantee better longitudinal reasoning | Keep the negative result visible in the submitted cut. |

## Ground-rule compliance

| Ground rule | Evidence | Status |
| --- | --- | --- |
| Pre-existing work disclosed | `docs/PREEXISTING_WORK.md` separates the earlier mobile recorder, approved exports, supplied interface prototype, coach plans, PM5 images, and competition references | READY WITH RESIDUAL NOTE |
| Licenses and service terms | `docs/THIRD_PARTY_AND_DATA_RIGHTS.md`, lockfiles, OpenAI server-side key boundary, weather consent and data minimization | READY |
| Consequential actions require a human | Questions record provenance; coach approval is required before club memory changes; no automatic crew selection or prescription | READY |
| Qualified human remains responsible | README, product contract, prompts, and interface boundaries say WAKE does not replace a coach | READY |
| Legal/ethical use and privacy | Public evidence is synthetic or minimized/anonymized; raw GPS, identities, credentials, official named sheets, and health data are excluded | READY |
| Credentials excluded | `.env` and private paths are ignored; `.env.example` contains no key; readiness audit rejects tracked `.env` or `private-data/` | READY |
| Claims linked to evidence | README, evaluation reports, manifests, trajectories, changelog, and this matrix use stable repository paths | READY |

## Claims WAKE may make

- On the ten frozen cases, the bounded WAKE workflow scored 83.76/100 versus
  49.00/100 for the direct-call baseline.
- The official WAKE runs added US$0.283344 beyond the baseline for that fixed
  comparison.
- The workflow preserves claim-level evidence, metric-level source trust,
  uncertainty, verification, and human approval more reliably on the submitted
  evaluation.
- Saved reports and the full judge replay reopen for US$0.00.
- The second public package demonstrates deterministic longitudinal comparison
  routes over 102 fictional activities.

## Claims WAKE must not make

- superiority over a qualified human coach;
- broad generalization from ten cases;
- improved race results, fitness, health, technique, strength, or physiology;
- a measured reduction in coach time;
- causal effect from wind, a lineup, or a training session;
- production-grade authentication, encryption, tenancy, billing control, or
  durable cloud storage;
- real athlete or club outcomes from the real-informed synthetic dataset.

## Manual closeout before upload

1. Confirm that the portal accepts the prepared environment/reproduction PDF
   and detailed solution PDF, and verify its exact filename, page, and size
   limits. The supplied brief does not define those portal fields.
2. Confirm the final portal's actual upload-size rule. The tested deterministic
   ZIP contains 684 files at approximately 7.29 MiB and is accompanied by a
   SHA-256 file; the
   local builder enforces a conservative 50 MiB source-only cap; that cap is
   not stated in the supplied organizer brief.
3. Inspect `git status`, review the complete diff, commit, push, and verify the
   repository from a clean clone.
4. Recheck the organizer portal/source brief for filename, link, visibility,
   deadline, or upload-field changes not present in the supplied local brief.
5. Decide whether to add an explicit project source-code license. The supplied
   hackathon brief does not require one, and no license is inferred here.

## Residual disclosures

- The exact repository/snapshot of the pre-competition mobile application is
  not included. No application source was copied; only approved export formats
  and minimized evidence were reused. Keep that claim narrow.
- Local state is Git-ignored and user-restricted but is not encrypted,
  authenticated, backed up, multi-tenant, or a production database.
- The operational authorization is a start gate, not a provider billing cap.
- The existing 64-second captioned walkthrough is supporting footage, not the
  required final submission video.
