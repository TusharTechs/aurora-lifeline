# Submission fields (Hack2Skill, Build with AI: Code for Communities, Second Edition)

Paste-ready text. Every claim below describes something in the deployed build; numbers come from the published runs (Montha IMD Bulletin 21 unless stated). Update the three links marked TODO before submitting.

## Project name

AURORA Lifeline

## Track

Track 05: Track-Based Cyclone Impact & Infrastructure Vulnerability Forecaster

## Links

- Live app: https://aurora-lifeline.web.app
- Control room (Montha, Kakinada): https://aurora-lifeline.web.app/storm/montha_2025/district/13999862/
- Second storm (Dana, Kendrapara, Odisha): https://aurora-lifeline.web.app/storm/dana_2024/district/9588868/
- Bulletin reader: https://aurora-lifeline.web.app/bulletin/
- Proof (validation with misses): https://aurora-lifeline.web.app/proof/
- Source code (Apache-2.0): https://github.com/TusharTechs/aurora-lifeline
- Video: TODO (unlisted YouTube link)
- Deck (PDF): TODO

## Brief description (2–3 lines)

AURORA Lifeline turns the official IMD cyclone bulletin into what a district control room must act on before landfall: which PHCs, hospitals, shelters and villages will lose road access, how likely, in what time window, and where to stage machinery first. Gemini reads the bulletin and drafts approval-ready advisories in English, Telugu and Hindi (with every number inserted by code), an ADK agent answers officers' questions from cited facts, field photos are checked by Gemini and routed by fixed rules to the map or an officer, and every forecast is scored against Sentinel-1 radar, misses included.

## Problem

Cyclone deaths in India have fallen sharply, but lifelines have not kept up: when a storm crosses the coast, the roads to PHCs and hospitals flood, bridges and culverts close, and villages are cut off from care for days. IMD's bulletins say where the storm will go and how strong it will be. They do not tell a District Collector which PHC will lose its last road, how likely that is, when, or what to move there before it happens. That translation is done today by phone calls and experience, in the 48–72 hours when it matters most.

## Solution

From one official IMD bulletin, AURORA Lifeline:

1. **Reads the bulletin** with Gemini (multimodal PDF input) into a structured reading where every value has a verbatim quote; code checks positions, speeds, category, quotes against the PDF text and the track against an independent table parser. An officer confirms before it drives a forecast.
2. **Runs storm futures**: every ECMWF and Google DeepMind WeatherNext ensemble member published by the bulletin's issue time (1,062 for Montha), aligned to IMD's track. IMD stays the authority; the ensembles are a labelled uncertainty envelope.
3. **Puts water on every road**: Holland winds, rain flooding from IMD's rainfall categories over a 90 m height-above-drainage model, and a storm-surge screen, hour by hour over 5.4 lakh road segments including 7,190 bridges and 1,245 culverts.
4. **Finds who is cut off, and when**: a bottleneck reachability search gives each village and health facility a chance of losing its last road to a public hospital, with a P10–P90 window (never a single, falsely precise hour).
5. **Decides what to move**: ranked machinery staging with deadlines and their basis ("P10 closure − 6 h"), indicative anticipatory-action triggers, and advisories drafted by Gemini in English, Telugu or Hindi, read aloud by Gemini-TTS, and exported as CAP 1.2 (Exercise, Restricted) for the SDMA's authorised originator. Nothing is sent without officer approval.

6. **Checks field reports after landfall**: Gemini assesses a field photo (passable, water-depth band, damage, blockage, consistency with the claimed place and time) after code has read and stripped its metadata. Fixed rules apply it to the map only when every check holds; everything else, and every bridge reopening, goes to an officer.

Montha (Andhra Pradesh, Oct 2025) and Dana (Odisha, Oct 2024) are replayed with only the forecasts published before landfall. A season-watch strip reads IMD's national-bulletin archive to show whether IMD is tracking a system today, and the Bulletin Reader can read IMD's latest bulletin live.

## How Google AI is used (each does real work)

- **Gemini 3.7 Flash on Agent Platform:** reads IMD bulletin PDFs (Bulletin Reader, with deterministic checks; 48 of 49 fields agree with hand labels on Montha bulletins 19 and 21), drafts advisories in three languages, and assesses field photos (Field Verifier; routing is deterministic).
- **Gemini 3.5 Flash-Lite + gemini-embedding-2:** back-translate Telugu and Hindi drafts and score similarity to the English draft (0.95 for Kakinada), flagging low scores to the officer.
- **Agent Development Kit:** Ask AURORA, an agent over five read-only tools; an after-model callback blocks any number the tools did not return.
- **Cloud Text-to-Speech Gemini-TTS:** advisories read aloud in Telugu, Hindi and English.
- **Google DeepMind WeatherNext (Weather Lab data):** 1,011 of Montha's 1,062 storm futures; 50 of Dana's 97.
- **Earth Engine:** Sentinel-1 flood mapping for validation.
- **Google Maps Platform, Cloud Run, Firebase Hosting, Secret Manager, Firestore, Workload Identity Federation:** basemap, API, site, secrets, usage caps, keyless deploys from GitHub.

**Guardrail:** Gemini never produces an AURORA number. It writes placeholders; code inserts every figure from the engine and rejects any digit it did not supply, in any script.

## Validation (published with misses)

- Sentinel-1 radar against forecast road closures, per district, with POD, FAR and CSI against two baselines (see the proof page for the current figures and caveats: the first radar passes came three to four days after landfall, so this is a weak test and AURORA's false-alarm rate against it is high).
- Bulletin Reader accuracy against hand-entered labels, and on IMD's live 2026 bulletin (all applicable checks pass).

## Built with

Python 3.12 (numpy, pandas, geopandas, shapely, rasterio, pyosmium, h3, numba, scipy), FastAPI, google-genai, google-adk, google-cloud-texttospeech, earthengine-api, Next.js (static export), React, deck.gl over the Google Maps vector basemap, Tailwind CSS, tippecanoe. Data: IMD, ECMWF open data, Google DeepMind Weather Lab, OpenStreetMap, Copernicus DEM GLO-30, JRC Global Surface Water, WorldPop, Sentinel-1.

## Real versus simulated

- Real: IMD bulletins, ensembles, roads, facilities, population, terrain, radar, every forecast figure.
- Simulated and labelled: the officer approval in the demo ("Approve as demo officer (SIMULATED)"); the field report (an openly licensed 2019 Kerala flood photo, credited, standing in for a field team's photo) and its officer confirmation; CAP messages are status Exercise.
- Not in this build: power-grid outage estimates, SMS/IVR delivery, field reports by voice note or WhatsApp.

## AI tools declaration

The code was written with the help of AI coding assistants. All data, methods and results were checked by running the pipelines and the deployed service; the design decisions and their reasons are recorded in `docs/HANDOFF.md`.

## Not an official warning service

IMD is the authoritative source for cyclone warnings in India. AURORA Lifeline is decision support for SDMA and district control rooms; it never issues public alerts.
