# WAKE demo club post-regatta package v1

This is the second public, real-informed synthetic period for the fictional WAKE Demo Club. It adds 50 compact activity records across ten weekdays for the same 16 athletes and 10 recurring crews shown in the pre-regatta interface.

The executable package is defined in [`web/app/lib/post-regatta.mjs`](../../../web/app/lib/post-regatta.mjs). The interface loads it locally and builds a deterministic comparison at US$0.00. No API key or model call is required.

The six deliberately varied outcomes are an observed faster comparable indoor result, an observed slower comparable indoor result, a stable comparable range, an environmentally confounded water comparison, a participation question, and insufficient equivalent evidence. These are product-test scenarios, not claims about real athletes and not proof that training caused a change.

Run `cd web && npm test` to validate coverage, provenance, evidence links, causal boundaries, and the interface entry point.
