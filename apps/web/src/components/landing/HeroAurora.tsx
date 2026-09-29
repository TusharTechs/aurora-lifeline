"use client";

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "@/components/site/A11yControl";

export type HeroTrack = { s: string; h0: number; step: number; pts: Array<[number, number]> };
export type HeroFacility = { name: string; lon: number; lat: number; hours: Array<number | null> };
export type HeroData = {
  bbox: [number, number, number, number];
  coast: Array<Array<[number, number]>>;
  tracks: HeroTrack[];
  official: HeroTrack;
  facilities: HeroFacility[];
  hourly: number[]; // median people cut off from every public hospital, by hour after the bulletin
  landfallH: number;
  nowUtc: string;
  members: number;
  bulletinNo: string;
  district: string;
};

const SOURCE_RGB: Record<string, string> = {
  ECMWF: "165,139,255",
  WNX: "92,200,255",
  WNX_LARGE: "62,230,196",
};
const LOOP_S = 14;
const HOLD_S = 2.5;

function probAt(hours: Array<number | null>, t: number): number {
  let p = 0;
  hours.forEach((h, i) => {
    if (h !== null && h <= t) p = (i + 1) / 10;
  });
  return p;
}

function riskRgb(p: number): string {
  if (p <= 0) return "62,230,196";
  if (p < 0.2) return "253,224,71";
  if (p < 0.4) return "245,158,11";
  return "239,68,68";
}

function posAt(tr: HeroTrack, t: number): [number, number] | null {
  const f = (t - tr.h0) / tr.step;
  if (f < 0 || f > tr.pts.length - 1) return null;
  const i = Math.floor(f);
  const a = tr.pts[i]!;
  const b = tr.pts[Math.min(i + 1, tr.pts.length - 1)]!;
  const k = f - i;
  return [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k];
}

function lakh(n: number): string {
  return n >= 100_000
    ? `${(n / 100_000).toFixed(1)} lakh`
    : Math.round(n / 100) * 100 > 0
      ? (Math.round(n / 100) * 100).toLocaleString("en-IN")
      : "0";
}

function istLabel(nowUtc: string, h: number): string {
  const d = new Date(Date.parse(nowUtc) + h * 3_600_000);
  return new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(d);
}

export function HeroAurora({ data }: { data: HeroData }) {
  const wrap = useRef<HTMLDivElement>(null);
  const canvas = useRef<HTMLCanvasElement>(null);
  const reduced = useReducedMotion();
  const end = data.landfallH + 6;
  const [t, setT] = useState(reduced ? data.landfallH : 0);
  const [manual, setManual] = useState(false);
  const tRef = useRef(t);
  const lens = useRef<{ x: number; y: number; on: boolean }>({ x: 0, y: 0, on: false });

  useEffect(() => {
    tRef.current = t;
  }, [t]);

  useEffect(() => {
    const cv = canvas.current;
    const box = wrap.current;
    if (!cv || !box) return;
    const ctx = cv.getContext("2d");
    if (!ctx) return;
    const stat = document.createElement("canvas");
    const sctx = stat.getContext("2d")!;
    let w = 0;
    let h = 0;
    let dpr = 1;
    const [x0, y0, x1, y1] = data.bbox;
    const kx = Math.cos(((y0 + y1) / 2) * (Math.PI / 180));
    let scale = 1;
    let ox = 0;
    let oy = 0;
    const proj = (lon: number, lat: number): [number, number] => [
      ox + (lon - x0) * kx * scale,
      oy + (y1 - lat) * scale,
    ];

    const layout = () => {
      const r = box.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = r.width;
      h = r.height;
      for (const c of [cv, stat]) {
        c.width = Math.round(w * dpr);
        c.height = Math.round(h * dpr);
      }
      cv.style.width = `${w}px`;
      cv.style.height = `${h}px`;
      const gw = (x1 - x0) * kx;
      const gh = y1 - y0;
      scale = Math.min(w / gw, (h - 72) / gh) * 0.98;
      ox = w - gw * scale; // anchor the geography to the right edge; text sits on the left
      oy = Math.max(64, (h - gh * scale) / 2); // keep the coast clear of the navigation bar
      // Static layer: coastline, then every storm future accumulating light additively.
      sctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      sctx.clearRect(0, 0, w, h);
      sctx.lineCap = "round";
      sctx.lineJoin = "round";
      sctx.globalCompositeOperation = "lighter";
      for (const tr of data.tracks) {
        sctx.strokeStyle = `rgba(${SOURCE_RGB[tr.s] ?? "92,200,255"},${tr.s === "WNX_LARGE" ? 0.05 : 0.11})`;
        sctx.lineWidth = tr.s === "WNX_LARGE" ? 1.1 : 1.4;
        sctx.beginPath();
        tr.pts.forEach(([lon, lat], i) => {
          const [px, py] = proj(lon, lat);
          if (i) sctx.lineTo(px, py);
          else sctx.moveTo(px, py);
        });
        sctx.stroke();
      }
      sctx.globalCompositeOperation = "source-over";
      sctx.strokeStyle = "rgba(255,226,184,0.55)";
      sctx.lineWidth = 1.3;
      for (const line of data.coast) {
        sctx.beginPath();
        line.forEach(([lon, lat], i) => {
          const [px, py] = proj(lon, lat);
          if (i) sctx.lineTo(px, py);
          else sctx.moveTo(px, py);
        });
        sctx.stroke();
      }
      sctx.strokeStyle = "rgba(255,226,184,0.9)";
      sctx.lineWidth = 2.2;
      sctx.setLineDash([2, 5]);
      sctx.beginPath();
      data.official.pts.forEach(([lon, lat], i) => {
        const [px, py] = proj(lon, lat);
        if (i) sctx.lineTo(px, py);
        else sctx.moveTo(px, py);
      });
      sctx.stroke();
      sctx.setLineDash([]);
    };

    const draw = () => {
      const tt = tRef.current;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, cv.width, cv.height);
      ctx.drawImage(stat, 0, 0);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      const L = lens.current;
      if (L.on) {
        // The lens: the futures under the pointer glow brighter.
        ctx.save();
        ctx.beginPath();
        ctx.arc(L.x, L.y, 90, 0, Math.PI * 2);
        ctx.clip();
        ctx.globalCompositeOperation = "lighter";
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.drawImage(stat, 0, 0);
        ctx.drawImage(stat, 0, 0);
        ctx.restore();
        const g = ctx.createRadialGradient(L.x, L.y, 0, L.x, L.y, 110);
        g.addColorStop(0, "rgba(255,226,184,0.10)");
        g.addColorStop(1, "rgba(255,226,184,0)");
        ctx.fillStyle = g;
        ctx.fillRect(L.x - 110, L.y - 110, 220, 220);
      }
      // Where each future puts the storm now.
      ctx.globalCompositeOperation = "lighter";
      for (const tr of data.tracks) {
        const p = posAt(tr, tt);
        if (!p) continue;
        const [px, py] = proj(p[0], p[1]);
        ctx.fillStyle = `rgba(${SOURCE_RGB[tr.s] ?? "92,200,255"},0.55)`;
        ctx.fillRect(px - 1.2, py - 1.2, 2.4, 2.4);
      }
      ctx.globalCompositeOperation = "source-over";
      const op = posAt(data.official, tt);
      if (op) {
        const [px, py] = proj(op[0], op[1]);
        const g = ctx.createRadialGradient(px, py, 0, px, py, 26);
        g.addColorStop(0, "rgba(255,226,184,0.55)");
        g.addColorStop(1, "rgba(255,226,184,0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(px, py, 26, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#fff7ea";
        ctx.beginPath();
        ctx.arc(px, py, 3.5, 0, Math.PI * 2);
        ctx.fill();
      }
      // Health facilities: teal while reachable, warming to red as the chance of being cut off rises.
      for (const f of data.facilities) {
        const p = probAt(f.hours, tt);
        const [px, py] = proj(f.lon, f.lat);
        const rgb = riskRgb(p);
        if (p > 0) {
          ctx.fillStyle = `rgba(${rgb},0.18)`;
          ctx.beginPath();
          ctx.arc(px, py, 4 + 10 * p, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.fillStyle = `rgb(${rgb})`;
        ctx.beginPath();
        ctx.arc(px, py, 2.2, 0, Math.PI * 2);
        ctx.fill();
      }
    };

    layout();
    draw();
    const ro = new ResizeObserver(() => {
      layout();
      draw();
    });
    ro.observe(box);

    let raf = 0;
    let visible = true;
    const io = new IntersectionObserver(([e]) => {
      visible = !!e?.isIntersecting;
    });
    io.observe(box);
    let last = performance.now();
    let hold = 0;
    const tick = (now: number) => {
      raf = requestAnimationFrame(tick);
      const dt = Math.min((now - last) / 1000, 0.1);
      last = now;
      if (!visible || document.hidden) return;
      if (!reduced && !manual) {
        if (tRef.current >= end) {
          hold += dt;
          if (hold > HOLD_S) {
            hold = 0;
            tRef.current = 0;
          }
        } else {
          tRef.current = Math.min(end, tRef.current + (end / LOOP_S) * dt);
        }
      }
      draw();
    };
    raf = requestAnimationFrame(tick);
    const hud = window.setInterval(() => setT(Math.round(tRef.current)), 200);

    const move = (e: PointerEvent) => {
      const r = cv.getBoundingClientRect();
      lens.current = { x: e.clientX - r.left, y: e.clientY - r.top, on: true };
    };
    const leave = () => {
      lens.current.on = false;
    };
    cv.addEventListener("pointermove", move);
    cv.addEventListener("pointerdown", move);
    cv.addEventListener("pointerleave", leave);
    return () => {
      cancelAnimationFrame(raf);
      window.clearInterval(hud);
      ro.disconnect();
      io.disconnect();
      cv.removeEventListener("pointermove", move);
      cv.removeEventListener("pointerdown", move);
      cv.removeEventListener("pointerleave", leave);
    };
  }, [data, reduced, manual, end]);

  const hToLandfall = data.landfallH - t;
  const pop = data.hourly[Math.max(0, Math.min(t, data.hourly.length - 1))] ?? 0;
  const atRisk = data.facilities.filter((f) => probAt(f.hours, t) > 0).length;

  return (
    <div ref={wrap} className="absolute inset-0">
      <canvas
        ref={canvas}
        role="img"
        aria-label={`Animated map: ${data.members.toLocaleString("en-IN")} possible tracks of Cyclone Montha from IMD Bulletin ${data.bulletinNo} converge on the Andhra Pradesh coast; health facilities around ${data.district} change colour as their chance of losing road access rises.`}
        className="h-full w-full touch-pan-y"
      />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(90deg,var(--color-bg)_0%,rgb(5_8_15/0.92)_34%,rgb(5_8_15/0.25)_62%,transparent_80%)] max-lg:bg-[linear-gradient(180deg,var(--color-bg)_0%,transparent_16%)]" />
      <div className="absolute bottom-5 right-4 z-10 w-[min(360px,calc(100%-2rem))] sm:right-6 lg:left-[50%] lg:right-auto">
        <div className="card bg-surface/70 p-3 backdrop-blur-md">
          <div className="flex items-center justify-between text-xs text-muted">
            <span className="inline-flex items-center gap-2">
              <span className="pulse-dot text-teal" aria-hidden />
              {hToLandfall > 0
                ? `T−${Math.round(hToLandfall)} h to landfall`
                : `T+${Math.round(-hToLandfall)} h after landfall`}
            </span>
            <span>{istLabel(data.nowUtc, t)} IST</span>
          </div>
          <div className="mt-2 grid grid-cols-2 gap-3" aria-live="off">
            <div>
              <div className="font-display text-2xl font-semibold tabular-nums">{lakh(pop)}</div>
              <div className="text-[11px] leading-tight text-muted">
                people cut off from every public hospital (median)
              </div>
            </div>
            <div>
              <div className="font-display text-2xl font-semibold tabular-nums">
                {atRisk}
                <span className="text-sm font-normal text-muted">/{data.facilities.length}</span>
              </div>
              <div className="text-[11px] leading-tight text-muted">
                {data.district} health facilities at any risk
              </div>
            </div>
          </div>
          <label className="mt-2 block">
            <span className="sr-only">Hours after the bulletin</span>
            <input
              type="range"
              min={0}
              max={end}
              value={t}
              onChange={(e) => {
                setManual(true);
                tRef.current = Number(e.target.value);
                setT(Number(e.target.value));
              }}
              className="w-full accent-[var(--color-cyan)]"
            />
          </label>
          <div className="flex items-center justify-between text-[11px] text-subtle">
            <span>
              {manual ? (
                <button type="button" className="underline hover:text-fg" onClick={() => setManual(false)}>
                  Resume
                </button>
              ) : (
                "Drag to scrub"
              )}
            </span>
            <span className="inline-flex items-center gap-2">
              <i className="inline-block h-0.5 w-4 rounded bg-dawn" aria-hidden /> IMD track
              <i
                className="inline-block h-0.5 w-4 rounded"
                style={{ background: "var(--aurora-gradient)" }}
                aria-hidden
              />{" "}
              futures
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
