**Summary:** Most of the stack costs little up to about 10k monthly active users (MAU) if the app is static-first and India Maps pricing applies. From 100k MAU, the big costs are Gemini called per user, Maps loads, Places and Routes calls per user, and CDN egress. Earth Engine becomes a paid commercial licence as soon as this turns into a government pilot.

## Cost architecture brief: AURORA / Demand Atlas (checked 2026-09-27)

Source tags such as [M3] link to the list at the end. **UNVERIFIED** means I could not confirm it on an official page.

### 1. Google Maps Platform

**Pricing model**
- Since 1 Mar 2025 each SKU has its own free monthly cap, replacing the $200 monthly credit.
- Global caps are Essentials 10,000, Pro 5,000 and Enterprise 1,000 events a month. Volume discounts now run to 5M+ events [M1][M2].
- India got these changes early, on 1 Aug 2024 [M2].

**India pricing is still active** and has no end date. It applies to "accounts that have billing and a large majority of usage in India" [M4]. India caps are 7× the global ones: 70k / 35k / 7k.

| SKU | India free cap / price per 1k [M3] | Global free cap / price per 1k [M1] |
|---|---|---|
| Dynamic Maps (Maps JS, billed per map load [M11]) | 70k / $2.10 | 10k / $7.00 |
| Map Tiles 2D | 700k / $0.18 | 100k / $0.60 |
| Photorealistic 3D Tiles (root tileset request) | 7k / $3.30 | 1k / $6.00 |
| Geocoding | 70k / $1.50 | 10k / $5.00 |
| Autocomplete | 70k / $0.85 | 10k / $2.83 |
| Place Details Essentials / Pro | 70k / $1.50; 35k / $5.10 | 10k / $5; 5k / $17 |
| Text Search Pro | 35k / $9.60 | 5k / $32 |
| Compute Routes Essentials / Pro / Enterprise | 70k / $1.50; 35k / $3.00; 7k / $4.50 | 10k / $5; 5k / $10; 1k / $15 |
| Route Matrix (per element) Essentials / Pro | 70k / $1.50; 35k / $3.00 | 10k / $5 |
| Route Optimization: single vehicle / fleet | 35k / $0.80; 7k / $2.40 | 5k / $10 (Pro) |
| Air Quality | 70k / $0.50 | 10k / $5.00 |
| Weather | 70k / $0.06 | 10k / $0.15 |
| Elevation | 35k / $1.50 | 5k / $5.00 |

**Routes API**
- It only supports `avoidTolls`, `avoidHighways`, `avoidFerries` and `avoidIndoor`, and these only bias the result.
- It **cannot avoid arbitrary closed roads or polygons**, and Route Matrix supports no route modifiers at all [M5].
- So AURORA has to compute access loss on its own OSM road graph. Routes API is only useful for normal-time travel times.

**Weather API**
- Offers current conditions, up to 240 h hourly, up to 10 days daily, and 24 h of history [M6].
- For India, conditions, forecast and history are supported, but **weather alerts are not** [M7]. CAP alert inputs must come from Indian agency feeds (UNVERIFIED which feed).

**Map Tiles quotas** [M10]
- 2D and Street View tiles: **15,000 requests per project per day** by default, and 6,000 per minute.
- 3D: 10,000 root tileset requests per day.

**API key practice** [M8][M9]
- Restrict browser keys by HTTP referrer and restrict each key to the APIs it needs. Use a separate key per app.
- Keep server keys behind a server-side proxy. Split client and server keys into separate projects.
- Use App Check, delete unused keys, and set per-API quota caps.
- A Maps budget does **not** cap spending.

### 2. Google Earth Engine

**Is our use noncommercial?** [E2]
- Nonprofits, academic research and teaching, news media and trainees qualify as noncommercial.
- Government agencies qualify **only** if they are in a UN Least Developed Country, are an Indigenous government, or are doing scholarly research. India is not an LDC.
- Commercial use includes "production of tooling for management, policy, or web applications" and datasets or apps "maintained on an on-going basis".
- **Result:** a ministry or state pilot, or a SaaS product, needs a commercial licence.
- **The hackathon itself is not addressed on the page (UNVERIFIED).** Individuals may not receive compensation for work built with EE, so whether prize money counts is unclear.
- Register truthfully through the noncommercial questionnaire [E6]. If in doubt, use the Limited commercial plan.

**Commercial plans** [E1]

| Plan | Fee | Included |
|---|---|---|
| Limited | usage only, $0.40 per EECU-hour (0–10k h), then $0.28, then $0.16 | no SLA; 20 concurrent high-volume requests |
| Basic | $500 / month | 100 batch + 33 online EECU-hours, 100 GB, up to 8 concurrent exports |
| Professional | $2,000 / month | 500 batch + 166 online EECU-hours, 1 TB, SLA, VPC Service Controls |

- Storage costs $0.000035616 per GiB-hour, about $0.026 per GiB-month.

**Noncommercial tiers** (enforced from 27 Apr 2026) [E4]
- Community: 150 EECU-hours a month.
- Contributor: 1,000 EECU-hours a month. Needs a billing account, but the EE usage itself is not charged.
- Partner: 100k EECU-hours a month, by application.
- These are soft limits: going over puts the project in a restricted, slower mode rather than cutting it off.

**Quotas** [E3]
- 40 concurrent interactive requests and 100 requests per second per project.
- About 2 concurrent batch tasks on average, and 3,000 queued tasks.
- 250 GB asset storage and a 10 MB request payload limit.
- **EE therefore cannot sit in the path of 10k users. Precompute results and serve them statically.**

**Calling EE from Cloud Run** [E5][E6]
- Register the Cloud project for EE and enable the API.
- Give the service account Earth Engine Resource Viewer or Writer, plus Service Usage Consumer.
- Authenticate with Application Default Credentials and call `ee.Initialize(credentials, project=...)`. Do not use JSON key files.

**Catalog IDs checked**

| Dataset | ID | Notes |
|---|---|---|
| GPM IMERG | `NASA/GPM_L3/IMERG_V07` | Runs to 2026-09-26. No "permanent" products after 2025-09-30 because of the move to V8 [D1] |
| ERA5-Land | `ECMWF/ERA5_LAND/HOURLY` | Runs to 2026-09-21. Copernicus licence, attribution required [D2] |
| Sentinel-1 GRD | `COPERNICUS/S1_GRD` | Updated daily [D3] |
| Sentinel-2 SR | `COPERNICUS/S2_SR_HARMONIZED` | [D4] |
| JRC Global Surface Water | `JRC/GSW1_4/GlobalSurfaceWater` | Data ends 2021 [D5] |
| Copernicus DEM | `COPERNICUS/DEM/GLO30_2024_1` | Band `DEM`. The older `COPERNICUS/DEM/GLO30` is **deprecated** [D6][D7] |
| MERIT Hydro | `MERIT/Hydro/v1_0_1` | Has an `hnd` band (height above nearest drainage). Licence is CC-BY-NC **or** ODbL; the ODbL option requires publishing derived data [D8] |
| WorldPop | `WorldPop/GP/100m/pop` | 2000–2021, CC BY 4.0 [D9] |
| GHSL | `JRC/GHSL/P2023A/GHS_POP` | 1975–2030 at 100 m; also `.../GHS_BUILT_S` [D10] |
| Open Buildings v3 | `GOOGLE/Research/open-buildings/v3/polygons` | Covers South Asia, CC BY 4.0 [D11] |
| Satellite Embedding (AlphaEarth) | `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` | 2017–2024, 64 bands at 10 m, CC BY 4.0 [D12] |
| WeatherNext 2 | `projects/gcp-public-data-weathernext/assets/weathernext_2_0_0` | 64 members at 0.25°, 6-hourly, 15 days ahead, about 7.5 h latency [D13] |
| WeatherNext 3 (new flagship) | `projects/gcp-public-data-weathernext/assets/weathernext_3_0_0_0p1deg` (also a `_0p05deg` variant) | Mean and p10–p90 statistics, hourly [D14][W1] |
| IBTrACS | `NOAA/IBTrACS/v4` | Includes North Indian Ocean; the EE copy **ends 2024-05-19** [D15] |

**WeatherNext access and licence**
- Access is through the WeatherNext Data Request form. Approval is "typically 5–7 business days" [W2]. **Apply today:** approval would arrive around Oct 6, after submission closes.
- Historical data is CC BY 4.0. Real-time data falls under Google DeepMind's experimental terms and is described as intended for research [D13]. This is a licensing risk for operational government use.
- I found no cyclone-track product (UNVERIFIED), so tracks must be derived from the ensemble.

### 3. BigQuery [B1]
- **Free tier:** 1 TiB of queries and 10 GiB of storage a month.
- **On-demand queries:** $6.25 per TiB. Minimum 10 MB billed per table referenced, and `LIMIT` does not reduce bytes billed.
- **Storage:** active about $0.023 per GiB-month, long-term about $0.016.
- **Storage Write API (gRPC):** first 2 TiB a month free, then $0.025 per GiB.
- **GIS:** ST_* functions (buffer, union_agg, intersects, dwithin, area, clusterdbscan) plus S2 cells and the raster function `ST_REGIONSTATS` [B4].
- **AI.GENERATE** [B3]
  - Default model is `gemini-2.5-flash`; Gemini 3.1 through 3.8 Flash variants are also supported.
  - Can run with end-user credentials (no connection) or through a connection.
  - The 3.x models only have multi-regional endpoints (US or EU), which matters for data residency.
  - Cost is BigQuery bytes processed plus Vertex batch pricing for Gemini [B1].
- **AI.FORECAST** [B2]
  - Default model is TimesFM 2.5; TimesFM 3.0 is in preview.
  - Horizon is 1–10,000 steps (1–1,024 for 3.0).
  - Billed at the prediction rate, $6.25 per TiB. TimesFM 3.0 moves to token pricing on 2026-12-01.
- **WeatherNext 3 in BigQuery:** available through an Analytics Hub listing, with tables `weathernext_3_0_0_0p1deg` and `_0p05deg` [W2]. Query costs are billed to whoever runs the query [B1].
- **OSM public dataset:** `bigquery-public-data.geo_openstreetmap` has **not been updated since Nov 2021** [B5]. Load a current OSM extract yourself.

### 4. Firebase [F1]
- **Firestore free quota:** 1 GiB, 50k reads / 20k writes / 20k deletes per day, and 10 GiB egress a month.
  - Paid (default region): $0.03 per 100k reads, $0.09 per 100k writes, $0.01 per 100k deletes [F2]. Mumbai prices load dynamically on the page (UNVERIFIED).
  - **Named databases get no free quota** [F2].
  - A real-time listener is billed one read per document added or changed. After a disconnect of more than 30 minutes, it re-reads the whole query [F2].
- **Concurrent listeners:** no hard limit is published on the current quotas page [F6]. Older docs cited 1M connections (UNVERIFIED). Google's scaling guide covers "hundreds of thousands of concurrent users" and the 500/50/5 ramp-up rule [F3][F4].
- **Hosting:** 10 GB storage and 360 MB/day transfer free, then $0.026/GB storage and $0.15/GB transfer.
- **App Hosting (Blaze plan):** $0.20/GiB uncached and $0.15/GiB cached egress; 5 GB storage free, then $0.10/GB.
- **FCM and App Check:** free [F1].
- **Auth:** free up to 50k MAU, then $0.0055 per MAU (50k–100k) and $0.0046 (100k–1M). Anonymous users count unless automatic clean-up is on [F5].
  - **Phone OTP to India costs $0.07 per SMS**, with the first 10 SMS a day free [F5].
- **App Check with reCAPTCHA Enterprise:** 10k assessments a month free per organisation, $8 flat for 10k–100k, then $1 per 1k [C15].
- **Cloud Storage for Firebase:** free quotas only apply to buckets in us-central1, us-west1 and us-east1 [F1].

### 5. Cloud Run and platform services
- **Cloud Run free tier** (request-based billing): 180k vCPU-seconds, 360k GiB-seconds and 2M requests a month [C1].
  - After that: $0.000024 per vCPU-second, $0.0000025 per GiB-second, $0.40 per 1M requests.
  - An idle minimum instance costs $0.0000025 per vCPU-second, so 1 vCPU with 0.5 GiB kept warm is about **$9.7 a month**.
  - asia-south1 (Mumbai) is a Tier 1 price region; asia-south2 (Delhi) is Tier 2 [C1].
- **Concurrency:** up to 1,000 requests per instance. The default is 80 per vCPU from the CLI, or 80 from the console [C3].
  - The quotas page lists **100 maximum instances per project and region** (can be raised) and a 60-minute request timeout [C2].
  - Cold starts: keep 1–2 minimum instances during demo windows.
- **Cloud Run functions (1st gen):** 2M invocations, 400k GB-seconds and 5 GB egress free [C4].
- **Cloud Storage:** 5 GB-month free, **US regions only**. Standard storage is about $0.020 per GiB-month (default region); Class B operations cost $0.0004 per 1k [C4][C8].
- **Internet egress** (Premium tier, to Asia): $0.12/GiB for 1 GiB–1 TiB [C6].
- **Cloud CDN:** cache egress to APAC is $0.09/GiB up to 10 TiB, then $0.06. Cache lookups are $0.0075 per 10k [C5]. The global load balancer forwarding rule adds $0.025/hour, about **$18 a month** [C7].
- **Messaging and scheduling:**
  - Pub/Sub: first 10 GiB a month free, then $40/TiB [C9].
  - Cloud Tasks: first 1M operations free, then $0.40 per 1M [C10].
  - Scheduler: 3 jobs free, then $0.10 per job a month [C11].
- **Secret Manager:** 6 secret versions and 10k access operations free [C12].
- **API Gateway:** first 2M calls free, then $3 per 1M [C14].
- **Memorystore:** **not needed.** A Basic M1 instance costs about $0.049/GiB-hour, roughly $36 a month for 1 GiB [C13]. The CDN plus in-instance caching is enough.

### 6. Cost safety
- **Budgets:** an alerts-only budget "doesn't automatically cap" Cloud or Maps spending, and billing data arrives with a delay [S1].
- **Spend-cap budgets (preview):** they pause new usage of **Gemini API, Vertex AI (now Gemini Enterprise Agent Platform), Cloud Run and Cloud Run functions** in one project [S2].
  - Maps, BigQuery and Firestore are not covered.
  - Enforcement is not instant and any overage is still billed.
  - **Enable spend caps on Gemini and Cloud Run.**
- **Kill switch:** a budget notification on Pub/Sub can trigger a function that detaches the billing account. This stops everything, including free-tier services, and resources may be deleted [S3]. Use it only on a sacrificial demo project.
- **Hard ceilings:**
  - Per-API requests-per-day quotas on every Maps SKU [M9].
  - BigQuery custom daily query quota and `maximum_bytes_billed` (UNVERIFIED setting names).
  - Cloud Run `max-instances`.
  - EE cost controls on daily EECU time [E3].
- **Abuse control:** referrer-restricted keys, App Check, and Cloud Armor rate-limit rules on the load balancer (UNVERIFIED pricing) or API Gateway keys. Throttle each user in the app itself.

### 7. Serving 10,000 concurrent users with flat cost and latency
1. **Precompute everything slow.** EE batch exports to Cloud Storage, a road-graph access analysis job, and Gemini advisories generated per district × language × forecast cycle, with human approval. Cloud Scheduler triggers these as Cloud Run jobs through Pub/Sub. Viewing costs then do not grow with the number of users.
2. **Serve statically from the CDN.** Use PMTiles/COG layers and versioned scenario JSON with immutable URLs, plus a `latest.json` pointer with a 60 s TTL.
   - Budget: about 5 MB per user per session, so 10k users is about 50 GB, about **$4.50 per 10k-user wave** at $0.09/GiB [C5].
3. **Keep the Cloud Run API thin.** At 10k users × 1 request per 15 s, that is about 670 requests/s. At 100 ms each, about 67 are in flight, which is **1–2 instances at concurrency 80**. Even 10× that load needs about 9 instances, well under the 100-instance quota [C2][C3].
4. **Firestore for the live parts only.** Keep one small `alerts/{district}` document per district. One update read by 10k listeners costs 10k reads, **$0.003** [F2].
5. **Use Maps JS for the basemap, not the Map Tiles API.** 10k map loads fit within India's 70k free monthly cap. Fetching raw 2D tiles would hit the 15k/day quota [M3][M10].
6. **Keep EE, BigQuery and Gemini out of the request path.** EE allows only 40 concurrent interactive requests [E3].
7. Load-test with an open-source tool such as k6 or Locust (cite it as reused OSS).

### 8. Cost estimates (asia-south1, India Maps pricing, USD per month)

**Prototype**

| Item | Cost |
|---|---|
| 20k map loads, 5k geocodes, 2k Route Matrix elements | $0, all within India's 70k caps. At global pricing the map loads alone would be $70 |
| Firestore 500k reads / 100k writes | $0, or about $0.14 if the reads all land on one day |
| Cloud Run, 1M requests | $0–2, or +$10 with one warm minimum instance |
| Cloud Storage, 50 GB | about $1 |
| Egress, 200 GB | Firebase Hosting about $28; Cloud CDN plus load balancer about $36; direct egress about $24 |
| BigQuery, 2 TB scanned | about $5 |
| Earth Engine (noncommercial) | $0 |
| **Total** | **about $30–50** |
| Optional: Gemini 3.7 Flash, 20k calls × 3k in / 0.5k out tokens | about $83 on the paid tier [G1] |

**Assumptions per MAU per month**
- 4 sessions and 4 Maps JS loads.
- 1 geocode and 1 route.
- 200 Firestore reads and 5 writes.
- 100 Cloud Run requests.
- 20 MB of static egress.
- 2 Gemini calls (3k tokens in, 0.5k out), which is $0.00825 per MAU at 2026 prices.
- Only officials sign in; citizens use the app without an account.

| Service | 1k MAU | 10k MAU | 100k MAU | 1M MAU | Class |
|---|---|---|---|---|---|
| Dynamic Maps | 0 | 0 | 693 | 8,253 | FREE → EXPENSIVE |
| Geocoding + Routes | 0 | 0 | 90 | 2,790 | FREE → MODERATE |
| Firestore | 0 | ~0 | 6 | 64 | VERY LOW |
| Cloud Run (incl. 1 min instance) | 10 | 10 | 15 | 70 | VERY LOW |
| CDN / Hosting egress (+ load balancer + lookups) | 1 | 28 | 245 | 1,900 | MODERATE |
| Cloud Storage | 1 | 1 | 2 | 4 | VERY LOW |
| BigQuery (2 / 3 / 5 / 10 TB scanned) | 5 | 11 | 22 | 51 | VERY LOW |
| Earth Engine, commercial Limited (100–1,000 EECU-h) | 40 | 80 | 200 | 400 | MODERATE (FREE if noncommercial) |
| Gemini, called per user | 8 | 83 | 825 | 8,250 | EXPENSIVE; **doubles on 1 Jan 2027** |
| Pub/Sub, Tasks, Scheduler, Secret Manager, FCM | 0 | 0 | 0 | ~1 | FREE |
| **Total** | **~65** | **~215** | **~2,100** | **~21,800** | |

**Optimised design, about $0.7k at 100k MAU and $3–4k at 1M MAU:**
- Cache advisories per district, so Gemini stays flat at about $200–300.
- Call geocoding and routing only when the user asks for it.
- Use an own OSM vector-tile basemap for the public view. Maps terms may restrict showing Google content on non-Google maps (UNVERIFIED), so check before mixing.

**Top 3 cost drivers**
1. Gemini tokens when generated per user. The price rises from $0.75/$3.75 to $1.50/$7.50 per 1M tokens from 2027-01-01 [G1].
2. Maps SKUs charged per user at 100k+ MAU. Deployments in other BRICS countries lose India pricing and pay about 3.3× for map loads [M1][M3][M4].
3. CDN egress plus per-request lookups for tiles.

**Billing traps**
- **Budgets do not cap spending** [S1].
- **Phone OTP:** $0.07 per SMS in India [F5], about $70k a month at 1M MAU.
- **Signed-in citizens:** Auth at 1M MAU is about $4.4k [F5], and reCAPTCHA-backed App Check at 1M+ assessments is about $1 per 1k [C15].
- **Map Tiles 2D:** 15k/day quota [M10].
- **Free tiers in US regions only:** Cloud Storage and Firebase Storage [C4][F1].
- **Firestore:** named databases get no free quota, and listener reconnects re-read the full query [F2].
- **Earth Engine:** a government pilot changes the licence to commercial [E2].
- **Data licences and freshness:** MERIT Hydro's licence is either non-commercial or share-alike [D8]. WeatherNext real-time data is under experimental terms [D13]. The BigQuery OSM and EE IBTrACS copies are out of date [B5][D15].
- **BigQuery:** minimum bytes billed and `LIMIT` not reducing cost, and the Gemini 3.x region restriction [B1][B3].

### Sources (all opened)
- **M1** https://developers.google.com/maps/billing-and-pricing/pricing
- **M2** https://developers.google.com/maps/billing-and-pricing/march-2025
- **M3** https://developers.google.com/maps/billing-and-pricing/pricing-india
- **M4** https://developers.google.com/maps/billing-and-pricing/india
- **M5** https://developers.google.com/maps/documentation/routes/route-modifiers
- **M6** https://developers.google.com/maps/documentation/weather/overview
- **M7** https://developers.google.com/maps/documentation/weather/coverage
- **M8** https://developers.google.com/maps/api-security-best-practices
- **M9** https://developers.google.com/maps/billing-and-pricing/manage-costs
- **M10** https://developers.google.com/maps/documentation/tile/usage-and-billing
- **M11** https://developers.google.com/maps/documentation/javascript/usage-and-billing
- **E1** https://cloud.google.com/earth-engine/pricing
- **E2** https://earthengine.google.com/noncommercial/
- **E3** https://developers.google.com/earth-engine/guides/usage
- **E4** https://developers.google.com/earth-engine/guides/noncommercial_tiers
- **E5** https://developers.google.com/earth-engine/guides/service_account
- **E6** https://developers.google.com/earth-engine/guides/access
- **D1–D15** https://developers.google.com/earth-engine/datasets/catalog/ followed by: `NASA_GPM_L3_IMERG_V07`, `ECMWF_ERA5_LAND_HOURLY`, `COPERNICUS_S1_GRD`, `COPERNICUS_S2_SR_HARMONIZED`, `JRC_GSW1_4_GlobalSurfaceWater`, `COPERNICUS_DEM_GLO30`, `COPERNICUS_DEM_GLO30_2024_1`, `MERIT_Hydro_v1_0_1`, `WorldPop_GP_100m_pop`, `JRC_GHSL_P2023A_GHS_POP`, `GOOGLE_Research_open-buildings_v3_polygons`, `GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL`, `projects_gcp-public-data-weathernext_assets_weathernext_2_0_0`, `projects_gcp-public-data-weathernext_assets_weathernext_3_0_0_0p1deg`, `NOAA_IBTrACS_v4`
- **W1** https://developers.google.com/weathernext/guides/earth-engine
- **W2** https://developers.google.com/weathernext/guides/bigquery (also opened: https://developers.google.com/weathernext)
- **B1** https://cloud.google.com/bigquery/pricing
- **B2** https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-forecast
- **B3** https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/bigqueryml-syntax-ai-generate
- **B4** https://docs.cloud.google.com/bigquery/docs/reference/standard-sql/geography_functions
- **B5** https://wiki.openstreetmap.org/wiki/BigQuery_dataset
- **F1** https://firebase.google.com/pricing
- **F2** https://cloud.google.com/firestore/pricing
- **F3** https://firebase.google.com/docs/firestore/real-time_queries_at_scale
- **F4** https://firebase.google.com/docs/firestore/best-practices
- **F5** https://cloud.google.com/identity-platform/pricing
- **F6** https://firebase.google.com/docs/firestore/quotas
- **C1** https://cloud.google.com/run/pricing
- **C2** https://docs.cloud.google.com/run/quotas
- **C3** https://docs.cloud.google.com/run/docs/about-concurrency
- **C4** https://docs.cloud.google.com/free/docs/free-cloud-features
- **C5** https://cloud.google.com/cdn/pricing
- **C6** https://cloud.google.com/vpc/network-pricing
- **C7** https://cloud.google.com/load-balancing/pricing
- **C8** https://cloud.google.com/storage/pricing
- **C9** https://cloud.google.com/pubsub/pricing
- **C10** https://cloud.google.com/tasks/pricing
- **C11** https://cloud.google.com/scheduler/pricing
- **C12** https://cloud.google.com/secret-manager/pricing
- **C13** https://cloud.google.com/memorystore/docs/redis/pricing
- **C14** https://cloud.google.com/api-gateway/pricing
- **C15** https://cloud.google.com/recaptcha/pricing
- **S1** https://docs.cloud.google.com/billing/docs/how-to/budgets
- **S2** https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps
- **S3** https://docs.cloud.google.com/billing/docs/how-to/disable-billing-with-notifications
- **G1** https://ai.google.dev/gemini-api/docs/pricing