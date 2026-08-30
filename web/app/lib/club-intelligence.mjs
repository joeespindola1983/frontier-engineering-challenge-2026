const DEFAULT_COST_BASIS = Object.freeze({
  observed_cases: 10,
  observed_total_cost_usd: 0.711516,
  planning_cost_per_execution_usd: 0.15,
  authorization_gate_per_execution_usd: 0.20,
  evidence_ref: 'evaluation/runs/expanded-evaluation-v2/official-20260830/agent/run-manifest.json',
});

function roundUsd(value) {
  return Math.round((value + Number.EPSILON) * 1_000_000) / 1_000_000;
}

function finding(code, route, statement, evidenceRefs) {
  return {
    code,
    route,
    statement,
    evidence_refs: [...new Set(evidenceRefs.filter(Boolean))],
  };
}

function reviewStatus(classification) {
  return {
    NO_MATERIAL_FLAG_IN_AVAILABLE_EVIDENCE: 'NO_MATERIAL_FLAG',
    SPM_BELOW_PLAN: 'NEEDS_COACH_REVIEW',
    EXCESS_RECOVERY: 'NEEDS_COACH_REVIEW',
    PLAN_NOT_LINKED: 'READY_FOR_INVESTIGATION',
    ATHLETE_CONTEXT_PENDING: 'AWAITING_ATHLETE_CONTEXT',
    CREW_UNAVAILABLE: 'ALTERNATIVE_TRAINING_REVIEW',
  }[classification] ?? classification;
}

export function analyzeOutingEvidence(outing) {
  if (outing.outcome === 'CREW_UNAVAILABLE') {
    const signal = finding(
      'CREW_UNAVAILABLE',
      'HUMAN_CONTEXT',
      'The planned crew did not launch; recorded alternatives and missing participation need review.',
      [`${outing.outing_id}:outcome`],
    );
    return {
      outing_id: outing.outing_id,
      date: outing.date,
      classification: signal.code,
      statement: signal.statement,
      review_status: reviewStatus(signal.code),
      evidence_refs: signal.evidence_refs,
      signals: [signal],
    };
  }

  const evidence = outing.evidence;
  if (!evidence) throw new TypeError(`Completed outing ${outing.outing_id} has no evidence summary`);

  const signals = [];
  if (!evidence.plan.linked) {
    signals.push(finding(
      'PLAN_NOT_LINKED',
      'SOURCE_REQUEST',
      'Telemetry was received, but no planned workout was linked.',
      [evidence.speedcoach.source_ref],
    ));
  }

  const target = evidence.plan.stroke_rate_target;
  const observedSpm = evidence.speedcoach.work_interval_spm;
  if (evidence.plan.linked && target && observedSpm) {
    const below = observedSpm.values.find((segment) => segment.average_spm < target.min_spm);
    if (below) {
      signals.push(finding(
        'SPM_BELOW_PLAN',
        'AGENT_INVESTIGATION',
        `${below.segment_id} averaged ${below.average_spm} SPM, below the prescribed ${target.min_spm}–${target.max_spm} SPM range.`,
        [target.evidence_ref, observedSpm.evidence_ref],
      ));
    }
  }

  const plannedRecovery = evidence.plan.planned_recovery_s;
  const observedRecovery = evidence.speedcoach.recovery_durations_s;
  if (evidence.plan.linked && plannedRecovery && observedRecovery) {
    const longest = Math.max(...observedRecovery.values);
    if (longest > plannedRecovery.value + plannedRecovery.tolerance_s) {
      signals.push(finding(
        'EXCESS_RECOVERY',
        'AGENT_INVESTIGATION',
        `A recovery lasted ${longest} seconds versus ${plannedRecovery.value} planned seconds.`,
        [plannedRecovery.evidence_ref, observedRecovery.evidence_ref],
      ));
    }
  }

  if (evidence.athlete_context.required && !evidence.athlete_context.available) {
    signals.push(finding(
      'ATHLETE_CONTEXT_PENDING',
      'ATHLETE_QUESTION',
      'Execution was reconstructed; perceived effort is still awaiting athlete context.',
      [evidence.speedcoach.source_ref, evidence.athlete_context.evidence_ref],
    ));
  }

  const primary = signals[0];
  const classification = primary?.code ?? 'NO_MATERIAL_FLAG_IN_AVAILABLE_EVIDENCE';
  const statement = primary?.statement ?? 'No material flag was found in the available deterministic evidence; this is not proof of full plan compliance.';
  return {
    outing_id: outing.outing_id,
    date: outing.date,
    classification,
    statement,
    review_status: reviewStatus(classification),
    evidence_refs: primary?.evidence_refs ?? [evidence.speedcoach.source_ref].filter(Boolean),
    signals,
  };
}

function activityAssessment(activity, outingById) {
  if (activity.modality !== 'WATER_CREW') {
    return {
      activity_id: activity.activity_id,
      date: activity.date,
      modality: activity.modality,
      classification: 'RECORDED_ALTERNATIVE',
      statement: 'The alternative activity is recorded; plan compliance was not assessed through the water-session workflow.',
      evidence_refs: [`${activity.activity_id}:record`],
    };
  }
  const outing = outingById.get(activity.outing_id);
  if (!outing) throw new RangeError(`Activity ${activity.activity_id} references an unknown outing`);
  const assessment = analyzeOutingEvidence(outing);
  return {
    activity_id: activity.activity_id,
    date: activity.date,
    modality: activity.modality,
    classification: assessment.classification,
    statement: assessment.statement,
    evidence_refs: assessment.evidence_refs,
  };
}

export function buildClubPeriodAnalysis(club, costBasis = DEFAULT_COST_BASIS) {
  const crewById = new Map(club.crews.map((crew) => [crew.crew_id, crew]));
  const athleteById = new Map(club.athletes.map((athlete) => [athlete.athlete_id, athlete]));
  const outingById = new Map(club.outings.map((outing) => [outing.outing_id, outing]));
  const outingAssessments = club.outings.map((outing) => ({
    ...analyzeOutingEvidence(outing),
    crew_id: outing.crew_id,
  }));
  const assessmentByOuting = new Map(outingAssessments.map((assessment) => [assessment.outing_id, assessment]));

  const outingSignals = club.outings.flatMap((outing) => {
    const assessment = assessmentByOuting.get(outing.outing_id);
    return assessment.signals.map((signal) => ({
      attention_id: `${signal.code.toLowerCase()}:${outing.outing_id}`,
      kind: signal.code === 'CREW_UNAVAILABLE' ? 'CREW_UNAVAILABLE' : 'SESSION_FINDING',
      code: signal.code,
      route: signal.route,
      date: outing.date,
      entity_id: outing.crew_id,
      entity_name: crewById.get(outing.crew_id).name,
      statement: signal.statement,
      evidence_refs: signal.evidence_refs,
      source_bundle_id: outing.evidence?.source_bundle_id ?? null,
    }));
  });
  const gapSignals = club.participation_gaps.map((gap) => ({
    attention_id: `gap:${gap.date}:${gap.athlete_id}`,
    kind: 'PARTICIPATION_GAP',
    code: gap.classification,
    route: 'HUMAN_CONTEXT',
    date: gap.date,
    entity_id: gap.athlete_id,
    entity_name: athleteById.get(gap.athlete_id).name,
    statement: gap.statement,
    evidence_refs: [`${gap.date}:${gap.athlete_id}:activity-coverage`],
  }));
  const attentionSignals = [...outingSignals, ...gapSignals].sort((left, right) => right.date.localeCompare(left.date));

  const routing = Object.fromEntries(
    ['AGENT_INVESTIGATION', 'ATHLETE_QUESTION', 'HUMAN_CONTEXT', 'SOURCE_REQUEST'].map((route) => [
      route,
      attentionSignals.filter((signal) => signal.route === route).length,
    ]),
  );
  const activityAssessments = club.activities.map((activity) => activityAssessment(activity, outingById));
  const deepQueue = attentionSignals.filter((signal) => signal.route === 'AGENT_INVESTIGATION');
  const completeSourceBundles = deepQueue.filter((signal) => signal.source_bundle_id).length;
  const allDeepBundlesReady = deepQueue.length > 0 && completeSourceBundles === deepQueue.length;
  const paidExecutions = deepQueue.length + 1;
  const observedAverage = costBasis.observed_total_cost_usd / costBasis.observed_cases;

  return {
    schema_version: 'wake.club_period_analysis.v1',
    analysis_mode: 'DETERMINISTIC_SCREEN',
    model_called: false,
    deterministic_analysis_cost_usd: 0,
    coverage: {
      activities_scanned: activityAssessments.length,
      water_crew_sessions_scanned: activityAssessments.filter((item) => item.modality === 'WATER_CREW').length,
      alternate_activities_scanned: activityAssessments.filter((item) => item.modality !== 'WATER_CREW').length,
      planned_outings_scanned: outingAssessments.length,
      completed_outings_scanned: club.outings.filter((outing) => outing.outcome === 'COMPLETED').length,
      disrupted_outings_scanned: club.outings.filter((outing) => outing.outcome === 'CREW_UNAVAILABLE').length,
      compact_evidence_summaries: club.outings.filter((outing) => outing.evidence).length,
      linked_plans: club.outings.filter((outing) => outing.evidence?.plan.linked).length,
      complete_source_bundles: completeSourceBundles,
    },
    activity_assessments: activityAssessments,
    outing_assessments: outingAssessments,
    attention_signals: attentionSignals,
    routing,
    deep_investigations: {
      completed: 0,
      queued: deepQueue.length,
      status: !deepQueue.length
        ? 'NOT_REQUIRED'
        : allDeepBundlesReady
          ? 'READY_FOR_AUTHORIZATION'
          : 'REQUIRES_SOURCE_BUNDLES',
      queue: deepQueue,
    },
    longitudinal_synthesis: {
      status: 'NOT_EXECUTED',
      prerequisite: 'Complete queued investigations and collect or explicitly mark missing human/source context.',
    },
    cost_forecast: {
      basis: costBasis.evidence_ref,
      paid_executions: paidExecutions,
      observed_average_per_execution_usd: roundUsd(observedAverage),
      observed_projection_usd: roundUsd(observedAverage * paidExecutions),
      planning_per_execution_usd: costBasis.planning_cost_per_execution_usd,
      planning_projection_usd: roundUsd(costBasis.planning_cost_per_execution_usd * paidExecutions),
      authorization_gate_per_execution_usd: costBasis.authorization_gate_per_execution_usd,
      authorization_gate_total_usd: roundUsd(costBasis.authorization_gate_per_execution_usd * paidExecutions),
      is_quote: false,
    },
    boundaries: [
      'The deterministic screen covers every recorded activity, but it is not a longitudinal agent conclusion.',
      'No material flag in available evidence is not proof that a workout was executed as planned.',
      'Missing participation requires human context and does not establish fitness, injury, or commitment.',
    ],
  };
}
