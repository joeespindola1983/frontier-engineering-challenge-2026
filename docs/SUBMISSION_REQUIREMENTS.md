# Hackathon Submission Requirements

This checklist summarizes the official micro1 Agentic Workflows Hackathon brief supplied to participants. Consult the source PDF before final submission if the organizer publishes an updated version.

Current WAKE coverage and manual closeout items are tracked in
[`SUBMISSION_AUDIT.md`](SUBMISSION_AUDIT.md).

## Core challenge

Choose a specific, meaningful problem understood by the team. Explain:

1. who has the problem;
2. which bottleneck makes it worth solving;
3. whether the agent solves it well;
4. whether another person can reproduce the result.

Agent capabilities must be purposeful. Better context, tools, memory, verification, skills, or orchestration matter only when they measurably improve the solution.

## Baseline and evaluation

- Create a reasonable simple baseline representing the task before the final workflow.
- Give baseline and final solution the same task and evaluation cases.
- Explain meaningful resource differences between them.
- Choose one primary metric that reflects user success.
- Define a good final result before running the evaluation.
- Share complete results, not only favorable examples.
- Target at least ten cases when the task permits.
- Include at least one challenging case and explain what it revealed.
- Where relevant, also report human time and cost per task.

## Judging rubric

| Criterion | Points | What must be demonstrated |
| --- | ---: | --- |
| Problem and User Value | 15 | A meaningful problem for a clearly defined user. |
| Agent Solution and Engineering | 30 | Purposeful, technically sound agent design choices. |
| End-to-End Quality | 20 | A realistic, self-contained execution with a polished result a user could use. |
| Measured Improvement | 15 | Fair gains over baseline, connected to changelog evidence. |
| Reproducibility | 15 | A clean path for another person to run baseline, solution, and evaluation. |
| Hot Take / Insights | 5 | A practical lesson derived from an observed failure mode. |
| **Total** | **100** | |

## Ground rules

- Existing tools and familiar components are allowed.
- Clearly disclose what existed before the competition and what was added.
- Follow licenses and service terms.
- Keep consequential actions in a sandbox or simulation and require human approval before they happen.
- Include a qualified human reviewer when the solution could significantly affect someone.
- Use a legal and ethical case and handle personal data responsibly.
- Use information the team is allowed to share; public, synthetic, or approved anonymous data are preferred.
- Exclude credentials and private information from the submission.
- Connect every result claim to submitted evidence.
- Give judges enough access to reproduce the main result.

## Required final deliverables

### 1. Complete solution code and Improvement Changelog

- Full project and everything required to run it.
- Code plus the instructions shaping every agent.
- README identifying the intended user, current bottleneck, and practical value.
- One changelog entry per meaningful iteration, connected to evidence and the next decision.
- Main failure mode and final hot take.
- Include removed experiments and what they taught.

### 2. Reproduction guide

- Written for a clean environment.
- Exact setup and commands for the solution, baseline, and evaluation.
- Required data and expected output.
- Relevant versions, approximate runtime, and cost.

### 3. Solution video

- Maximum duration: five minutes.
- Begin with the problem and simple baseline.
- Show one realistic execution from start to finish.
- Show the final comparison and summarize the changelog.
- Highlight the most impactful change and one removed experiment.

### 4. Agent trajectories

- Representative trajectories for every agent used.
- Followable from agent instructions to final result.
- Show actions and tool responses.
- Capture feedback affecting the next step, retries, and human checkpoints.

## WAKE evidence rule

No feature, performance, accuracy, time-saving, cost, or reliability statement should be presented as a result unless the repository contains the command, cases, output, and interpretation supporting that statement.
