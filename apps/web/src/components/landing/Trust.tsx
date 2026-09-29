"use client";

import { useEffect, useState } from "react";
import { draftAdvisory } from "@/lib/api";

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
export function Trust({ example, runId, lgd }: { example: TrustExample; runId: string; lgd: string }) {
  const [view, setView] = useState<"model" | "officer">("model");
  // Prefer the real, cached Gemini draft for this district; fall back to the labelled illustration.
  const [live, setLive] = useState<{ ex: TrustExample; model: string; version: string } | null>(null);
  useEffect(() => {
    let alive = true;
    draftAdvisory(runId, lgd, "en-IN", "district_officer")
      .then((r) => {
        const d = r.drafts?.["en-IN"];
        if (!alive || r.status !== "draft" || !d) return;
        const template = d.description;
        const used = new Set([...template.matchAll(/\{\{([a-z0-9_]+)\}\}/g)].map((m) => m[1]));
        const facts = r.facts
          .filter((f) => used.has(f.id))
          .map(
            (f) =>
              [f.id, f.text["en-IN"] ?? "", `${f.source.table} · ${f.source.row_id}`] as [
                string,
                string,
                string,
              ],
          );
        const model = (r as unknown as { calls?: Array<{ model: string }> }).calls?.[0]?.model ?? "Gemini";
        setLive({ ex: { template, rendered: "", facts }, model, version: r.prompt_version });
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, [runId, lgd]);
  const ex = live?.ex ?? example;
  const parts = ex.template.split(/(\{\{[a-z0-9_]+\}\})/g);
  const factText = Object.fromEntries(ex.facts.map(([id, text]) => [id, text]));
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
            <h3 className="font-display text-lg font-semibold">
              {live ? "A real Gemini draft, two views" : "One sentence, two views"}
            </h3>
            <div className="flex rounded-full border border-border p-1" role="group" aria-label="View">
              {(
                [
                  ["model", live ? "What Gemini wrote" : "Placeholders"],
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
              {ex.facts.map(([id, text, src]) => (
                <tr key={id} className="border-t border-border align-top">
                  <td className="py-2 pr-3 font-mono text-violet">{id}</td>
                  <td className="py-2 pr-3">{text}</td>
                  <td className="py-2 text-subtle">{src}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 text-xs text-subtle">
            {live
              ? `The description field of the Kakinada advisory, drafted by ${live.model} (${live.version}) and cached for the replay. Only the engine's facts can fill the placeholders.`
              : "Illustration assembled from this run's facts; the live draft appears here when the API responds."}
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
