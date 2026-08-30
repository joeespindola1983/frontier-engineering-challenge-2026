const ANSWERS = new Set(['YES', 'NO', 'UNKNOWN']);

function humanConfirmationFromAnswer(question, answer) {
  if (answer === 'YES' || answer === 'NO') {
    const label = answer === 'YES' ? 'Yes' : 'No';
    return {
      status: 'HUMAN_CONFIRMED',
      answer,
      value: answer === 'YES',
      source: 'Coach confirmation',
      question,
      statement: `Coach answered "${label}" to: ${question}`,
    };
  }
  return {
    status: 'UNKNOWN',
    answer: 'UNKNOWN',
    value: null,
    source: null,
    question,
    statement: `No human confirmation was supplied for: ${question}`,
  };
}

function reconstructedFinding(review) {
  return {
    status: 'SUPPORTED',
    title: `${review.workIntervals.length} prescribed work intervals were reconstructed.`,
    explanation:
      'The reconstruction uses the supplied training plan and SpeedCoach evidence; it does not by itself establish technique.',
    evidenceRefs: ['input/plan.json', 'input/speedcoach.csv'],
  };
}

function deviationFindings(review) {
  return review.workIntervals
    .filter((interval) => interval.status === 'DEVIATION')
    .map((interval) => ({
      status: 'ATTENTION',
      title: `Work interval ${interval.index} needs attention.`,
      explanation:
        `It averaged ${interval.averageSpm} SPM against the prescribed `
        + `${interval.targetMinSpm}–${interval.targetMaxSpm} SPM range.`,
      evidenceRefs: interval.evidenceRefs ?? ['input/plan.json', 'input/speedcoach.csv'],
    }));
}

export function resolveCheckpoint(review, answer) {
  if (!ANSWERS.has(answer)) {
    throw new TypeError(`Unsupported checkpoint answer: ${answer}`);
  }
  const humanConfirmation = humanConfirmationFromAnswer(
    review.checkpoint.question,
    answer,
  );
  const deviations = deviationFindings(review);
  const findings = [reconstructedFinding(review), ...deviations];
  if (review.environment?.summary) {
    findings.push({
      status: 'SUPPORTED_WITH_LIMITATION',
      title: 'Environmental context retains a non-causal boundary.',
      explanation: review.environment.summary,
      evidenceRefs: review.environment.evidenceRefs ?? [],
    });
  }
  findings.push({
    status: humanConfirmation.status,
    title: humanConfirmation.status === 'UNKNOWN'
      ? 'Coach context remains unknown.'
      : 'Coach context was human-confirmed.',
    explanation: humanConfirmation.statement,
    evidenceRefs: humanConfirmation.status === 'UNKNOWN'
      ? []
      : ['human-confirmation/checkpoint'],
  });
  const deviationLabel = deviations.length === 0
    ? 'no plan deviations were reported'
    : `${deviations.length} plan deviation${deviations.length === 1 ? ' needs' : 's need'} coach review`;

  return {
    briefingId: `briefing-${review.sessionId}`,
    sessionId: review.sessionId,
    goalId: `goal-${review.sessionId}`,
    scheduledDate: review.scheduledDate,
    title: review.title,
    verificationStatus: 'VERIFIED',
    headline:
      `${review.workIntervals.length} work intervals reconstructed; ${deviationLabel}.`,
    summary: review.coachBriefing,
    workIntervals: review.workIntervals,
    sourcePolicy: review.sourcePolicy,
    environment: review.environment,
    humanConfirmation,
    findings,
    limitations: review.abstentions,
    pendingApproval: true,
  };
}

export function approveBriefingMemory(briefing, approved) {
  const empty = {
    goalId: briefing.goalId,
    title: `Session learning · ${briefing.title}`,
    currentConclusion:
      'No session evidence has been approved for this goal in the prototype.',
    approvedSessions: [],
    unresolvedQuestions: [],
    nextUsefulEvidence: [],
  };
  if (!approved) return empty;

  const deviations = briefing.findings
    .filter((finding) => finding.status === 'ATTENTION')
    .map((finding) => finding.explanation);
  return {
    ...empty,
    currentConclusion:
      `One approved session preserves this result: ${briefing.headline} `
      + 'It does not establish a longitudinal trend.',
    approvedSessions: [
      {
        sessionId: briefing.sessionId,
        scheduledDate: briefing.scheduledDate,
        title: briefing.title,
        approval: 'COACH_APPROVED',
        summary: briefing.headline,
        humanConfirmation: briefing.humanConfirmation,
      },
    ],
    unresolvedQuestions: [
      ...deviations,
      ...(briefing.humanConfirmation.status === 'UNKNOWN'
        ? [briefing.humanConfirmation.question]
        : []),
    ],
    nextUsefulEvidence: [
      'A comparable session with the same plan and more stable conditions.',
      'Coach or athlete context recorded immediately after the outing.',
    ],
  };
}
