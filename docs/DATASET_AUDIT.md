# Private Dataset Audit

**Audit date:** 2026-08-29

**Scope:** read-only inventory of the pre-existing rowing export folder supplied by the project owner

**Privacy:** this document omits private paths, coordinates, device identifiers, workout identifiers, and real session dates

## Inventory

| Evidence type | Observed | Useful qualification |
| --- | ---: | --- |
| SpeedCoach CSV files | 18 | 17 unique by content |
| Mobile telemetry files | 39 | 38 unique by content |
| Unique mobile workout summaries | 32 | Derived summaries may conflict with raw telemetry |
| Unique mobile telemetry files with GPS | 37 | Strong basis for route matching and alignment |
| Mobile raw sessions with positive SPM | 3 | Mobile SPM is usually absent or failed |
| Watch CSV files | 23 | No positive heart-rate or watch-SPM values found |
| Concept2 exports | 0 | Not available in the audited folder |

The source folder also contains archives, generated reports, and database files. Those are not treated as independent evidence because they may duplicate or derive from the primary CSV/JSON exports.

## Important quality findings

- Device start time cannot be treated as session identity. Several plausible matches have seconds-to-minutes of start/stop variation, and the selected case has an almost one-hour clock discrepancy.
- GPS route geometry is the strongest broadly available matching signal.
- Mobile raw SPM coverage is too sparse for the phone to be the default SPM authority.
- A zero-valued sensor channel must be represented as unavailable or failed, not as a valid measurement.
- Mobile workout summaries are derived claims. They must remain distinct from raw sensor distance and from SpeedCoach summaries.
- `workout.csv` represents a completed-session summary, not the prescribed workout.
- Device metadata does not reliably establish boat class, crew, seats, planned workout, or coach-observed technique.
- Watch-presence metadata is not proof that usable watch metrics exist in the supplied evidence bundle.

## Case strategy

The first public case intentionally combines several failures rather than presenting a clean sample. Later cases should isolate individual behaviors so graders can locate the cause of an error:

1. a clean matched pair;
2. partial overlap or forgotten stop;
3. missing GPS;
4. mobile SPM present but implausible;
5. copied or incorrectly paired SpeedCoach export as a negative match;
6. planned workout supplied versus absent;
7. environmental enrichment available versus insufficient;
8. longitudinal athlete/crew memory with synthetic identities.

## Public-data policy

Only minimized synthetic or transformed evidence may be committed. A public fixture must remove the real route, date, serials, phone models, workout identifiers, athlete identity, and private paths while preserving the exact failure mode needed by the evaluator. The public verifier must check both content integrity and privacy invariants.
