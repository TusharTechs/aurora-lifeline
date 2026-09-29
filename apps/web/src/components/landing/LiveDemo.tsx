"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { askAurora, draftAdvisory, type AdvisoryResult, type AskResult, type Lang } from "@/lib/api";

export type DemoFacility = { name: string; type: string; hours: Array<number | null>; p: number };

const QUESTIONS = [
  "Which PHCs in Kakinada are most likely to lose road access before landfall?",
  "Where should we pre-position JCBs first, and by when?",
  "When does PHC Rachapalli likely lose road access?",
];
const LANGS: Array<[Lang, string]> = [
  ["en-IN", "English"],
  ["te-IN", "తెలుగు"],
  ["hi-IN", "हिन्दी"],
];

function probAt(hours: Array<number | null>, t: number): number {
  let p = 0;
  hours.forEach((h, i) => {
    if (h !== null && h <= t) p = (i + 1) / 10;
  });
  return p;
}

function barColor(p: number): string {
  if (p <= 0) return "var(--color-safe)";
  if (p < 0.2) return "var(--color-risk-1)";
  if (p < 0.4) return "var(--color-risk-2)";
  return "var(--color-risk-3)";
}

function lakh(n: number): string {
  return n >= 100_000
    ? `${(n / 100_000).toFixed(1)} lakh`
    : (Math.round(n / 100) * 100).toLocaleString("en-IN");
}

export function LiveDemo({
  runId,
  lgd,
  controlRoomHref,
  facilities,
  hourly,
  nowUtc,
  landfallH,
}: {
  runId: string;
  lgd: string;
  controlRoomHref: string;
  facilities: DemoFacility[];
  hourly: number[];
  nowUtc: string;
  landfallH: number;
}) {
  const [t, setT] = useState(Math.round(landfallH));
  const [mode, setMode] = useState<"ask" | "draft">("ask");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answer, setAnswer] = useState<AskResult | null>(null);
  const [question, setQuestion] = useState<string | null>(null);
  const [draft, setDraft] = useState<AdvisoryResult | null>(null);

  const when = useMemo(
    () =>
      new Intl.DateTimeFormat("en-IN", {
        timeZone: "Asia/Kolkata",
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
      }).format(new Date(Date.parse(nowUtc) + t * 3_600_000)),
    [nowUtc, t],
  );
  const h2l = Math.round(landfallH - t);

  const run = async (fn: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : "The request did not complete.");
    } finally {
      setBusy(false);
    }
  };
  const ask = (q: string) =>
    run(async () => {
      setQuestion(q);
      setAnswer(null);
      setAnswer(await askAurora(runId, q, "en-IN"));
    });
  const drawUp = (lang: Lang) =>
    run(async () => {
      setDraft(null);
      setDraft(await draftAdvisory(runId, lgd, lang, "district_officer"));
    });
  const shown = draft?.rendered?.[draft.language] ?? draft?.rendered?.["en-IN"];

  return (
    <section
      id="try"
      aria-labelledby="try-title"
      className="mx-auto max-w-7xl scroll-mt-16 px-4 py-24 sm:px-6"
    >
      <p className="eyebrow">Try it</p>
      <h2
        id="try-title"
        className="mt-3 max-w-3xl font-display text-3xl font-semibold leading-tight sm:text-5xl"
      >
        Stand in Kakinada&apos;s control room, 62 hours out.
      </h2>
      <p className="mt-4 max-w-2xl text-lg text-muted">
        Move through time and watch health facilities lose their roads. Then ask AURORA, or have Gemini draft
        the advisory. These run live on Google Cloud; replies are cached so every visitor sees the same
        replay.
      </p>
      <div className="mt-12 grid gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <div className="flex items-baseline justify-between gap-4">
            <h3 className="font-display text-lg font-semibold">Road access to referral care</h3>
            <span className="text-sm text-muted tabular-nums">
              {when} IST · {h2l > 0 ? `T−${h2l} h` : `T+${-h2l} h`}
            </span>
          </div>
          <label className="mt-4 block">
            <span className="text-xs text-muted">Hours after IMD Bulletin No. 21</span>
            <input
              type="range"
              min={0}
              max={Math.round(landfallH) + 12}
              value={t}
              onChange={(e) => setT(Number(e.target.value))}
              className="mt-2 w-full accent-[var(--color-cyan)]"
            />
          </label>
          <p className="mt-3 text-sm">
            <span className="font-display text-2xl font-semibold tabular-nums">
              {lakh(hourly[Math.min(t, hourly.length - 1)] ?? 0)}
            </span>{" "}
            <span className="text-muted">
              people cut off from every public hospital (median of the storm futures)
            </span>
          </p>
          <ul className="mt-5 space-y-3">
            {facilities.map((f) => {
              const p = probAt(f.hours, t);
              return (
                <li key={f.name}>
                  <div className="flex justify-between gap-3 text-sm">
                    <span className="truncate">
                      {f.name} <span className="text-subtle">· {f.type}</span>
                    </span>
                    <span className="tabular-nums text-muted">
                      {p > 0 ? `≥${Math.round(p * 100)}%` : "reachable"}
                    </span>
                  </div>
                  <div
                    className="mt-1.5 h-2 overflow-hidden rounded-full bg-surface-3"
                    role="img"
                    aria-label={`${f.name}: ${p > 0 ? `at least ${Math.round(p * 100)} percent chance cut off by now` : "reachable in every future so far"}`}
                  >
                    <div
                      className="h-full rounded-full transition-[width,background-color] duration-500"
                      style={{ width: `${Math.max(p * 100, 2)}%`, background: barColor(p) }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
          <p className="mt-5 text-xs text-subtle">
            Chances move in steps of ten points: that is the honest resolution of a thousand-member ensemble
            summary.
          </p>
        </div>

        <div className="card flex flex-col p-6">
          <div className="flex gap-2" role="tablist" aria-label="Live AI">
            {(
              [
                ["ask", "Ask AURORA · ADK agent"],
                ["draft", "Draft the advisory · Gemini"],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                type="button"
                role="tab"
                aria-selected={mode === k}
                onClick={() => setMode(k)}
                className={`btn !min-h-10 flex-1 text-sm ${mode === k ? "btn-primary" : "btn-ghost"}`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="mt-5 flex-1" role="tabpanel" aria-live="polite" aria-busy={busy}>
            {mode === "ask" ? (
              <>
                <div className="flex flex-wrap gap-2">
                  {QUESTIONS.map((q) => (
                    <button
                      key={q}
                      type="button"
                      disabled={busy}
                      onClick={() => void ask(q)}
                      className="rounded-2xl border border-border px-3 py-2 text-left text-sm hover:border-border-strong hover:bg-white/5 disabled:opacity-50"
                    >
                      {q}
                    </button>
                  ))}
                </div>
                {question && (
                  <div className="mt-5 rounded-2xl bg-surface-2 p-4">
                    <p className="text-xs text-muted">{question}</p>
                    {busy && !answer && <Thinking label="The agent is calling its tools" />}
                    {answer?.status === "answer" && (
                      <>
                        <p className="mt-2 whitespace-pre-wrap leading-relaxed">{answer.answer}</p>
                        <p className="mt-3 text-xs text-subtle">
                          {answer.citations?.length ?? 0} cited facts from the run · {answer.tool_calls} tool
                          calls
                          {answer.cached ? " · cached replay" : ""}
                        </p>
                      </>
                    )}
                    {answer?.status === "table" && (
                      <p className="mt-2 text-sm text-warning">
                        The number check withheld a written answer; the control room shows the facts table
                        instead.
                      </p>
                    )}
                  </div>
                )}
              </>
            ) : (
              <>
                <div className="flex flex-wrap gap-2">
                  {LANGS.map(([k, label]) => (
                    <button
                      key={k}
                      type="button"
                      disabled={busy}
                      onClick={() => void drawUp(k)}
                      className="btn btn-ghost !min-h-10 text-sm"
                      lang={k}
                    >
                      {label}
                    </button>
                  ))}
                </div>
                {busy && !draft && <Thinking label="Gemini is drafting; code checks every number" />}
                {draft && shown && (
                  <div className="mt-5 space-y-3 rounded-2xl bg-surface-2 p-4" lang={draft.language}>
                    <div className="flex flex-wrap gap-1.5 text-[11px]">
                      <span className="chip border-warning/40 text-warning">
                        Draft · needs officer approval
                      </span>
                      <span className="chip border-safe/40 text-safe">Number check passed</span>
                      {draft.badges.map((b) => (
                        <span key={b} className="chip">
                          {b}
                        </span>
                      ))}
                    </div>
                    <p className="font-display text-lg font-semibold">{shown.headline}</p>
                    <p className="text-sm leading-relaxed text-muted">{shown.sms_text}</p>
                  </div>
                )}
              </>
            )}
            {error && (
              <div role="alert" className="mt-4 rounded-2xl border border-danger/40 bg-danger/10 p-3 text-sm">
                {error}
              </div>
            )}
          </div>
          <Link href={controlRoomHref} className="btn btn-ghost mt-6 self-start text-sm">
            Open the full control room →
          </Link>
        </div>
      </div>
    </section>
  );
}

function Thinking({ label }: { label: string }) {
  return (
    <p className="mt-3 inline-flex items-center gap-2 text-sm text-muted">
      <span className="pulse-dot text-cyan" aria-hidden /> {label}…
    </p>
  );
}
