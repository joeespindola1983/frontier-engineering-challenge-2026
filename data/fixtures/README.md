# Public Evaluation Fixtures

Fixtures in this directory are safe-to-publish transformations of approved evidence or fully synthetic cases. They exist to make WAKE's baseline, agent behavior, and graders reproducible without exposing athlete identities, private routes, device identifiers, or real training dates.

Each case separates:

- `input/`: evidence available to the workflow;
- `ground-truth.json`: evaluator-only facts and expected abstentions;
- `source-manifest.json`: hashes and transformation metadata for integrity checks;
- `README.md`: the case's purpose and limitations.

Run the current fixture verifier from the repository root:

```bash
python3 scripts/verify_hero_fixture.py
```

Private source manifests belong under the ignored `private-data/` directory. Never commit those manifests or the original exports.
