import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { buildClubPeriodAnalysis } from '../app/lib/club-intelligence.mjs';
import { demoClub } from '../app/lib/demo-club.mjs';


test('screens every recorded activity without calling a model', () => {
  const analysis = buildClubPeriodAnalysis(demoClub);

  assert.equal(analysis.schema_version, 'wake.club_period_analysis.v1');
  assert.equal(analysis.analysis_mode, 'DETERMINISTIC_SCREEN');
  assert.equal(analysis.model_called, false);
  assert.equal(analysis.coverage.activities_scanned, 40);
  assert.equal(analysis.coverage.water_crew_sessions_scanned, 35);
  assert.equal(analysis.coverage.alternate_activities_scanned, 5);
  assert.equal(analysis.coverage.planned_outings_scanned, 38);
  assert.equal(analysis.coverage.compact_evidence_summaries, 35);
  assert.equal(analysis.coverage.linked_plans, 34);
  assert.equal(analysis.coverage.complete_source_bundles, 2);
  assert.equal(analysis.activity_assessments.length, demoClub.activities.length);
  assert.equal(analysis.deterministic_analysis_cost_usd, 0);
  assert.deepEqual(analysis.batch_validation.counts, {
    records_received: 40,
    data_validated: 40,
    sessions_reconstructed: 40,
    plan_compared: 39,
    agent_verified: 2,
    human_approved: 0,
  });
  assert.equal(analysis.batch_validation.routing.RECONSTRUCTED_ALTERNATIVE, 5);
  assert.equal(analysis.batch_validation.routing.SOURCE_ADAPTER_REQUIRED, undefined);
  assert.equal(analysis.batch_validation.longitudinal_synthesis_executed, false);
});


test('derives session findings from observations with evidence references', () => {
  const analysis = buildClubPeriodAnalysis(demoClub);
  const findings = analysis.attention_signals.filter((signal) => signal.kind === 'SESSION_FINDING');

  assert.deepEqual(findings.map((signal) => signal.code).sort(), [
    'ATHLETE_CONTEXT_PENDING',
    'EXCESS_RECOVERY',
    'PLAN_NOT_LINKED',
    'SPM_BELOW_PLAN',
  ]);
  assert.ok(findings.every((signal) => signal.evidence_refs.length > 0));

  const spm = findings.find((signal) => signal.code === 'SPM_BELOW_PLAN');
  assert.equal(spm.route, 'AGENT_INVESTIGATION');
  assert.match(spm.statement, /work-02/);
  assert.match(spm.statement, /18 SPM/);
  assert.ok(spm.evidence_refs.some((ref) => ref.endsWith(':plan-spm-target')));
  assert.ok(spm.evidence_refs.some((ref) => ref.endsWith(':speedcoach-work-spm')));

  const recovery = findings.find((signal) => signal.code === 'EXCESS_RECOVERY');
  assert.equal(recovery.route, 'AGENT_INVESTIGATION');
  assert.match(recovery.statement, /247 seconds/);

  const plan = findings.find((signal) => signal.code === 'PLAN_NOT_LINKED');
  assert.equal(plan.route, 'SOURCE_REQUEST');

  const context = findings.find((signal) => signal.code === 'ATHLETE_CONTEXT_PENDING');
  assert.equal(context.route, 'ATHLETE_QUESTION');
});


test('routes ten attention signals without paying for human or source gaps', () => {
  const analysis = buildClubPeriodAnalysis(demoClub);

  assert.equal(analysis.attention_signals.length, 10);
  assert.deepEqual(analysis.routing, {
    AGENT_INVESTIGATION: 2,
    ATHLETE_QUESTION: 1,
    HUMAN_CONTEXT: 6,
    SOURCE_REQUEST: 1,
  });
  assert.equal(analysis.deep_investigations.completed, 2);
  assert.equal(analysis.deep_investigations.queued, 2);
  assert.equal(analysis.deep_investigations.pending, 0);
  assert.equal(analysis.deep_investigations.status, 'COMPLETED');
  assert.ok(analysis.deep_investigations.queue.every((signal) => signal.source_bundle_id));
  assert.equal(analysis.deep_investigations.results.length, 2);
  assert.ok(analysis.deep_investigations.results.every((result) => result.verification_passed));
  assert.equal(analysis.longitudinal_synthesis.status, 'NOT_EXECUTED');
  assert.equal(analysis.cost_observed.execution_count, 2);
  assert.equal(analysis.cost_observed.approximate_total_cost_usd, 0.194118);
  assert.equal(analysis.cost_observed.total_tokens, 60094);
  assert.ok(analysis.deep_investigations.results.every((result) => result.result_ref));
  assert.equal(analysis.cost_forecast.paid_executions, 1);
  assert.equal(analysis.cost_forecast.observed_projection_usd, 0.071152);
  assert.equal(analysis.cost_forecast.planning_projection_usd, 0.15);
  assert.equal(analysis.cost_forecast.authorization_gate_total_usd, 0.2);
});


test('does not present a clean deterministic screen as proven plan compliance', () => {
  const analysis = buildClubPeriodAnalysis(demoClub);
  const clean = analysis.outing_assessments.filter((assessment) => assessment.classification === 'NO_MATERIAL_FLAG_IN_AVAILABLE_EVIDENCE');

  assert.ok(clean.length > 0);
  assert.ok(clean.every((assessment) => !/executed as planned/i.test(assessment.statement)));
  assert.ok(analysis.boundaries.some((boundary) => /not a longitudinal agent conclusion/i.test(boundary)));
});


test('club evidence stores observations rather than prefilled findings', async () => {
  const source = await readFile(new URL('../app/lib/demo-club.mjs', import.meta.url), 'utf8');

  assert.doesNotMatch(source, /findingByKey/);
  assert.ok(demoClub.outings.filter((outing) => outing.outcome === 'COMPLETED').every((outing) => outing.evidence));
  assert.ok(demoClub.outings.every((outing) => !Object.hasOwn(outing, 'finding')));
});


test('interface exposes screening coverage, queued intelligence, cost, and the no-model boundary', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');

  assert.match(page, /buildClubPeriodAnalysis/);
  assert.match(page, /Deterministic scan complete/);
  assert.match(page, /Two bounded investigations completed/);
  assert.match(page, /Longitudinal synthesis has not run/);
  assert.match(page, /cost_observed\.approximate_total_cost_usd/);
  assert.match(page, /Verified investigation results/);
  assert.match(page, /Two-week validation funnel/);
  assert.match(page, /Data validated/);
  assert.match(page, /Plan compared/);
  assert.match(page, /Human approved/);
  assert.match(page, /40 sessions reconstructed/);
  assert.match(page, /2 synthetic Concept2 transcription records/);
  assert.match(page, /result\.briefing/);
  assert.doesNotMatch(page, /Executed as planned/);
});
