import { buildClubPeriodAnalysis } from './club-intelligence.mjs';
import { buildAthleteTrainingDays } from './training-days.mjs';

const OBSERVED_PILOT_COST_PER_START_USD = 0.097059;
const PLANNING_COST_PER_START_USD = 0.15;
const AUTHORIZATION_GATE_PER_START_USD = 0.20;

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
      required_tools: ['Scope coverage', 'Attention signals', 'Comparable sessions', 'Verified investigations'],
    },
  ];
  const totalPaidStarts = cases.length * 2;
  return {
    schema_version: 'wake.longitudinal_pilot.v1',
    status: 'READY_FOR_AUTHORIZATION',
    model_called: false,
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
      count: 0,
      reopen_cost_usd: 0,
      status: 'NOT_EXECUTED',
    },
    evaluation: {
      comparison: 'DIRECT_BASELINE_VS_WAKE_BOUNDED_AGENT',
      same_inputs: true,
      same_model: true,
      same_output_schema: true,
      primary_checks: ['Evidence coverage', 'Unsupported claims', 'Useful prioritization', 'Required abstention'],
    },
    boundaries: [
      'No performance trend is supported by this pilot preflight.',
      'Water and indoor volume remain separate.',
      'Four paid starts require a new explicit US$0.80 authorization; this is not a provider cap.',
      'Reopening a saved result must not call the model again.',
    ],
  };
}
