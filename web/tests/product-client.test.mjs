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
  assert.equal(briefing.humanConfirmation.status, 'UNKNOWN');
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

test('HTTP client uploads typed evidence before source-based investigation', async () => {
  const requests = [];
  const responses = [
    {
      source_id: 'source-plan-abc123',
      kind: 'PLAN',
      status: 'READY',
      format: 'WAKE_TRAINING_PLAN_JSON',
    },
    {
      investigation_id: 'investigation-case-002',
      checkpoint_id: 'checkpoint-case-002',
      goal_id: 'goal-case-002',
      status: 'QUESTION_REQUIRED',
      mode: 'replay',
      review: { analysis: {}, summary: {}, context: {} },
    },
  ];
  const client = new HttpWakeClient({
    baseUrl: 'http://127.0.0.1:8788',
    fetchImpl: async (url, init) => {
      requests.push({ url, init });
      return { ok: true, json: async () => responses.shift() };
    },
    reviewAdapter: () => demoReview,
  });

  const source = await client.uploadSource({
    kind: 'PLAN',
    name: 'plan.json',
    contentBase64: 'e30=',
  });
  const investigation = await client.createInvestigation({
    sourceIds: [source.source_id],
  });

  assert.deepEqual(
    requests.map(({ url }) => url),
    [
      'http://127.0.0.1:8788/api/sources',
      'http://127.0.0.1:8788/api/investigations',
    ],
  );
  assert.deepEqual(JSON.parse(requests[0].init.body), {
    kind: 'PLAN',
    name: 'plan.json',
    content_base64: 'e30=',
  });
  assert.deepEqual(JSON.parse(requests[1].init.body).source_ids, [
    'source-plan-abc123',
  ]);
  assert.equal(investigation.review, demoReview);
});

test('HTTP client prepares and explicitly executes a new source bundle', async () => {
  const requests = [];
  const responses = [
    {
      bundle_id: 'source-bundle-abc123',
      status: 'READY_FOR_LIVE',
      agent_called: false,
    },
    {
      execution_id: 'execution-source-bundle-abc123',
      bundle_id: 'source-bundle-abc123',
      investigation_id: 'investigation-source-bundle-abc123',
      checkpoint_id: 'checkpoint-source-bundle-abc123',
      goal_id: 'goal-uploaded-session',
      investigation_status: 'QUESTION_REQUIRED',
      status: 'AGENT_COMPLETED',
      agent_called: true,
      review: { analysis: {}, summary: {}, context: {} },
    },
  ];
  const client = new HttpWakeClient({
    baseUrl: 'http://127.0.0.1:8788',
    fetchImpl: async (url, init) => {
      requests.push({ url, init });
      return { ok: true, status: 201, json: async () => responses.shift() };
    },
    reviewAdapter: () => demoReview,
  });

  const result = await client.analyzeSourceBundle({
    sourceIds: ['plan', 'speedcoach', 'mobile', 'environment', 'context'],
    mode: 'live',
  });

  assert.deepEqual(
    requests.map(({ url }) => url),
    [
      'http://127.0.0.1:8788/api/source-bundles/prepare',
      'http://127.0.0.1:8788/api/source-bundles/source-bundle-abc123/execute',
    ],
  );
  assert.deepEqual(JSON.parse(requests[0].init.body), {
    source_ids: ['plan', 'speedcoach', 'mobile', 'environment', 'context'],
  });
  assert.deepEqual(JSON.parse(requests[1].init.body), { mode: 'live' });
  assert.equal(result.review, demoReview);
  assert.equal(result.agentCalled, true);
  assert.equal(result.investigationId, 'investigation-source-bundle-abc123');
  assert.equal(result.checkpointId, 'checkpoint-source-bundle-abc123');
  assert.equal(result.goalId, 'goal-uploaded-session');
  assert.equal(result.investigationStatus, 'QUESTION_REQUIRED');
});

test('HTTP client refuses implicit new-bundle execution before any request', async () => {
  let requests = 0;
  const client = new HttpWakeClient({
    baseUrl: 'http://127.0.0.1:8788',
    fetchImpl: async () => {
      requests += 1;
      throw new Error('must not be called');
    },
  });

  await assert.rejects(
    client.analyzeSourceBundle({ sourceIds: ['one'], mode: 'replay' }),
    /explicit live mode/,
  );
  assert.equal(requests, 0);
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
