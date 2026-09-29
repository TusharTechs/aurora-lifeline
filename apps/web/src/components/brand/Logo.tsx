import { useId } from "react";

/**
 * The AURORA Lifeline mark: three bands of aurora light (violet, cyan, teal) spiral clockwise out
 * of a warm, calm core, as a Northern Hemisphere cyclone's rain bands do. The storm is drawn as
 * light; the core is the place whose lifeline must hold. 48-unit grid; legible down to 16 px.
 */
export const MARK_ARM = "M31 24C35.2 18.1 20.9-0.8 6.7 14";
export const MARK_ROTATIONS = [0, 120, 240] as const;
const ARM_COLORS = ["var(--color-violet)", "var(--color-cyan)", "var(--color-teal)"];

type MarkProps = {
  size?: number;
  mono?: boolean;
  title?: string;
  className?: string;
  animated?: boolean;
};

export function AuroraMark({ size = 32, mono = false, title, className, animated = false }: MarkProps) {
  const id = useId().replace(/:/g, "");
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      className={className}
      role={title ? "img" : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      {title && <title>{title}</title>}
      {!mono && (
        <defs>
          {ARM_COLORS.map((c, i) => (
            <linearGradient
              key={c}
              id={`${id}-a${i}`}
              x1="31"
              y1="0"
              x2="6"
              y2="0"
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0" stopColor={c} />
              <stop offset="0.6" stopColor={c} stopOpacity="0.8" />
              <stop offset="1" stopColor={c} stopOpacity="0.12" />
            </linearGradient>
          ))}
          <radialGradient id={`${id}-c`}>
            <stop offset="0" stopColor="#fffaf0" />
            <stop offset="1" stopColor="var(--color-dawn)" />
          </radialGradient>
        </defs>
      )}
      {/* Outer group turns (about the core); the inner group mirrors the arms. Kept separate so the
          rotation origin does not shift the mirror. */}
      <g className={animated ? "aurora-arms aurora-spin" : "aurora-arms"}>
        <g transform="matrix(-1 0 0 1 48 0)" strokeLinecap="round" strokeWidth="4.2">
          {MARK_ROTATIONS.map((rot, i) => (
            <path
              key={rot}
              d={MARK_ARM}
              stroke={mono ? "currentColor" : `url(#${id}-a${i})`}
              transform={`rotate(${rot} 24 24)`}
            />
          ))}
        </g>
      </g>
      <circle
        className="aurora-core"
        cx="24"
        cy="24"
        r="4.4"
        fill={mono ? "currentColor" : `url(#${id}-c)`}
      />
    </svg>
  );
}

export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span className={`font-display leading-none ${className}`}>
      <span className="font-semibold tracking-[0.14em]">AURORA</span>
      <span className="ml-1.5 font-light tracking-[0.04em] text-muted">Lifeline</span>
    </span>
  );
}

export function Logo({ size = 30, className = "" }: { size?: number; className?: string }) {
  return (
    <span className={`aurora-logo inline-flex items-center gap-2.5 ${className}`}>
      <AuroraMark size={size} />
      <Wordmark className="text-[1.05rem]" />
    </span>
  );
}

/** Loading state: the mark turns slowly, as a storm does, until content is ready. */
export function AuroraLoader({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" aria-live="polite" className="flex flex-col items-center gap-3 text-muted">
      <AuroraMark size={56} animated />
      <span className="text-sm">{label}…</span>
    </div>
  );
}
