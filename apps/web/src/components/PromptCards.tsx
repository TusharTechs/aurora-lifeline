"use client";

import { useState } from "react";
import prompts from "@/data/prompts.json";

/** The agents' real system instructions, to copy into Google AI Studio (public data only). */
export function PromptCards() {
  const [copied, setCopied] = useState<string | null>(null);
  const copy = async (agent: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(agent);
      window.setTimeout(() => setCopied(null), 2000);
    } catch {
      setCopied(null);
    }
  };
  return (
    <div className="mt-6 grid gap-4">
      {prompts.map((p) => (
        <details key={p.agent} className="card group p-5">
          <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-3">
            <span>
              <span className="font-display text-lg font-semibold">{p.agent}</span>{" "}
              <span className="text-xs text-subtle">{p.version}</span>
            </span>
            <span className="text-sm text-cyan group-open:hidden">Show the instruction</span>
          </summary>
          <pre className="mt-4 max-h-72 overflow-auto whitespace-pre-wrap rounded-xl bg-surface-2 p-4 font-mono text-xs leading-relaxed text-muted">
            {p.system}
          </pre>
          <p className="mt-3 text-sm text-muted">{p.try}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void copy(p.agent, p.system)}
              className="btn btn-ghost !min-h-10 text-sm"
            >
              {copied === p.agent ? "Copied" : "Copy instruction"}
            </button>
            <a
              href="https://aistudio.google.com/prompts/new_chat"
              target="_blank"
              rel="noopener"
              className="btn btn-primary !min-h-10 text-sm"
            >
              Open Google AI Studio
            </a>
          </div>
        </details>
      ))}
    </div>
  );
}
