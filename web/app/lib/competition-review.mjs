import { demoClub } from './demo-club.mjs';

const distanceRules = {
  JUVENILE: 500,
  BEGINNER: 500,
  ASPIRANT: 1000,
  JUNIOR: 1000,
  MASTER_B: 1000,
  MASTER_C: 1000,
  MASTER_D: 1000,
  MASTER_E: 1000,
  PARA_PR1: 1000,
  PARA_PR2: 1000,
  PARA_PR3: 1000,
  SENIOR: 2000,
};

export function distanceReferenceForCategory(category) {
  const distance = distanceRules[category];
  if (!distance) throw new RangeError(`Unknown competition category: ${category}`);
  return {
    distance_m: distance,
    evidence_status: 'EXACT_CATEGORY_REFERENCE',
    evidence_ref: `regatta-distance-reference:${category.toLowerCase().replaceAll('_', '-')}`,
  };
}

const externalAthletes = [
  ['ext-alice', 'Alice Rocha'], ['ext-amanda', 'Amanda Torres'], ['ext-ana', 'Ana Ribeiro'],
  ['ext-beatriz', 'Beatriz Farias'], ['ext-carolina', 'Carolina Leal'], ['ext-clara', 'Clara Moura'],
  ['ext-daniela', 'Daniela Prado'], ['ext-elisa', 'Elisa Nunes'], ['ext-fernanda', 'Fernanda Vale'],
  ['ext-gabriela', 'Gabriela Luz'], ['ext-isabela', 'Isabela Matos'], ['ext-laura', 'Laura Pires'],
  ['ext-arthur', 'Arthur Braga'], ['ext-benicio', 'Benício Dias'], ['ext-davi', 'Davi Mendes'],
  ['ext-enzo', 'Enzo Martins'], ['ext-gabriel', 'Gabriel Freitas'], ['ext-henrique', 'Henrique Lima'],
  ['ext-joao', 'João Castro'], ['ext-leonardo', 'Leonardo Cruz'], ['ext-marcelo', 'Marcelo Vieira'],
  ['ext-nicolas', 'Nicolas Tavares'], ['ext-pedro', 'Pedro Borges'], ['ext-vitor', 'Vitor Azevedo'],
].map(([athlete_id, name]) => ({ athlete_id, name, synthetic: true }));

const externalClubs = [
  { club_id: 'capital-sculls', name: 'Capital Sculls' },
  { club_id: 'lake-union', name: 'Lake Union RC' },
  { club_id: 'harbor-rowing', name: 'Harbor Rowing' },
];

const eventSpecs = [
  { event_id: 'demo-regatta:r01:2x-men-beginner', race_number: 1, boat_class: '2x', gender: 'MEN', category: 'BEGINNER', label: '2x Men Beginner' },
  { event_id: 'demo-regatta:r01:2x-women-beginner', race_number: 1, boat_class: '2x', gender: 'WOMEN', category: 'BEGINNER', label: '2x Women Beginner' },
  { event_id: 'demo-regatta:r04:2x-mixed-aspirant', race_number: 4, boat_class: '2x', gender: 'MIXED', category: 'ASPIRANT', label: '2x Mixed Aspirant' },
  { event_id: 'demo-regatta:r12:4x-men-master-d', race_number: 12, boat_class: '4x', gender: 'MEN', category: 'MASTER_D', label: '4x Men Master D' },
  { event_id: 'demo-regatta:r12:4x-women-master-d', race_number: 12, boat_class: '4x', gender: 'WOMEN', category: 'MASTER_D', label: '4x Women Master D' },
  { event_id: 'demo-regatta:r13:4x-mixed-master-d', race_number: 13, boat_class: '4x', gender: 'MIXED', category: 'MASTER_D', label: '4x Mixed Master D' },
  { event_id: 'demo-regatta:r14:8x-men-senior', race_number: 14, boat_class: '8x', gender: 'MEN', category: 'SENIOR', label: '8x Men Senior' },
  { event_id: 'demo-regatta:r14:8x-women-senior', race_number: 14, boat_class: '8x', gender: 'WOMEN', category: 'SENIOR', label: '8x Women Senior' },
].map((event) => ({ ...event, ...distanceReferenceForCategory(event.category) }));

const ourResultSpecs = [
  ['crew-2x-men', 'demo-regatta:r01:2x-men-beginner', 2, 109.8, 'FINISHED'],
  ['crew-2x-women', 'demo-regatta:r01:2x-women-beginner', 1, 112.5, 'FINISHED'],
  ['crew-2x-mixed-a', 'demo-regatta:r04:2x-mixed-aspirant', 2, 252.6, 'FINISHED'],
  ['crew-2x-mixed-b', 'demo-regatta:r04:2x-mixed-aspirant', 4, 261.9, 'FINISHED'],
  ['crew-4x-men', 'demo-regatta:r12:4x-men-master-d', 1, 236.8, 'FINISHED'],
  ['crew-4x-women', 'demo-regatta:r12:4x-women-master-d', 3, 248.7, 'FINISHED'],
  ['crew-4x-mixed-a', 'demo-regatta:r13:4x-mixed-master-d', 2, 245.2, 'FINISHED'],
  ['crew-4x-mixed-b', 'demo-regatta:r13:4x-mixed-master-d', null, null, 'NOT_CLASSIFIED'],
  ['crew-8x-men', 'demo-regatta:r14:8x-men-senior', 2, 432.4, 'FINISHED'],
  ['crew-8x-women', 'demo-regatta:r14:8x-women-senior', 1, 441.6, 'FINISHED'],
];

function internalEntry([crewId, eventId, rank, time, status]) {
  const crew = demoClub.crews.find((item) => item.crew_id === crewId);
  return {
    entry_id: `entry:${eventId}:${crewId}`,
    event_id: eventId,
    club_id: demoClub.club.club_id,
    crew_id: crewId,
    crew_label: crew.name,
    athlete_ids: crew.lineup.map((seat) => seat.athlete_id),
    official_rank: rank,
    finish_time_s: time,
    status,
    source_type: 'REAL_INFORMED_SYNTHETIC_RESULT',
  };
}

const opponentResultSpecs = {
  'demo-regatta:r01:2x-men-beginner': [[1, 106.4], [3, 109.8], [4, 116.2]],
  'demo-regatta:r01:2x-women-beginner': [[2, 114.8], [3, 117.4], [4, 121.0]],
  'demo-regatta:r04:2x-mixed-aspirant': [[1, 248.1], [3, 255.4], [5, 267.2]],
  'demo-regatta:r12:4x-men-master-d': [[2, 240.0], [3, 243.1], [4, 247.4]],
  'demo-regatta:r12:4x-women-master-d': [[1, 241.2], [2, 245.0], [4, 253.9]],
  'demo-regatta:r13:4x-mixed-master-d': [[1, 240.1], [3, 250.6], [4, 255.3]],
  'demo-regatta:r14:8x-men-senior': [[1, 425.3], [3, 438.9], [4, 447.2]],
  'demo-regatta:r14:8x-women-senior': [[2, 448.7], [3, 456.2], [4, 463.5]],
};

function externalLineup(eventIndex, opponentIndex, seats) {
  const offset = (eventIndex * 3 + opponentIndex * 5) % externalAthletes.length;
  return Array.from({ length: seats }, (_, seat) => externalAthletes[(offset + seat) % externalAthletes.length].athlete_id);
}

function opponentEntries() {
  return eventSpecs.flatMap((event, eventIndex) => {
    const seats = Number.parseInt(event.boat_class, 10);
    return opponentResultSpecs[event.event_id].map(([rank, time], opponentIndex) => {
      const club = externalClubs[opponentIndex % externalClubs.length];
      return {
        entry_id: `entry:${event.event_id}:${club.club_id}`,
        event_id: event.event_id,
        club_id: club.club_id,
        crew_id: null,
        crew_label: `${club.name} ${String.fromCharCode(65 + opponentIndex)}`,
        athlete_ids: externalLineup(eventIndex, opponentIndex, seats),
        official_rank: rank,
        finish_time_s: time,
        status: 'FINISHED',
        source_type: 'REAL_INFORMED_SYNTHETIC_RESULT',
      };
    });
  });
}

export const demoRegatta = {
  schema_version: 'wake.synthetic_regatta.v1',
  synthetic: true,
  competition: {
    competition_id: 'wake-demo-brasilia-stage-2',
    name: 'Brasília Club Regatta — Synthetic Review',
    organizer: 'Synthetic regional federation',
    stage: 2,
    date: '2026-08-30',
  },
  provenance: {
    basis: 'REAL_INFORMED_SYNTHETIC',
    official_result_reproduced: false,
    inputs: [
      'An official regional regatta programme supplied category-to-distance references.',
      'A separate official regional results document supplied structural patterns for fields, ranks, times, ties, and non-completions.',
      'The WAKE demo club supplied fictional athletes, crews, physical boats, and two weeks of training context.',
    ],
    boundary: 'Competition, clubs, identities, lineups, times, ranks, and outcomes in this fixture are fictional. No real athlete is attached to a fictional training history.',
  },
  distance_reference: {
    status: 'REFERENCE_ONLY',
    series_relationship: 'SAME_FEDERATION_AND_SEASON_REFERENCE',
    caveat: 'The earlier programme supports category distance rules but does not prove the distance used by a different stage.',
  },
  clubs: [demoClub.club, ...externalClubs],
  athletes: [...demoClub.athletes.map((athlete) => ({ ...athlete, synthetic: true })), ...externalAthletes],
  events: eventSpecs,
  entries: [...ourResultSpecs.map(internalEntry), ...opponentEntries()],
};

function median(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[middle] : (sorted[middle - 1] + sorted[middle]) / 2;
}

function round(value, digits = 2) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

function trainingContext(club, crewId, competitionDate) {
  const outings = club.outings.filter((outing) => outing.crew_id === crewId && outing.date < competitionDate);
  const completed = outings.filter((outing) => outing.outcome === 'COMPLETED');
  return {
    shared_outings: completed.length,
    disrupted_outings: outings.length - completed.length,
    shared_distance_m: completed.reduce((total, outing) => total + outing.distance_m, 0),
    last_shared_outing_date: completed.map((outing) => outing.date).sort().at(-1) ?? null,
    interpretation: 'DESCRIPTIVE_CONTEXT_ONLY',
    evidence_refs: completed.map((outing) => `${outing.outing_id}:speedcoach-session`),
  };
}

export function buildCompetitionReview(club, regatta) {
  const clubEntries = regatta.entries.filter((entry) => entry.club_id === club.club.club_id);
  const athleteById = new Map(regatta.athletes.map((athlete) => [athlete.athlete_id, athlete]));
  const clubById = new Map(regatta.clubs.map((item) => [item.club_id, item]));
  const crewById = new Map(club.crews.map((crew) => [crew.crew_id, crew]));
  const boatById = new Map(club.boats.map((boat) => [boat.boat_id, boat]));

  const events = regatta.events.map((event) => {
    const entries = regatta.entries.filter((entry) => entry.event_id === event.event_id);
    const finishers = entries.filter((entry) => entry.status === 'FINISHED');
    const timeCounts = new Map();
    for (const entry of finishers) timeCounts.set(entry.finish_time_s, (timeCounts.get(entry.finish_time_s) ?? 0) + 1);
    return {
      ...event,
      field_size: entries.length,
      finisher_count: finishers.length,
      winning_time_s: finishers.find((entry) => entry.official_rank === 1)?.finish_time_s ?? null,
      median_time_s: median(finishers.map((entry) => entry.finish_time_s)),
      results: [...entries]
        .sort((left, right) => (left.official_rank ?? Number.MAX_SAFE_INTEGER) - (right.official_rank ?? Number.MAX_SAFE_INTEGER))
        .map((entry) => ({
          ...entry,
          club: clubById.get(entry.club_id),
          athletes: entry.athlete_ids.map((athleteId) => athleteById.get(athleteId)),
          official_tie_preserved: entry.finish_time_s !== null && timeCounts.get(entry.finish_time_s) > 1,
        })),
    };
  });
  const eventById = new Map(events.map((event) => [event.event_id, event]));

  const enrichedEntries = clubEntries.map((entry) => {
    const event = eventById.get(entry.event_id);
    const crew = crewById.get(entry.crew_id);
    if (!event || !crew) throw new Error(`Competition entry ${entry.entry_id} has an invalid event or crew link.`);
    const winnerTime = event.winning_time_s;
    const finished = entry.status === 'FINISHED';
    return {
      ...entry,
      event,
      crew,
      boat: boatById.get(crew.boat_id),
      athletes: entry.athlete_ids.map((athleteId) => athleteById.get(athleteId)),
      distance: {
        distance_m: event.distance_m,
        evidence_status: event.evidence_status,
        evidence_ref: event.evidence_ref,
        stage_confirmation: 'NOT_DIRECTLY_OBSERVED',
      },
      pace_500m_s: finished ? round((entry.finish_time_s / event.distance_m) * 500, 1) : null,
      gap_to_winner_s: finished && winnerTime !== null ? round(entry.finish_time_s - winnerTime, 1) : null,
      gap_to_winner_pct: finished && winnerTime !== null ? round(((entry.finish_time_s - winnerTime) / winnerTime) * 100, 2) : null,
      field: {
        field_size: event.field_size,
        finisher_count: event.finisher_count,
        competitor_clubs: [...new Set(event.results.filter((result) => result.club_id !== club.club.club_id).map((result) => result.club.name))],
        winning_time_s: event.winning_time_s,
        median_time_s: event.median_time_s,
      },
      training_context: trainingContext(club, crew.crew_id, regatta.competition.date),
      missing_context: {
        reason_for_non_completion: entry.status === 'NOT_CLASSIFIED',
        race_conditions: true,
        incidents_or_penalties: true,
      },
      next_question: entry.status === 'NOT_CLASSIFIED'
        ? 'What happened before or during this race, and why was the crew not classified?'
        : 'Were there race conditions, incidents, or lineup changes that should contextualize this result?',
      claim_boundaries: {
        performance_cause: 'NOT_ESTABLISHED',
        training_effect: 'NOT_ESTABLISHED',
        crew_selection_recommendation: 'HUMAN_REVIEW_REQUIRED',
      },
    };
  });

  const startsByAthlete = new Map();
  for (const entry of clubEntries) {
    for (const athleteId of entry.athlete_ids) startsByAthlete.set(athleteId, (startsByAthlete.get(athleteId) ?? 0) + 1);
  }

  return {
    schema_version: 'wake.competition_review.v1',
    synthetic: regatta.synthetic,
    provenance: regatta.provenance,
    competition: regatta.competition,
    distance_reference: regatta.distance_reference,
    club: club.club,
    summary: {
      entries: clubEntries.length,
      events_entered: new Set(clubEntries.map((entry) => entry.event_id)).size,
      athletes_entered: startsByAthlete.size,
      multi_start_athletes: [...startsByAthlete.values()].filter((count) => count > 1).length,
      finishers: clubEntries.filter((entry) => entry.status === 'FINISHED').length,
      wins: clubEntries.filter((entry) => entry.official_rank === 1).length,
      podiums: clubEntries.filter((entry) => entry.official_rank !== null && entry.official_rank <= 3).length,
      not_classified: clubEntries.filter((entry) => entry.status === 'NOT_CLASSIFIED').length,
      opponent_clubs: new Set(regatta.entries.filter((entry) => entry.club_id !== club.club.club_id).map((entry) => entry.club_id)).size,
    },
    entries: enrichedEntries,
    events,
    athlete_starts: [...startsByAthlete.entries()].map(([athlete_id, starts]) => ({
      athlete_id,
      athlete: athleteById.get(athlete_id),
      starts,
      entry_ids: clubEntries.filter((entry) => entry.athlete_ids.includes(athlete_id)).map((entry) => entry.entry_id),
    })).sort((left, right) => right.starts - left.starts || left.athlete.name.localeCompare(right.athlete.name)),
  };
}

export const demoCompetitionReview = buildCompetitionReview(demoClub, demoRegatta);
