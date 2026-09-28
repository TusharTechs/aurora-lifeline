# Cyclone track: technical notes and references

Compiled from the Track 05 research agent (27 Sep 2026) and the red-team review (28 Sep 2026). Anything these sources could not confirm is marked UNVERIFIED. Re-check each link before relying on it.

## Pain evidence (India and APAC)

| Event | Key facts | Source |
| --- | --- | --- |
| 1999 Odisha super cyclone | ~9,887 deaths (official), mostly from a 5–6 m surge | https://en.wikipedia.org/wiki/1999_Odisha_cyclone |
| Fani 2019 | 64 deaths in Odisha; >1.2M evacuated; 1.56 lakh poles and >10k transformers down; 3.5M households without power on day 5; Puri without power on day 11 | https://www.outlookindia.com/national/india-news-five-days-after-cyclone-fani-hit-odisha-lakhs-still-without-electricity-towns-plunged-into-darkness-news-330010 ; https://www.outlookindia.com/national/india-news-11-days-after-cyclone-fani-no-electricity-in-puri-district-news-330396 |
| Amphan 2020 | ~5 m surge in West Bengal; >4,000 poles down in Kolkata; about a week to restore most power and water | https://en.wikipedia.org/wiki/Cyclone_Amphan |
| Dana 2024 | Zero deaths in Odisha; 8.1 lakh people in 6,210 relief centres | https://en.wikipedia.org/wiki/Cyclone_Dana |
| Montha 2025 | About 13,000 poles, 3,000 transformers and 14 bridges or culverts damaged in Andhra Pradesh; ~8 deaths in India (2 in AP per the Chief Minister, at least 6 in Telangana); landfall near Narasapuram, 28–29 Oct 2025 (confirm from IMD) | https://www.deccanchronicle.com/southern-states/andhra-pradesh/cyclone-montha-damages-13000-power-poles-3000-transformers-in-ap-1913863 |
| BOB 06, Sep 2026 | Deep depression crossed just south-west of Kalingapatnam around 23:00 IST on 23 Sep. About 74 deaths in India (UP 56, AP 9, Chhattisgarh 7, Odisha 2), plus about 14 in Nepal | https://www.aljazeera.com/news/2026/9/27/floods-and-landslides-kill-at-least-56-people-in-india-12-in-nepal ; IMD RSMC special outlook of 23 Sep 2026 |
| Senyar 2025 (Indonesia, Malaysia, Thailand) | 810 bridges and 215 health facilities damaged in Sumatra (BRICS/APAC relevance) | https://en.wikipedia.org/wiki/Cyclone_Senyar |

Wikipedia rows are secondary sources; cite primary reports in the deck where possible. Exposure figures: about 32 crore people vulnerable (NDMA 2008 estimate); coastline officially 11,098.81 km since 2025 (https://www.pib.gov.in/PressReleasePage.aspx?PRID=2198800).

## Existing systems (what they do not do)

- **IMD RSMC bulletins.** Track, intensity, cone, wind radii and surge guidance, plus a damage/action table keyed only to storm category (https://rsmcnewdelhi.imd.gov.in/images/pdf/sop.pdf).
- **NDMA Web-DCRA.** Built under NCRMP. Overlays IMD forecasts (wind, surge, inland flooding) on exposure; launched in 2022; used in Biparjoy and Michaung; district-level. The World Bank noted its mobile app was never released. No evidence found of road-access or power-cascade analysis (https://documents1.worldbank.org/curated/en/099021825083513126/pdf/P144726-bfd1dbca-dfec-4100-893b-09d38239f293.pdf).
- **INCOIS.** ADCIRC-based storm-surge and inundation warnings driven by IMD tracks, about 55 cyclones warned. No public API (https://tsunami.incois.gov.in/TEWS/AboutStormSurge.jsp).
- **Sachet.** CAP alert delivery only. Public RSS (https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml).
- **Others:** Odisha SATARK and TN SMART (RIMES decision support); CDRI GIRI (long-run infrastructure risk, not a specific event) (https://giri.unepgrid.ch/); GDACS and PDC (population-level exposure).

## Methods and references for the engine

- **Holland wind profile:**
  - Holland (1980), doi:10.1175/1520-0493(1980)108<1212:AAMOTW>2.0.CO;2
  - Holland et al. (2010), doi:10.1175/2010MWR3317.1
  - CLIMADA's implementation is a useful reference but is GPL; do not import it: https://climada-python.readthedocs.io/en/stable/user-guide/climada_hazard_TropCyclone.html
- **Surge bathtub reference.** CLIMADA petals TCSurgeBathtub (Xu 2010 decay of about 0.2 m/km): https://climada-petals.readthedocs.io/en/stable/tutorial/climada_hazard_TCSurgeBathtub.html. The red team suggests inland attenuation of roughly 1 m per 10–15 km and warns that plain bathtub models flood entire deltas.
- **Bay of Bengal surge studies:**
  - a surge index using approach angle: https://www.sciencedirect.com/science/article/abs/pii/S0378383923001539
  - a design reference with 2,570 synthetic storms: https://link.springer.com/article/10.1007/s11069-026-08196-5
- **Road passability.** About 0.3 m of water stops cars (Pregnolato et al., 2017, doi:10.1016/j.trd.2017.06.020).
- **Transmission-tower fragility from Fani, Odisha:** https://arxiv.org/abs/2107.06072. Prioritising grid hardening on a 40M-person Odisha network is data-limited: https://arxiv.org/abs/2105.00909.
- **Access loss after Cyclone Idai:** 0.59–1.03M people lost access to healthcare. OSM road length in the flooded area nearly doubled after the event, a warning about pre-event OSM completeness (https://pmc.ncbi.nlm.nih.gov/articles/PMC9559768/).
- **Low-data cascade method (DISruptionMap):** https://arxiv.org/abs/2410.05286
- **Sentinel-1 flood mapping in Earth Engine (UN-SPIDER recommended practice):** https://un-spider.org/advisory-support/recommended-practices/recommended-practice-google-earth-engine-flood-mapping. A published GEE study of Amphan found 3,979 km² flooded: https://link.springer.com/chapter/10.1007/978-981-16-8225-4_6
- **HAND limitations.** It underestimates flooding by up to about 40% on low relief and has no pluvial or coastal component (per the red team; primary source to confirm).
- **Machine-learned surge emulators.** Caution: prescribed cyclone inputs degraded a Bay of Bengal ocean emulator (https://arxiv.org/abs/2609.04635).
- **Fani damage and needs assessment:** https://recovery.preventionweb.net/publication/documents-and-publications/cyclone-fani-damage-loss-and-needs-assessment

## Forecast data

| Source | Access | Licence and notes |
| --- | --- | --- |
| IMD RSMC | PDFs on the website; IMD API with an account (`cyclone_track`, `cyclone_wind`, `cyclone_cou`) | Redistribution terms UNVERIFIED |
| ECMWF open data | IFS/AIFS ensemble tracks (BUFR, `stream=enfo`, `type=tf`); https://github.com/ecmwf/ecmwf-opendata | CC BY 4.0. As-issued history on `gs://ecmwf-open-data` from 12 Jul 2023 (current `ifs/0p25` layout from 29 Feb 2024; verified 28 Sep 2026). Use `step=240`/`144` and IFS ENS for Oct 2025 |
| Weather Lab / WeatherNext Cyclones | CSV/ATCF downloads, about 2023 onward; https://developers.google.com/weathernext/guides/weatherlab | Data less than 1 hour old is under experimental terms; older data is CC BY 4.0. Code Apache-2.0, weights CC BY 4.0. Nature paper, 6 Aug 2026 |
| WeatherNext 2 and 3 | Earth Engine and BigQuery after an access request (5–7 business days). WeatherNext 3 (Aug 2026, hourly, up to 0.05°) is recommended for new projects | Historical CC BY 4.0; real-time under Google DeepMind terms |
| IBTrACS | NOAA NCEI CSV | Open. The Earth Engine copy ends in 2024 |
| GPM IMERG V07 | Earth Engine `NASA/GPM_L3/IMERG_V07` | Early run ~4 h latency, late run ~14 h |

The ensemble intensity for Dana ran about 43 kt against 65 kt observed (per the red team). Use ensembles for track and timing spread, and bias-correct intensity to IMD.

## Parametric precedents (indicative panel only)

- **Cyclone-Ready:** SEEDS, Howden India and New India Assurance; about 2,500 households in Cuddalore; up to INR 25,000 per household; triggers on cyclone intensity and distance; launched 29 Oct 2025 (https://pnndigital.com/national/cyclone-ready-piloting-indias-first-of-its-kind-parametric-insurance-for-coastal-communities/).
- **Nagaland:** NSDMA and SBI General parametric cover, reinsured by Munich Re and GIC Re (https://www.artemis.bm/news/nagaland-renews-parametric-insurance-with-sbi-general-munich-re-gic-re-support/).
- **Bangladesh (OCHA):** anticipatory action, US$8.03M pre-arranged. Remal did not meet the trigger, so the funds were repurposed (https://cerf.un.org/sites/default/files/resources/24-RR-BGD-63521_Bangladesh_CERF_Report.pdf).

## BRICS and disaster-risk policy context

- India hosted the 3rd BRICS Ministerial Meeting on Disaster Risk Reduction on 24 Jul 2026 and adopted a joint statement. Early warning and resilient infrastructure were chairship priorities (https://www.pib.gov.in/PressReleasePage.aspx?PRID=2288986).
- The track theme labels match India's 2026 BRICS pillars: Resilience, Innovation, Cooperation, Sustainability.
