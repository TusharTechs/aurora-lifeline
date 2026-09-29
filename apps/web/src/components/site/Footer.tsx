import Link from "next/link";
import { AuroraMark, Wordmark } from "@/components/brand/Logo";

const REPO = "https://github.com/TusharTechs/aurora-lifeline";
const BUILD = (process.env.NEXT_PUBLIC_BUILD_SHA ?? "dev").slice(0, 7);

export function Footer({ controlRoomHref }: { controlRoomHref: string }) {
  return (
    <footer className="relative mt-24 border-t border-border">
      <div className="mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-3">
            <AuroraMark size={40} />
            <Wordmark className="text-lg" />
          </div>
          <p className="mt-4 max-w-sm text-sm text-muted">
            Help should reach people before the roads close. AURORA turns the official cyclone forecast into
            the few decisions a district control room must make in time.
          </p>
          <p className="mt-4 max-w-sm text-xs text-subtle">
            Decision support, not a warning service. The India Meteorological Department is the authority for
            cyclone warnings in India. Alerts are issued only by the SDMA&apos;s authorised originator.
          </p>
        </div>
        <FooterCol
          title="Product"
          links={[
            [controlRoomHref, "Control room (Kakinada)"],
            ["/bulletin/", "Bulletin reader"],
            ["/proof/", "Proof: scores and misses"],
            ["/#how", "How it works"],
            ["/#trust", "Why trust it"],
          ]}
        />
        <FooterCol
          title="Project"
          links={[
            ["/about/", "About, data and credits"],
            ["/deck/", "Deck"],
            ["/about/#accessibility", "Accessibility"],
            ["/about/#privacy", "Privacy"],
            [REPO, "Source code (Apache-2.0)"],
          ]}
        />
        <div>
          <h2 className="text-sm font-semibold">Built with Google AI</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>Gemini on Agent Platform</li>
            <li>Agent Development Kit</li>
            <li>Google DeepMind WeatherNext</li>
            <li>Earth Engine · Maps Platform</li>
            <li>Cloud Run · Firebase</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-border">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-2 px-4 py-5 text-xs text-subtle sm:px-6">
          <span>
            Roads and places © OpenStreetMap contributors · Map data © Google · Ensembles © ECMWF (CC BY 4.0)
            and Google DeepMind Weather Lab (CC BY 4.0) · Population © WorldPop (CC BY 4.0)
          </span>
          <span>Build {BUILD} · Apache-2.0</span>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }: { title: string; links: Array<[string, string]> }) {
  return (
    <div>
      <h2 className="text-sm font-semibold">{title}</h2>
      <ul className="mt-3 space-y-2 text-sm">
        {links.map(([href, label]) => (
          <li key={href}>
            {href.startsWith("http") ? (
              <a href={href} className="text-muted hover:text-fg" rel="noopener">
                {label}
              </a>
            ) : (
              <Link href={href} className="text-muted hover:text-fg">
                {label}
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
