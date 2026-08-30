export const STROKE_RATE_DOMAIN = Object.freeze({ min: 16, max: 26 });

function positionPercent(value) {
  const { min, max } = STROKE_RATE_DOMAIN;
  return Math.max(0, Math.min(100, ((value - min) / (max - min)) * 100));
}

export function buildStrokeRateGeometry({
  averageSpm,
  targetMinSpm,
  targetMaxSpm,
}) {
  const targetBottomPercent = positionPercent(targetMinSpm);
  const targetTopPercent = positionPercent(targetMaxSpm);
  return {
    measuredPercent: positionPercent(averageSpm),
    targetBottomPercent,
    targetHeightPercent: Math.max(0, targetTopPercent - targetBottomPercent),
  };
}
