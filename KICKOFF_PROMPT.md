# Kickoff prompt

Paste the text below as your first message to Claude Code, from the repo root that contains this package.

---

You are the lead engineer on **AURORA Lifeline**, our Track 05 entry for the hackathon _Build with AI: Code for Communities, Second Edition_. The research, idea selection, spec and plan are finished and are in this repo. Your job is to build it.

**Deadline:** Gate G1 is 29 Sep 2026 at 23:00 IST. Code freeze is 30 Sep at 18:00 IST. We submit by 30 Sep at 22:00 IST; the portal closes at 23:59.

1. Read `CLAUDE.md` (including its precedence rule), then these files in order: `docs/HANDOFF.md`, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ENGINE.md`, `docs/AI_AGENTS.md`, `docs/DATA.md`, `docs/BUILD_PLAN.md`, `docs/COSTS.md` and `docs/DEMO_AND_SUBMISSION.md`. Use `docs/BLUEPRINT.md` and `docs/research/` only as evidence.
2. Reply with:
   - the product and the non-negotiables in 10 bullets or fewer;
   - the owner actions still open from `docs/HANDOFF.md`, in time order, with exact steps;
   - anything still ambiguous, with your proposed resolution;
   - your plan for the next 6 hours, following the critical path and the solo-mode checkpoints in `docs/BUILD_PLAN.md`.
3. Then start immediately on the approval-free work:
   - task 1.1 (scaffold and CI);
   - task 1.3 (schemas and codegen);
   - task 1.4a (downloads), **beginning with the 30-minute check of Montha coverage in ECMWF and Weather Lab**. Record the result in `docs/HANDOFF.md`.
4. Prepare `infra/bootstrap.sh`, but run it only after I confirm the project ID and billing account. The APIs pre-approved in `docs/COSTS.md` §1a may then be enabled without asking again. Everything else in `docs/COSTS.md` §1a still needs my yes, including large jobs, anything over US$10, and any AI Studio billing. The budget is US$150.
5. Before coding against Gemini, Earth Engine, Maps or Firebase, check the current official docs and model availability on Agent Platform, and record what you verified in `docs/HANDOFF.md`.
6. Follow every non-negotiable in `CLAUDE.md`:
   - no AURORA numbers from Gemini (placeholders and a post-check);
   - IMD is the authority;
   - officer approval, and officer confirmation of every bridge reopening;
   - simulated data labelled;
   - asset-level results public only for archived replays;
   - no personal data or secrets;
   - no GPL runtime dependencies;
   - no code copied from other entries;
   - no hindsight tracks as forecast inputs.
7. Work in small, tested commits and keep the judge replay deterministic. Tell me whenever you need something only I can do: registration, consoles, the photo, reviews, recording, submission. At the end of each session, update the status, session log and any cuts in `docs/HANDOFF.md`.
