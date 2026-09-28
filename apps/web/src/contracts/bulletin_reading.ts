// Generated from schemas/bulletin_reading.json by `make schemas`. Do not edit.

/**
 * Structured reading of one IMD / RSMC New Delhi tropical-cyclone bulletin (AI_AGENTS §3). Numbers are copied from the bulletin with verbatim quotes; they are attributed to IMD, never shown as AURORA estimates.
 */
export interface BulletinReading {
  bulletin_no: string;
  issued_at_utc: string | null;
  issued_at_text: string;
  system_name: string | null;
  system_stage: "LPA" | "WML" | "D" | "DD" | "CS" | "SCS" | "VSCS" | "ESCS" | "SuCS";
  current: CurrentFix;
  forecast: ForecastPoint[];
  landfall: Landfall | null;
  surge: SurgeGuidance[];
  rainfall_warnings: RainfallWarning[];
  wind_warnings: WindWarning[];
  source_quotes: SourceQuote[];
  uncertain_fields: string[];
  /**
   * Provenance of the reading, e.g. 'hand-entered' before the Bulletin Reader exists.
   */
  source_note?: string | null;
}
/**
 * This interface was referenced by `BulletinReading`'s JSON-Schema
 * via the `definition` "CurrentFix".
 */
export interface CurrentFix {
  lat: number;
  lon: number;
  msw_min: number | null;
  msw_max: number | null;
  gust_value: number | null;
  wind_unit: "kt" | "kmph";
  pressure_hpa: number | null;
  movement_text: string | null;
}
/**
 * This interface was referenced by `BulletinReading`'s JSON-Schema
 * via the `definition` "ForecastPoint".
 */
export interface ForecastPoint {
  lead_h: number;
  valid_at_utc: string | null;
  valid_at_text: string | null;
  lat: number;
  lon: number;
  msw_min: number | null;
  msw_max: number | null;
  gust_value: number | null;
  wind_unit: "kt" | "kmph";
  category: string;
}
/**
 * This interface was referenced by `BulletinReading`'s JSON-Schema
 * via the `definition` "Landfall".
 */
export interface Landfall {
  window_text: string;
  start_utc: string | null;
  end_utc: string | null;
  location_text: string;
  lat: number | null;
  lon: number | null;
}
/**
 * This interface was referenced by `BulletinReading`'s JSON-Schema
 * via the `definition` "SurgeGuidance".
 */
export interface SurgeGuidance {
  area_text: string;
  height_m_min: number | null;
  height_m_max: number | null;
}
/**
 * This interface was referenced by `BulletinReading`'s JSON-Schema
 * via the `definition` "RainfallWarning".
 */
export interface RainfallWarning {
  area_text: string;
  date_text: string;
  category: "heavy" | "heavy_to_very_heavy" | "very_heavy" | "extremely_heavy" | "other";
}
/**
 * This interface was referenced by `BulletinReading`'s JSON-Schema
 * via the `definition` "WindWarning".
 */
export interface WindWarning {
  area_text: string;
  date_text: string | null;
  speed_min: number | null;
  speed_max: number | null;
  gust: number | null;
  unit: "kt" | "kmph";
}
/**
 * This interface was referenced by `BulletinReading`'s JSON-Schema
 * via the `definition` "SourceQuote".
 */
export interface SourceQuote {
  /**
   * JSON path of the field the quote supports
   */
  path: string;
  quote: string;
}
