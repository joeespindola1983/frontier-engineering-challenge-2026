# WAKE web replay

This React/Vinext application demonstrates the coach-facing WAKE workflow using committed public synthetic case 002.

## Run locally

Node.js 22.13 or newer is required.

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
npm run dev
```

The product client calls only task-level endpoints; source trust and agent tools remain server-side.

With the local service configured, the intake requires a plan and SpeedCoach file and accepts mobile, environment, and context files independently. Each selected file is validated and the browser receives metadata rather than stored bytes. SpeedCoach vendor and WAKE mobile sensor CSVs are normalized deterministically, with missing SPM preserved as missing. New bundles can be prepared and explicitly executed through the local live path; only the exact five-file public case-002 bundle can reuse committed replay output. The page still uses the replay investigation transition until generic checkpoint and briefing state is complete.

See `../docs/PRODUCT_INTERFACE.md` for the product contract.
