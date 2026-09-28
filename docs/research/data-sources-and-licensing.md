# Open-data and licensing report: AURORA (A) and Demand Atlas (B)
Pages read 2026-09-27. UNVERIFIED = could not open or confirm. SA = share-alike; NC = non-commercial; EE = Earth Engine; BQ = BigQuery.

## Headline findings
- A can use everything below in a government pilot or SaaS, **except**: FABDEM (NC), SHRUG (NC-SA), Bhuvan content (needs written permission), OSDMA shelter data ("All Rights Reserved"), and MERIT Hydro unless you choose its ODbL option.
- The main licence trigger is **Earth Engine itself**. Free noncommercial EE excludes government prototyping and operational use, so a ministry pilot needs a paid plan (Basic $500/month).
- WeatherNext needs an access form (5-7 business days). Submit it now. Until then, use ECMWF open data, Weather Lab CSVs and the IMD API.
- Rendered India maps must use Survey of India (SoI) boundaries, not OSM/Overture boundaries.
- For 10k concurrent users, serve precomputed PMTiles and BQ tables through a CDN. Don't call EE per user: Basic allows 20 concurrent high-volume requests per project.

## Part 1 - Direction A (cyclone impact)
| Dataset | Publisher | Contents (India relevance) | Access | Format & size | Licence | Attribution | Commercial/SaaS/gov pilot OK? | Update latency | URL |
|---|---|---|---|---|---|---|---|---|---|
| OSM India | OSM contributors; Geofabrik | Roads, health POIs, power, buildings | Bulk PBF/shp/gpkg | India PBF 1.6 GB; Eastern Zone 235 MB; Southern Zone 531 MB | ODbL 1.0 | "© OpenStreetMap contributors" + /copyright link | Yes; SA on publicly used derivative DB | Daily | https://download.geofabrik.de/asia/india.html |
| healthsites.io | Healthsites.io | Health facilities (OSM-based) | API token via OSM login; GeoJSON/SHP/CSV | UNVERIFIED | ODbL | OSM + healthsites.io | Yes, SA | Continuous | https://github.com/healthsites/healthsites/wiki/API |
| Open Buildings v3 | Google Research | Footprints + confidence, incl. India | EE `GOOGLE/Research/open-buildings/v3/polygons`; GCS CSV | Global CSV 178 GB | CC BY 4.0 **or** ODbL | Google Open Buildings | Yes | Static (2023) | https://sites.research.google/gr/open-buildings/ |
| Open Buildings 2.5D Temporal | Google Research | 2016-2023 presence, height, count; 4 m effective | EE `GOOGLE/Research/open-buildings-temporal/v1` | Raster | CC BY 4.0 or ODbL | Google; Copernicus Sentinel-2 | Yes | Annual | https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings-temporal_v1 |
| MS Global ML Footprints | Microsoft | 1.4B globally; +110M India edits (2024); 174M with heights | `dataset-links.csv` -> quadkey csv.gz | Per quadkey | CDLA-Permissive-2.0 | Licence notice | Yes | Irregular | https://github.com/microsoft/GlobalMLBuildingFootprints |
| Overture Maps | Overture Maps Foundation | Conflated buildings/transport/places | GeoParquet; BQ `bigquery-public-data.overture_maps` | UNVERIFIED | ODbL (base, buildings, divisions, transportation); CDLA-P-2.0 (places) | "Overture Maps Foundation, overturemaps.org" + © OSM contributors | Yes; SA on ODbL themes | BQ tracks latest release | https://docs.overturemaps.org/attribution/ |
| WorldPop | WorldPop | 100 m population 2000-2021 | EE `WorldPop/GP/100m/pop` | Raster | CC BY 4.0 | worldpop.org | Yes | Static | https://developers.google.com/earth-engine/datasets/catalog/WorldPop_GP_100m_pop |
| GHSL GHS-POP R2023A | EC JRC | 100 m population 1975-2030 | EE `JRC/GHSL/P2023A/GHS_POP` | Raster | EC reuse (acknowledge source) | DOI 10.2905/2FF68A52-5B5B-4A22-8F40-C41DA8332CFE | Yes | Static | https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_POP |
| Meta HRSL | Meta + CIESIN | ~30 m population density | AWS `s3://dataforgood-fb-data` | India tiles UNVERIFIED | CC BY 4.0 | Meta, CIESIN | Yes | Registry: quarterly (possibly discontinued, UNVERIFIED) | https://registry.opendata.aws/dataforgood-fb-hrsl/ |
| Census 2011 PCA / Village Directory | Office of RGI | Village population, amenities | Excel by series | ~6 lakh villages | Not stated (UNVERIFIED) | Census of India 2011 | UNVERIFIED | Static | https://censusindia.gov.in/census.website/data/census-tables |
| SHRUG v2.2 + open polygons | Development Data Lab | PCA/VD/MA by shrid; 649,618 PC11 polygons | Download after accepting terms; gpkg/shp | UNVERIFIED | CC BY-NC-SA 4.0 (polygon licence not stated, UNVERIFIED) | SHRUG + sources | **No** for SaaS | Static | https://www.devdatalab.org/shrug_download/ ; https://docs.devdatalab.org/SHRUG-Construction-Details/shrug-open-source-polygons/ |
| OSDMA shelters | OSDMA | ~877 shelters with lat/lon, district/block/village (JSON inside page) | Web page only | <1 MB | "All Rights Reserved" | OSDMA | Needs written permission | UNVERIFIED | https://www.osdma.org/shelter-locations/ |
| APSDMA / NCRMP / WB / TN shelters | APSDMA; NDMA | Shelter locator, hazard layers | APSDMA GIS apps; ncrmp.gov.in timed out; WB/TN not found | UNVERIFIED | Not stated | - | Seek data-sharing MoU | - | https://apsdmagis.ap.gov.in/weather-watch/portal-home.html |
| GEM Global Integrated Power Tracker | Global Energy Monitor | Plant units with coordinates; **no substations/lines** | Form download | UNVERIFIED | CC BY 4.0 | "Global Integrated Power Tracker, Global Energy Monitor, [month year] release" | Yes | Periodic | https://globalenergymonitor.org/creative-commons-public-license/ |
| OpenInfraMap | OIM (from OSM) | Substations, lines | Overpass / raw OSM | - | Data ODbL; analysis CC BY | © OSM contributors | Yes, SA | As OSM | https://openinframap.org/about |
| Bhuvan | NRSC/ISRO | Thematic layers, imagery | Portal (WMS UNVERIFIED) | - | ToS: no copying, derivatives or redistribution without prior written authorisation | - | **No** without permission | - | https://bhuvan.nrsc.gov.in/home/index.php |
| MOSDAC | SAC/ISRO | INSAT-3D/3DR/3DS, ocean products | Registration; API access menu | - | Tiers: general users get limited data at 3-day latency; privileged users get NRT; anonymous users get open data | MOSDAC | UNVERIFIED | NRT for privileged only | https://www.mosdac.gov.in/data-access-policy |
| IMD / RSMC New Delhi | IMD | Best Tracks 1982-2026 xlsx; bulletins; API `cyclone_track`, `cyclone_wind`, `cyclone_cou` | Web + api.imd.gov.in (account, JWT key) | Small | UNVERIFIED | IMD | Official source; redistribution terms UNVERIFIED | Real-time | https://rsmcnewdelhi.imd.gov.in/report.php?internal_menu=MzM= ; https://api.imd.gov.in/public/api_reference.html |
| INCOIS storm surge | INCOIS | Surge advisories, WebGIS | Web only; no API found | - | UNVERIFIED | INCOIS | UNVERIFIED | During events | https://tsunami.incois.gov.in/TEWS/AboutStormSurge.jsp |
| NDMA Sachet CAP | NDMA (C-DOT) | All-India CAP 1.2 alerts, multilingual, polygon URLs | Public RSS + per-alert CAP XML | KB | RSS `<copyright>public domain</copyright>` | NDMA Sachet | Yes (don't imply you are the issuer) | Near real-time | https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml |
| IBTrACS v04r01 | NOAA NCEI | Best tracks; NI basin from RSMC New Delhi | CSV/netCDF/SHP | Small | Open (WDC); commercial use per WMO Res. 40 | DOI 10.25921/82ty-9e16 | Yes | 3x/week | https://www.ncei.noaa.gov/products/international-best-track-archive |
| ECMWF open data | ECMWF | IFS + AIFS ensemble 0.25 deg, TC tracks | Portal; AWS/Azure/GCP mirrors | GRIB2; ~2-3-day rolling window | CC BY 4.0 | ECMWF | Yes | 4 runs/day | https://www.ecmwf.int/en/forecasts/datasets/open-data |
| Weather Lab (WeatherNext Cyclones) | Google DeepMind | Ensemble TC tracks + ECMWF baselines + observed | CSV/ATCF (~2023 onward) | Small | Data <1 h old: GDM experimental terms; older: CC BY 4.0 | Google DeepMind | Historical yes; not official warnings | Live | https://developers.google.com/weathernext/guides/weatherlab |
| WeatherNext 2 / 3 | Google | WN2 64 members, 0.25 deg, 15 days; WN3 (Aug 2026) up to 0.05 deg | EE `projects/gcp-public-data-weathernext/assets/weathernext_2_0_0`; BQ; GCS; **form** | Large | Historical CC BY 4.0; real-time under GDM terms. Model weights CC BY 4.0, code Apache-2.0 | Google | Yes (historical) | 6-hourly | https://developers.google.com/weathernext/guides/access-forecast ; https://github.com/google-deepmind/weathernext |
| GPM IMERG V07 | NASA | 30-minute rainfall | EE `NASA/GPM_L3/IMERG_V07` | 0.1 deg | NASA open | NASA GPM | Yes | Provisional NRT; no final products after 2025-09-30 | https://developers.google.com/earth-engine/datasets/catalog/NASA_GPM_L3_IMERG_V07 |
| ERA5-Land hourly | ECMWF/C3S | Reanalysis since 1950 | EE `ECMWF/ERA5_LAND/HOURLY` | ~11 km | C3S licence | "Generated using Copernicus Climate Change Service information [year]" | Yes | EE copy to 2026-09-21 | https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY |
| Sentinel-1 GRD / Sentinel-2 SR | EU/ESA Copernicus | SAR flood mapping; optical | EE `COPERNICUS/S1_GRD`, `COPERNICUS/S2_SR_HARMONIZED` | 10 m | Copernicus Sentinel T&C (free) | EU/ESA/Copernicus | Yes | S1 in EE within ~2 days | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD |
| Copernicus DEM GLO-30 | DLR/Airbus via Copernicus | 30 m DSM (EGM2008) | EE `COPERNICUS/DEM/GLO30_2024_1` | - | Free worldwide; commercial OK | Mandatory DLR/Airbus notice, exact text at URL | Yes | Static | https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_DEM_GLO30_2024_1 |
| FABDEM V1-2 | Univ. of Bristol / Fathom | 30 m bare-earth DEM | Bristol repository | - | Non-commercial free; commercial needs paid licence (CC BY-NC-SA per search) | - | **No** without Fathom licence | Static | https://www.fathom.global/insight/fabdem-download/ |
| MERIT Hydro (`hnd` = HAND) | Univ. of Tokyo | 90 m hydrography, HAND | EE `MERIT/Hydro/v1_0_1` | - | CC BY-NC 4.0 **or** ODbL 1.0 | Cite WRR 2019 paper | Yes via ODbL (SA) | Static | https://developers.google.com/earth-engine/datasets/catalog/MERIT_Hydro_v1_0_1 |
| GEBCO_2026 | GEBCO | 15 arc-second bathymetry | Global netCDF/GeoTIFF (~4 GB zipped) or area selection | - | Public domain | GEBCO Compilation Group (2026) GEBCO_2026 Grid | Yes | Annual | https://www.gebco.net/data-products/gridded-bathymetry-data |
| JRC Global Surface Water v1.4 | EC JRC / Google | Water occurrence 1984-2021 | EE `JRC/GSW1_4/GlobalSurfaceWater` | 30 m | Free, unrestricted | "Source: EC JRC/Google" | Yes | Static | https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater |

### Minimum dataset bundle (A)
| # | Layer | Source / ID | Size | Processing |
|---|---|---|---|---|
| 1 | Display boundaries | SoI Administrative Boundary Database (https://onlinemaps.surveyofindia.gov.in/) | Small | The only boundaries you render for India |
| 2 | Roads, POIs, power | Geofabrik `eastern-zone` (235 MB) + `southern-zone` (531 MB) PBF; which zone holds which state is UNVERIFIED, so fall back to India 1.6 GB if needed | 0.8-1.6 GB | `osmium extract` 100 km coastal buffer -> pyrosm `get_network("driving")`, `get_pois` (hospital/clinic), custom filter `power=substation/line` -> `to_graph(graph_type="networkx")` -> OSMnx travel times -> GeoParquet -> `bq load --source_format=PARQUET` |
| 3 | Buildings | Open Buildings v3 (confidence >= 0.75) + Temporal v1 2023 heights | Aggregates est. <5 GB | `reduceRegions` to H3 r8/village -> `Export.table.toBigQuery` |
| 4 | Population | `WorldPop/GP/100m/pop` 2020 or `JRC/GHSL/P2023A/GHS_POP` 2025 | Server-side | Same grid |
| 5 | Terrain/HAND/water | `COPERNICUS/DEM/GLO30_2024_1`, `MERIT/Hydro/v1_0_1:hnd`, `JRC/GSW1_4/GlobalSurfaceWater` | COGs est. 1-3 GB | Depth ~ water level minus HAND; mask permanent water |
| 6 | Bathymetry | GEBCO_2026 subset 5-25N, 76-93E | est. <100 MB | Surge input |
| 7 | Tracks | IBTrACS NI CSV; RSMC Best Tracks xlsx; Weather Lab CSV/ATCF; ECMWF TC tracks; IMD `cyclone_track`/`cyclone_cou` | <200 MB | One schema in BQ -> Holland wind |
| 8 | Rainfall | WeatherNext 2 (after approval); IMERG V07 | Server-side | 24/72 h totals -> HAND flooding |
| 9 | Backtest | `COPERNICUS/S1_GRD` IW VV, pre/post landfall | Server-side | Change detection vs model |
| 10 | Facilities | OSM + healthsites; GEM plants; OSDMA shelters **only with permission** | <50 MB | Snap to graph -> access-loss routing |
| 11 | Alerts | Sachet RSS/CAP | KB/day | Poll -> Pub/Sub -> BQ |
| 12 | Tiles | Protomaps build `pmtiles extract` India bbox `--maxzoom=14`; tippecanoe thematic PMTiles | Basemap est. several GB (UNVERIFIED) | Drop OSM national/disputed lines, overlay SoI; GCS + Cloud CDN. Protomaps counts as an ODbL Produced Work; self-host, don't hotlink (https://docs.protomaps.com/basemaps/downloads) |

## Part 2 - Direction B (citizen demand + planning)
| Dataset | Publisher | Contents | Access | Format & size | Licence | Attribution | Commercial/SaaS/gov pilot OK? | Update latency | URL |
|---|---|---|---|---|---|---|---|---|---|
| data.gov.in | NIC/MeitY; data owned by ministries | Multi-sector | API key required (keyless call returns "Authorization field missing"); rate limits UNVERIFIED. The footer currently shows a "sandbox environment" notice, so check each resource | Per resource | GODL-India (Gazette 13 Feb 2017): worldwide, royalty-free, all lawful commercial and non-commercial uses. Excludes personal info, logos, ID documents, RTI s.8 data | [Provider], [year], [dataset], [portal], [version], [URL], GODL | Yes | Per resource | https://www.data.gov.in/sites/default/files/Gazette_Notification_OGDL.pdf |
| Mission Antyodaya | MoRD/MoPR | GP/village facilities, 21 sectors, ~6.5 lakh villages | MA portal (DNS failed here, UNVERIFIED); eGramSwaraj PDSS by plan year 2019-20 to 2026-27; SHRUG MA-2020 | UNVERIFIED | Not stated; GODL via data.gov.in likely (UNVERIFIED) | MoRD | Likely (UNVERIFIED) | Per survey round | https://egramswaraj.gov.in/maSurveyDataState.do ; https://docs.devdatalab.org/SHRUG-Metadata/Mission%20Antyodaya%20Village%20Facilities%20(2020)/antyodaya-metadata/ |
| PAI 2.0 | MoPR | FY2023-24 GP scores; 150 indicators; grades A+ to D; released 24 Apr 2026 | Portal scorecards; bulk export UNVERIFIED | ~2.5 lakh GPs | UNVERIFIED | MoPR | UNVERIFIED | Annual | https://www.pib.gov.in/PressReleasePage.aspx?PRID=2256616 ; https://pai.gov.in/ |
| eGramSwaraj GPDP | MoPR | Approved action plans 2015-16 to 2026-27 | CAPTCHA-gated reports, no bulk export. Don't automate around the CAPTCHA; request data sharing | - | Owned by Panchayats/State PR departments | - | Permission needed for bulk use | Live | https://egramswaraj.gov.in/approveActionPlan.do |
| LGD | MoPR | Codes from state to village/GP/ULB; village-to-GP and pincode maps | Download Directory (XLS/ODT/PDF); NAPIX web services | est. ~6.5 lakh villages | UNVERIFIED | LGD | UNVERIFIED | Daily edits | https://lgdirectory.gov.in/ |
| NFHS-6 (2023-24) / NFHS-5 | MoHFW/IIPS | District factsheets for 715 districts (excl. Manipur), released 20-21 Aug 2026 | PDF via guest login; unit data on request | PDF | UNVERIFIED | IIPS, MoHFW | UNVERIFIED | ~5 years | https://www.nfhsiips.in/nfhsuser/release-details.php |
| NITI MPI 2023 | NITI Aayog | District MPI, NFHS-4 vs NFHS-5 | PDF, 410 pages, 22.7 MB | Tables need extraction | UNVERIFIED | NITI Aayog | UNVERIFIED | Occasional | https://www.niti.gov.in/sites/default/files/2023-08/India-National-Multidimentional-Poverty-Index-2023.pdf |
| HMIS | MoHFW | Service delivery, KPIs, facility master | Public web reports | - | UNVERIFIED | MoHFW | UNVERIFIED | Monthly | https://hmis.mohfw.gov.in/ |
| UDISE+ | MoE | School-level data | JS app, unreadable here | UNVERIFIED | UNVERIFIED | - | UNVERIFIED | Annual | https://udiseplus.gov.in/ |
| PMGSY OMMAS / GeoSadak | MoRD/NRIDA | Rural roads, habitations | Unreachable (DNS) | UNVERIFIED | UNVERIFIED | - | UNVERIFIED | - | https://omms.nic.in ; https://geosadak-pmgsy.nic.in |
| SHRUG | Development Data Lab | See Part 1 | - | - | CC BY-NC-SA 4.0 | SHRUG | Validation only | - | https://www.devdatalab.org/shrug_download/ |

**What SHRUG's NC-SA licence means:** NC rules out paid SaaS and paid pilots. SA would force derived tables (such as recommendation rankings built on SHRUG joins) to be NC-SA too, which conflicts with GODL/ODbL outputs and government ownership. Use SHRUG only for offline validation.

### Minimum bundle (B): one Aspirational District, then national
1. LGD blocks/GPs/villages + village-to-GP map -> BQ `lgd.*` (national est. <200 MB).
2. Census 2011 PCA + Village Directory -> crosswalk to LGD (Census codes in LGD: UNVERIFIED).
3. Mission Antyodaya facilities -> `ma.village_facilities`.
4. PAI 2.0 scores -> `pai.gp_scores_2023_24`.
5. Approved GPDP plans (manual export or MoPR sharing) -> `gpdp.activities`, so demands already planned are not re-recommended.
6. NFHS-6 district factsheet, NITI MPI district row, HMIS KPIs.
7. PMGSY roads if accessible, otherwise OSM.
8. Citizen inputs -> Gemini transcription/translation -> keep only LGD code, theme and text.

Going national uses the same schemas, partitioned by `state_lgd_code` (est. <20 GB).

## Part 3 - Legal notes
**Survey of India / geospatial policy**
- DST Guidelines of 15 Feb 2021, clause xiii: political maps of India at any scale must follow SoI maps or SoI digital boundary data. SoI is to offer these free, display/printing is allowed, and others may publish maps that adhere to them. Whether the SoI portal's boundary products are free is UNVERIFIED.
- Thresholds are 1 m horizontal and 3 m vertical. Finer data must be created/owned by Indian entities and stored and processed in India. A negative list covers sensitive attributes. In practice: use GCP India regions, an Indian entity as data owner, and no military features.
- NGP 2022 (Gazette 28 Dec 2022): publicly funded geospatial data is a common good; open standards/data are encouraged.
- In the app: strip OSM/Overture/Protomaps admin_level-2 and disputed lines, render SoI lines and label them "Boundaries: Survey of India". For BRICS views, use per-country boundary sources.
- Sources: https://dst.gov.in/sites/default/files/Final%20Approved%20Guidelines%20on%20Geospatial%20Data.pdf ; https://dst.gov.in/sites/default/files/National%20Geospatial%20Policy.pdf

**DPDP Act 2023 + Rules 2025**
- The Rules were notified 13/14 Nov 2025. The Consent Manager rule (R4) applies from ~Nov 2026. Notice, security, breach, retention and rights rules (R3, R5-16, R22-23) apply from ~May 2027, which falls inside a likely pilot.
- Voice, faces, phone numbers and GPS are personal data. Consent must be free, specific, informed and unambiguous, with an itemised notice.
- s.7 legitimate uses (no consent needed) include State functions under law, State benefits, and assisting people during a disaster. That fits AURORA advisories run by an SDMA. The SDMA or ministry is the Data Fiduciary; the team is a contracted processor.
- Build for: security safeguards with logs kept at least 1 year; breach reporting within 72 hours; erasure once the purpose is served; verifiable parental consent for children (so exclude minors from Gram Sabha media). The research exemption applies only when no decision is taken about an individual.
- Minimise: delete audio after transcription, blur faces, coarsen location to village/H3 r7, salt-hash WhatsApp IDs, and process in India regions.
- Sources: https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf ; Rules text (unofficial Gazette mirror) https://www.dpdpa.com/DPDP_Rules_2025_English_only.pdf ; https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/nov/doc20251117695301.pdf

**ODbL in practice**
- Your own attributes for a whole feature type, kept in a separate table keyed by OSM ID (e.g. flood depth per road), form a collective database: no SA on your data. Merging or deduplicating OSM hospitals with healthsites/government lists, or OSM buildings with Google/MS buildings, creates a derivative database, which carries SA.
- Produced works (PNG/PDF/raster) need attribution only. If one comes from a derivative DB and is used publicly, you must also offer that DB or the method. Vector tiles are unsettled, so attribute and publish your extraction scripts.
- An extract is insubstantial only below 100 features or about 1,000 inhabitants.
- Don't serve production traffic from tile.openstreetmap.org; self-host.
- Sources: https://www.openstreetmap.org/copyright ; https://osmfoundation.org/wiki/Licence/Community_Guidelines/Collective_Database_Guideline_Guideline ; https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline ; https://osmfoundation.org/wiki/Licence/Community_Guidelines/Substantial_-_Guideline ; https://operations.osmfoundation.org/policies/tiles/

**Earth Engine licence trigger**
- Free noncommercial EE covers nonprofits, academia, individuals, trainees, and LDC/Indigenous governments. Other government agencies may not use it for internal prototyping, repeated product generation or operational workloads. So an Indian state or ministry pilot, like any SaaS, needs a paid plan, and noncommercial projects must pass eligibility verification.
- Hackathon: members can register as individuals for noncommercial use. Building on a company's behalf makes it commercial.
- Plans: Limited (usage fees only); Basic $500/month (100 batch + 33 online EECU-h, 20 concurrent high-volume requests); Professional $2,000/month (500 + 166 EECU-h, up to 500 concurrent, SLA). Compute is $0.40/EECU-h for the first 10k hours.
- Each dataset's licence still applies on top of EE.
- Sources: https://earthengine.google.com/noncommercial/ ; https://developers.google.com/earth-engine/guides/access ; https://cloud.google.com/earth-engine/pricing

**BRICS:** OSM, Overture, MS footprints, ECMWF, IBTrACS, WeatherNext, GHSL and Copernicus are global. Open Buildings covers Africa, S/SE Asia and Latin America only. CAP 1.2 is the portable alert format.