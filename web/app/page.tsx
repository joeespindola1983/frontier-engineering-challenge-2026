'use client';

import { useEffect, useMemo, useState } from 'react';
import { buildStrokeRateGeometry, STROKE_RATE_DOMAIN } from './lib/chart-scale.mjs';
import { buildClubPeriodAnalysis } from './lib/club-intelligence.mjs';
import { demoCompetitionReview } from './lib/competition-review.mjs';
import { buildLongitudinalPilot } from './lib/longitudinal-intelligence.mjs';
import { demoClub, listCoachAttention, summarizeAthlete, summarizeClub, summarizeCrew } from './lib/demo-club.mjs';
import { demoReview } from './lib/demo-review.mjs';
import { formatEvidenceKind, formatMeasurementRange } from './lib/display-format.mjs';
import { evidenceSourceDefinitions, uploadEvidenceBundleWithWeather } from './lib/evidence-intake.mjs';
import { evaluationResults } from './lib/evaluation-results.mjs';
import { createWakeClient } from './lib/product-client.mjs';
import { sessionActionLabel, sessionStatusLabel, summarizeSessionInbox } from './lib/session-inbox.mjs';
import { approveBriefingMemory, resolveCheckpoint } from './lib/workflow-state.mjs';

type Screen = 'sessions' | 'club-crew' | 'club-athlete' | 'longitudinal-pilot' | 'competition' | 'intake' | 'review' | 'briefing' | 'memory' | 'evaluation';
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
  const sessionActive = ['sessions', 'club-crew', 'club-athlete', 'longitudinal-pilot', 'intake', 'review', 'briefing'].includes(screen);
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <button className="brand" onClick={() => onNavigate('sessions')} type="button">
          <span className="brand-mark" aria-hidden="true">≋</span><span>WAKE</span>
        </button>
        <nav className="primary-nav" aria-label="Primary navigation">
          <button className={sessionActive ? 'active' : ''} onClick={() => onNavigate('sessions')} type="button">Sessions</button>
          <button className={screen === 'competition' ? 'active' : ''} onClick={() => onNavigate('competition')} type="button">Competition</button>
          <button className={screen === 'memory' ? 'active' : ''} onClick={() => onNavigate('memory')} type="button">Goal memory</button>
          <button className={screen === 'evaluation' ? 'active' : ''} onClick={() => onNavigate('evaluation')} type="button">Evaluation</button>
        </nav>
        <div className="topbar-actions">
          <span className="demo-label">{configuredRuntimeMode === 'live' ? 'Local live runtime' : 'Real-informed synthetic demo'}</span>
          <button className="button button-primary button-small" onClick={() => onNavigate('intake')} type="button">Review a session</button>
        </div>
      </div>
    </header>
  );
}

function PrototypeNotice() {
  return <div className="prototype-notice" role="note"><span>{configuredRuntimeMode === 'live' ? 'Local live runtime' : 'Real-informed synthetic demo'}</span>{configuredRuntimeMode === 'live' ? 'The bounded WAKE agent is enabled. Uploaded evidence stays in the local process and every execution requires an explicit review action.' : 'Identities, club history, and session outcomes are fictional. Training patterns, source formats, value ranges, and operational failure modes were modeled from real rowing material supplied for this project.'}</div>;
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

function clubCategoryLabel(value: string) {
  return { MEN: 'Men', WOMEN: 'Women', MIXED: 'Mixed' }[value] ?? value;
}

function clubActivityLabel(value: string) {
  return { WATER_CREW: 'Crew water session', WATER_SOLO: 'Solo water session', ERG: 'Ergometer' }[value] ?? value;
}

function clubReviewLabel(value: string) {
  return {
    NO_MATERIAL_FLAG: 'No material flag',
    NEEDS_COACH_REVIEW: 'Coach review needed',
    READY_FOR_INVESTIGATION: 'Plan link missing',
    AWAITING_ATHLETE_CONTEXT: 'Athlete context pending',
    RECORDED_ALTERNATIVE: 'Alternative recorded',
    ALTERNATIVE_TRAINING_REVIEW: 'Crew unavailable',
  }[value] ?? value.replaceAll('_', ' ').toLowerCase();
}

function trainingDayLabel(value: string) {
  return {
    COMBINED: 'Combined day',
    INDOOR_ONLY: 'Indoor-only',
    WATER_ONLY: 'Water-only',
    EXPECTED_MISSING: 'Expected record missing',
  }[value] ?? value.replaceAll('_', ' ').toLowerCase();
}

function trainingRoleLabel(value: string) {
  return {
    PRIMARY: 'Primary session',
    PRE_WATER: 'Before water',
    POST_WATER: 'After water',
    ALTERNATIVE: 'Planned alternative',
  }[value] ?? value.replaceAll('_', ' ').toLowerCase();
}

function ergWorkoutLabel(value: string) {
  return {
    FIXED_DISTANCE: 'Fixed distance',
    FIXED_TIME: 'Fixed time',
    INTERVAL: 'Intervals',
  }[value] ?? value.replaceAll('_', ' ').toLowerCase();
}

function competitionCategoryLabel(value: string) {
  return {
    BEGINNER: 'Beginner',
    ASPIRANT: 'Aspirant',
    JUNIOR: 'Junior',
    SENIOR: 'Senior',
    MASTER_B: 'Master B',
    MASTER_C: 'Master C',
    MASTER_D: 'Master D',
    MASTER_E: 'Master E',
    PARA_PR1: 'Para-rowing PR1',
    PARA_PR2: 'Para-rowing PR2',
    PARA_PR3: 'Para-rowing PR3',
  }[value] ?? value.replaceAll('_', ' ').toLowerCase();
}

function formatRaceTime(seconds: number | null) {
  if (seconds === null) return 'N/C';
  const minutes = Math.floor(seconds / 60);
  return `${minutes}:${(seconds % 60).toFixed(1).padStart(4, '0')}`;
}

function ClubOverview({ onOpenCrew, onOpenAthlete, onOpenLongitudinalPilot }: { onOpenCrew: (crewId: string) => void; onOpenAthlete: (athleteId: string) => void; onOpenLongitudinalPilot: () => void }) {
  const summary = summarizeClub(demoClub);
  const attention = listCoachAttention(demoClub);
  const intelligence = buildClubPeriodAnalysis(demoClub);
  const pilot = buildLongitudinalPilot(demoClub);
  return (
    <section className="club-overview" aria-labelledby="club-pulse-title">
      <div className="club-overview-heading"><div><div className="kicker">Real-informed synthetic data · 17–28 Aug 2026</div><h2 id="club-pulse-title">Two-week club pulse</h2><p>Ten named crews share sixteen athletes across 2x, 4x, and 8x boats. WAKE surfaces the records that need attention without asking the coach to open every outing.</p></div><span className="saved-evidence-label">Deterministic scan complete · 2 verified agent calls</span></div>
      <div className="club-provenance-note"><div><span>What is grounded in reality</span><strong>Structure, formats, and plausible rowing patterns</strong><p>The demonstration was modeled from real coach plans, WhatsApp and spreadsheet-style prescriptions, SpeedCoach CSVs, WAKE mobile exports, and first-hand rowing-club context.</p></div><div><span>What remains fictional</span><strong>People, club history, and exact outcomes</strong><p>Names, lineups, physical-boat names, exact sessions, results, and aggregates do not describe real athletes. Real-informed is not statistically representative.</p></div></div>
      <section className="club-intelligence-status" aria-label="Club intelligence status"><div><span>Records screened</span><strong>{intelligence.coverage.activities_scanned}/{demoClub.activities.length}</strong><small>all recorded activities</small></div><div><span>Deep investigations</span><strong>{intelligence.deep_investigations.completed}/{intelligence.deep_investigations.queued}</strong><small>verified candidate outputs</small></div><div><span>Human or source routes</span><strong>{intelligence.routing.HUMAN_CONTEXT + intelligence.routing.ATHLETE_QUESTION + intelligence.routing.SOURCE_REQUEST}</strong><small>kept outside paid triage</small></div><div><span>Observed agent cost</span><strong>US${intelligence.cost_observed.approximate_total_cost_usd.toFixed(2)}</strong><small>{intelligence.cost_observed.total_tokens.toLocaleString('en-US')} tokens · 2 executions</small></div></section>
      <div className="club-intelligence-boundary" role="note"><strong>Two bounded investigations completed.</strong><span>Both candidate outputs passed deterministic verification for a combined US${intelligence.cost_observed.approximate_total_cost_usd.toFixed(6)}. Human and missing-source questions remain explicit. Longitudinal synthesis has not run and still requires separate authorization.</span></div>
      <section className="club-batch-validation" aria-labelledby="club-batch-validation-title">
        <div className="section-heading compact-heading"><div><div className="kicker">Mass intake · session-level isolation</div><h3 id="club-batch-validation-title">Two-week validation funnel</h3></div><p>Every source remains attached to one activity.</p></div>
        <div className="club-batch-funnel">
          <div><span>Received</span><strong>{intelligence.batch_validation.counts.records_received}</strong><small>independent activity records</small></div>
          <div><span>Data validated</span><strong>{intelligence.batch_validation.counts.data_validated}</strong><small>hash and source checks passed</small></div>
          <div><span>Reconstructed</span><strong>{intelligence.batch_validation.counts.sessions_reconstructed}</strong><small>water and indoor records</small></div>
          <div><span>Plan compared</span><strong>{intelligence.batch_validation.counts.plan_compared}</strong><small>prescription available</small></div>
          <div><span>Agent verified</span><strong>{intelligence.batch_validation.counts.agent_verified}</strong><small>selected exception cases</small></div>
          <div><span>Human approved</span><strong>{intelligence.batch_validation.counts.human_approved}</strong><small>not claimed before review</small></div>
        </div>
        <div className="club-batch-boundary" role="note"><strong>52 sessions reconstructed, including 14 individual synthetic Concept2 transcription records.</strong><span>Thirty-one water sessions had no material signal in the available evidence, seventeen sessions were reconstructed alternatives, one needs its plan, and one needs athlete context. Each PM5 result belongs to one athlete; the real reference transcriptions were human-confirmed and photo OCR is not claimed.</span></div>
      </section>
      <section className="club-investigation-results" aria-labelledby="club-investigation-results-title"><div className="section-heading compact-heading"><div><div className="kicker">Saved agent evidence</div><h3 id="club-investigation-results-title">Verified investigation results</h3></div><p>Two selected candidates · no synthesis</p></div><div className="club-investigation-result-grid">{intelligence.deep_investigations.results.map((result) => <article key={result.case_id}><div><span>{result.deviation_segment} · {result.deviation_type.replaceAll('_', ' ').toLowerCase()}</span><strong>{result.title}</strong></div><p>{result.briefing}</p><footer><span>{result.next_step}</span><small>US${result.approximate_cost_usd.toFixed(6)} · {result.total_tokens.toLocaleString('en-US')} tokens</small></footer></article>)}</div></section>
      <section className="longitudinal-pilot-card" aria-labelledby="longitudinal-pilot-card-title">
        <div><div className="kicker">Selective synthesis · ready, not executed</div><h3 id="longitudinal-pilot-card-title">Longitudinal intelligence pilot</h3><p>Two frozen cases test whether GPT adds useful evidence-linked prioritization after deterministic screening: one athlete briefing and one club briefing.</p></div>
        <div className="longitudinal-pilot-summary"><span><strong>0 paid calls</strong><small>no model output yet</small></span><span><strong>{pilot.execution_plan.total_paid_starts} planned starts</strong><small>baseline × WAKE</small></span><span><strong>US${pilot.execution_plan.authorization_gate_total_usd.toFixed(2)} authorization</strong><small>start gate, not provider cap</small></span></div>
        <button className="button button-primary" onClick={onOpenLongitudinalPilot} type="button">Inspect pilot design</button>
      </section>
      <div className="club-summary-grid" aria-label="Club activity summary">
        <div><span>Crews monitored</span><strong>{summary.crewCount}</strong><small>4 × 2x · 4 × 4x · 2 × 8x</small></div>
        <div><span>Athletes connected</span><strong>{summary.athleteCount}</strong><small>{summary.physicalBoatCount} physical boats used</small></div>
        <div><span>Crew outings</span><strong>{summary.completedCrewOutings}/{summary.plannedOutings}</strong><small>{summary.disruptedCrewOutings} crews did not launch</small></div>
        <div><span>Coach attention</span><strong>{summary.attentionCount}</strong><small>{summary.participationGaps} expected days lack a record</small></div>
      </div>
      <section className="training-day-overview" aria-labelledby="training-day-overview-title">
        <div className="section-heading compact-heading"><div><div className="kicker">Athlete-centered chronology</div><h3 id="training-day-overview-title">Training days connect water and indoor work.</h3></div><p>Volumes remain separated by modality.</p></div>
        <div className="training-day-overview-grid">
          <div><span>Active athlete-days</span><strong>{summary.activeAthleteDays}</strong><small>individual days with a recorded activity</small></div>
          <div><span>Combined days</span><strong>{summary.combinedDays}</strong><small>water plus Concept2 on the same plan-confirmed day</small></div>
          <div><span>Indoor-only days</span><strong>{summary.indoorOnlyDays}</strong><small>valid training, not a missing water session</small></div>
          <div><span>Modality volume</span><strong>{summary.waterDistanceKm.toFixed(1)} / {summary.ergDistanceKm.toFixed(1)} km</strong><small>water / indoor — never merged</small></div>
        </div>
        <div className="training-day-boundary" role="note"><strong>One PM5 result, one athlete.</strong><span>Shared indoor prescriptions create individual records. Pace, SPM, and watts support comparison within equivalent Concept2 workouts; they are not presented as direct measures of on-water speed, visible technique, or muscular strength.</span></div>
      </section>
      <div className="club-pulse-layout">
        <section className="club-attention" aria-labelledby="club-attention-title"><div className="section-heading compact-heading"><div><div className="kicker">Prioritized review</div><h3 id="club-attention-title">What changed the two-week picture</h3></div><p>{summary.recordedActivities} activities · {summary.waterDistanceKm.toFixed(1)} km water · {summary.ergDistanceKm.toFixed(1)} km indoor</p></div><div className="club-attention-list">{attention.map((item) => <button key={item.attention_id} onClick={() => item.kind === 'PARTICIPATION_GAP' ? onOpenAthlete(item.entity_id) : onOpenCrew(item.entity_id)} type="button"><time>{formatDate(item.date)}</time><div><strong>{item.entity_name}</strong><p>{item.statement}</p></div><span>{item.kind === 'PARTICIPATION_GAP' ? 'Athlete' : 'Crew'} →</span></button>)}</div></section>
        <aside className="club-boundary"><div className="kicker">Interpretation boundary</div><h3>An alert is a question, not a verdict.</h3><p>A missing activity may reflect availability, an unlinked device, a planned rest day, or an unreported session. WAKE asks for context and does not infer fitness, injury, or commitment.</p></aside>
      </div>
      <section className="crew-groups" aria-labelledby="crew-groups-title"><div className="section-heading compact-heading"><div><div className="kicker">Team and crew memory</div><h3 id="crew-groups-title">Every outing stays attached to people and a physical boat.</h3></div><p>Select a crew to inspect its lineup and two-week history.</p></div>{['2x', '4x', '8x'].map((boatClass) => <div className="crew-class-group" key={boatClass}><div className="crew-class-label"><strong>{boatClass}</strong><span>{demoClub.crews.filter((crew) => crew.boat_class === boatClass).length} crews</span></div><div className="crew-card-grid">{demoClub.crews.filter((crew) => crew.boat_class === boatClass).map((crew) => { const crewSummary = summarizeCrew(demoClub, crew.crew_id); return <button className="crew-card" key={crew.crew_id} onClick={() => onOpenCrew(crew.crew_id)} type="button"><div><span>{clubCategoryLabel(crew.category)} · {crew.boat_class}</span><strong>{crew.name}</strong><small>{crewSummary.boat.name} · {crewSummary.lineup.map((seat) => seat.athlete.name).join(' · ')}</small></div><div className="crew-card-result"><strong>{crewSummary.completedOutings}/{crewSummary.plannedOutings}</strong><span>launched</span>{crewSummary.attentionCount ? <small>{crewSummary.attentionCount} to review</small> : <small>no material flags</small>}</div></button>; })}</div></div>)}</section>
      <section className="athlete-roster" aria-labelledby="athlete-roster-title"><div className="section-heading compact-heading"><div><div className="kicker">Athlete paths</div><h3 id="athlete-roster-title">The same athlete can contribute across several crews.</h3></div><p>Open an athlete to see crew, solo, ergometer, and boat history.</p></div><div className="athlete-chip-grid">{demoClub.athletes.map((athlete) => { const athleteSummary = summarizeAthlete(demoClub, athlete.athlete_id); return <button key={athlete.athlete_id} onClick={() => onOpenAthlete(athlete.athlete_id)} type="button"><span>{athlete.name}</span><small>{athleteSummary.activeDays} active days · {athleteSummary.crews.length} crews{athleteSummary.participationGaps.length ? ` · ${athleteSummary.participationGaps.length} gap` : ''}</small></button>; })}</div></section>
    </section>
  );
}

function CrewScreen({ crewId, onBack, onOpenAthlete }: { crewId: string; onBack: () => void; onOpenAthlete: (athleteId: string) => void }) {
  const crew = summarizeCrew(demoClub, crewId);
  return <main className="page club-detail-page"><div className="prototype-notice" role="note"><span>Real-informed synthetic data</span>Identities and exact outcomes are fictional; workout patterns, source structures, and value ranges are grounded in the supplied real rowing material.</div><header className="page-header club-detail-header"><div className="page-header-copy"><div className="kicker">{clubCategoryLabel(crew.category)} · {crew.boat_class} · {crew.boat.name}</div><h1>{crew.name}</h1><p className="lede">A crew is stored as a lineup snapshot linked to one physical boat and every outing. Changing an athlete or seat creates new historical context instead of rewriting the past.</p></div><button className="button" onClick={onBack} type="button">Back to club</button></header><section className="club-detail-stats"><div><span>Launched</span><strong>{crew.completedOutings}/{crew.plannedOutings}</strong><small>planned crew outings</small></div><div><span>Distance</span><strong>{crew.distanceKm.toFixed(1)} km</strong><small>completed crew water sessions</small></div><div><span>Needs review</span><strong>{crew.attentionCount}</strong><small>findings or unavailable outings</small></div><div><span>Physical boat</span><strong>{crew.boat.name}</strong><small>{crew.boat.boat_class} club asset</small></div></section><div className="club-detail-layout"><section><div className="section-heading compact-heading"><div><div className="kicker">Lineup</div><h2>People behind the boat</h2></div></div><div className="lineup-list">{crew.lineup.map((seat) => { const athlete = summarizeAthlete(demoClub, seat.athlete_id); return <button key={seat.athlete_id} onClick={() => onOpenAthlete(seat.athlete_id)} type="button"><span className="seat-number">{seat.seat}</span><div><strong>{seat.athlete.name}</strong><small>{seat.role.toLowerCase()} · {athlete.activeDays} active days · {athlete.crews.length} crews</small></div><span>Open athlete →</span></button>; })}</div></section><aside className="club-boundary"><div className="kicker">Crew evidence</div><h3>Composition is context, not causation.</h3><p>WAKE can count shared outings and compare supported execution metrics. Numeric telemetry alone cannot prove visible synchronization, blade work, or that one athlete caused a crew result.</p></aside></div><section className="outing-history"><div className="section-heading compact-heading"><div><div className="kicker">Two-week history</div><h2>Planned versus recorded crew outings</h2></div></div><div className="outing-table">{crew.outings.map((outing) => <article key={outing.outing_id} className={outing.assessment.classification !== 'NO_MATERIAL_FLAG_IN_AVAILABLE_EVIDENCE' ? 'needs-attention' : ''}><time>{formatDate(outing.date)} · {outing.slot.toLowerCase()}</time><div><strong>{outing.plan_title}</strong><small>{outing.assessment.statement}</small></div><div><span>{outing.distance_m ? `${(outing.distance_m / 1000).toFixed(1)} km` : 'No crew distance'}</span><small>{clubReviewLabel(outing.assessment.review_status)}</small></div></article>)}</div></section></main>;
}

function AthleteScreen({ athleteId, onBack, onOpenCrew }: { athleteId: string; onBack: () => void; onOpenCrew: (crewId: string) => void }) {
  const athlete = summarizeAthlete(demoClub, athleteId);
  return (
    <main className="page club-detail-page">
      <div className="prototype-notice" role="note"><span>Real-informed synthetic data</span>Identities and exact outcomes are fictional; workout patterns, source structures, and value ranges are grounded in the supplied real rowing material.</div>
      <header className="page-header club-detail-header"><div className="page-header-copy"><div className="kicker">{clubCategoryLabel(athlete.category)} squad · Athlete memory</div><h1>{athlete.name}</h1><p className="lede">WAKE connects this athlete&apos;s water, indoor, crew, and physical-boat history while keeping each modality&apos;s evidence and meaning separate.</p></div><button className="button" onClick={onBack} type="button">Back to club</button></header>
      <section className="club-detail-stats athlete-training-stats">
        <div><span>Active days</span><strong>{athlete.activeDays}/10</strong><small>{athlete.combinedDays} combined · {athlete.indoorOnlyDays} indoor-only</small></div>
        <div><span>Water distance</span><strong>{athlete.waterDistanceKm.toFixed(1)} km</strong><small>{athlete.waterSessions} water sessions</small></div>
        <div><span>Indoor distance</span><strong>{athlete.ergDistanceKm.toFixed(1)} km</strong><small>{athlete.ergSessions} individual Concept2 records</small></div>
        <div><span>Expected gaps</span><strong>{athlete.expectedMissingDays}</strong><small>context requested, never treated as a fitness verdict</small></div>
      </section>
      {athlete.participationGaps.length ? <div className="athlete-gap-note"><strong>Context requested</strong><span>{athlete.participationGaps.map((gap) => `${formatDate(gap.date)}: ${gap.statement}`).join(' ')}</span></div> : null}
      <div className="club-detail-layout"><section><div className="section-heading compact-heading"><div><div className="kicker">Crew memberships</div><h2>{athlete.crews.length} recurring lineups</h2></div></div><div className="athlete-memberships">{athlete.crews.map((crew) => <button key={crew.crew_id} onClick={() => onOpenCrew(crew.crew_id)} type="button"><div><strong>{crew.name}</strong><small>{clubCategoryLabel(crew.category)} · {crew.boat_class}</small></div><span>Open crew →</span></button>)}</div></section><aside className="club-boundary"><div className="kicker">Physical boats rowed</div><h3>{athlete.boats.map((boat) => boat.name).join(' · ')}</h3><p>Boat names come from linked session context. A class such as 2x is not treated as the identity of the physical shell.</p></aside></div>
      <section className="training-day-history" aria-labelledby="athlete-training-days-title">
        <div className="section-heading compact-heading"><div><div className="kicker">Training days</div><h2 id="athlete-training-days-title">Water and indoor work in one chronology</h2></div><p>Associations come from the plan or remain standalone.</p></div>
        <div className="training-day-list">
          {athlete.days.map((day) => (
            <article className={`training-day-card training-day-${day.classification.toLowerCase().replaceAll('_', '-')}`} key={day.date}>
              <header><div><time>{formatDate(day.date)}</time><strong>{trainingDayLabel(day.classification)}</strong></div><div className="training-day-volume">{day.waterDistanceKm ? <span>{day.waterDistanceKm.toFixed(1)} km water</span> : null}{day.ergDistanceKm ? <span>{day.ergDistanceKm.toFixed(1)} km indoor</span> : null}</div></header>
              {day.activities.length ? <div className="training-day-activities">{day.activities.map((activity) => { const boat = activity.boat_id ? demoClub.boats.find((item) => item.boat_id === activity.boat_id) : null; const erg = activity.erg_metrics; return <div className={`training-day-activity ${activity.modality === 'ERG' ? 'indoor' : 'water'}`} key={activity.activity_id}><div><span>{trainingRoleLabel(activity.training_role)} · {clubActivityLabel(activity.modality)}</span><strong>{activity.title}</strong><small>{boat ? `${boat.name} · ` : ''}{activity.association_status === 'STANDALONE' ? 'Standalone indoor plan' : 'Plan-confirmed day link'}</small></div>{erg ? <div className="erg-metric-grid"><span><small>Workout</small>{ergWorkoutLabel(erg.workout_type)}</span><span><small>Concept2 pace</small>{formatDuration(erg.average_pace_500m_s)} /500m</span><span><small>Rate</small>{erg.average_spm.toFixed(1)} SPM</span><span><small>Power</small>{erg.average_watts.toFixed(0)} W</span></div> : <div className="water-activity-distance"><small>Water distance</small><strong>{(activity.distance_m / 1000).toFixed(1)} km</strong></div>}</div>; })}</div> : <div className="training-day-missing"><strong>No activity record</strong><span>{day.gap?.statement}</span></div>}
            </article>
          ))}
        </div>
        <div className="training-day-evidence-note" role="note"><strong>Comparison boundary</strong><span>Water and indoor distances are never added into one performance total. Concept2 pace, rate, and watts are compared only with equivalent workout shapes and supported plan context; they do not prove visible technique, direct muscular force, or medical fitness.</span></div>
      </section>
    </main>
  );
}

function LongitudinalPilotScreen({ onBack }: { onBack: () => void }) {
  const pilot = buildLongitudinalPilot(demoClub);
  return (
    <main className="page longitudinal-pilot-page">
      <PrototypeNotice />
      <header className="page-header longitudinal-pilot-header">
        <div className="page-header-copy"><div className="kicker">Evidence-ranked synthesis · preflight</div><h1>Longitudinal intelligence pilot</h1><p className="lede">The club is already reconstructed deterministically. This pilot tests whether a bounded GPT workflow can turn that evidence into a safer, more useful review order than one direct model call.</p></div>
        <button className="button" onClick={onBack} type="button">Back to club</button>
      </header>
      <section className="longitudinal-pilot-state" aria-label="Pilot execution state"><div><span>Status</span><strong>Ready for authorization</strong><small>0 paid calls · no report generated</small></div><div><span>Comparison</span><strong>2 × baseline + 2 × WAKE</strong><small>same inputs, model, and schema</small></div><div><span>Planning estimate</span><strong>US${pilot.execution_plan.planning_projection_usd.toFixed(2)}</strong><small>observed projection US${pilot.execution_plan.observed_projection_usd.toFixed(6)}</small></div><div><span>Required start gate</span><strong>US${pilot.execution_plan.authorization_gate_total_usd.toFixed(2)}</strong><small>authorization, not provider cap</small></div></section>
      <div className="longitudinal-no-spend" role="note"><strong>No model execution occurred.</strong><span>The requests, tool boundaries, evidence references, and strict output schema are frozen. A separate explicit US$0.80 authorization is required before four paid starts.</span></div>
      <section className="longitudinal-case-section" aria-labelledby="longitudinal-case-title"><div className="section-heading"><div><div className="kicker">Frozen evaluation cases</div><h2 id="longitudinal-case-title">Athlete briefing + Club briefing</h2></div><p>Selective synthesis follows deterministic screening.</p></div><div className="longitudinal-case-grid">{pilot.cases.map((item) => <article key={item.pilot_id}><header><span>{item.scope_type}</span><strong>{item.title}</strong><small>{item.subject}</small></header><div><h3>Why GPT is used</h3><p>{item.why_model_is_used}</p></div><dl><div><dt>Deterministic coverage</dt><dd>{item.deterministic_coverage}</dd></div><div><dt>Comparison boundary</dt><dd>{item.comparison_status}</dd></div></dl><footer>{item.required_tools.map((tool) => <span key={tool}>{tool}</span>)}</footer></article>)}</div></section>
      <section className="longitudinal-method" aria-labelledby="longitudinal-method-title"><div><div className="kicker">Controlled comparison</div><h2 id="longitudinal-method-title">What must improve</h2><p>Both workflows receive the same compact evidence and must return the same strict structure. WAKE earns its place only if bounded tools and verification improve evidence coverage, useful prioritization, abstention, and unsupported-claim control.</p></div><ol><li><span>01</span><div><strong>Direct baseline</strong><p>One model call receives the compact summary without investigation tools.</p></div></li><li><span>02</span><div><strong>WAKE bounded agent</strong><p>The same model can inspect four deterministic views, then its structured result is verified.</p></div></li><li><span>03</span><div><strong>Saved report</strong><p>Verified outputs are stored with request hashes, evidence references, runtime, tokens, and approximate cost.</p></div></li></ol></section>
      <section className="longitudinal-boundaries"><div><div className="kicker">Deliberate limits</div><h2>Useful memory without false certainty</h2></div><ul>{pilot.boundaries.map((boundary) => <li key={boundary}>{boundary}</li>)}</ul><div className="saved-report-behavior"><strong>Reopening a saved report makes no new model call.</strong><span>Saved results remain reviewable at US$0.00. Re-analysis is a new, separately authorized execution.</span></div></section>
    </main>
  );
}

function SessionsScreen({ onNavigate, onReview, onOpenSession, onOpenCrew, onOpenAthlete, onOpenLongitudinalPilot, sessions, processing, error }: { onNavigate: (screen: Screen) => void; onReview: () => void; onOpenSession: (session: SessionRecord) => void; onOpenCrew: (crewId: string) => void; onOpenAthlete: (athleteId: string) => void; onOpenLongitudinalPilot: () => void; sessions: SessionRecord[]; processing: boolean; error: string }) {
  const summary = summarizeSessionInbox(sessions);
  return (
    <main className="page">
      <PrototypeNotice />
      <header className="page-header">
        <div className="page-header-copy">
          <div className="kicker">Daily intelligence · Team and crew memory</div>
          <h1>Understand the club,<br />then the session.</h1>
          <p className="lede">WAKE connects athletes, recurring lineups, physical boats, and session evidence so the coach can find what needs attention without opening every chart.</p>
        </div>
        <div className="page-header-actions">
          <button className="button" onClick={() => onNavigate('evaluation')} type="button">View evaluation results</button>
          <button className="button" onClick={() => onNavigate('competition')} type="button">Open competition review</button>
          <button className="button button-primary" onClick={() => onNavigate('intake')} type="button">Review a session</button>
        </div>
      </header>
      <ClubOverview onOpenAthlete={onOpenAthlete} onOpenCrew={onOpenCrew} onOpenLongitudinalPilot={onOpenLongitudinalPilot} />
      <section className="operational-inbox-heading"><div><div className="kicker">Operational workflow</div><h2>Saved session reviews</h2></div><p>These records exercise the full evidence-to-review workflow. The two-week club pulse above is a separate real-informed synthetic relational dataset.</p></section>
      <section className="summary-strip" aria-label="Saved review workflow summary">
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

function CompetitionReviewScreen({ onBack }: { onBack: () => void }) {
  const report = demoCompetitionReview;
  const [selectedEntryId, setSelectedEntryId] = useState<string | null>(null);
  const selectedEntry = report.entries.find((entry) => entry.entry_id === selectedEntryId) ?? null;

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, [selectedEntryId]);

  if (selectedEntry) {
    return (
      <main className="page competition-page">
        <div className="competition-notice" role="note"><span>Real-informed synthetic regatta</span>No real athlete is attached to this fictional result or training history.</div>
        <header className="page-header competition-header"><div className="page-header-copy"><div className="kicker">Boat report · Race {selectedEntry.event.race_number}</div><h1>{selectedEntry.crew.name}</h1><p className="lede">{selectedEntry.event.label} · {selectedEntry.distance.distance_m.toLocaleString('en-US')} m · {selectedEntry.boat.name}</p></div><button className="button" onClick={() => setSelectedEntryId(null)} type="button">Back to competition</button></header>

        <section className="competition-boat-stats" aria-label="Boat result summary">
          <div><span>Official result</span><strong>{selectedEntry.status === 'FINISHED' ? `${selectedEntry.official_rank}/${selectedEntry.field.field_size}` : 'N/C'}</strong><small>official rank preserved</small></div>
          <div><span>Finish time</span><strong>{formatRaceTime(selectedEntry.finish_time_s)}</strong><small>{selectedEntry.status === 'FINISHED' ? `${formatRaceTime(selectedEntry.pace_500m_s)} /500 m` : 'no classified time'}</small></div>
          <div><span>Gap to winner</span><strong>{selectedEntry.gap_to_winner_s === null ? '—' : `+${selectedEntry.gap_to_winner_s.toFixed(1)} s`}</strong><small>{selectedEntry.gap_to_winner_pct === null ? 'not available' : `+${selectedEntry.gap_to_winner_pct.toFixed(2)}%`}</small></div>
          <div><span>Shared work</span><strong>{selectedEntry.training_context.shared_outings}</strong><small>{(selectedEntry.training_context.shared_distance_m / 1000).toFixed(1)} km before race day</small></div>
        </section>

        <div className="competition-boat-layout">
          <div>
            <section className="competition-context-card"><div className="kicker">Training context, not causation</div><h2>What preceded this start</h2><p>The lineup completed <strong>{selectedEntry.training_context.shared_outings} shared outings</strong> and had {selectedEntry.training_context.disrupted_outings} disrupted outing{selectedEntry.training_context.disrupted_outings === 1 ? '' : 's'} in the two-week window. Its last shared record was {formatDate(selectedEntry.training_context.last_shared_outing_date)}.</p><div className="competition-boundary-line"><strong>Not established</strong><span>WAKE cannot claim that this training caused the result, or recommend crew selection from this result alone.</span></div></section>

            <section className="competition-field-section"><div className="section-heading compact-heading"><div><div className="kicker">Competitive field</div><h2>Official order retained</h2></div><span>{selectedEntry.event.finisher_count}/{selectedEntry.event.field_size} classified</span></div><div className="competition-result-table"><div className="competition-result-head"><span>Rank</span><span>Entry</span><span>Club</span><span>Time</span></div>{selectedEntry.event.results.map((result) => <article className={result.entry_id === selectedEntry.entry_id ? 'our-result' : ''} key={result.entry_id}><strong>{result.official_rank ?? 'N/C'}</strong><div><span>{result.crew_label}</span><small>{result.athletes.map((athlete) => athlete.name).join(' · ')}</small></div><span>{result.club.name}</span><code>{formatRaceTime(result.finish_time_s)}</code>{result.official_tie_preserved ? <small className="official-tie">Displayed-time tie · official rank retained</small> : null}</article>)}</div></section>
          </div>

          <aside className="competition-boat-aside">
            <section><div className="kicker">Distance provenance</div><h3>{selectedEntry.distance.distance_m.toLocaleString('en-US')} m category reference</h3><p>The distance follows the same-federation, same-season programme pattern for {competitionCategoryLabel(selectedEntry.event.category)}. It was not directly printed in the separate stage result supplied to WAKE.</p><code>{selectedEntry.distance.evidence_ref}</code></section>
            <section><div className="kicker">Lineup snapshot</div>{selectedEntry.athletes.map((athlete, index) => <div className="competition-lineup-row" key={athlete.athlete_id}><span>{selectedEntry.athletes.length - index}</span><strong>{athlete.name}</strong></div>)}</section>
            <section className={selectedEntry.status === 'NOT_CLASSIFIED' ? 'question-needed' : ''}><div className="kicker">Human context</div><h3>{selectedEntry.status === 'NOT_CLASSIFIED' ? 'Reason still missing' : 'Race context still missing'}</h3><p>{selectedEntry.next_question}</p><small>Conditions, incidents, penalties, and lineup changes remain human-supplied context.</small></section>
          </aside>
        </div>
      </main>
    );
  }

  return (
    <main className="page competition-page">
      <div className="competition-notice" role="note"><span>Real-informed synthetic regatta</span>Categories, field shapes, distance rules, ties, and non-completion patterns are grounded in supplied official material; every displayed identity and outcome is fictional.</div>
      <header className="page-header competition-header"><div className="page-header-copy"><div className="kicker">Goal readiness → race outcome → next cycle</div><h1>Competition Review</h1><p className="lede">Connect every club entry to its athletes, boat, previous shared work, official result, and the full competitive field.</p></div><button className="button" onClick={onBack} type="button">Back to sessions</button></header>

      <section className="competition-scoreboard" aria-label="Club competition summary">
        <div><span>Our entries</span><strong>{report.summary.entries}</strong><small>{report.summary.events_entered} events</small></div>
        <div><span>Athletes</span><strong>{report.summary.athletes_entered}</strong><small>{report.summary.multi_start_athletes} with multiple starts</small></div>
        <div><span>Wins</span><strong>{report.summary.wins}</strong><small>{report.summary.podiums} podium finishes</small></div>
        <div><span>Classified</span><strong>{report.summary.finishers}/{report.summary.entries}</strong><small>{report.summary.not_classified} needs context</small></div>
        <div><span>Opposition</span><strong>{report.summary.opponent_clubs}</strong><small>fictional competitor clubs</small></div>
      </section>

      <div className="competition-overview-layout">
        <section className="competition-entry-section"><div className="section-heading compact-heading"><div><div className="kicker">Our entries</div><h2>Ten boats, one connected club history</h2></div><p>Open any boat to inspect the field and its pre-race evidence.</p></div><div className="competition-entry-list">{report.entries.map((entry) => <article className={entry.status === 'NOT_CLASSIFIED' ? 'needs-context' : ''} key={entry.entry_id}><div className="competition-place"><strong>{entry.official_rank ?? 'N/C'}</strong><small>of {entry.field.field_size}</small></div><div className="competition-entry-copy"><span>Race {entry.event.race_number} · {entry.event.label}</span><h3>{entry.crew.name}</h3><p>{entry.athletes.map((athlete) => athlete.name).join(' · ')}</p><small>{entry.training_context.shared_outings} shared outings · {(entry.training_context.shared_distance_m / 1000).toFixed(1)} km contextual history</small></div><div className="competition-entry-metrics"><strong>{formatRaceTime(entry.finish_time_s)}</strong><span>{entry.pace_500m_s === null ? 'Missing race context' : `${formatRaceTime(entry.pace_500m_s)} /500 m`}</span><button onClick={() => setSelectedEntryId(entry.entry_id)} type="button">Open boat report →</button></div></article>)}</div></section>

        <aside className="competition-overview-aside">
          <section><div className="kicker">Competitive field</div><h2>Eight events reconstructed</h2><p>Results retain opponent club, crew, athlete identities, official order, time, and non-completion. Raw time never replaces the published rank.</p>{report.events.map((event) => <div className="competition-event-row" key={event.event_id}><div><strong>R{event.race_number} · {event.label}</strong><small>{event.distance_m.toLocaleString('en-US')} m · {event.field_size} entries</small></div><span>{formatRaceTime(event.winning_time_s)}</span></div>)}</section>
          <section><div className="kicker">Distance provenance</div><h3>Category rule, not boat-size guess</h3><p>500 m for Beginner; 1,000 m for Aspirant and Master; 2,000 m for Senior. Each derived pace keeps the category reference and the missing stage confirmation visible.</p></section>
          <section><div className="kicker">Training context, not causation</div><h3>Outcome evidence closes a loop</h3><p>The report can show what preceded the race and what happened in the field. It cannot prove that one session, athlete, lineup, or condition caused the result.</p></section>
        </aside>
      </div>

      <section className="competition-athlete-section"><div className="section-heading compact-heading"><div><div className="kicker">Athlete race load</div><h2>Every athlete across every entry</h2></div><p>Starts remain linked to their exact crew snapshots.</p></div><div className="competition-athlete-grid">{report.athlete_starts.map((item) => <article key={item.athlete_id}><strong>{item.athlete.name}</strong><span>{item.starts} starts</span><small>{item.entry_ids.map((entryId) => report.entries.find((entry) => entry.entry_id === entryId)?.crew.name).join(' · ')}</small></article>)}</div></section>
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
  const [selectedCrewId, setSelectedCrewId] = useState('crew-2x-men');
  const [selectedAthleteId, setSelectedAthleteId] = useState('athlete-lucas');
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

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, [screen]);

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

  function openCrew(crewId: string) { setSelectedCrewId(crewId); setScreen('club-crew'); }
  function openAthlete(athleteId: string) { setSelectedAthleteId(athleteId); setScreen('club-athlete'); }

  return <><AppHeader screen={screen} onNavigate={setScreen} />{screen === 'sessions' ? <SessionsScreen error={error} onNavigate={setScreen} onOpenAthlete={openAthlete} onOpenCrew={openCrew} onOpenLongitudinalPilot={() => setScreen('longitudinal-pilot')} onOpenSession={openSession} onReview={investigate} processing={processing} sessions={sessions} /> : null}{screen === 'club-crew' ? <CrewScreen crewId={selectedCrewId} onBack={() => setScreen('sessions')} onOpenAthlete={openAthlete} /> : null}{screen === 'club-athlete' ? <AthleteScreen athleteId={selectedAthleteId} onBack={() => setScreen('sessions')} onOpenCrew={openCrew} /> : null}{screen === 'longitudinal-pilot' ? <LongitudinalPilotScreen onBack={() => setScreen('sessions')} /> : null}{screen === 'competition' ? <CompetitionReviewScreen onBack={() => setScreen('sessions')} /> : null}{screen === 'intake' ? <IntakeScreen error={error} onInvestigate={investigate} preparedBundle={preparedBundle} processing={processing} weatherOutcome={weatherOutcome} /> : null}{screen === 'review' ? <ReviewScreen error={error} executionCost={executionCost} onComplete={completeReview} processing={processing} review={review} /> : null}{screen === 'briefing' ? <BriefingScreen briefing={briefing} error={error} onApprove={approveMemory} onBack={() => setScreen('review')} onLeave={() => setScreen('sessions')} processing={processing} /> : null}{screen === 'memory' ? <MemoryScreen memory={memory} onBack={() => setScreen('sessions')} /> : null}{screen === 'evaluation' ? <EvaluationScreen onBack={() => setScreen('sessions')} /> : null}</>;
}
