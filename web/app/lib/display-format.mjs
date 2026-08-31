export function formatMeasurementRange(values, unit) {
  if (!values?.length) return 'Not available';
  const formatted = values.map((value) => value.toFixed(1));
  const range = formatted[0] === formatted.at(-1)
    ? formatted[0]
    : `${formatted[0]}–${formatted.at(-1)}`;
  return `${range}${unit === '%' ? '' : ' '}${unit}`;
}

export function formatEvidenceKind(kind) {
  return {
    PLAN: 'Plan',
    SPEEDCOACH: 'SpeedCoach',
    MOBILE: 'Mobile',
    ENVIRONMENT: 'Environment',
    CONTEXT: 'Context',
  }[kind] ?? kind;
}

export function formatAnalysisPeriod(period) {
  const start = new Date(`${period.start}T00:00:00Z`);
  const end = new Date(`${period.end}T00:00:00Z`);
  const dateFormatter = new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
  const dateRange = (start.getTime() === end.getTime()
    ? dateFormatter.format(start)
    : dateFormatter.formatRange(start, end)).replace(/\s*–\s*/u, '–');
  const trainingDays = Array.isArray(period.weekdays) ? period.weekdays.length : 0;
  const dayLabel = trainingDays === 1 ? 'training day' : 'training days';
  return trainingDays ? `${trainingDays} ${dayLabel} · ${dateRange}` : dateRange;
}
