import assert from 'node:assert/strict';
import test from 'node:test';

import { buildReconstructionDisplay } from '../app/lib/reconstruction-display.mjs';


test('turns a dense reconstruction into short bullets and product source names', () => {
  const display = buildReconstructionDisplay(
    'The SPM-based reconstruction identifies all six planned work intervals. Rates matched except work-05. Boat-relative wind remains unverified. [input/speedcoach.csv; input/plan.json; input/environment.json]',
  );

  assert.deepEqual(display.bullets, [
    'The SPM-based reconstruction identifies all six planned work intervals.',
    'Rates matched except work-05.',
    'Boat-relative wind remains unverified.',
  ]);
  assert.deepEqual(display.evidenceLabels, [
    'SpeedCoach recording',
    'Training plan',
    'Environment timeline',
  ]);
  assert.doesNotMatch(JSON.stringify(display), /input\//);
  assert.doesNotMatch(JSON.stringify(display), /\.csv|\.json/);
});

test('keeps an unstructured reconstruction readable when no references are appended', () => {
  const display = buildReconstructionDisplay('One supported observation remains.');

  assert.deepEqual(display.bullets, ['One supported observation remains.']);
  assert.deepEqual(display.evidenceLabels, []);
});
