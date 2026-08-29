'use client';

import { useMemo, useState } from 'react';
import { demoReview } from './lib/demo-review.mjs';
import { evidenceSourceDefinitions, uploadEvidenceBundle } from './lib/evidence-intake.mjs';
import { createWakeClient } from './lib/product-client.mjs';
import { approveBriefingMemory, resolveCheckpoint } from './lib/workflow-state.mjs';

type Screen = 'sessions' | 'intake' | 'review' | 'briefing' | 'memory';
type Briefing = ReturnType<typeof resolveCheckpoint>;
type GoalMemory = ReturnType<typeof approveBriefingMemory>;
type Review = typeof demoReview;
type EvidenceKind = 'PLAN' | 'SPEEDCOACH' | 'MOBILE' | 'ENVIRONMENT' | 'CONTEXT';
type EvidenceFiles = Partial<Record<EvidenceKind, File>>;

const configuredRuntimeUrl = process.env.NEXT_PUBLIC_WAKE_API_URL ?? '';
const configuredRuntimeMode = process.env.NEXT_PUBLIC_WAKE_RUNTIME_MODE === 'live' ? 'live' : 'replay';

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
          <p className="lede">WAKE combines the plan, recordings, conditions, and coach confirmations into one evidence-backed session review.</p>
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
        <button className="session-row" disabled={processing} onClick={onReview} type="button">
          <div><div className="session-title">{demoReview.title}</div><div className="session-subtitle">Plan, SpeedCoach, mobile telemetry, and wind timeline</div></div>
          <div><span className="meta-label">Date</span><span>{formatDate(demoReview.scheduledDate)}</span></div>
          <div><span className="meta-label">Goal</span><span>Regatta preparation</span></div>
          <span className="status attention">Needs context</span>
        </button>
      </section>
    </main>
  );
}

function IntakeScreen({ onInvestigate, processing, error }: { onInvestigate: (files: EvidenceFiles) => void; processing: boolean; error: string }) {
  const [files, setFiles] = useState<EvidenceFiles>({});
  const hasSelectedFiles = Object.keys(files).length > 0;
  return (
    <main className="page page-narrow">
      <PrototypeNotice />
      <header className="page-header">
        <div className="page-header-copy"><div className="kicker">New session review</div><h1>Bring the evidence together.</h1><p className="lede">Start with the training plan and SpeedCoach recording. Optional evidence expands what WAKE can verify without blocking the core review.</p></div>
      </header>
      <div className="intake-layout">
        <section>
          <div className="kicker">Evidence ready</div>
          <div className="upload-list">
            {evidenceSourceDefinitions.map((source, index) => {
              const selected = files[source.kind as EvidenceKind];
              return (
                <div className="upload-row" key={source.kind}><span className="upload-index">0{index + 1}</span><div><strong>{source.title} · {source.required ? 'Core' : 'Optional'}</strong><code>{selected?.name ?? source.defaultName}</code><small>{source.description}</small></div>{configuredRuntimeUrl ? <label className="upload-file-action">{selected ? 'Selected' : 'Choose'}<input accept={source.accept} className="sr-only" disabled={processing} onChange={(event) => { const file = event.target.files?.[0]; if (file) setFiles((current) => ({ ...current, [source.kind]: file })); }} type="file" /></label> : <span className="ready-label">Ready sample</span>}</div>
              );
            })}
          </div>
          {hasSelectedFiles ? <p className="upload-boundary">Plan and SpeedCoach enable the core review. Missing mobile, environment, or context will remain visible as evidence gaps. A different bundle cannot reuse the committed replay.</p> : null}
          <div className="known-context"><div className="kicker">Known context</div>{hasSelectedFiles ? <p>{files.CONTEXT ? 'Boat, crew, goal, and observations will be read from the selected context file.' : 'No context file selected. Boat, crew, goal, and human observations will remain unknown.'}</p> : <div className="context-grid"><span>Men&apos;s double scull (2x)</span><span>Two synthetic athletes</span><span>Regatta preparation</span><span>Water session</span></div>}</div>
          {error ? <div className="runtime-error" role="alert">{error}</div> : null}
          <button className="button button-primary" disabled={processing} onClick={() => onInvestigate(files)} type="button">{processing ? 'Investigating…' : hasSelectedFiles ? 'Validate and investigate' : 'Investigate sample session'}</button>
        </section>
        <aside className="process-note"><div className="kicker">What WAKE will do</div><ol><li>Match and align recordings.</li><li>Reconstruct plan blocks.</li><li>Select trust per metric.</li><li>Preserve unsupported unknowns.</li><li>Ask one material question.</li></ol></aside>
      </div>
    </main>
  );
}

function IntervalChart({ review }: { review: Review }) {
  return (
    <section className="interval-chart" aria-labelledby="interval-title">
      <div className="chart-legend"><span id="interval-title">Average stroke rate by work interval</span><span>Shaded area = prescribed range</span></div>
      <div className="interval-bars">
        {review.workIntervals.map((interval) => {
          const isDeviation = interval.status === 'DEVIATION';
          const height = Math.max(38, Math.min(88, interval.averageSpm * 3.25));
          return (
            <div className="interval-column" key={interval.segmentId} aria-label={`Work ${interval.index}: ${interval.averageSpm} SPM; target ${interval.targetMinSpm} to ${interval.targetMaxSpm} SPM; ${isDeviation ? 'deviation' : 'within range'}`}>
              <div className="interval-plot"><div className="target-band" /><div className={`interval-bar${isDeviation ? ' deviation' : ''}`} style={{ height: `${height}%` }} /></div>
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

function ReviewScreen({ review, onComplete, processing, error }: { review: Review; onComplete: (answer: string) => void; processing: boolean; error: string }) {
  const [answer, setAnswer] = useState('UNKNOWN');
  const questionRequired = review.status === 'QUESTION_REQUIRED';
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="review-header"><div className="review-title"><div className="kicker">Session review</div><h1>{review.title}</h1><div className="review-meta"><span>{formatDate(review.scheduledDate)}</span><span>Plan + SpeedCoach + mobile + environment</span>{review.mobileClockOffsetS == null ? null : <span>{review.mobileClockOffsetS} s mobile clock offset</span>}</div></div><div className="review-state"><span className={`status ${questionRequired ? 'attention' : 'approved'}`}>{questionRequired ? 'Human context required' : 'Ready for review'}</span><strong>{questionRequired ? 'One answer can change the briefing' : 'No additional question was requested'}</strong></div></header>
      <div className="progress-line" aria-label="Session review progress"><span /></div>
      <div className="review-layout">
        <div><section><div className="kicker">Current reconstruction</div><p className="finding-intro">{review.currentReconstruction}</p></section><IntervalChart review={review} /><SourcePolicy review={review} /><section className="environment-note"><div><div className="kicker">Environmental boundary</div><h2>Condition context, not a causal verdict</h2></div><p>{review.environment.summary}</p></section></div>
        <aside className="checkpoint"><div className="kicker">{questionRequired ? 'One material question' : 'Human review'}</div><h2>{review.checkpoint.question}</h2><p>A coach answer is stored as human context. It does not alter the device measurements or turn an unsupported claim into observed telemetry.</p>
          <fieldset className="answer-list"><legend className="sr-only">Coach confirmation</legend>{[['YES', 'Yes / confirmed'], ['NO', 'No / not confirmed'], ['UNKNOWN', 'Unknown / cannot confirm']].map(([value, label]) => <label className="answer-option" key={value}><input checked={answer === value} name="confirmation" onChange={() => setAnswer(value)} type="radio" value={value} />{label}</label>)}</fieldset>
          {error ? <div className="runtime-error" role="alert">{error}</div> : null}<div className="checkpoint-actions"><button className="button button-primary" disabled={processing} onClick={() => onComplete(answer)} type="button">{processing ? 'Verifying…' : 'Save answer and finish'}</button><button className="button button-quiet" disabled={processing} onClick={() => onComplete('UNKNOWN')} type="button">Keep unknown</button></div>
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
      </div><aside className="brief-aside"><section><div className="kicker">Evidence status</div><h3>Verified with preserved boundaries</h3><p>Material claims retain sources. Technique and physiology were not inferred from ordinary telemetry.</p></section><section><div className="kicker">Human context</div><h3>{briefing.equipment.status === 'UNKNOWN' ? 'Equipment remains unknown' : 'Coach confirmation retained'}</h3><p>{briefing.equipment.statement}</p></section><section><div className="kicker">Memory proposal</div><h3>Save one reviewed session</h3><p>Approval stores this briefing and unresolved questions; it does not create a performance trend.</p></section><div className="aside-actions">{error ? <div className="runtime-error" role="alert">{error}</div> : null}<button className="button button-primary" disabled={processing} onClick={onApprove} type="button">{processing ? 'Approving…' : 'Approve memory update'}</button><button className="button" disabled={processing} onClick={onLeave} type="button">Leave session unchanged</button></div></aside></div>
    </main>
  );
}

function MemoryScreen({ memory, onBack }: { memory: GoalMemory; onBack: () => void }) {
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="page-header"><div className="page-header-copy"><div className="kicker">Goal memory</div><h1>{memory.title}</h1><p className="lede">Only coach-approved evidence enters this history. One session is context, not a trend.</p></div><button className="button" onClick={onBack} type="button">Back to sessions</button></header>
      <section className="memory-conclusion"><div className="kicker">Current conclusion</div><p>{memory.currentConclusion}</p></section>
      <div className="memory-layout"><section><div className="kicker">Approved evidence</div>{memory.approvedSessions.length ? memory.approvedSessions.map((session) => <article className="memory-row" key={session.sessionId}><time>{formatDate(demoReview.scheduledDate)}</time><div><h3>{session.title}</h3><p>{session.summary}</p><small>{session.equipment.statement}</small></div><span className="status approved">Coach approved</span></article>) : <div className="empty-state"><h2>No approved sessions yet.</h2><p>Review a briefing and explicitly approve its memory proposal.</p></div>}</section>
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
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');

  async function investigate(files: EvidenceFiles = {}) { setProcessing(true); setError(''); try { const sourceIds = Object.keys(files).length ? await uploadEvidenceBundle(client, files) : undefined; const result = await client.createInvestigation({ mode: configuredRuntimeMode, sourceIds }); setReview(result.review); setCheckpointId(result.checkpointId); setScreen('review'); } catch (cause) { setError(cause instanceof Error ? cause.message : 'WAKE could not investigate this session.'); } finally { setProcessing(false); } }
  async function completeReview(answer: string) { setProcessing(true); setError(''); try { const next = await client.answerCheckpoint(checkpointId, answer); setBriefing(next); setScreen('briefing'); } catch (cause) { setError(cause instanceof Error ? cause.message : 'WAKE could not verify this answer.'); } finally { setProcessing(false); } }
  async function approveMemory() { setProcessing(true); setError(''); try { const next = await client.approveBriefing(briefing.briefingId); setMemory(next); setScreen('memory'); } catch (cause) { setError(cause instanceof Error ? cause.message : 'WAKE could not approve this memory.'); } finally { setProcessing(false); } }

  return <><AppHeader screen={screen} onNavigate={setScreen} />{screen === 'sessions' ? <SessionsScreen error={error} onNavigate={setScreen} onReview={investigate} processing={processing} /> : null}{screen === 'intake' ? <IntakeScreen error={error} onInvestigate={investigate} processing={processing} /> : null}{screen === 'review' ? <ReviewScreen error={error} onComplete={completeReview} processing={processing} review={review} /> : null}{screen === 'briefing' ? <BriefingScreen briefing={briefing} error={error} onApprove={approveMemory} onBack={() => setScreen('review')} onLeave={() => setScreen('sessions')} processing={processing} /> : null}{screen === 'memory' ? <MemoryScreen memory={memory} onBack={() => setScreen('sessions')} /> : null}</>;
}
