"use client";

import { useState } from "react";

export type QA = { q: string; a: string; how: string };

/** The four questions a control room asks, answered from the real run (the product in one glance). */
export function FourQuestions({ items, provenance }: { items: QA[]; provenance: string }) {
  const [active, setActive] = useState(0);
  const current = items[active]!;
  return (
    <section aria-labelledby="questions-title" className="mx-auto max-w-7xl px-4 py-24 sm:px-6">
      <p className="eyebrow">The gap</p>
      <h2
        id="questions-title"
        className="mt-3 max-w-4xl font-display text-3xl font-semibold leading-tight sm:text-5xl"
      >
        IMD tells you the storm. A district control room still has to answer four questions, in time.
      </h2>
      <div className="mt-12 grid gap-6 lg:grid-cols-[1fr_1.1fr]">
        <ol className="grid gap-3" role="tablist" aria-label="The four questions">
          {items.map((it, i) => (
            <li key={it.q} role="presentation">
              <button
                type="button"
                role="tab"
                id={`q-tab-${i}`}
                aria-selected={active === i}
                aria-controls="q-panel"
                onClick={() => setActive(i)}
                onMouseEnter={() => setActive(i)}
                onFocus={() => setActive(i)}
                className={`card card-hover flex w-full items-center gap-4 p-5 text-left transition-colors ${
                  active === i ? "!border-[color:var(--color-cyan)] bg-surface-2" : ""
                }`}
              >
                <span
                  className={`font-display text-sm tabular-nums ${active === i ? "text-cyan" : "text-subtle"}`}
                  aria-hidden
                >
                  0{i + 1}
                </span>
                <span className="font-display text-xl sm:text-2xl">{it.q}</span>
              </button>
            </li>
          ))}
        </ol>
        <div
          id="q-panel"
          role="tabpanel"
          aria-labelledby={`q-tab-${active}`}
          className="card atmosphere relative flex min-h-72 flex-col justify-between overflow-hidden p-8"
        >
          <div key={active} className="animate-[fadeUp_.5s_var(--ease-out-soft)]">
            <p className="text-sm text-muted">AURORA&apos;s answer for Kakinada</p>
            <p className="mt-4 font-display text-3xl font-semibold leading-snug sm:text-4xl">
              <span className="text-aurora">{current.a}</span>
            </p>
            <p className="mt-5 max-w-lg text-muted">{current.how}</p>
          </div>
          <p className="mt-8 border-t border-border pt-4 text-xs text-subtle">{provenance}</p>
        </div>
      </div>
    </section>
  );
}
