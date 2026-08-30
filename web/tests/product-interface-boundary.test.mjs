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
