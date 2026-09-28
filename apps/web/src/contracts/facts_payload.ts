// Generated from schemas/facts_payload.json by `make schemas`. Do not edit.

/**
 * Engine-produced facts that drafting and answering agents may cite only by placeholder (ARCHITECTURE §5; AI_AGENTS §2).
 */
export interface FactsPayload {
  run_id: string;
  district_lgd: string;
  audience: string;
  /**
   * @minItems 1
   */
  langs: [string, ...string[]];
  facts: Fact[];
}
/**
 * This interface was referenced by `FactsPayload`'s JSON-Schema
 * via the `definition` "Fact".
 */
export interface Fact {
  id: string;
  kind: "probability" | "count" | "time" | "time_window" | "place" | "provenance" | "text";
  value: number | string | null;
  unit: string | null;
  required: boolean;
  /**
   * Engine-rendered string per BCP-47 locale
   */
  text: {
    [k: string]: string;
  };
  source: {
    table: string;
    row_id: string;
  };
}
