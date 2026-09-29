"use client";

import { useState } from "react";

export type Persona = {
  role: string;
  who: string;
  asks: string;
  gets: string;
  rows: Array<[string, string]>;
};

/** The people AURORA serves, each with what they actually get from this run. */
export function Personas({ personas }: { personas: Persona[] }) {
  const [active, setActive] = useState(0);
  const p = personas[active]!;
  return (
    <section aria-labelledby="who-title" className="mx-auto max-w-7xl px-4 py-24 sm:px-6">
      <p className="eyebrow">Who it is for</p>
      <h2
        id="who-title"
        className="mt-3 max-w-3xl font-display text-3xl font-semibold leading-tight sm:text-5xl"
      >
        One forecast, read four ways.
      </h2>
      <div className="mt-10 flex flex-wrap gap-2" role="tablist" aria-label="Roles">
        {personas.map((x, i) => (
          <button
            key={x.role}
            type="button"
            role="tab"
            id={`p-tab-${i}`}
            aria-selected={active === i}
            aria-controls="p-panel"
            onClick={() => setActive(i)}
            className={`btn !min-h-11 text-sm ${active === i ? "btn-primary" : "btn-ghost"}`}
          >
            {x.role}
          </button>
        ))}
      </div>
      <div
        id="p-panel"
        role="tabpanel"
        aria-labelledby={`p-tab-${active}`}
        className="card atmosphere mt-6 grid gap-8 overflow-hidden p-6 sm:p-10 lg:grid-cols-[1fr_1.2fr]"
      >
        <div key={active} className="animate-[fadeUp_.45s_var(--ease-out-soft)]">
          <p className="text-sm text-muted">{p.who}</p>
          <p className="mt-4 font-display text-2xl leading-snug sm:text-3xl">“{p.asks}”</p>
          <p className="mt-5 text-muted">{p.gets}</p>
        </div>
        <ul
          key={`r${active}`}
          className="grid content-start gap-2 animate-[fadeUp_.55s_var(--ease-out-soft)]"
        >
          {p.rows.map(([a, b]) => (
            <li
              key={a}
              className="flex items-baseline justify-between gap-4 rounded-xl bg-surface-2/80 px-4 py-3"
            >
              <span className="text-sm">{a}</span>
              <span className="shrink-0 text-right text-sm font-semibold text-teal tabular-nums">{b}</span>
            </li>
          ))}
          <li className="px-1 pt-1 text-xs text-subtle">
            From the Montha replay, IMD Bulletin No. 21, Kakinada.
          </li>
        </ul>
      </div>
    </section>
  );
}
