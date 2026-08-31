import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import {
  buildWakeHistoryState,
  isNestedWakeLocation,
  parentWakeHistoryState,
  readWakeHash,
  readWakeHistoryState,
  wakeHashForState,
} from '../app/lib/navigation-history.mjs';

test('builds a restorable internal navigation entry with selection context', () => {
  assert.deepEqual(
    buildWakeHistoryState({
      depth: 2,
      screen: 'club-athlete',
      sessionsView: 'team',
      selectedCompetitionEntryId: null,
      selectedAthleteId: 'athlete-lucas',
      selectedCrewId: 'crew-2x-men',
    }),
    {
      wakeNavigation: true,
      depth: 2,
      screen: 'club-athlete',
      sessionsView: 'team',
      selectedCompetitionEntryId: null,
      selectedAthleteId: 'athlete-lucas',
      selectedCrewId: 'crew-2x-men',
    },
  );
});

test('accepts only valid WAKE history entries', () => {
  const valid = buildWakeHistoryState({
    depth: 1,
    screen: 'review',
    sessionsView: 'reviews',
    selectedCompetitionEntryId: null,
    selectedAthleteId: 'athlete-lucas',
    selectedCrewId: 'crew-2x-men',
  });

  assert.deepEqual(readWakeHistoryState(valid), valid);
  assert.equal(readWakeHistoryState({ screen: 'review' }), null);
  assert.equal(readWakeHistoryState({ ...valid, screen: 'unknown' }), null);
  assert.equal(readWakeHistoryState({ ...valid, depth: -1 }), null);
  assert.equal(readWakeHistoryState({ ...valid, sessionsView: 'unknown' }), null);
});

const defaults = {
  selectedCompetitionEntryId: null,
  selectedAthleteId: 'athlete-lucas',
  selectedCrewId: 'crew-2x-men',
};

test('publishes readable hashes for top-level and nested product destinations', () => {
  assert.equal(wakeHashForState(buildWakeHistoryState({
    ...defaults, depth: 0, screen: 'competition', sessionsView: 'overview',
  })), '#competition');
  assert.equal(wakeHashForState(buildWakeHistoryState({
    ...defaults, depth: 1, screen: 'competition', sessionsView: 'overview', selectedCompetitionEntryId: 'entry-harbor-men-2x',
  })), '#competition/entry/entry-harbor-men-2x');
  assert.equal(wakeHashForState(buildWakeHistoryState({
    ...defaults, depth: 0, screen: 'memory', sessionsView: 'overview',
  })), '#goal-memory');
  assert.equal(wakeHashForState(buildWakeHistoryState({
    ...defaults, depth: 0, screen: 'evaluation', sessionsView: 'overview',
  })), '#evaluation');
  assert.equal(wakeHashForState(buildWakeHistoryState({
    ...defaults, depth: 1, screen: 'club-athlete', sessionsView: 'team', selectedAthleteId: 'athlete-sofia',
  })), '#sessions/team/athlete/athlete-sofia');
});

test('restores bookmarkable hashes into navigation state', () => {
  assert.deepEqual(readWakeHash('#competition', defaults), buildWakeHistoryState({
    ...defaults, depth: 0, screen: 'competition', sessionsView: 'overview',
  }));
  assert.deepEqual(readWakeHash('#competition/entry/entry-harbor-men-2x', defaults), buildWakeHistoryState({
    ...defaults, depth: 0, screen: 'competition', sessionsView: 'overview', selectedCompetitionEntryId: 'entry-harbor-men-2x',
  }));
  assert.deepEqual(readWakeHash('#sessions/team/crew/crew-4x-men', defaults), buildWakeHistoryState({
    ...defaults, depth: 0, screen: 'club-crew', sessionsView: 'team', selectedCrewId: 'crew-4x-men',
  }));
  assert.deepEqual(readWakeHash('#goal-memory', defaults), buildWakeHistoryState({
    ...defaults, depth: 0, screen: 'memory', sessionsView: 'overview',
  }));
  assert.equal(readWakeHash('#unknown', defaults), null);
});

test('shows the product back trail only below a primary destination', () => {
  const state = (screen, selectedCompetitionEntryId = null) => buildWakeHistoryState({
    ...defaults, depth: 0, screen, sessionsView: 'overview', selectedCompetitionEntryId,
  });

  assert.equal(isNestedWakeLocation(state('sessions')), false);
  assert.equal(isNestedWakeLocation(state('competition')), false);
  assert.equal(isNestedWakeLocation(state('memory')), false);
  assert.equal(isNestedWakeLocation(state('evaluation')), false);
  assert.equal(isNestedWakeLocation(state('competition', 'entry-harbor-men-2x')), true);
  assert.equal(isNestedWakeLocation(state('club-crew')), true);
  assert.equal(isNestedWakeLocation(state('review')), true);
});

test('gives a directly opened bookmark a meaningful parent destination', () => {
  const competitionEntry = buildWakeHistoryState({
    ...defaults, depth: 0, screen: 'competition', sessionsView: 'overview', selectedCompetitionEntryId: 'entry-harbor-men-2x',
  });
  const crew = buildWakeHistoryState({
    ...defaults, depth: 0, screen: 'club-crew', sessionsView: 'team', selectedCrewId: 'crew-4x-men',
  });

  assert.equal(wakeHashForState(parentWakeHistoryState(competitionEntry)), '#competition');
  assert.equal(wakeHashForState(parentWakeHistoryState(crew)), '#sessions/team');
});

test('page restores hashes, updates the URL, and gates the location trail', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');

  assert.match(page, /readWakeHash\(window\.location\.hash/);
  assert.match(page, /history\.replaceState\(initial, '', wakeHashForState\(initial\)\)/);
  assert.match(page, /history\.pushState\(nextState, '', wakeHashForState\(nextState\)\)/);
  assert.match(page, /isNestedWakeLocation\(currentNavigationState\)/);
  assert.doesNotMatch(page, /screen !== 'sessions' \? <LocationTrail/);
});
