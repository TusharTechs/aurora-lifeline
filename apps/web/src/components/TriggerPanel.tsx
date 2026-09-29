"use client";

import type { DistrictScenario } from "@/contracts";
import { cleanName, ist, pct, people, siteLabel } from "@/lib/format";

/**
 * Indicative anticipatory-action triggers, evaluated deterministically on the published forecast.
 * The pattern follows forecast-based action practice (pre-agreed thresholds, lead times and
 * stop rules); every threshold here is PRIOR and illustrative, not an agreed protocol.
 */
type Trigger = {
  id: string;
  name: string;
  rule: string;
  action: string;
  fired: boolean;
  detail: string;
  items: Array<[string, string]>;
};

const T_FACILITY = 0.3; // PRIOR
const T_DISTRICT_PEOPLE = 100_000; // PRIOR
const T_CROSSING_P = 0.3; // PRIOR
const T_CROSSING_PEOPLE = 10_000; // PRIOR
const STAND_DOWN = 0.15; // PRIOR

export function TriggerPanel({ scenario }: { scenario: DistrictScenario }) {
  const s = scenario;
  const ens = s.provenance.mode === "ensemble";
  const facs = s.facilities
    .filter((f) => f.type !== "shelter" && (f.p_isolated_by_landfall ?? 0) >= T_FACILITY)
    .sort((a, b) => (b.p_isolated_by_landfall ?? 0) - (a.p_isolated_by_landfall ?? 0));
  const pop = s.headline.pop_cut_hospital;
  const crossings = s.actions.filter(
    (a) => (a.p_event ?? 0) >= T_CROSSING_P && a.people_protected >= T_CROSSING_PEOPLE,
  );
  const shelters = s.facilities.filter((f) => f.type === "shelter");
  const shelterRisk = shelters.filter((f) => (f.p_isolated_by_landfall ?? 0) >= T_FACILITY);

  const triggers: Trigger[] = [
    {
      id: "health",
      name: "Health facility will lose referral access",
      rule: `Chance the facility is cut off from referral care by landfall ≥ ${pct(T_FACILITY)}`,
      action:
        "Pre-position 72 hours of medicines, oxygen and a relief doctor; move expected deliveries and dialysis patients to a referral hospital now; arrange boat or air evacuation standby.",
      fired: facs.length > 0,
      detail: facs.length ? `${facs.length} facilities` : "No facility above the threshold",
      items: facs
        .slice(0, 6)
        .map((f) => [
          cleanName(f.name),
          `${pct(f.p_isolated_by_landfall)} · from ${f.t10 ? ist(f.t10) : "–"}`,
        ]),
    },
    {
      id: "district",
      name: "Large population cut off",
      rule: `Median people cut off from every public hospital by landfall ≥ ${people(T_DISTRICT_PEOPLE)}`,
      action:
        "Activate the district emergency operations centre round the clock; request SDRF/NDRF pre-deployment to the affected blocks; open the relief supply chain before landfall.",
      fired: (pop.p50 ?? 0) >= T_DISTRICT_PEOPLE,
      detail: `Median ${people(pop.p50)} (likely range ${people(pop.p10)} to ${people(pop.p90)})`,
      items: [],
    },
    {
      id: "crossings",
      name: "Critical crossing will close",
      rule: `Chance the crossing closes ≥ ${pct(T_CROSSING_P)} and it carries ≥ ${people(T_CROSSING_PEOPLE)} people's access`,
      action:
        "Stage an earthmover and crew at the crossing before the deadline; pre-stock sandbags; brief the block office on the detour.",
      fired: crossings.length > 0,
      detail: crossings.length ? `${crossings.length} crossings` : "No crossing above the threshold",
      items: crossings.slice(0, 6).map((a) => [siteLabel(a.site), `by ${ist(a.deadline_utc)}`]),
    },
    {
      id: "shelters",
      name: "Cyclone shelter may be cut off",
      rule: `Chance a mapped shelter is cut off from hospitals by landfall ≥ ${pct(T_FACILITY)}`,
      action:
        "Stock first-aid and a trained volunteer at the shelter; plan medical transfer before the road closes.",
      fired: shelterRisk.length > 0,
      detail: shelters.length
        ? `${shelterRisk.length} of ${shelters.length} mapped shelters`
        : "No shelters mapped in OpenStreetMap for this district (a data gap, not an all-clear)",
      items: shelterRisk.slice(0, 6).map((f) => [cleanName(f.name), pct(f.p_isolated_by_landfall)]),
    },
  ];

  if (!ens)
    return (
      <p className="text-sm text-muted">
        Triggers need ensemble probabilities; this run is deterministic (IMD track only).
      </p>
    );

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-warning/40 bg-warning/10 p-3 text-xs text-warning">
        Indicative trigger design, not an agreed protocol. Thresholds are prior and illustrative; a real
        system is set with the SDMA before the season. Evaluated at IMD Bulletin No.{" "}
        {s.provenance.imd_bulletin_no}; stand down if a later bulletin drops the chance below{" "}
        {pct(STAND_DOWN)}.
      </div>
      {triggers.map((t) => (
        <details key={t.id} className="card group p-3" open={t.fired && t.id === "health"}>
          <summary className="flex cursor-pointer list-none items-start gap-3">
            <span
              className={`mt-0.5 rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                t.fired ? "bg-danger/20 text-danger" : "bg-surface-3 text-muted"
              }`}
            >
              {t.fired ? "FIRED" : "not fired"}
            </span>
            <span className="flex-1">
              <span className="block text-sm font-semibold">{t.name}</span>
              <span className="block text-xs text-muted">{t.detail}</span>
            </span>
            <span className="text-subtle transition-transform group-open:rotate-90" aria-hidden>
              ›
            </span>
          </summary>
          <div className="mt-3 space-y-2 border-t border-border pt-3 text-xs">
            <p>
              <span className="text-subtle">Rule:</span> {t.rule}
            </p>
            <p>
              <span className="text-subtle">Pre-agreed action:</span> {t.action}
            </p>
            {t.items.length > 0 && (
              <ul className="space-y-1">
                {t.items.map(([a, b]) => (
                  <li key={a} className="flex justify-between gap-3">
                    <span className="truncate">{a}</span>
                    <span className="shrink-0 text-muted tabular-nums">{b}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </details>
      ))}
    </div>
  );
}
