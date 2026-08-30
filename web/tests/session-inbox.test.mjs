import assert from 'node:assert/strict';
import test from 'node:test';

import {
  sessionActionLabel,
  sessionStatusLabel,
  summarizeSessionInbox,
} from '../app/lib/session-inbox.mjs';


const sessions = [
  {
    session_id: 'ready',
    status: 'READY_FOR_INVESTIGATION',
    analysis_status: 'NOT_STARTED',
    coach_view_status: 'UNSEEN',
    human_context_status: 'NOT_REQUESTED',
    memory_status: 'NOT_READY',
  },
  {
    session_id: 'question',
    status: 'NEEDS_HUMAN_RESPONSE',
    analysis_status: 'COMPLETED',
    coach_view_status: 'VIEWED',
    human_context_status: 'AWAITING_RESPONSE',
    memory_status: 'NOT_READY',
  },
  {
    session_id: 'approval',
    status: 'READY_FOR_COACH_APPROVAL',
    analysis_status: 'COMPLETED',
    coach_view_status: 'VIEWED',
    human_context_status: 'RESPONDED',
    memory_status: 'AWAITING_APPROVAL',
  },
  {
    session_id: 'memory',
    status: 'IN_CLUB_MEMORY',
    analysis_status: 'COMPLETED',
    coach_view_status: 'VIEWED',
    human_context_status: 'RESPONDED',
    memory_status: 'APPROVED',
  },
];


test('summarizes operational milestones without collapsing them into one status', () => {
  assert.deepEqual(summarizeSessionInbox(sessions), {
    needsAction: 2,
    awaitingAnalysis: 1,
    viewed: 3,
    inClubMemory: 1,
  });
});


test('maps session states to coach-facing labels and actions', () => {
  assert.equal(sessionStatusLabel('READY_FOR_INVESTIGATION'), 'Ready for investigation');
  assert.equal(sessionStatusLabel('NEEDS_HUMAN_RESPONSE'), 'Needs athlete or coach answer');
  assert.equal(sessionStatusLabel('READY_FOR_COACH_APPROVAL'), 'Ready for coach approval');
  assert.equal(sessionStatusLabel('IN_CLUB_MEMORY'), 'In club memory');
  assert.equal(sessionActionLabel('READY_FOR_INVESTIGATION'), 'Open evidence');
  assert.equal(sessionActionLabel('NEEDS_HUMAN_RESPONSE'), 'Answer question');
  assert.equal(sessionActionLabel('READY_FOR_COACH_APPROVAL'), 'Review briefing');
  assert.equal(sessionActionLabel('IN_CLUB_MEMORY'), 'Open memory');
});
