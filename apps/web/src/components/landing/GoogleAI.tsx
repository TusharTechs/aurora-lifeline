const ITEMS: Array<[string, string, string]> = [
  [
    "Gemini 3.7 Flash",
    "Reads the IMD bulletin",
    "The PDF itself goes to Gemini on Agent Platform; every extracted value comes back with a verbatim quote and is checked in code.",
  ],
  [
    "Gemini 3.7 Flash",
    "Drafts the advisory",
    "Plain-language advisories in English, Telugu and Hindi for the Collector, health and road teams, with placeholders instead of numbers.",
  ],
  [
    "Agent Development Kit",
    "Ask AURORA",
    "An agent over five read-only tools. An after-model callback blocks any figure the tools did not return.",
  ],
  [
    "gemini-embedding-2",
    "Checks translations",
    "Telugu and Hindi drafts are translated back and compared with the English draft; low similarity is flagged.",
  ],
  [
    "Google DeepMind WeatherNext",
    "Most of the storm futures",
    "Weather Lab's ensembles supply 1,011 of the 1,062 tracks, alongside 51 from ECMWF.",
  ],
  [
    "Google Maps Platform · Cloud",
    "Where it runs",
    "A vector basemap under deck.gl; the API on Cloud Run behind Firebase Hosting; keyless deploys with Workload Identity Federation.",
  ],
];

export function GoogleAI() {
  return (
    <section aria-labelledby="google-title" className="mx-auto max-w-7xl px-4 py-24 sm:px-6">
      <p className="eyebrow">Built with Google AI</p>
      <h2
        id="google-title"
        className="mt-3 max-w-3xl font-display text-3xl font-semibold leading-tight sm:text-5xl"
      >
        Every Google model here has a job.
      </h2>
      <ul className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ITEMS.map(([tech, job, body]) => (
          <li key={job} className="card card-hover p-6">
            <p className="text-xs font-semibold uppercase tracking-wider text-violet">{tech}</p>
            <h3 className="mt-2 font-display text-xl font-semibold">{job}</h3>
            <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
