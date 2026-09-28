// Generated from schemas/field_observation.json by `make schemas`. Do not edit.

/**
 * Field Verifier output for one photo, video or voice report (AI_AGENTS §4). Routing is deterministic; bridge reopenings always go to an officer.
 */
export interface FieldObservation {
  asset_id: string | null;
  asset_type: "road" | "bridge" | "culvert" | "facility" | "substation" | "other";
  passable: "yes" | "no" | "unknown";
  water_depth_band: "none" | "lt_15cm" | "15_30cm" | "30_60cm" | "gt_60cm" | "unknown";
  damage_state: "none" | "minor" | "moderate" | "severe" | "destroyed" | "unknown";
  blockage: "none" | "debris" | "tree" | "collapse" | "water" | "vehicle" | "unknown";
  location_consistency: "consistent" | "inconsistent" | "unknown";
  time_consistency: "consistent" | "inconsistent" | "unknown";
  voice_language: string | null;
  voice_summary_en: string | null;
  /**
   * At most 60 words.
   */
  evidence_notes: string;
  confidence: number;
}
