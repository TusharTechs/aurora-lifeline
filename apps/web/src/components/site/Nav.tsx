"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Logo } from "@/components/brand/Logo";
import { A11yControl } from "./A11yControl";

const LINKS: Array<[string, string]> = [
  ["/#how", "How it works"],
  ["/#try", "Try it"],
  ["/#trust", "Why trust it"],
  ["/bulletin/", "Bulletin reader"],
  ["/proof/", "Proof"],
];

export function Nav({ controlRoomHref }: { controlRoomHref: string }) {
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 8);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);
  return (
    <header
      className={`sticky top-0 z-40 transition-[background-color,border-color] duration-300 ${
        scrolled ? "border-b border-border bg-bg/80 backdrop-blur-xl" : "border-b border-transparent"
      }`}
    >
      <nav aria-label="Main" className="mx-auto flex h-16 max-w-7xl items-center gap-4 px-4 sm:px-6">
        <Link href="/" aria-label="AURORA Lifeline home" className="flex shrink-0 items-center">
          <Logo />
        </Link>
        <ul className="ml-6 hidden items-center gap-1 lg:flex">
          {LINKS.map(([href, label]) => (
            <li key={href}>
              <Link
                href={href}
                className="rounded-full px-3 py-2 text-sm text-muted transition-colors hover:text-fg"
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>
        <div className="ml-auto flex items-center gap-2">
          <A11yControl />
          <Link
            href={controlRoomHref}
            className="btn btn-primary hidden !min-h-10 !py-2 text-sm sm:inline-flex"
          >
            Open control room
          </Link>
          <button
            type="button"
            className="btn btn-ghost !min-h-10 !px-3 lg:hidden"
            aria-expanded={open}
            aria-controls="mobile-menu"
            onClick={() => setOpen((o) => !o)}
          >
            <span className="sr-only">Menu</span>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              aria-hidden
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            >
              {open ? <path d="M6 6l12 12M18 6L6 18" /> : <path d="M4 7h16M4 12h16M4 17h16" />}
            </svg>
          </button>
        </div>
      </nav>
      {open && (
        <ul
          id="mobile-menu"
          className="border-t border-border bg-bg/95 px-4 pb-4 pt-2 backdrop-blur-xl lg:hidden"
        >
          {[...LINKS, [controlRoomHref, "Open control room"] as [string, string]].map(([href, label]) => (
            <li key={href}>
              <Link
                href={href}
                onClick={() => setOpen(false)}
                className="block rounded-lg px-3 py-3 text-base hover:bg-white/5"
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </header>
  );
}
