"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import coast from "@/data/coast.json";
import { useSearchParams } from "next/navigation";
import {
  getSeason,
  readKnownBulletin,
  readLatestBulletin,
  readUploadedBulletin,
  type BulletinResult,
  type Season,
} from "@/lib/api";
import { ist } from "@/lib/format";

const STAGES = ["Fetching the PDF", "Gemini is reading it", "Checking every value in code"];
const STAGE_LABEL: Record<string, string> = {
  D: "Depression",
  DD: "Deep Depression",
  CS: "Cyclonic Storm",
  SCS: "Severe Cyclonic Storm",
  VSCS: "Very Severe Cyclonic Storm",
  ESCS: "Extremely Severe Cyclonic Storm",
  SuCS: "Super Cyclonic Storm",
  LPA: "Low pressure area",
  WML: "Well-marked low",
};
const COVERAGE: Record<string, string> = {
  isolated: "isolated places",
  a_few: "a few places",
  many: "many places",
  most: "most places",
  unspecified: "unspecified",
};

type Props = { stormId: string; known: Array<{ bulletinNo: string; label: string; runHref: string }> };

export function BulletinReader({ stormId, known }: Props) {
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [res, setRes] = useState<BulletinResult | null>(null);
  const [drag, setDrag] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  const [season, setSeason] = useState<Season | null>(null);
  const params = useSearchParams();
  const wantLatest = params.get("latest") === "1";
  useEffect(() => {
    let alive = true;
    void getSeason().then((v) => alive && setSeason(v));
    return () => {
      alive = false;
    };
  }, []);

  const run = async (fn: () => Promise<BulletinResult>) => {
    setBusy(true);
    setError(null);
    setRes(null);
    setStage(0);
    const timers = [window.setTimeout(() => setStage(1), 900), window.setTimeout(() => setStage(2), 9000)];
    try {
      setRes(await fn());
    } catch (e) {
      setError(e instanceof Error ? e.message : "The bulletin could not be read.");
    } finally {
      timers.forEach(clearTimeout);
      setBusy(false);
    }
  };
  const onFile = (f: File | undefined) => {
    if (!f) return;
    if (f.type && f.type !== "application/pdf") {
      setError("Please choose a PDF file from IMD's RSMC archive.");
      return;
    }
    if (f.size > 5 * 1024 * 1024) {
      setError("That PDF is larger than 5 MB.");
      return;
    }
    void run(() => readUploadedBulletin(f));
  };

  const r = res?.reading;
  const quoteFor = (path: string) => r?.source_quotes.find((q) => q.path.startsWith(path))?.quote;
  const knownRun = res?.known ? known.find((k) => k.bulletinNo === res.known?.bulletin_no) : undefined;

  return (
    <div className="space-y-10">
      <div className="grid gap-4 lg:grid-cols-[1fr_1.2fr]">
        <div className="card p-6">
          <h2 className="font-display text-lg font-semibold">Read an IMD bulletin</h2>
          <p className="mt-1 text-sm text-muted">
            Fetched live from IMD&apos;s RSMC archive and verified by checksum. AURORA never re-hosts IMD
            documents.
          </p>
          <div className="mt-4 grid gap-2">
            {season?.active && season.latest && (
              <button
                type="button"
                disabled={busy}
                onClick={() => void run(() => readLatestBulletin())}
                className={`btn justify-between !rounded-2xl text-left text-sm ${wantLatest ? "btn-primary" : "btn-ghost !border-warning/50"}`}
              >
                <span>
                  <span className="mr-2 inline-block rounded-full bg-warning/20 px-2 py-0.5 text-[11px] font-semibold text-warning">
                    LIVE
                  </span>
                  IMD National Bulletin No. {season.latest.bulletin_no ?? "?"} · {season.latest.based_on_ist}
                </span>
                <span aria-hidden>→</span>
              </button>
            )}
            {known.map((k) => (
              <button
                key={k.bulletinNo}
                type="button"
                disabled={busy}
                onClick={() => void run(() => readKnownBulletin(stormId, k.bulletinNo))}
                className="btn btn-ghost justify-between !rounded-2xl text-left text-sm"
              >
                <span>{k.label}</span>
                <span aria-hidden>→</span>
              </button>
            ))}
          </div>
        </div>
        <div
          className={`card flex flex-col items-center justify-center gap-3 border-dashed p-8 text-center transition-colors ${
            drag ? "!border-cyan bg-surface-2" : ""
          }`}
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDrag(false);
            onFile(e.dataTransfer.files[0]);
          }}
        >
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" aria-hidden className="text-cyan">
            <path
              d="M14 3H7a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V8l-5-5z"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <path
              d="M14 3v5h5M12 12v6m0-6l-2.5 2.5M12 12l2.5 2.5"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <p className="font-display text-lg font-semibold">Or read any IMD cyclone bulletin</p>
          <p className="max-w-sm text-sm text-muted">
            Drop a National or RSMC bulletin PDF from rsmcnewdelhi.imd.gov.in (up to 5 MB). It is read,
            checked and discarded; only the reading is cached, keyed by the file&apos;s checksum.
          </p>
          <input
            ref={fileRef}
            type="file"
            accept="application/pdf"
            className="sr-only"
            id="bulletin-file"
            onChange={(e) => onFile(e.target.files?.[0])}
          />
          <label
            htmlFor="bulletin-file"
            className={`btn btn-primary text-sm ${busy ? "pointer-events-none opacity-50" : "cursor-pointer"}`}
          >
            Choose a PDF
          </label>
        </div>
      </div>

      <div aria-live="polite" aria-busy={busy}>
        {busy && (
          <ol className="card mx-auto max-w-xl space-y-3 p-6">
            {STAGES.map((s, i) => (
              <li
                key={s}
                className={`flex items-center gap-3 text-sm ${i <= stage ? "text-fg" : "text-subtle"}`}
              >
                {i < stage ? (
                  <span className="text-safe" aria-hidden>
                    ✓
                  </span>
                ) : i === stage ? (
                  <span className="pulse-dot text-cyan" aria-hidden />
                ) : (
                  <span className="inline-block size-2 rounded-full bg-border" aria-hidden />
                )}
                {s}
                {i === stage && <span className="sr-only">(in progress)</span>}
              </li>
            ))}
          </ol>
        )}
        {error && (
          <div role="alert" className="card mx-auto max-w-xl border-danger/40 p-5">
            <p className="font-semibold">The bulletin could not be read</p>
            <p className="mt-1 text-sm text-muted">{error}</p>
          </div>
        )}
      </div>

      {res && r && (
        <article className="space-y-6" aria-labelledby="reading-title">
          <header className="card atmosphere overflow-hidden p-6 sm:p-8">
            <div className="flex flex-wrap gap-2 text-xs">
              <span className="chip border-warning/40 text-warning">Pending officer confirmation</span>
              {res.needs_review ? (
                <span className="chip border-danger/40 text-danger">✕ Needs review: a check failed</span>
              ) : (
                <span className="chip border-safe/40 text-safe">✓ All applicable checks passed</span>
              )}
              {res.cached && <span className="chip">cached reading</span>}
              <span className="chip">
                {res.model} · {res.prompt_version}
              </span>
            </div>
            <h2 id="reading-title" className="mt-4 font-display text-2xl font-semibold sm:text-3xl">
              IMD bulletin No. {r.bulletin_no}
              {r.system_name ? ` · ${r.system_name}` : ""} · {STAGE_LABEL[r.system_stage] ?? r.system_stage}
            </h2>
            <p className="mt-2 text-muted">
              Issued {r.issued_at_utc ? ist(r.issued_at_utc, true) : r.issued_at_text} · {res.pages} page
              {res.pages === 1 ? "" : "s"} · values below are IMD&apos;s, as read by Gemini
            </p>
            {res.labels && (
              <p className="mt-4 text-sm">
                <span className="font-display text-xl font-semibold text-teal">
                  {res.labels.agree} of {res.labels.total}
                </span>{" "}
                <span className="text-muted">
                  fields agree with the hand-checked reading of this bulletin
                </span>
                {res.labels.differs.length > 0 && (
                  <span className="text-subtle"> · differs: {res.labels.differs.join(", ")}</span>
                )}
              </p>
            )}
          </header>

          <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
            <section className="card p-6" aria-labelledby="track-title">
              <h3 id="track-title" className="font-display text-lg font-semibold">
                Forecast track
              </h3>
              <TrackPlot
                current={[r.current.lon, r.current.lat]}
                points={r.forecast.map((p) => [p.lon, p.lat, p.lead_h])}
              />
              <p className="mt-2 text-xs text-subtle">
                Now: {r.current.lat}°N {r.current.lon}°E · {r.current.msw_min ?? "?"}–
                {r.current.msw_max ?? "?"} {r.current.wind_unit}
                {r.current.gust_value ? ` gusting ${r.current.gust_value}` : ""}. Coastline © OpenStreetMap
                contributors.
              </p>
            </section>
            <section className="card p-6" aria-labelledby="checks-title">
              <h3 id="checks-title" className="font-display text-lg font-semibold">
                Checked in code
              </h3>
              <ul className="mt-3 space-y-2.5">
                {res.checks.map((c) => (
                  <li key={c.id} className="flex gap-3 text-sm">
                    <span
                      className={`mt-0.5 w-12 shrink-0 text-xs font-semibold ${
                        c.status === "pass"
                          ? "text-safe"
                          : c.status === "fail"
                            ? "text-danger"
                            : "text-subtle"
                      }`}
                    >
                      {c.status === "pass" ? "✓ pass" : c.status === "fail" ? "✕ fail" : "– n/a"}
                    </span>
                    <span>
                      {c.label}
                      <span className="block text-xs text-subtle">{c.detail}</span>
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          </div>

          <section className="card overflow-x-auto p-6" aria-labelledby="fc-title">
            <h3 id="fc-title" className="font-display text-lg font-semibold">
              Forecast table
            </h3>
            <table className="mt-3 w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs text-subtle">
                <tr>
                  <th className="py-2 pr-3 font-normal">Lead</th>
                  <th className="py-2 pr-3 font-normal">Valid</th>
                  <th className="py-2 pr-3 font-normal">Position</th>
                  <th className="py-2 pr-3 font-normal">Wind</th>
                  <th className="py-2 pr-3 font-normal">Category</th>
                  <th className="py-2 font-normal">IMD&apos;s words</th>
                </tr>
              </thead>
              <tbody>
                {r.forecast.map((p, i) => (
                  <tr key={p.lead_h} className="border-t border-border align-top">
                    <td className="py-2 pr-3 tabular-nums">+{p.lead_h} h</td>
                    <td className="py-2 pr-3 tabular-nums">
                      {p.valid_at_utc ? ist(p.valid_at_utc) : (p.valid_at_text ?? "–")}
                    </td>
                    <td className="py-2 pr-3 tabular-nums">
                      {p.lat}°N {p.lon}°E
                    </td>
                    <td className="py-2 pr-3 tabular-nums">
                      {p.msw_min}–{p.msw_max} {p.wind_unit}
                      {p.gust_value ? `, gust ${p.gust_value}` : ""}
                    </td>
                    <td className="py-2 pr-3">{p.category}</td>
                    <td className="py-2 text-xs text-muted">{quoteFor(`forecast[${i}]`) ?? "–"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <div className="grid gap-6 lg:grid-cols-2">
            <section className="card p-6" aria-labelledby="lf-title">
              <h3 id="lf-title" className="font-display text-lg font-semibold">
                Landfall and surge
              </h3>
              {r.landfall ? (
                <p className="mt-3">
                  “{r.landfall.window_text}”, {r.landfall.location_text}
                  <span className="block text-xs text-subtle">
                    IMD&apos;s words; converted to a time only by the engine.
                  </span>
                </p>
              ) : (
                <p className="mt-3 text-muted">No landfall forecast in this bulletin.</p>
              )}
              <ul className="mt-4 space-y-1 text-sm">
                {r.surge.map((s) => (
                  <li key={s.area_text}>
                    Surge {s.height_m_min ?? "?"}–{s.height_m_max ?? "?"} m: {s.area_text}
                  </li>
                ))}
                {r.surge.length === 0 && (
                  <li className="text-muted">No storm-surge guidance in this bulletin.</li>
                )}
              </ul>
            </section>
            <section className="card overflow-x-auto p-6" aria-labelledby="rain-title">
              <h3 id="rain-title" className="font-display text-lg font-semibold">
                Heavy rainfall warnings
              </h3>
              <ul className="mt-3 space-y-2 text-sm">
                {r.rainfall_warnings.map((w, i) => (
                  <li
                    key={`${w.area_text}${w.date_text}${i}`}
                    className="border-t border-border pt-2 first:border-0 first:pt-0"
                  >
                    <span className="font-semibold">{w.category.replaceAll("_", " ")}</span> at{" "}
                    {COVERAGE[w.coverage]} · {w.date_text}
                    <span className="block text-xs text-muted">{w.area_text}</span>
                  </li>
                ))}
                {r.rainfall_warnings.length === 0 && <li className="text-muted">None stated.</li>}
              </ul>
            </section>
          </div>

          <section className="card p-6">
            <h3 className="font-display text-lg font-semibold">What happens next</h3>
            <p className="mt-2 max-w-3xl text-muted">
              An officer confirms these fields. The confirmed track becomes member 0 of a storm run: the
              ensemble members published by this bulletin&apos;s issue time are aligned to it, and the
              district answers follow.
            </p>
            {knownRun && (
              <Link href={knownRun.runHref} className="btn btn-primary mt-4 text-sm">
                See the district forecast from this bulletin
              </Link>
            )}
          </section>
        </article>
      )}
    </div>
  );
}

/** Track over the coastline, equirectangular, fitted to the points (a sketch, not a map). */
function TrackPlot({
  current,
  points,
}: {
  current: [number, number];
  points: Array<[number, number, number]>;
}) {
  const all = [current, ...points.map(([x, y]) => [x, y] as [number, number])];
  const xs = all.map((p) => p[0]);
  const ys = all.map((p) => p[1]);
  const pad = 1.2;
  const x0 = Math.min(...xs) - pad;
  const x1 = Math.max(...xs) + pad;
  const y0 = Math.min(...ys) - pad;
  const y1 = Math.max(...ys) + pad;
  const W = 480;
  const H = Math.max(
    220,
    Math.min(360, (W * (y1 - y0)) / ((x1 - x0) * Math.cos((((y0 + y1) / 2) * Math.PI) / 180))),
  );
  const px = (lon: number) => ((lon - x0) / (x1 - x0)) * W;
  const py = (lat: number) => ((y1 - lat) / (y1 - y0)) * H;
  const lines = (coast as unknown as { lines: Array<Array<[number, number]>> }).lines;
  const path = all.map(([x, y], i) => `${i ? "L" : "M"}${px(x).toFixed(1)} ${py(y).toFixed(1)}`).join("");
  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="mt-3 w-full"
      role="img"
      aria-label={`Forecast track with ${points.length} points`}
    >
      {lines.map((l, i) => (
        <path
          key={i}
          d={l.map(([x, y], j) => `${j ? "L" : "M"}${px(x).toFixed(1)} ${py(y).toFixed(1)}`).join("")}
          fill="none"
          stroke="var(--color-dawn)"
          strokeOpacity=".5"
          strokeWidth="1.2"
        />
      ))}
      <path d={path} fill="none" stroke="var(--color-cyan)" strokeWidth="2" strokeDasharray="4 4" />
      {points.map(([x, y, h]) => (
        <g key={h}>
          <circle cx={px(x)} cy={py(y)} r="4" fill="var(--color-cyan)" />
          <text x={px(x) + 7} y={py(y) - 6} fontSize="11" fill="var(--color-muted)">
            +{h}h
          </text>
        </g>
      ))}
      <circle cx={px(current[0])} cy={py(current[1])} r="6" fill="var(--color-dawn)" />
    </svg>
  );
}
