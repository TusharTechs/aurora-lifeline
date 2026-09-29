/** Storms and runs published with the site (mirrors config/storms/*.yaml; SPEC §3, HANDOFF D18). */

export type RunInfo = { runId: string; bulletinNo: string; label: string };
export type StormInfo = {
  stormId: string;
  name: string;
  status: "replay" | "live";
  defaultRun: string;
  runs: RunInfo[];
  demoDistrict: string; // OSM relation id until LGD codes are loaded
  observedLandfall: { text: string; utc: string; lat: number; lon: number };
};

export const STORMS: StormInfo[] = [
  {
    stormId: "montha_2025",
    name: "Severe Cyclonic Storm Montha (Oct 2025)",
    status: "replay",
    defaultRun: "montha_2025_b21",
    runs: [
      {
        runId: "montha_2025_b21",
        bulletinNo: "21",
        label: "IMD National Bulletin 21 · 62 h before landfall · 1,063 futures",
      },
      {
        runId: "montha_2025_b19",
        bulletinNo: "19",
        label: "IMD National Bulletin 19 · 75 h before landfall · ECMWF only",
      },
    ],
    demoDistrict: "13999862",
    observedLandfall: {
      text: "Crossed the coast near Narsapur, 23:30 IST 28 Oct to 00:30 IST 29 Oct 2025 (IMD)",
      utc: "2025-10-28T18:30:00Z",
      lat: 16.35,
      lon: 81.7,
    },
  },
];

export function storm(stormId: string): StormInfo | undefined {
  return STORMS.find((s) => s.stormId === stormId);
}
