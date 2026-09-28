# Engine: algorithms, parameters and honesty rules

The engine is deterministic Python (`engine/aurora_engine`). It produces every AURORA number users see.

- **PRIOR** marks a starting value that is not calibrated. Label it "prior" in the UI and in the run manifest.
- **CONFIRM** marks something to check against the cited source. Time-box each check to 20 minutes; if it is still unresolved, keep the stated value, record it as "PRIOR (unconfirmed)" and move on.
- Never invent other values. If no defensible number exists, show a qualitative class ("likely", "possible" or "unlikely").
- **The slice does no calibration.** Montha is the test storm and must never be used to fit parameters.

## 1. Conventions

- **Time:** UTC internally and IST in the UI. Hourly steps from the run's "now" (the bulletin issue time) to landfall + 24 h.
- **Units:** SI internally. Inputs in knots or km/h are converted at ingest.
- **Wind averaging:**
  - IMD maximum sustained wind is the highest 3-minute mean at 10 m (IMD RSMC terminology, https://rsmcnewdelhi.imd.gov.in/images/pdf/terminology.pdf).
  - **Slice:** no averaging-period conversion between sources, marked PRIOR. Authority alignment (§2) rescales ensemble intensity to IMD anyway.
  - **Demo Day:** apply WMO/TD-1555 (Harper et al., 2010) conversion factors.
- **Determinism:** fixed seeds, sorted iteration, pinned data versions. The manifest records everything.
- **Member key:** `(source, member_no)`. `IMD/0` is the official track.

## 2. Tracks and authority alignment

1. **Ingest:**
   - the IMD `BulletinReading`: positions and intensity ranges at the IMD lead times. The engine uses the midpoint of `msw_min` and `msw_max` (PRIOR);
   - ECMWF IFS ensemble TC tracks (BUFR, via eccodes/pdbufr);
   - Weather Lab CSV/ATCF members.

   Keep only tracks whose first point is within 300 km of the IMD position at the same valid time. IBTrACS and the IMD best track are verification labels only; **never use them as inputs** to a scored run.
2. **Interpolate** linearly to hourly steps.
3. **Alignment (default on), for each lead time L within IMD's horizon:**
   - translate every member by (IMD_L − ensemble mean position_L);
   - scale each member's intensity so the ensemble median equals IMD's intensity at L;
   - taper to zero over 24 h beyond IMD's horizon.

   The UI labels this "ensemble aligned to the IMD official forecast".
4. **Deterministic mode:** if no ensemble members exist, the run uses `IMD/0` only (SPEC §3).
5. **Radius of maximum wind:** if missing, R_m = 46.4·exp(−0.0155·V_max + 0.0169·|φ|) km, with V_max in m/s and φ the latitude (Willoughby et al., 2006; CONFIRM). Record the relation in the manifest.

## 3. Wind (Holland 1980)

The gradient wind at radius r:

```latex
V_g(r) = \sqrt{\frac{B}{\rho}\left(\frac{R_m}{r}\right)^{B} \Delta p \, e^{-(R_m/r)^{B}} + \left(\frac{r f}{2}\right)^{2}} - \frac{r f}{2}
```

- ρ = 1.15 kg/m³; f is the Coriolis parameter; p_n = 1010 hPa (PRIOR).
- **V_mg**, the maximum gradient-level wind, comes from the surface intensity: V_mg = (V_sfc − 0.5·V_translation) / K, with K = 0.8 over sea (PRIOR).
- **B:**
  - If p_c is known: B starts from ρ·e·V_mg² / Δp (Holland 1980: V_mg = sqrt(B·Δp / (ρ·e))). Then solve numerically for B, unclipped, so that max_r V_g(r) *including the Coriolis term* equals V_mg. Clip the result to [1.0, 2.5].
  - If p_c is missing, which is typical for IMD forecast points: B = 1.5 (PRIOR). Solve numerically for Δp so that max_r V_g(r) equals V_mg.
- **Surface wind** V_s = K·V_g, with a land reduction factor of 0.75 (PRIOR). Add 0.5 × the translation velocity projected onto the local wind direction (inflow angle 20°, PRIOR). Gust factor 1.4 (PRIOR).
- **Post-landfall:** use each member's own intensity; IMD bulletins and the ensembles give post-landfall values. A decay model (Roy Bhowmik et al., 2005) is Demo Day work, only for members that lack them.
- **Unit tests:**
  - over sea, the maximum of K·V_g(r) + 0.5·V_translation·cos θ on the R_m ring reproduces V_sfc within 2% (skip when B was clipped);
  - with V_translation = 0, K·max V_g reproduces V_sfc within 2%;
  - the profile peaks at R_m;
  - radii are sane against published wind radii where they exist.
- **Outputs:** hourly wind at facilities, substations and settlements. Edges store only their maximum wind; no slice closure rule uses wind.
- Implement from these equations. Do not import CLIMADA (GPL).

## 4. Storm surge (screening model)

1. **Coastal peak.** For member 0, take the IMD bulletin surge guidance per district, using the upper bound of any range. Map `surge[].area_text` to districts as in §5 step 1.

   A bulletin issued about 72 h ahead may give no surge guidance. Then use h = c·(V_max / V_ref)² with V_ref = 50 m/s. Take c from IMD RSMC reports of pre-2025 east-coast landfalls (for example Hudhud 2014, Titli 2018, Fani 2019). Cite them in `config/fragility.yaml` with status PRIOR, and use no Montha values. Time-box this to 20 minutes. If it is still unresolved, surge is "not modelled at this lead time": closures come from rain only, and the proof page says so.
2. **Alongshore shape.** The peak sits one R_m to the right of the track at landfall and decays as a Gaussian with σ = 2·R_m (PRIOR).
3. **Members.** Scale the peak by (V_max,m / V_max,0)² and move it with each member's landfall point.
4. **Inland, as a connected bathtub:**
   - water level η(x) = h_coast − a·d(x), with a = 0.083 m/km (PRIOR);
   - d(x) is the distance inland from the OSM coastline;
   - a cell floods if its elevation is below η(x) and it is 8-connected to the sea through flooded cells.
5. **Terrain.** Copernicus GLO-30 is a surface model, so flooding in built-up and vegetated areas is understated. Say so on the proof page.
6. **Timing.** A coastal segment is affected while the storm centre is within R_m + 50 km of it (PRIOR).
7. **UI label:** "Screening upper bound, not a hydrodynamic model. IMD surge guidance takes precedence." INCOIS products are linked, not ingested.
8. **Proof page:** modelled versus IMD-reported peak surge.

## 5. Rain flooding (height above nearest drainage)

- **HAND:** MERIT Hydro `hnd` band (90 m, ODbL option), taking the minimum over a 30 m buffer per edge. Mask JRC permanent water where occurrence exceeds 80%.
- **IMD categories** (IMD RSMC terminology): heavy 64.5–115.5 mm, very heavy 115.6–204.4 mm, extremely heavy > 204.5 mm per 24 h. These are station totals ending 08:30 IST, i.e. point values, not catchment means.

**Slice rain rule** (PRIOR; recorded in the manifest):

1. For each district and IST calendar day, take the category from the run's bulletin. Bounds in mm/day:
   - heavy 64.5–115.5;
   - heavy_to_very_heavy 64.5–204.4;
   - very_heavy 115.6–204.4;
   - extremely_heavy 204.5–300 (the 300 cap is PRIOR);
   - no warning = 0.

   **Mapping IMD text to districts and days** (deterministic; PRIOR):
   - `<state>_districts.csv` has an `imd_subdivision` column (for example "Coastal Andhra Pradesh & Yanam").
   - A warning for a subdivision or region applies to all its districts. A warning that names a district overrides it; match district names through `name_variants`.
   - Use the main category of each clause and ignore "isolated … falls" add-ons.
   - Parse `date_text` to the IMD day ending 08:30 IST, and record the phrases used in the manifest.
   - Unmatched text, or category `other`, gives 0 mm and sets `needs_review`.
2. Member m's daily total = lower + q_m·(upper − lower). q_m is the member's rank from 0 to 1 by closest approach to the district centroid, with the closest member at 1. Member 0 uses the midpoint.
3. Spread each daily total evenly over its 24 IST hours. R(t) is the cumulative total since "now". In the slice the local catchment is the district.
4. Riverine inflow from upstream districts is not modelled in the slice. The proof page says so.

**Flood rule:** a location floods at time t if HAND < h*(R(t)), where h*(R) = clamp(k·(R − R₀), 0, h_max).

- PRIORS: k = 0.02 m/mm, R₀ = 50 mm, h_max = 5 m. Depth ≈ h*(R) − HAND.
- Flag urban cells (GHSL built-up share > 0.5) as "drainage flooding not modelled".
- **Calibration (Demo Day only):** fit (k, R₀, h_max) on Sentinel-1 scenes of Fani (2019), Michaung (2023) or Dana (2024). Then re-score Montha out of sample and publish both the before and after scores.
- **IMERG** (for calibration and a perfect-forecast check on Demo Day): the `precipitation` band is mm/hr at 30-minute cadence, so accumulation = 0.5 × the sum. Montha has only provisional IMERG, and the manifest records this.
- **Riverine inland (Demo Day):** Flood Hub gauges at or above warning level flag adjacent edges.

## 6. Edge closure per member

t_close(e, m) is the earliest hour at which any of these holds:

- surge depth > 0.3 m at an edge sample point;
- rain-flood depth > 0.3 m;
- for a bridge, culvert or ford: either approach, within 200 m, has depth > 0.3 m;
- (Demo Day) a Flood Hub gauge above danger level, or tree-fall blockage (seeded, PRIOR).

0.3 m is where the published depth–disruption function reaches zero speed for cars in standing water (Pregnolato et al., 2017, doi:10.1016/j.trd.2017.06.020). Treat it as PRIOR for flowing surge water, where shallower depths are already dangerous, and say so on the proof page.

Closed edges stay closed for the horizon unless a confirmed field report reopens them. Store `cause` and `max_depth_m`.

## 7. Isolation (bottleneck, or widest-path, reachability)

Edges have closure times c_e (∞ if never). Sources S are the functioning targets; each has an availability time a_s (∞, or the time its own site floods). The isolation time of node v is:

```latex
b(v) = \max_{P:\,s \in S \to v} \; \min\Big(a_s,\; \min_{e \in P} c_e\Big)
```

v is isolated at time t if b(v) ≤ t. If b(v) = −∞ (no route at t₀), v is excluded from P and labelled "no mapped route (possible OSM gap)".

**Algorithm:** a max-heap Dijkstra variant, O(E log V). Implement it with a numpy CSR adjacency and heapq, or with numba.

```
for s in S: b[s] = a_s; push(s, b[s])
all other nodes: b = -inf
while heap:
    u = pop_max()
    for each (u, w, c_e):
        cand = min(b[u], c_e)
        if cand > b[w]:
            b[w] = cand
            pred[w] = (u, e)
            push(w, cand)
```

- Roads are undirected for emergency access.
- Target ≤ 20 s per member per state. Use at most 8 multiprocessing workers.
- **Aggregation:**
  - P_isolated_by(t, v) = the fraction of members with b_m(v) ≤ t;
  - windows are the P10, P50 and P90 of b_m(v) over finite members;
  - the slider uses deciles;
  - "never isolated" when b = ∞ in at least 90% of members.
- **Critical edges:** the bottleneck edge on each node's widest path, recovered from `pred`. Criticality(e) = mean over members of Σ population of the nodes whose bottleneck is e. It drives "stage a machine here".
- **Catchments** (slice): a facility of class c has as its catchment the settlements whose nearest class-c facility by t₀ network travel time is that facility. Ties are broken by `facility_id`; one multi-source Dijkstra per class. `pop_catchment` is their total population, and "the catchment's maximum t₀ network time" is the largest assigned time. A facility with no assigned settlements gets `pop_catchment = 0` and no patient-access run.
- **Referral tiers:** PHC → CHC, SDH or district hospital; CHC → SDH or district hospital; SDH → district hospital. A district hospital has no referral set, and its births window starts at its own availability time a_s.
- **Target classes:**
  - settlements → any hospital (district hospital, SDH or area hospital, CHC, PHC): a multi-source run;
  - facility → referral: a multi-source run from its higher-tier set;
  - settlements → shelters: multi-source.
  - **Patient access to a specific PHC:** a single-source run restricted to that PHC's catchment subgraph, i.e. the nodes within 1.5 × the catchment's maximum t₀ network time of the PHC, found once by a bounded Dijkstra and cached. **Never run a single-source search on the whole state graph.**
- **Tests:** a hand-worked 6-node graph; monotonicity (closing an edge never raises any b); source availability; determinism.

## 8. Power and health

### Power: the slice decision

- **Substations** come from OSM `power=substation`. Each settlement is assigned to its nearest substation by t₀ network distance (label "approximate"). The mapped share is the share of population within 30 km network distance of a mapped substation.
- **P_sub** = max(flood rule, wind fragility):
  - flood rule: site depth > 0.5 m (PRIOR);
  - wind fragility: a lognormal whose median and dispersion are copied, with citation, from a **substation** fragility source into `config/fragility.yaml` (status PRIOR). Spend at most 60 minutes finding one. If none is found, use the flood rule alone and show wind exposure as a class.
- **Local line outage (P_local) is not modelled in the slice.** On Demo Day it becomes a logistic function of gust, calibrated leave-one-storm-out on VIIRS.
- **Headline:** "people served by substations at risk", labelled as a lower bound: "substation failures only; local lines not modelled", with the "prior" badge.

### Health

- **Facility classes** come from OSM `amenity`/`healthcare` tags, healthsites.io, and name patterns ("PHC", "Primary Health Centre", "CHC", "Community Health Centre", "Area Hospital", "District Hospital", "Sub Divisional Hospital"). Store `class_confidence`.
- **Delivery points in the slice:** CHCs, SDH/area hospitals and district hospitals. PHCs are badged "possible delivery point". `delivery_point` and `dialysis` types are used only when an official list is loaded; otherwise dialysis shows as "not mapped".
- **Patient access** comes from §7, catchment-restricted. **Referral** comes from §7, multi-source.
- **Births window W** (per member, in days) = from the facility's referral-isolation time b_m to the end of the horizon (landfall + 24 h). W = 0 if the facility is never isolated in that member.
  - Expected births = catchment population × crude birth rate / 1000 × W / 365.
  - Report the P50 and P10–P90 across members, labelled "estimate". Take the crude birth rate from the SRS statistical report and cite its year.
- **Needs rules** (thresholds in config):
  - power risk likely, or p ≥ 0.5 before landfall → DG set with 72 h of fuel;
  - referral P_isolated ≥ 0.5 → delivery kit and a pre-positioned ambulance, or an early move to a birth-waiting home;
  - patient-access P_isolated ≥ 0.5 → a pre-landfall outreach camp.

## 9. Actions and optimiser

| Type | Deadline (config) and stated basis | People protected |
| --- | --- | --- |
| `stage_machine` (edge) | P10 closure − 6 h | Criticality(e) |
| `dg_set` (facility) | P10 power-risk time − 12 h (the flood-onset time when the risk is flood-driven) | Catchment population |
| `move_births` (facility) | P10 referral isolation − 24 h | Expected births (P50) |
| `evacuate` (settlement → nearest reachable shelter, slice rule) | P10 shelter-access closure − 6 h | Settlement population |

- Every action shows its deadline together with its basis ("by 14:00 IST (P10 closure − 6 h)").
- **Deterministic mode** (no ensemble members): the P10 time is replaced by the IMD-track time, and the basis text says "IMD-track closure − 6 h".
- Rank by people protected × P(event).
- Evidence JSON records the `run_id` and the member statistics.
- **Optimiser (Demo Day, OR-Tools CP-SAT):**
  - **Shelter assignment.** Integer y[s,k] in units of 10 people, subject to capacity, population and the P10 access-closure time before departure. Maximise Σy − ε·travel and report the shortfall. Capacities are simulated unless published, and badged.
  - **Staging.** Maximum coverage of critical edges reachable within 1 h before their P10 closure.

## 10. Validation

### Flooded roads (Sentinel-1, via Earth Engine)

1. **Pre-event:** median Sentinel-1 IW VV from the same relative orbit, T−30 to T−3 days.
2. **Post-event:** the first acquisition from T to T+4 days. If a district has none, extend to T+6 days and report the acquisition times. Districts with no scene are "not observed", not misses.
3. **Filter:** 50 m focal median.
4. **Flood mask** = (post − pre < −3 dB) AND (post < −16 dB) AND NOT permanent water (JRC occurrence > 80%) AND slope < 5° AND HAND < 15 m. These follow UN-SPIDER practice; report the values used.
5. **Observed flooded edge:** its midpoint, or at least 30% of a 15 m buffer, is flooded.
6. **Predicted closed:** closed by the observation time in at least 50% of members. Also report member 0 alone.

**Metrics:** POD, FAR and CSI per district, with the contingency table.

**Baselines:**

- **Distance-to-track:** flag the same number of edges nearest the official track.
- **IMD category table:** in districts where the bulletin expects flooding of low-lying areas, flag edges with HAND below the district median.

**Caveats:** the Sentinel-1 revisit can miss the flood peak; radar under-detects urban and under-canopy flooding. If Earth Engine is unavailable, the proof page says "Sentinel-1 scoring pending Earth Engine access".

### Power (Demo Day)

- `NASA/VIIRS/002/VNP46A2` (confirmed; daily, 500 m). Use band `Gap_Filled_DNB_BRDF_Corrected_NTL`, masked with `Mandatory_Quality_Flag` and `QF_Cloud_Mask`.
- Compute the post/pre ratio per service area, population-weighted. An area counts as observed outage if the ratio is below 0.5 (PRIOR).
- Report AUC, fitting leave-one-storm-out across Fani, Hudhud, Amphan, Dana and Montha.

### Surge and closures

- **Surge table:** modelled versus IMD-reported.
- **Sitrep closures:** extracted by the Gemini Sitrep Extractor with a 10% manual check, matched by name and location. Report lead time.

## 11. Sizing and performance

- **Slice scope:** wind hourly only at facilities, substations and settlements. `node_isolation` rows only for facility and settlement nodes (other nodes go to Parquet if needed).
- `build_graph`: ≤ 60 min per state (8 vCPU / 32 GiB).
- `storm_run`: ≤ 15 min per state for all members.
- In-API recompute of the demo district: ≤ 10 s.

## 12. Tests

- Unit tests per module.
- Property tests for monotonicity and determinism.
- Golden checksummed summaries for the Montha run in `tests/golden/`.
- A CI replay on `tests/fixtures/mini_district` in under 5 minutes.
