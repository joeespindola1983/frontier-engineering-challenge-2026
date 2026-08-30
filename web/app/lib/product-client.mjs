import { demoReview } from './demo-review.mjs';
import { buildSessionReview } from './replay-adapter.mjs';
import { approveBriefingMemory, resolveCheckpoint } from './workflow-state.mjs';


export class ReplayWakeClient {
  constructor(review = demoReview) {
    this.review = review;
    this.briefings = new Map();
    this.viewed = false;
  }

  async createInvestigation() {
    return {
      investigationId: `investigation-${this.review.sessionId}`,
      sessionId: this.review.sessionId,
      checkpointId: this.review.checkpoint.checkpointId,
      goalId: `goal-${this.review.sessionId}`,
      status: 'QUESTION_REQUIRED',
      mode: 'replay',
      review: this.review,
    };
  }

  async listSessions() {
    return {
      schema_version: 'wake.session_inbox.v1',
      storage: { status: 'REPLAY_ONLY', raw_evidence_scope: 'SYNTHETIC' },
      counts: {
        needs_action: 1,
        awaiting_analysis: 0,
        viewed: this.viewed ? 1 : 0,
        in_club_memory: 0,
      },
      sessions: [{
        session_id: this.review.sessionId,
        title: this.review.title,
        scheduled_date: this.review.scheduledDate,
        status: 'NEEDS_HUMAN_RESPONSE',
        analysis_status: 'COMPLETED',
        coach_view_status: this.viewed ? 'VIEWED' : 'UNSEEN',
        human_context_status: 'AWAITING_RESPONSE',
        memory_status: 'NOT_READY',
        storage_status: 'REPLAY_ONLY',
      }],
    };
  }

  async getSession(sessionId) {
    if (sessionId !== this.review.sessionId) {
      throw new Error(`Unknown session: ${sessionId}`);
    }
    return {
      ...(await this.listSessions()).sessions[0],
      investigation_id: `investigation-${this.review.sessionId}`,
      checkpoint_id: this.review.checkpoint.checkpointId,
      goal_id: `goal-${this.review.sessionId}`,
      review: this.review,
    };
  }

  async markSessionViewed(sessionId) {
    await this.getSession(sessionId);
    this.viewed = true;
    return this.getSession(sessionId);
  }

  async answerCheckpoint(checkpointId, answer) {
    if (checkpointId !== this.review.checkpoint.checkpointId) {
      throw new Error(`Unknown checkpoint: ${checkpointId}`);
    }
    const briefing = resolveCheckpoint(this.review, answer);
    this.briefings.set(briefing.briefingId, briefing);
    return briefing;
  }

  async approveBriefing(briefingId) {
    const briefing = this.briefings.get(briefingId);
    if (!briefing) throw new Error(`Unknown briefing: ${briefingId}`);
    return approveBriefingMemory(briefing, true);
  }
}


export class HttpWakeClient {
  constructor({ baseUrl, fetchImpl, reviewAdapter = buildSessionReview }) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.fetchImpl = fetchImpl ?? ((...args) => globalThis.fetch(...args));
    this.reviewAdapter = reviewAdapter;
  }

  async request(path, body) {
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `WAKE runtime failed with ${response.status}.`);
    }
    return payload;
  }

  async get(path) {
    const response = await this.fetchImpl(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `WAKE runtime failed with ${response.status}.`);
    }
    return payload;
  }

  listSessions() {
    return this.get('/api/sessions');
  }

  async getSession(sessionId) {
    const payload = await this.get(`/api/sessions/${sessionId}`);
    return {
      ...payload,
      ...(payload.review ? { review: this.reviewAdapter(payload.review) } : {}),
    };
  }

  markSessionViewed(sessionId) {
    return this.request(`/api/sessions/${sessionId}/view`, {});
  }

  async createInvestigation({ mode = 'replay', sourceIds } = {}) {
    const request = { mode };
    if (sourceIds) request.source_ids = sourceIds;
    else request.case_id = 'case-002-wind-shift-plan-deviation';
    const payload = await this.request('/api/investigations', request);
    return {
      investigationId: payload.investigation_id,
      sessionId: payload.session_id ?? payload.case_id,
      checkpointId: payload.checkpoint_id,
      goalId: payload.goal_id,
      status: payload.status,
      mode: payload.mode,
      review: this.reviewAdapter(payload.review),
    };
  }

  uploadSource({ kind, name, contentBase64, uploadedByRole, originRole }) {
    return this.request('/api/sources', {
      kind,
      name,
      content_base64: contentBase64,
      uploaded_by_role: uploadedByRole,
      origin_role: originRole,
    });
  }

  async enrichWeather({
    speedcoachSourceId,
    requestedByRole,
    authorizedLocationLookup,
    sessionTimezone,
  }) {
    if (authorizedLocationLookup !== true) {
      throw new TypeError(
        'Historical weather requires explicit location lookup authorization.',
      );
    }
    const request = {
      speedcoach_source_id: speedcoachSourceId,
      requested_by_role: requestedByRole,
      authorized_location_lookup: true,
    };
    if (sessionTimezone) request.session_timezone = sessionTimezone;
    return this.request('/api/environment-enrichments', request);
  }

  prepareSourceBundle(sourceIds) {
    return this.request('/api/source-bundles/prepare', {
      source_ids: sourceIds,
    });
  }

  prepareSourceBatch(items) {
    return this.request('/api/source-batches/prepare', { items });
  }

  getSourceBatch(batchId) {
    return this.get(`/api/source-batches/${batchId}`);
  }

  async executeSourceBatch({ batchId, mode, authorizedBatchCostUsd }) {
    if (mode !== 'live') {
      throw new TypeError('Source batch execution requires explicit live mode.');
    }
    if (!Number.isFinite(authorizedBatchCostUsd) || authorizedBatchCostUsd <= 0) {
      throw new TypeError('Live source batch execution requires explicit cost authorization.');
    }
    return this.request(`/api/source-batches/${batchId}/execute`, {
      mode: 'live',
      authorized_batch_cost_usd: authorizedBatchCostUsd,
    });
  }

  async analyzeSourceBundle({ sourceIds, mode, authorizedCostUsd }) {
    if (mode !== 'live') {
      throw new TypeError('New source bundle analysis requires explicit live mode.');
    }
    if (!Number.isFinite(authorizedCostUsd) || authorizedCostUsd <= 0) {
      throw new TypeError('Live source bundle analysis requires explicit cost authorization.');
    }
    const prepared = await this.prepareSourceBundle(sourceIds);
    const executed = await this.request(
      `/api/source-bundles/${prepared.bundle_id}/execute`,
      { mode: 'live', authorized_cost_usd: authorizedCostUsd },
    );
    return {
      executionId: executed.execution_id,
      sessionId: executed.session_id ?? executed.bundle_id,
      bundleId: executed.bundle_id,
      investigationId: executed.investigation_id,
      checkpointId: executed.checkpoint_id,
      goalId: executed.goal_id,
      investigationStatus: executed.investigation_status,
      cost: executed.cost,
      status: executed.status,
      agentCalled: executed.agent_called,
      review: this.reviewAdapter(executed.review),
    };
  }

  answerCheckpoint(checkpointId, response) {
    const normalized = response === 'UNKNOWN'
      ? {
          answer: 'UNKNOWN',
          answeredByRole: null,
          recordedByRole: null,
          authorityBasis: 'UNKNOWN',
        }
      : response;
    return this.request(`/api/checkpoints/${checkpointId}/answers`, {
      answer: normalized.answer,
      answered_by_role: normalized.answeredByRole,
      recorded_by_role: normalized.recordedByRole,
      authority_basis: normalized.authorityBasis,
    });
  }

  approveBriefing(briefingId) {
    return this.request(`/api/briefings/${briefingId}/approve`, {});
  }
}


export function createWakeClient({ baseUrl = '', fetchImpl } = {}) {
  if (baseUrl.trim()) {
    return new HttpWakeClient({ baseUrl, fetchImpl });
  }
  return new ReplayWakeClient();
}
