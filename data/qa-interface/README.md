# WAKE owner QA upload pack

This directory contains only public, derived-synthetic evidence prepared for
interface QA. It includes no evaluator ground truth, private GPS, real athlete
identity, credential, or hidden expected answer.

## Full replay bundle

Open `full-replay-bundle/` in the file chooser and map the files in this order:

1. Training plan — `plan.json`
2. SpeedCoach recording — `speedcoach.csv`
3. Mobile recording — `mobile.csv`
4. Environmental timeline — `environment.json`
5. Session context — `context.json`

In replay mode, all five byte-identical sources should enable **Validate and
open replay** and reopen the committed verified investigation at US$0.00.

## Minimum evidence preparation

From the same folder, select only `plan.json` and `speedcoach.csv`. The
interface should enable **Validate and prepare · No agent call**, save a local
prepared session, and keep mobile, environment, and human context visibly
missing. It must not inherit the answer from the complete replay bundle.

See `docs/OWNER_QA_GUIDE.md` for the complete sequential checklist.

The live QA section deliberately runs three separate investigation starts. It
requires an explicit US$0.60 total operational authorization before execution;
the authorization is a start gate, not a provider billing cap.
