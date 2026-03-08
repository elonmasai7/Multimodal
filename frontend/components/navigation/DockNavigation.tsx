"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/utils/cn";

const items = [
  { href: "/story", label: "Story" },
  { href: "/lesson", label: "Lesson" },
  { href: "/dashboard", label: "Progress" }
];

export function DockNavigation() {
  const pathname = usePathname();

  return (
    <div className="fixed bottom-5 left-1/2 z-50 -translate-x-1/2 rounded-2xl border border-white/20 bg-slate-950/80 p-2 backdrop-blur-lg">
      <nav className="flex gap-2" aria-label="Primary">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "rounded-xl px-4 py-2 text-sm text-slate-200 transition",
              pathname.startsWith(item.href) ? "bg-cyan-500/30 text-cyan-100" : "hover:bg-white/10"
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
