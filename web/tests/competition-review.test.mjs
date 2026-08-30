import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { demoClub } from '../app/lib/demo-club.mjs';
import {
  buildCompetitionReview,
  demoRegatta,
  distanceReferenceForCategory,
} from '../app/lib/competition-review.mjs';


test('keeps the synthetic regatta grounded in official reference patterns without claiming it is an official result', () => {
  assert.equal(demoRegatta.synthetic, true);
  assert.equal(demoRegatta.provenance.basis, 'REAL_INFORMED_SYNTHETIC');
  assert.equal(demoRegatta.provenance.official_result_reproduced, false);
  assert.match(demoRegatta.provenance.boundary, /fictional/i);
  assert.equal(demoRegatta.distance_reference.status, 'REFERENCE_ONLY');
  assert.match(demoRegatta.distance_reference.caveat, /does not prove/i);
});


test('assigns distance from competitive category rather than boat class', () => {
  assert.deepEqual(distanceReferenceForCategory('JUVENILE'), {
    distance_m: 500,
    evidence_status: 'EXACT_CATEGORY_REFERENCE',
    evidence_ref: 'regatta-distance-reference:juvenile',
  });
  assert.equal(distanceReferenceForCategory('BEGINNER').distance_m, 500);
  assert.equal(distanceReferenceForCategory('MASTER_B').distance_m, 1000);
  assert.equal(distanceReferenceForCategory('ASPIRANT').distance_m, 1000);
  assert.equal(distanceReferenceForCategory('JUNIOR').distance_m, 1000);
  assert.equal(distanceReferenceForCategory('PARA_PR3').distance_m, 1000);
  assert.equal(distanceReferenceForCategory('SENIOR').distance_m, 2000);
  assert.throws(() => distanceReferenceForCategory('UNKNOWN_CATEGORY'), /Unknown competition category/);
});


test('uses a composite event identity and links every internal entry to a valid crew snapshot', () => {
  const eventIds = demoRegatta.events.map((event) => event.event_id);
  assert.equal(new Set(eventIds).size, eventIds.length);
  assert.ok(new Set(demoRegatta.events.map((event) => event.race_number)).size < eventIds.length);

  for (const entry of demoRegatta.entries.filter((item) => item.club_id === demoClub.club.club_id)) {
    const crew = demoClub.crews.find((item) => item.crew_id === entry.crew_id);
    assert.ok(crew, `missing crew ${entry.crew_id}`);
    assert.deepEqual(entry.athlete_ids, crew.lineup.map((seat) => seat.athlete_id));
    assert.ok(demoRegatta.events.some((event) => event.event_id === entry.event_id));
  }
});


test('builds a club competition review over our boats, athletes, and the full field', () => {
  const report = buildCompetitionReview(demoClub, demoRegatta);

  assert.equal(report.schema_version, 'wake.competition_review.v1');
  assert.equal(report.club.club_id, demoClub.club.club_id);
  assert.equal(report.summary.entries, 10);
  assert.equal(report.summary.athletes_entered, 16);
  assert.ok(report.summary.multi_start_athletes >= 8);
  assert.ok(report.summary.events_entered >= 6);
  assert.equal(report.entries.length, report.summary.entries);
  assert.ok(report.entries.every((entry) => entry.training_context.shared_outings >= 1));
  assert.ok(report.entries.every((entry) => entry.field.field_size >= 3));
  assert.ok(report.entries.every((entry) => entry.distance.evidence_ref));
  assert.ok(report.entries.every((entry) => entry.claim_boundaries.performance_cause === 'NOT_ESTABLISHED'));
});


test('derives pace and gaps while preserving official rank when displayed times tie', () => {
  const report = buildCompetitionReview(demoClub, demoRegatta);
  const tiedEvent = report.events.find((event) => event.results.some((result) => result.official_tie_preserved));
  assert.ok(tiedEvent);

  const tiedResults = tiedEvent.results.filter((result) => result.official_tie_preserved);
  assert.equal(tiedResults.length, 2);
  assert.equal(tiedResults[0].finish_time_s, tiedResults[1].finish_time_s);
  assert.notEqual(tiedResults[0].official_rank, tiedResults[1].official_rank);

  const finisher = report.entries.find((entry) => entry.status === 'FINISHED' && entry.official_rank > 1);
  assert.ok(finisher.pace_500m_s > 0);
  assert.ok(finisher.gap_to_winner_s > 0);
  assert.ok(finisher.gap_to_winner_pct > 0);
});


test('keeps non-completion and missing context explicit instead of inventing a performance conclusion', () => {
  const report = buildCompetitionReview(demoClub, demoRegatta);
  const nonCompletion = report.entries.find((entry) => entry.status === 'NOT_CLASSIFIED');

  assert.ok(nonCompletion);
  assert.equal(nonCompletion.finish_time_s, null);
  assert.equal(nonCompletion.pace_500m_s, null);
  assert.equal(nonCompletion.official_rank, null);
  assert.equal(nonCompletion.missing_context.reason_for_non_completion, true);
  assert.match(nonCompletion.next_question, /what happened/i);
});


test('competition review is reachable from navigation and exposes consolidated and boat-level evidence', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');

  assert.match(page, /Competition Review/);
  assert.match(page, /function CompetitionReviewScreen/);
  assert.match(page, /Our entries/);
  assert.match(page, /Competitive field/);
  assert.match(page, /Training context, not causation/);
  assert.match(page, /Distance provenance/);
  assert.match(page, /Open boat report/);
  assert.match(page, /Real-informed synthetic regatta/);
  assert.ok((page.match(/onNavigate\('competition'\)/g) ?? []).length >= 2, 'competition must remain reachable when primary navigation is hidden');
  assert.ok((page.match(/window\.scrollTo\(\{ top: 0, behavior: 'auto' \}\)/g) ?? []).length >= 2, 'screen and boat transitions must both reset scroll');
});
