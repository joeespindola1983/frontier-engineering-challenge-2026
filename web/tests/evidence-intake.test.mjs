import assert from 'node:assert/strict';
import test from 'node:test';

import {
  evidenceSourceDefinitions,
  uploadEvidenceBundle,
  uploadEvidenceBundleWithWeather,
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

test('adds authorized historical weather in environment source order', async () => {
  const calls = [];
  const client = {
    uploadSource: async (source) => {
      calls.push(`upload:${source.kind}`);
      return { source_id: `source-${source.kind.toLowerCase()}` };
    },
    enrichWeather: async (request) => {
      calls.push(`weather:${request.sessionTimezone}`);
      assert.equal(request.authorizedLocationLookup, true);
      assert.equal(request.requestedByRole, 'ATHLETE');
      assert.equal(request.speedcoachSourceId, 'source-speedcoach');
      return {
        source: { source_id: 'source-weather', kind: 'ENVIRONMENT' },
        lookup: { provider: 'Open-Meteo', cache_hit: false },
        preview: {
          provider: 'Open-Meteo',
          sample_count: 3,
          wind_speed_range_m_s: [1, 4],
        },
      };
    },
  };

  const result = await uploadEvidenceBundleWithWeather(
    client,
    {
      PLAN: fakeFile('plan.json', '{}'),
      SPEEDCOACH: fakeFile('speedcoach.csv', 'telemetry'),
      CONTEXT: fakeFile('context.json', '{}'),
    },
    {
      uploadedByRole: 'ATHLETE',
      weather: {
        enabled: true,
        authorizedLocationLookup: true,
        sessionTimezone: 'America/Sao_Paulo',
      },
    },
  );

  assert.deepEqual(calls, [
    'upload:PLAN',
    'upload:SPEEDCOACH',
    'weather:America/Sao_Paulo',
    'upload:CONTEXT',
  ]);
  assert.deepEqual(result.sourceIds, [
    'source-plan',
    'source-speedcoach',
    'source-weather',
    'source-context',
  ]);
  assert.equal(result.weather.status, 'ADDED');
  assert.equal(result.weather.preview.provider, 'Open-Meteo');
});

test('rejects weather without consent or timezone before uploading files', async () => {
  let uploads = 0;
  const client = { uploadSource: async () => { uploads += 1; } };
  const files = {
    PLAN: fakeFile('plan.json', '{}'),
    SPEEDCOACH: fakeFile('speedcoach.csv', 'telemetry'),
  };

  await assert.rejects(
    uploadEvidenceBundleWithWeather(client, files, {
      weather: { enabled: true, authorizedLocationLookup: false, sessionTimezone: 'UTC' },
    }),
    /authorize.*approximate.*location/i,
  );
  await assert.rejects(
    uploadEvidenceBundleWithWeather(client, files, {
      weather: { enabled: true, authorizedLocationLookup: true, sessionTimezone: '' },
    }),
    /session timezone/i,
  );
  assert.equal(uploads, 0);
});

test('keeps the core bundle usable when historical weather is unavailable', async () => {
  const client = {
    uploadSource: async (source) => ({ source_id: `source-${source.kind.toLowerCase()}` }),
    enrichWeather: async () => { throw new Error('Weather provider unavailable.'); },
  };

  const result = await uploadEvidenceBundleWithWeather(
    client,
    {
      PLAN: fakeFile('plan.json', '{}'),
      SPEEDCOACH: fakeFile('speedcoach.csv', 'telemetry'),
    },
    {
      weather: {
        enabled: true,
        authorizedLocationLookup: true,
        sessionTimezone: 'America/Sao_Paulo',
      },
    },
  );

  assert.deepEqual(result.sourceIds, ['source-plan', 'source-speedcoach']);
  assert.equal(result.weather.status, 'UNAVAILABLE');
  assert.match(result.weather.message, /provider unavailable/i);
});

test('does not allow an uploaded environment and provider lookup in one bundle', async () => {
  let uploads = 0;
  const client = { uploadSource: async () => { uploads += 1; } };

  await assert.rejects(
    uploadEvidenceBundleWithWeather(
      client,
      {
        PLAN: fakeFile('plan.json', '{}'),
        SPEEDCOACH: fakeFile('speedcoach.csv', 'telemetry'),
        ENVIRONMENT: fakeFile('environment.json', '{}'),
      },
      {
        weather: {
          enabled: true,
          authorizedLocationLookup: true,
          sessionTimezone: 'UTC',
        },
      },
    ),
    /choose either.*environment/i,
  );
  assert.equal(uploads, 0);
});
