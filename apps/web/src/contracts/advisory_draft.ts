// Generated from schemas/advisory_draft.json by `make schemas`. Do not edit.

/**
 * Advisory Writer output (AI_AGENTS §5). Text refers to numbers only via {{fact_id}} placeholders; a post-check rejects any digit outside a placeholder.
 */
export interface AdvisoryDraft {
  /**
   * BCP-47 tag, e.g. en-IN, te-IN
   */
  language: string;
  audience: "district_officer" | "health" | "power" | "public_works" | "field_team";
  headline: string;
  sms_text: string;
  description: string;
  instruction: string;
  /**
   * At most 90 words (checked in code).
   */
  voice_script: string;
  placeholders_used: string[];
  cap: {
    event: string;
    urgency: "Immediate" | "Expected" | "Future";
    severity: "Extreme" | "Severe" | "Moderate" | "Minor";
    certainty: "Observed" | "Likely" | "Possible";
    category: "Met" | "Infra" | "Health" | "Safety";
  };
}
