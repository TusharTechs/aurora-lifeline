// Client for the AURORA API (Cloud Run behind Hosting at /api; NEXT_PUBLIC_API_BASE overrides in dev).

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";
// Bulletin reading calls Cloud Run directly: a long PDF can outlast Hosting's 60 s proxy limit.
const DIRECT = process.env.NEXT_PUBLIC_API_DIRECT ?? BASE;

export type Lang = "en-IN" | "te-IN" | "hi-IN";
export type Audience = "district_officer" | "health" | "public_works";

export type AdvisoryFields = {
  headline: string;
  sms_text: string;
  description: string;
  instruction: string;
  voice_script: string;
};

export type AdvisoryResult = {
  status: "draft" | "rejected";
  language: Lang;
  audience: string;
  district_name: string;
  approval: { required: boolean; state: string };
  badges: string[];
  rendered?: Partial<Record<Lang, AdvisoryFields>>;
  drafts?: Partial<Record<Lang, AdvisoryFields & { placeholders_used: string[] }>>;
  facts: Array<{
    id: string;
    kind: string;
    text: Record<string, string>;
    source: { table: string; row_id: string };
  }>;
  checks?: {
    numbers: string;
    back_translation?: { similarity: number; threshold: number; threshold_status: string; flag: boolean };
    warnings?: string[];
  };
  cap_xml?: string;
  cap_problems?: string[];
  problems?: string[];
  cached: boolean;
  prompt_version: string;
};

export type AskResult = {
  status: "answer" | "table";
  answer: string | null;
  answer_template?: string;
  citations?: Array<{ id: string; source: string; meaning: string }>;
  table: Array<{ id: string; meaning: string; text: string; source: string }>;
  problems?: string[];
  tool_calls: number;
  cached: boolean;
};

async function post<T>(path: string, body: unknown, base = BASE): Promise<T> {
  const r = await fetch(`${base}/api/v1/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    let msg = `${r.status}`;
    try {
      const j = (await r.json()) as { detail?: unknown };
      if (typeof j.detail === "string") msg = j.detail;
    } catch {
      /* not JSON */
    }
    throw new Error(msg);
  }
  return (await r.json()) as T;
}

export const draftAdvisory = (runId: string, lgd: string, language: Lang, audience: Audience) =>
  post<AdvisoryResult>("advisories", { run_id: runId, district_lgd: lgd, language, audience });

export const askAurora = (runId: string, question: string, language: Lang) =>
  post<AskResult>("ask", { run_id: runId, question, language });

export type BulletinCheck = { id: string; label: string; status: "pass" | "fail" | "na"; detail: string };
export type BulletinResult = {
  sha256: string;
  pages: number;
  reading: import("@/contracts").BulletinReading;
  checks: BulletinCheck[];
  needs_review: boolean;
  confirmation: { required: boolean; state: string };
  detected_bulletin_no: string | null;
  labels: { agree: number; total: number; differs: string[]; labels_status: string } | null;
  model: string;
  cached: boolean;
  prompt_version: string;
  known: { storm_id: string; bulletin_no: string; run_id: string; source_url: string } | null;
};

export const readKnownBulletin = (stormId: string, bulletinNo: string) =>
  post<BulletinResult>("bulletins/read-known", { storm_id: stormId, bulletin_no: bulletinNo }, DIRECT);

export async function readUploadedBulletin(file: File): Promise<BulletinResult> {
  const form = new FormData();
  form.append("file", file);
  const r = await fetch(`${DIRECT}/api/v1/bulletins/read`, { method: "POST", body: form });
  if (!r.ok) {
    let msg = `${r.status}`;
    try {
      const j = (await r.json()) as { detail?: unknown };
      if (typeof j.detail === "string") msg = j.detail;
    } catch {
      /* not JSON */
    }
    throw new Error(msg);
  }
  return (await r.json()) as BulletinResult;
}

export type Season = {
  status: "ok" | "unavailable";
  checked_at_ist: string;
  active?: boolean;
  latest?: {
    title: string;
    bulletin_no: string | null;
    based_on_ist: string;
    age_h: number;
    url: string | null;
  } | null;
  source?: string;
  active_rule?: string;
};

export async function getSeason(): Promise<Season | null> {
  try {
    const r = await fetch(`${BASE}/api/v1/season`);
    return r.ok ? ((await r.json()) as Season) : null;
  } catch {
    return null;
  }
}

export const readLatestBulletin = () =>
  post<BulletinResult & { live?: { based_on_ist: string; source_url: string } }>(
    "bulletins/read-latest",
    {},
    DIRECT,
  );

export type VoiceResult = {
  audio_b64: string;
  mime: string;
  model: string;
  voice: string;
  language: Lang;
  cached: boolean;
};

export const advisoryVoice = (runId: string, lgd: string, language: Lang, audience: Audience) =>
  post<VoiceResult>("advisories/voice", { run_id: runId, district_lgd: lgd, language, audience });

export type FieldResult = {
  observation: {
    asset_id: string | null;
    asset_type: string;
    passable: "yes" | "no" | "unknown";
    water_depth_band: string;
    damage_state: string;
    blockage: string;
    location_consistency: string;
    time_consistency: string;
    evidence_notes: string;
    confidence: number;
  };
  confidence_band: "high" | "medium" | "low";
  notes_withheld?: boolean;
  routing: {
    decision: "auto_apply" | "officer_queue";
    reasons: string[];
    asset: { asset_id: string; description: string; lat: number; lon: number } | null;
  };
  claimed: { place: string; time: string | null; action_id: string | null };
  candidates: Array<{
    asset_id: string;
    action_id: string;
    type: string;
    description: string;
    lat: number;
    lon: number;
  }>;
  model: string;
  prompt_version: string;
  cached: boolean;
};

export async function submitFieldReport(
  photo: Blob,
  runId: string,
  lgd: string,
  claimedAction: string,
  claimedTime: string,
): Promise<FieldResult> {
  const form = new FormData();
  form.append("file", photo, "field-report.jpg");
  form.append("run_id", runId);
  form.append("district_lgd", lgd);
  form.append("claimed_action", claimedAction);
  form.append("claimed_time", claimedTime);
  const r = await fetch(`${DIRECT}/api/v1/field-reports`, { method: "POST", body: form });
  if (!r.ok) {
    let msg = `${r.status}`;
    try {
      const j = (await r.json()) as { detail?: unknown };
      if (typeof j.detail === "string") msg = j.detail;
    } catch {
      /* not JSON */
    }
    throw new Error(msg);
  }
  return (await r.json()) as FieldResult;
}
