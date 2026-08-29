export const evidenceSourceDefinitions = [
  {
    kind: 'PLAN',
    title: 'Training plan',
    defaultName: 'plan.json',
    description: 'Normalized prescription and recovery structure',
    accept: '.json,application/json',
  },
  {
    kind: 'SPEEDCOACH',
    title: 'SpeedCoach recording',
    defaultName: 'speedcoach.csv',
    description: 'Normalized or SpeedCoach vendor CSV',
    accept: '.csv,text/csv',
  },
  {
    kind: 'MOBILE',
    title: 'Mobile recording',
    defaultName: 'mobile.csv',
    description: 'Normalized or WAKE mobile sensor CSV',
    accept: '.csv,text/csv',
  },
  {
    kind: 'ENVIRONMENT',
    title: 'Environmental timeline',
    defaultName: 'environment.json',
    description: 'Normalized time-aligned observations',
    accept: '.json,application/json',
  },
  {
    kind: 'CONTEXT',
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
  const missing = evidenceSourceDefinitions.filter(({ kind }) => !files[kind]);
  if (missing.length) {
    throw new Error('Select all five evidence files before uploading this bundle.');
  }

  const sourceIds = [];
  for (const definition of evidenceSourceDefinitions) {
    const file = files[definition.kind];
    const source = await client.uploadSource({
      kind: definition.kind,
      name: file.name,
      contentBase64: await fileToBase64(file),
    });
    sourceIds.push(source.source_id);
  }
  return sourceIds;
}
