import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

import { evaluationResults } from '../app/lib/evaluation-results.mjs';


test('committed evaluation summary exposes official scores without private evidence', () => {
  assert.equal(evaluationResults.comparison.case_count, 10);
  assert.equal(evaluationResults.comparison.baseline_score, 49);
  assert.equal(evaluationResults.comparison.wake_score, 83.76);
  assert.equal(evaluationResults.comparison.absolute_gain, 34.76);
  assert.equal(evaluationResults.cost.total_usd, 1.139688);
  assert.equal(evaluationResults.cases.length, 10);
  assert.equal(evaluationResults.agent_observability.tool_calls, 40);
  assert.equal(evaluationResults.agent_observability.verifier_retries, 5);
  assert.ok(evaluationResults.cases.every((item) => item.wake_score > item.baseline_score));
  assert.ok(evaluationResults.cases.every((item) => item.scenario.length > 0));
  assert.ok(evaluationResults.cases.every((item) => item.dimensions.length > 0));
  assert.doesNotMatch(JSON.stringify(evaluationResults), /ground_truth|coach_briefing|input\//);
  assert.doesNotMatch(JSON.stringify(evaluationResults), /evidence_refs|reasons/);
  assert.equal(evaluationResults.club_memory_comparison.baseline.passed_count, 3);
  assert.equal(evaluationResults.club_memory_comparison.wake.passed_count, 7);
  assert.equal(evaluationResults.club_memory_comparison.baseline.cost_usd, 0.0437);
  assert.equal(evaluationResults.club_memory_comparison.wake.cost_usd, 0.037384);
  assert.equal(evaluationResults.club_memory_comparison.accepted_claim, 'STRUCTURAL_FIDELITY_GAIN_ONLY');
  assert.equal(evaluationResults.club_memory_comparison.semantic_quality_gain, false);
  assert.equal(evaluationResults.club_memory_comparison.reopen_cost_usd, 0);
});


test('evaluation is a separate read-only submission evidence view', async () => {
  const page = await readFile(new URL('../app/page.tsx', import.meta.url), 'utf8');

  assert.match(page, /type Screen = .*'evaluation'/);
  assert.match(page, />Evaluation</);
  assert.match(page, /function EvaluationScreen/);
  assert.match(page, /Saved result · No model call/);
  assert.match(page, /Same model, same ten case summaries, same output schema/);
  assert.match(page, /Environmental interpretation/);
  assert.match(page, /comparison\.wake_score/);
  assert.match(page, /comparison\.baseline_score/);
  assert.match(page, /View evaluation results/);
  assert.match(page, /Consolidated official evaluation/);
  assert.match(page, /<details className="case-report"/);
  assert.match(page, /Open individual report/);
  assert.match(page, /item\.dimensions\.map/);
  assert.match(page, /Structured contract fidelity/);
  assert.match(page, /clubMemory\.wake\.passed_count/);
  assert.match(page, /clubMemory\.baseline\.passed_count/);
  assert.match(page, /not a semantic coaching-quality score/);
});
