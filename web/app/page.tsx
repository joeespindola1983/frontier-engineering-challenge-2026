'use client';

import { useMemo, useState } from 'react';
import { buildStrokeRateGeometry, STROKE_RATE_DOMAIN } from './lib/chart-scale.mjs';
import { demoReview } from './lib/demo-review.mjs';
import { formatEvidenceKind, formatMeasurementRange } from './lib/display-format.mjs';
import { evidenceSourceDefinitions, uploadEvidenceBundleWithWeather } from './lib/evidence-intake.mjs';
import { createWakeClient } from './lib/product-client.mjs';
import { approveBriefingMemory, resolveCheckpoint } from './lib/workflow-state.mjs';

type Screen = 'sessions' | 'intake' | 'review' | 'briefing' | 'memory';
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
  status: string;
  agent_called: boolean;
  source_coverage: { kind: string; status: string }[];
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

function SessionsScreen({ onNavigate, onReview, processing, error }: { onNavigate: (screen: Screen) => void; onReview: () => void; processing: boolean; error: string }) {
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="page-header">
        <div className="page-header-copy">
          <div className="kicker">Daily intelligence</div>
          <h1>Review the session,<br />not every chart.</h1>
          <p className="lede">WAKE combines the plan, recordings, conditions, and attributed human context into one evidence-backed session review.</p>
        </div>
        <button className="button button-primary" onClick={() => onNavigate('intake')} type="button">Review a session</button>
      </header>
      <section className="summary-strip" aria-label="Session summary">
        <div><span>Needs review</span><strong>1</strong><small>One material question</small></div>
        <div><span>Processing</span><strong>0</strong><small>No active investigations</small></div>
        <div><span>Approved memory</span><strong>0</strong><small>Coach approval required</small></div>
        <div><span>Open conflicts</span><strong>2</strong><small>Preserved, not averaged</small></div>
      </section>
      {error ? <div className="runtime-error" role="alert">{error}</div> : null}
      <section className="session-list" aria-label="Session reviews">
        <button className="session-row" disabled={processing} onClick={() => onReview()} type="button">
          <div><div className="session-title">{demoReview.title}</div><div className="session-subtitle">Plan, SpeedCoach, mobile telemetry, and wind timeline</div></div>
          <div><span className="meta-label">Date</span><span>{formatDate(demoReview.scheduledDate)}</span></div>
          <div><span className="meta-label">Goal</span><span>Regatta preparation</span></div>
          <span className="status attention">Needs context</span>
        </button>
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
          {preparedBundle ? <div className="prepared-bundle" role="status"><span>Bundle prepared</span><strong>{preparedBundle.source_coverage.filter((source) => source.status === 'PRESENT').map((source) => formatEvidenceKind(source.kind)).join(' + ')}</strong><p>No agent call was made. The validated process-local evidence is ready for an explicitly authorized live investigation.</p></div> : null}
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
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  async function investigate(files: EvidenceFiles = {}, contributorRole: ContributorRole = 'COACH', weather: WeatherRequest = { enabled: false, authorizedLocationLookup: false, sessionTimezone: '' }) { setProcessing(true); setError(''); setPreparedBundle(null); try { if (!Object.keys(files).length) { const sample = await client.createInvestigation({ mode: 'replay' }); setReview(sample.review); setCheckpointId(sample.checkpointId); setExecutionCost(null); setWeatherOutcome({ status: 'NOT_REQUESTED' }); setScreen('review'); return; } const uploaded = await uploadEvidenceBundleWithWeather(client, files, { uploadedByRole: contributorRole, weather }); const sourceIds = uploaded.sourceIds; setWeatherOutcome(uploaded.weather); if (configuredRuntimeMode === 'live') { const result = await client.analyzeSourceBundle({ sourceIds, mode: 'live', authorizedCostUsd: configuredCostAuthorizationUsd }); setReview(result.review); setCheckpointId(result.checkpointId); setExecutionCost(result.cost ?? null); setScreen('review'); return; } const allReplayFilesSelected = evidenceSourceDefinitions.every(({ kind }) => files[kind as EvidenceKind]); if (allReplayFilesSelected && uploaded.weather.status !== 'ADDED') { const replay = await client.createInvestigation({ mode: 'replay', sourceIds }); setReview(replay.review); setCheckpointId(replay.checkpointId); setExecutionCost(null); setScreen('review'); return; } const prepared = await client.prepareSourceBundle(sourceIds); setPreparedBundle(prepared); } catch (cause) { setError(cause instanceof Error ? cause.message : 'WAKE could not investigate this session.'); } finally { setProcessing(false); } }
  async function completeReview(response: CheckpointResponse | 'UNKNOWN') { setProcessing(true); setError(''); try { const next = await client.answerCheckpoint(checkpointId, response); setBriefing(next); setScreen('briefing'); } catch (cause) { setError(cause instanceof Error ? cause.message : 'WAKE could not verify this answer.'); } finally { setProcessing(false); } }
  async function approveMemory() { setProcessing(true); setError(''); try { const next = await client.approveBriefing(briefing.briefingId); setMemory(next); setScreen('memory'); } catch (cause) { setError(cause instanceof Error ? cause.message : 'WAKE could not approve this memory.'); } finally { setProcessing(false); } }

  return <><AppHeader screen={screen} onNavigate={setScreen} />{screen === 'sessions' ? <SessionsScreen error={error} onNavigate={setScreen} onReview={investigate} processing={processing} /> : null}{screen === 'intake' ? <IntakeScreen error={error} onInvestigate={investigate} preparedBundle={preparedBundle} processing={processing} weatherOutcome={weatherOutcome} /> : null}{screen === 'review' ? <ReviewScreen error={error} executionCost={executionCost} onComplete={completeReview} processing={processing} review={review} /> : null}{screen === 'briefing' ? <BriefingScreen briefing={briefing} error={error} onApprove={approveMemory} onBack={() => setScreen('review')} onLeave={() => setScreen('sessions')} processing={processing} /> : null}{screen === 'memory' ? <MemoryScreen memory={memory} onBack={() => setScreen('sessions')} /> : null}</>;
}
