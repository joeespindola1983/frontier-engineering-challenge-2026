# Demo-club two-week batch

Forty independent real-informed synthetic activity records. Water sessions carry plan, SpeedCoach-shaped telemetry, and context when available; two indoor alternatives carry synthetic Concept2 PM5 transcription-format records. Every source is hashed per session.

The Concept2 adapter distinguishes fixed-distance, fixed-time, and interval screen semantics. Automatic photo OCR and native ErgData ingestion are not implemented or implied.

The batch is designed for mass submission with per-session isolation. It does not place multiple sessions in one model prompt. Agent execution is preserved only for the two separately authorized candidates; longitudinal synthesis has not run.

Regenerate and verify without a model call:

```bash
uv run python scripts/generate_demo_club_batch.py
uv run python scripts/verify_demo_club_batch.py
```
