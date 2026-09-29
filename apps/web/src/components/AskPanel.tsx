"use client";

import { useState } from "react";
import { askAurora, type AskResult, type Lang } from "@/lib/api";

const SUGGESTED: Array<[string, Lang]> = [
  ["Which PHCs in Kakinada are most likely to lose road access before landfall?", "en-IN"],
  ["Where should we pre-position JCBs first, and by when?", "en-IN"],
  ["How many people in Kakinada could be cut off from a hospital by landfall?", "en-IN"],
  ["When does PHC Rachapalli likely lose road access?", "en-IN"],
  ["కాకినాడలో ఏ ఆరోగ్య కేంద్రాలకు రహదారి సంబంధం తెగిపోయే అవకాశం ఎక్కువ?", "te-IN"],
];

type Turn = { q: string; lang: Lang; res?: AskResult; error?: string };

export function AskPanel({ runId }: { runId: string }) {
  const [q, setQ] = useState("");
  const [lang, setLang] = useState<Lang>("en-IN");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);

  const send = async (question: string, language: Lang) => {
    if (!question.trim() || busy) return;
    setBusy(true);
    setQ("");
    setTurns((t) => [{ q: question, lang: language }, ...t]);
    try {
      const res = await askAurora(runId, question, language);
      setTurns((t) => [{ q: question, lang: language, res }, ...t.slice(1)]);
    } catch (e) {
      setTurns((t) => [
        { q: question, lang: language, error: e instanceof Error ? e.message : "failed" },
        ...t.slice(1),
      ]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted">
        An agent built with Google ADK and Gemini answers from AURORA&apos;s published facts only. It writes
        placeholders; code inserts the numbers and cites their source rows. If a number check fails you see
        the facts table instead.
      </p>
      <div className="flex flex-wrap gap-1">
        {SUGGESTED.map(([s, l]) => (
          <button
            key={s}
            onClick={() => send(s, l)}
            disabled={busy}
            className="rounded bg-surface-2 px-2 py-1 text-left text-[11px] text-fg hover:bg-surface-3 disabled:opacity-50"
            lang={l}
          >
            {s}
          </button>
        ))}
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void send(q, lang);
        }}
        className="flex gap-2"
      >
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          maxLength={500}
          placeholder="Ask about this run…"
          className="min-w-0 flex-1 rounded bg-surface px-2 py-1.5 text-sm"
          aria-label="Question"
        />
        <select
          value={lang}
          onChange={(e) => setLang(e.target.value as Lang)}
          className="rounded bg-surface px-1 text-xs"
          aria-label="Answer language"
        >
          <option value="en-IN">EN</option>
          <option value="te-IN">తె</option>
          <option value="hi-IN">हि</option>
        </select>
        <button disabled={busy} className="rounded bg-cyan text-primary-ink px-3 text-sm disabled:opacity-50">
          Ask
        </button>
      </form>
      <ul className="space-y-3">
        {turns.map((t, i) => (
          <li key={`${i}-${t.q}`} className="rounded bg-surface p-2 text-sm">
            <div className="text-xs text-muted" lang={t.lang}>
              {t.q}
            </div>
            {!t.res && !t.error && <div className="mt-1 text-xs text-subtle">Gemini is calling tools…</div>}
            {t.error && <div className="mt-1 text-xs text-red-300">{t.error}</div>}
            {t.res?.status === "answer" && (
              <>
                <div className="mt-1 whitespace-pre-wrap" lang={t.lang}>
                  {t.res.answer}
                </div>
                <details className="mt-1 text-[11px] text-muted">
                  <summary>
                    {t.res.citations?.length ?? 0} cited facts · {t.res.tool_calls} tool calls
                    {t.res.cached ? " · cached" : ""}
                  </summary>
                  <ul className="mt-1 space-y-0.5">
                    {t.res.citations?.map((c) => (
                      <li key={c.id}>
                        <span className="font-mono text-cyan">{c.id}</span> {c.meaning} · {c.source}
                      </li>
                    ))}
                  </ul>
                </details>
              </>
            )}
            {t.res?.status === "table" && (
              <div className="mt-1 text-xs">
                <div className="text-amber-300">
                  No safe written answer (the number check withheld it). Facts the tools returned:
                </div>
                <table className="mt-1 w-full">
                  <tbody>
                    {t.res.table.slice(0, 15).map((r) => (
                      <tr key={r.id} className="border-t border-border">
                        <td className="py-0.5 pr-2 text-muted">{r.meaning}</td>
                        <td className="py-0.5">{r.text}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
