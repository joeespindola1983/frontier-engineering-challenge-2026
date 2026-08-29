const SOURCE_LABELS = {
  'speedcoach-synthetic': 'SpeedCoach',
  'mobile-synthetic': 'Mobile',
  'synthetic-environment-002': 'Wind timeline',
};

const BOAT_LABELS = {
  DOUBLE_SCULL: "Men's 2x",
};

function prescribedTargets(blocks) {
  return blocks.flatMap((block) =>
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

export function buildSessionReview({ analysis, summary, context }) {
  const targets = prescribedTargets(summary.plan.blocks);
  const deviationSegments = new Set(
    analysis.deviations.map((deviation) => deviation.segment_ref),
  );
  const policies = sourcePolicy(analysis);
  const routePolicy = policies.route;
  const equipmentClaim = analysis.claims.find(
    (claim) => claim.claim_id === 'equipment-status',
  );
  const workIntervals = analysis.segments
    .filter((segment) => segment.kind === 'WORK')
    .map((segment, index) => ({
      segmentId: segment.segment_id,
      index: index + 1,
      averageSpm: segment.average_spm,
      distanceM: segment.distance_m,
      durationS: Number((segment.end_offset_s - segment.start_offset_s).toFixed(3)),
      targetMinSpm: targets[index].minSpm,
      targetMaxSpm: targets[index].maxSpm,
      plannedDistanceM: targets[index].distanceM,
      status: deviationSegments.has(segment.segment_id)
        ? 'DEVIATION'
        : 'WITHIN_RANGE',
      evidenceRefs: segment.evidence_refs,
    }));

  return {
    sessionId: summary.case_id,
    title: `${targets.length} × 1 km · ${BOAT_LABELS[context.session_candidate.boat_class] ?? context.session_candidate.world_rowing_code}`,
    scheduledDate: summary.plan.scheduled_date,
    provenance: 'SYNTHETIC',
    notice: context.input_notice,
    status: 'QUESTION_REQUIRED',
    planSummary: analysis.plan_summary.summary,
    coachBriefing: analysis.coach_briefing,
    mobileClockOffsetS: summary.cross_source_findings.find(
      (finding) => finding.finding_id === 'mobile-clock-offset',
    )?.values.mobile_from_speedcoach_s,
    workIntervals,
    sourcePolicy: {
      strokeRate: {
        selectedSource: displaySource(policies.stroke_rate_spm.selected_source_id),
        reason: policies.stroke_rate_spm.reason,
      },
      distance: {
        selectedSource: displaySource(policies.distance_m.selected_source_id),
        reason: policies.distance_m.reason,
      },
      route: {
        selectedSource: displaySource(routePolicy.selected_source_id),
        corroboratedBy: routePolicy.evidence_refs.some((ref) => ref.includes('mobile'))
          ? 'Mobile'
          : null,
        reason: routePolicy.reason,
      },
      environment: {
        selectedSource: displaySource(
          policies.environment_effective_headwind_m_s.selected_source_id,
        ),
        reason: policies.environment_effective_headwind_m_s.reason,
      },
    },
    environment: {
      association: analysis.environment_assessment.association,
      summary: analysis.environment_assessment.summary,
      limitations: analysis.environment_assessment.limitations,
      evidenceRefs: analysis.environment_assessment.evidence_refs,
    },
    checkpoint: {
      checkpointId: 'checkpoint-resistance-band-002',
      question: analysis.follow_up_questions[0],
      whyItMatters:
        'Equipment context changes how the first block should be interpreted, but it does not change measured SPM or distance.',
      options: ['YES', 'NO', 'UNKNOWN'],
      canSkip: true,
      affectedClaims: equipmentClaim ? [equipmentClaim.claim_id] : [],
      affectedMemoryFields: ['resistance_band_used'],
    },
    abstentions: analysis.abstentions,
  };
}
