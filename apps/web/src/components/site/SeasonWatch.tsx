"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getSeason, type Season } from "@/lib/api";

/**
 * Season watch: is IMD issuing national cyclone bulletins right now? Read from IMD's own archive
 * by the API (checked at most every 30 minutes). AURORA never publishes asset-level results for a
 * live storm; it points to IMD and offers to read IMD's latest bulletin.
 */
export function SeasonWatch() {
  const [s, setS] = useState<Season | null>(null);
  useEffect(() => {
    let alive = true;
    void getSeason().then((v) => alive && setS(v));
    return () => {
      alive = false;
    };
  }, []);
  if (!s || s.status !== "ok") return null;
  const l = s.latest;
  return (
    <div
      role="status"
      className={`card inline-flex max-w-full flex-wrap items-center gap-x-3 gap-y-1 !rounded-full px-4 py-2 text-sm ${
        s.active ? "border-warning/50" : ""
      }`}
    >
      <span className={`pulse-dot ${s.active ? "text-warning" : "text-safe"}`} aria-hidden />
      {s.active && l ? (
        <>
          <span>
            <strong className="font-semibold">IMD is tracking a system now.</strong>{" "}
            <span className="text-muted">
              National Bulletin No. {l.bulletin_no ?? "?"}, based on {l.based_on_ist}.
            </span>
          </span>
          <Link
            href="/bulletin/?latest=1"
            className="font-semibold text-cyan underline-offset-4 hover:underline"
          >
            Read it with Gemini →
          </Link>
        </>
      ) : (
        <span className="text-muted">
          No IMD national cyclone bulletin in the last 36 hours · checked {s.checked_at_ist}
        </span>
      )}
    </div>
  );
}
