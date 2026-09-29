"use client";

import { useState } from "react";

export type TrustExample = { template: string; rendered: string; facts: Array<[string, string, string]> };

const PRINCIPLES: Array<[string, string]> = [
  [
    "IMD stays the authority",
    "Every result is derived from, and stamped with, the official IMD bulletin. The ensembles are a labelled uncertainty envelope, not a rival forecast.",
  ],
  [
    "Gemini never writes a number",
    "The model writes words and placeholders. Code inserts every figure from the engine and rejects any digit it did not supply, in any script.",
  ],
  [
    "People decide",
    "Advisories are drafts until an officer approves them. CAP messages are marked Exercise and Restricted, for the SDMA's authorised originator only.",
  ],
  [
    "Uncertainty is shown, not hidden",
    "A chance and a P10–P90 window, never a single hour. Uncalibrated parameters are labelled prior. Replays use only what was known before landfall.",
  ],
];

/** Why an official can rely on it: the guardrails, with the placeholder mechanism made visible. */
export function Trust({ example }: { example: TrustExample }) {
  const [view, setView] = useState<"model" | "officer">("model");
  const parts = example.template.split(/(\{\{[a-z0-9_]+\}\})/g);
  const factText = Object.fromEntries(example.facts.map(([id, text]) => [id, text]));
  return (
    <section
      id="trust"
      aria-labelledby="trust-title"
      className="mx-auto max-w-7xl scroll-mt-16 px-4 py-24 sm:px-6"
    >
      <p className="eyebrow">Why trust it</p>
      <h2
        id="trust-title"
        className="mt-3 max-w-3xl font-display text-3xl font-semibold leading-tight sm:text-5xl"
      >
        Built so a Collector can sign off on it.
      </h2>
      <div className="mt-12 grid gap-6 lg:grid-cols-[1.15fr_1fr]">
        <div className="card p-6 sm:p-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="font-display text-lg font-semibold">One sentence, two views</h3>
            <div className="flex rounded-full border border-border p-1" role="group" aria-label="View">
              {(
                [
                  ["model", "What Gemini wrote"],
                  ["officer", "What the officer sees"],
                ] as const
              ).map(([k, label]) => (
                <button
                  key={k}
                  type="button"
                  aria-pressed={view === k}
                  onClick={() => setView(k)}
                  className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                    view === k ? "bg-cyan text-primary-ink" : "text-muted hover:text-fg"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          <p className="mt-6 text-lg leading-relaxed sm:text-xl" aria-live="polite">
            {parts.map((part, i) => {
              const m = part.match(/^\{\{([a-z0-9_]+)\}\}$/);
              if (!m) return <span key={i}>{part}</span>;
              const id = m[1]!;
              return view === "model" ? (
                <code
                  key={i}
                  className="rounded-md bg-violet/15 px-1.5 py-0.5 font-mono text-[0.85em] text-violet"
                >
                  {`{{${id}}}`}
                </code>
              ) : (
                <mark key={i} className="rounded-md bg-teal/15 px-1 text-teal">
                  {factText[id]}
                </mark>
              );
            })}
          </p>
          <table className="mt-6 w-full text-left text-xs">
            <caption className="sr-only">Facts inserted by code, with their sources</caption>
            <thead className="text-subtle">
              <tr>
                <th className="py-1 pr-3 font-normal">Fact</th>
                <th className="py-1 pr-3 font-normal">Inserted text</th>
                <th className="py-1 font-normal">Source row</th>
              </tr>
            </thead>
            <tbody>
              {example.facts.map(([id, text, src]) => (
                <tr key={id} className="border-t border-border align-top">
                  <td className="py-2 pr-3 font-mono text-violet">{id}</td>
                  <td className="py-2 pr-3">{text}</td>
                  <td className="py-2 text-subtle">{src}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-xs text-subtle">
            Illustration assembled from this run&apos;s facts. Live drafts, with the same check, are in the
            control room.
          </p>
        </div>
        <ul className="grid gap-3">
          {PRINCIPLES.map(([title, body], i) => (
            <li key={title} className="card card-hover p-5">
              <div className="flex items-baseline gap-3">
                <span className="font-display text-sm text-teal tabular-nums">0{i + 1}</span>
                <h3 className="font-display text-lg font-semibold">{title}</h3>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
