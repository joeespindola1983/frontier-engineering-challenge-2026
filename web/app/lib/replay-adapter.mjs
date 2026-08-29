const SOURCE_LABELS = {
  'speedcoach-synthetic': 'SpeedCoach',
  'mobile-synthetic': 'Mobile',
  'synthetic-environment-002': 'Wind timeline',
};

const BOAT_LABELS = {
  DOUBLE_SCULL: '2x',
  SINGLE_SCULL: '1x',
  QUADRUPLE_SCULL: '4x',
};

const CREW_LABELS = {
  MEN: "Men's",
  WOMEN: "Women's",
  MIXED: 'Mixed',
};

function prescribedTargets(blocks) {
  return blocks.filter((block) => !block.kind || block.kind === 'WORK').flatMap((block) =>
    Array.from({ length: block.repetitions }, () => ({
      distanceM: block.distance_m,
      minSpm: block.stroke_rate.min_spm,
      maxSpm: block.stroke_rate.max_spm,
      equipment: block.equipment,
    })),
  );
}

function sourcePolicy(analysis) {
  return Object.fromEntries(
    analysis.source_policy.map((policy) => [policy.metric, policy]),
  );
}

function displaySource(sourceId) {
  return SOURCE_LABELS[sourceId] ?? sourceId ?? 'No source selected';
}

function sourceLabels(summary) {
  const labels = {};
  for (const source of summary.sources ?? []) {
    labels[source.source_id] = {
      SPEEDCOACH: 'SpeedCoach',
      MOBILE: 'Mobile',
    }[source.kind] ?? source.kind;
  }
  const timelineId = summary.environment?.timeline_id;
  if (timelineId) labels[timelineId] = SOURCE_LABELS[timelineId] ?? 'Environment timeline';
  return labels;
}

function sourceDisplay(sourceId, labels) {
  return labels[sourceId] ?? displaySource(sourceId);
}

function findPolicy(policies, ...metrics) {
  return metrics.map((metric) => policies[metric]).find(Boolean) ?? null;
}

function policyView(policy, labels) {
  return {
    selectedSource: sourceDisplay(policy?.selected_source_id, labels),
    reason: policy?.reason ?? 'No trusted source was selected for this metric.',
  };
}

function distanceLabel(targets) {
  const distances = [...new Set(targets.map((target) => target.distanceM))];
  if (distances.length !== 1 || distances[0] == null) return 'work intervals';
  const distance = distances[0];
  return distance >= 1000 && distance % 1000 === 0
    ? `${distance / 1000} km`
    : `${distance} m`;
}

function boatLabel(context) {
  const candidate = context.session_candidate ?? {};
  const code = BOAT_LABELS[candidate.boat_class]
    ?? candidate.world_rowing_code
    ?? 'rowing session';
  const crew = CREW_LABELS[candidate.crew_category];
  return crew ? `${crew} ${code}` : code;
}

export function buildSessionReview({ analysis, summary, context }) {
  const targets = prescribedTargets(summary.plan?.blocks ?? []);
  const deviationSegments = new Set(
    analysis.deviations.map((deviation) => deviation.segment_ref),
  );
  const policies = sourcePolicy(analysis);
  const labels = sourceLabels(summary);
  const strokeRatePolicy = findPolicy(policies, 'stroke_rate_spm', 'spm');
  const distancePolicy = findPolicy(policies, 'distance_m', 'distance');
  const routePolicy = findPolicy(policies, 'route');
  const environmentPolicy = findPolicy(
    policies,
    'environment_effective_headwind_m_s',
    'environment',
  );
  const equipmentClaim = analysis.claims.find(
    (claim) => claim.claim_id === 'equipment-status',
  );
  const workIntervals = analysis.segments
    .filter((segment) => segment.kind === 'WORK')
    .map((segment, index) => {
      const target = targets[index] ?? {};
      return {
        segmentId: segment.segment_id,
        index: index + 1,
        averageSpm: segment.average_spm,
        distanceM: segment.distance_m,
        durationS: segment.start_offset_s == null || segment.end_offset_s == null
          ? 0
          : Number((segment.end_offset_s - segment.start_offset_s).toFixed(3)),
        targetMinSpm: target.minSpm ?? segment.average_spm,
        targetMaxSpm: target.maxSpm ?? segment.average_spm,
        plannedDistanceM: target.distanceM ?? segment.distance_m ?? 0,
        status: deviationSegments.has(segment.segment_id)
          ? 'DEVIATION'
          : 'WITHIN_RANGE',
        evidenceRefs: segment.evidence_refs,
      };
    });

  const environment = analysis.environment_assessment ?? {
    association: 'UNKNOWN',
    summary: 'Time-aligned environmental evidence was not supplied or is not available.',
    limitations: ['No boat-relative environmental interpretation is available.'],
    evidence_refs: [],
  };
  const inputNotice = context.input_notice ?? 'Coach-uploaded local evidence.';
  const isSynthetic = inputNotice.toLowerCase().includes('synthetic')
    || summary.plan?.source?.kind === 'SYNTHETIC';
  const clockFinding = summary.cross_source_findings?.find(
    (finding) => finding.type === 'CLOCK_OFFSET'
      || finding.finding_id === 'mobile-clock-offset',
  );
  const followUpQuestion = analysis.follow_up_questions?.[0]
    ?? 'No additional coach context was requested for this analysis.';

  return {
    sessionId: summary.case_id,
    title: `${targets.length || workIntervals.length} × ${distanceLabel(targets)} · ${boatLabel(context)}`,
    scheduledDate: summary.plan?.scheduled_date ?? null,
    provenance: isSynthetic ? 'SYNTHETIC' : 'UPLOADED',
    notice: inputNotice,
    status: analysis.follow_up_questions?.length ? 'QUESTION_REQUIRED' : 'READY_FOR_REVIEW',
    planSummary: analysis.plan_summary?.summary ?? 'No planned workout was supplied.',
    coachBriefing: analysis.coach_briefing,
    currentReconstruction: analysis.coach_briefing,
    mobileClockOffsetS: clockFinding?.values.mobile_from_speedcoach_s ?? null,
    workIntervals,
    sourcePolicy: {
      strokeRate: {
        ...policyView(strokeRatePolicy, labels),
      },
      distance: {
        ...policyView(distancePolicy, labels),
      },
      route: {
        ...policyView(routePolicy, labels),
        corroboratedBy: routePolicy?.evidence_refs?.some((ref) => ref.includes('mobile'))
          ? 'Mobile'
          : null,
      },
      environment: {
        ...policyView(environmentPolicy, labels),
      },
    },
    environment: {
      association: environment.association,
      summary: environment.summary,
      limitations: environment.limitations,
      evidenceRefs: environment.evidence_refs,
    },
    checkpoint: {
      checkpointId: `checkpoint-${summary.case_id}`,
      question: followUpQuestion,
      whyItMatters:
        'A coach answer becomes human-confirmed context; it does not rewrite measured telemetry.',
      options: ['YES', 'NO', 'UNKNOWN'],
      canSkip: true,
      affectedClaims: equipmentClaim ? [equipmentClaim.claim_id] : [],
      affectedMemoryFields: ['resistance_band_used'],
    },
    abstentions: analysis.abstentions,
  };
}
