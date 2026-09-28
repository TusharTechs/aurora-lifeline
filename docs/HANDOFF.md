# Handoff: AURORA Lifeline

Last updated 28 Sep 2026. Update this file at the end of every working session.

## Status

| Area | State |
| --- | --- |
| Research (hackathon rules, tracks, rubric, competitors, Google stack, costs, data licences) | Done. Evidence is in `docs/BLUEPRINT.md` and `docs/research/` |
| Idea selection | Done. Track 05, AURORA Lifeline, chosen unanimously by a four-judge panel (4.33 of 5) |
| Spec, architecture, algorithms, agent specs, data bundle, build plan, costs, demo plan | Done (this handoff). Reviewed by three independent agents on 28 Sep, with all findings applied |
| Cost approval | Owner approved a **US$150** budget on their Google Cloud account on 28 Sep. The owner has also offered to fund extra costs if needed; the per-item approval rules in `docs/COSTS.md` still apply |
| Code | **Not started** |
| Google Cloud project, billing link, APIs | Not created yet (owner actions below) |
| Access requests (WeatherNext, Flood Hub, Earth Engine) | Not submitted yet (owner actions below) |

**Next step:** Phase 1 in `docs/BUILD_PLAN.md`: scaffold, schemas, and the approval-free downloads (1.4a). Start with the 30-minute check of Montha coverage in Weather Lab and ECMWF.

## Verified during review (28 Sep 2026)

| Item | Verified |
| --- | --- |
| google-genai | `Client()` reads the project and location env vars; `GenerateContentConfig` has `response_mime_type`, `response_schema`, `system_instruction`, `max_output_tokens`, `speech_config` and `response_modalities`; `thinking_level` sits inside `ThinkingConfig` for 3.x; temperature and top_p/top_k deprecated on 21 Jul 2026 |
| Other components | google-adk is Apache-2.0. ECMWF `stream=enfo`, `type=tf` and `source="google"` work, CC BY 4.0. Geofabrik: Odisha is in `eastern-zone`, Andhra Pradesh in `southern-zone`. All Earth Engine IDs used exist, including `NASA/VIIRS/002/VNP46A2`. CAP 1.2 status and scope values and the XSD URL are correct |
| IMD definitions | Rainfall categories: heavy 64.5–115.5, very heavy 115.6–204.4, extremely heavy >204.5 mm per 24 h. MSW is a 3-minute mean at 10 m |
| Hosting, licences, formulas | Firebase Hosting returns 206 for single byte ranges. Licences as stated in `CLAUDE.md`. Holland (1980) formulas correct. The 0.3 m passability citation is correct |
| Not yet verified | Gemini 3.7 Flash, 3.5 Flash-Lite and embedding-2 on Agent Platform. Earth Engine noncommercial eligibility. Weather Lab publication delay per model (needed for the "available at bulletin issue time" rule) |

## C0: Montha ensemble coverage (checked 28 Sep 2026, 18:10–18:20 IST)

**Result: ensemble mode is available from both sources.** Use description version A (`docs/DEMO_AND_SUBMISSION.md` §6).

| Source | What exists for Montha | How it was checked |
| --- | --- | --- |
| ECMWF IFS ENS, `gs://ecmwf-open-data` | `enfo`/`tf` BUFR present for every 00z and 12z run on 24–28 Oct 2025 (HTTP 200, 0.64–0.75 MB each). Montha is **`03B`, 52 track subsets**, from the 27 Oct 00z run. Before that (24–26 Oct) ECMWF tracks the pre-genesis disturbance under provisional IDs (`70B`–`76B`, not stable across runs; e.g. `71B` with 46, 33 and 29 members on 24, 25 and 26 Oct 00z). Match these to IMD positions with the 300 km rule, never by ID | eccodes 2.x wheel; one BUFR message per storm, members as subsets |
| Weather Lab (Google DeepMind), public download endpoint `https://deepmind.google.com/science/weatherlab/download/cyclones/<MODEL>/<ensemble\|ensemble_mean>/paired/csv/<MODEL>_YYYY_MM_DDTHH_00_paired.csv` (no sign-in; the web UI itself now asks for a Google sign-in) | Montha is **`IO942025`**. 26 Oct 00z: **FNV3P2 50 members**; **FNV3_LARGE_ENSEMBLE 1,000 members** (16.7 MB CSV). OPER had no Bay of Bengal track at that cycle. Columns include per-member `radius_of_maximum_winds_km`, 34/50/64 kt wind radii by quadrant, MSLP and MSW (kt). Files are "paired" with observed tracks: **drop the paired observed columns/rows before use; they are hindsight** | curl + csv parse. URL pattern learned from the source of a community downloader (not used as a dependency) |
| Licence note | The CSV header says data relating to a time **more than 48 hours ago** is CC BY 4.0 (the guide says 1 hour). Montha data is ~11 months old, so CC BY 4.0 either way. Keep the "experimental; not produced with or endorsed by any government meteorological agency" label | File header |

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

## Owner actions (only a human can do these)

**Today, 28 Sep:**

- [ ] Confirm the team is **registered on Hack2Skill** for codeforcommunities2; registration closes with submission on 30 Sep at 23:59 IST. Confirm the team size is allowed: the page says 1–4 and the generic T&C say 2–6.
- [ ] Create a Google Cloud project, suggested ID `aurora-lifeline-<suffix>`, under the owner's **personal** Google account. Link the billing account that holds the US$150.
- [ ] Give Claude Code the project ID, the **billing account ID** and its **currency**, and say whether the US$150 is free-trial credit.
- [ ] Authenticate locally: `gcloud auth login` and `gcloud auth application-default login`.
- [ ] Register for **Earth Engine** noncommercial use as an individual, and register the Cloud project: https://developers.google.com/earth-engine/guides/access. Eligibility is UNVERIFIED: the noncommercial page does not cover hackathons, and prize money may count as compensation. Answer the questionnaire truthfully. If it is not eligible, the fallback is in `docs/COSTS.md`.
- [ ] Submit the **WeatherNext** data request form (free; 5–7 business days): https://developers.google.com/weathernext/guides/access-forecast
- [ ] Join the **Flood Hub API** waitlist (free): https://developers.google.com/flood-forecasting
- [ ] Create a **public GitHub repo** (`aurora-lifeline`, Apache-2.0) and give Claude Code push access.
- [ ] **Firebase console:** add Firebase to the project and accept the terms. Enable Auth providers Email/Password and Anonymous. Generate the Web Push (VAPID) key pair under Project settings > Cloud Messaging and give Claude the public key (`NEXT_PUBLIC_FCM_VAPID_KEY`).
- [ ] **Google Maps Platform > Map Management:** create a JavaScript **vector** Map ID and give it to Claude (`NEXT_PUBLIC_MAPS_MAP_ID`).
- [ ] **LGD district lists:** at lgdirectory.gov.in > Download Directory, download the district lists for Andhra Pradesh and Odisha as CSV into `data/raw/lgd/<date>/`. The form has a CAPTCHA, so Claude cannot do this.
- [ ] **MERIT Hydro:** if Earth Engine registration is not complete by 28 Sep 20:00, register on the University of Tokyo MERIT Hydro site and download the `hnd` tiles covering 10–25°N, 75–90°E yourself into `data/raw/merit_hydro/v1.0.1/`. Access uses an emailed password, which Claude cannot enter.
- [ ] **healthsites.io** (optional): sign in with an OpenStreetMap account, create an API token, and put it in `.env` as `HEALTHSITES_TOKEN`. If it isn't there by 29 Sep 00:00, facilities come from OSM tags only.
- [ ] **Approve or decline `recaptchaenterprise`** (App Check for the web; free up to 10,000 assessments a month). Until you approve, App Check runs in monitor-only mode.
- [ ] **Email the organisers now** (build-with-ai-india@googlegroups.com):
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
