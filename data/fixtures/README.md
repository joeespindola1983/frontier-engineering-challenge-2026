# Public Evaluation Fixtures

Fixtures in this directory are safe-to-publish transformations of approved evidence or fully synthetic cases. They exist to make WAKE's baseline, agent behavior, and graders reproducible without exposing athlete identities, private routes, device identifiers, or real training dates.

Each case separates:

- `input/`: evidence available to the workflow;
- `ground-truth.json`: evaluator-only facts and expected abstentions;
- a versioned manifest: hashes and transformation metadata for integrity checks;
- `README.md`: the case's purpose and limitations.

Run every public fixture and compact-input verifier from the repository root:

```bash
python3 scripts/verify_all.py
```

Private source manifests belong under the ignored `private-data/` directory. Never commit those manifests or the original exports.

Cases 003-010 are deterministic, entirely synthetic diagnostic fixtures. Their
inputs and evaluator-only ground truth are committed and verified, but they stay
`PLANNED` in the scored registry until the expanded grader and required model
outputs are also committed. Fixture readiness is not a measured workflow result.
