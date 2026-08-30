# WAKE ElevenLabs v3 voiceover generation sheet

model_id: `eleven_v3`

language: `English`

outputs: `seven separate audio files`

## wake-vo-01-problem-and-attention.mp3

Target: `00:00–01:05` · approximately `65 seconds`

```text
[thoughtfully] In a rowing club, the plan may arrive through WhatsApp. The SpeedCoach file usually stays with the athlete. Another phone may record the route. The coach knows the crew and the conditions, but cannot follow every boat every day. [short pause] A spreadsheet organizes the files, and a simple baseline can ask G P T to summarize one session. Neither one preserves the questions, relationships, and decisions that accumulate across the club. That is the problem WAKE was built to solve. [short pause] [confidently] WAKE begins at club scale. The coach sees which sessions were reconstructed, which crews went out, which records need a source, and which questions need a person. Here, Harbor Men's double scull is connected to its physical boat, lineup, and outings. Missing training is shown as something to investigate, not as a judgment about commitment, fitness, or injury.
```

## wake-vo-02-session-review.mp3

Target: `01:05–02:00` · approximately `55 seconds`

```text
[curious] Now the coach opens one real rowing question: did the crew execute the six one-kilometer pieces at the prescribed stroke rates? The training plan and SpeedCoach are enough to begin. Mobile telemetry, weather, and human context can improve the review when they exist, but they are not mandatory. [short pause] [measured] WAKE reconstructs the six work pieces and finds that most followed the plan, while one interval needs attention. It trusts the SpeedCoach for stroke rate, rejects the phone's zero-only stroke-rate signal, and can still use the phone for route or timing support. The wind changed during the row, but WAKE does not call that the cause of the result.
```

## wake-vo-03-human-checkpoint.mp3

Target: `02:00–02:35` · approximately `35 seconds`

```text
[calmly] Devices cannot tell us whether the resistance band was removed after the third repetition. That question belongs to the athlete, or to someone who directly observed the session. WAKE records who answered, who entered the answer, and why that person has authority to say it. [short pause] The answer adds context. It never rewrites the telemetry. [warmly] The coach reviews the briefing, and only an explicit approval turns it into club memory.
```

## wake-vo-04-longitudinal-memory.mp3

Target: `02:35–03:25` · approximately `50 seconds`

```text
[thoughtfully] One session is manageable. The real problem appears when another two weeks arrive. WAKE now connects one hundred and two activities for the same sixteen athletes and ten crews. It can distinguish comparable progress, slower comparable work, stable execution, weather-confounded sessions, missing participation, and cases that simply cannot be compared yet. [short pause] For Lucas, Training Days connect crew outings, solo rows, and Concept Two work without adding indoor meters to water distance as if they were the same thing. At club level, the saved briefing gives the coach priorities and focused questions. It does not invent a performance trend just because more data exists. Reopening this verified memory costs zero dollars.
```

## wake-vo-05-competition-review.mp3

Target: `03:25–03:55` · approximately `30 seconds`

```text
[confidently] Training eventually meets competition. Competition Review connects the same athletes, exact crew snapshot, physical boat, shared outings, and full race field. A coach can review the path to the regatta and the result together. [short pause] WAKE still does not claim that one workout or lineup caused the finish, and it does not select crews automatically. When a result is missing, it asks for context instead of inventing one.
```

## wake-vo-06-measured-evidence.mp3

Target: `03:55–04:25` · approximately `30 seconds`

```text
[measured] We tested the workflow against the same simple baseline on ten frozen cases. The direct G P T baseline scored forty-nine point zero zero out of one hundred. WAKE scored eighty-three point seven six. Every case improved overall, while environmental interpretation regressed from eighty to seventy-six percent, and we kept that limitation visible. [short pause] This demonstrates a stronger evidence workflow on these fixed cases. It is not a comparison with a human coach, and not proof of athletic improvement.
```

## wake-vo-07-learning-and-close.mp3

Target: `04:25–05:00` · approximately `35 seconds`

```text
[reflectively] The most useful change came from a failure. Early WAKE treated reconstructed distance as proof that the prescribed distance was completed. We removed that behavior, wrote a failing test, changed the evidence boundary, and reran the fixed evaluation. We also preserved a longitudinal experiment that showed no quality gain. Our history includes what did not work, not only the wins. [short pause] [warmly] Every row leaves a wake. WAKE turns fragmented training into memory a coach and athlete can use together.
```
