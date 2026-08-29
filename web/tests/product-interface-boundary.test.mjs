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
