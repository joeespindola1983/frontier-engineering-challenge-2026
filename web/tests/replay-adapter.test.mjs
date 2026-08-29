import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { buildSessionReview } from '../app/lib/replay-adapter.mjs';
import { demoReview } from '../app/lib/demo-review.mjs';
import {
  approveBriefingMemory,
  resolveCheckpoint,
} from '../app/lib/workflow-state.mjs';

async function readJson(relativePath) {
  return JSON.parse(
    await readFile(new URL(relativePath, import.meta.url), 'utf8'),
  );
}

test('builds the coach review from committed public evidence', async () => {
  const [analysis, summary, context] = await Promise.all([
    readJson(
      '../../evaluation/runs/comparison-v1-20260829/agent/outputs/case-002-wind-shift-plan-deviation.json',
    ),
    readJson(
      '../../evaluation/baseline-inputs/v1/case-002-wind-shift-plan-deviation.json',
    ),
    readJson(
      '../../data/fixtures/case-002-wind-shift-plan-deviation/input/context.json',
    ),
  ]);

  const review = buildSessionReview({ analysis, summary, context });

  assert.equal(review.sessionId, 'case-002-wind-shift-plan-deviation');
  assert.equal(review.title, "6 × 1 km · Men's 2x");
  assert.equal(review.provenance, 'SYNTHETIC');
  assert.equal(review.workIntervals.length, 6);
  assert.equal(review.workIntervals[4].segmentId, 'work-05');
  assert.equal(review.workIntervals[4].status, 'DEVIATION');
  assert.equal(review.workIntervals[4].averageSpm, 19.99);
  assert.equal(review.checkpoint.question, analysis.follow_up_questions[0]);
  assert.equal(review.sourcePolicy.strokeRate.selectedSource, 'SpeedCoach');
  assert.equal(review.sourcePolicy.route.corroboratedBy, 'Mobile');
});

test('keeps environmental language associative rather than causal', async () => {
  const [analysis, summary, context] = await Promise.all([
    readJson(
      '../../evaluation/runs/comparison-v1-20260829/agent/outputs/case-002-wind-shift-plan-deviation.json',
    ),
    readJson(
      '../../evaluation/baseline-inputs/v1/case-002-wind-shift-plan-deviation.json',
    ),
    readJson(
      '../../data/fixtures/case-002-wind-shift-plan-deviation/input/context.json',
    ),
  ]);

  const review = buildSessionReview({ analysis, summary, context });
  const environmentalCopy = review.environment.summary.toLowerCase();

  assert.match(environmentalCopy, /associated/);
  assert.match(environmentalCopy, /does not establish.*cause|not caus/);
  assert.doesNotMatch(environmentalCopy, /wind.*explains/);
});

test('ships a compact replay that stays faithful to the committed run', async () => {
  const [analysis, summary, context] = await Promise.all([
    readJson(
      '../../evaluation/runs/comparison-v1-20260829/agent/outputs/case-002-wind-shift-plan-deviation.json',
    ),
    readJson(
      '../../evaluation/baseline-inputs/v1/case-002-wind-shift-plan-deviation.json',
    ),
    readJson(
      '../../data/fixtures/case-002-wind-shift-plan-deviation/input/context.json',
    ),
  ]);
  const committedReview = buildSessionReview({ analysis, summary, context });

  assert.deepEqual(demoReview.workIntervals, committedReview.workIntervals);
  assert.deepEqual(demoReview.sourcePolicy, committedReview.sourcePolicy);
  assert.deepEqual(demoReview.environment, committedReview.environment);
  assert.equal(demoReview.checkpoint.question, committedReview.checkpoint.question);
});

test('preserves an unanswered equipment checkpoint as an explicit unknown', () => {
  const briefing = resolveCheckpoint(demoReview, 'UNKNOWN');

  assert.equal(briefing.verificationStatus, 'VERIFIED');
  assert.equal(briefing.equipment.status, 'UNKNOWN');
  assert.equal(briefing.equipment.value, null);
  assert.match(briefing.equipment.statement, /cannot be confirmed/i);
  assert.equal(briefing.pendingApproval, true);
});

test('records a coach answer as human confirmation without rewriting telemetry', () => {
  const briefing = resolveCheckpoint(demoReview, 'YES');

  assert.equal(briefing.equipment.status, 'HUMAN_CONFIRMED');
  assert.equal(briefing.equipment.value, true);
  assert.equal(briefing.equipment.source, 'Coach confirmation');
  assert.deepEqual(briefing.workIntervals, demoReview.workIntervals);
  assert.deepEqual(briefing.environment, demoReview.environment);
});

test('adds memory only after explicit briefing approval', () => {
  const briefing = resolveCheckpoint(demoReview, 'NO');
  const unchanged = approveBriefingMemory(briefing, false);
  const approved = approveBriefingMemory(briefing, true);

  assert.equal(unchanged.approvedSessions.length, 0);
  assert.equal(approved.approvedSessions.length, 1);
  assert.equal(approved.approvedSessions[0].approval, 'COACH_APPROVED');
  assert.equal(approved.approvedSessions[0].equipment.value, false);
  assert.match(approved.currentConclusion, /does not establish a longitudinal trend/i);
});
