# AURORA Lifeline: project instructions for Claude Code

## What we are building

AURORA Lifeline is our entry for **Track 05 (Track-Based Cyclone Impact & Infrastructure Vulnerability Forecaster)** of the hackathon _Build with AI: Code for Communities, Second Edition_ (Hack2Skill, Google Cloud and GDG India).

It takes an official IMD cyclone forecast and turns it into what a district control room must act on before landfall:

- which hospitals, PHCs, shelters and settlements will be cut off by road, how likely that is and in what time window;
- who loses power;
- what to move where before the roads close.

It also verifies field reports after landfall and scores every forecast against satellite radar.

The one-line pitch: _"IMD tells you the storm. Web-DCRA tells you the district's risk. AURORA Lifeline tells you which PHC is cut off, how likely, when, and what to move there now."_

The current status of Web-DCRA is unverified (`docs/research/verify-policy.md` P1). In the deck, describe it as "district-level composite risk, as documented up to 2023".

## Deadlines (IST)

| Date            | What happens                                                                                        |
| --------------- | --------------------------------------------------------------------------------------------------- |
| 29 Sep, 23:00   | **Gate G1:** the Montha run works end to end (see `docs/BUILD_PLAN.md`)                             |
| **30 Sep 2026** | Code freeze at 18:00. Record the video 18:00–21:00. **Submit by 22:00.** Submission closes at 23:59 |
| 1–15 Oct        | Evaluation. The submitted tag and deployed link stay frozen                                         |
| 16 Oct          | Top 20 shortlist                                                                                    |
| 23 Oct          | Virtual Demo Day. The Demo Day build continues on a branch and a separate Hosting site              |

## Read these before writing code

1. `docs/HANDOFF.md`: current status, decisions made and why, owner actions, open questions.
2. `docs/SPEC.md`: product spec, replay definition, screens and acceptance criteria.
3. `docs/ARCHITECTURE.md`: components, contract schemas, data model, API, deployment, scaling.
4. `docs/ENGINE.md`: hazard, network and validation algorithms, with parameters and sources.
5. `docs/AI_AGENTS.md`: Gemini agents, prompts, schemas, tools, CAP rules, evaluation, SDK usage.
6. `docs/DATA.md`: every dataset with its ID, licence, attribution and processing steps.
7. `docs/BUILD_PLAN.md`: critical path, solo-mode checkpoints, cut order, acceptance criteria, gates.
8. `docs/COSTS.md`: the US$150 budget, pre-approved APIs, cost controls, what needs owner approval.
9. `docs/DEMO_AND_SUBMISSION.md`: demo script, fallbacks, submission checklist.
10. `docs/BLUEPRINT.md`: the full research and product blueprint (background and evidence).
11. `docs/research/`: raw research reports and fact-checks.

**Precedence when files disagree:** `CLAUDE.md` > `docs/SPEC`, `ARCHITECTURE`, `ENGINE`, `AI_AGENTS`, `DATA`, `BUILD_PLAN`, `COSTS`, `DEMO_AND_SUBMISSION` > `docs/BLUEPRINT.md` > `docs/research/`.

`docs/BLUEPRINT.md` is superseded on these points, which the files above correct:

- rustworkx or NetworkX, not igraph;
- Firebase Hosting's built-in CDN, not a Cloud CDN load balancer;
- a US$150 budget, not a US$300 credit;
- slice versus Demo Day scope;
- rain-flood thresholds are PRIOR in the slice, not calibrated on Montha.

## Non-negotiables

1. **Gemini never produces an AURORA number** that reaches a user: no probability, count, time or depth.
   - Numbers come from the deterministic engine. They are inserted through `{{fact_id}}` placeholders, and a post-check rejects any digit outside a placeholder.
   - Extraction agents (Bulletin Reader, Sitrep Extractor) may copy numbers from official documents into schema fields, but only with a verbatim source quote and deterministic checks. Such values are shown attributed to their source ("IMD bulletin No. n states…"), never as AURORA estimates.
2. **IMD is the authority.** The official IMD bulletin is the default forecast input. ECMWF and WeatherNext ensembles are a labelled, non-official uncertainty envelope. INCOIS products are linked, not ingested. Every output carries a provenance stamp: IMD bulletin number, ensemble run, data versions, model version.
3. **Humans approve.**
   - No advisory is dispatched without officer approval.
   - Field reports below the confidence threshold, and **every bridge reopening**, need officer confirmation.
   - The tool never issues public alerts. CAP output is for the SDMA's authorised originator to publish through Sachet. Demo CAP messages use `status=Exercise` and `scope=Restricted`, with a `<restriction>` element.
   - No asset-level forecast for a live storm is made public. Public viewers see asset-level results only for archived past-storm replays.
4. **Label synthetic data.** Field reports, unknown shelter capacities, resource inventories and officer accounts are simulated. Anything simulated shows a visible "SIMULATED" badge and never enters skill scores.
5. **Never invent metrics.**
   - Publish validation results with misses.
   - Show uncertainty as a probability plus a P10–P90 window, never a single hour. Action deadlines state their basis, for example "by 14:00 IST (P10 closure − 6 h)".
   - The one exception is deterministic mode (no ensemble members; SPEC §3). Times come from the IMD track alone, carry the "deterministic: IMD track only" badge and no probability, and deadlines state "IMD-track closure − 6 h".
   - Uncalibrated parameters are labelled "prior".
   - Never use hindsight data (best tracks, IBTrACS) as a forecast input in a scored replay.
6. **No personal data in the repo or any report.**
   - Do not record names, emails or phone numbers of private people: officials, field reporters, or team names and handles of solo or private competitors.
   - Published author citations (for example "Holland 1980") and project names are fine.
   - Field media is minimised at upload: strip metadata after reading place and time, blur faces and number plates, hash phone numbers.
   - Simulated accounts use a placeholder domain (for example `example.org`), never real inboxes.
7. **No secrets in the repo.**
   - Use Secret Manager and `.env` files (git-ignored).
   - Browser keys are restricted by HTTP referrer and API.
   - Enable secret scanning in CI.
8. **Cost gate.**
   - The budget is **US$150** (`docs/COSTS.md`). APIs on the pre-approved list in `docs/COSTS.md` §1a may be enabled.
   - Anything else needs a yes from the owner in chat: new services, quota increases, min-instances outside the approved window, a "large job" (defined in `docs/COSTS.md`), any single new cost over US$10, or a projected total over US$120.
9. **Licensing.** The repo is Apache-2.0.
   - No GPL or AGPL runtime dependencies. python-igraph, CLIMADA, SFINCS, TCRM and osmium-tool are all GPL.
   - Use rustworkx (Apache-2.0), NetworkX (BSD), scipy, numba (BSD), pyosmium (BSD-2) or our own code.
   - GPL or AGPL command-line tools may be used only as separate build-time or test-time processes: never imported, vendored or shipped in an image, and always cited. For example osmium-tool, and k6 for load tests.
   - Do not use SHRUG (not even for offline validation), FABDEM or Bhuvan content.
   - Do not use OSDMA's shelter list in any form without written permission.
   - Cite every reused open-source component in the README.
10. **Do not copy code from other hackathon entries**, including ShadowCast and PRAVAAH, even if their licence allows it.
11. **Maps and boundaries.** Use the Google Maps basemap. Never render OpenStreetMap or Overture national or international boundaries. Credit OSM ("© OpenStreetMap contributors") and every other dataset on the About page and in the README.

## Stack

| Layer                | Choice                                                                                                                                                                                                                                                                                                                                                               |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Web                  | Next.js (App Router) with `output: 'export'`: static only, no SSR, no framework-aware Firebase deploy. TypeScript strict; `@vis.gl/react-google-maps` + deck.gl (`GoogleMapsOverlay`, interleaved with a vector Map ID); Firebase JS SDK (Auth, Firestore, Messaging, App Check); Tailwind CSS. Hosted on Firebase Hosting                                           |
| API                  | Python 3.12 + FastAPI on Cloud Run (asia-south1). In the slice it also holds the in-memory recompute for the demo district                                                                                                                                                                                                                                           |
| Engine and pipelines | Python 3.12 package `aurora_engine`, run as Cloud Run jobs. Libraries: numpy, pandas, geopandas, shapely 2, rasterio, xarray, h3 (Apache-2.0), pyrosm and osmnx (MIT), pyosmium (BSD-2), rustworkx or networkx, numba, ortools, eccodes + pdbufr (Apache-2.0, for ECMWF BUFR tracks), earthengine-api, google-cloud-bigquery, google-cloud-storage, pdfplumber (MIT) |
| AI                   | `google-genai>=2.25,<3.0.0` against Gemini Enterprise Agent Platform (`enterprise=True`; `vertexai=True` is the legacy alias); `google-adk` (Apache-2.0) for Ask AURORA (Demo Day)                                                                                                                                                                                   |
| Data                 | BigQuery (`aurora_ref`, `aurora_runs`, `aurora_eval`); Cloud Storage (raw data, run outputs, quarantine); Firestore `(default)` (live state)                                                                                                                                                                                                                         |
| Tiles                | One tippecanoe run per layer (edges, settlements, facilities, surge, flood, tracks): `tippecanoe -e tiles/<run_id>/<layer> -l <layer> --no-tile-compression`. The static `z/x/y.pbf` directories match `district_scenario.tiles.url_template` and are served from Firebase Hosting. Headers are set in `firebase.json`                                               |
| Tooling              | uv (Python), pnpm (Node), ruff + mypy, eslint + prettier, pytest, vitest, Playwright (one smoke test), k6 (load test), datamodel-code-generator and json-schema-to-typescript (codegen), GitHub Actions                                                                                                                                                              |

## Repo layout (target)

```
aurora-lifeline/
  CLAUDE.md  README.md  LICENSE  Makefile  .env.example  firebase.json
  docs/                  # this handoff; keep it current
  schemas/               # JSON Schemas, the source of truth, including schemas/cap/ with the vendored CAP 1.2 XSD
  engine/aurora_engine/  # tracks, wind, surge, flood, graph, reach, power, health, actions, optimise, validate, cap
  pipelines/             # Cloud Run job entrypoints: ee_exports, build_graph, storm_run, backtest, archiver (DD), recompute (DD)
  agents/                # bulletin_reader, field_verifier, advisory_writer, sitrep_extractor, ask_aurora (DD)
  services/api/          # FastAPI app (also the slice's in-memory recompute)
  apps/web/              # Next.js PWA
  config/states/         # odisha.yaml, andhra_pradesh.yaml, <state>_districts.csv (lgd_code, name, osm_relation_id, name_variants, imd_subdivision)
  config/storms/         # montha_2025.yaml (replay definition), montha_2025_demo.yaml (demo-officer sandbox)
  config/aoi/            # <state>.geojson (coastal buffer ∩ state)
  config/datasets.yaml   # dataset register (generates data/REGISTER.md)
  config/fragility.yaml  # fragility and PRIOR parameters, with status and citations
  infra/                 # bootstrap.sh, seed_users.py, firestore.rules, storage.rules, budgets
  tests/  loadtest/
  data/                  # git-ignored local cache
```

(DD = Demo Day.)

## Commands (create these Make targets early)

- `make setup`: install Python and Node dependencies and pre-commit hooks. Check for system tools and fail with a clear message if any is missing: uv, pnpm, Node 22+, tippecanoe, Java 21+ (for the Firebase emulators), the Google Cloud SDK and gitleaks; optionally osmium-tool. GDAL and ecCodes come bundled in the rasterio/pyogrio and eccodeslib wheels, and firebase-tools is a pinned dev dependency; `make setup` verifies them after install, and warns if Playwright browsers are missing. On macOS: `brew install tippecanoe gitleaks openjdk@21` (plus `osmium-tool` if wanted).
- `make schemas`: generate Pydantic v2 and TypeScript types from `schemas/`.
- `make test`: run ruff, mypy, pytest, eslint, vitest and the Firestore rules tests.
- `make graph STATE=andhra_pradesh`: build the lifeline graph for a state.
- `make replay STORM=montha_2025`: run the full storm pipeline for the replay run.
- `make tiles STORM=montha_2025`: build the MVT tiles and scenario JSON.
- `make validate STORM=montha_2025`: Sentinel-1 road skill, baselines and the surge table, written to `aurora_eval` and the proof-page JSON.
- `make eval`: run the agent evaluation sets and write `docs/eval-results.md`.
- `make publish RUN=<run_id>`: load local outputs into BigQuery, Cloud Storage and Firestore once the Cloud project exists.
- `make sandbox-reset`: reset the demo-officer sandbox storm (SPEC §2).
- `make web`, `make deploy-api`, `make deploy-web`, `make deploy-jobs`.

## How to work

- **Verify Google APIs before using them.** Model IDs, SDK parameter names, Agent Platform availability and prices change monthly in 2026. Check the official docs first and record what you checked in `docs/HANDOFF.md`.
- **Time-box literature checks.** Give any "CONFIRM" parameter 20 minutes. If it is still unresolved, keep the stated value, mark it "PRIOR (unconfirmed)" in the run manifest, and move on.
- **Build the vertical slice first:** one storm (Montha 2025), Andhra Pradesh's landfall district first, end to end. Breadth comes later.
- **Keep the judge replay deterministic.** Pin data versions and cache every Gemini output for demo storms, keyed by input hash.
- **Commit small and often.** Conventional commits. Keep `main` deployable.
- **At the end of every session,** update `docs/HANDOFF.md` with what changed, what is next, new decisions and any cuts.

## Known gotchas (as of 28 Sep 2026)

- **Gemini access.** Use Agent Platform, not AI Studio: AI Studio's Tier 1 caps spend at US$10 per 10 minutes, and free-tier data may be used by Google.
  - `genai.Client(enterprise=True, project=..., location="global")`, or set `GOOGLE_GENAI_USE_ENTERPRISE=true`.
  - Model IDs and prices were verified on ai.google.dev. **Availability on Agent Platform is unverified**, so check before Phase 3.
- **Gemini parameters.**
  - Thinking goes in `thinking_config=types.ThinkingConfig(thinking_level="low"|"medium")`. `"minimal"` is rejected on 3.7 Flash, and `thinking_budget` must not be used on 3.x.
  - `max_output_tokens` includes thinking tokens, so set a generous ceiling (16,384).
  - `temperature`, `top_p` and `top_k` are deprecated; do not set them.
  - Automatic caching only applies to prompts of 4,096 tokens or more. Maps grounding works in English only.
- **Speech.**
  - Chirp 3 speech-to-text is generally available only for Hindi and runs only in the US and EU. Send audio to Gemini directly instead.
  - `gemini-3.8-flash-lite-tts` is on the Gemini Developer API and AI Studio only; Gemini Enterprise support is "coming soon" as of 23 Sep 2026. On Google Cloud, use Cloud Text-to-Speech Gemini-TTS (`gemini-2.5-flash-tts`: te-IN and hi-IN GA, or-IN Preview).
  - Pre-rendering demo audio with a Developer API key needs the owner's approval (`docs/AI_AGENTS.md` §1).
- **Vertex AI Vision** shuts down on 30 Sep 2026. Do not use it.
- **Earth Engine.**
  - Batch-export only; never put it in the request path (40 concurrent interactive requests per project).
  - Noncommercial Community tier: 150 EECU-hours a month.
  - Noncommercial eligibility for this project is **unverified** (`docs/COSTS.md`). Government operational use needs a commercial licence.
  - `COPERNICUS/DEM/GLO30_2024_1` is an ImageCollection: mosaic it and export with an explicit `crs` and `scale`.
- **Maps Routes API** cannot avoid arbitrary closed roads. All access analysis runs on our own OSM graph.
- **Data coverage and history.**
  - IMERG `precipitation` is mm/hr at 30-minute cadence (accumulation = 0.5 × sum). Montha falls after the end of Final-run IMERG V07, so only provisional data exists.
  - The IBTrACS copy in Earth Engine ends in 2024; download IBTrACS from NOAA.
  - `bigquery-public-data.geo_openstreetmap` is stale (2021); use Geofabrik (Odisha is in `eastern-zone`, Andhra Pradesh in `southern-zone`, both verified).
  - ECMWF as-issued history is on `gs://ecmwf-open-data` from 12 Jul 2023 (current layout from 29 Feb 2024). Fetch tropical-cyclone tracks with `step=240` (00/12 UTC runs) or `step=144` (06/18 UTC runs), using IFS ENS for Oct 2025.
  - **Montha coverage in Weather Lab and in the ECMWF mirror is UNVERIFIED.** Check it first (`docs/BUILD_PLAN.md` 1.4a).
- **CAP 1.2** timestamps must be `YYYY-MM-DDThh:mm:ss±hh:mm`: no `Z` and no fractional seconds. Polygons are `lat,lon` pairs, latitude first.
- **Firestore:** named databases get no free quota; use `(default)`.
- **Map Tiles API:** 15,000 requests a day. Use the Maps JavaScript API basemap, not raw tiles.
