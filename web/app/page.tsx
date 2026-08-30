'use client';

import { useEffect, useMemo, useState } from 'react';
import { buildStrokeRateGeometry, STROKE_RATE_DOMAIN } from './lib/chart-scale.mjs';
import { demoReview } from './lib/demo-review.mjs';
import { formatEvidenceKind, formatMeasurementRange } from './lib/display-format.mjs';
import { evidenceSourceDefinitions, uploadEvidenceBundleWithWeather } from './lib/evidence-intake.mjs';
import { evaluationResults } from './lib/evaluation-results.mjs';
import { createWakeClient } from './lib/product-client.mjs';
import { sessionActionLabel, sessionStatusLabel, summarizeSessionInbox } from './lib/session-inbox.mjs';
import { approveBriefingMemory, resolveCheckpoint } from './lib/workflow-state.mjs';

type Screen = 'sessions' | 'intake' | 'review' | 'briefing' | 'memory' | 'evaluation';
type Briefing = ReturnType<typeof resolveCheckpoint>;
type GoalMemory = ReturnType<typeof approveBriefingMemory>;
type Review = typeof demoReview;
type EvidenceKind = 'PLAN' | 'SPEEDCOACH' | 'MOBILE' | 'ENVIRONMENT' | 'CONTEXT';
type EvidenceFiles = Partial<Record<EvidenceKind, File>>;
type ContributorRole = 'ATHLETE' | 'COACH';
type ConfirmationMode = 'ATHLETE_DIRECT' | 'ATHLETE_RELAYED_BY_COACH' | 'COACH_OBSERVED';
type CheckpointResponse = {
  answer: 'YES' | 'NO' | 'UNKNOWN';
  answeredByRole: ContributorRole | null;
  recordedByRole: ContributorRole | null;
  authorityBasis: 'DIRECT_PARTICIPANT' | 'DIRECT_OBSERVATION' | 'RELAYED_REPORT' | 'UNKNOWN';
};
type ExecutionCost = {
  approximate_cost_usd: number;
  authorized_cost_usd: number;
  status: 'WITHIN_AUTHORIZATION' | 'AUTHORIZATION_EXCEEDED';
  usage: { total_tokens: number };
  runtime_ms: number;
};
type WeatherRequest = {
  enabled: boolean;
  authorizedLocationLookup: boolean;
  sessionTimezone: string;
};
type WeatherOutcome = {
  status: 'NOT_REQUESTED' | 'ADDED' | 'UNAVAILABLE';
  message?: string;
  preview?: {
    provider: string;
    dataset: string;
    sample_count: number;
    temporal_resolution_minutes: number;
    location_precision_decimals: number;
    wind_speed_range_m_s: number[] | null;
    gust_max_m_s: number | null;
    temperature_range_c: number[] | null;
    relative_humidity_range_pct: number[] | null;
    causal_conclusion: 'NOT_ESTABLISHED';
  };
};
type PreparedBundle = {
  bundle_id: string;
  session_id?: string;
  status: string;
  agent_called: boolean;
  source_coverage: { kind: string; status: string }[];
};
type SessionRecord = {
  session_id: string;
  case_id?: string;
  title: string;
  scheduled_date: string | null;
  status: 'READY_FOR_INVESTIGATION' | 'NEEDS_HUMAN_RESPONSE' | 'READY_FOR_COACH_REVIEW' | 'READY_FOR_COACH_APPROVAL' | 'IN_CLUB_MEMORY';
  analysis_status: 'NOT_STARTED' | 'COMPLETED';
  coach_view_status: 'UNSEEN' | 'VIEWED';
  human_context_status: 'NOT_REQUESTED' | 'AWAITING_RESPONSE' | 'RESPONDED';
  memory_status: 'NOT_READY' | 'AWAITING_APPROVAL' | 'APPROVED';
  storage_status: 'SAVED_LOCALLY' | 'PROCESS_ONLY' | 'REPLAY_ONLY';
  source_coverage?: { kind: string; status: string }[];
};
type SessionDetail = SessionRecord & {
  review?: Review;
  briefing?: Briefing;
  goal?: GoalMemory;
  checkpoint_id?: string;
  bundle?: PreparedBundle;
};

const configuredRuntimeUrl = process.env.NEXT_PUBLIC_WAKE_API_URL ?? '';
const configuredRuntimeMode = process.env.NEXT_PUBLIC_WAKE_RUNTIME_MODE === 'live' ? 'live' : 'replay';
const configuredCostAuthorizationUsd = Number.parseFloat(
  process.env.NEXT_PUBLIC_WAKE_COST_AUTHORIZATION_USD ?? '0.20',
);

function formatDate(value: string | null) {
  if (!value) return 'Date not supplied';
  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit', month: 'short', year: 'numeric', timeZone: 'UTC',
  }).format(new Date(`${value}T00:00:00Z`));
}

function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${String(Math.round(seconds % 60)).padStart(2, '0')}`;
}

function formatRole(role: string) {
  return {
    ATHLETE: 'athlete',
    COACH: 'coach',
    DEVICE: 'device',
    SERVICE: 'service',
    ATHLETE_OR_COACH: 'athlete or coach',
  }[role] ?? 'human contributor';
}

function checkpointResponse(answer: 'YES' | 'NO', mode: ConfirmationMode): CheckpointResponse {
  return {
    ATHLETE_DIRECT: { answer, answeredByRole: 'ATHLETE', recordedByRole: 'ATHLETE', authorityBasis: 'DIRECT_PARTICIPANT' },
    ATHLETE_RELAYED_BY_COACH: { answer, answeredByRole: 'ATHLETE', recordedByRole: 'COACH', authorityBasis: 'RELAYED_REPORT' },
    COACH_OBSERVED: { answer, answeredByRole: 'COACH', recordedByRole: 'COACH', authorityBasis: 'DIRECT_OBSERVATION' },
  }[mode];
}

function AppHeader({ screen, onNavigate }: { screen: Screen; onNavigate: (screen: Screen) => void }) {
  const sessionActive = ['sessions', 'intake', 'review', 'briefing'].includes(screen);
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <button className="brand" onClick={() => onNavigate('sessions')} type="button">
          <span className="brand-mark" aria-hidden="true">≋</span><span>WAKE</span>
        </button>
        <nav className="primary-nav" aria-label="Primary navigation">
          <button className={sessionActive ? 'active' : ''} onClick={() => onNavigate('sessions')} type="button">Sessions</button>
          <button className={screen === 'memory' ? 'active' : ''} onClick={() => onNavigate('memory')} type="button">Goal memory</button>
          <button className={screen === 'evaluation' ? 'active' : ''} onClick={() => onNavigate('evaluation')} type="button">Evaluation</button>
        </nav>
        <div className="topbar-actions">
          <span className="demo-label">{configuredRuntimeMode === 'live' ? 'Local live runtime' : 'Synthetic demo data'}</span>
          <button className="button button-primary button-small" onClick={() => onNavigate('intake')} type="button">Review a session</button>
        </div>
      </div>
    </header>
  );
}

function PrototypeNotice() {
  return <div className="prototype-notice" role="note"><span>{configuredRuntimeMode === 'live' ? 'Local live runtime' : 'Prototype replay'}</span>{configuredRuntimeMode === 'live' ? 'The bounded WAKE agent is enabled. Uploaded evidence stays in the local process and every execution requires an explicit review action.' : demoReview.notice}</div>;
}

function milestoneLabel(session: SessionRecord, milestone: 'analysis' | 'view' | 'answer' | 'memory') {
  if (milestone === 'analysis') return session.analysis_status === 'COMPLETED' ? 'Analysed' : 'Awaiting analysis';
  if (milestone === 'view') return session.coach_view_status === 'VIEWED' ? 'Viewed by coach' : 'Unseen by coach';
  if (milestone === 'answer') return {
    NOT_REQUESTED: 'No answer requested',
    AWAITING_RESPONSE: 'Awaiting answer',
    RESPONDED: 'Answered',
  }[session.human_context_status];
  return {
    NOT_READY: 'Not in memory',
    AWAITING_APPROVAL: 'Awaiting approval',
    APPROVED: 'In club memory',
  }[session.memory_status];
}

function SessionsScreen({ onNavigate, onReview, onOpenSession, sessions, processing, error }: { onNavigate: (screen: Screen) => void; onReview: () => void; onOpenSession: (session: SessionRecord) => void; sessions: SessionRecord[]; processing: boolean; error: string }) {
  const summary = summarizeSessionInbox(sessions);
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="page-header">
        <div className="page-header-copy">
          <div className="kicker">Daily intelligence</div>
          <h1>Review the session,<br />not every chart.</h1>
          <p className="lede">WAKE combines the plan, recordings, conditions, and attributed human context into one evidence-backed session review.</p>
        </div>
        <div className="page-header-actions">
          <button className="button" onClick={() => onNavigate('evaluation')} type="button">View evaluation results</button>
          <button className="button button-primary" onClick={() => onNavigate('intake')} type="button">Review a session</button>
        </div>
      </header>
      <section className="summary-strip" aria-label="Session summary">
        <div><span>Needs action</span><strong>{summary.needsAction}</strong><small>Answer or coach approval</small></div>
        <div><span>Awaiting analysis</span><strong>{summary.awaitingAnalysis}</strong><small>Evidence received, agent pending</small></div>
        <div><span>Viewed by coach</span><strong>{summary.viewed}</strong><small>Opened at least once</small></div>
        <div><span>In club memory</span><strong>{summary.inClubMemory}</strong><small>Explicitly coach approved</small></div>
      </section>
      <div className="storage-note"><strong>Saved locally</strong><span>The inbox and workflow milestones survive a page refresh and service restart. Raw evidence stays in a Git-ignored, user-restricted prototype file; it is not yet encrypted, authenticated, or multi-club.</span></div>
      {error ? <div className="runtime-error" role="alert">{error}</div> : null}
      <section className="session-list" aria-label="Session reviews">
        {sessions.length ? sessions.map((session) => (
          <button className="session-row session-row-operational" disabled={processing} key={session.session_id} onClick={() => onOpenSession(session)} type="button">
            <div><div className="session-title">{session.title}</div><div className="session-subtitle">{session.storage_status === 'SAVED_LOCALLY' ? 'Private local record' : 'Prototype record'} · {session.source_coverage?.filter((source) => source.status === 'PRESENT').map((source) => formatEvidenceKind(source.kind)).join(' + ') || 'Committed synthetic evidence'}</div></div>
            <div><span className="meta-label">Date</span><span>{formatDate(session.scheduled_date)}</span></div>
            <div className="milestone-grid" aria-label="Session workflow milestones"><span className={session.analysis_status === 'COMPLETED' ? 'done' : ''}>{milestoneLabel(session, 'analysis')}</span><span className={session.coach_view_status === 'VIEWED' ? 'done' : ''}>{milestoneLabel(session, 'view')}</span><span className={session.human_context_status === 'RESPONDED' ? 'done' : ''}>{milestoneLabel(session, 'answer')}</span><span className={session.memory_status === 'APPROVED' ? 'done' : ''}>{milestoneLabel(session, 'memory')}</span></div>
            <div className="session-action"><span className={`status ${session.memory_status === 'APPROVED' ? 'approved' : 'attention'}`}>{sessionStatusLabel(session.status)}</span><small>{sessionActionLabel(session.status)} →</small></div>
          </button>
        )) : <button className="session-row" disabled={processing} onClick={() => onReview()} type="button"><div><div className="session-title">{demoReview.title}</div><div className="session-subtitle">Sample session · not added to the local inbox yet</div></div><div><span className="meta-label">Date</span><span>{formatDate(demoReview.scheduledDate)}</span></div><div><span className="meta-label">Start here</span><span>Open the committed replay</span></div><span className="status attention">Investigate sample</span></button>}
      </section>
    </main>
  );
}

function WeatherPreview({ outcome }: { outcome: WeatherOutcome }) {
  if (outcome.status === 'NOT_REQUESTED') return null;
  if (outcome.status === 'UNAVAILABLE') {
    return <div className="weather-result weather-result-warning" role="status"><strong>Conditions unavailable</strong><p>{outcome.message} The core plan and SpeedCoach bundle remains usable.</p></div>;
  }
  const preview = outcome.preview;
  if (!preview) return null;
  return (
    <div className="weather-result" role="status">
      <div className="weather-result-header"><div><span>Historical conditions added</span><strong>{preview.provider}</strong></div><small>{preview.temporal_resolution_minutes}-minute modeled data · {preview.sample_count} samples</small></div>
      <div className="weather-metrics">
        <div><span>Wind</span><strong>{formatMeasurementRange(preview.wind_speed_range_m_s, 'm/s')}</strong></div>
        <div><span>Peak gust</span><strong>{preview.gust_max_m_s == null ? 'Not available' : `${preview.gust_max_m_s.toFixed(1)} m/s`}</strong></div>
        <div><span>Temperature</span><strong>{formatMeasurementRange(preview.temperature_range_c, '°C')}</strong></div>
        <div><span>Humidity</span><strong>{formatMeasurementRange(preview.relative_humidity_range_pct, '%')}</strong></div>
      </div>
      <p>Approximate location rounded to {preview.location_precision_decimals} decimals. Time alignment supports context, not a causal performance verdict.</p>
    </div>
  );
}

function IntakeScreen({ onInvestigate, processing, error, preparedBundle, weatherOutcome }: { onInvestigate: (files: EvidenceFiles, contributorRole: ContributorRole, weather: WeatherRequest) => void; processing: boolean; error: string; preparedBundle: PreparedBundle | null; weatherOutcome: WeatherOutcome }) {
  const [files, setFiles] = useState<EvidenceFiles>({});
  const [contributorRole, setContributorRole] = useState<ContributorRole>('ATHLETE');
  const [weatherEnabled, setWeatherEnabled] = useState(false);
  const [authorizedLocationLookup, setAuthorizedLocationLookup] = useState(false);
  const [sessionTimezone, setSessionTimezone] = useState('');
  const hasSelectedFiles = Object.keys(files).length > 0;
  const allReplayFilesSelected = evidenceSourceDefinitions.every(({ kind }) => files[kind as EvidenceKind]);
  const buttonLabel = !hasSelectedFiles
    ? 'Investigate sample session'
    : configuredRuntimeMode === 'live'
      ? 'Validate and investigate'
      : allReplayFilesSelected
        ? 'Validate and open replay'
        : 'Validate and prepare · No agent call';
  return (
    <main className="page page-narrow">
      <PrototypeNotice />
      <header className="page-header">
        <div className="page-header-copy"><div className="kicker">New session review</div><h1>Bring the evidence together.</h1><p className="lede">Start with the training plan and SpeedCoach recording. Optional evidence expands what WAKE can verify without blocking the core review.</p></div>
      </header>
      <div className="intake-layout">
        <section>
          <fieldset className="contributor-selector"><legend>Who is contributing these files?</legend><label><input checked={contributorRole === 'ATHLETE'} disabled={processing} name="contributor" onChange={() => setContributorRole('ATHLETE')} type="radio" /> Athlete</label><label><input checked={contributorRole === 'COACH'} disabled={processing} name="contributor" onChange={() => setContributorRole('COACH')} type="radio" /> Coach</label><small>Either role may upload any file. WAKE keeps the uploader separate from the source&apos;s authority.</small></fieldset>
          <div className="kicker">Evidence ready</div>
          <div className="upload-list">
            {evidenceSourceDefinitions.map((source, index) => {
              const selected = files[source.kind as EvidenceKind];
              return (
                <div className="upload-row" key={source.kind}><span className="upload-index">0{index + 1}</span><div><strong>{source.title} · {source.required ? 'Core' : 'Optional'}</strong><code>{selected?.name ?? source.defaultName}</code><small>{source.description}</small><small className="authority-label">Origin: {formatRole(source.originRole ?? contributorRole)} · authority: {source.authorityScope.replaceAll('_', ' ').toLowerCase()} · uploader: {formatRole(contributorRole)}</small></div>{configuredRuntimeUrl ? <label className="upload-file-action">{selected ? 'Selected' : 'Choose'}<input accept={source.accept} className="sr-only" disabled={processing} onChange={(event) => { const file = event.target.files?.[0]; if (file) { setFiles((current) => ({ ...current, [source.kind]: file })); if (source.kind === 'ENVIRONMENT') { setWeatherEnabled(false); setAuthorizedLocationLookup(false); } } }} type="file" /></label> : <span className="ready-label">Ready sample</span>}</div>
              );
            })}
          </div>
          {configuredRuntimeUrl ? <section className={`weather-enrichment${files.ENVIRONMENT ? ' weather-disabled' : ''}`} aria-labelledby="weather-title"><div className="weather-heading"><div><div className="kicker">Optional evidence enhancer</div><h2 id="weather-title">Historical conditions</h2><p>WAKE can retrieve modeled wind, gusts, temperature, and humidity for the session window.</p></div><label className="weather-switch"><input checked={weatherEnabled} disabled={processing || Boolean(files.ENVIRONMENT)} onChange={(event) => setWeatherEnabled(event.target.checked)} type="checkbox" /><span>{files.ENVIRONMENT ? 'Uploaded timeline selected' : 'Use historical weather'}</span></label></div>{weatherEnabled && !files.ENVIRONMENT ? <div className="weather-fields"><label><span>Session timezone</span><input disabled={processing} onChange={(event) => setSessionTimezone(event.target.value)} placeholder="America/Sao_Paulo" type="text" value={sessionTimezone} /><small>Required when the SpeedCoach stores local time without an offset.</small></label><label className="weather-consent"><input checked={authorizedLocationLookup} disabled={processing} onChange={(event) => setAuthorizedLocationLookup(event.target.checked)} type="checkbox" /><span>I authorize WAKE to send a rounded approximate session location and bounded date window to Open-Meteo.</span></label><p className="weather-privacy">No route rows, athlete identity, plan, or device identifier leave the local service.</p></div> : null}{files.ENVIRONMENT ? <p className="weather-uploaded-note">The uploaded environmental timeline remains the selected source. Remove it before requesting provider data.</p> : null}<WeatherPreview outcome={weatherOutcome} /></section> : null}
          {hasSelectedFiles ? <p className="upload-boundary">Plan and SpeedCoach enable the core review. Missing mobile, environment, or context will remain visible as evidence gaps. A different bundle cannot reuse the committed replay.</p> : null}
          <div className="known-context"><div className="kicker">Known context</div>{hasSelectedFiles ? <p>{files.CONTEXT ? 'Boat, crew, goal, and observations will be read from the selected context file.' : 'No context file selected. Boat, crew, goal, and human observations will remain unknown.'}</p> : <div className="context-grid"><span>Men&apos;s double scull (2x)</span><span>Two synthetic athletes</span><span>Regatta preparation</span><span>Water session</span></div>}</div>
          {hasSelectedFiles && configuredRuntimeMode === 'live' ? <p className="upload-boundary"><strong>Operational authorization: US${configuredCostAuthorizationUsd.toFixed(2)}.</strong> This allows the run to start; it is not a provider billing cap. WAKE shows the token-based approximate cost after execution.</p> : null}
          {preparedBundle ? <div className="prepared-bundle" role="status"><span>Saved locally · Ready for investigation</span><strong>{preparedBundle.source_coverage.filter((source) => source.status === 'PRESENT').map((source) => formatEvidenceKind(source.kind)).join(' + ')}</strong><p>No agent call was made. This session now appears in the inbox and can continue through an explicitly authorized live investigation.</p></div> : null}
          {error ? <div className="runtime-error" role="alert">{error}</div> : null}
          <button className="button button-primary" disabled={processing} onClick={() => onInvestigate(files, contributorRole, { enabled: weatherEnabled, authorizedLocationLookup, sessionTimezone })} type="button">{processing ? configuredRuntimeMode === 'live' ? 'Investigating…' : 'Preparing…' : buttonLabel}</button>
        </section>
        <aside className="process-note"><div className="kicker">What WAKE will do</div><ol><li>Validate every selected source.</li><li>Retrieve authorized historical conditions.</li><li>Match and align recordings.</li><li>Select trust per metric.</li><li>Preserve unsupported unknowns.</li></ol></aside>
      </div>
    </main>
  );
}

function IntervalChart({ review }: { review: Review }) {
  return (
    <section className="interval-chart" aria-labelledby="interval-title">
      <div className="chart-legend"><span id="interval-title">Average stroke rate by work interval</span><span>Scale {STROKE_RATE_DOMAIN.min}–{STROKE_RATE_DOMAIN.max} SPM · shaded area = prescribed range</span></div>
      <div className="interval-bars">
        {review.workIntervals.map((interval) => {
          const isDeviation = interval.status === 'DEVIATION';
          const geometry = buildStrokeRateGeometry(interval);
          return (
            <div className="interval-column" key={interval.segmentId} aria-label={`Work ${interval.index}: ${interval.averageSpm} SPM; target ${interval.targetMinSpm} to ${interval.targetMaxSpm} SPM; ${isDeviation ? 'deviation' : 'within range'}`}>
              <div className="interval-plot"><div className="target-band" style={{ bottom: `${geometry.targetBottomPercent}%`, height: `${geometry.targetHeightPercent}%` }} /><div className={`interval-bar${isDeviation ? ' deviation' : ''}`} style={{ height: `${geometry.measuredPercent}%` }} /></div>
              <div className="interval-label"><span>W{interval.index}</span><span>{Math.round(interval.averageSpm)} SPM</span></div><small>{interval.targetMinSpm}–{interval.targetMaxSpm} target</small>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function SourcePolicy({ review }: { review: Review }) {
  const rows = [
    ['Stroke rate', review.sourcePolicy.strokeRate], ['Distance', review.sourcePolicy.distance],
    ['Route', review.sourcePolicy.route], ['Environment', review.sourcePolicy.environment],
  ] as const;
  return (
    <section className="source-table" aria-labelledby="source-policy-title">
      <div className="kicker" id="source-policy-title">Evidence selection</div>
      {rows.map(([label, policy]) => (
        <details className="source-row" key={label}><summary><span className="source-name">{label}</span><span className="source-choice">{policy.selectedSource}{'corroboratedBy' in policy && policy.corroboratedBy ? ` + ${policy.corroboratedBy} corroboration` : ''}</span><span className="disclosure-label">Why this source</span></summary><p>{policy.reason}</p></details>
      ))}
    </section>
  );
}

function ReviewScreen({ review, executionCost, onComplete, processing, error }: { review: Review; executionCost: ExecutionCost | null; onComplete: (response: CheckpointResponse | 'UNKNOWN') => void; processing: boolean; error: string }) {
  const [answer, setAnswer] = useState<'YES' | 'NO'>('YES');
  const [confirmationMode, setConfirmationMode] = useState<ConfirmationMode>('ATHLETE_DIRECT');
  const questionRequired = review.status === 'QUESTION_REQUIRED';
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="review-header"><div className="review-title"><div className="kicker">Session review</div><h1>{review.title}</h1><div className="review-meta"><span>{formatDate(review.scheduledDate)}</span><span>Plan + SpeedCoach + mobile + environment</span>{review.mobileClockOffsetS == null ? null : <span>{review.mobileClockOffsetS} s mobile clock offset</span>}{executionCost ? <span>Approx. agent cost US${executionCost.approximate_cost_usd.toFixed(4)} · {executionCost.usage.total_tokens.toLocaleString('en-US')} tokens{executionCost.status === 'AUTHORIZATION_EXCEEDED' ? ' · Exceeded operational authorization' : ''}</span> : null}</div></div><div className="review-state"><span className={`status ${questionRequired ? 'attention' : 'approved'}`}>{questionRequired ? 'Human context required' : 'Ready for review'}</span><strong>{questionRequired ? 'One answer can change the briefing' : 'No additional question was requested'}</strong></div></header>
      <div className="progress-line" aria-label="Session review progress"><span /></div>
      <div className="review-layout">
        <div><section><div className="kicker">Current reconstruction</div><p className="finding-intro">{review.currentReconstruction}</p></section><IntervalChart review={review} /><SourcePolicy review={review} /><section className="environment-note"><div><div className="kicker">Environmental boundary</div><h2>Condition context, not a causal verdict</h2></div><p>{review.environment.summary}</p></section></div>
        <aside className="checkpoint"><div className="kicker">Question for {formatRole(review.checkpoint.expectedRespondentRole)}</div><h2>{review.checkpoint.question}</h2><p>Who uploaded a file is not automatically the authority for this answer. WAKE stores who answered, who recorded it, and how they know.</p>
          <fieldset className="answer-list"><legend>Answer</legend>{[['YES', 'Yes / confirmed'], ['NO', 'No / not confirmed']].map(([value, label]) => <label className="answer-option" key={value}><input checked={answer === value} name="confirmation" onChange={() => setAnswer(value as 'YES' | 'NO')} type="radio" value={value} />{label}</label>)}</fieldset>
          <fieldset className="answer-list provenance-list"><legend>Answer provenance</legend>{[['ATHLETE_DIRECT', 'Athlete answered directly'], ['ATHLETE_RELAYED_BY_COACH', 'Athlete answer recorded by coach'], ['COACH_OBSERVED', 'Coach observed directly']].map(([value, label]) => <label className="answer-option" key={value}><input checked={confirmationMode === value} name="answer-source" onChange={() => setConfirmationMode(value as ConfirmationMode)} type="radio" value={value} />{label}</label>)}</fieldset>
          {error ? <div className="runtime-error" role="alert">{error}</div> : null}<div className="checkpoint-actions"><button className="button button-primary" disabled={processing} onClick={() => onComplete(checkpointResponse(answer, confirmationMode))} type="button">{processing ? 'Verifying…' : 'Save attributed answer'}</button><button className="button button-quiet" disabled={processing} onClick={() => onComplete('UNKNOWN')} type="button">Keep unknown</button></div>
          <div className="evidence-note"><strong>Why this matters:</strong> {review.checkpoint.whyItMatters}</div><p className="checkpoint-status" aria-live="polite">{processing ? 'WAKE is rebuilding the verified briefing.' : 'No memory is updated until the coach approves the briefing.'}</p>
        </aside>
      </div>
    </main>
  );
}

function BriefingScreen({ briefing, onBack, onApprove, onLeave, processing, error }: { briefing: Briefing; onBack: () => void; onApprove: () => void; onLeave: () => void; processing: boolean; error: string }) {
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="page-header"><div className="page-header-copy"><div className="kicker">Verified session briefing</div><h1>{briefing.title}</h1><p className="lede">A coach-facing result with findings, limitations, and source choices kept together.</p></div><button className="button" onClick={onBack} type="button">Review evidence</button></header>
      <div className="brief-grid"><div><section className="brief-lead"><p>{briefing.headline}</p><small>{briefing.summary}</small></section>
        <section><div className="kicker">Plan versus performed</div>{briefing.workIntervals.map((interval) => <div className={`metric-line${interval.status === 'DEVIATION' ? ' deviation' : ''}`} key={interval.segmentId}><span>{String(interval.index).padStart(2, '0')}</span><strong>{interval.plannedDistanceM.toLocaleString('en-US')} m</strong><code>{formatDuration(interval.durationS)} · {interval.averageSpm.toFixed(1)} SPM</code><span>{interval.status === 'DEVIATION' ? 'SPM deviation' : 'Within range'}</span></div>)}</section>
        <section className="findings"><div className="kicker">Verified findings</div>{briefing.findings.map((finding) => <article className={`finding-row ${finding.status === 'ATTENTION' || finding.status === 'UNKNOWN' ? 'warning' : ''}`} key={finding.title}><span>●</span><div><strong>{finding.title}</strong><p>{finding.explanation}</p>{finding.evidenceRefs.map((ref) => <code className="evidence-tag" key={ref}>{ref.replace('input/', '')}</code>)}</div></article>)}</section>
      </div><aside className="brief-aside"><section><div className="kicker">Evidence status</div><h3>Verified with preserved boundaries</h3><p>Material claims retain sources. Technique and physiology were not inferred from ordinary telemetry.</p></section><section><div className="kicker">Human context</div><h3>{briefing.humanConfirmation.status === 'UNKNOWN' ? 'Human context remains unknown' : briefing.humanConfirmation.source}</h3><p>{briefing.humanConfirmation.statement}</p></section><section><div className="kicker">Memory proposal</div><h3>Save one reviewed session</h3><p>Approval stores this briefing and unresolved questions; it does not create a performance trend.</p></section><div className="aside-actions">{error ? <div className="runtime-error" role="alert">{error}</div> : null}<button className="button button-primary" disabled={processing} onClick={onApprove} type="button">{processing ? 'Approving…' : 'Approve memory update'}</button><button className="button" disabled={processing} onClick={onLeave} type="button">Leave session unchanged</button></div></aside></div>
    </main>
  );
}

function MemoryScreen({ memory, onBack }: { memory: GoalMemory; onBack: () => void }) {
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="page-header"><div className="page-header-copy"><div className="kicker">Goal memory</div><h1>{memory.title}</h1><p className="lede">Only coach-approved evidence enters this history. One session is context, not a trend.</p></div><button className="button" onClick={onBack} type="button">Back to sessions</button></header>
      <section className="memory-conclusion"><div className="kicker">Current conclusion</div><p>{memory.currentConclusion}</p></section>
      <div className="memory-layout"><section><div className="kicker">Approved evidence</div>{memory.approvedSessions.length ? memory.approvedSessions.map((session) => <article className="memory-row" key={session.sessionId}><time>{formatDate(session.scheduledDate)}</time><div><h3>{session.title}</h3><p>{session.summary}</p><small>{session.humanConfirmation.statement}</small></div><span className="status approved">Coach approved</span></article>) : <div className="empty-state"><h2>No approved sessions yet.</h2><p>Review a briefing and explicitly approve its memory proposal.</p></div>}</section>
        <aside className="memory-aside"><section><div className="kicker">Open coaching questions</div>{memory.unresolvedQuestions.length ? <ul>{memory.unresolvedQuestions.map((question) => <li key={question}>{question}</li>)}</ul> : <p>No questions stored.</p>}</section><section><div className="kicker">Next useful evidence</div>{memory.nextUsefulEvidence.length ? <ul>{memory.nextUsefulEvidence.map((evidence) => <li key={evidence}>{evidence}</li>)}</ul> : <p>Approve a session before WAKE proposes comparable evidence.</p>}</section><section><div className="kicker">Boundary</div><p>WAKE does not prescribe crew selection, medical action, or autonomous training changes.</p></section></aside>
      </div>
    </main>
  );
}

function formatProvenance(value: string) {
  return value === 'REAL_ANONYMIZED' ? 'Real · anonymized' : value === 'DERIVED_SYNTHETIC' ? 'Derived synthetic' : 'Synthetic';
}

function EvaluationScreen({ onBack }: { onBack: () => void }) {
  const { comparison, cost, usage, agent_observability: observability, cases, dimensions, boundaries } = evaluationResults;
  return (
    <main className="page evaluation-page">
      <div className="evaluation-notice" role="note"><span>Saved result · No model call</span>This view renders committed evaluation artifacts. Opening it never runs the agent or spends API budget.</div>
      <header className="page-header evaluation-header">
        <div className="page-header-copy"><div className="kicker">Consolidated official evaluation</div><h1>Measured against the same ten sessions.</h1><p className="lede">Same model, same ten case summaries, same output schema. The difference is WAKE&apos;s bounded investigation tools and deterministic verification.</p></div>
        <button className="button" onClick={onBack} type="button">Back to sessions</button>
      </header>

      <section className="evaluation-scoreboard" aria-label="Official evaluation result">
        <article className="score-card score-card-wake"><div><span>Bounded WAKE agent</span><small>Four tools · verified output</small></div><strong>{comparison.wake_score.toFixed(2)}</strong><div className="score-track" aria-label={`WAKE score ${comparison.wake_score} out of 100`}><span style={{ width: `${comparison.wake_score}%` }} /></div></article>
        <article className="score-card"><div><span>Direct model baseline</span><small>One call · no tools or verifier</small></div><strong>{comparison.baseline_score.toFixed(2)}</strong><div className="score-track score-track-baseline" aria-label={`Baseline score ${comparison.baseline_score} out of 100`}><span style={{ width: `${comparison.baseline_score}%` }} /></div></article>
        <article className="gain-card"><span>Measured gain</span><strong>+{comparison.absolute_gain.toFixed(2)}</strong><p>points · +{comparison.relative_gain_percent.toFixed(2)}% relative</p><small>{comparison.all_cases_improved ? 'All 10 cases improved' : 'Not every case improved'}</small></article>
      </section>

      <section className="evaluation-facts" aria-label="Evaluation observability">
        <div><span>Incremental agent cost</span><strong>US${cost.incremental_agent_usd.toFixed(6)}</strong><small>US${cost.total_usd.toFixed(6)} total comparison</small></div>
        <div><span>Deterministic tool calls</span><strong>{observability.tool_calls}</strong><small>Four calls per case</small></div>
        <div><span>Verifier corrections</span><strong>{observability.verifier_retries}</strong><small>Bounded first-draft retries</small></div>
        <div><span>Saved trajectories</span><strong>{observability.trajectory_count}/10</strong><small>All final outputs verified</small></div>
      </section>

      <div className="evaluation-layout">
        <section className="case-comparison" aria-labelledby="case-comparison-title">
          <div className="section-heading"><div><div className="kicker">Case-by-case result</div><h2 id="case-comparison-title">No gain is hidden inside the average.</h2></div><div className="comparison-legend"><span className="legend-baseline">Direct baseline</span><span className="legend-wake">WAKE</span></div></div>
          <div className="case-score-list">
            {cases.map((item) => (
              <details className="case-report" key={item.case_id}>
                <summary className="case-score-row">
                  <div className="case-identity"><span>{item.short_id}</span><div><strong>{item.label}</strong><small>{formatProvenance(item.provenance)}</small></div></div>
                  <div className="paired-score-bars" aria-label={`${item.label}: baseline ${item.baseline_score}, WAKE ${item.wake_score}`}>
                    <div><span style={{ width: `${item.baseline_score}%` }} /><small>{item.baseline_score.toFixed(2)}</small></div>
                    <div className="wake-case-bar"><span style={{ width: `${item.wake_score}%` }} /><small>{item.wake_score.toFixed(2)}</small></div>
                  </div>
                  <div className="case-result-actions"><strong className="case-delta">+{item.delta.toFixed(2)}</strong><small>Open individual report</small></div>
                </summary>
                <div className="case-report-detail">
                  <div className="case-report-intro"><div><span>Scenario</span><p>{item.scenario}</p></div><small>{formatProvenance(item.provenance)} evaluation fixture · saved result</small></div>
                  <div className="case-dimension-table" role="table" aria-label={`${item.label} dimension scores`}>
                    <div className="case-dimension-header" role="row"><span role="columnheader">Rubric dimension</span><span role="columnheader">Baseline</span><span role="columnheader">WAKE</span><span role="columnheader">Change</span></div>
                    {item.dimensions.map((dimension) => (
                      <div className="case-dimension-row" role="row" key={dimension.dimension}><strong role="cell">{dimension.label}</strong><span role="cell">{dimension.baseline_score.toFixed(2)}</span><span role="cell">{dimension.wake_score.toFixed(2)}</span><span className={dimension.delta < 0 ? 'negative-delta' : ''} role="cell">{dimension.delta > 0 ? '+' : ''}{dimension.delta.toFixed(2)}</span></div>
                    ))}
                  </div>
                </div>
              </details>
            ))}
          </div>
        </section>

        <aside className="evaluation-aside">
          <section><div className="kicker">Comparable protocol</div><h3>One controlled difference</h3><p>The direct baseline had the same model, evidence summary, reasoning effort, and structured schema. It did not have WAKE&apos;s tools, loop, or verifier.</p></section>
          <section><div className="kicker">Observed execution</div><dl><div><dt>Baseline</dt><dd>{usage.baseline_tokens.toLocaleString('en-US')} tokens · {usage.baseline_runtime_seconds.toFixed(3)} s</dd></div><div><dt>WAKE</dt><dd>{usage.wake_tokens.toLocaleString('en-US')} tokens · {usage.wake_runtime_seconds.toFixed(3)} s</dd></div></dl></section>
          <section><div className="kicker">Saved for review</div><p>Structured answers, manifests, offline grade reports, and observable trajectories are committed. They can be reopened and regraded without another paid call.</p></section>
          <section><div className="kicker">Claim boundary</div><ul>{boundaries.map((boundary) => <li key={boundary}>{boundary}</li>)}</ul></section>
        </aside>
      </div>

      <section className="dimension-comparison" aria-labelledby="dimension-title">
        <div className="section-heading"><div><div className="kicker">Dimension diagnosis</div><h2 id="dimension-title">Strong structural gains, one honest regression.</h2></div><p>Percent of available rubric credit</p></div>
        <div className="dimension-list">
          {dimensions.map((item) => (
            <article className={`dimension-row${item.regression ? ' dimension-regression' : ''}`} key={item.dimension}>
              <div><strong>{item.label}</strong>{item.regression ? <small>Needs revision</small> : null}</div>
              <div className="dimension-bars"><div><span style={{ width: `${item.baseline_score}%` }} /></div><div><span style={{ width: `${item.wake_score}%` }} /></div></div>
              <div className="dimension-values"><span>{item.baseline_score.toFixed(2)}</span><span>{item.wake_score.toFixed(2)}</span></div>
              <strong className={item.regression ? 'negative-delta' : ''}>{item.delta > 0 ? '+' : ''}{item.delta.toFixed(2)}</strong>
            </article>
          ))}
        </div>
        <div className="evaluation-learning"><div><div className="kicker">Preserved failure</div><h3>Environmental interpretation: 80.00 → 76.00</h3></div><p>WAKE improved the wind-shift and calm cases but lost partial credit in the steady headwind, tailwind, and crosswind cases. The official output remains frozen; changing the prompt after seeing this result requires a new version and a fresh comparison.</p></div>
      </section>
    </main>
  );
}

export default function Home() {
  const client = useMemo(() => createWakeClient({ baseUrl: configuredRuntimeUrl }), []);
  const [screen, setScreen] = useState<Screen>('sessions');
  const [review, setReview] = useState<Review>(demoReview);
  const [checkpointId, setCheckpointId] = useState(demoReview.checkpoint.checkpointId);
  const [briefing, setBriefing] = useState<Briefing>(() => resolveCheckpoint(demoReview, 'UNKNOWN'));
  const [memory, setMemory] = useState<GoalMemory>(() => approveBriefingMemory(briefing, false));
  const [executionCost, setExecutionCost] = useState<ExecutionCost | null>(null);
  const [preparedBundle, setPreparedBundle] = useState<PreparedBundle | null>(null);
  const [weatherOutcome, setWeatherOutcome] = useState<WeatherOutcome>({ status: 'NOT_REQUESTED' });
  const [sessions, setSessions] = useState<SessionRecord[]>([]);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  async function reloadSessions() {
    const inbox = await client.listSessions();
    setSessions(inbox.sessions ?? []);
  }

  useEffect(() => {
    let active = true;
    client.listSessions().then((inbox) => {
      if (active) setSessions(inbox.sessions ?? []);
    }).catch((cause) => {
      if (active) setError(cause instanceof Error ? cause.message : 'WAKE could not load the session inbox.');
    });
    return () => { active = false; };
  }, [client]);

  function showSessionDetail(detail: SessionDetail) {
    if (detail.review) {
      setReview(detail.review);
      setCheckpointId(detail.checkpoint_id ?? detail.review.checkpoint.checkpointId);
    }
    if (detail.status === 'IN_CLUB_MEMORY' && detail.goal) {
      setMemory(detail.goal);
      setScreen('memory');
    } else if (detail.status === 'READY_FOR_COACH_APPROVAL' && detail.briefing) {
      setBriefing(detail.briefing);
      setScreen('briefing');
    } else if (detail.review) {
      setScreen('review');
    } else if (detail.bundle) {
      setPreparedBundle(detail.bundle);
      setScreen('intake');
    }
  }

  async function openSession(session: SessionRecord) {
    setProcessing(true);
    setError('');
    try {
      const detail = await client.getSession(session.session_id) as SessionDetail;
      if (detail.review) {
        await client.markSessionViewed(session.session_id);
      }
      showSessionDetail(detail);
      await reloadSessions();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'WAKE could not open this session.');
    } finally {
      setProcessing(false);
    }
  }

  async function investigate(files: EvidenceFiles = {}, contributorRole: ContributorRole = 'COACH', weather: WeatherRequest = { enabled: false, authorizedLocationLookup: false, sessionTimezone: '' }) { setProcessing(true); setError(''); setPreparedBundle(null); try { if (!Object.keys(files).length) { const sample = await client.createInvestigation({ mode: 'replay' }); if (sample.status === 'VERIFIED') { const detail = await client.getSession(sample.sessionId) as SessionDetail; await client.markSessionViewed(sample.sessionId); showSessionDetail(detail); await reloadSessions(); return; } await client.markSessionViewed(sample.sessionId); setReview(sample.review); setCheckpointId(sample.checkpointId); setExecutionCost(null); setWeatherOutcome({ status: 'NOT_REQUESTED' }); await reloadSessions(); setScreen('review'); return; } const uploaded = await uploadEvidenceBundleWithWeather(client, files, { uploadedByRole: contributorRole, weather }); const sourceIds = uploaded.sourceIds; setWeatherOutcome(uploaded.weather); if (configuredRuntimeMode === 'live') { const result = await client.analyzeSourceBundle({ sourceIds, mode: 'live', authorizedCostUsd: configuredCostAuthorizationUsd }); await client.markSessionViewed(result.sessionId); setReview(result.review); setCheckpointId(result.checkpointId); setExecutionCost(result.cost ?? null); await reloadSessions(); setScreen('review'); return; } const allReplayFilesSelected = evidenceSourceDefinitions.every(({ kind }) => files[kind as EvidenceKind]); if (allReplayFilesSelected && uploaded.weather.status !== 'ADDED') { const replay = await client.createInvestigation({ mode: 'replay', sourceIds }); await client.markSessionViewed(replay.sessionId); setReview(replay.review); setCheckpointId(replay.checkpointId); setExecutionCost(null); await reloadSessions(); setScreen('review'); return; } const prepared = await client.prepareSourceBundle(sourceIds); setPreparedBundle(prepared); await reloadSessions(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'WAKE could not investigate this session.'); } finally { setProcessing(false); } }
  async function completeReview(response: CheckpointResponse | 'UNKNOWN') { setProcessing(true); setError(''); try { const next = await client.answerCheckpoint(checkpointId, response); setBriefing(next); await reloadSessions(); setScreen('briefing'); } catch (cause) { setError(cause instanceof Error ? cause.message : 'WAKE could not verify this answer.'); } finally { setProcessing(false); } }
  async function approveMemory() { setProcessing(true); setError(''); try { const next = await client.approveBriefing(briefing.briefingId); setMemory(next); await reloadSessions(); setScreen('memory'); } catch (cause) { setError(cause instanceof Error ? cause.message : 'WAKE could not approve this memory.'); } finally { setProcessing(false); } }

  return <><AppHeader screen={screen} onNavigate={setScreen} />{screen === 'sessions' ? <SessionsScreen error={error} onNavigate={setScreen} onOpenSession={openSession} onReview={investigate} processing={processing} sessions={sessions} /> : null}{screen === 'intake' ? <IntakeScreen error={error} onInvestigate={investigate} preparedBundle={preparedBundle} processing={processing} weatherOutcome={weatherOutcome} /> : null}{screen === 'review' ? <ReviewScreen error={error} executionCost={executionCost} onComplete={completeReview} processing={processing} review={review} /> : null}{screen === 'briefing' ? <BriefingScreen briefing={briefing} error={error} onApprove={approveMemory} onBack={() => setScreen('review')} onLeave={() => setScreen('sessions')} processing={processing} /> : null}{screen === 'memory' ? <MemoryScreen memory={memory} onBack={() => setScreen('sessions')} /> : null}{screen === 'evaluation' ? <EvaluationScreen onBack={() => setScreen('sessions')} /> : null}</>;
}
