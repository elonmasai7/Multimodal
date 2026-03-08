export function DiagramRenderer({ src }: { src: string }) {
  return (
    <div className="rounded-2xl border border-fuchsia-200/20 bg-fuchsia-500/10 p-2">
      <img src={src} alt="Generated diagram" className="w-full rounded-xl object-cover" loading="lazy" />
    </div>
  );
}
