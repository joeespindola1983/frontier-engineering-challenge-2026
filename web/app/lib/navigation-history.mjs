const VALID_SCREENS = new Set([
  'sessions',
  'club-crew',
  'club-athlete',
  'longitudinal-pilot',
  'post-regatta',
  'competition',
  'intake',
  'review',
  'briefing',
  'memory',
  'evaluation',
]);
const VALID_SESSIONS_VIEWS = new Set([
  'overview',
  'attention',
  'team',
  'intelligence',
  'reviews',
]);

export function buildWakeHistoryState({
  depth,
  screen,
  sessionsView,
  selectedCompetitionEntryId,
  selectedAthleteId,
  selectedCrewId,
}) {
  return {
    wakeNavigation: true,
    depth,
    screen,
    sessionsView,
    selectedCompetitionEntryId,
    selectedAthleteId,
    selectedCrewId,
  };
}

export function readWakeHistoryState(state) {
  if (
    !state
    || state.wakeNavigation !== true
    || !VALID_SCREENS.has(state.screen)
    || !VALID_SESSIONS_VIEWS.has(state.sessionsView)
    || !Number.isInteger(state.depth)
    || state.depth < 0
    || !(state.selectedCompetitionEntryId === null || typeof state.selectedCompetitionEntryId === 'string')
    || typeof state.selectedAthleteId !== 'string'
    || typeof state.selectedCrewId !== 'string'
  ) return null;
  return buildWakeHistoryState(state);
}

function encodeSegment(value) {
  return encodeURIComponent(value);
}

function decodeSegment(value) {
  try {
    return decodeURIComponent(value);
  } catch {
    return null;
  }
}

export function wakeHashForState(state) {
  if (state.screen === 'sessions') return `#sessions/${state.sessionsView}`;
  if (state.screen === 'club-crew') return `#sessions/team/crew/${encodeSegment(state.selectedCrewId)}`;
  if (state.screen === 'club-athlete') return `#sessions/team/athlete/${encodeSegment(state.selectedAthleteId)}`;
  if (state.screen === 'longitudinal-pilot') return '#sessions/intelligence/longitudinal-pilot';
  if (state.screen === 'post-regatta') return '#sessions/intelligence/post-regatta';
  if (state.screen === 'competition') {
    return state.selectedCompetitionEntryId
      ? `#competition/entry/${encodeSegment(state.selectedCompetitionEntryId)}`
      : '#competition';
  }
  if (state.screen === 'intake') return '#sessions/reviews/new';
  if (state.screen === 'review') return '#sessions/reviews/current';
  if (state.screen === 'briefing') return '#sessions/reviews/briefing';
  if (state.screen === 'memory') return '#goal-memory';
  if (state.screen === 'evaluation') return '#evaluation';
  return '#sessions/overview';
}

export function readWakeHash(hash, defaults) {
  const rawSegments = hash.replace(/^#\/?/, '').split('/').filter(Boolean);
  const segments = rawSegments.map(decodeSegment);
  if (segments.some((segment) => segment === null)) return null;

  const state = (screen, sessionsView = 'overview', selection = {}) => buildWakeHistoryState({
    depth: 0,
    screen,
    sessionsView,
    selectedCompetitionEntryId: selection.selectedCompetitionEntryId ?? defaults.selectedCompetitionEntryId,
    selectedAthleteId: selection.selectedAthleteId ?? defaults.selectedAthleteId,
    selectedCrewId: selection.selectedCrewId ?? defaults.selectedCrewId,
  });

  if (segments[0] === 'competition') {
    if (segments.length === 1) return state('competition', 'overview', { selectedCompetitionEntryId: null });
    if (segments.length === 3 && segments[1] === 'entry' && segments[2]) {
      return state('competition', 'overview', { selectedCompetitionEntryId: segments[2] });
    }
    return null;
  }
  if (segments.length === 1 && segments[0] === 'goal-memory') return state('memory');
  if (segments.length === 1 && segments[0] === 'evaluation') return state('evaluation');
  if (segments[0] !== 'sessions') return null;
  if (segments.length === 1) return state('sessions');

  const view = segments[1];
  if (!VALID_SESSIONS_VIEWS.has(view)) return null;
  if (segments.length === 2) return state('sessions', view);
  if (view === 'team' && segments.length === 4 && segments[2] === 'crew' && segments[3]) {
    return state('club-crew', view, { selectedCrewId: segments[3] });
  }
  if (view === 'team' && segments.length === 4 && segments[2] === 'athlete' && segments[3]) {
    return state('club-athlete', view, { selectedAthleteId: segments[3] });
  }
  if (view === 'intelligence' && segments.length === 3 && segments[2] === 'longitudinal-pilot') {
    return state('longitudinal-pilot', view);
  }
  if (view === 'intelligence' && segments.length === 3 && segments[2] === 'post-regatta') {
    return state('post-regatta', view);
  }
  if (view === 'reviews' && segments.length === 3) {
    if (segments[2] === 'new') return state('intake', view);
    if (segments[2] === 'current') return state('review', view);
    if (segments[2] === 'briefing') return state('briefing', view);
  }
  return null;
}

export function isNestedWakeLocation(state) {
  if (state.screen === 'competition') return Boolean(state.selectedCompetitionEntryId);
  return new Set([
    'club-crew',
    'club-athlete',
    'longitudinal-pilot',
    'post-regatta',
    'intake',
    'review',
    'briefing',
  ]).has(state.screen);
}

export function parentWakeHistoryState(state) {
  if (!isNestedWakeLocation(state)) return null;
  if (state.screen === 'competition') {
    return buildWakeHistoryState({ ...state, depth: 0, selectedCompetitionEntryId: null });
  }
  const sessionsView = ['club-crew', 'club-athlete'].includes(state.screen)
    ? 'team'
    : ['longitudinal-pilot', 'post-regatta'].includes(state.screen)
      ? 'intelligence'
      : 'reviews';
  return buildWakeHistoryState({
    ...state,
    depth: 0,
    screen: 'sessions',
    sessionsView,
    selectedCompetitionEntryId: null,
  });
}
