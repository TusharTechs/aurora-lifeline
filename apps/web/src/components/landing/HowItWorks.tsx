"use client";

import { useEffect, useRef, useState } from "react";

export type Step = { title: string; body: string; stat?: string };

const TRACKS = [
  "M480 330C440 318 410 296 392 262",
  "M480 300C446 294 418 276 402 246",
  "M480 350C432 336 396 306 380 270",
  "M470 360C430 340 404 312 396 276",
  "M480 280C452 276 428 262 414 238",
  "M480 318C444 306 420 286 408 256",
  "M476 360C440 350 410 322 388 284",
];
const TRACK_COLORS = ["var(--color-violet)", "var(--color-cyan)", "var(--color-teal)"];
const VILLAGES: Array<[number, number]> = [
  [372, 168],
  [404, 128],
  [352, 78],
  [300, 150],
];

/**
 * Scroll-driven story: a sticky scene of one district (a hospital, a river, one bridge, a PHC and its
 * villages) that changes as each step scrolls past. The scene is a diagram, not a map; the numbers
 * in the steps come from the real run.
 */
export function HowItWorks({ steps }: { steps: Step[] }) {
  const [active, setActive] = useState(0);
  const refs = useRef<Array<HTMLLIElement | null>>([]);

  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) setActive(Number((e.target as HTMLElement).dataset.step));
        }
      },
      { rootMargin: "-45% 0px -45% 0px" },
    );
    refs.current.forEach((el) => el && io.observe(el));
    return () => io.disconnect();
  }, []);

  const on = (i: number) => (active >= i ? "opacity-100" : "opacity-0");
  return (
    <section
      id="how"
      aria-labelledby="how-title"
      className="relative mx-auto max-w-7xl scroll-mt-16 px-4 py-24 sm:px-6"
    >
      <p className="eyebrow">How it works</p>
      <h2
        id="how-title"
        className="mt-3 max-w-3xl font-display text-3xl font-semibold leading-tight sm:text-5xl"
      >
        From one official bulletin to the few decisions that matter.
      </h2>
      <div className="mt-14 grid gap-10 lg:grid-cols-[1.1fr_1fr]">
        <div className="lg:order-2">
          <div className="sticky top-20 lg:top-28">
            <figure className="card atmosphere relative aspect-[4/3] overflow-hidden">
              <svg
                viewBox="0 0 480 360"
                className="h-full w-full"
                role="img"
                aria-labelledby="scene-title scene-desc"
              >
                <title id="scene-title">{`Step ${active + 1} of ${steps.length}: ${steps[active]?.title ?? ""}`}</title>
                <desc id="scene-desc">
                  A diagram of a coastal district: a district hospital on the left, a river crossed by one
                  bridge, and a primary health centre with its villages on the far side.
                </desc>
                <defs>
                  <linearGradient id="sea" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0" stopColor="#0e2440" />
                    <stop offset="1" stopColor="#091526" />
                  </linearGradient>
                </defs>
                <path d="M290 360C320 300 380 250 480 215L480 360Z" fill="url(#sea)" />
                <path
                  d="M290 360C320 300 380 250 480 215"
                  stroke="var(--color-dawn)"
                  strokeOpacity=".5"
                  fill="none"
                  strokeWidth="1.5"
                />
                {/* River, which floods in step 3 */}
                <path
                  d="M60 40C120 110 160 160 190 196S262 282 318 316"
                  stroke="var(--color-cyan)"
                  strokeOpacity={active >= 2 ? 0.55 : 0.25}
                  strokeWidth={active >= 2 ? 16 : 6}
                  fill="none"
                  strokeLinecap="round"
                  className="transition-all duration-1000"
                />
                {/* Roads */}
                <g stroke="var(--color-border-strong)" strokeWidth="3" fill="none" strokeLinecap="round">
                  <path d="M92 282L190 196" />
                  <path
                    d="M190 196L330 120"
                    stroke={active >= 3 ? "var(--color-risk-3)" : "var(--color-border-strong)"}
                    strokeDasharray={active >= 3 ? "6 6" : undefined}
                    className="transition-[stroke] duration-700"
                  />
                  {VILLAGES.map(([x, y]) => (
                    <path key={`${x}${y}`} d={`M330 120L${x} ${y}`} strokeWidth="2" />
                  ))}
                </g>
                {/* District hospital and PHC */}
                <g>
                  <rect
                    x="64"
                    y="266"
                    width="44"
                    height="32"
                    rx="8"
                    fill="var(--color-surface-3)"
                    stroke="var(--color-safe)"
                    strokeWidth="2"
                  />
                  <text
                    x="86"
                    y="287"
                    textAnchor="middle"
                    fontSize="11"
                    fill="var(--color-fg)"
                    fontWeight="600"
                  >
                    DH
                  </text>
                  <text x="86" y="316" textAnchor="middle" fontSize="10" fill="var(--color-muted)">
                    District hospital
                  </text>
                </g>
                <circle
                  cx="330"
                  cy="120"
                  r={active >= 3 ? 26 : 0}
                  fill="var(--color-risk-3)"
                  fillOpacity=".16"
                  className="transition-all duration-700"
                />
                <rect
                  x="312"
                  y="104"
                  width="36"
                  height="32"
                  rx="8"
                  fill="var(--color-surface-3)"
                  stroke={active >= 3 ? "var(--color-risk-3)" : "var(--color-safe)"}
                  strokeWidth="2"
                  className="transition-[stroke] duration-700"
                />
                <text
                  x="330"
                  y="125"
                  textAnchor="middle"
                  fontSize="11"
                  fill="var(--color-fg)"
                  fontWeight="600"
                >
                  PHC
                </text>
                {VILLAGES.map(([x, y]) => (
                  <circle
                    key={`v${x}${y}`}
                    cx={x}
                    cy={y}
                    r="7"
                    fill={active >= 3 ? "var(--color-violet)" : "var(--color-surface-3)"}
                    stroke="var(--color-muted)"
                    strokeWidth="1"
                    className="transition-[fill] duration-700"
                  />
                ))}
                {/* Step 1: the bulletin, read */}
                <g
                  className={`transition-opacity duration-700 ${active === 0 ? "opacity-100" : "opacity-0"}`}
                >
                  <rect
                    x="24"
                    y="24"
                    width="210"
                    height="118"
                    rx="12"
                    fill="var(--color-surface)"
                    stroke="var(--color-border-strong)"
                  />
                  <text x="38" y="46" fontSize="10" fill="var(--color-muted)">
                    IMD National Bulletin No. 21
                  </text>
                  {[62, 76, 90].map((y, i) => (
                    <rect
                      key={y}
                      x="38"
                      y={y}
                      width={[170, 150, 160][i]}
                      height="7"
                      rx="3"
                      fill="var(--color-border-strong)"
                    />
                  ))}
                  <rect
                    x="36"
                    y="86"
                    width="164"
                    height="15"
                    rx="4"
                    fill="var(--color-teal)"
                    fillOpacity=".18"
                    stroke="var(--color-teal)"
                    strokeOpacity=".6"
                  />
                  <text x="38" y="120" fontSize="10" fill="var(--color-teal)">
                    track · winds · rain · surge · quotes ✓
                  </text>
                </g>
                {/* Step 2: storm futures */}
                <g
                  className={`transition-opacity duration-700 ${on(1)}`}
                  fill="none"
                  strokeLinecap="round"
                  strokeWidth="2"
                >
                  {TRACKS.map((d, i) => (
                    <path
                      key={d}
                      d={d}
                      stroke={TRACK_COLORS[i % 3]}
                      strokeOpacity=".75"
                      pathLength={1}
                      strokeDasharray="1"
                      strokeDashoffset={active >= 1 ? 0 : 1}
                      style={{ transition: `stroke-dashoffset 1.2s var(--ease-out-soft) ${i * 90}ms` }}
                    />
                  ))}
                </g>
                {/* Step 3: water at the crossing */}
                <g className={`transition-opacity duration-700 ${on(2)}`}>
                  {Array.from({ length: 14 }, (_, i) => (
                    <path
                      key={i}
                      d={`M${40 + i * 30} ${20 + (i % 3) * 18}l-6 14`}
                      stroke="var(--color-cyan)"
                      strokeOpacity=".45"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  ))}
                  <circle
                    cx="190"
                    cy="196"
                    r="12"
                    fill="var(--color-risk-2)"
                    fillOpacity=".25"
                    stroke="var(--color-risk-2)"
                    strokeWidth="2"
                  />
                </g>
                {/* Step 4: cut off */}
                <g className={`transition-opacity duration-700 ${on(3)}`}>
                  <rect
                    x="250"
                    y="30"
                    width="206"
                    height="44"
                    rx="10"
                    fill="var(--color-surface)"
                    stroke="var(--color-risk-3)"
                    strokeOpacity=".7"
                  />
                  <text x="262" y="49" fontSize="11" fill="var(--color-fg)" fontWeight="600">
                    Road to hospital lost
                  </text>
                  <text x="262" y="64" fontSize="10" fill="var(--color-muted)">
                    chance, and a P10–P90 time window
                  </text>
                </g>
                {/* Step 5: act before the road closes */}
                <g className={`transition-opacity duration-700 ${on(4)}`}>
                  <circle cx="190" cy="196" r="9" fill="var(--color-risk-1)" />
                  <path d="M190 196L150 150" stroke="var(--color-risk-1)" strokeWidth="1.5" />
                  <rect
                    x="24"
                    y="118"
                    width="150"
                    height="36"
                    rx="8"
                    fill="var(--color-surface)"
                    stroke="var(--color-risk-1)"
                  />
                  <text x="34" y="140" fontSize="10.5" fill="var(--color-fg)">
                    Stage a JCB here, early
                  </text>
                  <rect
                    x="130"
                    y="300"
                    width="190"
                    height="42"
                    rx="10"
                    fill="var(--color-surface)"
                    stroke="var(--color-border-strong)"
                  />
                  <text x="142" y="318" fontSize="10" fill="var(--color-fg)" fontWeight="600">
                    Advisory · draft
                  </text>
                  <text x="142" y="332" fontSize="9.5" fill="var(--color-muted)">
                    officer approves · CAP to SDMA
                  </text>
                </g>
              </svg>
              <figcaption className="sr-only">
                The scene updates as you read each step. Illustrative diagram; real results are in the control
                room.
              </figcaption>
            </figure>
            <div className="mt-4 flex gap-1.5" aria-hidden>
              {steps.map((s, i) => (
                <span
                  key={s.title}
                  className={`h-1 flex-1 rounded-full transition-colors duration-500 ${i <= active ? "bg-cyan" : "bg-border"}`}
                />
              ))}
            </div>
          </div>
        </div>
        <ol className="lg:order-1">
          {steps.map((s, i) => (
            <li
              key={s.title}
              data-step={i}
              ref={(el) => {
                refs.current[i] = el;
              }}
              className={`flex min-h-[46vh] flex-col justify-center border-l-2 py-10 pl-6 transition-colors duration-500 lg:min-h-[62vh] ${
                active === i ? "border-cyan" : "border-border"
              }`}
            >
              <span className="font-display text-sm text-cyan tabular-nums">Step {i + 1}</span>
              <h3
                className={`mt-2 font-display text-2xl font-semibold sm:text-3xl ${active === i ? "" : "text-muted"}`}
              >
                {s.title}
              </h3>
              <p className="mt-3 max-w-xl text-base leading-relaxed text-muted sm:text-lg">{s.body}</p>
              {s.stat && <p className="mt-4 font-display text-lg text-teal">{s.stat}</p>}
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
