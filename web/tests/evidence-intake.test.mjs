import assert from 'node:assert/strict';
import test from 'node:test';

import {
  evidenceSourceDefinitions,
  uploadEvidenceBundle,
} from '../app/lib/evidence-intake.mjs';


function fakeFile(name, text) {
  const bytes = new TextEncoder().encode(text);
  return {
    name,
    arrayBuffer: async () => bytes.buffer,
  };
}

test('defines the complete evidence bundle in a stable investigation order', () => {
  assert.deepEqual(
    evidenceSourceDefinitions.map(({ kind, defaultName }) => [kind, defaultName]),
    [
      ['PLAN', 'plan.json'],
      ['SPEEDCOACH', 'speedcoach.csv'],
      ['MOBILE', 'mobile.csv'],
      ['ENVIRONMENT', 'environment.json'],
      ['CONTEXT', 'context.json'],
    ],
  );
});

test('uploads every selected source and returns source ids in contract order', async () => {
  const calls = [];
  const client = {
    uploadSource: async (source) => {
      calls.push(source);
      return { source_id: `source-${source.kind.toLowerCase()}` };
    },
  };
  const files = Object.fromEntries(
    evidenceSourceDefinitions.map(({ kind, defaultName }) => [
      kind,
      fakeFile(defaultName, `${kind} content`),
    ]),
  );

  const sourceIds = await uploadEvidenceBundle(client, files);

  assert.deepEqual(sourceIds, [
    'source-plan',
    'source-speedcoach',
    'source-mobile',
    'source-environment',
    'source-context',
  ]);
  assert.equal(calls[0].contentBase64, 'UExBTiBjb250ZW50');
  assert.equal(calls[0].name, 'plan.json');
});

test('rejects a partial upload bundle before sending any source', async () => {
  let calls = 0;
  const client = { uploadSource: async () => { calls += 1; } };

  await assert.rejects(
    uploadEvidenceBundle(client, { PLAN: fakeFile('plan.json', '{}') }),
    /Select all five evidence files/,
  );
  assert.equal(calls, 0);
});
