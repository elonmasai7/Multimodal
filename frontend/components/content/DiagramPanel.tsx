export function DiagramPanel({ src, caption }: { src: string; caption: string }) {
  return (
    <figure className="overflow-hidden rounded-2xl border border-white/20 bg-slate-950/50 p-2">
      <img src={src} alt={caption} className="max-h-[320px] w-full rounded-xl object-cover" />
      <figcaption className="mt-2 text-xs text-slate-300">{caption}</figcaption>
    </figure>
  );
}
