import { buildClubPeriodAnalysis } from './club-intelligence.mjs';
import { buildAthleteTrainingDays } from './training-days.mjs';

const OBSERVED_PILOT_COST_PER_START_USD = 0.097059;
const PLANNING_COST_PER_START_USD = 0.15;
const AUTHORIZATION_GATE_PER_START_USD = 0.20;
const OFFICIAL_RUN = {
  execution_count: 4,
  total_cost_usd: 0.110426,
  baseline_cost_usd: 0.06458,
  wake_cost_usd: 0.045846,
  wake_vs_baseline_percent: -29.01,
  baseline_tokens: 15035,
  wake_tokens: 8238,
  wake_tool_events: 16,
};

function roundUsd(value) {
  return Math.round((value + Number.EPSILON) * 1_000_000) / 1_000_000;
}

export function buildLongitudinalPilot(club) {
  const period = buildClubPeriodAnalysis(club);
  const lucas = buildAthleteTrainingDays(club, 'athlete-lucas');
  const cases = [
    {
      pilot_id: 'athlete-lucas',
      scope_type: 'ATHLETE',
      title: 'Athlete briefing',
      subject: 'Lucas · two-week training history',
      why_model_is_used: 'Connect crew, solo, Concept2, attendance, and one verified crew-session exception while preserving incompatible modality boundaries.',
      deterministic_coverage: `${lucas.recordedActivities} activities · ${lucas.activeDays} active days`,
      comparison_status: 'No performance trend supported',
      result_summary: 'Both workflows found the verified recovery deviation and abstained from a performance trend. WAKE returned the narrower review path.',
      required_tools: ['Scope coverage', 'Attention signals', 'Comparable sessions', 'Verified investigations'],
    },
    {
      pilot_id: 'club-coach',
      scope_type: 'CLUB',
      title: 'Club briefing',
      subject: `${club.club.name} · coach priority queue`,
      why_model_is_used: 'Synthesize the complete deterministic screen into an evidence-ranked review order without paying to narrate every clean record.',
      deterministic_coverage: `${period.coverage.activities_scanned} activities · ${period.attention_signals.length} attention signals`,
      comparison_status: 'Prioritization only · no athlete ranking',
      result_summary: 'Both workflows found the missing source, athlete-context request, and two verified deviations in the same review order.',
      required_tools: ['Scope coverage', 'Attention signals', 'Comparable sessions', 'Verified investigations'],
    },
  ];
  const totalPaidStarts = cases.length * 2;
  return {
    schema_version: 'wake.longitudinal_pilot.v1',
    status: 'COMPLETED',
    model_called: true,
    model: 'gpt-5.6-terra',
    reasoning_effort: 'medium',
    cases,
    execution_plan: {
      baseline_calls: cases.length,
      wake_calls: cases.length,
      total_paid_starts: totalPaidStarts,
      observed_projection_usd: roundUsd(totalPaidStarts * OBSERVED_PILOT_COST_PER_START_USD),
      planning_projection_usd: roundUsd(totalPaidStarts * PLANNING_COST_PER_START_USD),
      authorization_gate_total_usd: roundUsd(totalPaidStarts * AUTHORIZATION_GATE_PER_START_USD),
      provider_cap: false,
    },
    saved_reports: {
      count: OFFICIAL_RUN.execution_count,
      reopen_cost_usd: 0,
      status: 'VERIFIED',
    },
    observed: OFFICIAL_RUN,
    evaluation: {
      comparison: 'DIRECT_BASELINE_VS_WAKE_BOUNDED_AGENT',
      same_inputs: true,
      same_model: true,
      same_output_schema: true,
      all_reports_verified: true,
      quality_score: null,
      quality_conclusion: 'NO_DEMONSTRATED_QUALITY_GAIN',
      design: 'POST_RUN_CAPABILITY_AUDIT_NOT_PREREGISTERED',
      primary_checks: ['Evidence coverage', 'Unsupported claims', 'Useful prioritization', 'Required abstention'],
    },
    boundaries: [
      'No performance trend is supported by this pilot preflight.',
      'Water and indoor volume remain separate.',
      'Both workflows passed the same capability checks; no quality improvement is claimed.',
      'The post-run audit has no weighted quality score because one was not frozen before execution.',
      'Reopening a saved result must not call the model again.',
    ],
  };
}
