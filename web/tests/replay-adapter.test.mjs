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
  assert.equal(review.checkpoint.expectedRespondentRole, 'ATHLETE');
  assert.equal(review.checkpoint.authorityScope, 'SESSION_EXECUTION');
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

test('adapts a different uploaded plan, boat, sources, and missing environment', () => {
  const summary = {
    case_id: 'uploaded-womens-single-500s',
    plan: {
      scheduled_date: '2026-08-30',
      source: { kind: 'COACH_UPLOAD' },
      blocks: [
        {
          kind: 'WORK',
          repetitions: 4,
          distance_m: 500,
          stroke_rate: { min_spm: 26, max_spm: 28 },
          equipment: [],
        },
      ],
    },
    sources: [
      { source_id: 'source-speedcoach-a1', kind: 'SPEEDCOACH' },
      { source_id: 'source-mobile-b2', kind: 'MOBILE' },
    ],
    cross_source_findings: [],
    environment: null,
  };
  const context = {
    input_notice: 'Coach-uploaded local evidence.',
    session_candidate: {
      boat_class: 'SINGLE_SCULL',
      world_rowing_code: '1x',
      crew_category: 'WOMEN',
    },
  };
  const analysis = {
    plan_summary: {
      status: 'PARSED',
      summary: 'Four 500 m work intervals at 26–28 SPM.',
    },
    segments: Array.from({ length: 4 }, (_, index) => ({
      segment_id: `work-${String(index + 1).padStart(2, '0')}`,
      kind: 'WORK',
      start_offset_s: index * 180,
      end_offset_s: index * 180 + 120,
      distance_m: 500,
      average_spm: index === 2 ? 24 : 27,
      evidence_refs: ['input/speedcoach.csv', 'input/plan.json'],
    })),
    source_policy: [
      { metric: 'stroke_rate_spm', selected_source_id: 'source-speedcoach-a1', reason: 'SPM is available.', evidence_refs: ['input/speedcoach.csv'] },
      { metric: 'distance_m', selected_source_id: 'source-speedcoach-a1', reason: 'Distance is selected.', evidence_refs: ['input/speedcoach.csv'] },
      { metric: 'route', selected_source_id: 'source-speedcoach-a1', reason: 'Mobile corroborates the route.', evidence_refs: ['input/speedcoach.csv', 'input/mobile.csv'] },
    ],
    claims: [],
    deviations: [
      { segment_ref: 'work-03', type: 'STROKE_RATE_BELOW_PRESCRIPTION' },
    ],
    environment_assessment: null,
    follow_up_questions: ['What was the athlete perceived effort?'],
    abstentions: ['No technique conclusion is made.'],
    coach_briefing: 'Three intervals met the target; work three was below it.',
  };

  const review = buildSessionReview({ analysis, summary, context });

  assert.equal(review.title, "4 × 500 m · Women's 1x");
  assert.equal(review.provenance, 'UPLOADED');
  assert.equal(review.workIntervals.length, 4);
  assert.equal(review.workIntervals[2].status, 'DEVIATION');
  assert.equal(review.sourcePolicy.strokeRate.selectedSource, 'SpeedCoach');
  assert.equal(review.sourcePolicy.route.corroboratedBy, 'Mobile');
  assert.equal(review.sourcePolicy.environment.selectedSource, 'No source selected');
  assert.equal(review.environment.association, 'UNKNOWN');
  assert.match(review.environment.summary, /not supplied|not available/i);
  assert.equal(review.mobileClockOffsetS, null);
  assert.equal(review.checkpoint.question, analysis.follow_up_questions[0]);
  assert.equal(review.currentReconstruction, analysis.coach_briefing);
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

test('preserves an unanswered checkpoint as explicit human-context unknown', () => {
  const briefing = resolveCheckpoint(demoReview, 'UNKNOWN');

  assert.equal(briefing.verificationStatus, 'VERIFIED');
  assert.equal(briefing.humanConfirmation.status, 'UNKNOWN');
  assert.equal(briefing.humanConfirmation.value, null);
  assert.equal(briefing.humanConfirmation.question, demoReview.checkpoint.question);
  assert.match(briefing.humanConfirmation.statement, /no human confirmation/i);
  assert.equal(briefing.pendingApproval, true);
});

test('records an athlete answer with explicit provenance without rewriting telemetry', () => {
  const briefing = resolveCheckpoint(demoReview, {
    answer: 'YES',
    answeredByRole: 'ATHLETE',
    recordedByRole: 'ATHLETE',
    authorityBasis: 'DIRECT_PARTICIPANT',
  });

  assert.equal(briefing.humanConfirmation.status, 'HUMAN_CONFIRMED');
  assert.equal(briefing.humanConfirmation.value, true);
  assert.equal(briefing.humanConfirmation.source, 'Athlete direct confirmation');
  assert.equal(briefing.humanConfirmation.expectedRespondentRole, 'ATHLETE');
  assert.equal(briefing.humanConfirmation.answeredByRole, 'ATHLETE');
  assert.equal(briefing.humanConfirmation.recordedByRole, 'ATHLETE');
  assert.equal(briefing.humanConfirmation.authorityBasis, 'DIRECT_PARTICIPANT');
  assert.equal(briefing.humanConfirmation.matchesExpectedRespondent, true);
  assert.deepEqual(briefing.workIntervals, demoReview.workIntervals);
  assert.deepEqual(briefing.environment, demoReview.environment);
});

test('adds memory only after explicit briefing approval', () => {
  const briefing = resolveCheckpoint(demoReview, {
    answer: 'NO',
    answeredByRole: 'ATHLETE',
    recordedByRole: 'ATHLETE',
    authorityBasis: 'DIRECT_PARTICIPANT',
  });
  const unchanged = approveBriefingMemory(briefing, false);
  const approved = approveBriefingMemory(briefing, true);

  assert.equal(unchanged.approvedSessions.length, 0);
  assert.equal(approved.approvedSessions.length, 1);
  assert.equal(approved.approvedSessions[0].approval, 'COACH_APPROVED');
  assert.equal(approved.approvedSessions[0].humanConfirmation.value, false);
  assert.match(approved.currentConclusion, /does not establish a longitudinal trend/i);
});

test('checkpoint and memory copy follow a different review instead of the demo case', () => {
  const review = {
    ...demoReview,
    sessionId: 'uploaded-short-rate',
    title: "2 × 500 m · Women's 1x",
    coachBriefing: 'Two intervals reconstructed; work two was below target.',
    workIntervals: [
      { ...demoReview.workIntervals[0], index: 1, averageSpm: 26, plannedDistanceM: 500, targetMinSpm: 25, targetMaxSpm: 27, status: 'WITHIN_RANGE' },
      { ...demoReview.workIntervals[1], index: 2, averageSpm: 23, plannedDistanceM: 500, targetMinSpm: 25, targetMaxSpm: 27, status: 'DEVIATION' },
    ],
    environment: {
      association: 'UNKNOWN',
      summary: 'No environmental timeline was supplied.',
      limitations: [],
      evidenceRefs: [],
    },
    abstentions: ['No technique conclusion is made.'],
    checkpoint: {
      ...demoReview.checkpoint,
      question: 'Did an equipment malfunction affect work interval two?',
    },
  };

  const briefing = resolveCheckpoint(review, {
    answer: 'YES',
    answeredByRole: 'ATHLETE',
    recordedByRole: 'COACH',
    authorityBasis: 'RELAYED_REPORT',
  });
  const memory = approveBriefingMemory(briefing, true);
  const serialized = JSON.stringify({ briefing, memory }).toLowerCase();

  assert.match(briefing.headline, /2 work intervals reconstructed/);
  assert.match(briefing.headline, /1 plan deviation needs coach review/);
  assert.equal(briefing.humanConfirmation.question, review.checkpoint.question);
  assert.doesNotMatch(serialized, /resistance-band|work interval five|all six/);
});
