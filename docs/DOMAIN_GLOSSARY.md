# Rowing Domain Glossary

**Version:** 0.1

This glossary records domain terms confirmed by the project owner as an experienced rower. It separates confirmed mappings from details that still require a coach or authoritative technical reference.

## Confirmed mappings

### Voga

- **Status:** human-confirmed on 2026-08-29.
- **Meaning in the supplied training plans:** target stroke rate.
- **Canonical WAKE metric:** `stroke_rate_spm`.
- **Example:** `voga 23` becomes a target of 23 strokes per minute, subject to any explicit range or progression in the prescription.

### B0-B7 and E1-E7

- **Status:** human-confirmed on 2026-08-29 as standardized rowing training zones rather than coach-specific labels.
- **Canonical representation:** preserve the zone code and mark `zone_system` as `STANDARD_ROWING_ZONES`.
- **Current boundary:** exact effort, physiological, heart-rate, lactate, or power thresholds are not yet encoded. WAKE must not invent those thresholds.

## Evidence policy

- A plan can establish that a zone, stroke rate, recovery, or equipment instruction was prescribed.
- Telemetry may establish observed SPM, distance, time, route, or supported environment metrics.
- A prescribed resistance band or other equipment is not proof that it was used; human confirmation or an appropriate sensor is required.
- Ordinary GPS and SPM data cannot establish visible technique or crew synchronization.

## Pending glossary work

- Add authoritative definitions and boundaries for each B and E zone.
- Confirm whether zone thresholds vary by athlete, boat class, test protocol, or club implementation.
- Define `lastro/lata`, race-start notation, and other equipment shorthand found in coach plans.
