"use client";

import { useEffect, useId, useRef, useState } from "react";

type Prefs = { motion: boolean; contrast: boolean; text: boolean };
const KEY = "aurora-a11y";
const LABELS: Array<[keyof Prefs, string, string]> = [
  ["motion", "Reduce motion", "Stops ambient animation; the story still works."],
  ["contrast", "High contrast", "Solid black, brighter text and borders."],
  ["text", "Larger text", "About a fifth larger everywhere."],
];

function readPrefs(): Prefs {
  if (typeof window === "undefined") return { motion: false, contrast: false, text: false };
  try {
    const saved = JSON.parse(localStorage.getItem(KEY) ?? "{}") as Partial<Prefs>;
    return { motion: !!saved.motion, contrast: !!saved.contrast, text: !!saved.text };
  } catch {
    return { motion: false, contrast: false, text: false }; // server render or storage unavailable
  }
}

function apply(p: Prefs) {
  const d = document.documentElement;
  if (p.motion) d.dataset.motion = "reduce";
  else delete d.dataset.motion;
  if (p.contrast) d.dataset.contrast = "high";
  else delete d.dataset.contrast;
  if (p.text) d.dataset.text = "large";
  else delete d.dataset.text;
  window.dispatchEvent(new CustomEvent("aurora-prefs", { detail: p }));
}

/** "Aurora adapts to the person": motion, contrast and text size, remembered on this device. */
export function A11yControl() {
  const [open, setOpen] = useState(false);
  const [prefs, setPrefs] = useState<Prefs>(readPrefs);
  const panelId = useId();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    const onClick = (e: MouseEvent) =>
      ref.current && !ref.current.contains(e.target as Node) && setOpen(false);
    document.addEventListener("keydown", onKey);
    document.addEventListener("mousedown", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("mousedown", onClick);
    };
  }, [open]);

  const toggle = (k: keyof Prefs) => {
    const next = { ...prefs, [k]: !prefs[k] };
    setPrefs(next);
    apply(next);
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* not persisted */
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        className="btn btn-ghost !min-h-10 !px-3"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((o) => !o)}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden>
          <circle cx="12" cy="4.5" r="2" fill="currentColor" />
          <path
            d="M4 8.5l8 1.5 8-1.5M12 10v5m0 0l-3.5 6M12 15l3.5 6"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
        <span className="sr-only sm:not-sr-only">Accessibility</span>
      </button>
      {open && (
        <div
          id={panelId}
          role="group"
          aria-label="Accessibility settings"
          className="card absolute right-0 z-50 mt-2 w-72 p-3 shadow-2xl"
        >
          {LABELS.map(([k, label, hint]) => (
            <label key={k} className="flex cursor-pointer items-start gap-3 rounded-lg p-2 hover:bg-white/5">
              <input
                type="checkbox"
                className="mt-1 size-4 accent-[var(--color-teal)]"
                checked={prefs[k]}
                onChange={() => toggle(k)}
              />
              <span>
                <span className="block text-sm font-semibold">{label}</span>
                <span className="block text-xs text-muted">{hint}</span>
              </span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

/** True when the OS or the in-app control asks for reduced motion (live). */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const read = () => setReduced(mq.matches || document.documentElement.dataset.motion === "reduce");
    read();
    mq.addEventListener("change", read);
    window.addEventListener("aurora-prefs", read);
    return () => {
      mq.removeEventListener("change", read);
      window.removeEventListener("aurora-prefs", read);
    };
  }, []);
  return reduced;
}
