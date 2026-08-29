# Case 002: Wind Shift with a Real Plan Deviation

This fully synthetic case is derived from the structure of an approved coach prescription. It does not represent a real athlete, outing, location, date, or weather observation.

The plan prescribes six 1,000 m work intervals: the first three at 19-21 SPM with a resistance band, the final three at 22-24 SPM without it, and 3-5 minutes of active recovery.

The generated session contains two simultaneous explanations that the workflow must keep separate:

- wind changes from a light tailwind to a strong headwind during work interval four, reducing later speed;
- work interval five is a genuine execution deviation at about 20 SPM instead of 22-24 SPM.

The SpeedCoach-like source contains usable SPM. The mobile source follows the same route with a 37-second clock offset and a small distance bias, but its SPM channel is stuck at zero. The files cannot confirm resistance-band use, visible technique, or crew synchronization.

Only `input/` belongs in model context. `ground-truth.json` and `fixture-manifest.json` are evaluator artifacts.

Regenerate and verify from the repository root:

```bash
python3 scripts/generate_synthetic_cases.py
python3 scripts/verify_synthetic_case.py
```
