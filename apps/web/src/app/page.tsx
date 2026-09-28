import fs from "node:fs";
import path from "node:path";
import type { DistrictScenario } from "@/contracts";
import { STORMS } from "@/lib/storms";

function districts(runId: string): DistrictScenario[] {
  const dir = path.join(process.cwd(), "public", "runs", runId, "districts");
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")) as DistrictScenario);
}

function lakh(n: number | null): string {
  if (n === null) return "–";
  return n >= 100_000 ? `${(n / 100_000).toFixed(1)} lakh` : n.toLocaleString("en-IN");
}

export default function Home() {
  const s = STORMS[0]!;
  const ds = districts(s.defaultRun).sort(
    (a, b) => (b.headline.pop_cut_hospital.p50 ?? 0) - (a.headline.pop_cut_hospital.p50 ?? 0),
  );
  const demo = ds.find((d) => d.district_lgd === s.demoDistrict) ?? ds[0];
  return (
    <main className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-12">
      <div>
        <p className="text-sm uppercase tracking-widest text-sky-400">{s.name} · historical replay</p>
        <h1 className="mt-2 text-4xl font-semibold">AURORA Lifeline</h1>
        <p className="mt-3 max-w-3xl text-lg text-slate-300">
          IMD tells you the storm. AURORA Lifeline tells you which PHC is cut off, how likely, when, and what
          to move there now.
        </p>
      </div>
      {demo && (
        <section className="grid gap-4 sm:grid-cols-3">
          <div className="rounded-lg bg-slate-900 p-5">
            <div className="text-sm text-slate-400">
              People cut off from any public hospital by landfall · {demo.district_name}
            </div>
            <div className="mt-2 text-3xl font-semibold">{lakh(demo.headline.pop_cut_hospital.p50)}</div>
            <div className="text-xs text-slate-400">
              P10–P90: {lakh(demo.headline.pop_cut_hospital.p10)} – {lakh(demo.headline.pop_cut_hospital.p90)}
            </div>
          </div>
          <div className="rounded-lg bg-slate-900 p-5">
            <div className="text-sm text-slate-400">
              Health facilities cut off from referral care (median)
            </div>
            <div className="mt-2 text-3xl font-semibold">{demo.headline.facilities_at_risk.p50 ?? "–"}</div>
            <div className="text-xs text-slate-400">
              P10–P90: {demo.headline.facilities_at_risk.p10} – {demo.headline.facilities_at_risk.p90}
            </div>
          </div>
          <div className="rounded-lg bg-slate-900 p-5">
            <div className="text-sm text-slate-400">Storm futures run through the road network</div>
            <div className="mt-2 text-3xl font-semibold">
              {Object.entries(demo.provenance.members)
                .filter(([k]) => k !== "IMD")
                .reduce((a, [, v]) => a + v, 0)
                .toLocaleString("en-IN")}
            </div>
            <div className="text-xs text-slate-400">
              Google DeepMind WeatherNext and ECMWF, aligned to the IMD official track
            </div>
          </div>
        </section>
      )}
      <section>
        <h2 className="text-lg font-semibold">Districts</h2>
        <ul className="mt-3 grid gap-2 sm:grid-cols-2">
          {ds.map((d) => (
            <li key={d.district_lgd}>
              <a
                href={`/storm/${s.stormId}/district/${d.district_lgd}/`}
                className="flex justify-between rounded bg-slate-900 px-4 py-3 hover:bg-slate-800"
              >
                <span>{d.district_name}</span>
                <span className="text-slate-400">
                  {lakh(d.headline.pop_cut_hospital.p50)} people at landfall (median)
                </span>
              </a>
            </li>
          ))}
        </ul>
      </section>
      <p className="text-sm text-slate-400">
        Not an official warning service. The India Meteorological Department is the authoritative source for
        cyclone warnings in India. This page replays a past storm with only the data available before it made
        landfall.
      </p>
    </main>
  );
}
