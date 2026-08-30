# Historical Weather Enrichment

**Status:** implemented as an opt-in local-service capability; interface controls are pending.

## Purpose

Historical weather is an optional evidence enhancer for a rowing session. It can
help WAKE describe time-aligned conditions, compare a session with other
conditions, and identify when a reported performance change coincided with a
wind shift. It does not prove that weather caused a performance outcome and it
does not replace on-boat measurements.

The core plan-versus-performed workflow remains valid with only a plan and a
SpeedCoach recording.

## Provider boundary

The first adapter uses the Open-Meteo Historical Forecast API:

- documentation: <https://open-meteo.com/en/docs/historical-forecast-api>
- historical reanalysis fallback candidate: <https://open-meteo.com/en/docs/historical-weather-api>
- attribution and licence: <https://open-meteo.com/en/license>
- usage and commercial plans: <https://open-meteo.com/en/pricing>

The request asks for hourly temperature, relative humidity, 10 m wind speed,
10 m wind direction, and 10 m gust speed in SI units. The provider may select a
nearby model grid point rather than the requested coordinate; the normalized
contract preserves both locations.

Provider availability, model selection, and commercial terms are external
dependencies. WAKE therefore treats lookup failure as a missing enhancer rather
than a failed session analysis.

## Privacy and authorization

Weather lookup is disabled unless the local service starts with
`--allow-weather`. Every request must also include
`authorized_location_lookup: true` and the requesting role.

The deterministic lookup builder:

1. requires timezone-aware telemetry timestamps or an explicitly supplied IANA
   timezone for a device export whose clock is local;
2. computes the median GPS point from normalized telemetry;
3. rounds latitude and longitude to two decimal places before the external
   request;
4. requests only the date range needed for the session plus a one-hour query
   buffer; and
5. sends no athlete identity, device identifier, plan, session context, route,
   or raw telemetry rows.

The returned API response and exact request URL are not exposed to the browser.
Generated environment evidence remains process-local like other uploaded
sources. This minimizes disclosure but does not make a coordinate anonymous;
a future hosted product needs an explicit privacy policy and retention review.

## Normalized contract

Provider responses become `wake.environment_timeline.v2`. Version 2 adds:

- provider, dataset/model, grid resolution, retrieval time, and attribution;
- rounded requested location and provider grid location;
- the exact UTC session window;
- declared units and wind-direction convention;
- temperature, humidity, wind speed, direction, and gust samples; and
- explicit limitations.

The schema remains backward-compatible with the committed v1 synthetic
fixture. Internal values stay in metres per second, degrees Celsius, percent,
degrees, and UTC. Locale-specific display conversion belongs at the interface
boundary and must never alter analysis values.

## Deterministic interpretation

Open-Meteo may return every hour of a requested day. WAKE filters those samples
to the bounded query window before storing the environment timeline. The bundle
assembler then anchors elapsed time to the session start and derives signed
headwind and crosswind components only when route heading is available.

The environment analysis uses only samples inside the session window. If the
provider cadence is too coarse to resolve a change during a short session, the
tool returns `INSUFFICIENT_TEMPORAL_RESOLUTION`. All condition comparisons are
time associations, not causal claims.

## Local operation

Start the product service with weather enabled:

```bash
uv run python scripts/wake_product_service.py --allow-weather
```

After uploading a SpeedCoach-compatible source, request an environment source.
Raw SpeedCoach vendor files have local timestamps with an unknown timezone, so
their request must include the confirmed session timezone:

```json
{
  "speedcoach_source_id": "source-id",
  "requested_by_role": "ATHLETE",
  "authorized_location_lookup": true,
  "session_timezone": "America/Sao_Paulo"
}
```

Send that body to `POST /api/environment-enrichments`. The response contains a
normal source metadata object that can be selected as the optional environment
input during bundle preparation.

## Evidence and limitations

The adapter and service were developed through red-green-refactor tests. A live
connectivity smoke test used only a public synthetic coordinate. That test
revealed that a date-bounded provider response contained the full day; the
behavior was converted into a regression test and fixed by query-window
filtering.

This smoke test demonstrates request compatibility and deterministic
normalization only. It does not validate local weather accuracy, establish a
performance effect, or make the provider data equivalent to an anemometer on
the rowing shell.
