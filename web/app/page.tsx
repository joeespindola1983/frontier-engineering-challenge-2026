'use client';

import { useState } from 'react';
import { demoReview } from './lib/demo-review.mjs';
import { approveBriefingMemory, resolveCheckpoint } from './lib/workflow-state.mjs';

type Screen = 'sessions' | 'intake' | 'review' | 'briefing' | 'memory';
type Briefing = ReturnType<typeof resolveCheckpoint>;
type GoalMemory = ReturnType<typeof approveBriefingMemory>;

function formatDate(value: string) {
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
          <span className="demo-label">Synthetic demo data</span>
          <button className="button button-primary button-small" onClick={() => onNavigate('intake')} type="button">Review a session</button>
        </div>
      </div>
    </header>
  );
}

function PrototypeNotice() {
  return <div className="prototype-notice" role="note"><span>Prototype replay</span>{demoReview.notice}</div>;
}

function SessionsScreen({ onNavigate }: { onNavigate: (screen: Screen) => void }) {
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
      <section className="session-list" aria-label="Session reviews">
        <button className="session-row" onClick={() => onNavigate('review')} type="button">
          <div><div className="session-title">{demoReview.title}</div><div className="session-subtitle">Plan, SpeedCoach, mobile telemetry, and wind timeline</div></div>
          <div><span className="meta-label">Date</span><span>{formatDate(demoReview.scheduledDate)}</span></div>
          <div><span className="meta-label">Goal</span><span>Regatta preparation</span></div>
          <span className="status attention">Needs context</span>
        </button>
      </section>
    </main>
  );
}

function IntakeScreen({ onNavigate }: { onNavigate: (screen: Screen) => void }) {
  const sources = [
    ['Training plan', 'plan.json', 'Prescription and recovery structure'],
    ['SpeedCoach recording', 'speedcoach.csv', 'Distance, speed, route, and SPM'],
    ['Mobile recording', 'mobile.csv', 'Route corroboration; SPM rejected'],
    ['Environmental timeline', 'environment.json', 'Time-aligned wind observations'],
  ];
  return (
    <main className="page page-narrow">
      <PrototypeNotice />
      <header className="page-header">
        <div className="page-header-copy"><div className="kicker">New session review</div><h1>Bring the evidence together.</h1><p className="lede">Partial evidence is accepted. This replay uses the committed public synthetic case and never exposes evaluation ground truth.</p></div>
      </header>
      <div className="intake-layout">
        <section>
          <div className="kicker">Evidence ready</div>
          <div className="upload-list">
            {sources.map(([title, file, description], index) => (
              <div className="upload-row" key={file}><span className="upload-index">0{index + 1}</span><div><strong>{title}</strong><code>{file}</code><small>{description}</small></div><span className="ready-label">Ready</span></div>
            ))}
          </div>
          <div className="known-context"><div className="kicker">Known context</div><div className="context-grid"><span>Men&apos;s double scull (2x)</span><span>Two synthetic athletes</span><span>Regatta preparation</span><span>Water session</span></div></div>
          <button className="button button-primary" onClick={() => onNavigate('review')} type="button">Investigate session</button>
        </section>
        <aside className="process-note"><div className="kicker">What WAKE will do</div><ol><li>Match and align recordings.</li><li>Reconstruct plan blocks.</li><li>Select trust per metric.</li><li>Preserve unsupported unknowns.</li><li>Ask one material question.</li></ol></aside>
      </div>
    </main>
  );
}

function IntervalChart() {
  return (
    <section className="interval-chart" aria-labelledby="interval-title">
      <div className="chart-legend"><span id="interval-title">Average stroke rate by work interval</span><span>Shaded area = prescribed range</span></div>
      <div className="interval-bars">
        {demoReview.workIntervals.map((interval) => {
          const isDeviation = interval.status === 'DEVIATION';
          const height = Math.max(38, Math.min(88, interval.averageSpm * 3.25));
          return (
            <div className="interval-column" key={interval.segmentId} aria-label={`Work ${interval.index}: ${interval.averageSpm} SPM; target ${interval.targetMinSpm} to ${interval.targetMaxSpm} SPM; ${isDeviation ? 'deviation' : 'within range'}`}>
              <div className="interval-plot"><div className="target-band" />{interval.index === 4 ? <span className="wind-marker">Wind shift</span> : null}<div className={`interval-bar${isDeviation ? ' deviation' : ''}`} style={{ height: `${height}%` }} /></div>
              <div className="interval-label"><span>W{interval.index}</span><span>{Math.round(interval.averageSpm)} SPM</span></div><small>{interval.targetMinSpm}–{interval.targetMaxSpm} target</small>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function SourcePolicy() {
  const rows = [
    ['Stroke rate', demoReview.sourcePolicy.strokeRate], ['Distance', demoReview.sourcePolicy.distance],
    ['Route', demoReview.sourcePolicy.route], ['Environment', demoReview.sourcePolicy.environment],
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

function ReviewScreen({ onComplete }: { onComplete: (answer: string) => void }) {
  const [answer, setAnswer] = useState('UNKNOWN');
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="review-header"><div className="review-title"><div className="kicker">Session review</div><h1>{demoReview.title}</h1><div className="review-meta"><span>{formatDate(demoReview.scheduledDate)}</span><span>Plan + SpeedCoach + mobile + wind timeline</span><span>{demoReview.mobileClockOffsetS} s mobile clock offset</span></div></div><div className="review-state"><span className="status attention">Human context required</span><strong>One answer can change the briefing</strong></div></header>
      <div className="progress-line" aria-label="Session review progress"><span /></div>
      <div className="review-layout">
        <div><section><div className="kicker">Current reconstruction</div><p className="finding-intro">Six work intervals are supported by the evidence. Work interval five fell below its prescribed stroke-rate range. A tailwind-to-headwind shift is time-aligned with later speed changes; it is not treated as causal evidence or athlete regression.</p></section><IntervalChart /><SourcePolicy /><section className="environment-note"><div><div className="kicker">Environmental boundary</div><h2>Condition change, not a causal verdict</h2></div><p>{demoReview.environment.summary}</p></section></div>
        <aside className="checkpoint"><div className="kicker">One material question</div><h2>{demoReview.checkpoint.question}</h2><p>The plan prescribes the equipment change, but neither recording can observe whether it happened. WAKE keeps prescription and observation separate.</p>
          <fieldset className="answer-list"><legend className="sr-only">Resistance band confirmation</legend>{[['YES', 'Yes, it was used and removed as planned'], ['NO', 'No, it was not used as planned'], ['UNKNOWN', 'Unknown / cannot confirm']].map(([value, label]) => <label className="answer-option" key={value}><input checked={answer === value} name="band" onChange={() => setAnswer(value)} type="radio" value={value} />{label}</label>)}</fieldset>
          <div className="checkpoint-actions"><button className="button button-primary" onClick={() => onComplete(answer)} type="button">Save answer and finish</button><button className="button button-quiet" onClick={() => onComplete('UNKNOWN')} type="button">Keep unknown</button></div>
          <div className="evidence-note"><strong>Why this matters:</strong> {demoReview.checkpoint.whyItMatters}</div><p className="checkpoint-status">No memory is updated until the coach approves the briefing.</p>
        </aside>
      </div>
    </main>
  );
}

function BriefingScreen({ briefing, onBack, onApprove, onLeave }: { briefing: Briefing; onBack: () => void; onApprove: () => void; onLeave: () => void }) {
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="page-header"><div className="page-header-copy"><div className="kicker">Verified session briefing</div><h1>{briefing.title}</h1><p className="lede">A coach-facing result with findings, limitations, and source choices kept together.</p></div><button className="button" onClick={onBack} type="button">Review evidence</button></header>
      <div className="brief-grid"><div><section className="brief-lead"><p>{briefing.headline}</p><small>{briefing.summary}</small></section>
        <section><div className="kicker">Plan versus performed</div>{briefing.workIntervals.map((interval) => <div className={`metric-line${interval.status === 'DEVIATION' ? ' deviation' : ''}`} key={interval.segmentId}><span>{String(interval.index).padStart(2, '0')}</span><strong>{interval.plannedDistanceM.toLocaleString('en-US')} m</strong><code>{formatDuration(interval.durationS)} · {interval.averageSpm.toFixed(1)} SPM</code><span>{interval.status === 'DEVIATION' ? 'SPM deviation' : 'Within range'}</span></div>)}</section>
        <section className="findings"><div className="kicker">Verified findings</div>{briefing.findings.map((finding) => <article className={`finding-row ${finding.status === 'ATTENTION' || finding.status === 'UNKNOWN' ? 'warning' : ''}`} key={finding.title}><span>●</span><div><strong>{finding.title}</strong><p>{finding.explanation}</p>{finding.evidenceRefs.map((ref) => <code className="evidence-tag" key={ref}>{ref.replace('input/', '')}</code>)}</div></article>)}</section>
      </div><aside className="brief-aside"><section><div className="kicker">Evidence status</div><h3>Verified with preserved boundaries</h3><p>Material claims retain sources. Technique and physiology were not inferred from ordinary telemetry.</p></section><section><div className="kicker">Human context</div><h3>{briefing.equipment.status === 'UNKNOWN' ? 'Equipment remains unknown' : 'Coach confirmation retained'}</h3><p>{briefing.equipment.statement}</p></section><section><div className="kicker">Memory proposal</div><h3>Save one reviewed session</h3><p>Approval stores this briefing and unresolved questions; it does not create a performance trend.</p></section><div className="aside-actions"><button className="button button-primary" onClick={onApprove} type="button">Approve memory update</button><button className="button" onClick={onLeave} type="button">Leave session unchanged</button></div></aside></div>
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
  const [screen, setScreen] = useState<Screen>('sessions');
  const [briefing, setBriefing] = useState<Briefing>(() => resolveCheckpoint(demoReview, 'UNKNOWN'));
  const [memory, setMemory] = useState<GoalMemory>(() => approveBriefingMemory(briefing, false));

  function completeReview(answer: string) { const next = resolveCheckpoint(demoReview, answer); setBriefing(next); setScreen('briefing'); }
  function approveMemory() { setMemory(approveBriefingMemory(briefing, true)); setScreen('memory'); }

  return <><AppHeader screen={screen} onNavigate={setScreen} />{screen === 'sessions' ? <SessionsScreen onNavigate={setScreen} /> : null}{screen === 'intake' ? <IntakeScreen onNavigate={setScreen} /> : null}{screen === 'review' ? <ReviewScreen onComplete={completeReview} /> : null}{screen === 'briefing' ? <BriefingScreen briefing={briefing} onApprove={approveMemory} onBack={() => setScreen('review')} onLeave={() => setScreen('sessions')} /> : null}{screen === 'memory' ? <MemoryScreen memory={memory} onBack={() => setScreen('sessions')} /> : null}</>;
}
