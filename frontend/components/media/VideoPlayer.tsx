"use client";

import { useRef, useEffect } from "react";

export function VideoPlayer({ src, clips }: { src: string; clips?: string[] }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const indexRef = useRef(0);
  const playlist = clips && clips.length > 0 ? clips : [src];
  const playlistKey = playlist.join("|");

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    indexRef.current = 0;
    video.src = playlist[0];

    if (playlist.length === 1) return;

    const handleEnded = () => {
      const next = indexRef.current + 1;
      if (next < playlist.length) {
        indexRef.current = next;
        video.src = playlist[next];
        video.play().catch(() => {});
      }
    };

    video.addEventListener("ended", handleEnded);
    return () => video.removeEventListener("ended", handleEnded);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playlistKey]);

  return (
    <div className="space-y-1">
      <video
        ref={videoRef}
        className="w-full rounded-2xl border border-white/20"
        controls
        playsInline
        preload="metadata"
      />
      {playlist.length > 1 && (
        <p className="text-xs text-slate-400 text-right">{playlist.length} clips · {playlist.length * 8}s total</p>
      )}
    </div>
  );
}
