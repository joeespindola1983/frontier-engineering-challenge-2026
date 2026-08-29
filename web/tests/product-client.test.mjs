import assert from 'node:assert/strict';
import test from 'node:test';

import { demoReview } from '../app/lib/demo-review.mjs';
import {
  HttpWakeClient,
  ReplayWakeClient,
  createWakeClient,
} from '../app/lib/product-client.mjs';


test('uses the replay client unless an HTTP runtime URL is explicit', () => {
  assert.ok(createWakeClient({ baseUrl: '' }) instanceof ReplayWakeClient);
  assert.ok(
    createWakeClient({ baseUrl: 'http://127.0.0.1:8788' }) instanceof HttpWakeClient,
  );
});

test('replay client follows the asynchronous product contract without API calls', async () => {
  const client = new ReplayWakeClient(demoReview);

  const investigation = await client.createInvestigation();
  const briefing = await client.answerCheckpoint(
    investigation.checkpointId,
    'UNKNOWN',
  );
  const memory = await client.approveBriefing(briefing.briefingId);

  assert.equal(investigation.review, demoReview);
  assert.equal(briefing.equipment.status, 'UNKNOWN');
  assert.equal(memory.approvedSessions.length, 1);
});

test('HTTP client calls only task-level product endpoints', async () => {
  const requests = [];
  const responses = [
    {
      investigation_id: 'investigation-case-002',
      checkpoint_id: 'checkpoint-case-002',
      review: { analysis: {}, summary: {}, context: {} },
    },
    { briefingId: 'briefing-case-002', equipment: { status: 'UNKNOWN' } },
    { approvedSessions: [{ sessionId: 'case-002' }] },
  ];
  const fetchImpl = async (url, init) => {
    requests.push({ url, init });
    return {
      ok: true,
      json: async () => responses.shift(),
    };
  };
  const client = new HttpWakeClient({
    baseUrl: 'http://127.0.0.1:8788/',
    fetchImpl,
    reviewAdapter: () => demoReview,
  });

  const investigation = await client.createInvestigation();
  const briefing = await client.answerCheckpoint(
    investigation.checkpointId,
    'UNKNOWN',
  );
  await client.approveBriefing(briefing.briefingId);

  assert.deepEqual(
    requests.map(({ url }) => url),
    [
      'http://127.0.0.1:8788/api/investigations',
      'http://127.0.0.1:8788/api/checkpoints/checkpoint-case-002/answers',
      'http://127.0.0.1:8788/api/briefings/briefing-case-002/approve',
    ],
  );
  assert.equal(investigation.review, demoReview);
  assert.equal(
    JSON.parse(requests[0].init.body).mode,
    'replay',
  );
});

test('HTTP errors stay visible to the product flow', async () => {
  const client = new HttpWakeClient({
    baseUrl: 'http://127.0.0.1:8788',
    fetchImpl: async () => ({
      ok: false,
      status: 503,
      json: async () => ({ error: 'Agent runtime unavailable.' }),
    }),
    reviewAdapter: () => demoReview,
  });

  await assert.rejects(
    client.createInvestigation(),
    /Agent runtime unavailable/,
  );
});
