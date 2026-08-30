import { analyzeOutingEvidence, buildClubPeriodAnalysis } from './club-intelligence.mjs';

const athletes = [
  { athlete_id: 'athlete-lucas', name: 'Lucas', category: 'MEN' },
  { athlete_id: 'athlete-rafael', name: 'Rafael', category: 'MEN' },
  { athlete_id: 'athlete-bruno', name: 'Bruno', category: 'MEN' },
  { athlete_id: 'athlete-diego', name: 'Diego', category: 'MEN' },
  { athlete_id: 'athlete-caio', name: 'Caio', category: 'MEN' },
  { athlete_id: 'athlete-andre', name: 'André', category: 'MEN' },
  { athlete_id: 'athlete-felipe', name: 'Felipe', category: 'MEN' },
  { athlete_id: 'athlete-mateus', name: 'Mateus', category: 'MEN' },
  { athlete_id: 'athlete-marina', name: 'Marina', category: 'WOMEN' },
  { athlete_id: 'athlete-helena', name: 'Helena', category: 'WOMEN' },
  { athlete_id: 'athlete-camila', name: 'Camila', category: 'WOMEN' },
  { athlete_id: 'athlete-julia', name: 'Júlia', category: 'WOMEN' },
  { athlete_id: 'athlete-bianca', name: 'Bianca', category: 'WOMEN' },
  { athlete_id: 'athlete-larissa', name: 'Larissa', category: 'WOMEN' },
  { athlete_id: 'athlete-renata', name: 'Renata', category: 'WOMEN' },
  { athlete_id: 'athlete-sofia', name: 'Sofia', category: 'WOMEN' },
];

const boats = [
  { boat_id: 'boat-2x-aurora', name: 'Aurora', boat_class: '2x' },
  { boat_id: 'boat-2x-iris', name: 'Íris', boat_class: '2x' },
  { boat_id: 'boat-2x-horizon', name: 'Horizon', boat_class: '2x' },
  { boat_id: 'boat-2x-current', name: 'Current', boat_class: '2x' },
  { boat_id: 'boat-4x-atlas', name: 'Atlas', boat_class: '4x' },
  { boat_id: 'boat-4x-gaia', name: 'Gaia', boat_class: '4x' },
  { boat_id: 'boat-4x-mistral', name: 'Mistral', boat_class: '4x' },
  { boat_id: 'boat-4x-dawn', name: 'Dawn', boat_class: '4x' },
  { boat_id: 'boat-8x-north', name: 'North Star', boat_class: '8x' },
  { boat_id: 'boat-8x-south', name: 'South Star', boat_class: '8x' },
  { boat_id: 'boat-1x-spare', name: 'Solitude', boat_class: '1x' },
];

const maleIds = athletes.filter((athlete) => athlete.category === 'MEN').map((athlete) => athlete.athlete_id);
const femaleIds = athletes.filter((athlete) => athlete.category === 'WOMEN').map((athlete) => athlete.athlete_id);

function lineup(ids) {
  return ids.map((athleteId, index) => ({
    athlete_id: athleteId,
    seat: ids.length - index,
    role: index === 0 ? 'STROKE' : index === ids.length - 1 ? 'BOW' : 'CREW',
  }));
}

const crews = [
  { crew_id: 'crew-2x-men', name: 'Harbor Men 2x', boat_class: '2x', category: 'MEN', boat_id: 'boat-2x-aurora', lineup: lineup(['athlete-lucas', 'athlete-rafael']) },
  { crew_id: 'crew-2x-women', name: 'Aurora Women 2x', boat_class: '2x', category: 'WOMEN', boat_id: 'boat-2x-iris', lineup: lineup(['athlete-marina', 'athlete-helena']) },
  { crew_id: 'crew-2x-mixed-a', name: 'Bridge Mixed 2x', boat_class: '2x', category: 'MIXED', boat_id: 'boat-2x-horizon', lineup: lineup(['athlete-bruno', 'athlete-camila']) },
  { crew_id: 'crew-2x-mixed-b', name: 'Current Mixed 2x', boat_class: '2x', category: 'MIXED', boat_id: 'boat-2x-current', lineup: lineup(['athlete-diego', 'athlete-julia']) },
  { crew_id: 'crew-4x-men', name: 'Atlas Men 4x', boat_class: '4x', category: 'MEN', boat_id: 'boat-4x-atlas', lineup: lineup(['athlete-lucas', 'athlete-rafael', 'athlete-bruno', 'athlete-diego']) },
  { crew_id: 'crew-4x-women', name: 'Gaia Women 4x', boat_class: '4x', category: 'WOMEN', boat_id: 'boat-4x-gaia', lineup: lineup(['athlete-marina', 'athlete-helena', 'athlete-camila', 'athlete-julia']) },
  { crew_id: 'crew-4x-mixed-a', name: 'Mistral Mixed 4x', boat_class: '4x', category: 'MIXED', boat_id: 'boat-4x-mistral', lineup: lineup(['athlete-caio', 'athlete-bianca', 'athlete-andre', 'athlete-larissa']) },
  { crew_id: 'crew-4x-mixed-b', name: 'Dawn Mixed 4x', boat_class: '4x', category: 'MIXED', boat_id: 'boat-4x-dawn', lineup: lineup(['athlete-felipe', 'athlete-renata', 'athlete-mateus', 'athlete-sofia']) },
  { crew_id: 'crew-8x-men', name: 'North Men 8x', boat_class: '8x', category: 'MEN', boat_id: 'boat-8x-north', lineup: lineup(maleIds) },
  { crew_id: 'crew-8x-women', name: 'South Women 8x', boat_class: '8x', category: 'WOMEN', boat_id: 'boat-8x-south', lineup: lineup(femaleIds) },
];

const schedules = {
  'crew-2x-men': [['2026-08-17', 'AM'], ['2026-08-19', 'AM'], ['2026-08-24', 'AM'], ['2026-08-27', 'PM']],
  'crew-2x-women': [['2026-08-18', 'AM'], ['2026-08-20', 'AM'], ['2026-08-25', 'AM'], ['2026-08-28', 'PM']],
  'crew-2x-mixed-a': [['2026-08-17', 'PM'], ['2026-08-20', 'PM'], ['2026-08-24', 'PM'], ['2026-08-26', 'PM']],
  'crew-2x-mixed-b': [['2026-08-18', 'PM'], ['2026-08-21', 'PM'], ['2026-08-25', 'PM'], ['2026-08-26', 'PM']],
  'crew-4x-men': [['2026-08-18', 'AM'], ['2026-08-21', 'AM'], ['2026-08-26', 'AM'], ['2026-08-28', 'AM']],
  'crew-4x-women': [['2026-08-17', 'AM'], ['2026-08-19', 'PM'], ['2026-08-24', 'AM'], ['2026-08-27', 'AM']],
  'crew-4x-mixed-a': [['2026-08-19', 'AM'], ['2026-08-21', 'AM'], ['2026-08-25', 'AM'], ['2026-08-28', 'AM']],
  'crew-4x-mixed-b': [['2026-08-18', 'AM'], ['2026-08-20', 'AM'], ['2026-08-27', 'PM'], ['2026-08-28', 'PM']],
  'crew-8x-men': [['2026-08-19', 'EVENING'], ['2026-08-21', 'EVENING'], ['2026-08-26', 'EVENING']],
  'crew-8x-women': [['2026-08-20', 'EVENING'], ['2026-08-25', 'EVENING'], ['2026-08-28', 'EVENING']],
};

const unavailableKeys = new Set([
  'crew-2x-men:2026-08-24',
  'crew-4x-women:2026-08-27',
  'crew-8x-men:2026-08-26',
]);

const evidenceOverridesByKey = {
  'crew-2x-mixed-a:2026-08-20': {
    source_bundle_id: 'club-bridge-mixed-20260820-spm',
    plan: {
      stroke_rate_target: { min_spm: 20, max_spm: 20 },
    },
    speedcoach: {
      work_interval_spm: [
        { segment_id: 'work-01', average_spm: 20 },
        { segment_id: 'work-02', average_spm: 18 },
      ],
    },
  },
  'crew-4x-men:2026-08-28': {
    source_bundle_id: 'club-atlas-men-20260828-recovery',
    plan: {
      planned_recovery_s: { value: 180, tolerance_s: 30 },
    },
    speedcoach: {
      recovery_durations_s: [178, 247, 183],
    },
  },
  'crew-4x-mixed-b:2026-08-27': {
    plan: { linked: false },
  },
  'crew-8x-women:2026-08-28': {
    athlete_context: { required: true, available: false },
  },
};

const planTitles = {
  '2x': ['B0/B2 technical row', '2 × 4 km · rate 20', '6 × 1 km · rate 20', 'B1 endurance · 12 km'],
  '4x': ['B2/B3 · 6 × 1 km', 'B0/B2 technique · 12 km', 'Rate ladder · 18–24 SPM', 'Race pieces · 4 × 2 km'],
  '8x': ['Crew rhythm · B1', 'Race pieces · 4 × 2 km', 'B0/B2 technique · 14 km'],
};

const baseDistance = { '2x': 12000, '4x': 14000, '8x': 16000 };

function buildEvidence(outingId, key) {
  const override = evidenceOverridesByKey[key] ?? {};
  const planLinked = override.plan?.linked ?? true;
  const strokeRateTarget = override.plan?.stroke_rate_target;
  const plannedRecovery = override.plan?.planned_recovery_s;
  const workIntervalSpm = override.speedcoach?.work_interval_spm;
  const recoveryDurations = override.speedcoach?.recovery_durations_s;
  return {
    source_bundle_id: override.source_bundle_id ?? null,
    plan: {
      linked: planLinked,
      source_ref: planLinked ? `${outingId}:plan` : null,
      stroke_rate_target: strokeRateTarget ? {
        ...strokeRateTarget,
        evidence_ref: `${outingId}:plan-spm-target`,
      } : null,
      planned_recovery_s: plannedRecovery ? {
        ...plannedRecovery,
        evidence_ref: `${outingId}:plan-recovery`,
      } : null,
    },
    speedcoach: {
      available: true,
      source_ref: `${outingId}:speedcoach-session`,
      work_interval_spm: workIntervalSpm ? {
        values: workIntervalSpm,
        evidence_ref: `${outingId}:speedcoach-work-spm`,
      } : null,
      recovery_durations_s: recoveryDurations ? {
        values: recoveryDurations,
        evidence_ref: `${outingId}:speedcoach-recovery`,
      } : null,
    },
    athlete_context: {
      required: override.athlete_context?.required ?? false,
      available: override.athlete_context?.available ?? true,
      evidence_ref: `${outingId}:athlete-context-status`,
    },
  };
}

const outings = crews.flatMap((crew) => schedules[crew.crew_id].map(([date, slot], index) => {
  const key = `${crew.crew_id}:${date}`;
  const unavailable = unavailableKeys.has(key);
  const outingId = `outing-${crew.crew_id}-${date}-${slot.toLowerCase()}`;
  return {
    outing_id: outingId,
    crew_id: crew.crew_id,
    boat_id: crew.boat_id,
    date,
    slot,
    plan_title: planTitles[crew.boat_class][index],
    outcome: unavailable ? 'CREW_UNAVAILABLE' : 'COMPLETED',
    distance_m: unavailable ? 0 : baseDistance[crew.boat_class] + ((index % 3) - 1) * 500,
    evidence: unavailable ? null : buildEvidence(outingId, key),
  };
}));

const crewActivities = outings.filter((outing) => outing.outcome === 'COMPLETED').map((outing) => {
  const crew = crews.find((item) => item.crew_id === outing.crew_id);
  const assessment = analyzeOutingEvidence(outing);
  return {
    activity_id: `activity-${outing.outing_id}`,
    outing_id: outing.outing_id,
    date: outing.date,
    slot: outing.slot,
    modality: 'WATER_CREW',
    title: outing.plan_title,
    athlete_ids: crew.lineup.map((seat) => seat.athlete_id),
    crew_id: crew.crew_id,
    boat_id: crew.boat_id,
    distance_m: outing.distance_m,
    review_status: assessment.review_status,
  };
});

const alternateActivities = [
  { activity_id: 'activity-lucas-solo-20260824', outing_id: null, date: '2026-08-24', slot: 'AM', modality: 'WATER_SOLO', title: 'Individual water session after crew cancellation', athlete_ids: ['athlete-lucas'], crew_id: null, boat_id: 'boat-1x-spare', distance_m: 8000, review_status: 'RECORDED_ALTERNATIVE' },
  { activity_id: 'activity-gaia-erg-20260827', outing_id: null, date: '2026-08-27', slot: 'AM', modality: 'ERG', title: 'Ergometer alternative after crew cancellation', athlete_ids: ['athlete-marina', 'athlete-helena'], crew_id: null, boat_id: null, distance_m: 10000, review_status: 'RECORDED_ALTERNATIVE' },
  { activity_id: 'activity-camila-solo-20260827', outing_id: null, date: '2026-08-27', slot: 'AM', modality: 'WATER_SOLO', title: 'Individual water session after crew cancellation', athlete_ids: ['athlete-camila'], crew_id: null, boat_id: 'boat-1x-spare', distance_m: 7000, review_status: 'RECORDED_ALTERNATIVE' },
  { activity_id: 'activity-north-erg-20260826', outing_id: null, date: '2026-08-26', slot: 'EVENING', modality: 'ERG', title: 'Squad ergometer alternative after 8x cancellation', athlete_ids: maleIds.slice(0, 6), crew_id: null, boat_id: null, distance_m: 12000, review_status: 'RECORDED_ALTERNATIVE' },
  { activity_id: 'activity-felipe-solo-20260826', outing_id: null, date: '2026-08-26', slot: 'EVENING', modality: 'WATER_SOLO', title: 'Individual water session after 8x cancellation', athlete_ids: ['athlete-felipe'], crew_id: null, boat_id: 'boat-1x-spare', distance_m: 9000, review_status: 'RECORDED_ALTERNATIVE' },
];

const participationGaps = [
  { date: '2026-08-24', athlete_id: 'athlete-rafael', crew_id: 'crew-2x-men', classification: 'EXPECTED_DAY_WITHOUT_RECORDED_ACTIVITY', statement: 'No completed crew or alternate activity was recorded after the planned 2x became unavailable.' },
  { date: '2026-08-27', athlete_id: 'athlete-julia', crew_id: 'crew-4x-women', classification: 'EXPECTED_DAY_WITHOUT_RECORDED_ACTIVITY', statement: 'No completed crew or alternate activity was recorded after the planned 4x became unavailable.' },
  { date: '2026-08-26', athlete_id: 'athlete-mateus', crew_id: 'crew-8x-men', classification: 'EXPECTED_DAY_WITHOUT_RECORDED_ACTIVITY', statement: 'No completed crew or alternate activity was recorded after the planned 8x became unavailable.' },
];

const investigationResults = [
  {
    case_id: 'club-bridge-mixed-20260820-spm',
    title: 'Bridge Mixed 2x',
    source_bundle_id: 'club-bridge-mixed-20260820-spm',
    status: 'AGENT_COMPLETED',
    verification_passed: true,
    deviation_segment: 'work-02',
    deviation_type: 'SPM_OUTSIDE_TARGET',
    approximate_cost_usd: 0.089806,
    total_tokens: 27963,
    briefing: 'Two work intervals were reconstructed. Work 1 met the 20 SPM target; work 2 averaged 18 SPM and is the only supported execution deviation. Distance completion, environmental cause, technique, and effort remain unestablished.',
    next_step: 'Athlete context requested',
    result_ref: 'evaluation/runs/product-live-bundles/20260830T142519911882Z/outputs/club-bridge-mixed-20260820-spm.json',
  },
  {
    case_id: 'club-atlas-men-20260828-recovery',
    title: 'Atlas Men 4x',
    source_bundle_id: 'club-atlas-men-20260828-recovery',
    status: 'AGENT_COMPLETED',
    verification_passed: true,
    deviation_segment: 'recovery-02',
    deviation_type: 'RECOVERY_DURATION_OUTSIDE_TARGET',
    approximate_cost_usd: 0.104312,
    total_tokens: 32131,
    briefing: 'Four work intervals stayed within the planned 20–22 SPM range. The only supported deviation is recovery-02 at 247 seconds, 67 seconds above the planned maximum. Distance completion and causal explanations remain unestablished.',
    next_step: 'Ready for coach review',
    result_ref: 'evaluation/runs/product-live-bundles/20260830T142616009750Z/outputs/club-atlas-men-20260828-recovery.json',
  },
];

const batchValidation = {
  schema_version: 'wake.demo_club_batch_report.v1',
  status: 'VERIFIED',
  evidence_ref: 'data/demo-club-batch/manifest.json',
  counts: {
    records_received: 40,
    data_validated: 40,
    sessions_reconstructed: 40,
    plan_compared: 39,
    agent_verified: 2,
    human_approved: 0,
  },
  routing: {
    RECONSTRUCTED_NO_MATERIAL_SIGNAL: 31,
    RECONSTRUCTED_ALTERNATIVE: 5,
    AGENT_VERIFIED: 2,
    SOURCE_REQUIRED: 1,
    HUMAN_CONTEXT_REQUIRED: 1,
  },
  longitudinal_synthesis_executed: false,
};

export const demoClub = {
  schema_version: 'wake.demo_club.v1',
  synthetic: true,
  provenance: {
    basis: 'REAL_INFORMED_SYNTHETIC',
    real_inputs: [
      'Coach prescriptions shared as WhatsApp images and a competition-preparation PDF.',
      'SpeedCoach CSV structure and observed timestamp, GPS, distance, pace or speed, and SPM patterns.',
      'WAKE mobile iOS and Android sensor and workout export structures, including missing or failed mobile SPM.',
      'Anonymized Concept2 PM5 detail-screen references covering fixed-distance, fixed-time, and interval workouts.',
      'First-hand club context about attendance, crew changes, boat classes, seats, and alternate training.',
    ],
    fictional_elements: 'Athlete and crew identities, the demo club, physical-boat names, exact outings, outcomes, and aggregate history are fictional.',
    boundary: 'Real-informed means structurally and operationally grounded; it is not statistically representative of rowing clubs or evidence of real athletic performance.',
  },
  club: { club_id: 'wake-demo-club', name: 'WAKE Demo Club' },
  period: {
    start: '2026-08-17',
    end: '2026-08-28',
    weekdays: ['2026-08-17', '2026-08-18', '2026-08-19', '2026-08-20', '2026-08-21', '2026-08-24', '2026-08-25', '2026-08-26', '2026-08-27', '2026-08-28'],
  },
  athletes,
  boats,
  crews,
  outings,
  activities: [...crewActivities, ...alternateActivities],
  participation_gaps: participationGaps,
  investigation_results: investigationResults,
  batch_validation: batchValidation,
};

function maps(club) {
  return {
    athletes: new Map(club.athletes.map((athlete) => [athlete.athlete_id, athlete])),
    boats: new Map(club.boats.map((boat) => [boat.boat_id, boat])),
    crews: new Map(club.crews.map((crew) => [crew.crew_id, crew])),
  };
}

export function listCoachAttention(club) {
  return buildClubPeriodAnalysis(club).attention_signals;
}

export function summarizeClub(club) {
  const completed = club.outings.filter((outing) => outing.outcome === 'COMPLETED');
  return {
    crewCount: club.crews.length,
    athleteCount: club.athletes.length,
    physicalBoatCount: club.boats.length,
    plannedOutings: club.outings.length,
    completedCrewOutings: completed.length,
    disruptedCrewOutings: club.outings.length - completed.length,
    recordedActivities: club.activities.length,
    participationGaps: club.participation_gaps.length,
    attentionCount: listCoachAttention(club).length,
    totalDistanceKm: Math.round(club.activities.reduce((sum, activity) => sum + activity.distance_m, 0) / 100) / 10,
  };
}

export function summarizeCrew(club, crewId) {
  const entities = maps(club);
  const crew = entities.crews.get(crewId);
  if (!crew) throw new RangeError(`Unknown crew: ${crewId}`);
  const outingsForCrew = club.outings.filter((outing) => outing.crew_id === crewId).map((outing) => ({
    ...outing,
    assessment: analyzeOutingEvidence(outing),
  }));
  const completed = outingsForCrew.filter((outing) => outing.outcome === 'COMPLETED');
  return {
    ...crew,
    boat: entities.boats.get(crew.boat_id),
    lineup: crew.lineup.map((seat) => ({ ...seat, athlete: entities.athletes.get(seat.athlete_id) })),
    outings: outingsForCrew,
    plannedOutings: outingsForCrew.length,
    completedOutings: completed.length,
    disruptedOutings: outingsForCrew.length - completed.length,
    attentionCount: outingsForCrew.filter((outing) => outing.assessment.classification !== 'NO_MATERIAL_FLAG_IN_AVAILABLE_EVIDENCE').length,
    distanceKm: Math.round(completed.reduce((sum, outing) => sum + outing.distance_m, 0) / 100) / 10,
  };
}

export function summarizeAthlete(club, athleteId) {
  const entities = maps(club);
  const athlete = entities.athletes.get(athleteId);
  if (!athlete) throw new RangeError(`Unknown athlete: ${athleteId}`);
  const memberships = club.crews.filter((crew) => crew.lineup.some((seat) => seat.athlete_id === athleteId));
  const activityHistory = club.activities.filter((activity) => activity.athlete_ids.includes(athleteId)).sort((left, right) => right.date.localeCompare(left.date));
  const boatIds = [...new Set(activityHistory.map((activity) => activity.boat_id).filter(Boolean))];
  return {
    ...athlete,
    crewIds: memberships.map((crew) => crew.crew_id),
    crews: memberships,
    boats: boatIds.map((boatId) => entities.boats.get(boatId)),
    activityHistory,
    activeDays: new Set(activityHistory.map((activity) => activity.date)).size,
    waterCrewSessions: activityHistory.filter((activity) => activity.modality === 'WATER_CREW').length,
    soloSessions: activityHistory.filter((activity) => activity.modality === 'WATER_SOLO').length,
    ergSessions: activityHistory.filter((activity) => activity.modality === 'ERG').length,
    distanceKm: Math.round(activityHistory.reduce((sum, activity) => sum + activity.distance_m, 0) / 100) / 10,
    participationGaps: club.participation_gaps.filter((gap) => gap.athlete_id === athleteId),
  };
}
