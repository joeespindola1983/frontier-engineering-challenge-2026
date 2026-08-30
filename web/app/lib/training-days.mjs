const slotOrder = { AM: 0, MIDDAY: 1, PM: 2, EVENING: 3 };
const roleOrder = { PRE_WATER: 0, PRIMARY: 1, POST_WATER: 2, ALTERNATIVE: 3 };

function roundKm(distanceM) {
  return Math.round(distanceM / 100) / 10;
}

function classifyDay(activities, hasExpectedGap) {
  if (!activities.length && hasExpectedGap) return 'EXPECTED_MISSING';
  const hasWater = activities.some((activity) => activity.modality.startsWith('WATER'));
  const hasIndoor = activities.some((activity) => activity.modality === 'ERG');
  if (hasWater && hasIndoor) return 'COMBINED';
  if (hasIndoor) return 'INDOOR_ONLY';
  return 'WATER_ONLY';
}

export function buildAthleteTrainingDays(club, athleteId) {
  if (!club.athletes.some((athlete) => athlete.athlete_id === athleteId)) {
    throw new RangeError(`Unknown athlete: ${athleteId}`);
  }
  const activities = club.activities.filter((activity) => activity.athlete_ids.includes(athleteId));
  const gaps = club.participation_gaps.filter((gap) => gap.athlete_id === athleteId);
  const dates = [...new Set([
    ...activities.map((activity) => activity.date),
    ...gaps.map((gap) => gap.date),
  ])].sort((left, right) => right.localeCompare(left));
  const days = dates.map((date) => {
    const dayActivities = activities
      .filter((activity) => activity.date === date)
      .sort((left, right) => {
        const slotDifference = (slotOrder[left.slot] ?? 99) - (slotOrder[right.slot] ?? 99);
        return slotDifference || (roleOrder[left.training_role] ?? 99) - (roleOrder[right.training_role] ?? 99);
      });
    const gap = gaps.find((item) => item.date === date) ?? null;
    const waterDistanceM = dayActivities
      .filter((activity) => activity.modality.startsWith('WATER'))
      .reduce((sum, activity) => sum + activity.distance_m, 0);
    const ergDistanceM = dayActivities
      .filter((activity) => activity.modality === 'ERG')
      .reduce((sum, activity) => sum + activity.distance_m, 0);
    return {
      date,
      classification: classifyDay(dayActivities, Boolean(gap)),
      activities: dayActivities,
      gap,
      waterDistanceKm: roundKm(waterDistanceM),
      ergDistanceKm: roundKm(ergDistanceM),
      recordedDurationS: dayActivities.reduce(
        (sum, activity) => sum + (activity.duration_s ?? activity.erg_metrics?.duration_s ?? 0),
        0,
      ),
    };
  });
  const recorded = activities.length;
  return {
    athleteId,
    days,
    activeDays: days.filter((day) => day.activities.length > 0).length,
    recordedActivities: recorded,
    combinedDays: days.filter((day) => day.classification === 'COMBINED').length,
    indoorOnlyDays: days.filter((day) => day.classification === 'INDOOR_ONLY').length,
    waterOnlyDays: days.filter((day) => day.classification === 'WATER_ONLY').length,
    expectedMissingDays: days.filter((day) => day.classification === 'EXPECTED_MISSING').length,
    waterSessions: activities.filter((activity) => activity.modality.startsWith('WATER')).length,
    ergSessions: activities.filter((activity) => activity.modality === 'ERG').length,
    waterDistanceKm: roundKm(activities
      .filter((activity) => activity.modality.startsWith('WATER'))
      .reduce((sum, activity) => sum + activity.distance_m, 0)),
    ergDistanceKm: roundKm(activities
      .filter((activity) => activity.modality === 'ERG')
      .reduce((sum, activity) => sum + activity.distance_m, 0)),
  };
}

export function buildClubTrainingDaySummary(club) {
  const athleteSummaries = club.athletes.map((athlete) => buildAthleteTrainingDays(club, athlete.athlete_id));
  return {
    athleteDays: athleteSummaries.reduce((sum, athlete) => sum + athlete.days.length, 0),
    activeAthleteDays: athleteSummaries.reduce((sum, athlete) => sum + athlete.activeDays, 0),
    combinedDays: athleteSummaries.reduce((sum, athlete) => sum + athlete.combinedDays, 0),
    indoorOnlyDays: athleteSummaries.reduce((sum, athlete) => sum + athlete.indoorOnlyDays, 0),
    waterOnlyDays: athleteSummaries.reduce((sum, athlete) => sum + athlete.waterOnlyDays, 0),
    expectedMissingDays: athleteSummaries.reduce((sum, athlete) => sum + athlete.expectedMissingDays, 0),
    ergSessions: club.activities.filter((activity) => activity.modality === 'ERG').length,
    waterSessions: club.activities.filter((activity) => activity.modality.startsWith('WATER')).length,
    waterDistanceKm: roundKm(club.activities
      .filter((activity) => activity.modality.startsWith('WATER'))
      .reduce((sum, activity) => sum + activity.distance_m, 0)),
    ergDistanceKm: roundKm(club.activities
      .filter((activity) => activity.modality === 'ERG')
      .reduce((sum, activity) => sum + activity.distance_m, 0)),
  };
}
