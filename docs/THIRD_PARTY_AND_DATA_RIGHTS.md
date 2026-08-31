# Third-party, service, and data-rights record

**Status:** public submission inventory as of 2026-08-30

This record supports the hackathon requirement to respect licenses, service
terms, and the right to share submitted evidence. Lockfiles remain the canonical
version inventory. This is an engineering record, not legal advice.

## Direct runtime dependencies

| Package | Locked version | Declared upstream license |
| --- | ---: | --- |
| `jsonschema` | 4.26.0 | MIT |
| `openai` | 3.6.0 | Apache-2.0 |
| `next` | 16.3.3 | MIT |
| `react` / `react-dom` | 19.2.8 | MIT |
| `@cloudflare/vite-plugin` | 1.54.2 | MIT |
| `@openai/sites-vite-plugin` | 0.2.0 | MIT |
| `vinext` | 1.0.0-beta.8 | MIT |
| `vite` | 8.2.2 | MIT |
| `typescript` | 5.9.3 | Apache-2.0 |
| `tailwindcss` and PostCSS adapter | 4.2.1 | MIT |
| `eslint` / `eslint-config-next` | 9.39.4 / 16.2.6 | MIT |
| `wrangler` / Cloudflare Workers types | 4.127.1 / 5.20260829.1 | MIT OR Apache-2.0 |

Transitive versions and integrity hashes are locked in `uv.lock` and
`web/package-lock.json`. No third-party application source was copied into this
repository. A public project-level license has not been selected; that remains
an owner decision before any reuse beyond judging.

## External services

### OpenAI API

- Used only by explicitly authorized server-side live execution.
- `OPENAI_API_KEY` is read from the local environment and never sent to browser
  code or committed.
- Saved official runs record model, prompt/config hashes, `store: false`, usage,
  runtime, and approximate cost.
- Judge replay, verification, and regrading do not call the API.
- The local authorization amount permits a start; it does not cap provider
  billing.

### Historical weather

- Lookup requires explicit approximate-location authorization and a confirmed
  session timezone.
- The service receives a rounded median coordinate and bounded time window, not
  athlete identity, plan, device metadata, or raw route rows.
- Provider output is contextual evidence. It cannot prove boat-relative wind or
  performance causation without trustworthy route direction.
- Provider failure does not block core Plan + SpeedCoach preparation.

### ElevenLabs

- The repository contains generation-ready narration text, not an API key.
- Final narration is generated outside the deterministic reproduction path.
- The project owner remains responsible for the selected voice's permitted use
  and the account's applicable terms.

## Public evidence rights and provenance

| Material | Public treatment |
| --- | --- |
| Evaluation case 001 | Minimized and anonymized from approved real exports; dates, coordinates, device identifiers, paths, and workout identifiers removed. |
| Evaluation cases 002–010 | Deterministic synthetic fixtures built from realistic failure modes and coach prescription patterns. |
| Demo club and post-regatta period | Real-informed synthetic people, crews, boats, sessions, aggregates, and outcomes. No displayed identity represents a real athlete. |
| Coach plans and WhatsApp/PDF examples | Raw files remain outside Git. Only prescription structures and notation patterns informed synthetic fixtures. |
| Concept2 PM5 material | Public packet contains minimized crops and human-confirmed transcriptions approved for the demonstration; automatic OCR is not claimed. |
| Competition programme and results | Real named documents remain outside Git. Only structural patterns and category-distance references informed a wholly fictional public competition. |
| Earlier mobile application | Source code was not copied. The project reuses only approved export structures and minimized recordings under the boundary in `docs/PREEXISTING_WORK.md`. |
| Owner QA uploads | `data/qa-interface/full-replay-bundle/` is public synthetic test material. |

## Excluded material

The public repository intentionally excludes raw private GPS, precise routes,
real athlete identity, device serials, credentials, health information, raw
WhatsApp content, official named competition sheets, original private PM5
photos outside the approved minimized packet, `.env`, and local state stores.

## Final checks

- Keep `.env`, `private-data/`, and local state outside Git.
- Keep all real athlete and club names out of synthetic training histories.
- Recheck the current service and voice terms before publishing the final video.
- If any pre-existing source code is later copied, record its exact repository,
  snapshot, and license before committing it.
