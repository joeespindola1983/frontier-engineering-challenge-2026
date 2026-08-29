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
- It does not upload evidence or invoke the live agent.
- Checkpoint answers and approved goal memory are in-memory browser state.
- The compact demo data is regression-tested against the committed agent output.

See `../docs/PRODUCT_INTERFACE.md` for the product contract.
