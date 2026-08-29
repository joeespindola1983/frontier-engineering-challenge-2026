export const evidenceSourceDefinitions = [
  {
    kind: 'PLAN',
    required: true,
    title: 'Training plan',
    defaultName: 'plan.json',
    description: 'Normalized prescription and recovery structure',
    accept: '.json,application/json',
  },
  {
    kind: 'SPEEDCOACH',
    required: true,
    title: 'SpeedCoach recording',
    defaultName: 'speedcoach.csv',
    description: 'Normalized or SpeedCoach vendor CSV',
    accept: '.csv,text/csv',
  },
  {
    kind: 'MOBILE',
    required: false,
    title: 'Mobile recording',
    defaultName: 'mobile.csv',
    description: 'Normalized or WAKE mobile sensor CSV',
    accept: '.csv,text/csv',
  },
  {
    kind: 'ENVIRONMENT',
    required: false,
    title: 'Environmental timeline',
    defaultName: 'environment.json',
    description: 'Normalized time-aligned observations',
    accept: '.json,application/json',
  },
  {
    kind: 'CONTEXT',
    required: false,
    title: 'Session context',
    defaultName: 'context.json',
    description: 'Boat, crew, goal, and investigation request',
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

export async function uploadEvidenceBundle(client, files) {
  const missing = evidenceSourceDefinitions.filter(({ kind, required }) => required && !files[kind]);
  if (missing.length) {
    throw new Error('Select the training plan and SpeedCoach recording before uploading this bundle.');
  }

  const sourceIds = [];
  for (const definition of evidenceSourceDefinitions) {
    const file = files[definition.kind];
    if (!file) continue;
    const source = await client.uploadSource({
      kind: definition.kind,
      name: file.name,
      contentBase64: await fileToBase64(file),
    });
    sourceIds.push(source.source_id);
  }
  return sourceIds;
}
