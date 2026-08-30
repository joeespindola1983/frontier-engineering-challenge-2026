import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { demoClub } from '../app/lib/demo-club.mjs';
import { buildPostRegattaComparison, postRegattaPackage } from '../app/lib/post-regatta.mjs';

const expectedScenarios = new Set([
  'OBSERVED_FASTER_COMPARABLE',
  'OBSERVED_SLOWER_COMPARABLE',
  'STABLE_RANGE',
  'ENVIRONMENT_CONFOUNDED',
  'PARTICIPATION_REVIEW',
  'INSUFFICIENT_EVIDENCE',
]);

test('provides a real-informed synthetic two-week package for every demo athlete and crew', () => {
  assert.equal(postRegattaPackage.schema_version, 'wake.post_regatta_package.v1');
  assert.equal(postRegattaPackage.synthetic, true);
  assert.equal(postRegattaPackage.provenance.basis, 'REAL_INFORMED_SYNTHETIC');
  assert.equal(postRegattaPackage.period.start, '2026-09-07');
  assert.equal(postRegattaPackage.period.end, '2026-09-18');
  assert.equal(postRegattaPackage.period.weekdays.length, 10);
  assert.equal(postRegattaPackage.model_called, false);
  assert.equal(postRegattaPackage.load_cost_usd, 0);

  assert.deepEqual(
    new Set(postRegattaPackage.athlete_ids),
    new Set(demoClub.athletes.map((athlete) => athlete.athlete_id)),
  );
  assert.deepEqual(
    new Set(postRegattaPackage.crew_ids),
    new Set(demoClub.crews.map((crew) => crew.crew_id)),
  );
  assert.ok(postRegattaPackage.activities.length >= 48);
  assert.ok(postRegattaPackage.activities.some((activity) => activity.modality === 'WATER_CREW'));
  assert.ok(postRegattaPackage.activities.some((activity) => activity.modality === 'ERG'));
});

test('commits a public no-spend manifest matching the executable package', async () => {
  const manifest = JSON.parse(await readFile(new URL('../../data/demo-club-post-regatta/v1/manifest.json', import.meta.url), 'utf8'));

  assert.equal(manifest.package_id, postRegattaPackage.package_id);
  assert.equal(manifest.coverage.activities, postRegattaPackage.activities.length);
  assert.equal(manifest.coverage.athletes, postRegattaPackage.athlete_ids.length);
  assert.equal(manifest.coverage.crews, postRegattaPackage.crew_ids.length);
  assert.equal(manifest.analysis.model_called, false);
  assert.equal(manifest.analysis.load_cost_usd, 0);
  assert.equal(manifest.analysis.causal_conclusion, 'NOT_ESTABLISHED');
});

test('builds evidence-linked observations without turning change into causation', () => {
  const comparison = buildPostRegattaComparison(demoClub, postRegattaPackage);
  const activityIds = new Set(postRegattaPackage.activities.map((activity) => activity.activity_id));

  assert.equal(comparison.schema_version, 'wake.post_regatta_comparison.v1');
  assert.equal(comparison.analysis_mode, 'DETERMINISTIC_PERIOD_COMPARISON');
  assert.equal(comparison.model_called, false);
  assert.equal(comparison.causal_conclusion, 'NOT_ESTABLISHED');
  assert.equal(comparison.coverage.post_regatta_activities, postRegattaPackage.activities.length);
  assert.deepEqual(new Set(comparison.signals.map((signal) => signal.scenario)), expectedScenarios);
  assert.ok(comparison.signals.every((signal) => signal.evidence_refs.length > 0));
  assert.ok(comparison.signals.flatMap((signal) => signal.evidence_refs).some((ref) => activityIds.has(ref)));

  const serialized = JSON.stringify(comparison);
  assert.doesNotMatch(serialized, /fitness improved|fitness declined|performance improved|performance declined/i);
  assert.match(serialized, /observed/i);
  assert.match(serialized, /context|comparable|evidence/i);
});

test('interface loads the package explicitly and preserves the no-spend boundary', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');

  assert.match(page, /Load 2-week package/);
  assert.match(page, /Post-regatta comparison/);
  assert.match(page, /No model call/);
  assert.match(page, /US\$0\.00/);
  assert.match(page, /buildPostRegattaComparison/);
  assert.match(page, /causal_conclusion/);
  assert.match(page, /signal\.label/);
  const labels = buildPostRegattaComparison(demoClub, postRegattaPackage).signals.map((signal) => signal.label);
  assert.ok(labels.includes('Observed faster'));
  assert.ok(labels.includes('Observed slower'));
  assert.doesNotMatch(page, /fitness improved|fitness declined/i);
});
