// Generated from schemas/run_manifest.json by `make schemas`. Do not edit.

/**
 * Everything needed to reproduce and audit one storm run (ARCHITECTURE §5).
 */
export interface RunManifest {
  run_id: string;
  storm_id: string;
  created_at_utc: string;
  code_sha: string;
  imd_bulletin_no: string;
  mode: "ensemble" | "deterministic";
  /**
   * e.g. 'hindsight (perfect-track)'; such runs never enter skill scores
   */
  run_label?: string | null;
  inputs: {
    uri: string;
    sha256: string;
    source: string;
    issued_at_utc: string | null;
    available_at_utc?: string | null;
  }[];
  members: {
    source: string;
    member_no: number;
    weight?: number;
  }[];
  parameters: {
    name: string;
    value: unknown;
    status: "PRIOR" | "PRIOR (unconfirmed)" | "CONFIRMED" | "CALIBRATED";
    source: string;
  }[];
  models: {
    id: string;
    prompt_version: string;
  }[];
  seed: number;
  outputs: {
    path: string;
    sha256: string;
    bytes: number;
  }[];
}
