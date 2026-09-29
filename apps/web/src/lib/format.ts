// Display formatting shared by pages (mirrors the engine's facts formatting in aurora_agents/facts.py).

type Site =
  | {
      crossing_type: string | null;
      road_name: string | null;
      near_place: { name: string } | null;
    }
  | null
  | undefined;

const CROSSING: Record<string, string> = { bridge: "bridge", culvert: "culvert", ford: "causeway" };

export function cleanName(name: string): string {
  return name.replace(/^(U?PHC|CHC|SC)\s*,\s*/, "$1 ").replace(/,(?=\S)/g, ", ");
}

export function siteLabel(site: Site, fallback = "road"): string {
  if (!site) return fallback;
  let s = CROSSING[site.crossing_type ?? ""] ?? "road";
  if (site.near_place) s += ` near ${site.near_place.name}`;
  if (site.road_name) s += ` (${site.road_name})`;
  return s;
}

export function pct(p: number | null | undefined): string {
  if (p === null || p === undefined) return "–";
  if (p < 0.005) return "<1%";
  if (p > 0.995) return ">99%";
  return `${Math.round(p * 100)}%`;
}

export function people(n: number | null | undefined): string {
  if (n === null || n === undefined) return "–";
  if (n >= 100_000) return `${(n / 100_000).toFixed(1)} lakh`;
  if (n >= 1000) return (Math.round(n / 100) * 100).toLocaleString("en-IN");
  return String(Math.round(n / 10) * 10);
}

export function ist(iso: string, withYear = false): string {
  const parts = new Intl.DateTimeFormat("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "numeric",
    month: "short",
    year: withYear ? "numeric" : undefined,
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(new Date(iso));
  const get = (t: string) => parts.find((p) => p.type === t)?.value ?? "";
  return `${get("day")} ${get("month")}${withYear ? ` ${get("year")}` : ""}, ${get("hour")}:${get("minute")} IST`;
}
