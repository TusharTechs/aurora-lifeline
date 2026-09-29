import Link from "next/link";
import { FourQuestions, type QA } from "@/components/landing/FourQuestions";
import { GoogleAI } from "@/components/landing/GoogleAI";
import { HeroAurora } from "@/components/landing/HeroAurora";
import { HowItWorks, type Step } from "@/components/landing/HowItWorks";
import { LiveDemo } from "@/components/landing/LiveDemo";
import { Personas, type Persona } from "@/components/landing/Personas";
import { Trust, type TrustExample } from "@/components/landing/Trust";
import { Footer } from "@/components/site/Footer";
import { Nav } from "@/components/site/Nav";
import { SeasonWatch } from "@/components/site/SeasonWatch";
import counts from "@/data/build_counts.json";
import { cleanName, ist, pct, people, siteLabel } from "@/lib/format";
import { landingData } from "@/lib/landingData";

const TYPE: Record<string, string> = {
  district_hospital: "District hospital",
  sdh_area_hospital: "Area hospital",
  chc: "CHC",
  phc: "PHC",
};

export default function Home() {
  const d = landingData();
  if (!d) return <main className="p-10">Run data not found.</main>;
  const { scenario: s, storm, members, leadH } = d;
  const href = `/storm/${storm.stormId}/district/${s.district_lgd}/`;
  const prov = s.provenance;
  const facs = s.facilities
    .filter((f) => f.type !== "shelter" && f.p_isolated_by_landfall !== null)
    .sort((a, b) => (b.p_isolated_by_landfall ?? 0) - (a.p_isolated_by_landfall ?? 0));
  const f1 = facs[0]!;
  const a1 = s.actions[0]!;
  const bulletin = `IMD National Bulletin No. ${prov.imd_bulletin_no} (${ist(prov.imd_issued_at_utc, true)})`;
  const wnx = (prov.members.WNX ?? 0) + (prov.members.WNX_LARGE ?? 0);
  const basis = (b: string) => b.replace(" - ", " − ");

  const questions: QA[] = [
    {
      q: "Which facility loses its road first?",
      a: cleanName(f1.name),
      how: `Ranked by the chance of losing road access to referral care before landfall, across ${members.toLocaleString("en-IN")} storm futures.`,
    },
    {
      q: "How likely is it?",
      a: `${pct(f1.p_isolated_by_landfall)} chance`,
      how: "The share of weighted storm futures in which every road from this PHC to a higher-level public hospital is cut by landfall.",
    },
    {
      q: "When?",
      a: f1.t10 && f1.t90 ? `${ist(f1.t10)} → ${ist(f1.t90)}` : "–",
      how: "If it is cut off, most likely in this window: the 10th to 90th percentile of when it happens, across the futures where it does. Never a single, falsely precise hour.",
    },
    {
      q: "What do we move, and by when?",
      a: `An earthmover to the ${siteLabel(a1.site)} by ${ist(a1.deadline_utc)}`,
      how: `Ranked by people protected times the chance the crossing closes (${pct(a1.p_event)}). Deadline basis: ${basis(a1.deadline_basis)}.`,
    },
  ];

  const steps: Step[] = [
    {
      title: "Read the official bulletin",
      body: `Gemini reads ${bulletin}: the track, winds, rain and surge warnings. Each value carries a verbatim quote and is checked in code against an independent parser. IMD remains the authority.`,
      stat: `Landfall expected “${prov.landfall_window_text}” (IMD)`,
    },
    {
      title: `Run ${members.toLocaleString("en-IN")} storm futures`,
      body: `Ensembles published by that hour, ${wnx.toLocaleString("en-IN")} from Google DeepMind WeatherNext and ${prov.members.ECMWF ?? 0} from ECMWF, are aligned to IMD's track. Each is a plausible version of the next three days.`,
      stat: `${leadH} hours before the storm crossed the coast`,
    },
    {
      title: "Put water on every road",
      body: "For every future, wind, rain flooding from IMD's rain warnings over a 90 m terrain model, and a storm-surge screen close road segments hour by hour, including every bridge, culvert and causeway.",
      stat: `${counts.road_segments.toLocaleString("en-IN")} road segments · ${counts.bridges.toLocaleString("en-IN")} bridges · ${counts.culverts.toLocaleString("en-IN")} culverts`,
    },
    {
      title: "Find who is cut off, and when",
      body: "A bottleneck search finds the hour each village and health facility loses its last road to a public hospital. Across the futures: a chance, and a P10–P90 window.",
      stat: `${people(s.headline.pop_cut_hospital.p50)} people in ${s.district_name} cut off by landfall (median; P10–P90 ${people(s.headline.pop_cut_hospital.p10)} to ${people(s.headline.pop_cut_hospital.p90)})`,
    },
    {
      title: "Decide what to move, by when",
      body: "Machinery goes where it protects the most people, six hours before the earliest likely closure. Gemini drafts the advisory in English, Telugu or Hindi; an officer approves; a CAP message goes to the SDMA's originator.",
      stat: `First action: the ${siteLabel(a1.site)}, by ${ist(a1.deadline_utc)}`,
    },
  ];

  const personas: Persona[] = [
    {
      role: "Collector · DDMA",
      who: "District Collector and the DDMA control room",
      asks: "Where do I stage machinery first, and by when?",
      gets: "A ranked list of crossings to pre-position earthmovers at, each with its deadline and basis, and an advisory ready to approve.",
      rows: s.actions
        .slice(0, 4)
        .map((a) => [`${a.rank}. ${siteLabel(a.site)}`, `by ${ist(a.deadline_utc)}`]),
    },
    {
      role: "Health · DM&HO",
      who: "District Medical and Health Officer, PHC medical officers",
      asks: "Which of my facilities lose access to referral care, and when?",
      gets: "Every PHC, CHC and hospital with its chance of being cut off and the likely window, so referrals and staff can move early.",
      rows: facs
        .slice(0, 4)
        .map((f) => [`${cleanName(f.name)} · ${TYPE[f.type] ?? f.type}`, pct(f.p_isolated_by_landfall)]),
    },
    {
      role: "Roads · R&B, PR",
      who: "Roads and Buildings and Panchayat Raj engineers",
      asks: "Which crossings close, how likely, and how many people depend on them?",
      gets: "Bridges, culverts and causeways ranked by the people whose access they carry, with each closure probability.",
      rows: s.actions
        .slice(0, 4)
        .map((a) => [siteLabel(a.site), `${pct(a.p_event)} · ${people(a.people_protected)} people`]),
    },
    {
      role: "SDMA · CAP originator",
      who: "State Disaster Management Authority",
      asks: "What exactly would we send, and who approved it?",
      gets: "A CAP 1.2 message validated against the official schema, marked Exercise and Restricted, carrying the IMD bulletin it came from.",
      rows: [
        ["Status and scope", "Exercise · Restricted"],
        ["Source", `IMD Bulletin No. ${prov.imd_bulletin_no}`],
        ["Area", `${s.district_name} district polygon`],
        ["Approval", "Officer, before any dispatch"],
      ],
    },
  ];

  const trust: TrustExample = {
    template:
      "Derived from {{provenance}}: {{fac1_name}} may lose road access to referral care ({{fac1_p}} chance, {{fac1_window}}). Pre-position an earthmover at the {{act1_site}} by {{act1_deadline}}.",
    rendered: "",
    facts: [
      ["provenance", `IMD National Bulletin No. ${prov.imd_bulletin_no}`, "district_scenario.provenance"],
      ["fac1_name", cleanName(f1.name), `facilities · ${f1.facility_id}`],
      ["fac1_p", pct(f1.p_isolated_by_landfall), `facilities · ${f1.facility_id}`],
      [
        "fac1_window",
        f1.t10 && f1.t90 ? `${ist(f1.t10)} to ${ist(f1.t90)}` : "–",
        `facilities · ${f1.facility_id}`,
      ],
      ["act1_site", siteLabel(a1.site), `actions · ${a1.action_id}`],
      ["act1_deadline", `${ist(a1.deadline_utc)} (${basis(a1.deadline_basis)})`, `actions · ${a1.action_id}`],
    ],
  };

  return (
    <>
      <Nav controlRoomHref={href} />
      <main id="main">
        <section
          aria-labelledby="hero-title"
          className="atmosphere grain relative -mt-16 flex min-h-[100svh] items-center overflow-hidden pt-16 max-lg:flex-col max-lg:items-stretch"
        >
          <div className="relative z-10 mx-auto w-full max-w-7xl px-4 py-16 sm:px-6 lg:py-24">
            <div className="max-w-2xl">
              <div className="mb-6">
                <SeasonWatch />
              </div>
              <p className="eyebrow">Cyclone decision support for district control rooms</p>
              <h1
                id="hero-title"
                className="mt-5 font-display text-5xl font-semibold leading-[1.02] tracking-tight sm:text-6xl lg:text-7xl"
              >
                Know who the cyclone will cut off.{" "}
                <span className="text-aurora">Before the roads close.</span>
              </h1>
              <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted sm:text-xl">
                AURORA Lifeline turns the official IMD bulletin into a district plan: which PHCs, hospitals,
                shelters and villages lose road access, how likely, when, and where to stage machinery first.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link href={href} className="btn btn-primary text-base">
                  Open the {s.district_name} control room
                </Link>
                <Link href="/bulletin/" className="btn btn-ghost text-base">
                  Read an IMD bulletin with Gemini
                </Link>
              </div>
              <p className="mt-8 max-w-xl text-sm text-subtle">
                Below: Cyclone Montha, a past storm, as AURORA would have seen it {leadH} hours before
                landfall, from {bulletin}, using only forecasts published by then.{" "}
                {storm.observedLandfall.text}.
              </p>
            </div>
          </div>
          <div className="relative h-[70svh] w-full lg:absolute lg:inset-0 lg:h-auto">
            <HeroAurora data={d.hero} />
          </div>
        </section>

        <FourQuestions
          items={questions}
          provenance={`Kakinada · ${bulletin} · ${members.toLocaleString("en-IN")} storm futures aligned to the IMD track`}
        />
        <HowItWorks steps={steps} />
        <LiveDemo
          runId={storm.defaultRun}
          lgd={s.district_lgd}
          controlRoomHref={href}
          facilities={facs.slice(0, 6).map((f) => ({
            name: cleanName(f.name),
            type: TYPE[f.type] ?? f.type,
            p: f.p_isolated_by_landfall ?? 0,
            hours: f.iso_deciles.map((x) =>
              x === null ? null : (Date.parse(x) - Date.parse(s.time_axis.now_utc)) / 3_600_000,
            ),
          }))}
          hourly={d.hero.hourly}
          nowUtc={s.time_axis.now_utc}
          landfallH={d.hero.landfallH}
        />
        <Personas personas={personas} />
        <Trust example={trust} />
        <GoogleAI />

        <section aria-labelledby="districts-title" className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
          <h2 id="districts-title" className="font-display text-2xl font-semibold">
            Every district in the Montha replay
          </h2>
          <ul className="mt-6 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {d.districts.map((x) => (
              <li key={x.lgd}>
                <Link
                  href={`/storm/${storm.stormId}/district/${x.lgd}/`}
                  className="card card-hover flex items-baseline justify-between gap-3 px-5 py-4"
                >
                  <span className="font-medium">{x.name}</span>
                  <span className="text-sm text-muted">{people(x.p50)} cut off at landfall</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      </main>
      <Footer controlRoomHref={href} />
    </>
  );
}
