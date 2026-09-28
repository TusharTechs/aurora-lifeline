# Competitive-intelligence report: Build with AI: Code for Communities (read 2026-09-27)

**Bottom line:** Track 05 already has at least one public entry that does almost everything AURORA plans, and it has published satellite validation. Track 1 has the most entries by count, but only a few join citizen demand to official datasets the way Demand Atlas plans to.

## 1. First edition (June–July 2026, not 2025)

| Item | Finding | Source |
|---|---|---|
| Dates | Registration opened 17 Jun 2026 (the page says 22 Jun). Briefing/AMA 26 Jun. Registration and submission both closed 8 Jul (about 3 weeks to build). Mentor review 8–13 Jul, Top 40 announced 14 Jul, virtual finale 16 Jul, in-person demo day 22 Jul in New Delhi. | [page](https://hack2skill.com/event/codeforcommunities/), [API](https://hack2skill.com/api/v1/event/codeforcommunities/event-details) |
| Problem statements | 4 tracks, each submitted by an MP's office (six sitting MPs are quoted on the page; the Kisan Alert brief came from Narasaraopet constituency): T1 People's Priorities (constituency planning), T2 CleanAir & Clear Streets, T3 Smart Health (PHC/CHC), T4 Kisan Alert | same |
| Prizes | ₹10L pool. Per track: ₹1L / ₹75K / ₹50K (₹2.25L × 4 = ₹9L; the other ₹1L is not explained, UNVERIFIED). Pilot with the MP's office. GCP credits for shortlisted teams only. | same |
| Scale | 7,191 registrations (API tag). Press: 7,000+ developers, 18+ cities, 1,000+ open-source projects, 12 winners. GDG India says "1,000+ teams". | [API](https://hack2skill.com/api/v1/event/codeforcommunities/event-details), [FoneArena](https://www.fonearena.com/blog/488078/google-wraps-up-build-with-ai.html), [GDG India video](https://www.youtube.com/watch?v=eAD1epZJcGU) |
| Judging | Problem-Solution Fit 20, AI/Technical Execution 25 ("not decorative"), Deployability & Scalability 25, Inclusivity & Accessibility 15, Impact 10, Presentation 5 | [API](https://hack2skill.com/api/v1/event/codeforcommunities/event-details) |
| IP | "All rights related to the solutions stays with the participants" | same |
| Finale partner | The Dialogue co-organised the 22 Jul Parliamentary Showcase | [FoneArena](https://www.fonearena.com/blog/488078/google-wraps-up-build-with-ai.html) |

**Winning projects** ([FoneArena](https://www.fonearena.com/blog/488078/google-wraps-up-build-with-ai.html); stack details from GDG India videos [T1](https://www.youtube.com/watch?v=JRVivhLxR3w), [T2](https://www.youtube.com/watch?v=9HNmgINkFnU), [T3](https://www.youtube.com/watch?v=eAD1epZJcGU), [T4](https://www.youtube.com/watch?v=45oOY3VMpf0)):

| Track | Winner, what it does | 2nd / 3rd place |
|---|---|---|
| T1 | **Techjays, Praja Svaram.** Voice-first grievance intake over WhatsApp and phone. Gemini turns complaints into structured data, maps them to government schemes, removes duplicates, ranks by urgency and fits the list to what the MP's budget can pay for. Built by a Google Cloud premium partner company, so professional firms compete and win. | Civic Pulse: text/voice/photo in Indian languages plus hotspots. Nexons, AreaPulse: AR and WhatsApp reporting, spam/duplicate filter, SLA dashboards, weather-risk model. |
| T2 | **Code_smashers.** Delhi NCR hotspot map from CPCB sensors, satellite fire detections and Gemini analysis of citizen photos. Severity scores and multilingual audio summaries. Built on Gemini, Maps, Firebase and Project IDX. | WeBuild: AI checks on citizen reports, Speech-to-Text and Translation in 13 languages. GLM Harmonizers, CleaniSense: image validation and routing to the right department. |
| T3 | **Noida Boys, HealthGrid AI.** District health command centre covering stock, footfall, beds, doctor attendance and test availability. | GHC: unified admissions and inventory. ai-rangers: command centre plus a multilingual reporting app. |
| T4 | **Vishwakarma Devs, KisanVaani.** Toll-free voice and SMS, so no smartphone is needed. Photo diagnosis, and a priority ticket to officials when the AI can't answer. Gemini Flash, Speech-to-Text, Weather API. A team member tested it with a farmer in his village. | Rocket, Bhumija: GPS field insights. Sarkitects, Krishi Kalyan: Telegram assistant. |

**Why they won (inferred):** every winner reached users through low-tech channels (IVR, SMS, WhatsApp, Telegram), used Gemini multimodal for real work, gave officials a dashboard, used real public data, and could show some field validation. What the jury pushed back on is mentioned in the videos, but I couldn't get the transcripts: UNVERIFIED.

## 2. Second edition: extra details

| Item | Finding | Source |
|---|---|---|
| Slug and timeline | `codeforcommunities2`. Registration and submission end 2026-09-30 18:29 UTC (23:59 IST). **No extension** as of 27 Sep. Page quirks: the submission phase is listed as starting 10/08, a day before launch, and the Overview block still contains lorem-ipsum text. | [API](https://hack2skill.com/api/v1/event/codeforcommunities2/event-details) |
| Scale | **16,256 registrations** (hidden tag, about 2.3× the first edition), 145K impressions. If the first edition's ratio holds (about 1,000 teams from 7.2K registrations), expect roughly 2,000+ submissions. That is my estimate. | same |
| Prizes | "Cash prize pool: INR 10 lakhs". No per-track split is published. Third-party listings repeat the first edition's "₹2.25L per challenge", which would cost ₹11.25L across 5 tracks and exceed the pool, so that figure is probably stale (UNVERIFIED). Credits: "Top teams will receive Google Cloud credits"; no amount given. The page still carries the placeholder "Organizers: confirm Google AI Studio and Vertex AI credit details". | [API](https://hack2skill.com/api/v1/event/codeforcommunities2/event-details), [Internshala](https://internshala.com/competitions/build-with-ai-code-for-communities-hackathon-2026/) |
| Pilot | "Through official channels established with the government… evaluated for pilot deployment within relevant ministries". **No ministry is named.** No MeitY, IndiaAI or ministry press release found (UNVERIFIED). | same |
| Demo day | In-person demo day in "October", date and venue TBA. Virtual Demo Day 23 Oct. | same |
| Submission package | Public or access-granted GitHub repo, 3–5 min demo video, 10–12-slide deck, 2–3 line description, **live deployed link** | same |
| Explainer session (14 Aug) | No recording or content found on YouTube (Hack2skill or GDG India): UNVERIFIED. GDG skilling sprints taught Gemini, AI Studio, Firebase and Cloud Functions agent builds. | [GDG Ahmedabad](https://gdg.community.dev/events/details/google-gdg-ahmedabad-presents-code-for-communities-20-build-with-ai/) |
| Rubric changes from ed.1 | Deployability 25→20. Inclusivity 15 replaced by **Depth & Reach Across India 20**. Impact 10→15. Presentation 5 removed. The first edition's "rights stay with participants" line is **gone**. | both APIs |

**Is Track 05 sponsored?** No partner is named on the page. The track "Theme" labels (Innovation, Sustainability, Resilience, Cooperation) are the four pillars of **India's 2026 BRICS chairship** ([Tribune](https://www.tribuneindia.com/news/brics-expansion/brics-summit-2026-indias-chairship-centres-on-four-pillars-of-resilience-innovation-cooperation-and-sustainability)). Track 05 is the only track new in this edition; the other four are national-scale versions of the MP-sourced tracks. Its wording ("coastal APAC", "parametric insurance liquidity", "Gemini 3.7 Flash") suggests Google wrote it, but that is UNVERIFIED. Gemini 3.7 Flash is listed as stable, and so is the newer 3.8 Flash ([ai.google.dev](https://ai.google.dev/gemini-api/docs/models)).

**Key clauses of [hack2skill.com/legacy/tnc](https://hack2skill.com/legacy/tnc).** The event's own T&C field is hidden and empty, so whether this page applies is UNVERIFIED.
- **IP:** the organiser gets a **6-month right of first refusal** on any exclusive licence of the materials (30 days to match a third-party offer). It also gets a free, worldwide right to publish submitted ideas, and sponsors get a perpetual, non-exclusive licence for marketing content.
- **Originality:** the participant warrants they are the "sole author and copyright owner", with no third-party IP and no malware, and indemnifies the organiser.
- **AI-generated code:** no clause. The "sole author" warranty could be in tension with heavy AI-assisted generation (my inference).
- **Data:** "Data Security… as per IT Act 2008". Nothing more specific.
- **Disqualification:** third-party rights or law violations, objectionable content, leaving the official communication platforms, incomplete entries. The organiser can change the rules or prizes at any time.
- **Prizes:** paid within 60 days, after TDS.
- **Public voting:** none mentioned.
- **Conflict:** T&C team size is 2–6; the event page says 1–4.

## 3. Saturation (GitHub, as of 27 Sep)

Query: [`"code for communities" in:readme created:>2026-08-10`](https://api.github.com/search/repositories?q=%22code+for+communities%22+in:readme+created:%3E2026-08-10) returned **185 public repos** (many teams keep repos private until submission). I classified them by name and description:

| Track | ≈Repos | Dominant pattern |
|---|---|---|
| T1 DPI/Governance | **~50** (84 READMEs mention "citizen") | Voice/WhatsApp intake → Gemini classify and dedupe → hotspot map → ranked list. Lots of "CivicPulse/JanSetu/NagarVaani-BRICS" clones. |
| T4 Agri | ~27 | Leaf-photo diagnosis plus voice advisory, Soil Health Card plus satellite |
| T3 Health | ~25 | PHC stock/bed/staff dashboard, forecasting, redistribution. Voice-note reporting; one uses TimesFM, one uses ADK. |
| T2 Air | ~17 | Citizen photos + Sentinel-5P + CPCB fusion. One does leave-one-station-out validation on 86K CPCB station-days. |
| T5 Cyclone | ~10 mention C4C; **~20+ Track-05-shaped repos** in a [description search](https://api.github.com/search/repositories?q=cyclone+vulnerability+created:%3E2026-08-05) | IBTrACS + Open-Meteo + GEE + OSM infrastructure + Gemini advisory |

Languages: TypeScript 58, Python 54, JS 43. 28 of the READMEs mention Earth Engine and 31 mention BigQuery.

**Direct threats to AURORA** (README lines I read in the repos, found via the [search](https://api.github.com/search/repositories?q=%22code+for+communities%22+cyclone+in:readme+created:%3E2026-08-10)):
- **ShadowCast** (solo, Apache-2.0, live on Vercel plus Cloud Run) is close to AURORA end to end:
  - Holland wind at 15-minute steps, R-CLIPER rain, a 1D surge model against bare-earth DeltaDTM, and OSM arterial roads cut per IMD damage classes, with each shelter or hospital linked to its road.
  - A substation outage model learned from **VIIRS night-light loss** on Fani, reported ROC AUC 0.97 in-sample and 0.79 on Hudhud, with the failures (Amphan) published.
  - **ECMWF ensemble tracks replayed as issued** from `gs://ecmwf-open-data`, and WeatherNext 2 via Open-Meteo.
  - A Gemini agent reads IMD bulletin PDFs and drafts **CAP 1.2** in English, Hindi and the regional language, with **officer approval** and a Firestore audit log.
  - Parametric district triggers.
- **Cyclone AI Command Center**: GEE + OSM + IBTrACS + **HAND flood calibrated on Hudhud** + a damage model + Gemini action plans.
- **AeroRelief AI**: GEE Sentinel-1 SAR, parametric trigger, Odia alerts.
- Also SagarShield-AI, CycloneX, cycloneguard, CopperNick-Vision and others.

**Direct threats to Demand Atlas:**
- **civic-demand-intelligence**: Gemini need extraction → **LGD** resolution → deterministic lookups on JJM, Mission Antyodaya and Census in **BigQuery**, on Cloud Run.
- **JanSetu**: LGD coding, PMGSY routing and an "equity-constrained" budget portfolio.
- **pragatitrace**: complaints checked against PMGSY/JJM sanction orders.

GPDP/Gram Sabha/PAI appear in very few C4C repos. I found no public LinkedIn posts I could verify.

## 4. Winning patterns in comparable Google × Hack2Skill hackathons, 2024–2026

| Event | Scale / format | Rubric | Winners |
|---|---|---|---|
| Gen AI Exchange 2025 | 93K registrations on Hack2Skill ([API](https://hack2skill.com/api/v1/event/genaiexchangehackathon/event-details)). Press: 2.7L developers, 4,457 prototypes, top 100 at an in-person finale, 30-member jury. | Not published. Press says judges favoured production-readiness, explainability/auditability and public-sector scalability ([Outlook Business](https://www.outlookbusiness.com/artificial-intelligence/google-cloud-gen-ai-hackathon-2025-winners-use-cases-and-what-270000-developers-built)). | **One winner per problem statement** (10 for 10), including GovernAI, a dual-agent governance platform for the Maharashtra problem statement ([YourStory](https://yourstory.com/2025/12/google-cloud-gen-ai-exchange-hackathon-the-10-innovations-that-stood-out-this-year)) |
| Agentic AI Day 2025 | 57K registrations ([API](https://hack2skill.com/api/v1/event/googlecloudagenticaiday2025/event-details)), 9,100+ teams, 700 offline, 30-hour in-person build | Not published. Special prize for deploying with Firebase Studio. | Teacher assistant for multi-grade classrooms. A winning-team member's Medium write-up (URL withheld because it contains a personal name) credits research with 48+ teachers, "simple but scalable", offline-first, multilingual/multimodal, and clear storytelling. |
| Solution Challenge 2026 | 63.5K registrations ([API](https://hack2skill.com/api/v1/event/solution-challenge-2026/event-details)), top 106, mandatory deck template | Technical Merit 40, Cause Alignment 25, Innovation 25, UX 10 ([PromptWars](https://promptwars.in/solutionchallenge2026.html)) | Has **People's Choice** and **Best Usage of AI** awards (C4C has none published) |

**What winners had in common:**
1. A live deployed demo that works end to end.
2. Channels suited to low connectivity and low literacy.
3. Gemini doing essential work (multimodal checking, structuring, multilingual), not decoration.
4. Real public data plus some field validation.
5. A dashboard for the official, with a human escalation step.
6. A clear 5-minute story.

**Common failure modes** (inferred from the rubrics and press):
- "Decorative" AI.
- No deployed link.
- Scoped to a single city (the second-edition FAQ says this explicitly).
- Over-engineering.
- Cluttered pitch.
- Unverifiable metrics. Some Track 05 repos make bold claims such as "89.4% F1" and "BFT oracles", which is a credibility risk if judges probe them.

**What this means for the team:**
- In Track 05, AURORA's core pipeline is no longer different. To stand out it would need things ShadowCast lacks: population without power from Open Buildings, turn-by-turn access loss, HAND pluvial flooding, a load-tested 10K-user tier, and shown transfer to other BRICS coasts.
- Track 1 has the most entries by count, but most of them rank grievances. Demand Atlas's joins to official datasets are less crowded, though they are not unique.