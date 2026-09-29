# Demo and submission

## 1. Demo script (4:45; the deployed build on 29–30 Sep 2026)

Record at https://aurora-lifeline.web.app in Chrome, 1440 x 900, dark theme, no personal data on screen. Every figure below comes from the live replay; read it off the screen rather than from this script. Show and name only what exists.

| Time | Click path (what is on screen) | Voice-over | Name |
| --- | --- | --- | --- |
| 0:00–0:20 | Landing page, hero playing: the storm futures sweep to the coast; the time card counts people cut off | "Seventy-two hours before a cyclone lands, a control room knows the storm. It does not know which PHC will lose its last road. AURORA Lifeline does." | — |
| 0:20–0:35 | Point at the season-watch strip; the "four questions" section: click through the four answers | "It runs on every official IMD bulletin. For Kakinada, from Bulletin 21, it answered four questions: which facility, how likely, when, and what to move." | IMD |
| 0:35–1:05 | Bulletin reader: click the live IMD bulletin (or Montha No. 21); show the checks and the forecast table with IMD's words | "Gemini reads the bulletin PDF itself. Every value comes with a verbatim quote, and code checks it against the PDF and an independent parser. An officer confirms before it drives a forecast." | Gemini 3.7 Flash on Agent Platform |
| 1:05–1:50 | Open the Kakinada control room. Play the timeline from Bulletin 21 to landfall; hover a red PHC; switch Bulletin 19 / 21 | "A thousand storm futures from Google DeepMind WeatherNext and ECMWF, aligned to IMD's track, put water on five lakh road segments. This PHC has a [p] chance of losing referral access, most likely between [t1] and [t2]." | WeatherNext; Maps Platform; deck.gl |
| 1:50–2:10 | Forecast tab: the action list; Triggers tab: open the fired triggers | "Machinery goes to the bridge that protects the most people, six hours before its earliest likely closure. Pre-agreed triggers fire for the facilities above threshold." | — |
| 2:10–2:50 | Advisory tab: Telugu, Collector; Draft; show the placeholders view and cited facts; Listen; Download CAP; Approve (simulated) | "Gemini drafts the Telugu advisory, but it never writes a number: code inserts every figure from the engine. It is read aloud with Gemini-TTS, and exported as a CAP message for the SDMA's originator, after an officer approves." | Gemini; gemini-embedding-2; Cloud TTS Gemini-TTS |
| 2:50–3:15 | Ask AURORA tab: click "Where should we pre-position JCBs first, and by when?"; open the citations | "Ask AURORA is an agent built with Google's Agent Development Kit. It answers only from the run's facts, and a guard blocks any number the tools did not return." | Agent Development Kit |
| 3:15–3:35 | Field tab: "Use the demo photo"; Send; show the assessment chips and "Sent to the officer queue" with its reasons; "Confirm as officer (SIMULATED)"; the marker appears on the map | "After landfall, field teams send photos. Gemini reads the damage; fixed rules decide. A report it cannot place goes to an officer, and a bridge reopening always does." | Gemini 3.7 Flash |
| 3:35–4:05 | Proof page: the Sentinel-1 table and "How to read this"; the Bulletin Reader scores | "We scored it against Sentinel-1 radar. It is a weak test, the passes came days later, and we publish the misses. The Bulletin Reader agrees with hand-checked labels on 48 of 49 fields." | Earth Engine |
| 4:05–4:25 | Landing page: the Dana card; open Kendrapara | "Geography is configuration. The same pipeline runs Cyclone Dana in Odisha." | Cloud Run; Firebase Hosting |
| 4:25–4:45 | Deck slide 7 (Google stack) then slide 11 | "Google AI is the engine, not a chatbot on top. Next: a shadow-mode pilot with an SDMA this season." | — |

**Before recording:** open each page once so cached answers are warm; turn on "Reduce motion" only if the machine stutters. **Captions:** English, from this script.

## 2. Wow moments and backups

| Moment | Backup |
| --- | --- |
| Bulletin PDF becomes checked data | Cached reading shown side by side |
| Lifeline Countdown | Pre-tiled layers, a lower default zoom, a recorded clip |
| Telugu voice advisory after approval | Pre-rendered or cached audio |
| A field photo is checked and routed to the officer | Cached verdict (same photo, same claimed place) |
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

## 4. Track text to feature (the 30 Sep build)

| Track 05 asks for | Where it lives |
| --- | --- |
| AI-powered predictive risk and vulnerability modelling | Storm futures → hazards on every road → bottleneck isolation for every facility and village (control room) |
| Google Earth Engine satellite feeds | Sentinel-1 flood mapping for validation (proof page) |
| Real-time meteorological data | IMD bulletins (season watch reads IMD's archive; the Bulletin Reader reads the latest bulletin live); ECMWF and WeatherNext ensembles |
| Gemini multimodal reasoning | Bulletin Reader (PDF), Advisory Writer, Ask AURORA (ADK) |
| Simulate storm surges | Surge screening model scaled to IMD surge guidance (Montha); Dana's first bulletin had none |
| Predict local rainfall damage pathways | IMD rainfall categories and coverage → height-above-drainage flooding → road, bridge and culvert closures → isolation |
| Exposure of power grids, arterial roads and medical shelters | Roads, bridges, culverts, PHCs, CHCs, hospitals and shelters; power is on the roadmap |
| Automated early-warning advisory dispatch | Drafts in three languages, voice, officer approval (simulated in the demo), CAP 1.2 for Sachet |
| Evacuation planning, hardening, parametric liquidity | Machinery staging with deadlines; indicative anticipatory-action triggers |

## 5. Deck (11 slides)

The deck is a page of the site: https://aurora-lifeline.web.app/deck/ . Print it from Chrome (landscape, margins none, background graphics on) to get the PDF; every figure is read from the published runs at build time.

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
