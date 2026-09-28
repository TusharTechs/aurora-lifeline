/** Probability helpers for decile-encoded results (ARCHITECTURE §5, client rules). */

export type DecileProps = Partial<
  Record<"d1" | "d2" | "d3" | "d4" | "d5" | "d6" | "d7" | "d8" | "d9", number>
>;

const KEYS = ["d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9"] as const;

/**
 * P(event by hour t) from deciles d1..d9 (hours since "now"; missing = not reached in that share
 * of members). The weighted share reaches k/10 at dk, so P(t) is the largest k/10 with dk <= t.
 * Resolution is 10 percentage points, which is honest for what the deciles carry.
 */
export function probAt(props: DecileProps, t: number): number {
  let p = 0;
  KEYS.forEach((k, i) => {
    const v = props[k];
    if (v !== undefined && v !== null && v <= t) p = (i + 1) / 10;
  });
  return p;
}

/** Hours since `nowIso` for each ISO decile time (null stays null). */
export function isoDecilesToHours(
  nowIso: string,
  deciles: ReadonlyArray<string | null>,
): Array<number | null> {
  const now = Date.parse(nowIso);
  return deciles.map((d) => (d === null ? null : (Date.parse(d) - now) / 3_600_000));
}

/** P(event by t) from an array of decile hours (as produced by isoDecilesToHours). */
export function probAtHours(hours: ReadonlyArray<number | null>, t: number): number {
  let p = 0;
  hours.forEach((h, i) => {
    if (h !== null && h <= t) p = (i + 1) / 10;
  });
  return p;
}

/** A sequential colour ramp (pale amber -> deep red), colour-blind safe as a single hue family. */
export function rampRed(p: number, alpha = 230): [number, number, number, number] {
  if (p <= 0) return [0, 0, 0, 0]; // not at risk yet: leave the road to the basemap
  const stops: Array<[number, number, number]> = [
    [253, 224, 71],
    [249, 115, 22],
    [220, 38, 38],
    [127, 29, 29],
  ];
  const x = Math.min(Math.max(p, 0), 1) * (stops.length - 1);
  const i = Math.min(Math.floor(x), stops.length - 2);
  const f = x - i;
  const a = stops[i]!;
  const b = stops[i + 1]!;
  return [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f, alpha];
}

/** Purple ramp for settlements cut off (distinct from the road ramp). */
export function rampPurple(p: number): [number, number, number, number] {
  if (p <= 0) return [0, 0, 0, 0];
  return [124, 58, 237, Math.round(40 + p * 170)];
}
