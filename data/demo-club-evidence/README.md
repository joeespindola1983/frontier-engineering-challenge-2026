# Demo-club evidence bundles

Two complete real-informed synthetic plan + SpeedCoach + context bundles for the numeric candidates selected by the zero-cost club-period screen. They are public fixtures, not real athlete sessions. `agent_executed` remains false until an explicit paid run is preserved.

- `club-bridge-mixed-20260820-spm` reconstructs two planned 4 km work intervals and exposes only `work-02` below the prescribed 20 SPM.
- `club-atlas-men-20260828-recovery` reconstructs four planned 2 km work intervals and exposes only `recovery-02` above the allowed recovery duration.

Regenerate and verify them without a model call:

```bash
uv run python scripts/generate_demo_club_evidence.py
uv run python scripts/verify_demo_club_evidence.py
```

The verifier checks manifest hashes, text privacy invariants, the training-plan schema, and exact deterministic v2 reconstruction. Passing preflight proves fixture and tool behavior; it does not prove agent quality or a longitudinal coaching conclusion.
