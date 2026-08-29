import { buildSessionReview } from './replay-adapter.mjs';

const analysis = {
  plan_summary: {
    summary:
      'Planned water session: 6 x 1 km with 3–5 minutes active light-rowing recovery; repetitions 1–3 at 19–21 SPM with a resistance band, then repetitions 4–6 at 22–24 SPM without it.',
  },
  segments: [
    { segment_id: 'work-01', kind: 'WORK', start_offset_s: 5, end_offset_s: 301.092, distance_m: 983.374, average_spm: 20.02, evidence_refs: ['input/speedcoach.csv', 'input/plan.json'] },
    { segment_id: 'work-02', kind: 'WORK', start_offset_s: 546.092, end_offset_s: 842.123, distance_m: 983.24, average_spm: 20.02, evidence_refs: ['input/speedcoach.csv', 'input/plan.json'] },
    { segment_id: 'work-03', kind: 'WORK', start_offset_s: 1087.123, end_offset_s: 1383.262, distance_m: 983.177, average_spm: 19.97, evidence_refs: ['input/speedcoach.csv', 'input/plan.json'] },
    { segment_id: 'work-04', kind: 'WORK', start_offset_s: 1628.262, end_offset_s: 1912.301, distance_m: 981.714, average_spm: 22.99, evidence_refs: ['input/speedcoach.csv', 'input/plan.json'] },
    { segment_id: 'work-05', kind: 'WORK', start_offset_s: 2157.301, end_offset_s: 2489.056, distance_m: 985.032, average_spm: 19.99, evidence_refs: ['input/speedcoach.csv', 'input/plan.json'] },
    { segment_id: 'work-06', kind: 'WORK', start_offset_s: 2734.056, end_offset_s: 3044.648, distance_m: 984.309, average_spm: 22.97, evidence_refs: ['input/speedcoach.csv', 'input/plan.json'] },
  ],
  source_policy: [
    { metric: 'stroke_rate_spm', selected_source_id: 'speedcoach-synthetic', reason: 'SpeedCoach reports SPM; mobile SPM is all zero and is rejected.', evidence_refs: ['input/speedcoach.csv', 'input/mobile.csv'] },
    { metric: 'distance_m', selected_source_id: 'speedcoach-synthetic', reason: 'Mobile cumulative distance has a 1.2% positive bias/conflict relative to SpeedCoach and is rejected for distance.', evidence_refs: ['input/speedcoach.csv', 'input/mobile.csv'] },
    { metric: 'route', selected_source_id: 'speedcoach-synthetic', reason: 'SpeedCoach GPS route is selected and mobile GPS route corroborates close bidirectional overlap.', evidence_refs: ['input/speedcoach.csv', 'input/mobile.csv'] },
    { metric: 'environment_effective_headwind_m_s', selected_source_id: 'synthetic-environment-002', reason: 'The supplied high-quality synthetic environmental timeline is time-aligned to the SpeedCoach session; it supports condition association only.', evidence_refs: ['input/environment.json', 'input/speedcoach.csv'] },
  ],
  claims: [
    {
      claim_id: 'equipment-status',
      status: 'UNKNOWN',
      statement:
        'Resistance-band use for the first three repetitions, and its removal before the final three, cannot be confirmed from the supplied telemetry.',
    },
  ],
  deviations: [
    {
      segment_ref: 'work-05',
      type: 'STROKE_RATE_BELOW_PRESCRIPTION',
    },
  ],
  environment_assessment: {
    association: 'SUPPORTED',
    summary:
      'Effective headwind changed from -1.0 m/s (tailwind by the stated sign convention) at the session start to +5.5 m/s, crossing from tailwind to headwind at about 1,800 seconds. The work-04 to work-05 speed reduction is temporally associated with that shift; this does not establish wind as its cause or establish athlete regression. Work-06 speed increased relative to work-05 despite continuing +5.5 m/s headwind, alongside restored prescribed stroke rate.',
    limitations: [
      'Environmental timing establishes association, not causation.',
      'Changing stroke rate, unobserved effort, equipment status, and other rowing conditions prevent attribution of speed changes to wind or athlete performance.',
    ],
    evidence_refs: ['input/environment.json', 'input/speedcoach.csv'],
  },
  follow_up_questions: [
    'Was the resistance band used for repetitions 1–3 and removed before repetition 4?',
  ],
  abstentions: [
    'No conclusion is made about resistance-band use or removal.',
    'No conclusion is made about technique, crew synchronization, medical state, perceived effort, physiological zone, athlete improvement, or regression.',
    'The reconstructed work distances are segmentation outputs and are not asserted as confirmed shortfalls from the prescribed 1,000 m repetitions.',
  ],
  coach_briefing:
    'Execution matched the planned six-work / five-active-recovery structure and all recoveries met the 3–5 minute target. Rates were on target for repetitions 1–4 and 6; repetition 5 is the material deviation at 19.99 SPM instead of 22–24. A tailwind-to-headwind shift occurred around 30 minutes and is associated with the later speed reduction, but cannot be treated as a causal explanation. Confirm band use before judging execution beyond rate and recovery timing.',
};

const summary = {
  case_id: 'case-002-wind-shift-plan-deviation',
  plan: {
    scheduled_date: '2026-01-20',
    blocks: [
      { repetitions: 3, distance_m: 1000, stroke_rate: { min_spm: 19, max_spm: 21 }, equipment: ['RESISTANCE_BAND'] },
      { repetitions: 3, distance_m: 1000, stroke_rate: { min_spm: 22, max_spm: 24 }, equipment: [] },
    ],
  },
  cross_source_findings: [
    {
      finding_id: 'mobile-clock-offset',
      values: { mobile_from_speedcoach_s: 37 },
    },
  ],
};

const context = {
  input_notice:
    'All people, dates, route coordinates, telemetry, and weather in this case are synthetic.',
  session_candidate: {
    boat_class: 'DOUBLE_SCULL',
    world_rowing_code: '2x',
  },
};

export const demoReview = buildSessionReview({ analysis, summary, context });
