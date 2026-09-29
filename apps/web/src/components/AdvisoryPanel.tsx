"use client";

import { useState } from "react";
import { draftAdvisory, type AdvisoryFields, type AdvisoryResult, type Audience, type Lang } from "@/lib/api";

const LANGS: Array<[Lang, string]> = [
  ["en-IN", "English"],
  ["te-IN", "తెలుగు"],
  ["hi-IN", "हिन्दी"],
];
const AUDIENCES: Array<[Audience, string]> = [
  ["district_officer", "Collector / DDMA"],
  ["health", "DM&HO / PHC doctors"],
  ["public_works", "R&B / PR engineers"],
];
const FIELDS: Array<[keyof AdvisoryFields, string]> = [
  ["headline", "Headline"],
  ["sms_text", "SMS"],
  ["description", "Situation"],
  ["instruction", "Recommended actions"],
  ["voice_script", "Voice script"],
];

function download(name: string, text: string) {
  const url = URL.createObjectURL(new Blob([text], { type: "application/xml" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export function AdvisoryPanel({ runId, lgd }: { runId: string; lgd: string }) {
  const [lang, setLang] = useState<Lang>("en-IN");
  const [audience, setAudience] = useState<Audience>("district_officer");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AdvisoryResult | null>(null);
  const [approved, setApproved] = useState(false);
  const [showTemplate, setShowTemplate] = useState(false);

  const run = async () => {
    setBusy(true);
    setError(null);
    setApproved(false);
    try {
      setResult(await draftAdvisory(runId, lgd, lang, audience));
    } catch (e) {
      setError(e instanceof Error ? e.message : "request failed");
    } finally {
      setBusy(false);
    }
  };

  const shown = result?.rendered?.[result.language] ?? result?.rendered?.["en-IN"];
  const template = result?.drafts?.[result.language];
  const bt = result?.checks?.back_translation;

  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-400">
        Gemini drafts the wording; every number, name and time is inserted by the engine from cited facts. A
        draft is never sent: an officer must approve it, and CAP output is for the SDMA originator.
      </p>
      <div className="flex flex-wrap gap-2">
        {LANGS.map(([k, label]) => (
          <button
            key={k}
            onClick={() => setLang(k)}
            className={`rounded px-2 py-1 text-xs ${lang === k ? "bg-sky-600 text-white" : "bg-slate-800 text-slate-300"}`}
          >
            {label}
          </button>
        ))}
      </div>
      <select
        value={audience}
        onChange={(e) => setAudience(e.target.value as Audience)}
        className="w-full rounded bg-slate-900 px-2 py-1 text-xs"
        aria-label="Audience"
      >
        {AUDIENCES.map(([k, label]) => (
          <option key={k} value={k}>
            {label}
          </option>
        ))}
      </select>
      <button
        onClick={run}
        disabled={busy}
        className="w-full rounded bg-sky-600 px-3 py-2 text-sm font-medium disabled:opacity-50"
      >
        {busy ? "Gemini is drafting… (checks run after)" : "Draft advisory with Gemini"}
      </button>
      {error && <div className="rounded bg-red-900/40 p-2 text-xs text-red-200">{error}</div>}

      {result && result.status === "rejected" && (
        <div className="rounded bg-red-900/40 p-2 text-xs text-red-200">
          The draft failed the number check twice and was withheld: {result.problems?.join("; ")}
        </div>
      )}

      {result && shown && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1 text-[10px]">
            <span className="rounded bg-amber-500/20 px-1.5 py-0.5 text-amber-300">
              {approved
                ? "APPROVED (simulated officer) · not dispatched"
                : "DRAFT · pending officer approval"}
            </span>
            <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-emerald-300">
              number check passed
            </span>
            {result.badges.map((b) => (
              <span key={b} className="rounded bg-slate-700 px-1.5 py-0.5">
                {b}
              </span>
            ))}
            {result.cached && (
              <span className="rounded bg-slate-800 px-1.5 py-0.5">cached replay output</span>
            )}
          </div>
          {FIELDS.map(([k, label]) => (
            <div key={k} className="rounded bg-slate-900 p-2">
              <div className="text-[10px] uppercase tracking-wider text-slate-500">{label}</div>
              <div className="whitespace-pre-wrap text-sm" lang={result.language}>
                {shown[k]}
              </div>
            </div>
          ))}
          {bt && (
            <div
              className={`rounded p-2 text-xs ${bt.flag ? "bg-red-900/40 text-red-200" : "bg-slate-900 text-slate-300"}`}
            >
              Back-translation similarity to the English draft {bt.similarity.toFixed(2)} (flag below{" "}
              {bt.threshold}, {bt.threshold_status.toLowerCase()}){bt.flag ? ": review the translation" : ""}
            </div>
          )}
          <button onClick={() => setShowTemplate((s) => !s)} className="text-xs text-sky-300 underline">
            {showTemplate ? "Hide" : "Show"} what Gemini wrote (placeholders) and the cited facts
          </button>
          {showTemplate && template && (
            <div className="space-y-2 rounded bg-slate-900 p-2 text-xs">
              <pre className="whitespace-pre-wrap text-slate-300">{template.description}</pre>
              <pre className="whitespace-pre-wrap text-slate-300">{template.instruction}</pre>
              <table className="w-full text-left">
                <tbody>
                  {result.facts
                    .filter(
                      (f) =>
                        template.placeholders_used.includes(f.id) ||
                        template.description.includes(`{{${f.id}}}`) ||
                        template.instruction.includes(`{{${f.id}}}`),
                    )
                    .map((f) => (
                      <tr key={f.id} className="border-t border-slate-800 align-top">
                        <td className="py-1 pr-2 font-mono text-sky-300">{f.id}</td>
                        <td className="py-1 pr-2">{f.text[result.language] ?? f.text["en-IN"]}</td>
                        <td className="py-1 text-slate-500">
                          {f.source.table} · {f.source.row_id}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="flex gap-2">
            <button
              onClick={() => setApproved(true)}
              disabled={approved}
              className="flex-1 rounded bg-emerald-700 px-2 py-1.5 text-xs disabled:opacity-50"
            >
              Approve as demo officer (SIMULATED)
            </button>
            {result.cap_xml && (
              <button
                onClick={() => download(`aurora-cap-${lgd}-${result.language}.xml`, result.cap_xml ?? "")}
                className="flex-1 rounded bg-slate-700 px-2 py-1.5 text-xs"
              >
                Download CAP 1.2 (Exercise)
              </button>
            )}
          </div>
          <div className="text-[10px] text-slate-500">
            CAP: status Exercise, scope Restricted, for the SDMA originator to review in Sachet; XSD check{" "}
            {result.cap_problems && result.cap_problems.length === 0
              ? "passed"
              : `failed: ${result.cap_problems?.join("; ")}`}
            . Prompt {result.prompt_version}.
          </div>
        </div>
      )}
    </div>
  );
}
