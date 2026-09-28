# Data: sources, licences, processing and attribution

Every engine input is real, openly licensed data. The full licence research is in `docs/research/data-sources-and-licensing.md`. Where that file conflicts with `CLAUDE.md`, `CLAUDE.md` wins; for example, SHRUG is not used at all.

Before using a dataset, check its licence page again. Record the source, version, licence, access date and checksum in `config/datasets.yaml`; it generates `data/REGISTER.md`.

## 1. Storage layout

```
data/raw/<source>/<version>/ + sha256sums.txt    # local, git-ignored (task 1.4a, no approval needed)
gs://<data-bucket>/
  raw/<source>/<version>/...        # mirror of data/raw plus Earth Engine exports (task 1.4b)
  ref/<state>/<build_id>/...        # graph and exposure exports (also in BigQuery aurora_ref)
  storms/<storm_id>/{imd,ecmwf,weatherlab,sitreps}/
  runs/<run_id>/...                 # manifest, district JSON, recompute bundle, audio
gs://<quarantine-bucket>/           # field uploads until verified; 90-day lifecycle rule
```

## 2. Slice bundle (Andhra Pradesh landfall district first, then all of AP, then Odisha; Cyclone Montha 2025)

| # | Dataset | Get it | Licence and attribution | Processing |
| --- | --- | --- | --- | --- |
| 1 | OpenStreetMap | Geofabrik: `southern-zone-latest.osm.pbf` (Andhra Pradesh; ~531 MB) and `eastern-zone-latest.osm.pbf` (Odisha; ~235 MB), both verified against the zone polygons on 28 Sep 2026: https://download.geofabrik.de/asia/india.html | ODbL 1.0. Credit "© OpenStreetMap contributors". Publish derived databases under ODbL | Clip to `config/aoi/<state>.geojson` with **pyosmium** (BSD-2) or pyrosm's bounding-box filter; osmium-tool only as a separate build-time CLI. Then pyrosm: `get_network("driving")`, POIs, `custom_filter={"power": ["substation"]}`. OSMnx simplify, then a CSR graph. Bridges from `bridge=*`; culverts where roads cross `waterway=river/stream/canal/drain`; fords from `ford=yes` |
| 2 | Coastline and area of interest | OSM land polygons (osmdata.openstreetmap.de), clipped to 5–25°N, 76–93°E | ODbL | `config/aoi/<state>.geojson` = 120 km coastal buffer ∩ state polygon. Also used for surge inland distance and `coast_dist_km` |
| 3 | District polygons and LGD codes | OSM `boundary=administrative`, `admin_level=5` relations from the same extracts, joined by name to the LGD "Download Directory" district list (https://lgdirectory.gov.in/), saved as `config/states/<state>_districts.csv` (`lgd_code`, `name`, `osm_relation_id`, `name_variants`) | ODbL (OSM); LGD is a government publication | Use the district set in force in Oct 2025 (the post-2022 AP set of 26; Kakinada and Konaseema among them). If LGD's current list differs, record the difference. The LGD file comes from the owner (CAPTCHA); until it arrives, key districts by `osm_relation_id` and fill `lgd_code` later. Add the `imd_subdivision` column (for example "Coastal Andhra Pradesh & Yanam") for the rain rule (ENGINE §5). Hand-check coastal districts. Render district outlines only, never admin_level 4 or lower. If a relation is missing, the owner downloads Survey of India boundaries |
| 4 | Health facilities | healthsites.io API (token via OSM login): https://github.com/healthsites/healthsites/wiki/API, plus OSM `amenity`/`healthcare` | ODbL | Deduplicate within 150 m and by name. Classify (ENGINE §8). Completeness against Health Dynamics of India 2022-23 (https://www.pib.gov.in/PressReleasePage.aspx?PRID=2053070) |
| 5 | Settlements | WorldPop 2020 100 m India, **constrained** BSGM product (`ind_ppp_2020_constrained`, population placed only where buildings are mapped), downloaded directly from data.worldpop.org (no sign-in; switched from the 1.84 GB unconstrained `IND_ppp_2020` on 28 Sep because that server cannot resume interrupted downloads; HANDOFF D21); Open Buildings v3 **centroids only** (`GOOGLE/Research/open-buildings/v3/polygons`, confidence ≥ 0.75) as CSV | WorldPop CC BY 4.0 (www.worldpop.org); Open Buildings CC BY 4.0 (or ODbL) | **Slice:** settlements are H3 resolution-8 cells (h3-py, Apache-2.0) in the area of interest with population ≥ 25 (PRIOR). Population = sum of WorldPop pixel centres in the cell, computed locally with rasterio. Buildings = count of centroids per cell (null if the export isn't done by 29 Sep 06:00 IST). The hull is the H3 polygon. DBSCAN clustering is Demo Day |
| 6 | Terrain | Slice default: Copernicus DEM GLO-30 tiles from the AWS open-data bucket `s3://copernicus-dem-30m/` (no sign-in). Alternative: Earth Engine `COPERNICUS/DEM/GLO30_2024_1`, band `DEM`. It is an **ImageCollection**: `ee.ImageCollection(...).select('DEM').mosaic()`, exported with `crs='EPSG:4326', scale=30`. The older `COPERNICUS/DEM/GLO30` is deprecated | Free including commercial use. Copy the mandatory DLR/Airbus notice exactly from the dataset page | Coastal-band COG for surge; minimum elevation per edge |
| 7 | Height above drainage | Earth Engine `MERIT/Hydro/v1_0_1`, band `hnd`; or `hnd` tiles the owner downloads from the University of Tokyo site (emailed password) into `data/raw/merit_hydro/v1.0.1/` | **ODbL option** (the alternative is CC BY-NC). Cite Yamazaki et al. 2019 | Minimum HAND per edge (30 m buffer); per facility |
| 8 | Permanent water | Slice default: JRC Global Surface Water `occurrence` tiles from the JRC/Google download bucket (no sign-in). Alternative: Earth Engine `JRC/GSW1_4/GlobalSurfaceWater`, band `occurrence` | Free. Credit "Source: EC JRC/Google" | Mask where occurrence > 80% |
| 9 | Bathymetry | GEBCO_2026, subset 5–25°N, 76–93°E: https://www.gebco.net/data-products/gridded-bathymetry-data | Public domain. Credit "GEBCO Compilation Group (2026) GEBCO_2026 Grid" | Shelf slope (optional in the slice) |
| 10 | Rainfall (Demo Day calibration) | Earth Engine `NASA/GPM_L3/IMERG_V07`; WeatherNext 3 after access | NASA open; WeatherNext historical data CC BY 4.0 | `precipitation` is **mm/hr at 30-minute cadence**: accumulation = 0.5 × sum. Montha falls after the end of Final-run V07 in Earth Engine (30 Sep 2025), so only provisional data exists; record the run type |
| 11 | Radar flood maps | Earth Engine `COPERNICUS/S1_GRD` | Copernicus free. Credit "Contains modified Copernicus Sentinel data [2025]" | ENGINE §10 change detection → `aurora_eval.observed_flood_edges` |
| 12 | Best tracks (verification only) | IBTrACS v04r01 CSV from NOAA NCEI: https://www.ncei.noaa.gov/products/international-best-track-archive. Not the Earth Engine copy, which ends in 2024 | Open; commercial use per WMO Resolution 40. DOI 10.25921/82ty-9e16 | Verification labels only. **Never a forecast input** |
| 13 | ECMWF ensemble tracks as issued | Public mirror `gs://ecmwf-open-data` (runs from 12 Jul 2023; current `ifs/0p25` layout from 29 Feb 2024); ECMWF's own portal keeps only about 2–3 days. Example: `20251027/00z/ifs/0p25/enfo/20251027000000-240h-enfo-tf.bufr`. Client: `Client(source="google").retrieve(date=20251027, time=0, stream="enfo", type="tf", step=240, target=...)`; `step=144` for 06/18 UTC runs | CC BY 4.0. Credit ECMWF | **Use IFS ENS (`model="ifs"`) for Oct 2025** (no AIFS-ENS TC tracks on the mirror then). Parse BUFR with eccodes/pdbufr. Use only runs issued at or before the demo bulletin. **Check Montha is present first (1.4a)** |
| 14 | WeatherNext Cyclones tracks | Weather Lab downloads (CSV/ATCF, about 2023 onward): https://developers.google.com/weathernext/guides/weatherlab | Data older than 1 hour is CC BY 4.0. Label it: experimental, not produced with or endorsed by any government meteorological agency | Parse → `tracks`; member count from the file. North Indian Ocean and **Montha coverage is UNVERIFIED; check first (1.4a)** |
| 15 | IMD bulletins (Montha) | RSMC New Delhi: https://rsmcnewdelhi.imd.gov.in/rsmc-tropical-cyclones.php. IMD API with an account (optional): https://api.imd.gov.in/public/api_reference.html | Redistribution terms UNVERIFIED. **Never commit or re-host the PDFs**; link to IMD | Download every bulletin from genesis to landfall, with checksums, to `data/raw` and Cloud Storage. Bulletin Reader; labels |
| 16 | INCOIS surge guidance | https://tsunami.incois.gov.in/TEWS/AboutStormSurge.jsp (web only, no API) | Terms UNVERIFIED; link, do not re-host | Hand-record any published Montha surge guidance for the proof-page table |
| 17 | Issued alerts | NDMA Sachet RSS: https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml | Public domain (per the RSS). Never imply we are the issuer | Server-side proxy (no CORS); de-duplication |
| 18 | Shelters | OSM `amenity=shelter`, `emergency=*`, `social_facility`, and school buildings tagged as cyclone shelters | ODbL. **The OSDMA list is not used in any form** without written permission | Capacities simulated where unknown (`is_simulated=true`) |
| 19 | Crude birth rate | SRS Statistical Report (Office of the Registrar General), latest year | Government publication; cite it | One value per state in config |
| 20 | Validation closures | SDMA situation reports (Montha for AP, Fani for Odisha) | Government publications; link, don't re-host | Sitrep Extractor, then matched to edges |
| 21 | CAP 1.2 XSD | https://docs.oasis-open.org/emergency/cap/v1.2/CAP-v1.2.xsd | OASIS | Vendored in `schemas/cap/` with a checksum |

**Demo Day additions:**

- NASA Black Marble VIIRS `NASA/VIIRS/002/VNP46A2` (confirmed; band `Gap_Filled_DNB_BRDF_Corrected_NTL`; masks `Mandatory_Quality_Flag` and `QF_Cloud_Mask`).
- Flood Hub API (waitlist; free; CC BY 4.0).
- Tamil Nadu, West Bengal and Gujarat extracts.
- BOB 06 (Sep 2026) and Remal (2024) storm folders.
- PMNDP dialysis list, if one exists (UNVERIFIED).

## 3. Do not use

| Dataset | Why |
| --- | --- |
| SHRUG | CC BY-NC-SA; banned even for offline validation |
| FABDEM | Non-commercial |
| Bhuvan content | No derivatives without written permission |
| OSDMA shelter list (committed or fetched) without permission | All Rights Reserved |
| `bigquery-public-data.geo_openstreetmap` | Stale (2021) |
| Google Maps content as data | Violates the Maps terms; Maps is the basemap only |
| IBTrACS or IMD best track as a forecast input | Hindsight; would inflate the scores |

## 4. Synthetic and simulated data policy

- **Simulated:**
  - demo field reports (staged team photos, or openly licensed post-storm images with credit);
  - unpublished shelter capacities;
  - district resource inventories;
  - officer and field accounts (placeholder domain; anonymous demo officer).
- Each simulated record carries `is_simulated=true` and shows a "SIMULATED" badge. It never enters `aurora_eval`.
- The replay uses only data issued at or before the demo bulletin's issue time.

## 5. Attribution block (README and `/about`)

```
Map data © OpenStreetMap contributors (ODbL). Health facilities: healthsites.io (ODbL).
Buildings: Google Open Buildings (CC BY 4.0). Population: WorldPop (CC BY 4.0).
Terrain: Copernicus DEM GLO-30 — [paste the exact mandatory DLR/Airbus notice from the dataset page].
Height above nearest drainage: MERIT Hydro (Yamazaki et al., 2019), used under ODbL.
Surface water: Source: EC JRC/Google. Bathymetry: GEBCO Compilation Group (2026) GEBCO_2026 Grid.
Radar: Contains modified Copernicus Sentinel data [2025].
Tracks: ECMWF open data (CC BY 4.0); Google DeepMind Weather Lab / WeatherNext (CC BY 4.0 historical data).
Weather Lab / WeatherNext outputs are experimental, are not produced with or endorsed by any government meteorological agency, and are shown only as a non-official uncertainty envelope.
Verification: IBTrACS (NOAA NCEI). Official forecasts: India Meteorological Department (RSMC New Delhi). Alerts context: NDMA Sachet.
AURORA Lifeline is not an official warning service. IMD is the authoritative source for cyclone warnings in India.
```

## 6. Fixtures for tests and CI

- `tests/fixtures/mini_district/`: a clipped graph (~5,000 edges), 20 facilities, 200 settlements, a 3-member track set, rain and HAND grids.
- `tests/fixtures/bulletins/`: **no PDFs committed.** `download.py` fetches them by URL and checks checksums. Labels go in `labels/*.json` with `labelled_by`.
