// Generated from schemas/district_scenario.json by `make schemas`. Do not edit.

/**
 * Static per-district result of one storm run (ARCHITECTURE §5), at most 1 MB. Every number comes from the engine. In deterministic mode probabilities are null and only the IMD-track time is given.
 */
export interface DistrictScenario {
  schema_version: "1";
  run_id: string;
  storm_id: string;
  storm_status: "replay" | "live";
  district_lgd: string;
  district_name: string;
  provenance: {
    imd_bulletin_no: string;
    imd_issued_at_utc: string;
    landfall_window_text?: string | null;
    /**
     * Member count per source, e.g. IMD, ECMWF, WNX, WNX_LARGE
     */
    members: {
      [k: string]: number;
    };
    mode: "ensemble" | "deterministic";
    data_versions: {
      [k: string]: string;
    };
    code_sha: string;
    model_ids: {
      [k: string]: string;
    };
  };
  time_axis: {
    now_utc: string;
    landfall_utc: string;
    step_h: number;
    n_steps: number;
  };
  headline: {
    pop_cut_hospital: Window;
    facilities_at_risk: Window;
    pop_served_by_substations_at_risk: {
      p10: number | null;
      p50: number | null;
      p90: number | null;
      class: "likely" | "possible" | "unlikely" | null;
    };
    at: "landfall";
  };
  hourly: {
    t_utc: string;
    pop_cut_p10: number | null;
    pop_cut_p50: number | null;
    pop_cut_p90: number | null;
    pop_power_risk_p50: number | null;
    facilities_at_risk: number;
  }[];
  facilities: Facility[];
  actions: Action[];
  completeness: {
    badge: "good" | "partial" | "poor";
    phc_ratio: number | null;
    chc_ratio: number | null;
    substations_mapped: number;
  };
  tiles: {
    url_template: string;
    layers: ("edges" | "settlements" | "facilities" | "surge" | "flood" | "tracks")[];
    minzoom: number;
    maxzoom: number;
  };
  flags: {
    needs_review: boolean;
    screening_surge: boolean;
    prior_params: string[];
  };
}
/**
 * This interface was referenced by `DistrictScenario`'s JSON-Schema
 * via the `definition` "Window".
 */
export interface Window {
  p10: number | null;
  p50: number | null;
  p90: number | null;
}
/**
 * This interface was referenced by `DistrictScenario`'s JSON-Schema
 * via the `definition` "Facility".
 */
export interface Facility {
  facility_id: string;
  type:
    | "district_hospital"
    | "sdh_area_hospital"
    | "chc"
    | "phc"
    | "sub_centre"
    | "shelter"
    | "delivery_point"
    | "dialysis";
  name: string;
  lat: number;
  lon: number;
  is_simulated: boolean;
  p_isolated_by_landfall: number | null;
  /**
   * Per-source probability (D15)
   */
  p_isolated_by_source?: {
    [k: string]: number;
  };
  /**
   * Conditional window: the 10th percentile of the time the facility is cut off, over the futures in which it is cut off at all.
   */
  t10: string | null;
  /**
   * Conditional window: the 50th percentile of the time the facility is cut off, over the futures in which it is cut off at all.
   */
  t50: string | null;
  /**
   * Conditional window: the 90th percentile of the time the facility is cut off, over the futures in which it is cut off at all.
   */
  t90: string | null;
  /**
   * Unconditional: decile k is the first time by which k/10 of the weighted storm futures cut this facility off (null if never). P(t) = largest k/10 with decile_k <= t.
   *
   * @minItems 9
   * @maxItems 9
   */
  iso_deciles: [
    string | null,
    string | null,
    string | null,
    string | null,
    string | null,
    string | null,
    string | null,
    string | null,
    string | null,
  ];
  referral_p_isolated: number | null;
  power: {
    p: number | null;
    class: "likely" | "possible" | "unlikely" | null;
  };
  expected_births_window: Window;
  badges: string[];
}
/**
 * This interface was referenced by `DistrictScenario`'s JSON-Schema
 * via the `definition` "Action".
 */
export interface Action {
  action_id: string;
  type: "stage_machine" | "dg_set" | "move_births" | "evacuate";
  target_id: string;
  deadline_utc: string;
  /**
   * e.g. 'P10 closure - 6 h' or 'IMD-track closure - 6 h'
   */
  deadline_basis: string;
  people_protected: number;
  p_event: number | null;
  rank: number;
  evidence_ref: string;
  /**
   * Where the action happens, for labels and advisories. Names are from OpenStreetMap.
   */
  site?: {
    lat: number;
    lon: number;
    /**
     * bridge, culvert, ford or null
     */
    crossing_type: string | null;
    road_class: string | null;
    road_name: string | null;
    near_place: {
      name: string;
      name_te?: string | null;
      name_hi?: string | null;
      name_or?: string | null;
      distance_km: number;
    } | null;
  };
}
