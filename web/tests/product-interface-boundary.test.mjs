import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';


test('session review renders adapter findings without case-002-only narration', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /review\.currentReconstruction/);
  assert.doesNotMatch(page, /Six work intervals are supported/);
  assert.doesNotMatch(page, /interval\.index === 4/);
  assert.doesNotMatch(page, /selected case remains fully synthetic/);
});

test('selected evidence uses the prepared live bundle path before review', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /client\.analyzeSourceBundle\(\{\s*sourceIds,/);
  assert.match(page, /configuredRuntimeMode === 'live'/);
  assert.match(page, /authorizedCostUsd: configuredCostAuthorizationUsd/);
  assert.match(page, /setCheckpointId\(result\.checkpointId\)/);
});

test('session row opens the investigation without forwarding the click event as files', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /onClick=\{\(\) => onReview\(\)\}/);
  assert.doesNotMatch(page, /onClick=\{onReview\}/);
});

test('live review discloses approximate usage cost without calling it a hard cap', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /NEXT_PUBLIC_WAKE_COST_AUTHORIZATION_USD/);
  assert.match(page, /Approx\. agent cost/);
  assert.match(page, /executionCost\.approximate_cost_usd/);
  assert.match(page, /Exceeded operational authorization/);
  assert.match(page, /Operational authorization/);
  assert.match(page, /not a provider billing cap/);
  assert.doesNotMatch(page, /Guaranteed cost cap/);
});

test('page asks the athlete checkpoint without describing every answer as coach context', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /Question for \{formatRole\(review\.checkpoint\.expectedRespondentRole\)\}/);
  assert.match(page, /Athlete answered directly/);
  assert.match(page, /Athlete answer recorded by coach/);
  assert.match(page, /Coach observed directly/);
  assert.doesNotMatch(page, /A coach answer is stored as human context/);
});

test('intake distinguishes source origin from the current uploader', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /Origin: \{formatRole\(source\.originRole \?\? contributorRole\)\}/);
  assert.match(page, /uploader: \{formatRole\(contributorRole\)\}/);
});

test('review adapter has no coach-only fallback for unattributed uploads', async () => {
  const adapter = await readFile(
    new URL('../app/lib/replay-adapter.mjs', import.meta.url),
    'utf8',
  );

  assert.match(adapter, /Locally uploaded evidence/);
  assert.doesNotMatch(adapter, /Coach-uploaded local evidence/);
});

test('weather intake makes consent, timezone, provenance, and no-model preparation visible', async () => {
  const page = await readFile(
    new URL('../app/page.tsx', import.meta.url),
    'utf8',
  );

  assert.match(page, /Historical conditions/);
  assert.match(page, /approximate session location/i);
  assert.match(page, /authorizedLocationLookup/);
  assert.match(page, /sessionTimezone/);
  assert.match(page, /uploadEvidenceBundleWithWeather/);
  assert.match(page, /prepareSourceBundle/);
  assert.match(page, /No agent call/i);
  assert.match(page, /mode: 'replay'/);
  assert.doesNotMatch(page, /weather explains/i);
});
