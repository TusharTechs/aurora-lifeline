import type { Metadata } from "next";
import { Suspense } from "react";
import { BulletinReader } from "@/components/bulletin/BulletinReader";
import { Footer } from "@/components/site/Footer";
import { Nav } from "@/components/site/Nav";
import { STORMS } from "@/lib/storms";

export const metadata: Metadata = {
  title: "Bulletin reader",
  description: "Gemini reads an official IMD cyclone bulletin; code checks every value against the PDF.",
};

export default function BulletinPage() {
  const s = STORMS[0]!;
  const href = `/storm/${s.stormId}/district/${s.demoDistrict}/`;
  return (
    <>
      <Nav controlRoomHref={href} />
      <main id="main" className="atmosphere relative">
        <div className="mx-auto max-w-7xl px-4 pb-10 pt-14 sm:px-6">
          <p className="eyebrow">Bulletin reader · Gemini on Google Cloud</p>
          <h1 className="mt-3 max-w-4xl font-display text-4xl font-semibold leading-tight sm:text-6xl">
            Read an IMD cyclone bulletin. <span className="text-aurora">Trace every number to its line.</span>
          </h1>
          <p className="mt-5 max-w-2xl text-lg text-muted">
            Gemini reads the official PDF, text and tables alike, into a structured reading with a verbatim
            quote for every value. Code then checks it: positions, speeds, category, quotes and an independent
            table parser. An officer confirms before it drives a forecast.
          </p>
          <div className="mt-10">
            <Suspense>
              <BulletinReader
                stormId={s.stormId}
                known={s.runs.map((r) => ({
                  bulletinNo: r.bulletinNo,
                  label: `Montha · National Bulletin No. ${r.bulletinNo}`,
                  runHref: href,
                }))}
              />
            </Suspense>
          </div>
        </div>
      </main>
      <Footer controlRoomHref={href} />
    </>
  );
}
