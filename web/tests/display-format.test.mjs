import assert from 'node:assert/strict';
import test from 'node:test';

import {
  formatEvidenceKind,
  formatMeasurementRange,
} from '../app/lib/display-format.mjs';


test('formats measurement ranges without awkward percent spacing', () => {
  assert.equal(formatMeasurementRange([31, 50], '%'), '31.0–50.0%');
  assert.equal(formatMeasurementRange([1.3, 1.5], 'm/s'), '1.3–1.5 m/s');
  assert.equal(formatMeasurementRange(null, '°C'), 'Not available');
});

test('preserves product source names in prepared bundle labels', () => {
  assert.equal(formatEvidenceKind('PLAN'), 'Plan');
  assert.equal(formatEvidenceKind('SPEEDCOACH'), 'SpeedCoach');
  assert.equal(formatEvidenceKind('ENVIRONMENT'), 'Environment');
});
