# Handoff: AURORA Lifeline

Last updated 29 Sep 2026. Update this file at the end of every working session.

## Status

| Area | State |
| --- | --- |
| Research (hackathon rules, tracks, rubric, competitors, Google stack, costs, data licences) | Done. Evidence is in `docs/BLUEPRINT.md` and `docs/research/` |
| Idea selection | Done. Track 05, AURORA Lifeline, chosen unanimously by a four-judge panel (4.33 of 5) |
| Spec, architecture, algorithms, agent specs, data bundle, build plan, costs, demo plan | Done (this handoff). Reviewed by three independent agents on 28 Sep, with all findings applied |
| Cost approval | Owner approved a **US$150** budget on their Google Cloud account on 28 Sep. The owner has also offered to fund extra costs if needed; the per-item approval rules in `docs/COSTS.md` still apply |
| Code | **Gate G1 met on 28 Sep 23:55 IST** (a day early): bulletin (hand-entered member 0) -> 1,063 aligned members -> surge + rain hazards -> closures -> isolation -> schema-valid district JSON for 6 districts + run manifest (`make replay`, run `montha_2025_b21`). Phases 1-2 core done: tracks, Holland wind, own HAND, IMD-coverage rain rule, surge screen, closures, bottleneck isolation, publish. Next: b19 run, tiles (2.7), web command map (4.x), Gemini agents (3.x), power/health (2.6), Sentinel-1 validation (6.1) |
| Google Cloud project, billing link, APIs | Done 29 Sep: project `aurora-lifeline` (billing linked, budget set by the owner); pre-approved APIs enabled; Firestore `(default)`, buckets `aurora-lifeline-data` and `aurora-lifeline-quarantine` (90-day delete) in asia-south1; service accounts `aurora-api` and `aurora-jobs`. Cloud steps run from the scripts in `infra/cloudshell/` |
| Access requests (WeatherNext, Flood Hub, Earth Engine) | Not submitted yet (owner actions below) |

**Next step:** 1.3 schemas and codegen; IMD Montha bulletins and the demo-bulletin rule (SPEC §3); then 2.1 tracks. **Scope changed on 28 Sep (D14): the full project, including the former Demo Day features, ships by 30 Sep.**

## Verified during review (28 Sep 2026)

| Item | Verified |
| --- | --- |
| google-genai | `Client()` reads the project and location env vars; `GenerateContentConfig` has `response_mime_type`, `response_schema`, `system_instruction`, `max_output_tokens`, `speech_config` and `response_modalities`; `thinking_level` sits inside `ThinkingConfig` for 3.x; temperature and top_p/top_k deprecated on 21 Jul 2026 |
| Other components | google-adk is Apache-2.0. ECMWF `stream=enfo`, `type=tf` and `source="google"` work, CC BY 4.0. Geofabrik: Odisha is in `eastern-zone`, Andhra Pradesh in `southern-zone`. All Earth Engine IDs used exist, including `NASA/VIIRS/002/VNP46A2`. CAP 1.2 status and scope values and the XSD URL are correct |
| IMD definitions | Rainfall categories: heavy 64.5–115.5, very heavy 115.6–204.4, extremely heavy >204.5 mm per 24 h. MSW is a 3-minute mean at 10 m |
| Hosting, licences, formulas | Firebase Hosting returns 206 for single byte ranges. Licences as stated in `CLAUDE.md`. Holland (1980) formulas correct. The 0.3 m passability citation is correct |
| Toolchain (28 Sep, build session 1) | google-genai 2.25.0: `Client(enterprise=..., vertexai=..., project=..., location=...)` exists; `ThinkingConfig.thinking_level` exists (`thinking_budget` also still exists in the SDK: do not use it on 3.x); `GenerateContentConfig` has `response_json_schema` as well as `response_schema`. GDAL 3.12.4 via rasterio/pyogrio wheels; ecCodes 2.49.0 via the `eccodeslib` wheel, which must be a direct dependency (uv's lock drops the transitive one). Next.js 16.3.6; TypeScript pinned to 6.x (typescript-eslint rejects TS 7.0); ESLint pinned to 9.x (eslint-plugin-react breaks on ESLint 10); firebase-tools 15.31.0 as a dev dependency |
| Agent Platform and Earth Engine (29 Sep, 00:40 IST, Cloud Shell, `infra/cloudshell/01_bootstrap.sh`) | google-genai 2.25.0 with `Client(enterprise=True, project="aurora-lifeline", location="global")`: `gemini-3.7-flash`, `gemini-3.8-flash` and `gemini-3.5-flash-lite` all answer; `gemini-embedding-2` answers with **3,072 dimensions by default** (not 768; code requests 768 with `output_dimensionality`). Earth Engine `ee.Initialize(project="aurora-lifeline")` works; `COPERNICUS/DEM/GLO30_2024_1` lists 26,475 images. google-adk latest on PyPI is 2.10.0 (Python >= 3.10) |
| google-adk 2.10.0 (29 Sep) | `google/adk/utils/env_utils.py` reads `GOOGLE_GENAI_USE_ENTERPRISE` (and the deprecated `GOOGLE_GENAI_USE_VERTEXAI`), so ADK agents run on Agent Platform with the same environment as our client. `LlmAgent` has `after_model_callback(callback_context, llm_response)`; tools receive `tool_context` with session `state`; `RunConfig(max_llm_calls=...)` caps model calls per question |
| Not yet verified | Earth Engine noncommercial eligibility. Weather Lab publication delay per model (needed for the "available at bulletin issue time" rule). Live API model availability on Agent Platform |

## C0: Montha ensemble coverage (checked 28 Sep 2026, 18:10–18:20 IST)

**Result: ensemble mode is available from both sources.** Use description version A (`docs/DEMO_AND_SUBMISSION.md` §6).

| Source | What exists for Montha | How it was checked |
| --- | --- | --- |
| ECMWF IFS ENS, `gs://ecmwf-open-data` | `enfo`/`tf` BUFR present for every 00z and 12z run on 24–28 Oct 2025 (HTTP 200, 0.64–0.75 MB each). Montha is **`03B`, 52 track subsets**, from the 27 Oct 00z run. Before that (24–26 Oct) ECMWF tracks the pre-genesis disturbance under provisional IDs (`70B`–`76B`, not stable across runs; e.g. `71B` with 46, 33 and 29 members on 24, 25 and 26 Oct 00z). Match these to IMD positions with the 300 km rule, never by ID | eccodes 2.x wheel; one BUFR message per storm, members as subsets |
| Weather Lab (Google DeepMind), public download endpoint `https://deepmind.google.com/science/weatherlab/download/cyclones/<MODEL>/<ensemble\|ensemble_mean>/paired/csv/<MODEL>_YYYY_MM_DDTHH_00_paired.csv` (no sign-in; the web UI itself now asks for a Google sign-in) | Montha is **`IO942025`**. 26 Oct 00z: **FNV3P2 50 members**; **FNV3_LARGE_ENSEMBLE 1,000 members** (16.7 MB CSV). OPER had no Bay of Bengal track at that cycle. Columns include per-member `radius_of_maximum_winds_km`, 34/50/64 kt wind radii by quadrant, MSLP and MSW (kt). "Paired" means each forecast track carries the official storm ID; the files hold forecast rows only (lead 0 is the model analysis at init), so there is no hindsight to strip. Weather Lab only starts a track once the system has an ID: Montha first appears in the **25 Oct 18z** run (`IO942025`), and from 26 Oct 12z as `IO032025`; match by the 300 km rule, never by ID | curl + csv parse. URL pattern learned from the source of a community downloader (not used as a dependency) |
| Licence note | The CSV header says data relating to a time **more than 48 hours ago** is CC BY 4.0 (the guide says 1 hour). Montha data is ~11 months old, so CC BY 4.0 either way. Keep the "experimental; not produced with or endorsed by any government meteorological agency" label | File header |

## Replay selection (28 Sep 2026)

- **Observed landfall** (selection only, never a model input): IMD press release of 29 Oct 2025, "crossed the Andhra Pradesh & Yanam coasts between Machilipatnam and Kalingapatnam, to the south of Kakinada, close to Narsapur near latitude 16.35°N and longitude 81.70°E during same midnight (2330 hrs IST of 28th and 0030 hrs IST of 29th October 2025)". T_obs = 2025-10-28T18:30Z (window midpoint). `replay_start_utc` = 2025-10-25T18:30Z.
- **SPEC §3 rule result:** National Bulletin **No. 19** (issued 2130 IST 25 Oct = 16:00 UTC; landfall forecast "around Kakinada during evening/night of 28th October"). Member 0 is hand-entered in `config/storms/montha_2025/bulletins/national_19.reading.json` (21 verbatim quotes, checked by script) and matches the deterministic table parser exactly. **Needs human confirmation** (`tests/fixtures/bulletins/labels/montha_2025_national_19.json`, `labelled_by: draft`).
- **Ensemble availability at No. 19** (runs usable at issue time with PRIOR publication delays ECMWF 8 h, Weather Lab 6 h): ECMWF 06z 25 Oct, **49 members** match (pre-genesis tracks). **No Weather Lab members**: Weather Lab's first Montha run (18z 25 Oct) starts after No. 19 was issued.
- **First bulletin with every source:** National Bulletin **No. 21** (issued 04:15 UTC 26 Oct, 62 h before observed landfall): ECMWF 18z 25 Oct **51**, WNX FNV3 **38**, WNX large ensemble **979** members (1,068 in total).
- **D18 (decided by the owner, 28 Sep):** publish **two** runs, `montha_2025_b19` (the SPEC §3 run, ECMWF only) and `montha_2025_b21` (first bulletin with all sources), and let the slider step between bulletins. Judge mode opens on b21 ("1,068 futures"); the proof page scores both, so skill versus lead time is shown. The choice of b21 depends only on what was available at issue time, and was made before any skill was computed.
- Raw versus aligned (observation, not yet a claim): at 28 Oct 12Z the raw WeatherNext large ensemble median sits near 15.5°N versus IMD's 16.5°N; the storm crossed the coast further south than IMD forecast. The proof page will score raw and aligned tracks side by side. Nothing is tuned on Montha.

Open points from C0: pick the demo bulletin by the SPEC §3 rule once the IMD bulletins are downloaded; set a Weather Lab publication delay (PRIOR, conservative 6 h unless documented) and ECMWF's (dissemination schedule) in the manifest; decide how members are weighted across sources (1,000 WeatherNext vs 52 ECMWF).

## Hackathon facts that constrain the build

Verified from the official page and its data feed on 27 Sep 2026.

- **Submission package:**
  - a public or access-granted GitHub repo;
  - a 3–5 minute video;
  - a 10–12 slide deck;
  - a 2–3 line description;
  - a **live deployed link**.
- **Rules:**
  - Google AI integration is mandatory.
  - The product must be designed to scale across states.
  - Build during the hackathon; pre-existing projects are ineligible unless substantially extended; cite reused open-source code.
  - Design for BRICS applicability.
- **Judging weights:** AI/Technical Execution 25%, Problem-Solution Fit 20%, Depth & Reach Across India 20%, Deployability & Scalability 20%, Impact 15%.
- **Deadline:** 30 Sep 2026, 23:59 IST; registration closes at the same time. Top 20 shortlist on 16 Oct; Virtual Demo Day on 23 Oct.
- **After winning:** winners are "evaluated for pilot deployment within relevant ministries". No ministry is named.
- **Track 05** names Earth Engine, real-time meteorological data and Gemini 3.7 Flash. It asks for surge simulation, rainfall damage pathways, exposure of power grids, arterial roads and medical shelters, and automated advisory dispatch to municipal and disaster management authorities.

## Decisions (with reasons)

| # | Decision | Why |
| --- | --- | --- |
| D1 | Track 05 | The only candidate that fits its track clause for clause, runs on real open data and has a verified gap. Track 01 is the most crowded (~50 public repos); its best idea, a demand-by-deficit quadrant, is already live in a competitor (CIVOS); and a government voice-complaint system (Samadhan Didi) launched in May 2026 |
| D2 | Product = AURORA Lifeline, with the health-continuity view as the lead | No government system or competitor repo we found gives probabilistic, time-windowed isolation per facility and settlement, population without power, or radar-scored road predictions. "Medical shelters" is in the track text |
| D3 | Lead with what the strongest competitor lacks | ShadowCast has wind, surge, cut-off deadlines per site, a Gemini IMD-PDF reader, CAP with approval, and parametric triggers. We lead with network reachability windows (P10–P90); population without power; radar-scored roads; the post-landfall recompute; breadth. Capacity-aware shelter assignment, SMS/IVR delivery and the inland replay are Demo Day work |
| D4 | IMD as authority; ensembles as a labelled envelope | Credibility with SDMAs |
| D5 | Gemini reads, verifies, explains and writes; the engine produces all AURORA numbers | Avoids hallucinated numbers; placeholders plus a post-check enforce it |
| D6 | Precompute; serve static files from Firebase Hosting (no Cloud CDN load balancer) | Earth Engine concurrency limits; flat cost per viewer; a robust demo |
| D7 | Slice = one run (Montha 2025, one IMD bulletin), Andhra Pradesh landfall district first, then the rest of AP and Odisha if time allows; advisories in English and Telugu, with Hindi and Odia if checks pass | About 2.5 days to the deadline; the shortlist is judged on this build |
| D8 | Demo Day additions on a branch and a separate Hosting site | VIIRS power validation, OR-Tools optimiser, SMS/IVR delivery, Ask AURORA, BOB 06 inland with Flood Hub, more states, Remal replay, archiver with hash-committed shadow forecasts |
| D9 | Apache-2.0; no GPL runtime dependencies | Digital Public Good packaging and government procurement |
| D10 | Gemini via Agent Platform, `gemini-3.7-flash` as the main model | Named in the track; no AI Studio tier caps; billed to Google Cloud |
| D11 | Google Maps JavaScript API basemap with a vector Map ID | Familiar to officials; India pricing; avoids rendering boundaries ourselves |
| D12 | Parametric insurance is at most one indicative panel on Demo Day | Politically sensitive; already done by competitors |
| D13 | The team's earlier JanDrishti "Community Impact Graph" **concept** becomes the dependency engine, and its civic-reporting idea the field-truth loop | Keeps the best idea where it adds value. All code is written fresh during the hackathon. If any earlier code is reused, disclose and cite it under the originality rule |
| D14 | **Full scope by 30 Sep.** The former Demo Day features are pulled into the submission, in this order after G1: Ask AURORA (ADK + Gemini, voice), Dana 2024 (Odisha) as a second replay, the indicative anticipatory-action trigger panel, the OR-Tools shelter optimiser, the Sitrep Extractor as a second validation, the full field loop. No work is planned after 30 Sep, so no separate Demo Day site | Owner decision, 28 Sep. The Top 20 is picked **overall**, not per track, so the bar is every submission. G1 stays a hard gate: a working end-to-end run comes before any addition |
| D15 | Weather Lab `FNV3_LARGE_ENSEMBLE` (1,000 members) is the primary WeatherNext source, with FNV3 (50) and ECMWF ENS (52) alongside. Show per-source probabilities plus a source-balanced blend (each source weighted equally; PRIOR) | C0 found the 1,000-member ensemble. Equal weighting stops one source dominating by member count |
| D16 | Google AI first: use a Google product wherever it does load-bearing work (WeatherNext, Gemini, ADK, Gemini Live and TTS, Earth Engine incl. AlphaEarth embeddings, Open Buildings, Flood Hub, Gemini embeddings). Publish "Open in AI Studio" links for each agent prompt on public data; the app's own calls stay on Agent Platform. No decorative uses | Owner direction, 28 Sep; the 25% criterion asks whether Google AI does meaningful work |
| D17 | Toolchain: GDAL and ecCodes from wheels rather than Homebrew; gitleaks for secret scanning (pre-commit and CI); local, network-free pre-commit hooks; Cloud deploys from GitHub Actions via Workload Identity Federation | Smaller local footprint; no stored keys |
| D18 | Two Montha runs: `montha_2025_b19` (SPEC §3 rule; ECMWF only) and `montha_2025_b21` (first bulletin with every ensemble source; 1,068 members). Judge mode opens on b21; the proof page scores both | Weather Lab's first Montha run started after bulletin 19 was issued, so b19 cannot carry WeatherNext without hindsight. b21 was chosen on availability at issue time, before any skill was computed |
| D19 | "Cut off from any hospital" counts **public tiers only** (district hospital, SDH/area hospital, CHC, PHC), as SPEC §3 defines. OSM's 1,713 other `amenity=hospital` points in the landfall region are classed `hospital_other` and shown for context only | Many are small private clinics; counting them would overstate access |
| D20 | Demo district **Kakinada** (member 0's forecast coast crossing at 17.157°N 82.423°E for both b19 and b21). The first build covers the landfall region: Kakinada, Konaseema, East Godavari, West Godavari, Eluru and Krishna, plus 30 km | The storm actually crossed near Narsapur (West Godavari); a single-district build would miss where the impacts were |
| D21 | Population from **WorldPop 2020 constrained** (BSGM, 531 MB for India) instead of the unconstrained 1.84 GB file | data.worldpop.org ignores range requests and twice stalled mid-download of the large file. The constrained product places people only where buildings are mapped, which suits settlement detection; same provider and licence (CC BY 4.0) |
| D22 | **Rain rule amended once, then frozen (28 Sep, before any scoring).** (a) IMD's spatial-distribution terms set the share of a district that receives each category (IMD RSMC terminology: isolated < 25%, scattered/'a few places' 26-50%, fairly widespread/'many' 51-75%, widespread/'most' 76-100%; middle of range used), drawn per member and day on H3 res-6 patches with nested categories; this replaces "ignore isolated add-ons". (b) Roads sit above the ground by a formation allowance: 1.0 m motorway/trunk/primary, 0.6 m secondary/tertiary, 0.3 m other (PRIOR (unconfirmed), after Indian Roads Congress practice of raising formation above flood level); applied to rain and surge closures | The first 30-member dev run applied 'heavy to very heavy at a few places' to every road in the district and gave an implausible 7.6 M people (64%) cut off from any hospital and 117/134 PHCs cut from referral. After (a)+(b): median 2.0 M (P10-P90 1.2-3.1 M) and 22 PHCs. This used only IMD definitions and road-design practice, not Montha observations (none have been computed yet). Parameters are frozen from here; the proof page scores them as they are |
| D23 | **Deploys run from GitHub Actions with Workload Identity Federation** (29 Sep). After CI passes on `main`, `deploy.yml` builds the API image, deploys Cloud Run `aurora-api` (asia-south1, max 3 instances, public, behind Hosting at `/api`) and deploys Hosting. The provider accepts only `TusharTechs/aurora-lifeline` on `refs/heads/main`; the `aurora-deploy` account has Cloud Run admin, Hosting admin, registry writer on `aurora`, act-as on `aurora-api` and access to the `web-env` secret. Generated tiles and run JSON live on the single-commit `web-data` branch (`make web-data`) | No service-account keys anywhere; one owner action (`infra/cloudshell/03_github_deploy.sh`), then no manual deploy steps. Revoke: `gcloud iam workload-identity-pools delete github --location=global` |
| D24 | **Generated Pydantic contracts live in `aurora_agents.contracts`**; agents and API no longer depend on the engine | Keeps the API image free of the geospatial stack (fast cold starts). Nothing imported them from the engine |
| D25 | **Public demo cost guards**: per-IP limit (8 per minute), a daily cap of 300 uncached model runs (Firestore `usage/gemini-YYYY-MM-DD`), inputs of at most 500 characters, and response caching by input hash so the judge replay replays cached Gemini output | The API is public for judges; these bound Gemini spend well inside the US$40 allocation |
| D26 | **Facility deciles are unconditional; the P10-P90 window is conditional** (29 Sep). `iso_deciles`: decile k = first hour by which k/10 of all weighted futures cut the facility off (null if never), read by clients as P(t). `t10/t50/t90`: percentiles of the cut-off time among futures where it happens ("if it is cut off, most likely between") | The earlier conditional deciles made a PHC with a 36% chance by landfall display as at least 70% and over-coloured the map. Found in UI QA before any scoring |
| D27 | **Brand and single "Aurora Night" theme** (29 Sep). Mark: three aurora bands spiralling clockwise out of a calm core (a Northern Hemisphere cyclone's bands drawn as light). Sora/Inter plus Noto Telugu/Devanagari; semantic tokens in `globals.css`; accessibility menu (reduced motion, high contrast, larger text). Landing page tells the story with real run data only | Owner asked for a world-class, non-generic experience; the product brief's emergency-app personas were replaced by the real users (Collector/DDMA, DM&HO, R&B/PR engineers, SDMA CAP originator) |
| D28 | **Season watch reads IMD's national-bulletin archive** (29 Sep). A national bulletin based on observations in the last 36 h means IMD is tracking a system (IMD issues them only for a depression or stronger; the daily Tropical Weather Outlook is excluded). The site then links to reading IMD's latest bulletin with Gemini; it still publishes no asset-level results for a live storm | On 29 Sep IMD was issuing national bulletins (No. 04 based on 28 Sep 17:30 IST) |
| D29 | **Dana 2024 (Odisha) is the second replay** (29 Sep). Bulletin No. 1 (first national bulletin with a landfall forecast; none existed before T-72 h), member 0 read by the Gemini Bulletin Reader (table cross-check missed the +84 h row, so marked for confirmation). 97 futures (ECMWF 47, FNV3 50; FNV3 large ensemble has no Oct 2024 runs). No surge guidance in the bulletin, so rain flooding only. Region north_odisha: Kendrapara, Bhadrak, Balasore, Jagatsinghpur, Jajpur, Cuttack + 30 km | Owner chose Dana as the second replay (D14); the pipeline is now state-agnostic (config-driven) |
| D30 | **Surge overlay bug fixed** (29 Sep): overlays.json surge bounds were lat/lon swapped since G1, so the surge layer never showed. Runs now also publish their tile extent | Found in UI QA |

## Owner actions (only a human can do these)

**Today, 28 Sep:**

- [x] Confirm the team is **registered on Hack2Skill** for codeforcommunities2; registration closes with submission on 30 Sep at 23:59 IST. Confirm the team size is allowed: the page says 1–4 and the generic T&C say 2–6.
- [ ] Create a Google Cloud project, suggested ID `aurora-lifeline-<suffix>`, under the owner's **personal** Google account. Link the billing account that holds the US$150.
- [ ] Give Claude Code the project ID, the **billing account ID** and its **currency**, and say whether the US$150 is free-trial credit.
- [ ] Authenticate locally with `gcloud auth login --no-launch-browser` and `gcloud auth application-default login --no-launch-browser` (open the printed link, paste the code back). Fallback: a service-account JSON key kept outside the repo.
- [x] **Earth Engine** registered on 28 Sep 2026 for the `aurora-lifeline` Cloud project: organisation type Other, use case "Individual research or non-commercial use", Community tier, categories Adaptation plus Disaster and Crisis Response, Natural disasters/Climate risk, Freshwater, Public health, Transport infrastructure. The description disclosed the hackathon and possible prizes.
- [ ] Submit the **WeatherNext** data request form (free; 5–7 business days): https://developers.google.com/weathernext/guides/access-forecast
- [ ] Join the **Flood Hub API** waitlist (free): https://developers.google.com/flood-forecasting
- [ ] Create a **public GitHub repo** `aurora-lifeline` (empty; no README, .gitignore or licence) and add the repo-scoped SSH deploy key Claude generated, with write access. Send the GitHub username.
- [ ] **Firebase console:** add Firebase to the project and accept the terms. Enable Auth providers Email/Password and Anonymous. Generate the Web Push (VAPID) key pair under Project settings > Cloud Messaging and give Claude the public key (`NEXT_PUBLIC_FCM_VAPID_KEY`).
- [ ] **Google Maps Platform > Map Management:** create a JavaScript **vector** Map ID and give it to Claude (`NEXT_PUBLIC_MAPS_MAP_ID`).
- [ ] **LGD district lists:** at lgdirectory.gov.in > Download Directory, download the district lists for Andhra Pradesh and Odisha as CSV into `data/raw/lgd/<date>/`. The form has a CAPTCHA, so Claude cannot do this.
- [ ] **MERIT Hydro:** if Earth Engine registration is not complete by 28 Sep 20:00, register on the University of Tokyo MERIT Hydro site and download the `hnd` tiles covering 10–25°N, 75–90°E yourself into `data/raw/merit_hydro/v1.0.1/`. Access uses an emailed password, which Claude cannot enter.
- [ ] **healthsites.io** (optional): sign in with an OpenStreetMap account, create an API token, and put it in `.env` as `HEALTHSITES_TOKEN`. If it isn't there by 29 Sep 00:00, facilities come from OSM tags only.
- [ ] **Approve or decline `recaptchaenterprise`** (App Check for the web; free up to 10,000 assessments a month). Until you approve, App Check runs in monitor-only mode.
- [x] ~~Email the organisers~~ Not needed. Owner answers (28 Sep): no post-deadline work is planned; AI coding tools are allowed and will be declared in the submission; the Top 20 and prizes are overall, not per track. The original questions were:
  1. May the deployed link be updated after 30 Sep, or must Demo Day work use a separate link?
  2. Are prizes or shortlist places allocated per track?
  3. Does the generic Hack2Skill T&C apply (IP, right of first refusal, the "sole author" warranty given AI-assisted code)?

**By 30 Sep:**

- [ ] **12:00 IST:** supply one staged bridge or road photo for the field-report demo, with no faces or number plates. Or approve an openly licensed image that Claude proposes, with credit.
- [ ] **14:00 IST:** a native speaker reviews 5 Telugu (and, if shipped, 5 Odia) advisories. Otherwise they are labelled "machine-translated, not reviewed".
- [ ] **Throughout:** confirm the hand-labelled fields of at least 5 Montha IMD bulletins. Claude pre-fills drafts; a human confirms (`docs/AI_AGENTS.md` §9).
- [ ] **18:00–21:00 IST:** record the screen capture and voice-over from Claude's click-path script. Upload the video (unlisted) and export the deck to PDF.
- [ ] **21:00–22:00 IST:** submit on Hack2Skill using the fields Claude prepares in `docs/SUBMISSION_FIELDS.md`.

**Optional:**

- An IMD API account.
- An SMS/IVR provider trial (Demo Day).
- Written permission from OSDMA to use its shelter list.

## Data caveats found so far

- **District set.** OSM (27 Sep 2026) has 28 AP districts. Markapuram and Polavaram are marked `in_oct_2025_set = no` in `config/states/andhra_pradesh_districts.csv`; this is inferred (absent from IMD's Oct 2025 district lists; very recent Wikidata items), not confirmed against LGD.
- **Shelters.** OSM has only 28 shelters in the landfall region; Andhra Pradesh has many more cyclone shelters. The completeness badge must say so, and evacuation actions are limited to mapped shelters.
- **WorldPop** (data.worldpop.org) ignores HTTP range requests, so the 1.84 GB India raster is downloaded once, clipped to AP and Odisha, and deleted.

## Open questions

| Question | Default if no answer |
| --- | --- |
| Team roles | Solo mode (`docs/BUILD_PLAN.md`) unless teammates are named |
| Is the US$150 a credit or a balance? Is billing in India? | Budget alerts exclude credits (they track gross usage); cap Maps loads at 2,000 a day |
| Which Montha IMD bulletins are downloadable | Collect every bulletin from genesis to landfall; the replay uses the rule in SPEC §3 |
| Montha coverage in Weather Lab and in ECMWF | Check first. Fallbacks are in `docs/BUILD_PLAN.md` "If blocked" |
| PMNDP dialysis list downloadable? | Show dialysis as "not mapped" |
| PMTiles on Firebase Hosting? | Tested: 206 for single ranges, but ranges apply to compressed bytes when Hosting compresses. The default stays a static `z/x/y.pbf` directory |
| Can updates be deployed after submission? | Keep the submitted link frozen; Demo Day uses a separate Hosting site |

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Scope versus deadline | Solo-mode checkpoints C1–C5 and a cut order (`docs/BUILD_PLAN.md`). At Gate G1 (29 Sep 23:00), if the run isn't end to end, cut to hospitals, CHCs and PHCs only, skip power, one district, and still submit |
| No ensemble for Montha | IMD member 0 only, with a "deterministic" badge and no probabilities; stated on the proof page |
| Looking like a less polished ShadowCast | Open every artefact on isolation windows and people cut off |
| Scientific credibility | Surge labelled "screening"; PRIOR parameters labelled; completeness badges; misses published; no calibration on Montha |
| Live demo failure | Static replay; cached Gemini outputs; fallbacks in `docs/DEMO_AND_SUBMISSION.md` |
| Budget | Pre-approved API list, budget alerts on gross usage, spend caps with headroom, quotas (`docs/COSTS.md`) |
| Licences | Licence register; no NC or GPL runtime inputs; Earth Engine commercial path stated |

## Competitor notes (positioning only; do not copy code)

- **ShadowCast** (Track 05; solo; live; Apache-2.0). Holland wind; R-CLIPER rain; 1D surge setup; arterial-road cut deadlines per site (its README says no routing is attempted); a VIIRS-fitted substation outage model (published AUCs, with an Amphan failure); ECMWF ensembles replayed as issued; a Gemini IMD-PDF reader; CAP 1.2 in 3 languages with approval and audit; parametric triggers. East coast only. Its roadmap includes routing and shelter capacity.
- **PRAVAAH** (Track 05; live; Odisha only). Deterministic multi-source Dijkstra hospital reachability on H3 cells; it has no access ground truth.
- **Others** (AeroRelief AI, SAGAR-AI, AEGIS-Cyclone, Cyclone AI Command Center): flashier, with weaker validation.
- Detail: `docs/research/decision-panel.md` and `docs/research/hackathon-and-competitor-intel.md`.

## Session log

| Date | Who | What |
| --- | --- | --- |
| 27–28 Sep 2026 | Research session | Research, decision, blueprint, this handoff, three-agent review with fixes applied |
| 28 Sep 2026 | Research session | Second-pass review (61/70 earlier findings fully addressed, 9 partly). Those 9 and 5 new issues fixed: the replay selection rule, the demo-officer sandbox, the Holland V_mg test, no-sign-in rasters, owner actions for LGD, MERIT and healthsites, IMD area-to-district mapping, the surge fallback, catchments and referral tiers, per-layer tiles, local-first storage, a 30 km district buffer, App Check monitor-only, the warm-instance cost, Java 21 |
| 28 Sep 2026, 18:00– | Build session 1 | Hackathon page re-checked (unchanged). C0 done: Montha is in ECMWF ENS (`03B`, 52 tracks) and Weather Lab (`IO942025`, 50 FNV3 + 1,000 large-ensemble members). Repo initialised locally with the handoff docs; `pipelines/downloads/fetch_raw.sh` started (ECMWF tf, Weather Lab, IBTrACS NI, CAP XSD, Geofabrik southern-zone) |
| 28 Sep 2026, 19:00– | Build session 1 (cont.) | 1.1 scaffold and 1.3 schemas committed. IMD Montha archive downloaded (57 national + 58 RSMC bulletins, tracks, surge, rainfall, press releases). Replay rule applied (No. 19); member 0 hand-entered. Track module (ECMWF BUFR, Weather Lab CSV, 300 km matching, hourly interpolation, IMD alignment) with 10 tests. Found that Weather Lab is unavailable at No. 19; proposed D18 (two runs, b19 and b21) |
| 28 Sep 2026, 19:45 | Build session 1 (cont.) | D18 confirmed (two runs). Member 0 for b21 entered. Demo district Kakinada (D20). OSM extraction (pyosmium, C++ key filter: 2 min per zone). Graph for Kakinada, Konaseema, East/West Godavari, Eluru, Krishna + 30 km: 419,246 nodes, 542,133 edges, 7,901 bridges, 1,124 culverts, 119 fords; 205 PHCs, 35 CHCs, 25 hospitals, 121 sub-centres, 28 shelters, 189 substations. Bottleneck-reachability algorithm (numba) with the ENGINE §7 tests. WorldPop settlements pending the 1.84 GB download (the server ignores range requests) |
| 28 Sep 2026, 23:55 | Build session 1 (cont.) | Earth Engine registered (Community tier, to 28 Mar 2028). Firebase project, Auth (Email/Password + Anonymous with auto clean-up), Web Push key, vector Map ID done by the owner; values in git-ignored `.env`. WorldPop switched to the constrained product (D21). Own 90 m HAND (priority-flood). Rain rule amended once per IMD definitions and frozen (D22). Surge screen, closures, storm run (1,063 members in 83 s on 7 cores) and publish: **G1 met**. Kakinada P50 335k people cut off from any public hospital by landfall (P10-P90 125k-634k). Commits since `a8e7ceb` are local; pushing is the owner's call |
| 29 Sep 2026, 00:00– | Build session 2 | Pushed to GitHub; CI green. b19 run rebuilt and tiled; generated web data published as the single-commit `web-data` branch (`make web-data`), which CI and the Cloud Shell deploy unpack. Fixed NaN district ids in settlement tiles. Cloud Shell bootstrap: APIs, Firestore, buckets, service accounts; Gemini 3.7 Flash, 3.8 Flash, 3.5 Flash-Lite and embedding-2 verified on Agent Platform; Earth Engine verified |
| 29 Sep 2026, 01:00–08:00 | Build session 2 (cont.) | Hosting live (aurora-lifeline.web.app). Advisory Writer (placeholders, digit/number-word post-check in any script, one retry, Telugu/Hindi back-translation with gemini-embedding-2, CAP 1.2 Exercise/Restricted validated against the XSD). Ask AURORA on ADK (five read-only tools, facts recorded in session state, after-model number guard, table fallback). FastAPI on Cloud Run with cost guards; auto-deploy via WIF (D23). Action sites labelled from OSM places (Telugu names where mapped); CAP district outlines in `areas.json`. **Fixed a map bug**: binary MVT decoding read missing deciles as hour 0, so most roads showed about 90% at every time step; tiles now carry all nine deciles with a 999 sentinel. 103 Python and 7 web tests pass |
| 29 Sep 2026, 08:00– | Build session 2 (cont.) | Step 1 (reframe: "runs on every IMD bulletin", Montha as the proof), step 2 (Bulletin Reader live: Gemini reads the PDF, code checks schema, basin, speed, category, quotes verbatim against the text layer and the track against the deterministic table parser; known bulletins fetched from IMD and scored against hand labels) and step 3 (season watch, D28). UI transformation (D27): brand mark and assets, design tokens, landing page with the real ensemble as a canvas hero, four questions answered from the run, scroll-driven method, live Ask/draft demo, personas, guardrails with the placeholder view, Google AI roles; Bulletin reader and About pages; control room restyled with a bulletin 19/21 switch and legend. Fixes: ADK treated {{fact_id}} as a state template (callable instruction), ADK call limit now falls back to the facts table, 12-page bulletin limit raised to 40, facility deciles (D26) |
