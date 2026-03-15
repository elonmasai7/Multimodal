"use client";

import Link from "next/link";

import { AuthPanel } from "@/components/forms/AuthPanel";
import { useLearningStore } from "@/store/learningStore";

const navLinks = [
  { href: "/", label: "World" },
  { href: "/story", label: "Story" },
  { href: "/lesson", label: "Lesson" },
  { href: "/dashboard", label: "Student" },
  { href: "/teacher", label: "Teacher" }
];

export function Navbar() {
  const audioEnabled = useLearningStore((s) => s.audioEnabled);
  const setAudioEnabled = useLearningStore((s) => s.setAudioEnabled);

  return (
    <header className="sticky top-0 z-40 mb-6 rounded-2xl border border-white/15 bg-slate-950/70 p-3 backdrop-blur-xl">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <Link href="/" className="flex items-center gap-2">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/msomi-book.png" alt="Msomi" className="h-16 w-16 object-contain" />
          <span className="text-lg font-bold tracking-wide text-cyan-200">Msomi</span>
        </Link>
        <nav className="flex flex-wrap items-center gap-2">
          {navLinks.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-xl border border-transparent px-3 py-1.5 text-sm text-slate-200 transition hover:border-cyan-300/50 hover:bg-cyan-400/10"
            >
              {item.label}
            </Link>
          ))}
          <button
            onClick={() => setAudioEnabled(!audioEnabled)}
            className="rounded-xl border border-cyan-200/40 px-3 py-1.5 text-sm text-cyan-100"
            aria-label="Toggle audio"
          >
            Audio: {audioEnabled ? "On" : "Off"}
          </button>
        </nav>
        <div className="w-full md:w-72">
          <AuthPanel />
        </div>
      </div>
    </header>
  );
}
