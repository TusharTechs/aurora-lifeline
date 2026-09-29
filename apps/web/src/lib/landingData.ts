// Build-time data for the landing page, read from the published run (never invented).
import fs from "node:fs";
import path from "node:path";
import type { DistrictScenario } from "@/contracts";
import type { HeroData, HeroTrack } from "@/components/landing/HeroAurora";
import coast from "@/data/coast.json";
import { STORMS } from "@/lib/storms";

type TrackFeature = {
  properties: { s: string; m: number; o: boolean; h0: number };
  geometry: { coordinates: Array<[number, number]> };
};

const RUNS = path.join(process.cwd(), "public", "runs");

function readJson<T>(...p: string[]): T | null {
  const f = path.join(RUNS, ...p);
  return fs.existsSync(f) ? (JSON.parse(fs.readFileSync(f, "utf8")) as T) : null;
}

export type Fact = { label: string; value: string; note: string };
export type LandingData = {
  storm: (typeof STORMS)[number];
  scenario: DistrictScenario;
  districts: Array<{ lgd: string; name: string; p50: number | null }>;
  hero: HeroData;
  members: number;
  leadH: number;
};

function hoursAfter(nowUtc: string, iso: string | null): number | null {
  return iso === null ? null : (Date.parse(iso) - Date.parse(nowUtc)) / 3_600_000;
}

export function landingData(): LandingData | null {
  const storm = STORMS[0]!;
  const run = storm.defaultRun;
  const scenario = readJson<DistrictScenario>(run, "districts", `${storm.demoDistrict}.json`);
  if (!scenario) return null;
  const dir = path.join(RUNS, run, "districts");
  const districts = fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => readJson<DistrictScenario>(run, "districts", f)!)
    .map((d) => ({ lgd: d.district_lgd, name: d.district_name, p50: d.headline.pop_cut_hospital.p50 }))
    .sort((a, b) => (b.p50 ?? 0) - (a.p50 ?? 0));

  // Tracks: every ECMWF and WeatherNext member, and one in three large-ensemble members, 3-hourly.
  const tracks = readJson<{ features: TrackFeature[] }>(run, "tracks.json")?.features ?? [];
  const toTrack = (f: TrackFeature, thin: number): HeroTrack => ({
    s: f.properties.s,
    h0: f.properties.h0,
    step: 3 * thin,
    pts: f.geometry.coordinates.filter((_, i) => i % thin === 0).map(([x, y]) => [x, y] as [number, number]),
  });
  const ens = tracks
    .filter((f) => !f.properties.o)
    .filter((f) => f.properties.s !== "WNX_LARGE" || f.properties.m % 3 === 0)
    .map((f) => toTrack(f, 1));
  const imd = tracks.find((f) => f.properties.o);
  const official: HeroTrack = imd
    ? {
        s: "IMD",
        h0: imd.properties.h0,
        step: 1,
        pts: imd.geometry.coordinates.map(([x, y]) => [x, y] as [number, number]),
      }
    : { s: "IMD", h0: 0, step: 1, pts: [] };

  const now = scenario.time_axis.now_utc;
  const facilities = scenario.facilities
    .filter((f) => f.type !== "shelter")
    .map((f) => ({
      name: f.name,
      lon: f.lon,
      lat: f.lat,
      hours: f.iso_deciles.map((d) => hoursAfter(now, d)),
    }));
  const members = Object.entries(scenario.provenance.members)
    .filter(([k]) => k !== "IMD")
    .reduce((a, [, v]) => a + v, 0);
  const landfallH = (Date.parse(scenario.time_axis.landfall_utc) - Date.parse(now)) / 3_600_000;
  const leadH = Math.round(
    (Date.parse(storm.observedLandfall.utc) - Date.parse(scenario.provenance.imd_issued_at_utc)) / 3_600_000,
  );

  return {
    storm,
    scenario,
    districts,
    members,
    leadH,
    hero: {
      bbox: [79.2, 9.6, 89.2, 18.4],
      coast: (coast as unknown as { lines: Array<Array<[number, number]>> }).lines,
      tracks: ens,
      official,
      facilities,
      hourly: scenario.hourly.map((h) => h.pop_cut_p50 ?? 0),
      landfallH,
      nowUtc: now,
      members,
      bulletinNo: scenario.provenance.imd_bulletin_no,
      district: scenario.district_name,
    },
  };
}
