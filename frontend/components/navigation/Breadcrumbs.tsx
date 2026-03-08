import Link from "next/link";

export function Breadcrumbs({ items }: { items: Array<{ href: string; label: string }> }) {
  return (
    <nav aria-label="breadcrumbs" className="mb-3 flex items-center gap-2 text-xs text-slate-300">
      {items.map((item, idx) => (
        <div key={item.href} className="flex items-center gap-2">
          {idx > 0 && <span>/</span>}
          <Link href={item.href} className="hover:text-cyan-200">
            {item.label}
          </Link>
        </div>
      ))}
    </nav>
  );
}
