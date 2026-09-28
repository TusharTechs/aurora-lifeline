# Product spec: AURORA Lifeline

## 1. Problem

District control rooms get official cyclone forecasts in the 72 hours before landfall: track, intensity, colour-coded district warnings and surge heights. No public Indian system we found tells them which roads, bridges, substations, hospitals, PHCs and shelters will fail, how likely that is and when. So decisions on where to stage earthmovers, repair crews, generators, medical kits and evacuations rest on category tables and experience.

Deaths have fallen from about 9,887 in the 1999 Odisha super cyclone to zero in Odisha during Dana (2024). Lifeline losses have not:

- Fani (2019) left 3.5 million households without power on day 5.
- Montha (2025) damaged about 13,000 poles, 3,000 transformers and 14 bridges or culverts in Andhra Pradesh.
- Deep depression BOB 06 (Sep 2026) killed about 74 people in India, 56 of them far inland in Uttar Pradesh.

Sources are in `docs/BLUEPRINT.md` and `docs/research/cyclone-technical-notes.md`.

## 2. Users and roles

| Role | Who | Can do |
| --- | --- | --- |
| `officer` | District emergency operations centre officer or Collector | See district timelines and actions; edit and approve advisories; confirm field reports |
| `analyst` | SDMA state control room | Everything an officer can do, for all districts in the state; view the proof page; set thresholds |
| `line_dept` | Health, power or public-works control room | Role-filtered view; acknowledge and close tasks |
| `field` | Block official, Aapda Mitra volunteer, lineman, ASHA supervisor | Receive tasks; submit photo, voice or video reports |
| `admin` | State IT or NIC | Onboard a state; manage users and roles; audit exports |
| `viewer` | Judges, NDMA; the public later | Read-only. For **archived past-storm replays** (a storm with `status=replay`), viewers see full facility- and settlement-level results, labelled "historical replay, not a forecast". For **live storms**, viewers see district aggregates only. No personal data |

**Demo officer.** The landing page has a "Try as officer (SIMULATED)" button.

1. It signs in with Firebase Anonymous Auth.
2. The API grants that uid a `demo_officer` claim scoped to `storms/montha_2025_demo`. That storm is defined in `config/storms/montha_2025_demo.yaml` (`status: replay`, `sandbox_of: montha_2025`, same `run_id`), so `generateStaticParams` builds its pages.
3. Everything a demo officer writes goes **only under the sandbox storm**, with `is_simulated=true`: approvals, field-report confirms, deltas, assetStates and audit rows. CAP uses `status=Exercise`. **The public `montha_2025` replay is never changed.** "Try as officer" and the two-browser demo open `/storm/montha_2025_demo/...`.
4. `make sandbox-reset` runs nightly via Cloud Scheduler. It copies the `montha_2025` summaries and advisory drafts into the sandbox, deletes the sandbox's deltas, fieldReports, assetStates and audit rows, and reloads the API's in-memory bundle.

Simulated named accounts, if needed, use email and password on a placeholder domain such as `example.org`. They are created by `infra/seed_users.py`, never with real inboxes.

## 3. Core concepts

- **Storm run:** one pipeline execution for one storm and one IMD bulletin (member 0), plus the ensemble members issued at or before that bulletin. It is identified by `run_id` and is immutable once published.
- **Member:** one ensemble track, keyed by `(source, member_no)`.
  - `IMD/0` is the official track.
  - The others come from WeatherNext Cyclones (Weather Lab) and the ECMWF IFS ensemble. Read member counts from the data.
  - A source track belongs to the storm if its first point is within 300 km of the IMD position at the same valid time.
- **Replay definition (slice).** The judge replay is **one** published run, `run_id = montha_2025_b<bulletin_no>`.
  - **Choosing the bulletin:** let T_obs be IMD's *observed* landfall time, from its post-landfall bulletin or report. T_obs is used only to pick the replay bulletin, never as a model input.
    - `replay_start_utc` = T_obs − 72 h.
    - Member 0 is the last bulletin issued at or before `replay_start_utc` that contains a landfall forecast. If there is none, use the first later bulletin that does.
    - Record it as `demo_bulletin_no` in `config/storms/montha_2025.yaml`.
  - **Forecast landfall:** `landfall_utc` is the first hour at which member 0's hourly track crosses the OSM coastline. The bulletin's `landfall.window_text` is shown in the provenance bar.
  - **Ensemble members:** the latest ECMWF and Weather Lab runs *available* at the bulletin's issue time. A run counts as available at its base time plus its publication delay, which is recorded in the manifest.
  - **Slider:** it shows the valid time of this single forecast. "Now", the default position, is the bulletin's issue time. The slider runs to `landfall_utc` + 24 h.
  - **"Before landfall"** always means `landfall_utc`, applied to every member.
  - **Demo district:** the Andhra Pradesh district (using the district set in force in Oct 2025) that contains member 0's forecast coast-crossing point. The observed landfall district is recorded separately in the manifest.
  - A member whose track ends before landfall contributes no hazard after its last point.
  - Runs for later bulletins are Demo Day work.
- **Lifeline graph:** road nodes and edges (bridges, culverts and fords as explicit edges), facilities, settlements, substations and service areas, per state.
- **Isolation time `b(v)`:** the latest time at which node `v` can still reach any functioning target of a class (hospital, referral or shelter), per member.
  - **P(isolated before landfall)** is the fraction of members with `b(v)` before landfall.
  - The **window** is the P10, P50 and P90 of `b(v)` across members where it is finite.
  - Nodes with `b = −∞` (no route even at t₀) are excluded from P and labelled "no mapped route (possible OSM gap)".
- **Action:** a deterministic recommendation with a deadline that states its basis, for example "by 14:00 IST (P10 closure − 6 h)". Each carries the people it protects and its evidence.
- **Advisory:** a Gemini-drafted, placeholder-grounded message in CAP 1.2, SMS text and a voice script. It is officer-approved before dispatch.
- **Deterministic mode:** if no ensemble members exist for a storm, the run uses `IMD/0` only. The UI shows a "deterministic: IMD track only" badge and isolation times without probabilities or windows. Action deadlines state "IMD-track closure − 6 h" as their basis. This is the only allowed exception to the window rule (`CLAUDE.md` non-negotiable 5).

## 4. Screens

| Route | Purpose | Roles |
| --- | --- | --- |
| `/` | Judge-mode landing. Storm picker (Montha 2025 replay). Three headline figures with windows: people cut off from any hospital, facilities at risk, and **people served by substations at risk**. Buttons: "Open district view", "See proof" and "Try as officer (SIMULATED)". No login | all |
| `/storm/[stormId]/district/[lgd]` | Command map (see below) | all (viewers read-only) |
| `/storm/[stormId]/approvals` | Queue of draft advisories and field reports awaiting confirmation | officer, analyst, demo officer (sandbox) |
| `/field` | Field report form: photo, video or voice, auto-location, asset picker, offline queue | field, officer, demo officer |
| `/storm/[stormId]/proof` | Validation: hit and miss maps, metrics against baselines, the surge table, bulletin-reading accuracy, completeness badges, limitations | all |
| `/about` | Method notes, data licences and attributions, synthetic-data policy, "not an official warning service" | all |

All routes are statically generated (`output: 'export'`, `generateStaticParams` for the configured storms and districts). `/approvals` and `/field` are client-only pages.

### Command map (district view)

- **Map:** Google Maps basemap with a vector Map ID and deck.gl layers:
  - ensemble tracks, with the IMD track in bold;
  - flood and surge extents at the slider time;
  - road edges coloured by P(closed by t);
  - facility glyphs by type with a probability halo;
  - settlements shaded by isolation probability;
  - substation service areas.
- **Time slider:** hourly from "now" (bulletin issue time) to landfall + 24 h. Play and pause. Keyboard accessible.
- **Right panel tabs:**
  - *Lifelines:* facilities sorted by P(isolated), with the window.
  - *Power:* population served by substations at risk, and the mapped share.
  - *Health:* CHCs, hospitals and possible delivery points, with expected births and needs.
  - *Actions:* ranked cards with deadlines and their basis.
  - *Advisories:* drafts and their status.
  - *Ask:* Demo Day.
- **Provenance bar** (always visible): "Derived from IMD bulletin No. [n] issued [time] · members: [k by source] · data versions · model version".
- **Badges:** "SIMULATED"; "prior" on uncalibrated parameters; "screening model" on surge; "deterministic" when there are no members; a completeness badge per district.
- **Live updates:** the client overlays Firestore `deltas` on the static district JSON (`docs/ARCHITECTURE.md` §2).

## 5. Feature acceptance criteria

Feature priorities are in `docs/BLUEPRINT.md` (Features), as corrected by `CLAUDE.md` precedence. **Slice** = the 30 Sep submission; **DD** = Demo Day.

### M1 Forecast intake (Slice)

- JSON valid against `schemas/bulletin_reading.json`.
- 100% field accuracy on the demo bulletin or bulletins.
- Accuracy reported on at least 5 human-confirmed Montha bulletins in the slice, and on 30 by Demo Day.
- Any failed check marks the run `needs_review`, and the analyst sees a banner.
- The bulletin number and issue time appear in the provenance bar.

### M2 Hazard engine (Slice)

- For each member and hourly step:
  - **wind** at facilities, substations and settlements (edges store only their maximum);
  - **surge depth** on coastal cells;
  - **drainage-based flood depth**.
- The same inputs give byte-identical outputs.
- Surge is labelled "screening model".
- The proof page includes the modelled-versus-IMD-reported surge table.

### M3 Lifeline graph (Slice)

- `make graph STATE=andhra_pradesh` finishes in under 60 minutes on a Cloud Run job (8 vCPU, 32 GiB). Odisha follows if time allows.
- Facilities and settlements snap within 2 km, otherwise they are flagged `unsnapped`.
- Bridges, culverts and fords are explicit edges.
- A completeness table covers every district.

### M4 Isolation forecast (Slice, the hero)

- For every facility and settlement: P(isolated before landfall), the P10/P50/P90 isolation times, and the deciles used by the slider.
- The population cut off from any functioning hospital, by hour.
- The 6-node unit test and the monotonicity tests pass.
- No single isolation hour is ever shown without its window (except in deterministic mode, where it carries the badge).

### M5 Power (Slice)

- Each settlement is assigned to a substation service area.
- In the slice, **only substation failures** are modelled: local line outage is not.
- The headline is "people served by substations at risk", labelled as a lower bound, with the "prior" badge and the mapped share.
- Wind fragility appears as a class unless a citable substation curve is found (`docs/ENGINE.md` §8).

### M6 Health continuity (Slice)

- For CHCs, area or sub-district hospitals and district hospitals (counted as delivery points in the slice), plus PHCs (badged "possible delivery point"):
  - patient-access and referral isolation windows;
  - power risk class or probability.
- Expected births in window W (`docs/ENGINE.md` §8), labelled "estimate".
- Dialysis appears as "not mapped" unless an official list is loaded.
- No patient-level data.

### M7 Actions and advisories with approval (Slice)

- Actions come only from the engine, ranked, each with a deadline and its basis.
- The Advisory Writer drafts in **English and Telugu** (Hindi and Odia if their checks pass by 30 Sep 12:00 IST).
- 100% of drafts pass the placeholder and number checks.
- The CAP XML validates against the vendored OASIS CAP 1.2 XSD and passes the rule checks: `status=Exercise`, `scope=Restricted` with a `<restriction>`, exercise ID in `<note>`, timestamp format, polygon axis order.
- Approval writes an audit record. Dispatch in the slice is a Firebase Cloud Messaging web push plus the CAP file download. SMS and IVR are Demo Day.
- The voice note plays through Cloud Text-to-Speech Gemini-TTS or the pre-rendered fallback (`docs/AI_AGENTS.md` §1).

### M8 Replay and proof (Slice)

`/storm/montha_2025/proof` shows:

- POD, FAR and CSI of predicted closed edges against Sentinel-1 flooding, for AURORA and two baselines, plus the misses and any districts marked "not observed";
- the surge table;
- bulletin-reading accuracy;
- limitations.

Everything is computed by `make validate`. If Earth Engine is unavailable, the proof page says "Sentinel-1 scoring pending Earth Engine access".

### M9 Command map (Slice)

- First meaningful map within 3 s on a laptop over throttled 4G.
- Default-zoom layers at most 5 MB per district.
- Colour-blind-safe palette.
- Works signed out.

### S1 Field-report loop (Slice: one report; DD: full)

- A report returns a structured observation in under 10 s.
- Above the threshold, the asset state updates, **except bridge reopenings, which always go to the officer queue**. Below the threshold, reports are queued.
- On confirmation, the API's in-memory recompute updates the demo district, and both open browsers reflect the change within 10 s through Firestore deltas.
- The demo image's verdict is cached.

### Demo Day features

| Feature | Acceptance criteria |
| --- | --- |
| S2 Optimiser | Assigns settlements to shelters within capacity, arriving before closure; reports the shortfall; solves in 30 s or less per district |
| S3 Phone delivery | SMS and IVR reach a test phone in Telugu |
| S4 Ask AURORA | 10/10 scripted questions, with citations and placeholders |
| S5 Inland | BOB 06 replay with a Flood Hub overlay |
| S6 Power validation | Leave-one-storm-out AUC for at least 3 storms |
| S7 States | Tamil Nadu, West Bengal and Gujarat build; a new storm runs in 10 minutes or less |

## 6. Non-functional requirements

- **Scale:** 10,000 concurrent viewers with p95 API latency under 500 ms, shown by a k6 test by Demo Day (`docs/ARCHITECTURE.md` §8).
- **Availability:** the judge replay works from static files alone.
- **Languages:** advisories in English and Telugu (Hindi and Odia if checks pass) in the slice; Bengali and Tamil by Demo Day.
- **Accessibility:** WCAG 2.2 AA target; never convey information by colour alone.

## 7. Out of scope

Citizen chatbot; track prediction; public broadcast alerts; insurance pricing; patient-level data; native apps; blockchain; model training in the slice; a self-hosted basemap in the slice.
