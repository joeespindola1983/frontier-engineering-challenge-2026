const HUMAN_ROLES = new Set(['ATHLETE', 'COACH']);
const AUTHORITY_BASES = new Set([
  'DIRECT_PARTICIPANT',
  'DIRECT_OBSERVATION',
  'RELAYED_REPORT',
]);

export function routeHumanQuestion(question) {
  const normalized = question.toLowerCase();
  const athleteSignals = [
    'was the resistance band used',
    'equipment used',
    'equipment malfunction',
    'perceived effort',
    'discomfort',
    'what happened',
  ];
  const coachSignals = [
    'official prescription',
    'coach observation',
    'training intent',
    'was prescribed',
  ];
  if (athleteSignals.some((signal) => normalized.includes(signal))) {
    return { expectedRespondentRole: 'ATHLETE', authorityScope: 'SESSION_EXECUTION' };
  }
  if (coachSignals.some((signal) => normalized.includes(signal))) {
    return { expectedRespondentRole: 'COACH', authorityScope: 'TRAINING_INTENT' };
  }
  return { expectedRespondentRole: 'ATHLETE_OR_COACH', authorityScope: 'HUMAN_CONTEXT' };
}

export function normalizeCheckpointAnswer(response) {
  if (response === 'UNKNOWN') {
    return {
      answer: 'UNKNOWN',
      answeredByRole: null,
      recordedByRole: null,
      authorityBasis: 'UNKNOWN',
    };
  }
  if (!response || typeof response !== 'object') {
    throw new TypeError('Confirmed checkpoint answers require explicit answer provenance.');
  }
  const {
    answer,
    answeredByRole,
    recordedByRole,
    authorityBasis,
  } = response;
  if (!['YES', 'NO', 'UNKNOWN'].includes(answer)) {
    throw new TypeError(`Unsupported checkpoint answer: ${answer}`);
  }
  if (answer === 'UNKNOWN') {
    return {
      answer,
      answeredByRole: null,
      recordedByRole: recordedByRole ?? null,
      authorityBasis: 'UNKNOWN',
    };
  }
  if (
    !HUMAN_ROLES.has(answeredByRole)
    || !HUMAN_ROLES.has(recordedByRole)
    || !AUTHORITY_BASES.has(authorityBasis)
  ) {
    throw new TypeError('Confirmed checkpoint answers require explicit answer provenance.');
  }
  if (authorityBasis === 'DIRECT_PARTICIPANT' && answeredByRole !== 'ATHLETE') {
    throw new TypeError('DIRECT_PARTICIPANT requires an athlete answerer.');
  }
  if (authorityBasis === 'RELAYED_REPORT' && answeredByRole === recordedByRole) {
    throw new TypeError('RELAYED_REPORT requires different answerer and recorder roles.');
  }
  if (authorityBasis === 'DIRECT_OBSERVATION' && answeredByRole !== recordedByRole) {
    throw new TypeError('DIRECT_OBSERVATION must be recorded by the observer.');
  }
  return { answer, answeredByRole, recordedByRole, authorityBasis };
}

