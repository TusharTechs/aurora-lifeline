"use client";

import { GoogleMapsOverlay } from "@deck.gl/google-maps";
import { MVTLayer } from "@deck.gl/geo-layers";
import { BitmapLayer, GeoJsonLayer, ScatterplotLayer } from "@deck.gl/layers";
import type { Layer, PickingInfo } from "@deck.gl/core";
import { APIProvider, Map, useMap } from "@vis.gl/react-google-maps";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import type { DistrictScenario } from "@/contracts";
import { isoDecilesToHours, probAt, probAtHours, rampPurple, rampRed, type DecileProps } from "@/lib/prob";
import { istAfter } from "@/lib/time";
import type { StormInfo } from "@/lib/storms";
import { AuroraLoader, Logo } from "./brand/Logo";
import { AdvisoryPanel } from "./AdvisoryPanel";
import { AskPanel } from "./AskPanel";
import { TriggerPanel } from "./TriggerPanel";

type Overlay = { url: string; bounds: [number, number, number, number]; label: string };
type Overlays = { extent?: [number, number, number, number]; flood: Overlay; surge: Overlay };
type Facility = DistrictScenario["facilities"][number];
type Action = DistrictScenario["actions"][number];
type Tab = "forecast" | "triggers" | "advisory" | "ask";

const MAPS_KEY = process.env.NEXT_PUBLIC_MAPS_API_KEY ?? "";
const MAP_ID = process.env.NEXT_PUBLIC_MAPS_MAP_ID ?? "";

const TYPE_LABEL: Record<string, string> = {
  district_hospital: "District hospital",
  sdh_area_hospital: "Area / sub-district hospital",
  chc: "CHC",
  phc: "PHC",
  shelter: "Shelter",
  sub_centre: "Sub-centre",
};
// Fallback data extent (Godavari region); runs publish their own in overlays.json. Tiles outside the
// extent do not exist (tippecanoe skips empty tiles).
const TILE_EXTENT: [number, number, number, number] = [80.3, 15.4, 82.95, 17.95];
const quietTileError = () => {};

const ROAD_WIDTH: Record<string, number> = { motorway: 4, trunk: 4, primary: 3.5, secondary: 3, tertiary: 2 };

const CROSSING_LABEL: Record<string, string> = { bridge: "bridge", culvert: "culvert", ford: "causeway" };

function siteLabel(a: Action): string {
  const s = a.site;
  if (!s) return a.target_id;
  let label = CROSSING_LABEL[s.crossing_type ?? ""] ?? "road";
  if (s.near_place) label += ` near ${s.near_place.name}`;
  if (s.road_name) label += ` (${s.road_name})`;
  return label;
}

function DeckOverlay({ layers }: { layers: Layer[] }) {
  const map = useMap();
  const overlay = useMemo(() => new GoogleMapsOverlay({ interleaved: true }), []);
  useEffect(() => {
    overlay.setMap(map);
    return () => overlay.setMap(null);
  }, [map, overlay]);
  useEffect(() => {
    overlay.setProps({ layers });
  }, [overlay, layers]);
  return null;
}

function pct(p: number | null | undefined): string {
  return p === null || p === undefined ? "–" : `${Math.round(p * 100)}%`;
}

function fmtPeople(n: number | null | undefined): string {
  if (n === null || n === undefined) return "–";
  if (n >= 100_000) return `${(n / 100_000).toFixed(1)} lakh`;
  return Math.round(n).toLocaleString("en-IN");
}

export function CommandMap({
  storm,
  runId: initialRun,
  lgd,
}: {
  storm: StormInfo;
  runId: string;
  lgd: string;
}) {
  const [activeRun, setActiveRun] = useState(initialRun);
  const runId = activeRun;
  const [scenario, setScenario] = useState<DistrictScenario | null>(null);
  const [overlays, setOverlays] = useState<Overlays | null>(null);
  const [t, setT] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [show, setShow] = useState({
    tracks: true,
    roads: true,
    settlements: true,
    flood: false,
    surge: true,
  });
  const [hover, setHover] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("forecast");
  const base = `/runs/${runId}`;

  useEffect(() => {
    fetch(`${base}/districts/${lgd}.json`)
      .then((r) => r.json())
      .then(setScenario);
    fetch(`${base}/overlays.json`)
      .then((r) => r.json())
      .then(setOverlays);
  }, [base, lgd]);

  const nSteps = scenario?.time_axis.n_steps ?? 0;
  const landfallH = scenario
    ? (Date.parse(scenario.time_axis.landfall_utc) - Date.parse(scenario.time_axis.now_utc)) / 3_600_000
    : 0;

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setT((x) => (x >= nSteps ? 0 : x + 1)), 350);
    return () => clearInterval(id);
  }, [playing, nSteps]);

  const facHours = useMemo(() => {
    const m: Record<string, Array<number | null>> = {};
    if (scenario)
      for (const f of scenario.facilities)
        m[f.facility_id] = isoDecilesToHours(scenario.time_axis.now_utc, f.iso_deciles);
    return m;
  }, [scenario]);

  const center = useMemo(() => {
    const fs = scenario?.facilities ?? [];
    if (!fs.length) return { lat: 16.9, lng: 82.2 };
    return {
      lat: fs.reduce((a, f) => a + f.lat, 0) / fs.length,
      lng: fs.reduce((a, f) => a + f.lon, 0) / fs.length,
    };
  }, [scenario]);

  const layers = useMemo(() => {
    const out: Layer[] = [];
    if (overlays && show.flood)
      out.push(
        new BitmapLayer({
          id: "flood",
          image: overlays.flood.url,
          bounds: overlays.flood.bounds,
          opacity: 0.75,
        }),
      );
    if (overlays && show.surge)
      out.push(
        new BitmapLayer({
          id: "surge",
          image: overlays.surge.url,
          bounds: overlays.surge.bounds,
          opacity: 0.85,
        }),
      );
    if (show.settlements)
      out.push(
        new MVTLayer({
          id: "settlements",
          data: `/tiles/${runId}/settlements/{z}/{x}/{y}.pbf`,
          extent: overlays?.extent ?? TILE_EXTENT,
          onTileError: quietTileError,
          minZoom: 6,
          maxZoom: 12,
          stroked: false,
          getFillColor: (f: { properties: DecileProps }) => rampPurple(probAt(f.properties, t)),
          updateTriggers: { getFillColor: [t] },
          pickable: true,
        }),
      );
    if (show.roads)
      out.push(
        new MVTLayer({
          id: "edges",
          data: `/tiles/${runId}/edges/{z}/{x}/{y}.pbf`,
          extent: overlays?.extent ?? TILE_EXTENT,
          onTileError: quietTileError,
          minZoom: 6,
          maxZoom: 13,
          getLineColor: (f: { properties: DecileProps }) => rampRed(probAt(f.properties, t)),
          getLineWidth: (f: { properties: { rc?: string } }) => ROAD_WIDTH[f.properties.rc ?? ""] ?? 1.2,
          lineWidthUnits: "pixels",
          updateTriggers: { getLineColor: [t] },
          pickable: true,
        }),
      );
    if (show.tracks)
      out.push(
        new GeoJsonLayer({
          id: "tracks",
          data: `${base}/tracks.json`,
          stroked: true,
          filled: false,
          getLineColor: (f: { properties: { o: boolean; s: string } }) =>
            f.properties.o
              ? [255, 255, 255, 255]
              : f.properties.s === "ECMWF"
                ? [167, 139, 250, 60]
                : [45, 212, 191, 18],
          getLineWidth: (f: { properties: { o: boolean } }) => (f.properties.o ? 4 : 1),
          lineWidthUnits: "pixels",
        }),
      );
    if (scenario) {
      out.push(
        new ScatterplotLayer<Facility>({
          id: "facility-halo",
          data: scenario.facilities.filter((f) => f.type !== "shelter"),
          getPosition: (f) => [f.lon, f.lat],
          getRadius: (f) => 400 + 2600 * probAtHours(facHours[f.facility_id] ?? [], t),
          getFillColor: (f) => {
            const p = probAtHours(facHours[f.facility_id] ?? [], t);
            return p > 0 ? [239, 68, 68, 70] : [0, 0, 0, 0];
          },
          updateTriggers: { getRadius: [t], getFillColor: [t] },
        }),
        new ScatterplotLayer<Facility>({
          id: "facilities",
          data: scenario.facilities,
          getPosition: (f) => [f.lon, f.lat],
          getRadius: (f) => (f.type === "district_hospital" ? 9 : f.type === "shelter" ? 5 : 7),
          radiusUnits: "pixels",
          stroked: true,
          getLineColor: [255, 255, 255, 255],
          lineWidthMinPixels: 1.5,
          getFillColor: (f) => {
            if (f.type === "shelter") return [56, 189, 248, 255];
            const p = probAtHours(facHours[f.facility_id] ?? [], t);
            return p >= 0.3 ? [127, 29, 29, 255] : p > 0 ? [249, 115, 22, 255] : [16, 185, 129, 255];
          },
          updateTriggers: { getFillColor: [t] },
          pickable: true,
        }),
        new ScatterplotLayer<Action>({
          id: "actions",
          data: scenario.actions.filter((a) => a.site).slice(0, 10),
          getPosition: (a) => [a.site?.lon ?? 0, a.site?.lat ?? 0],
          getRadius: 8,
          radiusUnits: "pixels",
          stroked: true,
          getLineColor: [250, 204, 21, 255],
          lineWidthMinPixels: 2.5,
          getFillColor: [250, 204, 21, 60],
          pickable: true,
        }),
      );
    }
    return out;
  }, [overlays, show, runId, t, base, scenario, facHours]);

  const onHover = (info: PickingInfo) => {
    const o = info.object as {
      properties?: Record<string, unknown>;
      name?: string;
      type?: string;
      facility_id?: string;
    } | null;
    if (!o) return setHover(null);
    if ((o as { action_id?: string }).action_id) {
      const a = o as unknown as Action;
      setHover(
        `Action ${a.rank}: stage an earthmover at the ${siteLabel(a)} by ${istAfter(a.deadline_utc, 0)} (${a.deadline_basis}) · closure ${pct(a.p_event)}`,
      );
    } else if (o.facility_id) {
      const f = o as Facility;
      setHover(
        `${TYPE_LABEL[f.type] ?? f.type}: ${f.name} · cut off by now: ${pct(probAtHours(facHours[f.facility_id] ?? [], t))}`,
      );
    } else if (o.properties && "pop" in o.properties) {
      const p = o.properties as DecileProps & { pop: number };
      setHover(
        `Settlement · ${fmtPeople(p.pop)} people · cut off from any public hospital by now: ${pct(probAt(p, t))}`,
      );
    } else if (o.properties && "rc" in o.properties) {
      const p = o.properties as DecileProps & { rc: string; ct: string };
      const kind = p.ct !== "none" ? ` (${p.ct})` : "";
      setHover(`${p.rc} road${kind} · closed by now: ${pct(probAt(p, t))}`);
    }
  };

  if (!scenario)
    return (
      <div className="grid h-screen place-items-center bg-bg">
        <AuroraLoader label="Loading the district forecast" />
      </div>
    );
  const hourly = scenario.hourly[Math.min(t, scenario.hourly.length - 1)];
  const hToLandfall = landfallH - t;
  const facilities = [...scenario.facilities]
    .filter((f) => f.type !== "shelter" && f.p_isolated_by_landfall !== null)
    .sort((a, b) => (b.p_isolated_by_landfall ?? 0) - (a.p_isolated_by_landfall ?? 0));
  const prov = scenario.provenance;
  const members = Object.entries(prov.members)
    .map(([k, v]) => `${k} ${v.toLocaleString("en-IN")}`)
    .join(" · ");

  return (
    <div className="flex h-screen flex-col bg-bg text-fg">
      <header className="flex flex-wrap items-center gap-x-5 gap-y-2 border-b border-border px-4 py-2.5 text-sm">
        <Link href="/" aria-label="AURORA Lifeline home" className="flex shrink-0 items-center">
          <Logo size={26} />
        </Link>
        <span className="hidden text-muted md:inline">{storm.name}</span>
        <span className="font-display font-semibold">{scenario.district_name}</span>
        {storm.runs.length > 1 && (
          <div
            className="flex rounded-full border border-border p-0.5"
            role="group"
            aria-label="IMD bulletin"
          >
            {storm.runs.map((r) => (
              <button
                key={r.runId}
                type="button"
                aria-pressed={activeRun === r.runId}
                title={r.label}
                onClick={() => setActiveRun(r.runId)}
                className={`rounded-full px-3 py-1 text-xs font-semibold transition-colors ${
                  activeRun === r.runId ? "bg-cyan text-primary-ink" : "text-muted hover:text-fg"
                }`}
              >
                Bulletin {r.bulletinNo}
              </button>
            ))}
          </div>
        )}
        <span
          className="chip border-warning/40 text-warning"
          title="Archived storm: asset-level results are public only for past storms"
        >
          Replay · IMD Bulletin {prov.imd_bulletin_no}, {istAfter(prov.imd_issued_at_utc, 0)} · past storm,
          not a live forecast
        </span>
        {prov.mode === "deterministic" && <span className="chip">deterministic: IMD track only</span>}
      </header>

      <div className="flex min-h-0 flex-1">
        <div className="relative min-w-0 flex-1">
          {MAPS_KEY ? (
            <APIProvider apiKey={MAPS_KEY}>
              <Map
                mapId={MAP_ID}
                defaultCenter={center}
                defaultZoom={9.5}
                defaultTilt={45}
                defaultHeading={-10}
                gestureHandling="greedy"
                colorScheme="DARK"
                disableDefaultUI
                style={{ width: "100%", height: "100%" }}
              >
                <DeckOverlay layers={layers.map((l) => l.clone({ onHover }))} />
              </Map>
            </APIProvider>
          ) : (
            <div className="p-8 text-muted">Set NEXT_PUBLIC_MAPS_API_KEY to show the map.</div>
          )}
          {hover && (
            <div className="pointer-events-none absolute left-3 top-3 max-w-md rounded bg-surface/90 px-3 py-2 text-xs shadow">
              {hover}
            </div>
          )}
          <div className="card absolute right-3 top-3 hidden bg-surface/85 p-3 text-[11px] backdrop-blur md:block">
            <p className="mb-1.5 font-semibold text-fg">Chance by the selected hour</p>
            <div className="h-1.5 w-44 rounded-full bg-[linear-gradient(90deg,#fde047,#f59e0b,#dc2626,#7f1d1d)]" />
            <div className="mt-1 flex justify-between text-subtle">
              <span>10%</span>
              <span>90%</span>
            </div>
            <ul className="mt-2 space-y-1 text-muted">
              <li>
                <span className="mr-2 inline-block h-0.5 w-4 bg-risk-2 align-middle" />
                road closed
              </li>
              <li>
                <span className="mr-2 inline-block size-2.5 rounded-sm bg-violet/70 align-middle" />
                village cut off from hospitals
              </li>
              <li>
                <span className="mr-2 inline-block size-2.5 rounded-full bg-safe align-middle" />
                facility reachable ·{" "}
                <span className="inline-block size-2.5 rounded-full bg-risk-3 align-middle" /> at risk
              </li>
              <li>
                <span className="mr-2 inline-block size-2.5 rounded-full border-2 border-risk-1 align-middle" />
                stage machinery here
              </li>
              <li>
                <span className="mr-2 inline-block h-0.5 w-4 bg-fg align-middle" />
                IMD official track
              </li>
            </ul>
          </div>
          <div className="absolute bottom-3 left-3 flex flex-wrap gap-2 text-xs">
            {(Object.keys(show) as Array<keyof typeof show>).map((k) => (
              <button
                key={k}
                onClick={() => setShow((s) => ({ ...s, [k]: !s[k] }))}
                className={`rounded px-2 py-1 ${show[k] ? "bg-cyan text-primary-ink" : "bg-surface-2 text-muted"}`}
              >
                {k === "surge" ? "surge (screening model)" : k === "flood" ? "rain flooding (prior)" : k}
              </button>
            ))}
          </div>
        </div>

        <aside className="w-[400px] shrink-0 overflow-y-auto border-l border-border p-4 text-sm">
          <div className="mb-3 flex gap-1" role="tablist">
            {(
              [
                ["forecast", "Forecast"],
                ["triggers", "Triggers"],
                ["advisory", "Advisory"],
                ["ask", "Ask AURORA"],
              ] as Array<[Tab, string]>
            ).map(([k, label]) => (
              <button
                key={k}
                role="tab"
                aria-selected={tab === k}
                onClick={() => setTab(k)}
                className={`flex-1 rounded px-2 py-1.5 text-xs font-medium ${tab === k ? "bg-cyan text-primary-ink" : "bg-surface-2 text-muted"}`}
              >
                {label}
              </button>
            ))}
          </div>
          {tab === "triggers" && <TriggerPanel scenario={scenario} />}
          {tab === "advisory" && <AdvisoryPanel runId={runId} lgd={lgd} />}
          {tab === "ask" && <AskPanel runId={runId} />}
          {tab === "forecast" && (
            <>
              <div className="text-xs uppercase tracking-wider text-muted">
                {istAfter(scenario.time_axis.now_utc, t)} ·{" "}
                {hToLandfall > 0
                  ? `T−${Math.round(hToLandfall)} h to forecast landfall`
                  : `T+${Math.round(-hToLandfall)} h after landfall`}
              </div>
              <div className="mt-3 rounded bg-surface p-3">
                <div className="text-muted">People cut off from any public hospital</div>
                <div className="mt-1 text-3xl font-semibold">{fmtPeople(hourly?.pop_cut_p50)}</div>
                <div className="text-xs text-muted">
                  P10–P90: {fmtPeople(hourly?.pop_cut_p10)} – {fmtPeople(hourly?.pop_cut_p90)} · across{" "}
                  {members}
                </div>
              </div>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="rounded bg-surface p-3">
                  <div className="text-xs text-muted">Health facilities cut off from referral (median)</div>
                  <div className="text-xl font-semibold">{hourly?.facilities_at_risk ?? "–"}</div>
                </div>
                <div className="rounded bg-surface p-3">
                  <div className="text-xs text-muted">By landfall (P10–P90)</div>
                  <div className="text-xl font-semibold">
                    {scenario.headline.pop_cut_hospital.p50 === null
                      ? "–"
                      : fmtPeople(scenario.headline.pop_cut_hospital.p50)}
                  </div>
                  <div className="text-xs text-muted">
                    {fmtPeople(scenario.headline.pop_cut_hospital.p10)} –{" "}
                    {fmtPeople(scenario.headline.pop_cut_hospital.p90)}
                  </div>
                </div>
              </div>

              <h3 className="mt-5 font-semibold">Health facilities most at risk</h3>
              <p className="text-xs text-muted">
                Chance of losing road access to referral care before landfall, with the likely window
                (P10–P90).
              </p>
              <ul className="mt-2 space-y-2">
                {facilities.slice(0, 12).map((f) => (
                  <li key={f.facility_id} className="rounded bg-surface p-2">
                    <div className="flex justify-between gap-2">
                      <span className="truncate">{f.name}</span>
                      <span className="font-semibold text-orange-300">{pct(f.p_isolated_by_landfall)}</span>
                    </div>
                    <div className="text-xs text-muted">
                      {TYPE_LABEL[f.type] ?? f.type}
                      {f.t10 && f.t90 ? ` · ${istAfter(f.t10, 0)} → ${istAfter(f.t90, 0)}` : ""}
                    </div>
                  </li>
                ))}
              </ul>

              <h3 className="mt-5 font-semibold">Actions before the roads close</h3>
              <ul className="mt-2 space-y-2">
                {scenario.actions.slice(0, 8).map((a) => (
                  <li key={a.action_id} className="rounded bg-surface p-2">
                    <div>
                      <span className="mr-1 rounded bg-yellow-400/20 px-1 text-xs text-yellow-300">
                        {a.rank}
                      </span>
                      Stage an earthmover at the {siteLabel(a)}
                    </div>
                    <div className="text-xs text-muted">
                      by {istAfter(a.deadline_utc, 0)} ({a.deadline_basis}) · ~{fmtPeople(a.people_protected)}{" "}
                      people · closure {pct(a.p_event)}
                    </div>
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-xs text-subtle">
                Parameters marked prior are uncalibrated. Surge is a screening upper bound, not a hydrodynamic
                model; IMD surge guidance takes precedence.
              </p>
            </>
          )}
        </aside>
      </div>

      <footer className="border-t border-border px-4 py-2">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setPlaying((p) => !p)}
            className="rounded bg-cyan text-primary-ink px-3 py-1 text-sm"
            aria-label={playing ? "Pause" : "Play"}
          >
            {playing ? "Pause" : "Play"}
          </button>
          <input
            type="range"
            min={0}
            max={nSteps}
            value={t}
            onChange={(e) => setT(Number(e.target.value))}
            className="flex-1"
            aria-label="Hours after the bulletin"
          />
          <span className="w-44 text-right text-xs text-muted">
            {istAfter(scenario.time_axis.now_utc, t)}
          </span>
        </div>
        <div className="mt-1 text-[11px] text-subtle">
          Derived from IMD National Bulletin No. {prov.imd_bulletin_no} issued{" "}
          {istAfter(prov.imd_issued_at_utc, 0)} · members: {members} · ensemble aligned to the IMD official
          forecast · WeatherNext and ECMWF are a non-official uncertainty envelope ·{" "}
          {storm.observedLandfall.text} · code {prov.code_sha.slice(0, 7)}
        </div>
      </footer>
    </div>
  );
}
