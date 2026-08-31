const SOURCE_LABELS = {
  'speedcoach.csv': 'SpeedCoach recording',
  'plan.json': 'Training plan',
  'mobile.csv': 'Mobile recording',
  'environment.json': 'Environment timeline',
  'context.json': 'Session context',
};

export function formatEvidenceReference(reference) {
  const filename = reference.trim().replace(/^input\//, '');
  return SOURCE_LABELS[filename] ?? 'Supporting evidence';
}

export function buildReconstructionDisplay(reconstruction) {
  const evidenceMatch = reconstruction.match(/\s*\[([^\]]+)\]\s*$/u);
  const narrative = evidenceMatch
    ? reconstruction.slice(0, evidenceMatch.index).trim()
    : reconstruction.trim();
  const bullets = narrative
    .split(/(?<=[.!?])\s+(?=[A-Z])/u)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
  const evidenceLabels = evidenceMatch
    ? [...new Set(evidenceMatch[1].split(/[;,]/u).map(formatEvidenceReference))]
    : [];

  return { bullets, evidenceLabels };
}
