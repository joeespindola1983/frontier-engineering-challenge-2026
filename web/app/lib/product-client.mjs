import { demoReview } from './demo-review.mjs';
import { buildSessionReview } from './replay-adapter.mjs';
import { approveBriefingMemory, resolveCheckpoint } from './workflow-state.mjs';


export class ReplayWakeClient {
  constructor(review = demoReview) {
    this.review = review;
    this.briefings = new Map();
  }

  async createInvestigation() {
    return {
      investigationId: `investigation-${this.review.sessionId}`,
      checkpointId: this.review.checkpoint.checkpointId,
      goalId: `goal-${this.review.sessionId}`,
      status: 'QUESTION_REQUIRED',
      mode: 'replay',
      review: this.review,
    };
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

  async createInvestigation({ mode = 'replay', sourceIds } = {}) {
    const request = { mode };
    if (sourceIds) request.source_ids = sourceIds;
    else request.case_id = 'case-002-wind-shift-plan-deviation';
    const payload = await this.request('/api/investigations', request);
    return {
      investigationId: payload.investigation_id,
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

  async analyzeSourceBundle({ sourceIds, mode, authorizedCostUsd }) {
    if (mode !== 'live') {
      throw new TypeError('New source bundle analysis requires explicit live mode.');
    }
    if (!Number.isFinite(authorizedCostUsd) || authorizedCostUsd <= 0) {
      throw new TypeError('Live source bundle analysis requires explicit cost authorization.');
    }
    const prepared = await this.request('/api/source-bundles/prepare', {
      source_ids: sourceIds,
    });
    const executed = await this.request(
      `/api/source-bundles/${prepared.bundle_id}/execute`,
      { mode: 'live', authorized_cost_usd: authorizedCostUsd },
    );
    return {
      executionId: executed.execution_id,
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
