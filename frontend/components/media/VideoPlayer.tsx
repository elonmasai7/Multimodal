"use client";

import { useRef, useEffect } from "react";

export function VideoPlayer({
  src,
  clips,
  onProgress,
}: {
  src: string;
  clips?: string[];
  onProgress?: (watchedSeconds: number, totalSeconds: number) => void;
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const indexRef = useRef(0);
  const lastReportRef = useRef(0);
  const playlist = clips && clips.length > 0 ? clips : [src];
  const playlistKey = playlist.join("|");

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    indexRef.current = 0;
    video.src = playlist[0];

    const handleEnded = () => {
      // Report full watch on end
      if (onProgress && video.duration) {
        onProgress(Math.round(video.currentTime), Math.round(video.duration));
      }
      const next = indexRef.current + 1;
      if (next < playlist.length) {
        indexRef.current = next;
        video.src = playlist[next];
        video.play().catch(() => {});
      }
    };

    const handleTimeUpdate = () => {
      if (!onProgress || !video.duration) return;
      const now = Math.round(video.currentTime);
      // Report every 10 seconds of watch time
      if (now - lastReportRef.current >= 10) {
        lastReportRef.current = now;
        onProgress(now, Math.round(video.duration));
      }
    };

    const handlePause = () => {
      if (onProgress && video.duration) {
        onProgress(Math.round(video.currentTime), Math.round(video.duration));
      }
    };

    video.addEventListener("ended", handleEnded);
    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("pause", handlePause);
    return () => {
      video.removeEventListener("ended", handleEnded);
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("pause", handlePause);
    };
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
