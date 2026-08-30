import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildStrokeRateGeometry,
  STROKE_RATE_DOMAIN,
} from '../app/lib/chart-scale.mjs';


test('stroke-rate chart positions each prescribed range on one shared scale', () => {
  assert.deepEqual(STROKE_RATE_DOMAIN, { min: 16, max: 26 });

  const lowRate = buildStrokeRateGeometry({
    averageSpm: 20,
    targetMinSpm: 19,
    targetMaxSpm: 21,
  });
  const highRate = buildStrokeRateGeometry({
    averageSpm: 23,
    targetMinSpm: 22,
    targetMaxSpm: 24,
  });

  assert.deepEqual(lowRate, {
    measuredPercent: 40,
    targetBottomPercent: 30,
    targetHeightPercent: 20,
  });
  assert.deepEqual(highRate, {
    measuredPercent: 70,
    targetBottomPercent: 60,
    targetHeightPercent: 20,
  });
  assert.ok(highRate.targetBottomPercent > lowRate.targetBottomPercent);
});

test('stroke-rate chart clamps out-of-domain values without hiding the labels', () => {
  assert.deepEqual(
    buildStrokeRateGeometry({
      averageSpm: 30,
      targetMinSpm: 14,
      targetMaxSpm: 28,
    }),
    {
      measuredPercent: 100,
      targetBottomPercent: 0,
      targetHeightPercent: 100,
    },
  );
});
