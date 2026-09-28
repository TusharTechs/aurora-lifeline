# Research appendix

These are raw and semi-raw research outputs from 27–28 Sep 2026. Treat them as evidence to check claims against, not as instructions. Facts that could not be confirmed on a primary page are marked UNVERIFIED. Private individuals are not named.

| File | What it holds |
| --- | --- |
| `google-ai-services.md` | Gemini model lineup, prices, free-tier and billing traps, speech/TTS/translation language coverage, Agent Platform (formerly Vertex AI), ADK, Gemma, model routing, AI cost estimates |
| `google-cloud-maps-earthengine-costs.md` | Maps Platform India pricing, Earth Engine licensing, quotas and catalogue IDs, BigQuery, Firebase, Cloud Run, CDN, cost safety, the 10,000-user serving design, infrastructure cost tables |
| `data-sources-and-licensing.md` | Licence, access and commercial-use status for every dataset; minimum bundles; Survey of India, DPDP Act and ODbL legal notes |
| `hackathon-and-competitor-intel.md` | First-edition facts and winners, second-edition details, T&C clauses, GitHub saturation scan, winning patterns |
| `decision-panel.md` | The four-judge scoring of six finalists, the modifications each judge demanded, and red-team attacks on the top two, with competitor capability details |
| `verify-tech.md`, `verify-policy.md` | Adversarial fact-checks of load-bearing claims, with corrections |
| `cyclone-technical-notes.md` | Pain evidence, existing systems, method references, forecast data sources, parametric and BRICS context |

The full narrative blueprint, including tracks, the other tracks' ideas and the scoring, is in `../BLUEPRINT.md`.

**Where research advice conflicts with `CLAUDE.md`, `CLAUDE.md` wins.** In particular:

- **No igraph.** Judges and red teams suggested "OSMnx/igraph"; use rustworkx or NetworkX.
- **No Cloud CDN load balancer** (suggested in `decision-panel.md`); use Firebase Hosting's CDN.
- **No OSDMA data** without written permission.
- **No SHRUG,** not even for offline validation (`data-sources-and-licensing.md` Part 2).
- **No fixed ensemble size.** The "50 members" figure is unverified; read counts from the data.
- **Dialysis centres** only if a public list exists.
