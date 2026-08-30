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
    evidenceSourceDefinitions.map(({ kind, defaultName, required }) => [kind, defaultName, required]),
    [
      ['PLAN', 'plan.json', true],
      ['SPEEDCOACH', 'speedcoach.csv', true],
      ['MOBILE', 'mobile.csv', false],
      ['ENVIRONMENT', 'environment.json', false],
      ['CONTEXT', 'context.json', false],
    ],
  );
  assert.deepEqual(
    evidenceSourceDefinitions.map(({ kind, originRole, authorityScope }) => [kind, originRole, authorityScope]),
    [
      ['PLAN', 'COACH', 'TRAINING_PRESCRIPTION'],
      ['SPEEDCOACH', 'DEVICE', 'MEASURED_TELEMETRY'],
      ['MOBILE', 'DEVICE', 'MEASURED_TELEMETRY'],
      ['ENVIRONMENT', 'SERVICE', 'ENVIRONMENT_OBSERVATION'],
      ['CONTEXT', null, 'HUMAN_CONTEXT'],
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

  const sourceIds = await uploadEvidenceBundle(client, files, {
    uploadedByRole: 'ATHLETE',
  });

  assert.deepEqual(sourceIds, [
    'source-plan',
    'source-speedcoach',
    'source-mobile',
    'source-environment',
    'source-context',
  ]);
  assert.equal(calls[0].contentBase64, 'UExBTiBjb250ZW50');
  assert.equal(calls[0].name, 'plan.json');
  assert.equal(calls[0].uploadedByRole, 'ATHLETE');
  assert.equal(calls[0].originRole, 'COACH');
  assert.equal(calls[1].uploadedByRole, 'ATHLETE');
  assert.equal(calls[1].originRole, 'DEVICE');
  assert.equal(calls[4].originRole, 'ATHLETE');
});

test('uploads the minimum plan and SpeedCoach bundle without optional evidence', async () => {
  const calls = [];
  const client = {
    uploadSource: async (source) => {
      calls.push(source.kind);
      return { source_id: `source-${source.kind.toLowerCase()}` };
    },
  };

  const sourceIds = await uploadEvidenceBundle(client, {
    PLAN: fakeFile('plan.json', '{}'),
    SPEEDCOACH: fakeFile('speedcoach.csv', 'telemetry'),
  });

  assert.deepEqual(calls, ['PLAN', 'SPEEDCOACH']);
  assert.deepEqual(sourceIds, ['source-plan', 'source-speedcoach']);
});

test('rejects a bundle missing a core source before uploading', async () => {
  let calls = 0;
  const client = { uploadSource: async () => { calls += 1; } };

  await assert.rejects(
    uploadEvidenceBundle(client, { PLAN: fakeFile('plan.json', '{}') }),
    /Select the training plan and SpeedCoach recording/,
  );
  assert.equal(calls, 0);
});
