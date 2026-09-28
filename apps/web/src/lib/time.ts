const IST = "Asia/Kolkata";

/** Formats a UTC ISO timestamp for display in IST, e.g. "28 Oct, 14:00 IST". */
export function formatIst(utcIso: string): string {
  const d = new Date(utcIso);
  if (Number.isNaN(d.getTime())) throw new Error(`Invalid timestamp: ${utcIso}`);
  const parts = new Intl.DateTimeFormat("en-IN", {
    timeZone: IST,
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(d);
  const get = (type: string) => parts.find((p) => p.type === type)?.value ?? "";
  return `${get("day")} ${get("month")}, ${get("hour")}:${get("minute")} IST`;
}

/** IST label for `h` hours after `nowIso`, e.g. "27 Oct, 20:30 IST". */
export function istAfter(nowIso: string, h: number): string {
  return formatIst(new Date(Date.parse(nowIso) + h * 3_600_000).toISOString());
}
