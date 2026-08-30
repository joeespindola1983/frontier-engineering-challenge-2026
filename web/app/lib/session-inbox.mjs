const STATUS_LABELS = {
  READY_FOR_INVESTIGATION: 'Ready for investigation',
  NEEDS_HUMAN_RESPONSE: 'Needs athlete or coach answer',
  READY_FOR_COACH_REVIEW: 'Ready for coach review',
  READY_FOR_COACH_APPROVAL: 'Ready for coach approval',
  IN_CLUB_MEMORY: 'In club memory',
};

const ACTION_LABELS = {
  READY_FOR_INVESTIGATION: 'Open evidence',
  NEEDS_HUMAN_RESPONSE: 'Answer question',
  READY_FOR_COACH_REVIEW: 'Review analysis',
  READY_FOR_COACH_APPROVAL: 'Review briefing',
  IN_CLUB_MEMORY: 'Open memory',
};


export function sessionStatusLabel(status) {
  return STATUS_LABELS[status] ?? 'Needs attention';
}


export function sessionActionLabel(status) {
  return ACTION_LABELS[status] ?? 'Open session';
}


export function summarizeSessionInbox(sessions) {
  return {
    needsAction: sessions.filter((session) => [
      'NEEDS_HUMAN_RESPONSE',
      'READY_FOR_COACH_APPROVAL',
    ].includes(session.status)).length,
    awaitingAnalysis: sessions.filter(
      (session) => session.analysis_status === 'NOT_STARTED',
    ).length,
    viewed: sessions.filter(
      (session) => session.coach_view_status === 'VIEWED',
    ).length,
    inClubMemory: sessions.filter(
      (session) => session.memory_status === 'APPROVED',
    ).length,
  };
}
