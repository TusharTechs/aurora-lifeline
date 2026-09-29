# AURORA Lifeline

**Cyclone decision support for district control rooms.** IMD tells you the storm. AURORA Lifeline tells you which PHC is cut off, how likely, when, and what to move there now.

- Live: **https://aurora-lifeline.web.app**
- Control room (Cyclone Montha, Kakinada): https://aurora-lifeline.web.app/storm/montha_2025/district/13999862/
- Read an IMD bulletin with Gemini: https://aurora-lifeline.web.app/bulletin/
- Proof, with misses: https://aurora-lifeline.web.app/proof/

Built for Track 05 (Track-Based Cyclone Impact & Infrastructure Vulnerability Forecaster) of _Build with AI: Code for Communities, Second Edition_.

## What it does

From the official India Meteorological Department (IMD) bulletin, AURORA Lifeline estimates, for every road, bridge, culvert and health facility in a coastal district:

- **who loses road access** to a public hospital (PHCs, CHCs, hospitals, shelters, villages);
- **how likely** that is, across a thousand storm futures, and **when** (a P10–P90 window, never a single hour);
- **what to move, and by when**: where to stage earthmovers before the crossings they depend on close, with the basis of each deadline ("P10 closure − 6 h").

It then drafts the advisory in English, Telugu or Hindi, and a CAP 1.2 message for the SDMA's authorised originator. Nothing is sent without officer approval.

The public site replays Cyclone Montha (Oct 2025) exactly as AURORA would have seen it 62 hours before landfall, from IMD National Bulletin No. 21, using only forecasts published by then. A season-watch strip shows whether IMD is issuing cyclone bulletins today.

## How it works

1. **Read the bulletin.** Gemini reads the IMD PDF into a structured reading with a verbatim quote for every value. Code checks it: basin, fix-to-fix speed, winds against category, quotes found verbatim in the PDF, and the track against an independent table parser. An officer confirms before it drives a run.
2. **Storm futures.** Every ECMWF IFS ensemble member and Google DeepMind WeatherNext (Weather Lab) member published by the bulletin's issue time is matched and aligned to the IMD track (1,062 futures for Montha, weighted equally per source).
3. **Hazards on every road.** Holland (1980) winds; rain flooding from IMD's rainfall categories and spatial coverage over AURORA's own 90 m height-above-drainage model (priority-flood, Barnes 2014, from Copernicus GLO-30); a storm-surge screen. Roads close hour by hour, with a formation allowance per road class.
4. **Who is cut off, and when.** A bottleneck (widest-path) reachability search over 5.4 lakh road segments finds the hour each place loses its last road to a public hospital, per future; the ensemble gives the chance and the window.
5. **Decide.** Machinery goes where it protects the most people; Gemini drafts the words; code inserts every number; an officer approves.

## Google AI in the product

| Where                                                      | What it does                                                                                                         |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Gemini 3.7 Flash (Agent Platform)                          | Reads IMD bulletin PDFs (multimodal) with quotes; drafts advisories in English, Telugu and Hindi                     |
| Gemini 3.5 Flash-Lite                                      | Back-translates Telugu and Hindi drafts for the review check                                                         |
| gemini-embedding-2                                         | Scores back-translation similarity (flags low scores to the officer)                                                 |
| Agent Development Kit                                      | Ask AURORA: an agent over five read-only tools; an after-model callback blocks any number it did not get from a tool |
| Google DeepMind WeatherNext (Weather Lab data)             | 1,011 of the 1,062 Montha storm futures                                                                              |
| Earth Engine                                               | Sentinel-1 flood mapping for the proof page                                                                          |
| Maps Platform, Cloud Run, Firebase Hosting, Secret Manager | Basemap; API; site; keyless deploys from GitHub with Workload Identity Federation                                    |

**Gemini never produces an AURORA number.** It writes `{{fact_id}}` placeholders; code fills them from the engine's facts and rejects any digit it did not supply, in any script, with one corrective retry. Gemini calls are cached by input hash so the public replay is deterministic.

## Validation

The [proof page](https://aurora-lifeline.web.app/proof/) scores forecasts against independent evidence, misses included: Sentinel-1 radar flooding at road segments (POD, FAR, CSI per district against two baselines), and Bulletin Reader accuracy against hand-entered labels (see `docs/eval-results.md`). Parameters not yet calibrated are labelled prior in every run manifest.

## Repository

```
engine/aurora_engine/     tracks, wind, rain, surge, HAND, graph, reachability, weights (Python 3.12)
pipelines/                OSM extraction, graph build, storm run, publish, tiles, Sentinel-1 scoring
agents/aurora_agents/     Bulletin Reader, Advisory Writer, CAP 1.2, Ask AURORA (ADK), number safety
services/api/             FastAPI on Cloud Run
apps/web/                 Next.js static site (deck.gl over the Google Maps vector basemap)
schemas/                  JSON Schemas (source of truth) and the vendored CAP 1.2 XSD
config/                   storms (replay definitions), states, districts
infra/cloudshell/         one-time Cloud Shell setup scripts
docs/                     spec, architecture, engine, agents, data, build plan, handoff
```

Generated map tiles and run JSON are published on the `web-data` branch (`make web-data`); CI and deploys unpack them.

## Run it locally

Requirements: uv, pnpm, Node 22+, tippecanoe, Java 21 (Firebase emulators), gitleaks. `make setup` checks and installs.

```bash
make setup
make download                       # public raw data (no sign-in)
make graph STATE=andhra_pradesh     # HAND and the road graph for the delta districts
make replay STORM=montha_2025       # storm run and district JSON
make tiles STORM=montha_2025        # vector tiles and overlays
make web                            # http://localhost:3000
make test                           # ruff, mypy, pytest, eslint, vitest
```

## Limits

- Surge is a screening upper bound, not a hydrodynamic model; IMD surge guidance takes precedence.
- Riverine inflow from upstream districts is not modelled; closures never reopen within a run.
- Road data is OpenStreetMap; facilities with no mapped route are flagged, not guessed.
- Weather Lab / WeatherNext outputs are experimental, are not produced with or endorsed by any government meteorological agency, and are shown only as a non-official uncertainty envelope.

AURORA Lifeline is not an official warning service. IMD is the authoritative source for cyclone warnings in India.

## Data and credits

Map data © OpenStreetMap contributors (ODbL). Population: WorldPop (CC BY 4.0). Terrain: produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. Height above nearest drainage (Sentinel-1 mask filter): MERIT Hydro (Yamazaki et al., 2019). Surface water: Source: EC JRC/Google. Radar: Contains modified Copernicus Sentinel data [2025]. Tracks: ECMWF open data (CC BY 4.0); Google DeepMind Weather Lab / WeatherNext (CC BY 4.0 historical data). Verification: IBTrACS (NOAA NCEI). Official forecasts: India Meteorological Department (RSMC New Delhi); IMD bulletins are read from IMD's archive and never re-hosted. Basemap: Google Maps Platform. CAP 1.2: OASIS. Demo field photo: "Kerala Flood 9-8-2019 at Kidangoor–Mookkannoor road near Angamaly" by Navaneeth Krishnan S, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), via [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Kerala_Flood_9-8-2019_at_Kidangoor_-Mookkannoor_road_near_Angamaly.jpg); resized and metadata removed (`apps/web/public/demo/`).

Method references: Holland (1980) for the wind profile; Barnes et al. (2014) priority-flood; Pregnolato et al. (2017) for the 0.3 m passability depth; UN-SPIDER recommended practice for Sentinel-1 flood mapping.

Open-source components include numpy, pandas, geopandas, shapely, rasterio, pyosmium, h3, numba, scipy, pydantic, FastAPI, google-genai, google-adk, earthengine-api, Next.js, React, deck.gl, vis.gl react-google-maps, Tailwind CSS and tippecanoe (build-time only). Licences are listed in each package; no GPL or AGPL code is imported or shipped.

The code was written with the help of AI coding assistants, as declared in the hackathon submission.

## Licence

Apache-2.0. See `LICENSE`.
