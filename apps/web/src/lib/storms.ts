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
  {
    stormId: "dana_2024",
    name: "Severe Cyclonic Storm Dana (Oct 2024)",
    status: "replay",
    defaultRun: "dana_2024_b01",
    runs: [
      {
        runId: "dana_2024_b01",
        bulletinNo: "1",
        label: "IMD National Bulletin 1 · 65 h before landfall · 97 futures",
      },
    ],
    demoDistrict: "9588868",
    observedLandfall: {
      text: "Crossed the north Odisha coast near Habalikhati (Bhitarkanika) and Dhamara, 01:30 to 03:30 IST 25 Oct 2024 (IMD)",
      utc: "2024-10-24T21:00:00Z",
      lat: 20.8,
      lon: 86.95,
    },
  },
];

export function storm(stormId: string): StormInfo | undefined {
  return STORMS.find((s) => s.stormId === stormId);
}
