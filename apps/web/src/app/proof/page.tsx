import fs from "node:fs";
import path from "node:path";
import type { Metadata } from "next";
import { Footer } from "@/components/site/Footer";
import { Nav } from "@/components/site/Nav";
import evalData from "@/data/eval_bulletins.json";
import { STORMS } from "@/lib/storms";

export const metadata: Metadata = {
  title: "Proof",
  description:
    "How AURORA Lifeline's forecasts and readings score against what actually happened, misses included.",
};

type Scores = {
  hits: number;
  misses: number;
  false_alarms: number;
  correct_negatives: number;
  pod: number | null;
  far: number | null;
  csi: number | null;
  flagged: number;
};
type DistrictRow = {
  district_lgd: string;
  district_name: string;
  status: string;
  edges_observed?: number;
  edges_observed_flooded?: number;
  obs_hours_after_landfall?: number[];
  aurora?: Scores;
  member0_imd_track?: Scores;
  baseline_distance_to_track?: Scores;
  baseline_low_hand?: Scores;
};
type Validation = {
  generated_at_utc: string;
  reference_time_utc: string;
  sentinel1: {
    orbits?: Array<{ relative_orbit: number; acquired_utc: string; hours_after_t: number }>;
    attribution?: string;
  };
  rules: Record<string, string>;
  total: { edges_observed: number; edges_observed_flooded: number } & Record<string, Scores | number>;
  districts: DistrictRow[];
  caveats: string[];
};

function readValidation(runId: string): Validation | null {
  const f = path.join(process.cwd(), "public", "runs", runId, "validation.json");
  return fs.existsSync(f) ? (JSON.parse(fs.readFileSync(f, "utf8")) as Validation) : null;
}

function readPriors(runId: string): string[] {
  const f = path.join(process.cwd(), "public", "runs", runId, "manifest.json");
  if (!fs.existsSync(f)) return [];
  const m = JSON.parse(fs.readFileSync(f, "utf8")) as {
    parameters?: Array<{ name: string; status: string }>;
  };
  return (m.parameters ?? []).filter((p) => p.status.startsWith("PRIOR")).map((p) => p.name);
}

const f3 = (v: number | null | undefined) => (v === null || v === undefined ? "–" : v.toFixed(2));
const METHODS: Array<[keyof DistrictRow, string]> = [
  ["aurora", "AURORA (≥50% of futures)"],
  ["member0_imd_track", "IMD track alone"],
  ["baseline_distance_to_track", "Baseline: nearest the track"],
  ["baseline_low_hand", "Baseline: lowest ground"],
];

export default function Proof() {
  const s = STORMS[0]!;
  const href = `/storm/${s.stormId}/district/${s.demoDistrict}/`;
  const v = readValidation(s.defaultRun);
  const priors = readPriors(s.defaultRun);
  return (
    <>
      <Nav controlRoomHref={href} />
      <main id="main" className="mx-auto max-w-6xl px-4 pb-10 pt-14 sm:px-6">
        <p className="eyebrow">Proof</p>
        <h1 className="mt-3 max-w-4xl font-display text-4xl font-semibold leading-tight sm:text-6xl">
          Scored against what actually happened. <span className="text-aurora">Misses included.</span>
        </h1>
        <p className="mt-5 max-w-3xl text-lg text-muted">
          Every number below was computed after the fact, from independent evidence, without tuning anything
          to it. Where AURORA is weak, it says so.
        </p>

        <section aria-labelledby="s1-title" className="mt-14">
          <h2 id="s1-title" className="font-display text-2xl font-semibold sm:text-3xl">
            Roads under water: forecast against Sentinel-1 radar
          </h2>
          {v ? (
            <>
              <p className="mt-3 max-w-3xl text-muted">
                Montha, IMD Bulletin No. 21 run. Radar flood maps from the first Sentinel-1 passes after
                landfall ({(v.sentinel1.orbits ?? []).map((o) => `${o.hours_after_t} h`).join(", ")} after it)
                were compared with every road segment AURORA had forecast to close.{" "}
                {v.total.edges_observed.toLocaleString("en-IN")} segments were observed;{" "}
                {v.total.edges_observed_flooded.toLocaleString("en-IN")} showed water.
              </p>
              <div className="mt-6 overflow-x-auto">
                <table className="w-full min-w-[760px] text-left text-sm">
                  <caption className="sr-only">Skill scores per district and method</caption>
                  <thead className="text-xs text-subtle">
                    <tr>
                      <th className="py-2 pr-3 font-normal">District</th>
                      <th className="py-2 pr-3 font-normal">Method</th>
                      <th className="py-2 pr-3 font-normal">Hit rate (POD)</th>
                      <th className="py-2 pr-3 font-normal">False alarms (FAR)</th>
                      <th className="py-2 pr-3 font-normal">CSI</th>
                      <th className="py-2 font-normal">Hits · misses · false alarms</th>
                    </tr>
                  </thead>
                  <tbody>
                    {v.districts.map((d) =>
                      d.status !== "observed" ? (
                        <tr key={d.district_lgd} className="border-t border-border">
                          <td className="py-2 pr-3">{d.district_name}</td>
                          <td className="py-2 text-muted" colSpan={5}>
                            Not observed by Sentinel-1 in the window (not counted as a miss)
                          </td>
                        </tr>
                      ) : (
                        METHODS.map(([k, label], i) => {
                          const sc = d[k] as Scores | undefined;
                          return (
                            <tr
                              key={`${d.district_lgd}-${k}`}
                              className={i === 0 ? "border-t border-border" : ""}
                            >
                              <td className="py-1.5 pr-3">{i === 0 ? d.district_name : ""}</td>
                              <td
                                className={`py-1.5 pr-3 ${i === 0 ? "font-semibold text-teal" : "text-muted"}`}
                              >
                                {label}
                              </td>
                              <td className="py-1.5 pr-3 tabular-nums">{f3(sc?.pod)}</td>
                              <td className="py-1.5 pr-3 tabular-nums">{f3(sc?.far)}</td>
                              <td className="py-1.5 pr-3 tabular-nums">{f3(sc?.csi)}</td>
                              <td className="py-1.5 tabular-nums text-muted">
                                {sc ? `${sc.hits} · ${sc.misses} · ${sc.false_alarms}` : "–"}
                              </td>
                            </tr>
                          );
                        })
                      ),
                    )}
                  </tbody>
                </table>
              </div>
              <ul className="mt-6 grid gap-2 text-sm text-muted sm:grid-cols-2">
                {Object.entries(v.rules).map(([k, r]) => (
                  <li key={k} className="card p-3">
                    <span className="text-subtle">{k.replaceAll("_", " ")}:</span> {r}
                  </li>
                ))}
                {v.caveats.map((c) => (
                  <li key={c} className="card p-3">
                    {c}
                  </li>
                ))}
              </ul>
              <p className="mt-3 text-xs text-subtle">{v.sentinel1.attribution}</p>
            </>
          ) : (
            <div className="card mt-6 p-6">
              <p className="font-semibold">Sentinel-1 scoring pending Earth Engine access.</p>
              <p className="mt-2 text-sm text-muted">
                The flood mask follows ENGINE §10 (UN-SPIDER change detection); scores will appear here per
                district, with the contingency table and both baselines.
              </p>
            </div>
          )}
        </section>

        <section aria-labelledby="br-title" className="mt-16">
          <h2 id="br-title" className="font-display text-2xl font-semibold sm:text-3xl">
            Reading IMD bulletins: Gemini against hand-checked labels
          </h2>
          <p className="mt-3 max-w-3xl text-muted">
            Each bulletin was read on the deployed service. Agreement is field by field with a reading entered
            by hand from the PDF; those labels are drafts awaiting a second person&apos;s confirmation.
          </p>
          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            {evalData.bulletins.map((b) => (
              <article key={b.label} className="card p-5">
                <h3 className="font-display text-lg font-semibold">{b.label}</h3>
                <p className="mt-1 text-xs text-subtle">
                  {b.pages} pages · {b.model} · {b.prompt_version}
                </p>
                <p className="mt-3 font-display text-3xl font-semibold text-teal">
                  {b.labels ? `${b.labels.agree}/${b.labels.total}` : "–"}
                </p>
                <p className="text-xs text-muted">
                  {b.labels
                    ? `fields agree with the labels${b.labels.differs.length ? `; differs: ${b.labels.differs.join(", ")}` : ""}`
                    : "no labels (live bulletin)"}
                </p>
                <ul className="mt-4 space-y-1 text-xs">
                  {b.checks.map((c) => (
                    <li key={c.id} className="flex gap-2">
                      <span
                        className={`w-11 shrink-0 font-semibold ${c.status === "pass" ? "text-safe" : c.status === "fail" ? "text-danger" : "text-subtle"}`}
                      >
                        {c.status === "pass" ? "✓ pass" : c.status === "fail" ? "✕ fail" : "– n/a"}
                      </span>
                      <span className="text-muted">
                        {c.label} <span className="text-subtle">({c.detail})</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section aria-labelledby="todo-title" className="mt-16">
          <h2 id="todo-title" className="font-display text-2xl font-semibold sm:text-3xl">
            Not validated yet
          </h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-muted">
            <li>Power: VIIRS night-lights outage scoring is not done; power results are not shown.</li>
            <li>
              Storm surge: the screening model is not yet compared with IMD&apos;s surge guidance and
              observations.
            </li>
            <li>Closures reported in state situation reports are not yet matched to the forecast.</li>
            <li>
              Parameters still marked prior (uncalibrated):{" "}
              {priors.length ? priors.join(", ") : "see the run manifest"}.
            </li>
          </ul>
        </section>
      </main>
      <Footer controlRoomHref={href} />
    </>
  );
}
