# Case 001: Misaligned Men's Double Scull

This is WAKE's first difficult evaluation case. Three devices recorded the same men's double scull (`2x`) session, but their clocks differ by almost one hour, their summaries disagree, and both mobile exports contain incorrect boat defaults. Raw mobile SPM is absent, Android gyroscope values are zero, and no planned workout or technique observation is available.

The case tests whether a workflow can:

1. match recordings using route geometry and duration instead of exact start time;
2. distinguish raw telemetry from derived summaries;
3. select evidence per metric rather than trusting one device globally;
4. preserve a human correction to boat and crew context;
5. ask for missing information and abstain from unsupported conclusions.

## Privacy transformation

- The real route was translated to a synthetic origin while preserving local geometry in meters.
- Every timestamp received the same deterministic date shift, preserving device clock differences.
- Workout IDs, device names, serial numbers, and models were replaced.
- High-frequency mobile sensor rows were reduced to the first sample at each distinct GPS position plus the final row. The retained rows support route matching, distance checks, sensor-availability checks, and timing analysis; they are not suitable for reconstructing stroke motion.
- Athlete identities, real date, real location, weather, and the physical boat are not included.

The deliberately incorrect `SINGLE_SCULL` and `OC1` values are retained as evaluation evidence. Evaluator-only truth lives in `ground-truth.json`; a real agent run should receive only the `input/` directory.

## Verify

From the repository root:

```bash
python3 scripts/verify_hero_fixture.py
```

The verifier checks hashes, privacy tokens, source metrics, clock offsets, route overlap, missing mobile SPM, and the confirmed `2x` context.
