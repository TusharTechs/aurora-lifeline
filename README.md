# AURORA Lifeline: handoff package

This package gives a fresh Claude Code session (or a new teammate) the full context to build AURORA Lifeline. AURORA Lifeline is our Track 05 entry for *Build with AI: Code for Communities, Second Edition*. **Submission closes 30 Sep 2026, 23:59 IST.**

## How to use it

1. Create an empty repo folder (for example `aurora-lifeline/`) and copy everything in this package into its root. `CLAUDE.md` must sit at the repo root, because Claude Code loads it automatically.
2. Open Claude Code in that folder.
3. Paste the prompt from `KICKOFF_PROMPT.md`.
4. Complete the owner actions listed in `docs/HANDOFF.md`: Cloud project and billing, Earth Engine registration, WeatherNext and Flood Hub requests, GitHub repo. Some steps need you personally (web forms, account sign-ins).

## What's inside

| File | Purpose |
| --- | --- |
| `CLAUDE.md` | Project instructions Claude Code reads first: goal, deadlines, non-negotiables, stack, repo layout, commands, gotchas |
| `KICKOFF_PROMPT.md` | The first message to paste into the new session |
| `docs/HANDOFF.md` | Status, decisions and reasons, owner actions, open questions, risks, competitor notes, session log |
| `docs/SPEC.md` | Product spec: users, concepts, screens, acceptance criteria, non-functional requirements |
| `docs/ARCHITECTURE.md` | Components, data flow, BigQuery and Firestore schemas, API, scaling, configuration, deployment |
| `docs/ENGINE.md` | Hazard, network, power, health, action and validation algorithms with parameters and sources |
| `docs/AI_AGENTS.md` | Gemini models, access, number safety, prompts, schemas, tools, injection defences, evaluation |
| `docs/DATA.md` | Datasets, IDs, licences, processing steps, attribution block, synthetic-data policy |
| `docs/BUILD_PLAN.md` | Timed plan to 30 Sep with acceptance criteria and gates; Demo Day backlog |
| `docs/COSTS.md` | US$150 budget allocation, cost controls, costs outside Google Cloud |
| `docs/DEMO_AND_SUBMISSION.md` | Demo script, backups, failure plan, track-to-feature map, deck outline, submission checklist |
| `docs/BLUEPRINT.md` | The full research and product blueprint, including the evidence behind every decision |
| `docs/research/` | Raw research reports, fact-checks and the decision panel |

The live, editable version of the blueprint is the team's Claude Doc, "Code for Communities 2.0 — Research & Product Blueprint". This package is a snapshot taken on 28 Sep 2026.
