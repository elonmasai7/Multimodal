export function VideoPlayer({ src }: { src: string }) {
  return <video className="w-full rounded-2xl border border-white/20" controls playsInline src={src} preload="metadata" />;
}
