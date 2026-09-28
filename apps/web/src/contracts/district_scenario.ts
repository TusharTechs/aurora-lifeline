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
  t10: string | null;
  t50: string | null;
  t90: string | null;
  /**
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
    string | null
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
}
