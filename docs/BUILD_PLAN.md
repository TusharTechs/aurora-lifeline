# Build plan

Times are IST. Today is 28 Sep 2026.

| Milestone | Time |
| --- | --- |
| **Gate G1:** a Montha run is end to end (bulletin or hand-entered member 0 → tracks → hazards → closures → isolation → published JSON) | 29 Sep, 23:00 |
| **Code freeze** | 30 Sep, 18:00 |
| **Submit** | By 30 Sep, 22:00 (the portal closes at 23:59) |

Phase 5 is intentionally absent from the slice: it is the Demo Day build (backlog at the end).

## Critical path (one Claude Code session plus the owner)

1. **Phase 1:** 1.1 → 1.3 → 1.4a (approval-free downloads; start now). Then, once the owner approves: 1.2 → 1.4b (Earth Engine exports run in the background).
2. **Engine to G1:** 2.3 (Andhra Pradesh landfall district first) → 2.1 (a hand-entered IMD member 0 is fine) → 2.2 → 2.4 → 2.5 → 2.7-min (district JSON and tiles for that district) → 4.1–4.2 → 2.6 → 2.7 (all districts built so far) → **G1**.
3. **After G1:** 3.1 (replaces the hand-entered member 0) → 3.2 → 4.3 → 6.1–6.2 → 4.4–4.5 → 3.3 → 6.3 → 7 → 8.

**Local-first until task 1.2 exists.** Pipelines read and write local GeoParquet under `data/ref/<state>/<build_id>/` and `data/runs/<run_id>/`, using the BigQuery column names from `docs/ARCHITECTURE.md` §6. Wherever an acceptance criterion says "rows written" or "table", it means these files. `make publish RUN=<run_id>` loads them into BigQuery, Cloud Storage and Firestore once 1.2 exists. **G1 does not require 1.2.**

## Solo-mode checkpoints (the default unless the owner names teammates)

| Checkpoint | Condition | If it fails |
| --- | --- | --- |
| C0, 28 Sep, 14:00 | Montha coverage in ECMWF and Weather Lab checked and recorded | Apply the "If blocked" rows below |
| C1, 29 Sep, 06:00 | AP landfall-district graph built and snapped | Limit the slice to that district and its two neighbours |
| C2, 29 Sep, 14:00 | Isolation for one district published as JSON | Power (M5) becomes "not modelled"; Odisha moves to Demo Day |
| C3, 29 Sep, 23:00 | G1 | Cut to hospitals, CHCs and PHCs only; skip power; one district; still submit |
| C4, 30 Sep, 12:00 | Advisory checks pass in all shipped languages | Ship English and Telugu only; label Hindi and Odia as Demo Day |
| C5, 30 Sep, 15:00 | Two-browser live update works | Show the cached verdict and the officer-confirm step in one browser |

**Cut order when late** (first to go first):

1. S1 live recompute
2. Hindi and Odia advisories
3. Odisha
4. Proof-page baselines (keep AURORA's scores and misses)
5. Power
6. Second district

**Never cut:** judge mode, the provenance bar, SIMULATED badges, the proof page with misses, the deployed link.

Record every cut in `docs/HANDOFF.md`.

## Workstreams (if a team is available)

| Stream | Owns |
| --- | --- |
| A Engine | Tracks, wind, surge, flood, closures, reachability, power, health, actions |
| B Data and validation | Downloads, Earth Engine exports, OSM graph, facilities and settlements, Sentinel-1 validation, completeness |
| C AI and API | Gemini agents, cache, CAP, FastAPI, Firestore rules, in-API recompute, dispatch |
| D Web and demo | Static Next.js app, map and layers, approval UX, proof and about pages, click-path script, deck, README |

## Phase 1: Foundation (28 Sep)

| Task | Acceptance criteria |
| --- | --- |
| 1.1 Repo scaffold: layout from `CLAUDE.md`; Makefile (including the `make setup` system-tool checks); uv and pnpm workspaces; linters; tests; pre-commit; Apache-2.0 LICENSE; `.env.example`; CI with secret scanning | `make setup && make test` passes locally and in CI; no secrets in the tree |
| 1.3 Schemas: `bulletin_reading`, `field_observation`, `advisory_draft`, `facts_payload`, `district_scenario`, `run_manifest` (`docs/ARCHITECTURE.md` §5 and `docs/AI_AGENTS.md`); the vendored CAP XSD; codegen | `make schemas` generates Pydantic and TypeScript types; both compile; a sample district JSON validates |
| 1.4a Approval-free downloads, started immediately, to `data/raw/<source>/<version>/` with `sha256sums.txt`: **first, a check of Montha coverage (30 minutes or less)**; Geofabrik southern-zone and eastern-zone; OSM land polygons; the IMD Montha bulletins (every one from genesis to landfall); ECMWF `enfo`/`tf` BUFR for 24–29 Oct 2025; Weather Lab Montha CSVs; the IBTrACS NI CSV; the CAP XSD.

**No-sign-in rasters,** so the graph never waits for Earth Engine:
- Copernicus DEM GLO-30 tiles for the area of interest from the AWS open-data bucket `s3://copernicus-dem-30m/`;
- WorldPop 2020 100 m India (`IND_ppp_2020`, the same product as `WorldPop/GP/100m/pop`) from data.worldpop.org;
- JRC Global Surface Water `occurrence` tiles from the JRC/Google download bucket.

Then write `config/aoi/<state>.geojson` and `config/states/<state>_districts.csv`. The LGD file comes from the owner (CAPTCHA); until it arrives, key districts by `osm_relation_id` | Checksums recorded; `config/datasets.yaml` filled; the coverage result recorded in `docs/HANDOFF.md` |
| 1.2 `infra/bootstrap.sh` (**after the owner approves the project ID**): enable the pre-approved APIs (`docs/COSTS.md` §1a); buckets with lifecycle rules; BigQuery datasets in asia-south1; Firestore `(default)` in asia-south1; service accounts with least privilege; the budget (`docs/COSTS.md` §2); quotas; `infra/seed_users.py` (demo accounts on a placeholder domain, plus the anonymous demo-officer claim flow) | Idempotent; resources listed in `docs/HANDOFF.md`; budget visible in the console |
| 1.4b Once the owner has approved 1.2 and completed Earth Engine registration: Earth Engine exports clipped to the area of interest (HAND `hnd`, Open Buildings centroid CSV, Sentinel-1 pre/post for Montha). The DEM, WorldPop and JRC exports only replace the 1.4a downloads if they arrive before C1. Then `gsutil rsync data/raw gs://<data-bucket>/raw` | Exports in Cloud Storage with checksums; the register is updated |

## Phase 2: Engine (28 Sep evening to 29 Sep evening)

| Task | Acceptance criteria |
| --- | --- |
| 2.3 `build_graph` for the AP demo district (SPEC §3), then the rest of AP, then Odisha. Build each district graph from the district polygon buffered by 30 km (PRIOR), including roads, facilities and targets inside the buffer, and publish results only for nodes inside the district. The area of interest likewise extends 30 km inland for targets | Meets SPEC M3 |
| 2.1 Tracks: member 0 (hand-entered, then the Bulletin Reader); ECMWF IFS ENS and Weather Lab filtered by the 300 km rule; hourly interpolation; alignment | Unit tests pass; `tracks` rows written; the ensemble plot looks sane against the IMD track |
| 2.2 Wind (ENGINE §3) | The ENGINE §3 surface-intensity unit tests pass within 2% |
| 2.4 Surge screen, slice rain rule, edge closures (ENGINE §4–6) | An `edge_closure` table; a plausible closure map on the landfall coast |
| 2.5 Reachability, aggregation, critical edges (ENGINE §7) | Meets SPEC M4 |
| 2.7-min Publish district JSON, tiles (`--no-tile-compression`) and the recompute bundle for the landfall district | Valid against `district_scenario`; ≤ 5 MB at default zoom; a tile decodes in the smoke test |
| 2.6 Power (slice decision) and health, plus rule-based actions (ENGINE §8–9) | Meets SPEC M5 and M6; actions carry deadlines with their basis |
| 2.7 Publish all the districts built | Manifest with checksums and the code SHA |

## Phase 3: Core AI (29 Sep to 30 Sep morning)

| Task | Acceptance criteria |
| --- | --- |
| 3.1 Bulletin Reader with checks and cache; confirm model availability on Agent Platform first | Correct on the demo bulletin; accuracy on ≥ 5 **human-confirmed** labels |
| 3.2 Advisory Writer: placeholders, checks, back-translation, CAP (all the rules in `docs/AI_AGENTS.md` §5), TTS via Cloud Text-to-Speech Gemini-TTS or owner-approved pre-rendered audio | 100% placeholder and number checks; CAP valid and rule checks pass; Telugu audio plays |
| 3.3 Field Verifier and routing; one end-to-end report; in-API recompute; Firestore deltas | The staged photo produces an observation; after officer confirmation the bridge reopens and the PHC updates on two browsers within 10 s |

## Phase 4: Product UX (29 Sep to 30 Sep afternoon)

| Task | Acceptance criteria |
| --- | --- |
| 4.1 Static web scaffold (`output: 'export'`, `generateStaticParams`); Firebase Auth (email/password on a placeholder domain, plus anonymous for the demo officer); App Check registered in **monitor-only** mode, enforced in 4.3 once the owner approves `recaptchaenterprise`; Maps with a vector Map ID; deck.gl MVT layers; `firebase.json` headers | Loads signed out in judge mode; Maps key restricted |
| 4.2 Landing page and command map (SPEC §4) | Meets SPEC M9 |
| 4.3 Approval flow for the sandbox demo officer (`montha_2025_demo`); FCM web push; CAP download; `make sandbox-reset` (nightly Cloud Scheduler job) | Approve writes the audit record under the sandbox, sends the push and serves the CAP; the public replay is unchanged; the reset restores the sandbox |
| 4.4 Proof page | Renders the `make validate` outputs, or the "pending Earth Engine" limitation |
| 4.5 About page | Attribution block, licence register, synthetic-data policy, disclaimer |

## Phase 6: Testing and validation (30 Sep)

| Task | Acceptance criteria |
| --- | --- |
| 6.1 Sentinel-1 validation and baselines (ENGINE §10) | `road_skill` rows; districts not observed are listed |
| 6.2 Surge table | On the proof page |
| 6.3 Playwright smoke test (judge path); determinism (two runs, identical checksums); Firestore rules emulator tests; spend check | All pass; spend recorded in `docs/HANDOFF.md` |

## Phase 7: Demo (30 Sep, 18:00–21:00)

- Code freeze at 18:00. Tag `submission-2026-09-30`.
- Claude writes a click-path script with timings from `docs/DEMO_AND_SUBMISSION.md`. **The owner** records the screen capture and voice-over on the deterministic replay.
- Fill every bracketed number from the run. Show only what exists.

## Phase 8: Submission (30 Sep, 21:00–22:00)

- Claude prepares `docs/SUBMISSION_FIELDS.md`: the description, links, the track-to-feature table and a deck outline as text.
- The owner exports the deck, uploads the video, and submits on Hack2Skill.
- A warm Cloud Run instance runs 1–23 Oct (1 vCPU / 2 GiB, about US$15, budgeted in `docs/COSTS.md`).
- Check the deployed link from a clean browser on two networks.

## If blocked

| Blocker | Fallback |
| --- | --- |
| Weather Lab lacks Montha | ECMWF members only; say so |
| Neither ECMWF nor Weather Lab has Montha | Deterministic mode: IMD member 0 only, with the "deterministic" badge, no probabilities or windows, stated on the proof page. **Never synthesise members** |
| Some Montha bulletins missing | Use the bulletins that exist. If no bulletin with a landfall forecast was issued at or before `replay_start_utc`, use the first later one that has one (SPEC §3); member 0 may be hand-entered from it. **Never use the best track or IBTrACS as member 0.** If one has to stand in, label the run "hindsight (perfect-track)" and keep it out of skill scores |
| Earth Engine still pending at 29 Sep 00:00 | DEM, WorldPop and JRC water already come from the 1.4a direct downloads. HAND comes from MERIT Hydro tiles the owner downloads. Skip IMERG. **Move Sentinel-1 validation to Demo Day**; the proof page shows the surge table, bulletin accuracy and "Sentinel-1 scoring pending Earth Engine access" |
| TTS model not available on Agent Platform | Cloud Text-to-Speech Gemini-TTS; or owner-approved pre-rendered audio (`docs/AI_AGENTS.md` §1) |
| Gemini 3.7 Flash not on Agent Platform | `gemini-3.8-flash`, then ask the owner |
| OSM gaps | Completeness badge; never invent facilities |

## Demo Day backlog (1–22 Oct, on a branch and a separate Hosting site; ship each item behind a flag)

| Priority | Item | Acceptance criteria |
| --- | --- | --- |
| P1 | VIIRS power validation; local-outage curve (S6) | Leave-one-storm-out AUC for at least 3 storms |
| P2 | Calibrate drainage flooding on Fani, Michaung or Dana; re-score Montha out of sample | Before and after published |
| P3 | Full field loop: officer queue, duplicates, Eventarc, recompute job | Adversarial tests routed to the officer |
| P4 | OR-Tools shelter assignment and staging (S2) | ≤ 30 s per district; shortfall shown |
| P5 | SMS and IVR delivery via a provider trial (S3); FCM web push already ships in the slice | Telugu SMS and voice reach a test phone |
| P6 | Ask AURORA (S4) | 10/10 with citations and placeholders |
| P7 | BOB 06 inland replay with Flood Hub (S5) | Inland Uttar Pradesh districts shown |
| P8 | Tamil Nadu, West Bengal and Gujarat; one-click new storm (S7) | ≤ 10 minutes |
| P9 | k6 load test at 10,000 virtual users | Report committed; p95 under 500 ms |
| P10 | Remal replay (BRICS story) | Configuration only |
| P11 | Archiver and live shadow mode | Any new IMD depression triggers a run. **Only SHA-256 hashes** of forecast artefacts are committed publicly before landfall; the artefacts stay private to officer and analyst roles and are published after landfall for verification |
| P12 | Full evaluation sets (30 bulletins, 60+10 images) | `docs/eval-results.md` |
| P13 | Bengali and Tamil advisories | Checks pass |
| P14 | Deck and video v2 | Rehearsed with the failure drills |
