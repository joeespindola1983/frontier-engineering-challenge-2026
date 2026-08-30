import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import {
  demoClub,
  listCoachAttention,
  summarizeAthlete,
  summarizeClub,
  summarizeCrew,
} from '../app/lib/demo-club.mjs';
import { buildAthleteTrainingDays, buildClubTrainingDaySummary } from '../app/lib/training-days.mjs';


test('models two work weeks across the requested ten rowing crews', () => {
  assert.equal(demoClub.schema_version, 'wake.demo_club.v1');
  assert.equal(demoClub.synthetic, true);
  assert.equal(demoClub.provenance.basis, 'REAL_INFORMED_SYNTHETIC');
  assert.ok(demoClub.provenance.real_inputs.length >= 4);
  assert.match(demoClub.provenance.boundary, /not statistically representative/i);
  assert.equal(demoClub.period.weekdays.length, 10);
  assert.equal(demoClub.athletes.length, 16);
  assert.equal(demoClub.crews.filter((crew) => crew.boat_class === '2x').length, 4);
  assert.equal(demoClub.crews.filter((crew) => crew.boat_class === '4x').length, 4);
  assert.equal(demoClub.crews.filter((crew) => crew.boat_class === '8x').length, 2);
  assert.deepEqual(
    demoClub.crews.filter((crew) => crew.boat_class === '8x').map((crew) => crew.category).sort(),
    ['MEN', 'WOMEN'],
  );

  for (const crew of demoClub.crews) {
    assert.equal(crew.lineup.length, Number.parseInt(crew.boat_class, 10));
    assert.equal(new Set(crew.lineup.map((seat) => seat.athlete_id)).size, crew.lineup.length);
    assert.equal(new Set(crew.lineup.map((seat) => seat.seat)).size, crew.lineup.length);
    assert.ok(demoClub.boats.some((boat) => boat.boat_id === crew.boat_id && boat.boat_class === crew.boat_class));
  }
});


test('preserves cancelled crews, alternate training, and explicit unrecorded athletes', () => {
  const cancelled = demoClub.outings.filter((outing) => outing.outcome === 'CREW_UNAVAILABLE');
  assert.equal(cancelled.length, 3);
  assert.ok(demoClub.activities.some((activity) => activity.modality === 'WATER_SOLO'));
  assert.ok(demoClub.activities.some((activity) => activity.modality === 'ERG'));
  assert.equal(demoClub.participation_gaps.length, 3);

  for (const gap of demoClub.participation_gaps) {
    const athleteTrained = demoClub.activities.some(
      (activity) => activity.date === gap.date && activity.athlete_ids.includes(gap.athlete_id),
    );
    assert.equal(athleteTrained, false);
    assert.equal(gap.classification, 'EXPECTED_DAY_WITHOUT_RECORDED_ACTIVITY');
  }
});


test('stores every Concept2 result as an individual athlete record', () => {
  const ergActivities = demoClub.activities.filter((activity) => activity.modality === 'ERG');

  assert.equal(ergActivities.length, 14);
  assert.ok(ergActivities.every((activity) => activity.athlete_ids.length === 1));
  assert.ok(ergActivities.every((activity) => activity.erg_metrics));
  assert.deepEqual(
    [...new Set(ergActivities.map((activity) => activity.erg_metrics.workout_type))].sort(),
    ['FIXED_DISTANCE', 'FIXED_TIME', 'INTERVAL'],
  );
  assert.ok(ergActivities.every((activity) => ['PLAN_CONFIRMED', 'STANDALONE'].includes(activity.association_status)));
});


test('builds athlete training days without merging water and ergometer distance', () => {
  const lucas = buildAthleteTrainingDays(demoClub, 'athlete-lucas');
  const combined = lucas.days.find((day) => day.date === '2026-08-18');
  const secondCombined = lucas.days.find((day) => day.date === '2026-08-26');

  assert.equal(combined.classification, 'COMBINED');
  assert.deepEqual(combined.activities.map((activity) => activity.modality).sort(), ['ERG', 'WATER_CREW']);
  assert.ok(combined.activities.some((activity) => activity.training_role === 'POST_WATER'));
  assert.equal(secondCombined.classification, 'COMBINED');
  assert.ok(lucas.waterDistanceKm > 0);
  assert.ok(lucas.ergDistanceKm > 0);
  assert.equal(Object.hasOwn(lucas, 'distanceKm'), false);

  const sofia = buildAthleteTrainingDays(demoClub, 'athlete-sofia');
  assert.equal(sofia.days.find((day) => day.date === '2026-08-24').classification, 'INDOOR_ONLY');

  const club = buildClubTrainingDaySummary(demoClub);
  assert.equal(club.ergSessions, 14);
  assert.ok(club.combinedDays >= 3);
  assert.ok(club.indoorOnlyDays >= 3);
  assert.equal(club.expectedMissingDays, 3);
});


test('club, crew, and athlete summaries are relational rather than decorative labels', () => {
  const club = summarizeClub(demoClub);
  assert.equal(club.crewCount, 10);
  assert.equal(club.athleteCount, 16);
  assert.equal(club.plannedOutings, 38);
  assert.equal(club.completedCrewOutings, 35);
  assert.equal(club.disruptedCrewOutings, 3);
  assert.ok(club.recordedActivities > club.completedCrewOutings);

  const menEight = summarizeCrew(demoClub, 'crew-8x-men');
  assert.equal(menEight.lineup.length, 8);
  assert.equal(menEight.plannedOutings, 3);
  assert.equal(menEight.completedOutings, 2);
  assert.equal(menEight.disruptedOutings, 1);

  const lucas = summarizeAthlete(demoClub, 'athlete-lucas');
  assert.equal(lucas.name, 'Lucas');
  assert.ok(lucas.crewIds.includes('crew-2x-men'));
  assert.ok(lucas.crewIds.includes('crew-4x-men'));
  assert.ok(lucas.crewIds.includes('crew-8x-men'));
  assert.ok(lucas.soloSessions >= 1);
  assert.ok(lucas.boats.length >= 3);
  assert.ok(lucas.combinedDays >= 2);
  assert.equal(lucas.indoorOnlyDays, 0);
  assert.ok(lucas.waterDistanceKm > lucas.ergDistanceKm);
  assert.equal(Object.hasOwn(lucas, 'distanceKm'), false);
});


test('coach attention separates missing records from observed execution findings', () => {
  const attention = listCoachAttention(demoClub);
  assert.ok(attention.some((item) => item.kind === 'PARTICIPATION_GAP'));
  assert.ok(attention.some((item) => item.kind === 'CREW_UNAVAILABLE'));
  assert.ok(attention.some((item) => item.kind === 'SESSION_FINDING'));
  assert.ok(attention.every((item) => item.statement && item.date));
  assert.ok(attention.every((item) => !/injury|fitness|medical/i.test(item.statement)));
});


test('sessions surface exposes club, crew, and athlete drill-downs', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');

  assert.match(page, /function ClubOverview/);
  assert.match(page, /function CrewScreen/);
  assert.match(page, /function AthleteScreen/);
  assert.match(page, /Two-week club pulse/);
  assert.match(page, /Real-informed synthetic data/);
  assert.match(page, /modeled from real coach plans/);
  assert.match(page, /Identities, club history, and session outcomes are fictional/);
  assert.match(page, /onOpenCrew/);
  assert.match(page, /onOpenAthlete/);
  assert.match(page, /Training days/);
  assert.match(page, /Water distance/);
  assert.match(page, /Indoor distance/);
  assert.match(page, /Combined day/);
  assert.match(page, /Indoor-only/);
  assert.match(page, /Concept2 pace/);
});
