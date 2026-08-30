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
