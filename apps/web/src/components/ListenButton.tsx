"use client";

import { useState } from "react";
import { advisoryVoice, type Audience, type Lang } from "@/lib/api";

/** Reads the approved-language voice script aloud (Cloud Text-to-Speech, Gemini-TTS). */
export function ListenButton({
  runId,
  lgd,
  language,
  audience,
}: {
  runId: string;
  lgd: string;
  language: Lang;
  audience: Audience;
}) {
  const [busy, setBusy] = useState(false);
  const [src, setSrc] = useState<string | null>(null);
  const [meta, setMeta] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const load = async () => {
    setBusy(true);
    setError(null);
    try {
      const v = await advisoryVoice(runId, lgd, language, audience);
      setSrc(`data:${v.mime};base64,${v.audio_b64}`);
      setMeta(`${v.model} · voice ${v.voice}${v.cached ? " · cached" : ""}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "The voice service did not answer.");
    } finally {
      setBusy(false);
    }
  };
  if (src)
    return (
      <div className="space-y-1">
        <audio controls autoPlay src={src} className="w-full" aria-label="Advisory read aloud" />
        <p className="text-[11px] text-subtle">
          Cloud Text-to-Speech {meta}. Transcript: the voice script above.
        </p>
      </div>
    );
  return (
    <div>
      <button
        type="button"
        onClick={() => void load()}
        disabled={busy}
        className="btn btn-ghost !min-h-10 text-sm"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
          <path d="M4 10v4h4l5 4V6L8 10H4z" fill="currentColor" />
          <path
            d="M16 9a4 4 0 010 6M18.5 6.5a8 8 0 010 11"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
          />
        </svg>
        {busy ? "Preparing the voice…" : "Listen (Gemini-TTS)"}
      </button>
      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
    </div>
  );
}
