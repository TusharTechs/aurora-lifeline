"use client";

import { useState } from "react";
import type { DistrictScenario } from "@/contracts";
import { submitFieldReport, type FieldResult } from "@/lib/api";
import { ist, siteLabel } from "@/lib/format";

const DEMO_PHOTO = "/demo/field-report-flooded-road.jpg";
const LABEL: Record<string, string> = {
  yes: "Passable",
  no: "Not passable",
  unknown: "Passability unknown",
  none: "no water",
  lt_15cm: "water under 15 cm",
  "15_30cm": "water 15–30 cm",
  "30_60cm": "water 30–60 cm",
  gt_60cm: "water over 60 cm",
};

export type FieldMark = { lat: number; lon: number; label: string; passable: string };

/** After landfall: a field photo, assessed by Gemini, routed by rules, confirmed by an officer. */
export function FieldPanel({
  runId,
  scenario,
  onConfirm,
}: {
  runId: string;
  scenario: DistrictScenario;
  onConfirm: (m: FieldMark) => void;
}) {
  const sites = scenario.actions.filter((a) => a.site).slice(0, 10);
  const [action, setAction] = useState(sites[0]?.action_id ?? "");
  const [photo, setPhoto] = useState<{ blob: Blob; url: string; demo: boolean } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [res, setRes] = useState<FieldResult | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const claimedTime = ist(
    new Date(Date.parse(scenario.time_axis.landfall_utc) + 6 * 3_600_000).toISOString(),
    true,
  );

  const loadDemo = async () => {
    const blob = await (await fetch(DEMO_PHOTO)).blob();
    setPhoto({ blob, url: DEMO_PHOTO, demo: true });
    setRes(null);
    setConfirmed(false);
  };
  const submit = async () => {
    if (!photo) return;
    setBusy(true);
    setError(null);
    setConfirmed(false);
    try {
      setRes(await submitFieldReport(photo.blob, runId, scenario.district_lgd, action, claimedTime));
    } catch (e) {
      setError(e instanceof Error ? e.message : "The report could not be assessed.");
    } finally {
      setBusy(false);
    }
  };
  const o = res?.observation;
  const claimedSite = sites.find((a) => a.action_id === action);

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted">
        After landfall, a field team sends a photo. Gemini assesses it; fixed rules decide whether it can
        update the map or must go to an officer. Bridge reopenings always need an officer.
      </p>
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => void loadDemo()} className="btn btn-ghost !min-h-10 text-xs">
          Use the demo photo
        </button>
        <label className="btn btn-ghost !min-h-10 cursor-pointer text-xs">
          Upload a photo
          <input
            type="file"
            accept="image/jpeg,image/png"
            className="sr-only"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) {
                setPhoto({ blob: f, url: URL.createObjectURL(f), demo: false });
                setRes(null);
              }
            }}
          />
        </label>
      </div>
      {photo && (
        <figure className="card overflow-hidden">
          {/* eslint-disable-next-line @next/next/no-img-element -- static export, local file */}
          <img
            src={photo.url}
            alt="Field photo: a road under flood water"
            className="max-h-56 w-full object-cover"
          />
          <figcaption className="p-2 text-[10px] leading-snug text-subtle">
            <span className="mr-1 rounded bg-sim/20 px-1 font-semibold text-sim">SIMULATED</span>
            {photo.demo ? (
              <>
                Photo: Navaneeth Krishnan S, &ldquo;Kerala Flood 9-8-2019 at Kidangoor–Mookkannoor road near
                Angamaly&rdquo;, CC BY-SA 3.0, via Wikimedia Commons (resized; metadata removed). Not from
                Cyclone Montha; used to demonstrate the check.
              </>
            ) : (
              "Your photo; metadata is removed before the model sees it."
            )}
          </figcaption>
        </figure>
      )}
      <label className="block text-xs">
        <span className="text-muted">Claimed place</span>
        <select
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="mt-1 w-full rounded-lg bg-surface-2 px-2 py-1.5 text-xs"
        >
          {sites.map((a) => (
            <option key={a.action_id} value={a.action_id}>
              {siteLabel(a.site)}
            </option>
          ))}
        </select>
        <span className="mt-1 block text-subtle">
          Claimed time: {claimedTime} (six hours after forecast landfall)
        </span>
      </label>
      <button
        type="button"
        disabled={!photo || busy}
        onClick={() => void submit()}
        className="btn btn-primary w-full text-sm"
      >
        {busy ? "Gemini is assessing the photo…" : "Send the field report"}
      </button>
      {error && (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      )}
      {res && o && (
        <div className="card space-y-3 p-3 text-xs" aria-live="polite">
          <div className="flex flex-wrap gap-1.5">
            <span
              className={`chip ${o.passable === "no" ? "border-danger/50 text-danger" : o.passable === "yes" ? "border-safe/50 text-safe" : ""}`}
            >
              {LABEL[o.passable]}
            </span>
            <span className="chip">{LABEL[o.water_depth_band] ?? o.water_depth_band}</span>
            <span className="chip">damage: {o.damage_state}</span>
            <span className="chip">blocked by: {o.blockage}</span>
            <span className="chip">place: {o.location_consistency}</span>
            <span className="chip">time: {o.time_consistency}</span>
            <span className="chip">confidence: {res.confidence_band}</span>
          </div>
          {o.evidence_notes ? (
            <p className="text-muted">
              &ldquo;{o.evidence_notes}&rdquo; ({res.model})
            </p>
          ) : (
            <p className="text-subtle">
              Gemini&apos;s notes were withheld: they contained a number, and only the engine may show
              numbers. The depth band above is a fixed category.
            </p>
          )}
          <div
            className={`rounded-lg p-2 ${res.routing.decision === "auto_apply" ? "bg-safe/10" : "bg-warning/10"}`}
          >
            <p className="font-semibold">
              {res.routing.decision === "auto_apply"
                ? "Applied to the map by rule"
                : "Sent to the officer queue"}
            </p>
            {res.routing.reasons.length > 0 && (
              <ul className="mt-1 list-disc pl-4 text-muted">
                {res.routing.reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            )}
          </div>
          {res.routing.decision === "officer_queue" && claimedSite?.site && (
            <button
              type="button"
              disabled={confirmed}
              onClick={() => {
                setConfirmed(true);
                onConfirm({
                  lat: claimedSite.site!.lat,
                  lon: claimedSite.site!.lon,
                  label: siteLabel(claimedSite.site),
                  passable: o.passable,
                });
              }}
              className="btn btn-ghost w-full !min-h-10 text-xs"
            >
              {confirmed
                ? "Confirmed by the demo officer (SIMULATED) · marked on the map"
                : "Confirm as officer (SIMULATED)"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
