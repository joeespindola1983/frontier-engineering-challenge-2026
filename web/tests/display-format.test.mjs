import assert from 'node:assert/strict';
import test from 'node:test';

import {
  formatAnalysisPeriod,
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

test('formats the analysis period from dataset dates and recorded training days', () => {
  assert.equal(formatAnalysisPeriod({
    start: '2026-08-17',
    end: '2026-08-28',
    weekdays: ['2026-08-17', '2026-08-18', '2026-08-19'],
  }), '3 training days · 17–28 Aug 2026');
  assert.equal(formatAnalysisPeriod({
    start: '2026-08-17',
    end: '2026-08-17',
    weekdays: ['2026-08-17'],
  }), '1 training day · 17 Aug 2026');
});
