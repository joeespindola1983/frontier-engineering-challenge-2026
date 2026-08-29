const ANSWERS = new Set(['YES', 'NO', 'UNKNOWN']);

function equipmentFromAnswer(answer) {
  if (answer === 'YES') {
    return {
      status: 'HUMAN_CONFIRMED',
      value: true,
      source: 'Coach confirmation',
      statement:
        'The coach confirmed that the resistance band was used for repetitions 1–3 and removed before repetition 4.',
    };
  }
  if (answer === 'NO') {
    return {
      status: 'HUMAN_CONFIRMED',
      value: false,
      source: 'Coach confirmation',
      statement:
        'The coach confirmed that the prescribed resistance-band change was not completed as planned.',
    };
  }
  return {
    status: 'UNKNOWN',
    value: null,
    source: null,
    statement:
      'Resistance-band use and removal cannot be confirmed from the supplied telemetry or human context.',
  };
}

export function resolveCheckpoint(review, answer) {
  if (!ANSWERS.has(answer)) {
    throw new TypeError(`Unsupported checkpoint answer: ${answer}`);
  }
  const equipment = equipmentFromAnswer(answer);
  return {
    briefingId: `briefing-${review.sessionId}`,
    sessionId: review.sessionId,
    title: review.title,
    verificationStatus: 'VERIFIED',
    headline:
      'Planned structure completed; one stroke-rate deviation needs coach review.',
    summary: review.coachBriefing,
    workIntervals: review.workIntervals,
    sourcePolicy: review.sourcePolicy,
    environment: review.environment,
    equipment,
    findings: [
      {
        status: 'SUPPORTED',
        title: 'All six prescribed work intervals were reconstructed.',
        explanation:
          'The work/recovery structure and order are supported by the plan and SpeedCoach evidence.',
        evidenceRefs: ['input/plan.json', 'input/speedcoach.csv'],
      },
      {
        status: 'ATTENTION',
        title: 'Work interval five missed its prescribed stroke-rate range.',
        explanation:
          'It averaged 19.99 SPM against the prescribed 22–24 SPM range.',
        evidenceRefs: ['input/plan.json', 'input/speedcoach.csv'],
      },
      {
        status: 'SUPPORTED_WITH_LIMITATION',
        title: 'The wind shift is associated with later speed changes.',
        explanation:
          'The evidence is time-aligned, but it does not establish wind as the cause or establish athlete regression.',
        evidenceRefs: review.environment.evidenceRefs,
      },
      {
        status: equipment.status,
        title:
          equipment.status === 'UNKNOWN'
            ? 'Resistance-band use remains unknown.'
            : 'Resistance-band context was confirmed by the coach.',
        explanation: equipment.statement,
        evidenceRefs:
          equipment.status === 'UNKNOWN'
            ? []
            : ['human-confirmation/resistance-band'],
      },
    ],
    limitations: review.abstentions,
    pendingApproval: true,
  };
}

export function approveBriefingMemory(briefing, approved) {
  if (!approved) {
    return {
      goalId: 'synthetic-goal-regatta-01',
      title: `Regatta preparation · ${briefing.title.split('·').at(-1).trim()}`,
      currentConclusion:
        'No session evidence has been approved for this goal in the prototype.',
      approvedSessions: [],
      unresolvedQuestions: [],
      nextUsefulEvidence: [],
    };
  }

  return {
    goalId: 'synthetic-goal-regatta-01',
    title: `Regatta preparation · ${briefing.title.split('·').at(-1).trim()}`,
    currentConclusion:
      'One approved session supports completion of the planned structure and identifies a fifth-interval stroke-rate deviation; it does not establish a longitudinal trend.',
    approvedSessions: [
      {
        sessionId: briefing.sessionId,
        title: briefing.title,
        approval: 'COACH_APPROVED',
        summary:
          'Six work intervals reconstructed; work five below target SPM; environmental change limits pace interpretation.',
        equipment: briefing.equipment,
      },
    ],
    unresolvedQuestions: [
      'Why did work interval five fall below the prescribed stroke-rate range?',
      ...(briefing.equipment.status === 'UNKNOWN'
        ? ['Was the resistance-band change completed?']
        : []),
    ],
    nextUsefulEvidence: [
      'A comparable session with the same plan and more stable conditions.',
      'Coach or athlete context recorded immediately after the outing.',
    ],
  };
}
