# Demo and submission

## 1. Demo script (4:45, recorded on the deterministic Montha replay)

The demo follows four beats (who is cut off, what goes dark, what to move where, what happened after landfall), then proof and scale. Fill every [bracket] from the actual run. **Show and name only features that exist in the build being judged.** The 30 Sep video has no OR-Tools plan, no SMS or IVR, no Ask AURORA, no inland replay and no load test.

| Time | On screen | Voice-over | Technology to name |
| --- | --- | --- | --- |
| 0:00–0:25 | Credited Montha damage photos; the BOB 06 headline | "Cyclone deaths have fallen close to zero. Lifelines have not. Seventy-two hours out, a control room knows the storm's category, not which PHC will be cut off." | — |
| 0:25–0:50 | IMD bulletin PDF beside Gemini's structured reading; ensemble members fan out (or the "deterministic" badge if there are no members) | "The official bulletin goes in. Gemini reads it into data we check. The ensembles show the uncertainty around IMD's track." | Gemini 3.7 Flash; ECMWF and WeatherNext Cyclones (if Montha coverage is confirmed) |
| 0:50–1:40 | Lifeline Countdown slider from the bulletin time to landfall; PHCs and settlements fade, with probability halos and windows | "This PHC has a [P] chance of losing its last road between [T1] and [T2]. [N] people lose access to any working hospital. About [B] births are expected in that window." | Earth Engine; OSM lifeline graph; BigQuery; deck.gl on Google Maps |
| 1:40–2:10 | Substation service areas; completeness badge | "At least [M] people are served by substations at risk. That is a lower bound: we show how much of the grid is mapped." | BigQuery GIS; WorldPop |
| 2:10–2:50 | Action cards with deadlines and their basis; Gemini drafts a Telugu advisory; the demo officer edits and approves; an in-app push with a voice note; the CAP file validates (`status=Exercise`) | "Stage a machine here before this road's earliest likely closure; generators to these PHCs. The officer approves, and the Telugu advisory arrives as a push with its voice note." | Gemini drafting; Cloud Text-to-Speech; Firestore approval; Firebase Cloud Messaging |
| 2:50–3:25 | Staged photo of a bridge; Gemini's verdict; the officer confirms; the bridge reopens and the PHC turns green on two screens | "After landfall, one verified photo reopens a bridge, and every control room sees it within seconds." | Gemini multimodal; Cloud Run; Firestore listeners |
| 3:25–3:55 | Proof page: Sentinel-1 hits and misses, POD/FAR/CSI against baselines; the surge table; bulletin accuracy | "Here is how we did on Montha, misses included." | Earth Engine Sentinel-1 |
| 3:55–4:20 | A second district or state from the same pipeline; the architecture slide | "Geography is configuration: the same pipeline runs for any coastal district." | Cloud Run jobs; Firebase Hosting |
| 4:20–4:45 | Google stack slide; measured results; Demo Day roadmap shown as roadmap | "Google AI is the engine, not a chatbot on top." | — |

**Recording tips:** 1080p; the browser zoomed for legibility; English captions; no personal data on screen; demo accounts badged SIMULATED. Claude writes a click-path script with timings; the owner records it.

## 2. Wow moments and backups

| Moment | Backup |
| --- | --- |
| Bulletin PDF becomes checked data | Cached reading shown side by side |
| Lifeline Countdown | Pre-tiled layers, a lower default zoom, a recorded clip |
| Telugu voice advisory after approval | Pre-rendered or cached audio |
| A photo reopens a bridge | Cached verdict; the officer-confirm path in one browser |
| Proof page with misses | Static page |

## 3. Failure plan (judge mode is a static replay first)

| If this fails | Fallback |
| --- | --- |
| Gemini | Cached outputs, marked with the cache time |
| Maps JavaScript API | A plain deck.gl background with district polygons only; no national or international boundaries rendered. No self-hosted basemap in the slice |
| Network at a venue | PWA offline cache of the replay; a local static copy; the recorded video |
| Earth Engine | Nothing live depends on it |
| Cloud Run or Firestore | The static replay still works; Firestore offline cache |
| Cold start | Warm instance 1–23 Oct plus a scheduled ping |

## 4. Track text to feature (for the README and one slide; slice only)

| Track 05 asks for | Where it lives in the 30 Sep build |
| --- | --- |
| AI-powered predictive risk and vulnerability modelling | Hazard engine, lifeline graph, isolation, power (substation lower bound), health (SPEC M2–M6) |
| Google Earth Engine satellite feeds | Earth Engine precompute of terrain, drainage, water, population and buildings; Sentinel-1 validation |
| Real-time meteorological data | IMD bulletins; ECMWF and WeatherNext Cyclones tracks (if coverage confirmed). The 6-hourly archiver is Demo Day |
| Gemini 3.7 Flash multimodal reasoning | Bulletin Reader, Field Verifier, Advisory Writer (Ask AURORA on Demo Day) |
| Simulate storm surges | Surge screening model scaled to IMD bulletin surge guidance, with a validation table. INCOIS products are linked, not ingested |
| Predict local rainfall damage pathways | IMD rainfall categories → drainage-based flooding → road and bridge closures → isolation |
| Exposure of power grids, arterial roads and medical shelters | Substation service areas; road graph with bridges and culverts; health-continuity view |
| Automated early-warning advisory dispatch | Drafting, officer approval, CAP 1.2, in-app push (SMS and IVR on Demo Day) |
| Evacuation planning, hardening, parametric liquidity | Rule-based pre-positioning and evacuation actions with deadlines. Capacity-aware shelter assignment and a trigger panel are Demo Day |

## 5. Deck (11 slides)

1. **Title:** "IMD tells you the storm. AURORA Lifeline tells you which PHC is cut off, how likely, when, and what to move there now."
2. **Problem:** lifelines, not deaths (Fani outages, Montha damage, BOB 06 inland deaths; cited).
3. **What exists and the gap:** IMD's category damage table; Web-DCRA (district-level composite risk as documented to 2023; 2026 status unconfirmed); INCOIS surge; Sachet delivery. Government tools only; no competitor names.
4. **Solution:** the four beats.
5. **Demo screens.**
6. **AI approach:** Gemini reads, verifies and writes; the engine counts; the human approves.
7. **Google stack:** Earth Engine, Gemini 3.7 Flash, BigQuery, Cloud Run, Firebase, Maps, Cloud Text-to-Speech, plus WeatherNext Cyclones (Weather Lab) **only if Montha coverage is confirmed**. Demo Day adds OR-Tools and ADK.
8. **Proof:** Montha skill against baselines, misses included; bulletin-reading accuracy.
9. **Who it serves and the pilot:** a district emergency operations centre and SDMA shadow-mode pilot in the October–December season; CAP for Sachet; Digital Public Good.
10. **Scale:** geography as configuration; cost per state; the static 10,000-user design (load test on Demo Day); BRICS and APAC coasts; the Earth Engine commercial path.
11. **Roadmap and ask:** a pilot state, data agreements, the Demo Day additions.

## 6. Submission checklist (30 Sep; submit by 22:00 IST)

- [ ] **Repo public** (Apache-2.0), tagged `submission-2026-09-30`. The README has:
  - problem;
  - quick start (`make setup`, `make replay STORM=montha_2025`, `make web`);
  - architecture;
  - the track-to-feature table (§4);
  - validation with misses;
  - the licence register and attribution block;
  - the synthetic-data policy;
  - the cost sheet;
  - open-source citations: OSMnx, pyrosm, pyosmium, rustworkx or NetworkX, h3, deck.gl, @vis.gl/react-google-maps, tippecanoe, eccodes and pdbufr, OR-Tools if used, and k6 as a test-only AGPL tool;
  - the "not an official warning service" note.
- [ ] No secrets or personal data; the secret scan passes.
- [ ] **Deployed link** opens judge mode without login. Checked from a clean browser on two networks and on a phone.
- [ ] **Video** 3–5 minutes, uploaded (unlisted is fine) and linked.
- [ ] **Deck** 10–12 slides, as PDF.
- [ ] **Brief description**, 2–3 lines. Use version A if Montha ensemble coverage is confirmed, otherwise version B.

> **A:** AURORA Lifeline turns an official IMD cyclone forecast into the consequences district control rooms must act on: which hospitals, PHCs, shelters and villages will be cut off, how likely and when, who is served by substations at risk, and what to pre-position where. Earth Engine and Gemini 3.7 Flash power it, with ECMWF and Google WeatherNext Cyclones ensembles as the uncertainty envelope. Officers approve every multilingual advisory, field photos update the map live, and every forecast is scored against satellite radar.
>
> **B:** The same text, replacing the ensemble clause with "running on IMD's official track".

- [ ] Warm instance on for 1–23 Oct; spend checked.
- [ ] `docs/SUBMISSION_FIELDS.md` complete; `docs/HANDOFF.md` updated.

## 7. Questions for the organisers (send now: build-with-ai-india@googlegroups.com)

1. May the deployed link be updated after 30 Sep, or must Demo Day work use a separate link?
2. Are prizes or shortlist places allocated per track?
3. Does the generic Hack2Skill T&C apply (IP, right of first refusal, the "sole author" warranty given AI-assisted code)?
