const weekdays = [
  '2026-09-07', '2026-09-08', '2026-09-09', '2026-09-10', '2026-09-11',
  '2026-09-14', '2026-09-15', '2026-09-16', '2026-09-17', '2026-09-18',
];

const athleteIds = [
  'athlete-lucas', 'athlete-rafael', 'athlete-bruno', 'athlete-diego',
  'athlete-caio', 'athlete-andre', 'athlete-felipe', 'athlete-mateus',
  'athlete-marina', 'athlete-helena', 'athlete-camila', 'athlete-julia',
  'athlete-bianca', 'athlete-larissa', 'athlete-renata', 'athlete-sofia',
];

const crewLineups = {
  'crew-2x-men': ['athlete-lucas', 'athlete-rafael'],
  'crew-2x-women': ['athlete-marina', 'athlete-helena'],
  'crew-2x-mixed-a': ['athlete-bruno', 'athlete-camila'],
  'crew-2x-mixed-b': ['athlete-diego', 'athlete-julia'],
  'crew-4x-men': ['athlete-lucas', 'athlete-rafael', 'athlete-bruno', 'athlete-diego'],
  'crew-4x-women': ['athlete-marina', 'athlete-helena', 'athlete-camila', 'athlete-julia'],
  'crew-4x-mixed-a': ['athlete-caio', 'athlete-bianca', 'athlete-andre', 'athlete-larissa'],
  'crew-4x-mixed-b': ['athlete-felipe', 'athlete-renata', 'athlete-mateus', 'athlete-sofia'],
  'crew-8x-men': ['athlete-lucas', 'athlete-rafael', 'athlete-bruno', 'athlete-diego', 'athlete-caio', 'athlete-andre', 'athlete-felipe', 'athlete-mateus'],
  'crew-8x-women': ['athlete-marina', 'athlete-helena', 'athlete-camila', 'athlete-julia', 'athlete-bianca', 'athlete-larissa', 'athlete-renata', 'athlete-sofia'],
};

const crewIds = Object.keys(crewLineups);
const boatClassDistance = { '2x': 12000, '4x': 14000, '8x': 16000 };

function boatClass(crewId) {
  if (crewId.includes('2x')) return '2x';
  if (crewId.includes('4x')) return '4x';
  return '8x';
}

const waterActivities = crewIds.flatMap((crewId, crewIndex) => [0, 1, 2].map((sessionIndex) => {
  const date = weekdays[(crewIndex * 2 + sessionIndex * 3) % weekdays.length];
  const highWind = crewId === 'crew-4x-men' && sessionIndex === 2;
  const className = boatClass(crewId);
  return {
    activity_id: `post-${crewId}-${date}`,
    date,
    modality: 'WATER_CREW',
    crew_id: crewId,
    athlete_ids: crewLineups[crewId],
    title: sessionIndex === 2 ? 'Post-regatta race pieces' : 'Post-regatta technical endurance',
    distance_m: boatClassDistance[className] + ((crewIndex + sessionIndex) % 3) * 500,
    average_spm: 20 + ((crewIndex + sessionIndex) % 4),
    environment: {
      wind_speed_m_s: highWind ? 7.8 : 1.4 + ((crewIndex + sessionIndex) % 4) * 0.7,
      wind_relation: highWind ? 'TAIL_CROSS' : 'VARIABLE',
      source: 'SYNTHETIC_HISTORICAL_WEATHER_PATTERN',
    },
    evidence_ref: `post-${crewId}-${date}`,
  };
}));

const ergActivities = athleteIds.map((athleteId, index) => ({
  activity_id: `post-${athleteId}-erg-${weekdays[(index + 1) % weekdays.length]}`,
  date: weekdays[(index + 1) % weekdays.length],
  modality: 'ERG',
  athlete_ids: [athleteId],
  title: 'Individual Concept2 post-regatta record',
  workout_type: index % 3 === 0 ? 'FIXED_DISTANCE' : 'FIXED_TIME',
  distance_m: index % 3 === 0 ? 2000 : 6000 + index * 50,
  duration_s: index % 3 === 0 ? 470 + index * 3 : 1800,
  average_pace_500m_s: 117.5 + index * 1.25,
  average_spm: 20 + (index % 6),
  average_watts: 205 - index * 3,
  evidence_ref: `post-${athleteId}-erg-${weekdays[(index + 1) % weekdays.length]}`,
}));

const comparableErgActivities = [
  {
    activity_id: 'post-athlete-lucas-erg-1000m-20260917', date: '2026-09-17', modality: 'ERG',
    athlete_ids: ['athlete-lucas'], title: '1,000 m low-rate technique comparison', workout_type: 'FIXED_DISTANCE',
    distance_m: 1000, duration_s: 246, average_pace_500m_s: 123, average_spm: 12, average_watts: 188,
    evidence_ref: 'post-athlete-lucas-erg-1000m-20260917',
  },
  {
    activity_id: 'post-athlete-bianca-erg-2000m-20260916', date: '2026-09-16', modality: 'ERG',
    athlete_ids: ['athlete-bianca'], title: '2,000 m benchmark comparison', workout_type: 'FIXED_DISTANCE',
    distance_m: 2000, duration_s: 492, average_pace_500m_s: 123, average_spm: 26, average_watts: 188,
    evidence_ref: 'post-athlete-bianca-erg-2000m-20260916',
  },
  {
    activity_id: 'post-athlete-marina-erg-1000m-20260915', date: '2026-09-15', modality: 'ERG',
    athlete_ids: ['athlete-marina'], title: '1,000 m activation comparison', workout_type: 'FIXED_DISTANCE',
    distance_m: 1000, duration_s: 249, average_pace_500m_s: 124.5, average_spm: 18, average_watts: 183,
    evidence_ref: 'post-athlete-marina-erg-1000m-20260915',
  },
  {
    activity_id: 'post-athlete-sofia-erg-interval-20260918', date: '2026-09-18', modality: 'ERG',
    athlete_ids: ['athlete-sofia'], title: '4 × 4 minute interval', workout_type: 'INTERVAL',
    distance_m: 4200, duration_s: 960, average_pace_500m_s: 114.3, average_spm: 27, average_watts: 239,
    evidence_ref: 'post-athlete-sofia-erg-interval-20260918',
  },
];

export const postRegattaPackage = {
  schema_version: 'wake.post_regatta_package.v1',
  package_id: 'wake-demo-club-post-regatta-v1',
  synthetic: true,
  model_called: false,
  load_cost_usd: 0,
  provenance: {
    basis: 'REAL_INFORMED_SYNTHETIC',
    grounded_in: 'Supplied rowing plans, SpeedCoach structures, PM5 reference images, regatta programs and results, and first-hand club operations.',
    fictional_elements: 'Every identity, exact activity, result, environmental condition, and comparison outcome in this package is fictional.',
    boundary: 'The package demonstrates longitudinal product behavior. It is not evidence that a real athlete or crew changed after a regatta.',
  },
  period: { start: weekdays[0], end: weekdays.at(-1), weekdays },
  athlete_ids: athleteIds,
  crew_ids: crewIds,
  activities: [...waterActivities, ...ergActivities, ...comparableErgActivities],
};

export function buildPostRegattaComparison(club, packageData) {
  const crewName = new Map(club.crews.map((crew) => [crew.crew_id, crew.name]));
  const athleteName = new Map(club.athletes.map((athlete) => [athlete.athlete_id, athlete.name]));
  const signals = [
    {
      signal_id: 'post-signal-lucas-faster', scenario: 'OBSERVED_FASTER_COMPARABLE', severity: 'POSITIVE_OBSERVATION',
      entity_name: athleteName.get('athlete-lucas'), label: 'Observed faster',
      statement: 'Lucas completed a comparable 1,000 m low-rate Concept2 record 4 seconds faster than the pre-regatta synthetic reference, at the same 12 SPM.',
      interpretation: 'This is a supported within-workout observation; the package does not establish why the time changed.',
      evidence_refs: ['activity-lucas-erg-20260818', 'post-athlete-lucas-erg-1000m-20260917'],
    },
    {
      signal_id: 'post-signal-bianca-slower', scenario: 'OBSERVED_SLOWER_COMPARABLE', severity: 'REVIEW',
      entity_name: athleteName.get('athlete-bianca'), label: 'Observed slower',
      statement: 'Bianca completed the comparable 2,000 m Concept2 record 12 seconds slower than the pre-regatta synthetic reference, with the same 26 SPM average.',
      interpretation: 'The difference is observed. Fatigue, intent, resistance setting, recovery, and other context remain unknown.',
      evidence_refs: ['activity-bianca-erg-20260824', 'post-athlete-bianca-erg-2000m-20260916'],
    },
    {
      signal_id: 'post-signal-marina-stable', scenario: 'STABLE_RANGE', severity: 'NEUTRAL_OBSERVATION',
      entity_name: athleteName.get('athlete-marina'), label: 'Stable comparable range',
      statement: 'Marina’s comparable 1,000 m activation was within 1 second of the pre-regatta synthetic reference.',
      interpretation: 'The observed values are stable within this narrow comparison; no broader trend is claimed.',
      evidence_refs: ['activity-marina-erg-20260820', 'post-athlete-marina-erg-1000m-20260915'],
    },
    {
      signal_id: 'post-signal-atlas-wind', scenario: 'ENVIRONMENT_CONFOUNDED', severity: 'CONTEXT_REQUIRED',
      entity_name: crewName.get('crew-4x-men'), label: 'Water comparison is weather-confounded',
      statement: 'Atlas Men 4x recorded a different on-water pace pattern during a 7.8 m/s tail-cross wind session.',
      interpretation: 'Environmental context prevents a clean period comparison; the change is not attributed to the crew.',
      evidence_refs: [waterActivities.find((activity) => activity.crew_id === 'crew-4x-men' && activity.environment.wind_speed_m_s === 7.8).activity_id],
    },
    {
      signal_id: 'post-signal-andre-gap', scenario: 'PARTICIPATION_REVIEW', severity: 'HUMAN_CONTEXT',
      entity_name: athleteName.get('athlete-andre'), label: 'Participation needs context',
      statement: 'André has one expected post-regatta training day without an individual or linked crew record.',
      interpretation: 'Ask whether this was rest, absence, unlinked data, or another training modality.',
      evidence_refs: ['post-athlete-andre-expected-20260911'],
    },
    {
      signal_id: 'post-signal-sofia-insufficient', scenario: 'INSUFFICIENT_EVIDENCE', severity: 'BOUNDARY',
      entity_name: athleteName.get('athlete-sofia'), label: 'No equivalent benchmark',
      statement: 'Sofia’s post-regatta interval has no equivalent pre-regatta workout shape in the package.',
      interpretation: 'The result is stored, but a direction-of-change comparison is unsupported.',
      evidence_refs: ['post-athlete-sofia-erg-interval-20260918'],
    },
  ];

  return {
    schema_version: 'wake.post_regatta_comparison.v1',
    analysis_mode: 'DETERMINISTIC_PERIOD_COMPARISON',
    model_called: false,
    analysis_cost_usd: 0,
    causal_conclusion: 'NOT_ESTABLISHED',
    coverage: {
      pre_regatta_activities: club.activities.length,
      post_regatta_activities: packageData.activities.length,
      athletes: packageData.athlete_ids.length,
      crews: packageData.crew_ids.length,
      weekdays: packageData.period.weekdays.length,
    },
    signals,
    boundaries: [
      'A faster or slower comparable result is an observed difference, not proof of physiological change.',
      'Water comparisons remain sensitive to wind, current, crew composition, equipment, and course conditions.',
      'Missing activity records trigger a human question rather than a conclusion about commitment or readiness.',
    ],
  };
}
