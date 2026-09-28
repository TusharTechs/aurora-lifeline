# Google AI services for AURORA / Demand Atlas (checked 2026-09-27)

Keys in brackets like [P] point to the source list at the end. I opened every source on 2026-09-27. **UNVERIFIED** means I could not confirm the claim on a primary page. Prices are USD on the paid tier of the Gemini Developer API unless marked otherwise.

## 0. Headlines
- **`gemini-3.7-flash` exists.** It became generally available (GA) on 13 Aug 2026 with a stable ID.
  - Price: $0.75 in / $3.75 out per 1M tokens until 31 Dec 2026, then $1.50 / $7.50 [CL][P][M37].
  - `gemini-3.8-flash` (GA 2 Sep 2026) costs the same and can replace it without code changes [CL][M38].
  - Use 3.7 Flash so the submission matches the Track 05 wording.
- **Vertex AI has been renamed "Gemini Enterprise Agent Platform".** Google announced this on 23 Apr 2026 [BLOG], and the old Vertex AI URL now redirects to a page titled "(formerly Vertex AI)" [GEAP]. Agent Engine is now called **Agent Runtime** [BLOG].
- **Vertex AI Vision shuts down on 30 Sep 2026.** It was deprecated on 15 Jun 2026 [VIS]. Don't cite it.
- **For the live demo, billing limits are a bigger risk than model price.**
  - On AI Studio Tier 1 you can spend at most $10 in any 10-minute window and $250 a month.
  - If the prepaid balance hits $0, every API key on that billing account starts returning HTTP 402 errors [RL][BILL].
- **Indian-language coverage differs a lot between services** (full table in section 3–5):
  - Gemini Live covers all 12 target languages.
  - Gemini 3.8 TTS covers 11; Urdu is not listed.
  - Cloud Chirp 3 speech-to-text is GA only for Hindi. The other languages are Preview, and it runs only in the `us` and `eu` regions.
  - Chirp 3 HD text-to-speech has no Odia and no Assamese.

## 1. Gemini models

| Model | ID | Status | Context in/out (tokens) | Paid $ per 1M tokens, in/out | Batch price | Free tier |
|---|---|---|---|---|---|---|
| 3.8 Flash | `gemini-3.8-flash` | GA 2 Sep 26 | 1,048,576 / 65,536 | 0.75 / 3.75 (1.50 / 7.50 from 1 Jan 27) | 0.375 / 1.875 | Yes |
| 3.7 Flash | `gemini-3.7-flash` | GA 13 Aug 26 | 1,048,576 / 65,536 | same as 3.8 | same | Yes |
| 3.6 Flash | `gemini-3.6-flash` | GA 21 Jul 26 | – | same | same | Yes |
| 3.5 Flash | `gemini-3.5-flash` | GA 19 May 26 | – | 1.50 / 9.00 | 0.75 / 4.50 | Yes |
| 3.5 Flash-Lite | `gemini-3.5-flash-lite` | GA 21 Jul 26 | 1M / 65,536 | 0.30 (any input type) / 2.50 | 0.15 / 1.25 | Yes |
| 3.1 Flash-Lite | `gemini-3.1-flash-lite` | GA 7 May 26 | UNVERIFIED | 0.25 (audio 0.50) / 1.50 | 0.125 / 0.75 | Yes |
| 3.1 Pro | `gemini-3.1-pro-preview` | **Preview** | 1M / 65,536 | 2 / 12 up to 200k tokens; 4 / 18 above | 1 / 6 | **No** |
| 3.8 Live (voice) | `gemini-3.8-live`, also `-extended-thinking` | GA 15 Sep 26 | 131,072 / 65,536 | text 0.75 / 4.50; audio 3 (about $0.005/min) / 12 (about $0.018/min) | – | Yes |
| 3.5 Transcribe | `gemini-3.5-transcribe` | GA 26 Aug 26 | – | about $0.003/min in + $0.002/min out | – | Yes |
| 3.8 Flash TTS | `gemini-3.8-flash-tts` | GA 22 Sep 26 | – | 0.50 text in / 9.00 audio out (about $0.0135 per min of audio) | 0.25 / 4.50 | Yes |
| 3.8 Flash-Lite TTS | `gemini-3.8-flash-lite-tts` | GA 22 Sep 26 | – | 0.50 / 6.00 (about $0.009 per min of audio) | 0.25 / 3.00 | Yes |
| Embedding 2 | `gemini-embedding-2` | GA 22 Apr 26 | 8,192 tokens in; 3072 dimensions, can shrink to 768/1536 | text 0.20, image 0.45, audio 6.50, video 12 | 50% off | Yes |
| Image generation | `gemini-3.1-flash-image`, `-lite-image`, `gemini-3-pro-image` | GA | – | about $0.067 / $0.034 / $0.134 per 1K image | 50% off | No |

Sources for the table: [P][CL][M37][M38][MFL][MPRO][MLIVE][EMB]. The models page still lists `gemini-embedding-2-preview`, but pricing and the changelog use `gemini-embedding-2`, so use that ID. Since 18 Sep 2026, Gemini 2.5 models are open only to projects that already used them [CL].

**Features**
- **3.7 Flash, 3.8 Flash and 3.5 Flash-Lite support all of these** [M37][M38][MFL]:
  - Inputs: text, image, video, audio and PDF.
  - Structured output against a JSON Schema, including `anyOf` and `enum` [SO].
  - Function calling.
  - Grounding with Google Search and with Google Maps.
  - Code execution, URL context and file search.
  - Caching.
  - Batch, Flex and Priority modes.
- **The Live model** supports function calling and Search grounding. It does not support structured output, caching, code execution or Maps grounding [MLIVE].
- **Thinking** is set with `thinking_level`, and thinking tokens are billed as output [P][TH]:
  - 3.7 and 3.8 Flash: default is medium; you can choose low, medium or high. "minimal" returns an error.
  - 3.5 Flash-Lite: default is minimal.
  - 3.1 Pro: default is high.
- **Deprecated parameters:** `temperature`, `top_p` and `top_k` were deprecated in July 2026. Remove them from configs [CL][LM].
- **Google Search grounding:**
  - Works in every language the model supports [GS].
  - The first 5,000 queries a month are free, shared across all Gemini 3.x models. After that it costs $14 per 1,000.
  - You pay for each search the model runs, not for each prompt [P][MAPS].
- **Google Maps grounding** handles English prompts and responses only [MAPS].
- **Code execution** is billed at normal token rates [P].
- **Caching:**
  - Automatic ("implicit") caching is on by default, but only for prompts of at least 4,096 tokens on 3.x models [CACHE].
  - Cached input costs 10% of the normal input price.
  - Storage for explicitly created caches costs $0.50 per 1M tokens per hour [P].
- **Batch** gives 50% off with a 24-hour target turnaround [BATCH]. Flex costs the same as Batch, and Priority about 1.8× standard [P].
- **Token cost of media on Gemini 3** [MR]:
  - Image: 1,120 tokens by default.
  - PDF: 560 tokens per page at medium resolution, plus the page's text.
  - Video: 70 tokens per frame.
  - Audio: 25 tokens per second.
- **Free tier:**
  - Free-tier data is used to improve Google products; paid-tier data is not [P].
  - Google no longer publishes per-model request limits (per minute or per day) in its docs. They are shown only inside AI Studio [RL].
  - A third-party site reports about 20 requests/day for 3.x Flash and 500/day for Flash-Lite (UNVERIFIED) [SBA].
  - Pro has no free tier.
- **Countries:** the Gemini API is available in India, Brazil, South Africa, Egypt, Ethiopia, the UAE, Saudi Arabia and Indonesia. China, Russia and Iran are not on the list [REG], so the BRICS design needs an open-model fallback (Gemma).

## 2. Agent Platform (formerly Vertex AI)
- **Rename confirmed.** Google describes Agent Platform as the "evolution of Vertex AI", and all Vertex AI services now ship through it [BLOG]. The API endpoint is still `aiplatform.googleapis.com` [LOC].
- **Gemini prices:** the same as the Developer API on the global endpoint. Regional endpoints cost 10% more; for 3.7 Flash that is $0.825 in / $4.125 out [GENP].
- **ADK (Agent Development Kit):** free and open source. It was upgraded with graph-based multi-agent support [BLOG]. The latest release is `adk-python` v2.10.0 (25 Sep 2026), Apache-2.0 licence [ADK].
- **Agent Runtime pricing** [GEAPP]:
  - Compute: $0.085 per vCPU-hour; first 50 vCPU-hours each month free.
  - Memory: $0.009 per GiB-hour; first 100 GiB-hours free.
  - Storage: $0.30 per GiB-month; first 1 GiB free.
  - Sessions and Memory Bank have been billed since 1 Sep 2026.
- **Throughput for Flash models on the standard pay-as-you-go plan** [PAYGO]:
  - Guaranteed baseline for your whole organisation is 2M tokens per minute at Tier 1 (spend of $10 to $250 in 30 days), 4M at Tier 2 and 10M at Tier 3.
  - Traffic above the baseline is served only when capacity allows.
- **Vertex AI Vision** shuts down on 30 Sep 2026 [VIS].
- **AutoML** for images and tables is still offered and priced [GEAPP][AML]. AutoML Text and AutoML Video were shut down in 2025 [DEP].
- **Free credits:** new customers get up to $300 [GEAP][FREE]. On AI Studio's prepaid billing you must buy at least $5 of credit before those free Cloud credits can be spent on the Gemini API [BILL].
- **Mumbai region (`asia-south1`) for Gemini 3.x: UNVERIFIED.** The region table on the page loads in the browser and I could not read it [LOC].

## 3–5. Speech, voice and translation by language

| Language | Chirp 3 speech-to-text [C3] | 3.5 Transcribe [TRN] | Live API [LIVE] | Chirp 3 HD text-to-speech [C3HD] | Cloud Gemini-TTS [GTTS] | Gemini API 3.8 TTS [TTSG] | Translation LLM [TRL] |
|---|---|---|---|---|---|---|---|
| Hindi | **GA** | ✔ | ✔ | ✔ | GA | ✔ | Official |
| Bengali | Preview | ✔ | ✔ | ✔ | GA (Bangladesh variant only) | ✔ | Official |
| Telugu | Preview | ✔ | ✔ | ✔ | GA | ✔ | Official |
| Tamil | Preview | **✗** | ✔ | ✔ | GA | ✔ | Official |
| Odia | Preview | ✔ | ✔ | **✗** | Preview | **✔** | Experimental |
| Marathi | Preview | ✔ | ✔ | ✔ | GA | ✔ | Official |
| Kannada | Preview | ✔ | ✔ | ✔ | Preview | ✔ | Official |
| Malayalam | Preview | ✔ | ✔ | ✔ | Preview | ✔ | Official |
| Gujarati | Preview | ✔ | ✔ | ✔ | Preview | ✔ | Official |
| Punjabi | Preview | ✔ | ✔ | Preview | Preview | ✔ | Official |
| Assamese | Preview | ✔ | ✔ | **✗** | ✗ | ✔ | ✗ (standard translation model only) |
| Urdu | Only in the region table, not on the Chirp 3 page (UNVERIFIED) [STTL] | ✗ | ✔ | ✔ (India variant) | Preview (Pakistan variant) | ✗ | Official |

**Speech-to-text**
- **Chirp 3 regions:** only the `us` and `eu` multi-regions, both GA.
  - **Mumbai (`asia-south1`) has no Chirp model.** Its only speech-to-text offering is US English for short phone calls [C3][STTL].
- **Chirp 3 price** (Speech-to-Text V2) [STTP]:
  - $0.016 per minute for the first 500k minutes a month, falling to $0.004 above 2M minutes.
  - Dynamic batch costs $0.003 per minute.
  - UNVERIFIED: whether Chirp 3 is billed at this standard rate. The pricing footnote names "chirp" but not "chirp_3".
- **Gemini alternatives:**
  - 3.5 Transcribe: about $0.005 per minute in total. It covers 85+ languages and supports speaker separation and a custom vocabulary of up to 1,000 terms [CL][TRN].
  - Transcribe Live (streaming): about $0.009 per minute [P].
  - Sending raw audio to 3.7 Flash: about $0.0011 per minute of input, plus output tokens [P][MR].
- **Live API:**
  - Supports 99 languages, including all 12 above [LIVE].
  - Costs $0.005 per minute of audio in and $0.018 per minute of audio out [P].
  - Audio sessions end after 15 minutes and connections after about 10 minutes unless you turn on context compression and session resumption [LSESS].
  - Live Translate (Preview) covers 70+ languages [P].

**Text-to-speech**
- **Prices:**
  - Chirp 3 HD: $30 per 1M characters after 1M free characters each month [TTSP].
  - Cloud Gemini-TTS (2.5 Flash): $0.50 per 1M text tokens in and $10 per 1M audio tokens out, with no free tier [TTSP].
  - Gemini API 3.8 Flash-Lite TTS: about $0.009 per minute of audio, with a free tier [P].
- **Rough comparison:** if speech runs at about 15 characters a second (my assumption), 1M characters costs about $30 on Chirp 3 HD and about $10 on 3.8 Flash-Lite TTS.
- **Recommendation:**
  - Use `gemini-3.8-flash-lite-tts` for 11 languages, including Odia, Telugu, Bengali and Tamil.
  - Use Chirp 3 HD's India Urdu voice for Urdu.
  - Note that Cloud Gemini-TTS has no India region [GTTS].

**Translation**
- **Standard neural translation (Translation API v3)** supports all 12 languages. It costs $20 per 1M characters, and the first 500k characters each month are free [TRP][TRL].
- **Translation LLM** costs $10 per 1M input characters plus $10 per 1M output characters. Adaptive translation costs $25 plus $25 [TRP].
- **Is Gemini alone good enough for reasoning in these languages?** This is my judgement; I found no official benchmark for Indian languages, so treat it as UNVERIFIED.
  - Flash should be adequate for the 10 major languages.
  - For safety advisories (the CAP alerts in AURORA), use fixed templates with a glossary through standard translation or Translation LLM. Add a back-translation check and human approval.
  - Odia and Assamese are the weakest. Test 50 samples per language before relying on them.

## 6. Dialogflow CX (now "Conversational Agents")
- **It is still a current product.** Dialogflow CX is now called Conversational Agents, with two editions: Flows (the former Dialogflow CX, rule-based) and Playbooks (generative) [DFP].
- **Pricing** [DFP]:

  | Edition | Chat | Voice |
  |---|---|---|
  | Flows | $0.007 per request | $0.001 per second ($0.06/min) |
  | Playbooks | $0.012 per request | $0.12/min |

  - New users get $600 (Flows) or $1,000 (Playbooks) in credits, valid for 12 months.
- **Verdict: skip it for the hackathon.**
  - Gemini 3.8 Live costs at most about $0.023 per minute and covers all 12 languages.
  - A chain of 3.5 Transcribe, then Flash, then TTS is also cheaper than Conversational Agents.
  - Either route shows judges more Google AI doing meaningful work.
  - Consider Flows only if a ministry pilot needs a fixed phone menu. Its Indian-language coverage is UNVERIFIED.

## 7. Gemma (open models for offline use)
- **Gemma 3n** [GEMMA3N][GTERMS]:
  - Released 26 Jun 2025 in E2B and E4B sizes.
  - Runs on devices and accepts audio, images and text.
  - Covers 140+ languages with a 32K-token context.
  - Licence: the custom **Gemma Terms of Use**, which include a prohibited-use policy.
- **Gemma 4** [GREL][GEMMA4][GAPACHE]:
  - Released 31 Mar 2026 in E2B, E4B, 31B and 26B-A4B sizes; a 12B "Unified" model followed on 3 Jun 2026.
  - Context is 128K tokens on the small models and 256K on the medium ones.
  - Native audio on E2B, E4B and 12B, and function calling.
  - Licence: **Apache 2.0**.
- **Recommendation:**
  - Use Gemma 4 E4B for the offline field app.
  - Also use it for BRICS countries where the Gemini API isn't available [REG].
  - The Apache 2.0 licence makes the "cite reused OSS" rule easy to meet.

## 8. Which model for which job

| Task | Model | $ per 1M tokens, in/out | Note |
|---|---|---|---|
| (a) Bulk classification and extraction | `gemini-3.5-flash-lite`, minimal thinking, JSON schema | 0.30 / 2.50 (batch 0.15 / 1.25) | `gemini-3.1-flash-lite` is cheapest at 0.25 / 1.50 |
| (b) Image, PDF and video understanding | `gemini-3.7-flash`, PDFs at medium resolution | 0.75 / 3.75 | Agentic video mode uses up to 88% fewer tokens [CL] |
| (c) Complex reasoning and reports | `gemini-3.7-flash` on high thinking; `gemini-3.1-pro-preview` only for the final ministry report | 0.75 / 3.75; Pro 2 / 12 | Pro is Preview and has no free tier |
| (d) Real-time voice | `gemini-3.8-live` | audio 3 / 12 (about $0.005 / $0.018 per min) | Fallback: 3.5 Transcribe, then Flash, then TTS |
| (e) Embeddings and cross-lingual clustering | `gemini-embedding-2` at 768 dimensions | 0.20 (batch 0.10) | 100+ languages; 8,192-token limit; state the task in the input text, because the `task_type` setting isn't accepted [EMB] |
| (f) Batch jobs (backtests, GPDP ranking, bulletins) | Batch API on 3.5 Flash-Lite or 3.7 Flash | 50% off | Flex costs the same but returns immediately |
| Speech-to-text / text-to-speech | `gemini-3.5-transcribe` / `gemini-3.8-flash-lite-tts` | about $0.005 per min / 0.50 / 6.00 | Tamil speech: Live API or Chirp 3. Urdu voice: Chirp 3 HD |

## 9. Cost estimate

**Prototype, at 2026 prices**

| Item | Assumption | Cost |
|---|---|---|
| 2,000 Flash calls | 3.7 Flash; 6M tokens in, 1.6M out | $4.50 + $6.00 = **$10.50** |
| 300 image analyses | 1,620 tokens in, 500 out each | $0.92 |
| 50 PDFs of 10 pages | about 11,600 tokens in, 2,000 out each | $0.82 |
| 200 minutes of speech-to-text | Chirp 3 at $0.016/min | $3.20 (3.5 Transcribe: $1.00) |
| 100,000 characters of TTS | Chirp 3 HD, inside the free 1M | $0 (3.8 Flash-Lite TTS: about $1) |
| 20,000 embeddings | 4M tokens | $0.80 (batch: $0.40) |
| Search grounding | under 5,000 queries | $0 |

The prototype costs **about $16**, or about $25 if thinking tokens run 50% over. That is well inside the $300 credit.

**Monthly cost at scale.** Assumptions for each monthly active user (MAU):
- 20 AI calls a month:
  - 14 on Flash-Lite (1,500 tokens in, 300 out).
  - 5 on Flash (3,000 in, 800 out).
  - 1 image call on Flash (1,600 in, 500 out).
- 30% of input tokens are served from cache.
- 20 embeddings.
- 0.5 minutes of Chirp 3 speech-to-text.
- 1,000 characters of 3.8 Flash-Lite TTS, with half the audio reused because advisories go out to many people.
- 0.5 grounded searches.

| MAU | LLM | Speech-to-text | TTS | Search grounding | Embeddings | **Total, 2026 prices** | **Total, from Jan 2027** |
|---|---|---|---|---|---|---|---|
| 1,000 | $41 | $8 | $5 | $0 | $1 | **$55** | $81 |
| 10,000 | $411 | $80 | $51 | $0 | $8 | **$549** | $809 |
| 100,000 | $4,107 | $800 | $508 | $630 | $80 | **$6,125** | $8,722 |
| 1,000,000 | $41,073 | $8,000 | $5,076 | $6,930 | $800 | **$61,900** | $87,900 |

That is about $0.06 per user a month in 2026 and $0.09 from 2027.

**Biggest cost drivers**
1. Flash output tokens, including thinking. Keep thinking low and cap output length.
2. Speech-to-text minutes.
3. Search grounding beyond 5,000 queries a month.
4. The Flash price doubling on 1 Jan 2027.

**The most effective saving is to precompute results.** For AURORA, run the AI once per cyclone, district and language. The 10,000 concurrent viewers then read stored results from Firestore or a CDN instead of calling Gemini each time.

**Traps**
1. **AI Studio usage tiers** [RL][BILL]:
   - At Tier 1, 10,000 users each making one 3.7 Flash call within 10 minutes costs about $52. That is over the $10 per 10-minute limit, so requests would fail with "429 too many requests" errors.
   - Tier 2 allows $50 per 10 minutes. It needs $100 paid plus 3 days, so reach it before about 10 Oct.
   - Tier 3 needs $1,000 paid plus 30 days, which is too late for Demo Day on 23 Oct.
   - Agent Platform's guaranteed 2M tokens per minute is only about 500 of these calls a minute [PAYGO].
2. **Prepaid balance at $0:** every API key on the account returns 402, and the balance updates about 10 minutes late. Turn on auto-reload and set a monthly limit [BILL].
3. **Free tier:** reportedly about 20 requests a day on 3.x Flash (UNVERIFIED) [SBA]. Free-tier data is used by Google, so never send citizen voice recordings or personal data through it [P].
4. **Models change quickly:** Gemini 2.0 was shut down on 1 Jun 2026, and 2.5 was restricted on 18 Sep 2026 [CL]. Pin fixed model IDs rather than `-latest` names.
5. **API changes:**
   - The sampling parameters are deprecated.
   - The response format of the Interactions API (one of the Gemini API's two request APIs) changed in May 2026.
   - "minimal" thinking fails on 3.7 and 3.8 Flash [CL][TH].
6. **Grounding:** Maps grounding is English-only, and Search grounding is billed per search the model runs [MAPS][P].
7. **Data location:**
   - Chirp 3 runs only in the US and EU.
   - Cloud Gemini-TTS has no India region [C3][GTTS].
   - Gemini in Mumbai is UNVERIFIED.
   - This matters for the "pilot within a ministry" judging criterion.
8. **Caching:** automatic caching needs prompts of at least 4,096 tokens, so the assumed 3,000-token prompts won't be cached unless they share a longer common opening [CACHE].
9. **Live API sessions** end after 15 minutes of audio or about 10 minutes of connection, so build in session resumption [LSESS].

## Sources
- [P] https://ai.google.dev/gemini-api/docs/pricing
- [M] https://ai.google.dev/gemini-api/docs/models
- [M37] https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash
- [M38] https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
- [MFL] https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite
- [MPRO] https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview
- [MLIVE] https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live
- [CL] https://ai.google.dev/gemini-api/docs/changelog
- [RL] https://ai.google.dev/gemini-api/docs/rate-limits
- [BILL] https://ai.google.dev/gemini-api/docs/billing
- [TH] https://ai.google.dev/gemini-api/docs/thinking
- [CACHE] https://ai.google.dev/gemini-api/docs/caching
- [BATCH] https://ai.google.dev/gemini-api/docs/batch-api
- [SO] https://ai.google.dev/gemini-api/docs/structured-output
- [GS] https://ai.google.dev/gemini-api/docs/google-search
- [MAPS] https://ai.google.dev/gemini-api/docs/maps-grounding
- [MR] https://ai.google.dev/gemini-api/docs/media-resolution
- [EMB] https://ai.google.dev/gemini-api/docs/embeddings
- [TTSG] https://ai.google.dev/gemini-api/docs/speech-generation
- [LIVE] https://ai.google.dev/gemini-api/docs/live-api/capabilities
- [LSESS] https://ai.google.dev/gemini-api/docs/live-api/session-management
- [TRN] https://ai.google.dev/gemini-api/docs/transcribe
- [LM] https://ai.google.dev/gemini-api/docs/latest-model
- [REG] https://ai.google.dev/gemini-api/docs/available-regions
- [GEAP] https://cloud.google.com/products/gemini-enterprise-agent-platform
- [BLOG] https://cloud.google.com/blog/products/ai-machine-learning/introducing-gemini-enterprise-agent-platform
- [GEAPP] https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing
- [GENP] https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing
- [PAYGO] https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/standard-paygo
- [LOC] https://docs.cloud.google.com/gemini-enterprise-agent-platform/resources/locations
- [VIS] https://docs.cloud.google.com/vision-ai/docs
- [DEP] https://docs.cloud.google.com/vertex-ai/docs/deprecations
- [AML] https://docs.cloud.google.com/gemini-enterprise-agent-platform/machine-learning/beginner/beginners-guide
- [FREE] https://cloud.google.com/free
- [ADK] https://github.com/google/adk-python/releases
- [C3] https://docs.cloud.google.com/speech-to-text/docs/models/chirp-3
- [STTL] https://docs.cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages
- [STTP] https://cloud.google.com/speech-to-text/pricing
- [C3HD] https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd
- [GTTS] https://docs.cloud.google.com/text-to-speech/docs/gemini-tts
- [TTSP] https://cloud.google.com/text-to-speech/pricing
- [TRL] https://docs.cloud.google.com/translate/docs/languages
- [TRP] https://cloud.google.com/products/translate/pricing
- [DFP] https://cloud.google.com/products/conversational-agents/pricing
- [GEMMA3N] https://ai.google.dev/gemma/docs/gemma-3n
- [GEMMA4] https://ai.google.dev/gemma/docs/core
- [GREL] https://ai.google.dev/gemma/docs/releases
- [GTERMS] https://ai.google.dev/gemma/terms
- [GAPACHE] https://ai.google.dev/gemma/apache_2
- [SBA] https://www.scriptbyai.com/gemini-api-free-tier-limits/ (third-party site, not authoritative)