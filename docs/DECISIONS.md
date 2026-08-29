# Decision Log

This log records product and engineering decisions as they are made. Accepted decisions may still be revised, but revisions must preserve the earlier rationale and link to new evidence.

## 2026-08-28 - Select rowing as the problem domain

- **Status:** accepted.
- **Decision:** Build for the fragmented daily training workflow experienced by rowing coaches and athletes.
- **Rationale:** The project owner has direct domain knowledge, access to representative device exports, and firsthand understanding of the missing context that generic fitness products overlook.

## 2026-08-28 - Use WAKE as the product identity

- **Status:** accepted working identity.
- **Decision:** Use **WAKE - Agentic Rowing Intelligence** with the tagline **Every row leaves a wake.**
- **Rationale:** The name supports both analytical progression and the emotional history of rowing without limiting the product to competitions.

## 2026-08-28 - Treat regattas as goals, not product boundaries

- **Status:** accepted.
- **Decision:** Model a regatta as one high-value goal and evaluation milestone inside continuous rowing intelligence.
- **Rationale:** Daily sessions, crew changes, boats, indoor work, conditions, and athlete history remain valuable between events.

## 2026-08-28 - Keep the hackathon repository separate

- **Status:** accepted.
- **Decision:** Build in a new repository and document the earlier mobile rowing application as pre-existing work.
- **Rationale:** This creates an honest competition boundary, protects a working application with unrelated changes, and makes reproduction simpler.

## 2026-08-28 - Preserve private telemetry outside Git

- **Status:** accepted.
- **Decision:** Commit only public, synthetic, or explicitly anonymized fixtures. Ignore raw private data by default.
- **Rationale:** Rowing exports may reveal location, time, device, and identity information.

## 2026-08-28 - Prefer metric-level sensor trust

- **Status:** accepted as the central hypothesis; evaluation pending.
- **Decision:** Do not merge devices by blindly averaging values. Select or reject evidence independently for each metric and claim.
- **Rationale:** A dedicated SpeedCoach may provide reliable SPM while a phone may still provide useful GPS, motion, or redundancy. Device quality varies by mounting, hardware, conditions, and failure mode.

## 2026-08-28 - Start with a minimal evidence scaffold

- **Status:** accepted.
- **Decision:** Commit the problem definition, pre-existing boundary, requirements, architecture hypothesis, and changelog before choosing an implementation stack.
- **Rationale:** The hackathon requires a genuine improvement story. Recording assumptions before experiments makes later results auditable and avoids rewriting the history after the solution exists.

## 2026-08-29 - Select the misaligned men's 2x session as the hero case

- **Status:** accepted.
- **Decision:** Use one real, three-device outing as the first end-to-end evaluation case. A human domain expert confirmed that the recordings describe the same men's double scull (`2x`) session with two athletes.
- **Rationale:** The case contains several valuable failure modes at once: device clocks differ by almost one hour, route evidence strongly matches, source summaries disagree, mobile raw SPM is absent, Android gyroscope readings are zero, and both mobile boat defaults are wrong.

## 2026-08-29 - Preserve conflicts and require abstention in the hero case

- **Status:** accepted.
- **Decision:** Keep the incorrect `SINGLE_SCULL` and `OC1` source values and conflicting distance/SPM summaries. The reference answer must prefer the confirmed `2x` context, choose evidence per metric, expose disagreements, and abstain from plan-compliance and technique claims.
- **Rationale:** Cleaning away contradictions would remove the agentic work. No planned workout or direct technique observation exists for this outing.

## 2026-08-29 - Publish a transformed, minimized fixture

- **Status:** accepted.
- **Decision:** Translate the route to a synthetic origin, shift all dates by one shared deterministic delta, replace identifiers, and retain only one mobile sensor row per distinct GPS position plus the final row. Keep original schemas and metric failure modes.
- **Rationale:** The transformation preserves matching, timing, source-quality, and reconciliation behavior while removing the real route, date, serials, device models, workout IDs, and unnecessary high-frequency motion data.

## 2026-08-29 - Keep raw-data regeneration local and verification public

- **Status:** accepted.
- **Decision:** Store private paths and source hashes only in ignored `private-data/`. Commit the generated fixture, public content hashes, generator, and a standalone verifier.
- **Rationale:** Maintainers with approved raw data can reproduce the transformation, while judges can verify the published artifact without private access.

## Pending decisions

- Technology stack and deployment target.
- Primary metric and evaluation rubric.
- Baseline definition.
- Agent/tool framework and model.
- Normalized evidence and session schemas beyond the first fixture contract.
