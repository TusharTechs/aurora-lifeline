import type { Metadata } from "next";
import { Footer } from "@/components/site/Footer";
import { Nav } from "@/components/site/Nav";
import { PromptCards } from "@/components/PromptCards";
import counts from "@/data/build_counts.json";
import { STORMS } from "@/lib/storms";

export const metadata: Metadata = {
  title: "About, data and credits",
  description: "What AURORA Lifeline does, the data it stands on, its limits, accessibility and privacy.",
};

const DATA: Array<[string, string, string]> = [
  [
    "IMD / RSMC New Delhi bulletins",
    "India Meteorological Department",
    "The authority for cyclone forecasts in India; read from IMD's archive, never re-hosted",
  ],
  ["WeatherNext ensembles (Weather Lab)", "Google DeepMind", "CC BY 4.0 (data older than 48 hours)"],
  ["IFS ensemble tropical-cyclone tracks", "ECMWF open data", "CC BY 4.0"],
  [
    "Roads, bridges, facilities, places, coastline",
    "© OpenStreetMap contributors (Geofabrik extract)",
    "ODbL 1.0",
  ],
  [
    "Elevation (Copernicus DEM GLO-30)",
    "Produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved",
    "Free licence; AURORA's own 90 m height-above-drainage model is derived from it",
  ],
  ["Surface water occurrence", "Source: EC JRC/Google (Global Surface Water)", "Free, with credit"],
  ["Population 2020 (constrained)", "WorldPop, University of Southampton", "CC BY 4.0"],
  ["Basemap", "Google Maps Platform", "Map data © Google"],
  [
    "Demo field photo (Field tab)",
    "“Kerala Flood 9-8-2019 at Kidangoor–Mookkannoor road near Angamaly” by Navaneeth Krishnan S, via Wikimedia Commons; resized, metadata removed. Not from Cyclone Montha",
    "CC BY-SA 3.0",
  ],
  ["CAP 1.2 schema", "OASIS", "OASIS IPR policy"],
];

export default function About() {
  const s = STORMS[0]!;
  const href = `/storm/${s.stormId}/district/${s.demoDistrict}/`;
  return (
    <>
      <Nav controlRoomHref={href} />
      <main id="main" className="mx-auto max-w-4xl px-4 pb-10 pt-14 sm:px-6">
        <p className="eyebrow">About</p>
        <h1 className="mt-3 font-display text-4xl font-semibold leading-tight sm:text-5xl">
          What AURORA Lifeline is, and what it is not.
        </h1>
        <div className="mt-8 space-y-5 text-lg leading-relaxed text-muted">
          <p>
            AURORA Lifeline is decision support for State and District Disaster Management Authorities. From
            the official IMD cyclone bulletin it estimates which health facilities, shelters and villages lose
            road access to public hospitals, how likely that is, in what time window, and where to stage
            machinery before the roads close.
          </p>
          <p>
            It is not a warning service. IMD is the authority for cyclone warnings in India. AURORA never
            issues public alerts: advisories are drafts until an officer approves them, and CAP messages are
            marked Exercise and Restricted for the SDMA&apos;s authorised originator. Asset-level results are
            public only for past storms.
          </p>
        </div>

        <h2 className="mt-14 font-display text-2xl font-semibold">How the numbers are made</h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-muted">
          <li>
            Storm futures: every ECMWF and WeatherNext member published by the bulletin&apos;s issue time,
            matched and aligned to the IMD track, weighted equally per source. Replays never use hindsight
            data.
          </li>
          <li>
            Hazards: Holland (1980) winds; rain flooding from IMD&apos;s rainfall categories and coverage over
            AURORA&apos;s 90 m height-above-drainage model; a storm-surge screening upper bound (IMD surge
            guidance takes precedence).
          </li>
          <li>
            Network: {counts.road_segments.toLocaleString("en-IN")} road segments,{" "}
            {counts.bridges.toLocaleString("en-IN")} bridges, {counts.culverts.toLocaleString("en-IN")}{" "}
            culverts and {counts.fords} causeways from OpenStreetMap for the six Godavari–Krishna delta
            districts; a bottleneck reachability search finds when each place loses its last road.
          </li>
          <li>
            Parameters not yet calibrated are labelled <em>prior</em> in every run manifest. Chances are shown
            with a P10–P90 window, never as a single hour.
          </li>
          <li>
            Gemini never produces an AURORA number: it writes placeholders, and code inserts and checks every
            figure.
          </li>
        </ul>

        <h2 className="mt-14 font-display text-2xl font-semibold">Data and credits</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="text-xs text-subtle">
              <tr>
                <th className="py-2 pr-4 font-normal">Data</th>
                <th className="py-2 pr-4 font-normal">Source</th>
                <th className="py-2 font-normal">Licence and use</th>
              </tr>
            </thead>
            <tbody>
              {DATA.map(([d, src, lic]) => (
                <tr key={d} className="border-t border-border align-top">
                  <td className="py-2.5 pr-4">{d}</td>
                  <td className="py-2.5 pr-4 text-muted">{src}</td>
                  <td className="py-2.5 text-muted">{lic}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-4 text-sm text-subtle">
          Weather Lab / WeatherNext outputs are experimental, are not produced with or endorsed by any
          government meteorological agency, and are shown only as a non-official uncertainty envelope.
        </p>
        <p className="mt-2 text-sm text-subtle">
          National and international boundaries from OpenStreetMap are never rendered; district outlines are
          used only for aggregation and CAP areas.
        </p>

        <h2 id="prompts" className="mt-14 scroll-mt-20 font-display text-2xl font-semibold">
          Try the prompts in Google AI Studio
        </h2>
        <p className="mt-4 text-muted">
          These are the agents&apos; real system instructions. Copy one into AI Studio&apos;s system
          instructions and try it on public data, such as any IMD bulletin. The product itself calls Gemini on
          Agent Platform, with the checks described above.
        </p>
        <PromptCards />

        <h2 className="mt-14 font-display text-2xl font-semibold">Google AI and tools used to build it</h2>
        <p className="mt-4 text-muted">
          In the product: Gemini 3.7 Flash and 3.5 Flash-Lite on Agent Platform, gemini-embedding-2, the Agent
          Development Kit, WeatherNext data, Google Maps Platform, Cloud Run, Firebase Hosting and Secret
          Manager. The code was written with the help of AI coding assistants, as declared in the hackathon
          submission.
        </p>

        <h2 id="accessibility" className="mt-14 scroll-mt-20 font-display text-2xl font-semibold">
          Accessibility
        </h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-muted">
          <li>Keyboard access throughout, a skip link and a visible focus ring.</li>
          <li>
            The accessibility menu (top right) reduces motion, raises contrast and enlarges text; the site
            also follows your device&apos;s reduced-motion setting.
          </li>
          <li>Risk is never shown by colour alone: every chance is also written as a number or a label.</li>
          <li>Telugu and Hindi text use Noto fonts so advisories render correctly on any device.</li>
        </ul>

        <h2 id="privacy" className="mt-14 scroll-mt-20 font-display text-2xl font-semibold">
          Privacy
        </h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-muted">
          <li>No accounts, analytics or advertising trackers on the public site.</li>
          <li>
            A bulletin you upload is read and discarded; only the structured reading is cached, keyed by the
            file&apos;s checksum. Questions to Ask AURORA are cached with their answers so the replay stays
            identical for every visitor; do not type personal information into them.
          </li>
          <li>Your accessibility choices are stored only in this browser.</li>
        </ul>

        <h2 className="mt-14 font-display text-2xl font-semibold">Source and contact</h2>
        <p className="mt-4 text-muted">
          The code is open source under Apache-2.0 at{" "}
          <a className="text-cyan underline" href="https://github.com/TusharTechs/aurora-lifeline">
            github.com/TusharTechs/aurora-lifeline
          </a>
          . Questions and corrections are welcome as GitHub issues.
        </p>
      </main>
      <Footer controlRoomHref={href} />
    </>
  );
}
