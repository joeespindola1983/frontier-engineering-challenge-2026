# WAKE web replay

This React/Vinext application demonstrates the coach-facing WAKE workflow using committed public synthetic case 002.

The hackathon build also includes a read-only **Evaluation** destination. Its
scores, costs, case comparisons, and limitations are generated from the saved
official ten-case artifacts. Opening it never calls the model or changes the
session inbox.

## Run locally

Node.js 22.13 or newer is required.

From the repository root, the recommended complete local startup is:

```bash
./scripts/start_dashboard.sh
```

It starts the Python product service and this development server, enables the
optional weather adapter, waits for readiness, and stops both with one
`Ctrl+C`. Replay is the default and cannot invoke the model. The launcher also
finds a compatible Homebrew Node installation when an older Node version is
first on `PATH`.

For explicit paid execution, use `./scripts/start_dashboard.sh --live`. That
mode loads the ignored repository `.env`, requires `OPENAI_API_KEY`, and keeps
the existing US$0.20 start authorization visible. It is authorization to start,
not a provider billing cap. Run `./scripts/start_dashboard.sh --help` for all
options.

To run only the web process:

```bash
npm install
npm test
npm run dev
```

Validate the production artifact with:

```bash
npm run lint
npm run build
npm audit
```

## Current boundary

- The replay contains no private athlete or route data.
- It does not read evaluator ground truth.
- The hosted build does not upload evidence or invoke the live agent.
- The Evaluation view contains a public aggregate only; it includes no ground truth, raw evidence, or agent execution control.
- Checkpoint answers and approved goal memory are in-memory browser state.
- The compact demo data is regression-tested against the committed agent output.

## Connect the local product service

Start the service from the repository root:

```bash
uv run python scripts/wake_product_service.py
```

Then start the interface with the explicit service URL:

```bash
NEXT_PUBLIC_WAKE_API_URL=http://127.0.0.1:8788 npm run dev
```

This still uses replay mode and makes no API call. Live execution additionally requires the service flag `--allow-live`, `OPENAI_API_KEY`, and:

```bash
NEXT_PUBLIC_WAKE_API_URL=http://127.0.0.1:8788 \
NEXT_PUBLIC_WAKE_RUNTIME_MODE=live \
NEXT_PUBLIC_WAKE_COST_AUTHORIZATION_USD=0.20 \
npm run dev
```

Start the service with the matching operational start gate:

```bash
uv run python scripts/wake_product_service.py \
  --allow-live \
  --required-cost-authorization-usd 0.20
```

For no-model historical-weather QA, start the service in replay mode with the
weather adapter enabled:

```bash
uv run python scripts/wake_product_service.py --allow-weather
```

Then select a plan and SpeedCoach file, enable **Historical conditions**, enter
the session's IANA timezone, authorize the rounded approximate-location lookup,
and choose **Validate and prepare · No agent call**. The interface shows a safe
wind, gust, temperature, and humidity preview and a prepared source-coverage
summary. A provider failure leaves the plan plus SpeedCoach bundle usable.

The authorization is not a provider billing cap. The review shows the
token-based approximate cost after execution and flags an overrun. The service
also exposes a process-local aggregate at `GET /api/runtime/costs`.

The product client calls only task-level endpoints; source trust and agent tools remain server-side.

With the local service configured, the intake requires a plan and SpeedCoach file and accepts mobile, environment, and context files independently. An athlete or coach may contribute the files; the service records the uploader separately from the source origin and authority scope. Each selected file is validated and the browser receives metadata rather than stored bytes. SpeedCoach vendor and WAKE mobile sensor CSVs are normalized deterministically, with missing SPM preserved as missing. In explicit live mode, a selected bundle now continues through preparation, bounded-agent execution, a role-routed human checkpoint, verified briefing, and approval-gated process-local memory. Confirmed answers retain answerer, recorder, and authority basis. Only the exact five-file public case-002 bundle can reuse committed replay output.

The local service stores its prototype state at `private-data/wake-product/product-state.json` by default. The Sessions page reloads this safe index, distinguishes whether analysis, coach view, human response, and coach approval happened, and can reopen the appropriate review, briefing, or memory screen. The ignored state file also retains raw evidence so a prepared bundle survives a service restart. It is restricted to the current OS user, but it is not encrypted, authenticated, backed up, or multi-tenant; do not treat it as production club storage.

The HTTP client also supports source batches through prepare, restore, and
explicit execute calls. A batch groups previously uploaded per-session source
ids; it never uploads one combined telemetry document or creates one
multi-session model prompt. Paid execution remains sequential, resumable, and
cost-authorized. The current page visualizes the committed forty-record public
batch but does not yet expose folder or ZIP mapping controls.

## Safe browser rehearsal bundle

Use the five public synthetic files under:

```text
../data/fixtures/case-002-wind-shift-plan-deviation/input/
```

Select them in this order:

1. `plan.json` as Training plan;
2. `speedcoach.csv` as SpeedCoach recording;
3. `mobile.csv` as Mobile recording;
4. `environment.json` as Environmental timeline;
5. `context.json` as Session context.

With the service in replay mode, this exact byte-identical bundle exercises the
real upload and validation boundary without calling the model or incurring API
cost. A changed bundle cannot inherit its conclusions.

See `../docs/PRODUCT_INTERFACE.md` for the product contract.
