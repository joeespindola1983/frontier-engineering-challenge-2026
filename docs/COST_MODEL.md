# Cost authorization and observability

**Status:** accepted for the local demonstration runtime

WAKE separates permission to start a paid investigation from the price later
reported by the provider. The current product runtime requires an explicit
**US$0.20 operational authorization** before a new prepared bundle can reach
the bounded agent. This is a start gate, not a provider-enforced billing cap.

Preparation, source normalization, replay, checkpoint transitions, briefing
approval, and deterministic verification do not require a model call. Only an
explicitly enabled live prepared-bundle execution can incur OpenAI API cost.

## Price basis

The pinned `gpt-5.6-terra` configuration uses the official token prices of
US$2.00 per million input tokens, US$0.20 per million cached input tokens, and
US$12.00 per million output tokens:

- <https://developers.openai.com/api/docs/models/gpt-5.6-terra>

The runner calculates approximate cost from the usage returned by the
Responses API. `max_output_tokens` limits generated tokens, including reasoning
tokens; it does not set a dollar-denominated provider cap:

- <https://developers.openai.com/api/reference/cli/resources/responses/methods/create>

The word **approximate** is intentional. Provider billing remains the source of
truth, and future changes to prices, caching, or model configuration require a
new version of this cost model.

## Measured reference and planning projection

The accepted v2 evidence-ablation run is evaluation evidence, not a measurement
of a novel product upload. Its three conditions cost US$0.119132, US$0.151718,
and US$0.087826. This supports US$0.15 as a transparent planning reference while
retaining US$0.20 as the local start authorization.

At US$0.15 per live investigation, a simple planning projection is:

- 100 investigations: approximately US$15;
- 1,000 investigations: approximately US$150;
- 10,000 investigations: approximately US$1,500.

These figures are linear estimates, not a quote or a guarantee. Real cost
depends on input size, retries, output length, caching, model choice, and tool
rounds.

### Two-week demo-club projection

The deterministic period screen processes all 40 recorded activities at zero
model cost. Of ten attention signals, two complete candidates were explicitly
authorized for bounded investigation; the other eight remain routed to a human
or missing source. The two calls cost US$0.089806 and US$0.104312, for an
observed total of **US$0.194118**, 60,094 tokens, and 56.001 seconds of summed
case runtime. Both stayed within their individual US$0.20 start authorizations.

Only the optional longitudinal synthesis remains a projected paid execution.
At the accepted planning reference it projects to US$0.15 and requires a new
US$0.20 operational start authorization. Neither value is an observed synthesis
charge, and the synthesis has not been authorized or executed.

The complete public batch validates 40 activity records and reconstructs 38
water sessions without a model call. It does not multiply the two observed
agent calls across every record. At the observed two-candidate average of
US$0.097059, calling the agent on all 40 records would project to US$3.882360;
that is a counterfactual linear estimate, not a performed run. Selective routing
is both the product behavior and the cost-control mechanism.

## Runtime contract

`POST /api/source-bundles/:id/execute` requires both `mode: live` and
`authorized_cost_usd` at or above the service's configured threshold. The
default threshold is US$0.20 and can be changed locally with:

```bash
uv run python scripts/wake_product_service.py \
  --allow-live \
  --required-cost-authorization-usd 0.20
```

The browser must deliberately pass the same authorization:

```bash
NEXT_PUBLIC_WAKE_API_URL=http://127.0.0.1:8788 \
NEXT_PUBLIC_WAKE_RUNTIME_MODE=live \
NEXT_PUBLIC_WAKE_COST_AUTHORIZATION_USD=0.20 \
npm run dev
```

`POST /api/source-batches/:id/execute` applies the same gate sequentially. An
explicit batch authorization is divided into a whole number of start slots: a
US$0.40 authorization at the default threshold permits at most two new starts
in that request. Completed bundles are idempotent; item failures are isolated;
pending items may resume with a later authorization. The batch authorization is
still not a provider cap.

After execution, the response and coach review expose input, output, and total
tokens; monotonic runtime; approximate cost; authorized amount; and whether the
observed cost exceeded that authorization. An exceedance is visible but cannot
retroactively stop a provider request. `GET /api/runtime/costs` aggregates each
new execution once and the local prototype state restores that ledger after a
service restart. This is still not production billing control: the JSON store is
not transactional across processes, externally reconciled, or provider-enforced.

## Optimization policy

Cost changes must preserve the fixed-case quality and abstention boundaries.
The optimization order is:

1. remove unnecessary evidence and repeated tool context deterministically;
2. reduce avoidable verifier retries;
3. evaluate prompt caching where the provider reports it;
4. compare a cheaper model or routing policy only on the same frozen cases;
5. adopt a change only when its quality/cost trade-off is measured and recorded.

WAKE does not switch models or remove verification merely because a single run
was expensive. Every meaningful optimization belongs in
`IMPROVEMENT_CHANGELOG.md`, including attempts that are later removed.
