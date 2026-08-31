export const evidenceSourceDefinitions = [
  {
    kind: 'PLAN',
    required: true,
    title: 'Training plan',
    defaultName: 'plan.json',
    description: 'Normalized prescription and recovery structure',
    originRole: 'COACH',
    authorityScope: 'TRAINING_PRESCRIPTION',
    accept: '.json,application/json',
  },
  {
    kind: 'SPEEDCOACH',
    required: true,
    title: 'SpeedCoach recording',
    defaultName: 'speedcoach.csv',
    description: 'Normalized or SpeedCoach vendor CSV',
    originRole: 'DEVICE',
    authorityScope: 'MEASURED_TELEMETRY',
    accept: '.csv,text/csv',
  },
  {
    kind: 'MOBILE',
    required: false,
    title: 'Mobile recording',
    defaultName: 'mobile.csv',
    description: 'Normalized or WAKE mobile sensor CSV',
    originRole: 'DEVICE',
    authorityScope: 'MEASURED_TELEMETRY',
    accept: '.csv,text/csv',
  },
  {
    kind: 'ENVIRONMENT',
    required: false,
    title: 'Environment timeline',
    defaultName: 'environment.json',
    description: 'Normalized time-aligned observations',
    originRole: 'SERVICE',
    authorityScope: 'ENVIRONMENT_OBSERVATION',
    accept: '.json,application/json',
  },
  {
    kind: 'CONTEXT',
    required: false,
    title: 'Session context',
    defaultName: 'context.json',
    description: 'Boat, crew, goal, and investigation request',
    originRole: null,
    authorityScope: 'HUMAN_CONTEXT',
    accept: '.json,application/json',
  },
];

function bytesToBase64(bytes) {
  let binary = '';
  const chunkSize = 0x8000;
  for (let start = 0; start < bytes.length; start += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(start, start + chunkSize));
  }
  return btoa(binary);
}

async function fileToBase64(file) {
  return bytesToBase64(new Uint8Array(await file.arrayBuffer()));
}

function validateUpload(files, uploadedByRole, weather) {
  if (!['ATHLETE', 'COACH'].includes(uploadedByRole)) {
    throw new TypeError('Evidence contributor must be ATHLETE or COACH.');
  }
  const missing = evidenceSourceDefinitions.filter(({ kind, required }) => required && !files[kind]);
  if (missing.length) {
    throw new Error('Select the training plan and SpeedCoach recording before uploading this bundle.');
  }
  if (weather?.enabled && files.ENVIRONMENT) {
    throw new Error('Choose either an uploaded environment timeline or historical weather enrichment.');
  }
  if (weather?.enabled && weather.authorizedLocationLookup !== true) {
    throw new Error('Authorize the approximate session location lookup before requesting historical weather.');
  }
  if (weather?.enabled && !weather.sessionTimezone?.trim()) {
    throw new Error('Confirm the session timezone before requesting historical weather.');
  }
}

export async function uploadEvidenceBundleWithWeather(
  client,
  files,
  { uploadedByRole = 'COACH', weather = { enabled: false } } = {},
) {
  validateUpload(files, uploadedByRole, weather);

  const sourceIds = [];
  const uploadedByKind = {};
  let weatherResult = { status: 'NOT_REQUESTED' };
  for (const definition of evidenceSourceDefinitions) {
    const file = files[definition.kind];
    if (file) {
      const source = await client.uploadSource({
        kind: definition.kind,
        name: file.name,
        contentBase64: await fileToBase64(file),
        uploadedByRole,
        originRole: definition.originRole ?? uploadedByRole,
      });
      uploadedByKind[definition.kind] = source.source_id;
      sourceIds.push(source.source_id);
      continue;
    }
    if (definition.kind === 'ENVIRONMENT' && weather.enabled) {
      try {
        const enrichment = await client.enrichWeather({
          speedcoachSourceId: uploadedByKind.SPEEDCOACH,
          requestedByRole: uploadedByRole,
          authorizedLocationLookup: true,
          sessionTimezone: weather.sessionTimezone.trim(),
        });
        sourceIds.push(enrichment.source.source_id);
        weatherResult = {
          status: 'ADDED',
          sourceId: enrichment.source.source_id,
          lookup: enrichment.lookup,
          preview: enrichment.preview,
        };
      } catch (cause) {
        weatherResult = {
          status: 'UNAVAILABLE',
          message: cause instanceof Error
            ? cause.message
            : 'Historical weather is unavailable.',
        };
      }
    }
  }
  return { sourceIds, weather: weatherResult };
}

export async function uploadEvidenceBundle(client, files, options = {}) {
  const result = await uploadEvidenceBundleWithWeather(client, files, options);
  return result.sourceIds;
}
