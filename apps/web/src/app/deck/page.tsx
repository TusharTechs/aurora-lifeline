import fs from "node:fs";
import path from "node:path";
import type { Metadata } from "next";
import { AuroraMark } from "@/components/brand/Logo";
import counts from "@/data/build_counts.json";
import evalData from "@/data/eval_bulletins.json";
import { cleanName, ist, pct, people, siteLabel } from "@/lib/format";
import { landingData, stormSummaries } from "@/lib/landingData";

export const metadata: Metadata = {
  title: "Deck",
  description: "AURORA Lifeline: the submission deck (print to PDF, landscape).",
};

type Scores = { hits: number; flagged: number; pod: number | null; far: number | null; csi: number | null };

function validation(runId: string) {
  const f = path.join(process.cwd(), "public", "runs", runId, "validation.json");
  if (!fs.existsSync(f)) return null;
  return JSON.parse(fs.readFileSync(f, "utf8")) as {
    total: { edges_observed: number; edges_observed_flooded: number } & Record<string, Scores | number>;
    sentinel1: { orbits?: Array<{ hours_after_t: number }> };
    districts: Array<{ district_name: string; edges_observed_flooded: number; aurora: Scores }>;
  };
}

function Slide({
  n,
  eyebrow,
  title,
  children,
}: {
  n: number;
  eyebrow: string;
  title: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="deck-slide atmosphere relative mx-auto flex aspect-video w-full max-w-[1280px] flex-col overflow-hidden rounded-3xl border border-border bg-bg p-14">
      <div className="flex items-center justify-between text-sm text-subtle">
        <span className="eyebrow">{eyebrow}</span>
        <span className="flex items-center gap-2">
          <AuroraMark size={22} /> AURORA Lifeline · {n}/11
        </span>
      </div>
      <h2 className="mt-5 max-w-5xl font-display text-[2.6rem] font-semibold leading-[1.1]">{title}</h2>
      <div className="mt-8 flex-1">{children}</div>
    </section>
  );
}

export default function Deck() {
  const d = landingData();
  if (!d) return null;
  const s = d.scenario;
  const facs = s.facilities
    .filter((f) => f.type !== "shelter" && f.p_isolated_by_landfall !== null)
    .sort((a, b) => (b.p_isolated_by_landfall ?? 0) - (a.p_isolated_by_landfall ?? 0));
  const acts = s.actions.slice(0, 3);
  const v = validation(d.storm.defaultRun);
  const tot = v?.total as unknown as Record<string, Scores> | undefined;
  const storms = stormSummaries();
  const labelled = evalData.bulletins.filter((b) => b.labels);
  return (
    <main id="main" className="deck space-y-10 bg-bg px-4 py-10">
      <p className="deck-hint mx-auto max-w-[1280px] text-sm text-muted">
        Print to PDF (landscape, no margins, background graphics on) for the submission deck. Every number is
        read from the published runs.
      </p>

      <section className="deck-slide atmosphere grain relative mx-auto flex aspect-video w-full max-w-[1280px] flex-col justify-between overflow-hidden rounded-3xl border border-border bg-bg p-16">
        <div className="flex items-center gap-4">
          <AuroraMark size={72} />
          <span className="font-display text-3xl">
            <span className="font-semibold tracking-[0.14em]">AURORA</span>{" "}
            <span className="font-light text-muted">Lifeline</span>
          </span>
        </div>
        <div>
          <h1 className="max-w-5xl font-display text-6xl font-semibold leading-[1.05]">
            IMD tells you the storm.{" "}
            <span className="text-aurora">AURORA tells you which PHC is cut off,</span> how likely, when, and
            what to move there now.
          </h1>
          <p className="mt-6 text-xl text-muted">Cyclone decision support for district control rooms</p>
        </div>
        <p className="text-sm text-subtle">
          Track 05 · Build with AI: Code for Communities, Second Edition · aurora-lifeline.web.app
        </p>
      </section>

      <Slide
        n={2}
        eyebrow="The problem"
        title="Seventy-two hours out, a control room knows the storm, not which PHC will be cut off."
      >
        <div className="grid grid-cols-3 gap-6">
          {[
            [
              people(s.headline.pop_cut_hospital.p50),
              `people in ${s.district_name} cut off from every public hospital by landfall (median; P10–P90 ${people(s.headline.pop_cut_hospital.p10)}–${people(s.headline.pop_cut_hospital.p90)})`,
            ],
            [
              String(s.headline.facilities_at_risk.p50 ?? "–"),
              "health facilities cut off from referral care by landfall (median)",
            ],
            [
              ist(acts[0]!.deadline_utc),
              `first action deadline, ${Math.round((Date.parse(d.storm.observedLandfall.utc) - Date.parse(acts[0]!.deadline_utc)) / 3_600_000)} h before landfall: machinery to the ${siteLabel(acts[0]!.site)}`,
            ],
          ].map(([big, small]) => (
            <div key={small} className="card p-6">
              <p className="font-display text-4xl font-semibold text-aurora">{big}</p>
              <p className="mt-3 text-muted">{small}</p>
            </div>
          ))}
        </div>
        <p className="mt-8 max-w-4xl text-lg text-muted">
          Cyclone Montha, as AURORA would have seen it {d.leadH} hours before landfall from IMD National
          Bulletin No. {s.provenance.imd_bulletin_no}. Roads flood, bridges and culverts close, and villages
          lose their last road to care. Deciding what to move, and where, is still done by phone and
          experience.
        </p>
      </Slide>

      <Slide
        n={3}
        eyebrow="What exists, and the gap"
        title="Good forecasts and alert channels exist. The asset-level, time-windowed translation does not."
      >
        <div className="grid grid-cols-2 gap-5 text-lg">
          {[
            [
              "IMD bulletins",
              "Track, intensity, rain by district, surge by coast. The authority, and AURORA's input.",
            ],
            ["Web-DCRA", "District-level composite risk, as documented up to 2023."],
            ["INCOIS", "Storm-surge and inundation guidance (linked, not ingested)."],
            ["Sachet (CAP)", "The national alert channel. AURORA drafts CAP for the SDMA's originator."],
          ].map(([a, b]) => (
            <div key={a} className="card p-5">
              <p className="font-display text-xl font-semibold">{a}</p>
              <p className="mt-1 text-muted">{b}</p>
            </div>
          ))}
        </div>
        <p className="mt-6 text-xl">
          Missing:{" "}
          <span className="text-teal">
            which facility, which crossing, how likely, in what window, and what to do first.
          </span>
        </p>
      </Slide>

      <Slide
        n={4}
        eyebrow="The solution"
        title="From one official bulletin to the few decisions that matter."
      >
        <ol className="grid grid-cols-5 gap-4">
          {[
            ["Read", "Gemini reads the IMD PDF; every value quoted and checked in code"],
            [
              "Futures",
              `${d.members.toLocaleString("en-IN")} WeatherNext and ECMWF storm futures aligned to IMD's track`,
            ],
            [
              "Water",
              `Rain, surge and wind on ${counts.road_segments.toLocaleString("en-IN")} road segments, ${counts.bridges.toLocaleString("en-IN")} bridges`,
            ],
            ["Cut off", "Chance and P10–P90 window for every PHC, hospital, shelter, village"],
            ["Decide", "Machinery by deadline, triggers, advisories in 3 languages, CAP 1.2"],
          ].map(([a, b], i) => (
            <li key={a} className="card p-5">
              <p className="font-display text-sm text-teal">Step {i + 1}</p>
              <p className="mt-1 font-display text-2xl font-semibold">{a}</p>
              <p className="mt-2 text-muted">{b}</p>
            </li>
          ))}
        </ol>
        <p className="mt-6 text-lg text-muted">
          After landfall, field photos are checked by Gemini and routed by fixed rules to the map or an
          officer. Replays of Montha (Andhra Pradesh) and Dana (Odisha) use only forecasts published before
          landfall; a season watch reads IMD&apos;s archive to show whether IMD is tracking a system today.
        </p>
      </Slide>

      <Slide
        n={5}
        eyebrow="In the control room"
        title={`${s.district_name}: the facilities most at risk, and what to move first`}
      >
        <div className="grid grid-cols-2 gap-6">
          <div className="card p-5">
            <p className="text-sm text-subtle">
              Chance of losing referral access by landfall · likely window if it does
            </p>
            <ul className="mt-3 space-y-2">
              {facs.slice(0, 5).map((f) => (
                <li key={f.facility_id} className="flex justify-between gap-4">
                  <span>{cleanName(f.name)}</span>
                  <span className="text-muted tabular-nums">
                    {pct(f.p_isolated_by_landfall)} · {f.t10 ? ist(f.t10) : "–"}
                  </span>
                </li>
              ))}
            </ul>
          </div>
          <div className="card p-5">
            <p className="text-sm text-subtle">Stage an earthmover · deadline (basis: P10 closure − 6 h)</p>
            <ul className="mt-3 space-y-2">
              {acts.map((a) => (
                <li key={a.action_id} className="flex justify-between gap-4">
                  <span>{siteLabel(a.site)}</span>
                  <span className="text-muted tabular-nums">{ist(a.deadline_utc)}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <p className="mt-6 text-lg text-muted">
          Plus: a map that plays the storm forward, a Bulletin 19 / 21 switch, indicative anticipatory-action
          triggers, a Telugu advisory read aloud, Ask AURORA, and a field-photo check after landfall.
        </p>
      </Slide>

      <Slide
        n={6}
        eyebrow="AI approach"
        title="Gemini reads, writes and answers. The engine counts. An officer approves."
      >
        <div className="grid grid-cols-2 gap-4">
          {[
            [
              "Reads",
              "Bulletin Reader: the PDF goes to Gemini; code checks basin, speed, category, verbatim quotes and an independent table parser.",
            ],
            [
              "Writes",
              "Advisory Writer: placeholders only; code inserts every number and rejects any digit it did not supply, in any script; Telugu and Hindi back-translated and scored.",
            ],
            [
              "Answers",
              "Ask AURORA on ADK: five read-only tools; an after-model callback blocks any figure a tool did not return; the facts table if it fails.",
            ],
            [
              "Checks",
              "Field Verifier: metadata stripped, Gemini assesses the photo, fixed rules route it; bridge reopenings always go to an officer.",
            ],
          ].map(([a, b]) => (
            <div key={a} className="card p-4">
              <p className="font-display text-xl font-semibold text-teal">{a}</p>
              <p className="mt-1 text-muted">{b}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 rounded-2xl border border-border bg-surface-2 p-3 font-mono text-sm text-violet">
          {
            "{{fac1_name}} has a {{fac1_p}} chance of losing road access to referral care; stage an earthmover at the {{act1_site}} by {{act1_deadline}}."
          }
        </p>
      </Slide>

      <Slide n={7} eyebrow="Google stack" title="Every Google model here has a job.">
        <div className="grid grid-cols-3 gap-4">
          {[
            ["Gemini 3.7 Flash", "Reads bulletins; drafts advisories; checks field photos"],
            ["Agent Development Kit", "Ask AURORA agent with a number guard"],
            ["Gemini 3.5 Flash-Lite · embedding-2", "Back-translation and similarity checks"],
            ["Cloud TTS Gemini-TTS", "Advisories read aloud in Telugu, Hindi and English"],
            [
              "Google DeepMind WeatherNext",
              `${((s.provenance.members.WNX ?? 0) + (s.provenance.members.WNX_LARGE ?? 0)).toLocaleString("en-IN")} of Montha's storm futures`,
            ],
            ["Earth Engine", "Sentinel-1 flood mapping for validation"],
            ["Maps Platform", "Vector basemap under deck.gl"],
            ["Cloud Run · Firebase Hosting", "API; static site and tiles on the CDN"],
            ["Cloud Storage · Firestore · WIF", "Gemini cache, daily cap, keyless deploys"],
          ].map(([a, b]) => (
            <div key={a} className="card p-4">
              <p className="font-display text-lg font-semibold">{a}</p>
              <p className="text-sm text-muted">{b}</p>
            </div>
          ))}
        </div>
      </Slide>

      <Slide n={8} eyebrow="Proof, misses included" title="Scored against what actually happened.">
        <div className="grid grid-cols-2 gap-6">
          <div className="card p-5">
            <p className="font-display text-xl font-semibold">Sentinel-1 radar vs forecast road closures</p>
            {v && tot ? (
              <>
                <p className="mt-2 text-muted">
                  Passes {(v.sentinel1.orbits ?? []).map((o) => `${o.hours_after_t} h`).join(" and ")} after
                  landfall; {v.total.edges_observed.toLocaleString("en-IN")} segments observed,{" "}
                  {v.total.edges_observed_flooded.toLocaleString("en-IN")} with water.
                </p>
                <ul className="mt-3 space-y-1">
                  {[
                    ["AURORA", tot.aurora],
                    ["Baseline: lowest ground", tot.baseline_low_hand],
                    ["Baseline: nearest the track", tot.baseline_distance_to_track],
                  ].map(([k, sc]) => (
                    <li key={k as string} className="flex justify-between">
                      <span>{k as string}</span>
                      <span className="tabular-nums text-muted">
                        {(sc as Scores).hits} hits · FAR {(sc as Scores).far?.toFixed(3)}
                      </span>
                    </li>
                  ))}
                </ul>
                <p className="mt-3 text-sm text-muted">
                  By district:{" "}
                  {v.districts
                    .filter((x) => x.edges_observed_flooded > 0)
                    .map((x) => `${x.district_name} ${x.aurora.hits} of ${x.edges_observed_flooded}`)
                    .join(" · ")}
                </p>
                <p className="mt-2 text-sm text-warning">
                  A weak test: water had largely drained; the false-alarm rate is high.
                </p>
              </>
            ) : (
              <p className="mt-2 text-muted">Sentinel-1 scoring pending.</p>
            )}
          </div>
          <div className="card p-5">
            <p className="font-display text-xl font-semibold">Bulletin Reader vs hand-checked labels</p>
            <ul className="mt-3 space-y-2">
              {labelled.map((b) => (
                <li key={b.label} className="flex justify-between">
                  <span>{b.label}</span>
                  <span className="tabular-nums text-teal">
                    {b.labels!.agree}/{b.labels!.total} fields
                  </span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-sm text-muted">
              IMD&apos;s live 2026 bulletin: all applicable checks pass.
            </p>
          </div>
        </div>
      </Slide>

      <Slide
        n={9}
        eyebrow="Who it serves, and the pilot"
        title="Built for the people who decide in the 72 hours before landfall."
      >
        <div className="grid grid-cols-4 gap-4">
          {[
            ["Collector · DDMA", "Where to stage machinery, by when"],
            ["DM&HO · PHC doctors", "Which facilities lose referral access, when"],
            ["R&B · PR engineers", "Which crossings close, for how many people"],
            ["SDMA originator", "A validated CAP 1.2 draft, officer-approved"],
          ].map(([a, b]) => (
            <div key={a} className="card p-5">
              <p className="font-display text-lg font-semibold">{a}</p>
              <p className="mt-1 text-muted">{b}</p>
            </div>
          ))}
        </div>
        <p className="mt-6 text-lg text-muted">
          Pilot: shadow mode with one SDMA and two coastal districts through the October–December season;
          AURORA runs on each IMD bulletin, officers compare with their own plans, results are scored after
          each storm. No public alerts; CAP drafts go to the authorised originator for Sachet.
        </p>
      </Slide>

      <Slide n={10} eyebrow="Scale" title="Geography is configuration.">
        <div className="grid grid-cols-2 gap-6">
          {storms.map((ss) => (
            <div key={ss.storm.stormId} className="card p-5">
              <p className="font-display text-xl font-semibold">{ss.storm.name}</p>
              <p className="mt-1 text-muted">
                IMD Bulletin No. {ss.bulletinNo} · {ss.members.toLocaleString("en-IN")} futures ·{" "}
                {ss.districts.length} districts
              </p>
              <p className="mt-3 text-muted">
                {ss.demo?.name}: {people(ss.demo?.p50 ?? null)} people cut off by landfall (median)
              </p>
            </div>
          ))}
        </div>
        <ul className="mt-6 space-y-2 text-lg text-muted">
          <li>
            A new state is a config file and a district list: Odisha&apos;s graph, terrain model and storm run
            took under two minutes of compute.
          </li>
          <li>
            Montha&apos;s 1,063 futures ran through 5.4 lakh road segments in 83 seconds on one 7-core
            machine; the site is static and cached.
          </li>
          <li>
            Static tiles on a CDN; the API on Cloud Run scales to zero, with per-IP limits, a daily model-call
            cap and cached Gemini outputs, within a US$150 budget. Keyless CI/CD; 115 Python and 7 web tests.
          </li>
          <li>
            Every input except the IMD bulletin is global open data; CAP 1.2 is an international standard.
          </li>
        </ul>
      </Slide>

      <Slide n={11} eyebrow="Roadmap and ask" title="Next: a pilot district, then every cyclone-prone coast.">
        <div className="grid grid-cols-2 gap-6 text-lg">
          <div className="card p-5">
            <p className="font-display text-xl font-semibold">Roadmap</p>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-muted">
              <li>Power-grid exposure and VIIRS outage validation</li>
              <li>Field reports by WhatsApp and voice note, into the same checks</li>
              <li>SMS and IVR through Sachet partners</li>
              <li>Automatic runs on every IMD bulletin in season</li>
              <li>More states: Tamil Nadu, West Bengal, Gujarat</li>
            </ul>
          </div>
          <div className="card p-5">
            <p className="font-display text-xl font-semibold">Ask</p>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-muted">
              <li>An SDMA partner for a shadow-mode pilot this season</li>
              <li>Access to official facility and road registries</li>
              <li>IMD API access for bulletins as they are issued</li>
            </ul>
          </div>
        </div>
        <p className="mt-8 text-sm text-subtle">
          Not an official warning service; IMD is the authority for cyclone warnings in India. Open source
          (Apache-2.0): github.com/TusharTechs/aurora-lifeline
        </p>
      </Slide>
    </main>
  );
}
