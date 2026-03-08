export function AIImageRenderer({ src, alt }: { src: string; alt: string }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-cyan-100/20 bg-slate-900/60 p-2">
      <img src={src} alt={alt} className="w-full rounded-xl object-cover" loading="lazy" />
    </div>
  );
}
