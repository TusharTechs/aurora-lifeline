# Costs: the US$150 budget and cost controls

On 28 Sep 2026 the owner approved **US$150** on their Google Cloud account for this project. They have also offered to fund extra costs if needed; the approval rules in §1a still apply.

Estimated need through Demo Day (23 Oct) is **about US$50–100**. Prices were read from official pages on 27 Sep 2026; re-check them before large jobs.

## 1. Allocation through 23 Oct

| Item | What it covers | Cap (US$) |
| --- | --- | --- |
| Gemini (all models, via Agent Platform) | Bulletins, advisories, field verification, back-translation, evaluation sets, Ask AURORA; demo outputs cached | 40 |
| Cloud Run services and jobs | API (2 GiB), graph builds, storm runs, backtests; one warm API instance 1–23 Oct at 1 vCPU / 2 GiB (about US$15 at idle min-instance rates; re-check on the pricing page) | 30 |
| Firebase Hosting egress | Judges' traffic plus one load test of 10 minutes or less (~50 GB at US$0.15/GB) | 15 |
| BigQuery | Partitioned and clustered; `maximum_bytes_billed` on every query | 10 |
| Cloud Storage | Raw data, run outputs, media (Mumbai; the free tier is US-only) | 3 |
| Firestore `(default)` | Live state, deltas, audit | 2 |
| Cloud Build, Artifact Registry | Container builds (free-tier amounts UNVERIFIED) | 2 |
| Cloud Text-to-Speech (Gemini-TTS) | Demo voice notes, cached | 1 |
| Maps JavaScript API | India pricing: 70,000 free loads a month; quota set at 2,000 a day | 0 |
| Earth Engine | Noncommercial Community tier (150 EECU-hours a month), registered as an individual. **Eligibility is UNVERIFIED** (see §4) | 0 |
| WeatherNext, Weather Lab, Flood Hub API | Free after the access request or waitlist | 0 |
| **Reserve** | Re-runs, an Earth Engine Limited-plan fallback if needed, Demo Day extras | 47 |
| **Total** | | **150** |

## 1a. Pre-approved services, and what still needs a yes

**Pre-approved by the owner on 28 Sep.** Enable these without asking further (all `.googleapis.com`):

- AI and compute: `aiplatform`, `run`, `cloudbuild`, `artifactregistry`
- Data: `storage`, `bigquery`, `bigquerystorage`, `firestore`
- Firebase: `firebase`, `firebasehosting`, `identitytoolkit`, `fcm`, `fcmregistrations`, `firebaseappcheck`
- Geo and speech: `earthengine`, `texttospeech`, `maps-backend` (the Maps JavaScript API only)
- Security and identity: `apikeys`, `secretmanager`, `iam`, `iamcredentials`, `sts`, `cloudresourcemanager`, `serviceusage`
- Operations: `logging`, `monitoring`, `pubsub`, `eventarc`, `cloudscheduler`, `billingbudgets`

**Still needs a yes in chat:**

- any other service;
- any quota increase;
- min-instances outside the 1–23 Oct warm window;
- any single new cost over US$10, or a projected total over US$120;
- a **large job**, meaning any of:
  - an Earth Engine export estimated at more than 10 EECU-hours, or more than 25 queued tasks;
  - a BigQuery query over 20 GB scanned;
  - a Cloud Run job over 8 vCPU × 1 hour;
  - a Gemini batch over US$5;
- any AI Studio or Gemini Developer API billing (for example, pre-rendering TTS);
- `recaptchaenterprise` (App Check enforcement; free up to 10,000 assessments a month). Until approved, App Check runs in monitor-only mode.

## 2. Controls: set these before the first deploy

1. **Budget.** Set it in the billing account's own currency. It covers the whole project window, and tracks **gross** usage so alerts fire even while a credit is being consumed. CONFIRM the flags against the current gcloud reference.

   ```bash
   gcloud services enable billingbudgets.googleapis.com
   # BUDGET_AMOUNT must be in the billing account's currency: "150USD" for a USD account,
   # or the INR equivalent of US$150 (e.g. "<amount>INR") for an INR account. Never pass a bare number.
   gcloud billing budgets create --billing-account="$BILLING_ACCOUNT" --display-name="aurora-hackathon" \
     --budget-amount="$BUDGET_AMOUNT" --filter-projects="projects/$PROJECT_ID" \
     --credit-types-treatment=exclude-all-credits --start-date=2026-09-28 --end-date=2026-10-31 \
     --threshold-rule=percent=0.33 --threshold-rule=percent=0.67 --threshold-rule=percent=0.87 \
     --threshold-rule=percent=1.0 --threshold-rule=percent=0.9,basis=forecasted-spend
   ```

   Custom date ranges start at 00:00 US Pacific time. Budgets alert but do not cap spend.

2. **Spend caps** (Preview; for the Gemini API, Agent Platform and Cloud Run). Each cap covers one project and one service, uses gross estimated cost, and resets monthly on the 1st. Enforcement is not instant, and overage is billed. **Once a cap trips, all new usage of that service is blocked until the owner lifts it by hand.** So:
   - set small September caps, then October caps equal to the remaining allocation on 1 Oct;
   - give Cloud Run headroom of about 1.5× its allocation, so a trip cannot take down the judged API;
   - keep the judged replay fully static on Firebase Hosting;
   - the owner acts on the 50% and 80% cap emails.

   Docs: https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps
3. **Maps:**
   - Maps JavaScript API map loads capped at 2,000 a day.
   - The browser key restricted by HTTP referrer (the Hosting domains and localhost) and to the Maps JavaScript API.
   - All other Maps APIs disabled.
4. **Cloud Run:**
   - The API runs with `--max-instances=10 --concurrency=80 --memory=2Gi`.
   - Jobs run with parallelism of 4 or less and a 60-minute task timeout.
   - Min-instances is 0, except 1 for the API during 1–23 Oct.
5. **BigQuery:**
   - Every query sets `maximum_bytes_billed` (20 GB).
   - A per-user daily quota of 200 GB.
   - Partitioned and clustered tables.
   - No `SELECT *` on geometry tables.
6. **Gemini:**
   - Cache every demo output.
   - Use Flash-Lite for bulk work, and `thinking_level` low or medium.
   - Set a **generous** `max_output_tokens` ceiling (16,384; it includes thinking tokens, and a small cap truncates responses while still billing them).
   - The Batch API for evaluation sets.
   - At most 5 tool calls per agent turn.
   - Never call Gemini per viewer.
7. **Hosting:**
   - Immutable, versioned static files cached for a year.
   - Default-zoom layers at 5 MB or less per district.
   - The load test capped at 10 minutes.
8. **Avoid:**
   - a Cloud CDN load balancer (about US$18 a month fixed; Firebase Hosting's CDN is enough);
   - Memorystore, Cloud NAT, static IPs, GPUs, VMs;
   - Next.js SSR through Firebase framework deploys, which creates Cloud Functions;
   - AI Studio billing without approval.
9. **Kill switch (optional):** a budget → Pub/Sub → function that detaches billing, only on a separate throwaway project.
10. **Weekly:** check the billing report and record the spend in `docs/HANDOFF.md`.

## 3. Costs outside Google Cloud

| Item | Needed? | Estimate |
| --- | --- | --- |
| SMS/IVR provider trial (Demo Day) | Optional | US$0–20 after any trial credit (India rates UNVERIFIED) |
| Custom domain | Optional; `*.web.app` is fine | about US$10 a year |
| Anything else | No | — |

## 4. Earth Engine eligibility

The noncommercial page does not cover hackathons. Prize money may count as compensation, and the product targets a government pilot. The owner answers the registration questionnaire truthfully.

**If the project is not eligible:**

- the **Limited plan** at US$0.40 per EECU-hour (about US$60 for 150 EECU-hours), paid from the reserve with owner approval; or
- the direct Copernicus and NASA downloads in `docs/BUILD_PLAN.md` "If blocked".

A government pilot needs a commercial plan in any case: Limited, or Basic at US$500 a month.

## 5. After the hackathon (only if a pilot happens)

- An Earth Engine commercial licence (as in §4).
- SMS and IVR costs at a state gateway.
- Production cost is about US$0.7–1k a month at 100,000 monthly users and US$3–4k at 1 million, with the precompute design (`docs/BLUEPRINT.md`).
- Gemini list prices double on 1 Jan 2027.

## 6. Credit caveats

- If the US$150 is a free-trial credit, it covers most Google Cloud services, including Agent Platform. Maps Platform coverage is UNVERIFIED.
- India Maps pricing needs billing and most usage to be in India. Confirm the billing account's country and currency.
