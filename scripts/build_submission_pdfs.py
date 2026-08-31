#!/usr/bin/env python3
"""Build the two polished PDF companions for the WAKE submission.

The content model is intentionally importable without ReportLab so deterministic
tests can validate the promised sections in the normal project environment.
ReportLab is imported only by the rendering path, which is run with the bundled
artifact Python runtime documented by Codex.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class SectionSpec:
    heading: str
    paragraphs: tuple[str, ...]
    bullets: tuple[str, ...] = ()
    code_blocks: tuple[str, ...] = ()
    callout: str | None = None


@dataclass(frozen=True)
class DocumentSpec:
    output_name: str
    title: str
    subtitle: str
    audience: str
    sections: tuple[SectionSpec, ...]


@dataclass(frozen=True)
class VisualAsset:
    role: str
    path: Path
    caption: str


def report_visual_assets(root: Path) -> tuple[VisualAsset, ...]:
    asset_dir = root / "submission" / "pdf" / "assets"
    return (
        VisualAsset(
            "club_overview",
            asset_dir / "club-overview.jpg",
            "Club overview: deterministic screening turns 52 activities into a coach-facing queue before deeper investigations are selected.",
        ),
        VisualAsset(
            "team_memory",
            asset_dir / "team-memory.jpg",
            "Team memory connects recurring crews, athletes, physical boats, and indoor training without merging unlike modalities.",
        ),
        VisualAsset(
            "session_investigation",
            asset_dir / "session-investigation.jpg",
            "Session investigation: each metric names its trusted evidence source while environmental context remains explicitly non-causal.",
        ),
        VisualAsset(
            "athlete_history",
            asset_dir / "athlete-history.jpg",
            "Athlete history preserves crew, solo, and Concept2 work in one chronology while keeping water and indoor distance separate.",
        ),
        VisualAsset(
            "competition_review",
            asset_dir / "competition-review.jpg",
            "Competition review closes the training loop with crew snapshots, boats, opponents, official order, and honest context boundaries.",
        ),
        VisualAsset(
            "evaluation_results",
            asset_dir / "evaluation-results.jpg",
            "Evaluation uses the same ten cases, model family, structured output contract, and grader for WAKE and the direct baseline.",
        ),
    )


def document_specs(root: Path) -> tuple[DocumentSpec, DocumentSpec]:
    del root  # Reserved for future repository-derived content validation.

    guide = DocumentSpec(
        output_name="wake-environment-setup-and-reproduction.pdf",
        title="WAKE Environment Setup and Reproduction Guide",
        subtitle=(
            "A clean-environment path to verify the public evidence, run the "
            "coach dashboard, and reproduce the saved evaluation at US$0.00."
        ),
        audience="Hackathon judges, reviewers, and technical evaluators",
        sections=(
            SectionSpec(
                "What this guide reproduces",
                (
                    "WAKE - Agentic Rowing Intelligence reconstructs fragmented rowing evidence, "
                    "routes uncertainty to the right human, and preserves approved rowing memory. "
                    "The repository ships public fixtures, saved model outputs, verifiers, a replay "
                    "dashboard, and the exact evaluation artifacts used in the submission.",
                    "The default reproduction is intentionally offline with respect to model calls. "
                    "It verifies committed artifacts and never spends API budget, even if a local key exists.",
                ),
                bullets=(
                    "52 pre-regatta and 50 post-regatta synthetic activities, grounded in real rowing formats and plausible value ranges.",
                    "Ten fixed WAKE-versus-baseline evaluation cases and observable saved trajectories.",
                    "A React/Vinext coach interface with sessions, team memory, goal memory, competition review, and evaluation.",
                    "Replay-first execution; live analysis remains an explicit, separately authorized action.",
                ),
                callout="Expected clean verification cost: US$0.00. Expected live cost: shown before and after each authorized run.",
            ),
            SectionSpec(
                "Clean-environment setup",
                (
                    "Start from the repository root on macOS or Linux. The locked workflow expects Python 3.11 or newer, uv, and Node.js 22 or newer. Node.js 24.19.0 and npm 10.8.2 were used for the final local audit.",
                    "Do not add a .env file for replay. Secrets and private athlete material are intentionally excluded from the source package.",
                ),
                code_blocks=(
                    "unzip wake-source-submission.zip\ncd micro1-hackaton\npython3 --version\nuv --version\nnode --version\nnpm --version",
                    "./scripts/reproduce_submission.sh",
                ),
                callout="If the web build reports that Node is too old, switch to Node 22+ before repeating the command.",
            ),
            SectionSpec(
                "Replay without an API key",
                (
                    "The full verification path installs locked dependencies, validates public data, checks saved outputs and trajectories, runs Python and web tests, lints the interface, and creates a production build.",
                    "When dependencies already exist, use the verification-only path. Both commands ignore OPENAI_API_KEY and make no provider request.",
                ),
                code_blocks=(
                    "./scripts/reproduce_submission.sh --verify-only",
                    ".venv/bin/python scripts/verify_submission_readiness.py --json",
                ),
                bullets=(
                    "Complete Git checkout status: READY with repository_ready and final_video_ready both true.",
                    "Extracted source-only ZIP status: PENDING_FINAL_VIDEO with repository_ready true, because the accepted MP4 is uploaded separately.",
                    "Expected fixed-case counts: 10 WAKE outputs, 10 baseline outputs, and 10 trajectories.",
                    "Expected official scores: WAKE 83.76 and direct baseline 49.00.",
                ),
            ),
            SectionSpec(
                "Run the dashboard in replay mode",
                (
                    "Replay is the product default. It opens saved evidence and deterministic club packages without calling a model. The launcher starts the local API and web interface together and stops both with Ctrl+C.",
                ),
                code_blocks=(
                    "./scripts/start_dashboard.sh",
                    "open http://localhost:3000/",
                ),
                bullets=(
                    "Sessions: club pulse, attention, crews, athletes, intelligence, and saved reviews.",
                    "Goal memory: coach-approved session memory plus the saved 102-activity club synthesis.",
                    "Competition: connected fictional race outcomes with explicit non-causal boundaries.",
                    "Evaluation: committed WAKE-versus-baseline evidence; opening it costs US$0.00.",
                ),
            ),
            SectionSpec(
                "Optional live investigation",
                (
                    "Live mode is not required to judge the saved submission. Use it only when a reviewer wants to execute a new bounded investigation. The key remains local and must never be committed or included in the ZIP.",
                    "Every live execution requires a positive finite operational authorization in the interface. That authorization is a start gate, not a provider billing cap. The resulting output displays observed tokens, runtime, and approximate cost.",
                ),
                code_blocks=(
                    "cp .env.example .env\n# Add OPENAI_API_KEY locally; never commit .env\n./scripts/start_dashboard.sh --live",
                ),
                callout="A live run may spend money. Replay, reopening saved results, and the fixed reproduction script do not.",
            ),
            SectionSpec(
                "Baseline and evaluation",
                (
                    "The official comparison holds the model family, ten case summaries, output schema, and grader constant. The direct baseline receives the compact case and produces one structured answer. WAKE receives the same case but can call deterministic tools and must pass a verifier.",
                    "The comparison measures the submitted workflows, not superiority over a qualified human coach. The separate club-memory audit is a structural capability check and is not a semantic coaching-quality score.",
                ),
                code_blocks=(
                    ".venv/bin/python scripts/run_official_evaluation.py --help",
                    ".venv/bin/python scripts/verify_submission_readiness.py",
                ),
                bullets=(
                    "WAKE: 83.76/100 across ten cases.",
                    "Direct baseline: 49.00/100 across the same ten cases.",
                    "Incremental official comparison cost: US$0.283344.",
                    "Preserved regression: environmental interpretation moved from 80.00 to 76.00.",
                ),
            ),
            SectionSpec(
                "Expected outputs and cost",
                (
                    "A successful clean run ends with passing public verifiers, Python tests, web tests, lint, and a production build. Saved results can be reopened and regraded without a new model call.",
                    "The exact number of tests can grow as the repository evolves; treat a non-zero exit code or failed verifier as a reproduction failure. Review the generated JSON summary for machine-readable evidence counts and scores.",
                ),
                bullets=(
                    "Replay and clean verification: US$0.00 model cost.",
                    "Saved 102-activity club memory reopen: US$0.00.",
                    "Saved club-memory creation: US$0.037384, 6,322 tokens.",
                    "Three final owner live-QA runs: US$0.283834 observed total.",
                ),
            ),
            SectionSpec(
                "Troubleshooting and support boundary",
                (
                    "Use the commands below before changing code. They expose the launch plan, verify repository readiness, and show whether the local ports are already occupied.",
                ),
                code_blocks=(
                    "./scripts/start_dashboard.sh --print-plan\n.venv/bin/python scripts/verify_submission_readiness.py --json\nlsof -nP -iTCP:3000 -sTCP:LISTEN\nlsof -nP -iTCP:8788 -sTCP:LISTEN",
                ),
                bullets=(
                    "Port in use: stop the earlier WAKE launcher or select different --web-port and --api-port values.",
                    "No API key: remain in replay; live mode is intentionally unavailable.",
                    "Private state: keep it under private-data/ or another ignored local path.",
                    "Browser cache: reload after changing the build or restarting the service.",
                ),
                callout="This prototype storage is user-restricted but is not encrypted, authenticated, backed up, multi-tenant, or a production database.",
            ),
        ),
    )

    report = DocumentSpec(
        output_name="wake-detailed-solution-report.pdf",
        title="WAKE - Agentic Rowing Intelligence",
        subtitle=(
            "Detailed solution report: how evidence, bounded agents, verification, "
            "human context, and rowing memory turn fragmented training records into reviewable decisions."
        ),
        audience="Rowing practitioners, hackathon judges, product reviewers, and technical evaluators",
        sections=(
            SectionSpec(
                "Executive summary",
                (
                    "Rowing clubs already collect valuable information, but it lives in different places: coach plans, SpeedCoach exports, Concept2 PM5 results, mobile telemetry, weather, crew lineups, boats, and conversations. The difficult task is not drawing another chart. It is reconstructing what happened, deciding which source can support each claim, exposing what remains unknown, and preserving the coach's reviewed conclusion.",
                    "WAKE is a replay-first agentic workflow for that task. It screens high-volume data deterministically, selects a bounded investigation when needed, verifies every structured output, asks the appropriate athlete or coach for missing context, and gates durable club memory behind human approval.",
                ),
                callout="Every row leaves a wake. WAKE makes that trail inspectable without pretending uncertainty has disappeared.",
            ),
            SectionSpec(
                "The operational problem",
                (
                    "A coach can understand one SpeedCoach file. The value problem appears when the same coach must follow many athletes, recurring crews, physical boats, substitutions, indoor alternatives, missed sessions, weather shifts, and competition outcomes across weeks.",
                    "A spreadsheet can store these records and a dashboard can summarize them. Neither automatically investigates contradictions, asks who can resolve missing context, separates observed evidence from hypothesis, or remembers only what a coach approved.",
                ),
                bullets=(
                    "Plans express intent; device records express measured execution.",
                    "Mobile and dedicated devices can overlap without being interchangeable for every metric.",
                    "Crew outcomes depend on people, lineup snapshots, physical boats, and conditions.",
                    "Indoor work is athlete-owned evidence and must not be converted into on-water speed or visible technique claims.",
                ),
            ),
            SectionSpec(
                "Users and human workflow",
                (
                    "WAKE treats coaches and athletes as complementary contributors. The athlete often owns the SpeedCoach or PM5 file and can explain equipment use or perceived effort. The coach owns the planned objective, group context, and consequential approval. Either person can upload evidence; provenance records who supplied each item.",
                    "Questions are routed by authority rather than by a forced uploader role. A human answer becomes human context. It never rewrites device measurements or turns an unsupported claim into observed telemetry.",
                ),
                bullets=(
                    "Athlete: uploads personal device evidence and answers first-hand execution questions.",
                    "Coach: supplies or confirms the plan, reviews findings, and approves club memory.",
                    "Source owner: resolves a missing file or unclear transcription.",
                    "WAKE: reconstructs, compares, verifies, and abstains where evidence is insufficient.",
                ),
            ),
            SectionSpec(
                "Evidence architecture and metric-level trust",
                (
                    "Multi-sensor intelligence is not an average of every number. WAKE assigns metric-level trust. When multiple sources report SPM, the workflow compares coverage, plausibility, continuity, and consistency, then selects the best-supported source for that session and metric. GPS distance, SPM, environment, and human context may therefore come from different evidence owners.",
                    "Every user-facing statement is typed as observed fact, derived metric, user-provided context, hypothesis, recommendation, or explicit unknown. Evidence references stay attached to the statement so a reviewer can inspect why it exists.",
                ),
                bullets=(
                    "Planned workout: prescription, target SPM, intervals, recovery, and training objective.",
                    "SpeedCoach: dedicated rowing measurements such as distance, pace, and stroke rate.",
                    "Mobile telemetry: optional route, timing, and overlapping sensor evidence.",
                    "Environment: supplied or consented historical observations, treated as associative context.",
                    "Concept2 PM5: individual indoor pace, SPM, watts, and workout structure.",
                    "Human context: equipment, crew, effort, interruption, and first-hand observations.",
                ),
            ),
            SectionSpec(
                "System architecture",
                (
                    "WAKE separates high-volume data processing from model reasoning. Source adapters validate and normalize the evidence, deterministic tools reconstruct the session and compare it with the prescription, and one bounded orchestrating agent decides which tools to call and how to synthesize the compact findings. A strict verifier rejects unsupported claims or malformed output before anything reaches the coach.",
                    "The human checkpoint is part of the architecture, not a disclaimer added at the end. Athlete and coach answers retain provenance, and durable club memory changes only after explicit coach approval. Saved verified artifacts can then be reopened and regraded without another model call.",
                ),
                bullets=(
                    "Evidence layer: plans, SpeedCoach, optional mobile and weather, PM5, and attributed human context.",
                    "Deterministic layer: validation, alignment, feature extraction, reconstruction, comparison, and club-scale screening.",
                    "Agent layer: one bounded orchestration loop over four read-only investigation tools.",
                    "Control layer: schema validation, claim-level evidence checks, bounded retry, cost authorization, and human approval.",
                    "Memory layer: application-owned saved reviews and coach-approved club context.",
                ),
            ),
            SectionSpec(
                "The bounded agentic workflow",
                (
                    "The weekend MVP deliberately uses one orchestrating agent with deterministic tools and a verification checkpoint. Specialized roles are expressed as bounded capabilities inside the workflow rather than uncontrolled autonomous agents. This keeps the trace inspectable and makes cost authorization meaningful.",
                    "A representative trajectory stores versioned instructions, structured inputs, tool calls and responses, evidence references, retries, verifier checkpoints, output, runtime, and approximate cost. It does not store private chain-of-thought.",
                ),
                bullets=(
                    "1. Intake validates required files, hashes evidence, and isolates one activity.",
                    "2. Reconstruction aligns plan, device streams, environment, and context.",
                    "3. Comparison identifies supported deviations and evidence gaps.",
                    "4. The bounded model synthesizes only compact extracted features.",
                    "5. A verifier rejects unsupported claims or schema violations and allows a bounded retry.",
                    "6. The coach reviews questions and explicitly approves any memory proposal.",
                ),
                callout="High-volume sensor rows are processed deterministically. Raw telemetry dumps are not sent directly to the model.",
            ),
            SectionSpec(
                "Product walkthrough",
                (
                    "The product story moves from club scale to a single investigation and back to longitudinal memory. The coach first sees coverage, exceptions, crews, and athletes. A selected session then exposes evidence ownership, reconstructed intervals, metric-level source authority, environmental limits, and the smallest unresolved human question.",
                    "After verification and coach approval, the session becomes reusable club memory. The same relational model supports athlete training days, crew history, indoor alternatives, goal review, and competition context without claiming that one observation caused a later result.",
                ),
                bullets=(
                    "Overview and Attention prioritize work instead of asking the coach to open every chart.",
                    "Team connects named crews, athletes, physical boats, substitutions, and training attendance.",
                    "Session review preserves the measured-versus-human boundary and evidence names.",
                    "Goal memory and Competition Review connect reviewed history to the next coaching cycle.",
                    "Evaluation remains a separate, transparent view of baseline, costs, trajectories, gains, and regressions.",
                ),
            ),
            SectionSpec(
                "Rowing data model across water and indoor work",
                (
                    "The public demonstration connects sixteen fictional athletes, ten recurring crews, eleven physical boats, and training across 2x, 4x, and 8x classes. Names and exact outcomes are fictional; formats and plausible patterns were informed by supplied coach plans, SpeedCoach files, PM5 photographs, and first-hand club context.",
                    "Concept2 results belong to one athlete even when a prescription is shared. Equivalent PM5 workouts can support within-workout comparisons of pace, SPM, and watts. They do not directly measure on-water speed, visible technique, muscular strength, injury, or medical fitness.",
                ),
                bullets=(
                    "Pre-regatta package: 52 activities, 52 validated, 52 reconstructed, 51 plan-compared, 2 agent-verified, 0 human-approved.",
                    "Post-regatta package: 50 additional activities for the same athletes and crews.",
                    "Combined club view: 102 activities and six deterministic longitudinal outcomes.",
                    "Water and indoor volume remain separate even when they occur on the same training day.",
                ),
            ),
            SectionSpec(
                "Product experience",
                (
                    "The interface begins with the club, not an isolated chart. Sessions is divided into Overview, Attention, Team, Intelligence, and Session reviews. Hash routes make primary destinations and detail pages bookmarkable, while location trails appear only on nested pages.",
                    "Compact information controls hold stable technical explanations so they do not dominate the page. Interpretation-changing evidence and limits remain visible in the normal flow. Saved results are labeled to show that reopening does not call a model or spend API budget.",
                ),
                bullets=(
                    "Overview: coverage, validation funnel, and coach-facing shortcuts.",
                    "Attention: questions and exceptions, never athlete verdicts.",
                    "Team: crews, athletes, physical boats, and PM5 context.",
                    "Intelligence: verified investigations, longitudinal replay, and saved synthesis.",
                    "Competition Review: race outcomes linked to lineups and prior evidence without claiming causation.",
                    "Evaluation: official fixed-case results, costs, failures, and case-level reports.",
                ),
            ),
            SectionSpec(
                "Evaluation design",
                (
                    "The primary comparison uses ten implemented v2 cases, one versioned grader, the same compact case summaries, the same output schema, and the same model family. The direct baseline makes one structured call with no tools or verifier. WAKE may use four deterministic tools and must pass verification.",
                    "The evaluation checks plan adherence, reconstruction, evidence grounding, uncertainty, source trust, human routing, and actionable coaching support. It does not claim that WAKE is superior to a human coach or that better scores imply improved athletic performance.",
                ),
                bullets=(
                    "One real anonymized case and nine controlled synthetic cases.",
                    "Same expected behavior and rubric applied to both workflows.",
                    "Saved trajectories make retries, tools, tokens, runtime, and costs auditable.",
                    "Negative results and abandoned ideas remain documented in the improvement changelog.",
                ),
            ),
            SectionSpec(
                "Measured results",
                (
                    "Across the ten fixed cases, bounded WAKE scored 83.76/100 and the direct baseline scored 49.00/100: a gain of 34.76 points at US$0.283344 incremental cost. Every case improved under the selected rubric.",
                    "The result is not uniformly positive. Environmental interpretation regressed from 80.00 to 76.00, and the single real anonymized case remains WAKE's weakest at 53.71. These results are preserved rather than edited away after inspection.",
                    "A separate four-report longitudinal pilot found NO_DEMONSTRATED_QUALITY_GAIN: both workflows passed the same non-scored capability checks. WAKE used fewer tokens and cost 29.01% less, which is useful operational evidence but not proof of better reasoning.",
                ),
                bullets=(
                    "Official WAKE score: 83.76/100.",
                    "Official direct baseline score: 49.00/100.",
                    "Observed saved club-memory run: US$0.037384 and 6,322 tokens.",
                    "Reopening saved model outputs: US$0.00.",
                ),
            ),
            SectionSpec(
                "Cost, persistence, and reproducibility",
                (
                    "WAKE spends model budget only after deterministic screening identifies a useful investigation. Every live start requires explicit authorization and shows the observed cost afterward. Saved outputs are application-owned artifacts and can be reopened or regraded offline without another model call.",
                    "The source package includes public fixtures and committed saved analyses, never the owner's API key. A clean reproduction script installs locked dependencies, runs verifiers and tests, lints the interface, creates a production build, and reports readiness at US$0.00 model cost.",
                ),
                bullets=(
                    "Replay is the default execution mode.",
                    "Live mode requires OPENAI_API_KEY plus a positive finite authorization.",
                    "Authorization permits a start; it is not a durable provider billing cap.",
                    "Local state survives refreshes and restarts but is not production storage.",
                ),
            ),
            SectionSpec(
                "What changed or failed",
                (
                    "The project records experiments that failed, regressed, or changed direction. This is part of the evidence, not an appendix of excuses. Examples include an environmental-scoring regression, a longitudinal pilot with no demonstrated quality gain, early navigation that was not bookmarkable, oversized explanatory banners, and an initial assumption that a few cases could describe the solution.",
                    "The current architecture also reflects scope corrections: mobile telemetry became optional, source authority became metric-specific, the product expanded from one hero session to club-scale relational memory, and PM5 records became an athlete-owned modality instead of crew performance evidence.",
                ),
                callout="A failed experiment can still improve the product when its expected behavior, evidence, cost, and decision are preserved.",
            ),
            SectionSpec(
                "Safety, privacy, and honest boundaries",
                (
                    "WAKE does not replace a qualified rowing coach. It does not autonomously select crews, diagnose injury or physiology, infer commitment from absence, or evaluate visible technique without appropriate video or biomechanical evidence.",
                    "Weather and race context are associative. A wind-correlated pace change does not establish causation. The correct causal conclusion is not established unless stronger evidence exists.",
                ),
                bullets=(
                    "Raw private GPS, device identifiers, credentials, and identifiable health data are excluded from the repository.",
                    "Public demonstration identities, sessions, club history, and exact outcomes are fictional.",
                    "Human approval is required before consequential coaching memory changes.",
                    "Prototype state is ignored by Git and user-restricted, but not encrypted, authenticated, backed up, or multi-tenant.",
                ),
            ),
            SectionSpec(
                "Submission readiness and next steps",
                (
                    "The reproducible MVP demonstrates the value chain from fragmented evidence to verified session review, club memory, longitudinal comparison, competition context, and fixed-case evaluation. The final interface narrative and five-minute video have completed owner QA.",
                    "The next product stage should validate the workflow with coaches over real longitudinal use, add authenticated multi-club storage, expand privacy controls, accept additional input adapters, and evaluate whether specialized agents improve quality enough to justify their cost and complexity.",
                ),
                bullets=(
                    "Keep the single bounded orchestration until evidence supports specialization.",
                    "Measure coach time saved, question resolution, review coverage, and false-confidence reduction.",
                    "Add more real anonymized cases before claiming broad generalization.",
                    "Treat competition as a high-value milestone, not the sole scope of the product.",
                ),
            ),
        ),
    )

    return guide, report


def _renderer():
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Flowable,
        Image,
        KeepTogether,
        ListFlowable,
        ListItem,
        PageBreak,
        Paragraph,
        Preformatted,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    palette = {
        "ink": colors.HexColor("#10201d"),
        "muted": colors.HexColor("#5d6d68"),
        "green": colors.HexColor("#176f65"),
        "mint": colors.HexColor("#e5f2ef"),
        "line": colors.HexColor("#c7d5d1"),
        "paper": colors.HexColor("#fafbf8"),
        "amber": colors.HexColor("#b66a1f"),
        "soft_amber": colors.HexColor("#f6eadc"),
        "slate": colors.HexColor("#7c8a86"),
    }

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "WakeBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.7,
        leading=14.2,
        textColor=palette["ink"],
        spaceAfter=7,
    )
    heading = ParagraphStyle(
        "WakeHeading",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        textColor=palette["ink"],
        spaceBefore=8,
        spaceAfter=10,
        keepWithNext=True,
    )
    subheading = ParagraphStyle(
        "WakeSubheading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=palette["green"],
        spaceBefore=8,
        spaceAfter=5,
        keepWithNext=True,
    )
    bullet = ParagraphStyle(
        "WakeBullet",
        parent=body,
        leftIndent=12,
        firstLineIndent=-7,
        bulletIndent=0,
        spaceAfter=4,
    )
    callout = ParagraphStyle(
        "WakeCallout",
        parent=body,
        fontName="Helvetica-Bold",
        textColor=palette["green"],
        backColor=palette["mint"],
        borderColor=palette["line"],
        borderWidth=0.6,
        borderPadding=9,
        spaceBefore=6,
        spaceAfter=10,
    )
    cover_title = ParagraphStyle(
        "WakeCoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=31,
        leading=35,
        alignment=TA_LEFT,
        textColor=palette["ink"],
        spaceAfter=14,
    )
    cover_subtitle = ParagraphStyle(
        "WakeCoverSubtitle",
        parent=body,
        fontSize=13,
        leading=18,
        textColor=palette["muted"],
        spaceAfter=20,
    )
    kicker = ParagraphStyle(
        "WakeKicker",
        parent=body,
        fontName="Courier-Bold",
        fontSize=8,
        leading=10,
        textColor=palette["green"],
        spaceAfter=10,
    )
    code = ParagraphStyle(
        "WakeCode",
        parent=body,
        fontName="Courier",
        fontSize=7.7,
        leading=11,
        leftIndent=8,
        rightIndent=8,
        borderColor=palette["line"],
        borderWidth=0.6,
        borderPadding=8,
        backColor=colors.white,
        spaceBefore=5,
        spaceAfter=8,
    )
    center_small = ParagraphStyle(
        "WakeCenterSmall",
        parent=body,
        alignment=TA_CENTER,
        fontSize=8,
        leading=10,
        textColor=palette["muted"],
    )
    caption = ParagraphStyle(
        "WakeCaption",
        parent=body,
        fontSize=7.8,
        leading=10.5,
        textColor=palette["muted"],
        spaceBefore=4,
        spaceAfter=0,
    )
    table_text = ParagraphStyle(
        "WakeTableText",
        parent=body,
        fontSize=7.7,
        leading=10.3,
        spaceAfter=0,
    )
    table_head = ParagraphStyle(
        "WakeTableHead",
        parent=table_text,
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    metric_label = ParagraphStyle(
        "WakeMetricLabel",
        parent=table_text,
        fontName="Courier-Bold",
        fontSize=6.7,
        leading=8.5,
        textColor=palette["muted"],
    )
    metric_value = ParagraphStyle(
        "WakeMetricValue",
        parent=body,
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        textColor=palette["green"],
        spaceAfter=2,
    )

    class ScoreChart(Flowable):
        def __init__(self, width: float = 150 * mm, height: float = 42 * mm):
            super().__init__()
            self.width = width
            self.height = height

        def draw(self):
            c = self.canv
            rows = [("WAKE", 83.76, palette["green"]), ("Direct baseline", 49.00, palette["slate"])]
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(palette["ink"])
            c.drawString(0, self.height - 10, "Official ten-case comparison")
            y = self.height - 29
            for label, value, color in rows:
                c.setFont("Helvetica", 8)
                c.setFillColor(palette["ink"])
                c.drawString(0, y + 2, label)
                x = 34 * mm
                w = 105 * mm
                c.setFillColor(palette["mint"])
                c.roundRect(x, y, w, 7, 3, fill=1, stroke=0)
                c.setFillColor(color)
                c.roundRect(x, y, w * value / 100, 7, 3, fill=1, stroke=0)
                c.setFont("Helvetica-Bold", 9)
                c.drawRightString(self.width, y + 1, f"{value:.2f}")
                y -= 18

    class PipelineDiagram(Flowable):
        def __init__(self, width: float = 165 * mm, height: float = 43 * mm):
            super().__init__()
            self.width = width
            self.height = height

        def draw(self):
            c = self.canv
            labels = ["Validate", "Reconstruct", "Investigate", "Verify", "Human review", "Memory"]
            gap = 4
            box_w = (self.width - gap * (len(labels) - 1)) / len(labels)
            y = 12
            for index, label in enumerate(labels):
                x = index * (box_w + gap)
                fill = palette["mint"] if index not in (2, 4) else palette["soft_amber"]
                c.setFillColor(fill)
                c.setStrokeColor(palette["line"])
                c.roundRect(x, y, box_w, 25, 4, fill=1, stroke=1)
                c.setFillColor(palette["ink"])
                c.setFont("Helvetica-Bold", 6.8)
                words = label.split()
                if len(words) == 1:
                    c.drawCentredString(x + box_w / 2, y + 9, label)
                else:
                    c.drawCentredString(x + box_w / 2, y + 13, words[0])
                    c.drawCentredString(x + box_w / 2, y + 5, " ".join(words[1:]))
                if index < len(labels) - 1:
                    c.setStrokeColor(palette["green"])
                    c.line(x + box_w, y + 12.5, x + box_w + gap - 1, y + 12.5)
                    c.line(x + box_w + gap - 3, y + 15, x + box_w + gap - 1, y + 12.5)
                    c.line(x + box_w + gap - 3, y + 10, x + box_w + gap - 1, y + 12.5)
            c.setFont("Courier", 7)
            c.setFillColor(palette["muted"])
            c.drawString(0, 1, "DETERMINISTIC")
            c.drawCentredString(self.width / 2, 1, "BOUNDED MODEL + VERIFIER")
            c.drawRightString(self.width, 1, "COACH-APPROVED")

    class ArchitectureDiagram(Flowable):
        def __init__(self, width: float = 165 * mm, height: float = 70 * mm):
            super().__init__()
            self.width = width
            self.height = height

        def draw(self):
            c = self.canv
            source_labels = ["Plan", "SpeedCoach", "Mobile", "Weather", "PM5", "Human"]
            gap = 4
            source_w = (self.width - gap * 5) / 6
            source_y = self.height - 24
            for index, label in enumerate(source_labels):
                x = index * (source_w + gap)
                c.setFillColor(colors.white)
                c.setStrokeColor(palette["line"])
                c.roundRect(x, source_y, source_w, 20, 4, fill=1, stroke=1)
                c.setFillColor(palette["ink"])
                c.setFont("Helvetica-Bold", 6.8)
                c.drawCentredString(x + source_w / 2, source_y + 7, label)

            layers = [
                ("DETERMINISTIC EVIDENCE LAYER", "Validate, align, normalize, extract compact features", palette["mint"]),
                ("BOUNDED WAKE AGENT", "Reconstruct  |  inspect sources  |  compare plan  |  synthesize", palette["soft_amber"]),
                ("VERIFIER AND CONTROL", "Schema + provenance + claim boundaries + bounded retry + cost gate", palette["mint"]),
                ("HUMAN CHECKPOINT AND MEMORY", "Attributed athlete / coach answer  ->  coach approval  ->  saved replay", colors.white),
            ]
            y = source_y - 35
            for index, (title, detail, fill) in enumerate(layers):
                c.setFillColor(fill)
                c.setStrokeColor(palette["green"] if index == 1 else palette["line"])
                c.roundRect(0, y, self.width, 26, 5, fill=1, stroke=1)
                c.setFillColor(palette["green"])
                c.setFont("Courier-Bold", 7)
                c.drawString(8, y + 15, title)
                c.setFillColor(palette["ink"])
                c.setFont("Helvetica", 7.5)
                c.drawString(8, y + 6, detail)
                if index < len(layers) - 1:
                    c.setStrokeColor(palette["green"])
                    c.line(self.width / 2, y, self.width / 2, y - 7)
                    c.line(self.width / 2 - 3, y - 4, self.width / 2, y - 7)
                    c.line(self.width / 2 + 3, y - 4, self.width / 2, y - 7)
                y -= 33

    def header_footer(canvas, doc):
        canvas.saveState()
        page_w, page_h = A4
        canvas.setStrokeColor(palette["line"])
        canvas.setLineWidth(0.5)
        canvas.line(18 * mm, 14 * mm, page_w - 18 * mm, 14 * mm)
        canvas.setFont("Courier-Bold", 7)
        canvas.setFillColor(palette["green"])
        canvas.drawString(18 * mm, 9 * mm, "WAKE - AGENTIC ROWING INTELLIGENCE")
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(palette["muted"])
        canvas.drawRightString(page_w - 18 * mm, 9 * mm, f"{doc.page}")
        canvas.restoreState()

    return {
        "A4": A4,
        "PageBreak": PageBreak,
        "Paragraph": Paragraph,
        "Image": Image,
        "Preformatted": Preformatted,
        "SimpleDocTemplate": SimpleDocTemplate,
        "Spacer": Spacer,
        "Table": Table,
        "TableStyle": TableStyle,
        "KeepTogether": KeepTogether,
        "ListFlowable": ListFlowable,
        "ListItem": ListItem,
        "colors": colors,
        "mm": mm,
        "palette": palette,
        "body": body,
        "heading": heading,
        "subheading": subheading,
        "bullet": bullet,
        "callout": callout,
        "cover_title": cover_title,
        "cover_subtitle": cover_subtitle,
        "kicker": kicker,
        "code": code,
        "center_small": center_small,
        "caption": caption,
        "table_text": table_text,
        "table_head": table_head,
        "metric_label": metric_label,
        "metric_value": metric_value,
        "ScoreChart": ScoreChart,
        "PipelineDiagram": PipelineDiagram,
        "ArchitectureDiagram": ArchitectureDiagram,
        "header_footer": header_footer,
    }


def _cover(spec: DocumentSpec, r: dict) -> list:
    Paragraph = r["Paragraph"]
    Spacer = r["Spacer"]
    Table = r["Table"]
    TableStyle = r["TableStyle"]
    mm = r["mm"]
    palette = r["palette"]
    colors = r["colors"]

    facts = [
        [Paragraph("<b>Prepared for</b>", r["body"]), Paragraph(spec.audience, r["body"])],
        [Paragraph("<b>Submission state</b>", r["body"]), Paragraph("Reproducible replay and owner-approved final media ready", r["body"])],
        [Paragraph("<b>Evidence date</b>", r["body"]), Paragraph("31 August 2026", r["body"])],
    ]
    table = Table(facts, colWidths=[35 * mm, 118 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.6, palette["line"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, palette["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return [
        Spacer(1, 22 * mm),
        Paragraph("EVERY ROW LEAVES A WAKE.", r["kicker"]),
        Paragraph(spec.title, r["cover_title"]),
        Paragraph(spec.subtitle, r["cover_subtitle"]),
        Spacer(1, 7 * mm),
        table,
        Spacer(1, 14 * mm),
        Paragraph(
            "Evidence-backed rowing review. Replay-first operation. Human-approved memory.",
            r["callout"],
        ),
    ]


def _section_flowables(section: SectionSpec, r: dict) -> list:
    Paragraph = r["Paragraph"]
    Preformatted = r["Preformatted"]
    Spacer = r["Spacer"]
    items: list = []
    paragraphs = [Paragraph(paragraph, r["body"]) for paragraph in section.paragraphs]
    if paragraphs:
        items.append(r["KeepTogether"]([Paragraph(section.heading, r["heading"]), paragraphs[0]]))
        items.extend(paragraphs[1:])
    else:
        items.append(Paragraph(section.heading, r["heading"]))
    if section.bullets:
        bullet_items = [
            r["ListItem"](Paragraph(item, r["body"]), leftIndent=11, spaceAfter=2)
            for item in section.bullets
        ]
        items.append(r["ListFlowable"](
            bullet_items,
            bulletType="bullet",
            start="-",
            leftIndent=12,
            bulletFontName="Helvetica",
            bulletFontSize=8,
            bulletOffsetY=1,
            spaceBefore=2,
            spaceAfter=7,
        ))
    for block in section.code_blocks:
        items.append(Preformatted(block, r["code"] ))
    if section.callout:
        items.append(Paragraph(section.callout, r["callout"]))
    items.append(Spacer(1, 3 * r["mm"]))
    return items


def _visual_frame(asset: VisualAsset, r: dict, width_mm: float = 159) -> object:
    width = width_mm * r["mm"]
    image = r["Image"](str(asset.path), width=width, height=width * 0.75)
    image.hAlign = "CENTER"
    frame = r["Table"](
        [[image], [r["Paragraph"](asset.caption, r["caption"])]],
        colWidths=[width],
        hAlign="CENTER",
    )
    frame.setStyle(r["TableStyle"]([
        ("BACKGROUND", (0, 0), (-1, -1), r["colors"].white),
        ("BOX", (0, 0), (-1, -1), 0.6, r["palette"]["line"]),
        ("LEFTPADDING", (0, 0), (-1, 0), 0),
        ("RIGHTPADDING", (0, 0), (-1, 0), 0),
        ("TOPPADDING", (0, 0), (-1, 0), 0),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
        ("LEFTPADDING", (0, 1), (-1, 1), 8),
        ("RIGHTPADDING", (0, 1), (-1, 1), 8),
        ("TOPPADDING", (0, 1), (-1, 1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 7),
    ]))
    return frame


def _report_table(rows: list[list[str]], widths_mm: list[float], r: dict) -> object:
    rendered: list[list[object]] = []
    for row_index, row in enumerate(rows):
        style = r["table_head"] if row_index == 0 else r["table_text"]
        rendered.append([r["Paragraph"](value, style) for value in row])
    table = r["Table"](
        rendered,
        colWidths=[width * r["mm"] for width in widths_mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    table.setStyle(r["TableStyle"]([
        ("BACKGROUND", (0, 0), (-1, 0), r["palette"]["green"]),
        ("BACKGROUND", (0, 1), (-1, -1), r["colors"].white),
        ("GRID", (0, 0), (-1, -1), 0.4, r["palette"]["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _metric_strip(metrics: list[tuple[str, str, str]], r: dict) -> object:
    cells = []
    for label, value, note in metrics:
        cells.append([
            r["Paragraph"](label, r["metric_label"]),
            r["Paragraph"](value, r["metric_value"]),
            r["Paragraph"](note, r["caption"]),
        ])
    table = r["Table"](
        [cells],
        colWidths=[159 * r["mm"] / len(cells)] * len(cells),
        hAlign="CENTER",
    )
    table.setStyle(r["TableStyle"]([
        ("BACKGROUND", (0, 0), (-1, -1), r["colors"].white),
        ("BOX", (0, 0), (-1, -1), 0.6, r["palette"]["line"]),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, r["palette"]["line"]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


def _build_detailed_report(root: Path, output_dir: Path, spec: DocumentSpec) -> Path:
    r = _renderer()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / spec.output_name
    doc = r["SimpleDocTemplate"](
        str(target),
        pagesize=r["A4"],
        rightMargin=18 * r["mm"],
        leftMargin=18 * r["mm"],
        topMargin=16 * r["mm"],
        bottomMargin=20 * r["mm"],
        title=spec.title,
        author="WAKE - Agentic Rowing Intelligence",
        subject=spec.subtitle,
        creator="WAKE submission PDF builder",
    )
    sections = {section.heading: section for section in spec.sections}
    visuals = {asset.role: asset for asset in report_visual_assets(root)}
    P = r["Paragraph"]
    S = r["Spacer"]
    PB = r["PageBreak"]
    mm = r["mm"]

    story: list = [
        S(1, 10 * mm),
        P("EVERY ROW LEAVES A WAKE.", r["kicker"]),
        P(spec.title, r["cover_title"]),
        P(
            "A visual solution dossier for rowing practitioners, hackathon judges, product reviewers, and technical evaluators.",
            r["cover_subtitle"],
        ),
        _metric_strip([
            ("CLUB MEMORY", "102", "public pre/post-regatta activities"),
            ("FIXED EVALUATION", "10", "same cases for both workflows"),
            ("MEASURED GAIN", "+34.76", "points over direct baseline"),
            ("SAVED REPLAY", "US$0", "to reopen committed results"),
        ], r),
        S(1, 8 * mm),
        _visual_frame(visuals["club_overview"], r, width_mm=145),
        S(1, 5 * mm),
        P("Evidence-backed review. Metric-level source trust. Human-approved memory.", r["callout"]),
        PB(),
    ]

    executive = sections["Executive summary"]
    problem = sections["The operational problem"]
    users = sections["Users and human workflow"]
    story.extend([
        P("01  Problem, users, and product value", r["kicker"]),
        P("One file is manageable. A whole club is not.", r["heading"]),
        P(executive.paragraphs[0], r["body"]),
        P(executive.paragraphs[1], r["body"]),
        P(problem.paragraphs[0], r["body"]),
        _report_table([
            ["Before WAKE", "WAKE contribution", "Human authority"],
            ["Plans, device exports, weather, lineups, boats, and conversations remain fragmented.", "Normalizes evidence, investigates contradictions, and shows only supported claims.", "Athletes provide first-hand execution context; coaches own consequential approval."],
            ["A spreadsheet stores rows but does not decide what deserves attention.", "Deterministic screening selects exceptions before any paid investigation.", "A missing session remains a question, never a fitness, injury, or commitment verdict."],
            ["A direct summary can sound complete even when evidence is incomplete.", "Verifier-enforced uncertainty, provenance, and source boundaries survive the final output.", "Human answers add attributed context; they never rewrite measured telemetry."],
        ], [53, 56, 50], r),
        S(1, 5 * mm),
        P(users.paragraphs[0], r["body"]),
        P("WAKE does not replace a qualified rowing coach. It prepares consistent, exception-focused evidence for review.", r["callout"]),
        PB(),
    ])

    architecture = sections["System architecture"]
    story.extend([
        P("02  System architecture", r["kicker"]),
        P("Bounded intelligence between evidence and memory", r["heading"]),
        P(architecture.paragraphs[0], r["body"]),
        r["ArchitectureDiagram"](),
        S(1, 3 * mm),
        _report_table([
            ["Capability", "Implementation boundary", "Why it exists"],
            ["Validate and normalize", "Deterministic adapters and schemas", "Reject malformed or mismatched evidence before reasoning."],
            ["Reconstruct and compare", "Four read-only investigation tools", "Turn high-volume rows into compact, inspectable findings."],
            ["Synthesize", "One bounded orchestrating agent", "Choose tools, reconcile evidence, and draft a structured review."],
            ["Verify", "Schema, provenance, and claim checks", "Reject unsupported assertions and allow only a bounded retry."],
            ["Approve memory", "Athlete / coach checkpoint", "Keep consequential context under accountable human control."],
        ], [38, 53, 68], r),
        S(1, 4 * mm),
        P(architecture.paragraphs[1], r["callout"]),
        PB(),
    ])

    evidence = sections["Evidence architecture and metric-level trust"]
    workflow = sections["The bounded agentic workflow"]
    story.extend([
        P("03  Evidence and trust", r["kicker"]),
        P("The best source can change by metric", r["heading"]),
        P(evidence.paragraphs[0], r["body"]),
        _report_table([
            ["Evidence", "Status", "Supports", "Does not prove"],
            ["Training plan", "Core", "Intent, intervals, target SPM, recovery, objective", "What was actually completed"],
            ["SpeedCoach", "Core", "Dedicated rowing pace, distance, stroke-rate evidence", "Crew context or visible technique"],
            ["Mobile telemetry", "Optional enhancer", "Route, timing overlap, corroborating sensors", "Automatic authority over a more consistent source"],
            ["Environment", "Optional enhancer", "Time-aligned wind, gust, temperature, humidity", "That weather caused a performance change"],
            ["Concept2 PM5", "Athlete-owned", "Indoor pace, watts, SPM, workout structure", "On-water speed, technique, strength, or health"],
            ["Human context", "Attributed", "Equipment, effort, interruption, crew observation", "A rewrite of device measurements"],
        ], [29, 27, 56, 47], r),
        S(1, 5 * mm),
        P("Every statement is typed", r["subheading"]),
        _report_table([
            ["Observed", "Derived", "Human context", "Hypothesis", "Action", "Unknown"],
            ["Direct evidence", "Transparent calculation", "Attributed answer", "Marked inference", "Coach-reviewable action", "Explicit gap"],
        ], [26.5, 26.5, 26.5, 26.5, 26.5, 26.5], r),
        S(1, 5 * mm),
        P(workflow.callout or "", r["callout"]),
        PB(),
    ])

    walkthrough = sections["Product walkthrough"]
    story.extend([
        P("04  Product walkthrough", r["kicker"]),
        P("Start at club scale", r["heading"]),
        P(walkthrough.paragraphs[0], r["body"]),
        _visual_frame(visuals["club_overview"], r),
        S(1, 5 * mm),
        _metric_strip([
            ("PRE-REGATTA", "52", "validated and reconstructed activities"),
            ("POST-REGATTA", "50", "additional longitudinal activities"),
            ("ATHLETES", "16", "fictional identities in the public demo"),
            ("CREWS", "10", "recurring 2x, 4x, and 8x lineups"),
        ], r),
        PB(),
    ])

    data_model = sections["Rowing data model across water and indoor work"]
    side_width = 77
    story.extend([
        P("05  Team and athlete memory", r["kicker"]),
        P("People, lineups, boats, and training days", r["heading"]),
        P(data_model.paragraphs[0], r["body"]),
        r["Table"](
            [[_visual_frame(visuals["team_memory"], r, side_width), _visual_frame(visuals["athlete_history"], r, side_width)]],
            colWidths=[79.5 * mm, 79.5 * mm],
            hAlign="CENTER",
            style=r["TableStyle"]([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
            ]),
        ),
        S(1, 5 * mm),
        _report_table([
            ["Relationship retained", "Product value"],
            ["Athlete -> crew -> physical boat -> outing", "A coach can inspect shared history without losing individual ownership."],
            ["Athlete -> solo water / Concept2 -> training day", "Indoor-only work is valid training, not a missing-water-session alert."],
            ["Crew snapshot -> race entry -> official field", "A later result retains who raced together without rewriting training causality."],
        ], [58, 101], r),
        P(data_model.paragraphs[1], r["callout"]),
        PB(),
    ])

    story.extend([
        P("06  Session investigation", r["kicker"]),
        P("Reconstruct, verify, and ask the right person", r["heading"]),
        _visual_frame(visuals["session_investigation"], r),
        S(1, 5 * mm),
        r["PipelineDiagram"](),
        S(1, 3 * mm),
        _report_table([
            ["Checkpoint", "What becomes available", "What remains protected"],
            ["Evidence received", "A deterministic reconstruction and evidence gaps", "No paid model call happens automatically."],
            ["Bounded investigation", "Supported deviations, trusted sources, and human questions", "Verifier rejects unsupported claims and malformed provenance."],
            ["Attributed answer", "Human context linked to athlete, coach, or source owner", "Measurements remain unchanged."],
            ["Coach approval", "A saved briefing can enter club memory", "No automatic training prescription or crew selection."],
        ], [37, 61, 61], r),
        PB(),
    ])

    story.extend([
        P("07  Goal readiness and competition", r["kicker"]),
        P("Close the loop without inventing causation", r["heading"]),
        _visual_frame(visuals["competition_review"], r),
        S(1, 5 * mm),
        P(
            "Ten fictional club entries across eight fictional events connect all sixteen athletes to exact lineup snapshots, physical boats, pre-race shared outings, opponent clubs, official order, pace, gaps, and one context-seeking non-completion. Category distances are informed by supplied competition material, while identities and displayed outcomes remain fictional.",
            r["body"],
        ),
        _report_table([
            ["WAKE can show", "WAKE must not claim"],
            ["Training context before the race, the exact lineup, boat, opposition, official order, and missing evidence.", "That one session, crew change, or weather condition caused the result."],
            ["Comparable observations across periods when the evidence contract matches.", "Automatic selection, athletic potential, injury, physiology, or medical conclusions."],
        ], [79.5, 79.5], r),
        PB(),
    ])

    results = sections["Measured results"]
    story.extend([
        P("08  Evaluation", r["kicker"]),
        P("Measured against the same ten sessions", r["heading"]),
        _visual_frame(visuals["evaluation_results"], r),
        S(1, 4 * mm),
        _report_table([
            ["Workflow", "Score", "Cases", "Observed cost", "Interpretation"],
            ["Direct baseline", "49.00 / 100", "10", "Reference", "One structured model call; no investigation tools or verifier."],
            ["Bounded WAKE", "83.76 / 100", "10", "+US$0.283344", "Four tools, verification, claim boundaries, and saved trajectories."],
            ["Measured gain", "+34.76 points", "10 / 10 improved", "+70.94% relative", "Workflow evidence only; not a human-coach comparison."],
        ], [34, 27, 25, 30, 43], r),
        S(1, 4 * mm),
        P(results.paragraphs[1], r["callout"]),
        PB(),
    ])

    changed = sections["What changed or failed"]
    story.extend([
        P("09  Learning and TDD", r["kicker"]),
        P("Failures remained part of the evidence", r["heading"]),
        P(changed.paragraphs[0], r["body"]),
        _report_table([
            ["Experiment or failure", "Observed evidence", "Decision kept in the product"],
            ["Three-case framing", "Too narrow to express wind, changing conditions, incorrect execution, crews, and longitudinal context.", "Expanded to ten fixed evaluations plus a 102-activity relational club demonstration."],
            ["Core reconstructed-distance claim", "The first evidence ablation overinterpreted derived segment margins as completed-distance shortfall.", "Added a failing regression test and verifier-enforced distance boundary; v2 passed 8/8, 10/10, and 12/12 checks."],
            ["Longitudinal reasoning pilot", "WAKE and baseline both passed the same non-scored capability checks.", "Preserved NO_DEMONSTRATED_QUALITY_GAIN; report only the observed 29.01% cost reduction."],
            ["Environment interpretation", "Official dimension score regressed from 80% to 76%.", "Keep weather associative, visible, and explicitly non-causal."],
            ["More autonomous agents", "No submitted evidence showed specialization improved the MVP.", "Keep one bounded orchestrator until evaluation justifies extra complexity and cost."],
        ], [43, 61, 55], r),
        S(1, 5 * mm),
        _report_table([
            ["RED", "GREEN", "REFACTOR", "EVALUATE"],
            ["Write a failing behavioral or regression test.", "Implement the smallest deterministic change.", "Preserve boundaries while the full suite stays green.", "Run fixed cases and record gains, regressions, cost, and decisions."],
        ], [39.75, 39.75, 39.75, 39.75], r),
        S(1, 4 * mm),
        P(changed.callout or "", r["callout"]),
        PB(),
    ])

    cost = sections["Cost, persistence, and reproducibility"]
    safety = sections["Safety, privacy, and honest boundaries"]
    readiness = sections["Submission readiness and next steps"]
    story.extend([
        P("10  Reproduction, cost, and boundaries", r["kicker"]),
        P("A judge can reopen the evidence without a key", r["heading"]),
        P(cost.paragraphs[0], r["body"]),
        _report_table([
            ["Artifact or run", "Observed model cost", "Can reopen without a call?"],
            ["Official ten-case incremental WAKE comparison", "US$0.283344", "Yes"],
            ["Saved 102-activity club memory", "US$0.037384 / 6,322 tokens", "Yes, US$0.00"],
            ["Two saved demo-club investigations", "US$0.194118 combined", "Yes, US$0.00"],
            ["Clean reproduction and dashboard replay", "US$0.00", "Yes; no OPENAI_API_KEY required"],
            ["Optional new live investigation", "Authorized per start", "The new output is saved after verification"],
        ], [68, 44, 47], r),
        S(1, 5 * mm),
        P("Clean judge path", r["subheading"]),
        r["Preformatted"](
            "./scripts/reproduce_submission.sh\n./scripts/start_dashboard.sh\n# open http://localhost:3000/\n# replay and saved evaluation cost US$0.00",
            r["code"],
        ),
        P(safety.paragraphs[0], r["body"]),
        _report_table([
            ["Public submission includes", "Public submission excludes"],
            ["Synthetic fixtures, minimized approved references, saved outputs, trajectories, tests, schemas, prompts, and PDFs.", "API keys, .env, private GPS, device identifiers, identifiable health data, and raw private athlete records."],
        ], [79.5, 79.5], r),
        S(1, 5 * mm),
        P(readiness.paragraphs[0], r["callout"]),
        P("Every row leaves a wake. WAKE makes that trail inspectable without pretending uncertainty has disappeared.", r["cover_subtitle"]),
    ])

    doc.build(story, onFirstPage=r["header_footer"], onLaterPages=r["header_footer"])
    return target


def _build_one(root: Path, output_dir: Path, spec: DocumentSpec, detailed: bool) -> Path:
    r = _renderer()
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / spec.output_name
    doc = r["SimpleDocTemplate"](
        str(target),
        pagesize=r["A4"],
        rightMargin=18 * r["mm"],
        leftMargin=18 * r["mm"],
        topMargin=18 * r["mm"],
        bottomMargin=20 * r["mm"],
        title=spec.title,
        author="WAKE - Agentic Rowing Intelligence",
        subject=spec.subtitle,
        creator="WAKE submission PDF builder",
    )
    story = _cover(spec, r)
    story.append(r["PageBreak"]())

    if detailed:
        story.extend([
            r["Paragraph"]("Solution at a glance", r["heading"]),
            r["PipelineDiagram"](),
            r["Spacer"](1, 5 * r["mm"]),
            r["ScoreChart"](),
            r["Paragraph"](
                "The score comparison evaluates fixed model workflows. It is not evidence of superiority over a human coach or of improved athletic performance.",
                r["callout"],
            ),
            r["PageBreak"](),
        ])
    else:
        facts = [
            ["Mode", "Model call", "API key", "Expected model cost"],
            ["Clean reproduction", "No", "Not required", "US$0.00"],
            ["Dashboard replay", "No", "Not required", "US$0.00"],
            ["Optional live", "Yes", "Required", "Authorized per run"],
        ]
        table = r["Table"](facts, colWidths=[42 * r["mm"], 30 * r["mm"], 35 * r["mm"], 47 * r["mm"]])
        table.setStyle(r["TableStyle"]([
            ("BACKGROUND", (0, 0), (-1, 0), r["palette"]["green"]),
            ("TEXTCOLOR", (0, 0), (-1, 0), r["colors"].white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.4, r["palette"]["line"]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.extend([
            r["Paragraph"]("Choose the correct execution path", r["heading"]),
            table,
            r["Spacer"](1, 7 * r["mm"]),
            r["Paragraph"](
                "Recommended judge path: run the clean reproduction, start replay, inspect the saved dashboard and evaluation, then use live mode only if a new paid investigation is desired.",
                r["callout"],
            ),
            r["PageBreak"](),
        ])

    for section in spec.sections:
        story.extend(_section_flowables(section, r))

    doc.build(story, onFirstPage=r["header_footer"], onLaterPages=r["header_footer"])
    return target


def build_pdfs(root: Path, output_dir: Path) -> tuple[Path, Path]:
    guide, report = document_specs(root)
    return (
        _build_one(root, output_dir, guide, detailed=False),
        _build_detailed_report(root, output_dir, report),
    )


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    output_dir = (args.output_dir or (root / "output" / "pdf")).resolve()
    for path in build_pdfs(root, output_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
