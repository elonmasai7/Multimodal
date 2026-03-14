"use client";

import { useState } from "react";

type Platform = "whatsapp" | "x" | "instagram" | "tiktok";

const platforms: { id: Platform; label: string; bg: string; fg: string; icon: React.ReactNode }[] = [
  {
    id: "whatsapp",
    label: "WhatsApp",
    bg: "bg-[#25D366]/15 hover:bg-[#25D366]/25 border-[#25D366]/30",
    fg: "text-[#25D366]",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
      </svg>
    ),
  },
  {
    id: "x",
    label: "X",
    bg: "bg-white/5 hover:bg-white/10 border-white/20",
    fg: "text-white",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.746l7.73-8.835L1.254 2.25H8.08l4.259 5.629 5.905-5.629zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
      </svg>
    ),
  },
  {
    id: "instagram",
    label: "Instagram",
    bg: "bg-[#E1306C]/10 hover:bg-[#E1306C]/20 border-[#E1306C]/30",
    fg: "text-[#E1306C]",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" />
      </svg>
    ),
  },
  {
    id: "tiktok",
    label: "TikTok",
    bg: "bg-[#ff0050]/10 hover:bg-[#ff0050]/20 border-[#ff0050]/30",
    fg: "text-[#ff0050]",
    icon: (
      <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
        <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 00-.79-.05 6.34 6.34 0 00-6.34 6.34 6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.33-6.34V8.69a8.18 8.18 0 004.78 1.52V6.74a4.85 4.85 0 01-1.01-.05z" />
      </svg>
    ),
  },
];

function buildShareUrl(platform: Platform, pageUrl: string, title: string): string | null {
  const text = `Check out this story: ${title}`;
  const encoded = encodeURIComponent(pageUrl);
  const encodedText = encodeURIComponent(text);

  if (platform === "whatsapp") return `https://wa.me/?text=${encodedText}%20${encoded}`;
  if (platform === "x") return `https://twitter.com/intent/tweet?text=${encodedText}&url=${encoded}`;
  return null; // Instagram & TikTok: handled via Web Share API / clipboard
}

export function SharePanel({ storyUrl, title, videoUrl }: { storyUrl: string; title?: string; videoUrl?: string | null }) {
  const [copied, setCopied] = useState(false);
  const displayTitle = title ?? "My Msomi Story";
  const shareText = `Check out this story: ${displayTitle}`;

  async function handlePlatform(platform: Platform) {
    const url = buildShareUrl(platform, storyUrl, displayTitle);

    if (url) {
      window.open(url, "_blank", "noopener,noreferrer");
      return;
    }

    // Instagram / TikTok — use Web Share API on mobile, copy link on desktop
    if (typeof navigator !== "undefined" && "share" in navigator) {
      try {
        await navigator.share({ title: displayTitle, text: shareText, url: storyUrl });
        return;
      } catch {
        // user cancelled or share failed — fall through to copy
      }
    }

    // Fallback: copy story link to clipboard
    await navigator.clipboard.writeText(storyUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  }

  async function copyLink() {
    await navigator.clipboard.writeText(storyUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-white/10" />
        <h3 className="text-xs font-semibold uppercase tracking-widest text-slate-400">Share</h3>
        <div className="h-px flex-1 bg-white/10" />
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/3 p-4">
        {videoUrl && (
          <p className="mb-3 text-xs text-slate-400">
            Share your story book or copy the video link to post on Instagram / TikTok.
          </p>
        )}

        <div className="flex flex-wrap gap-2">
          {platforms.map((p) => (
            <button
              key={p.id}
              onClick={() => handlePlatform(p.id)}
              className={`flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-medium transition-all ${p.bg} ${p.fg}`}
              title={
                p.id === "instagram" || p.id === "tiktok"
                  ? "Opens native share or copies link"
                  : `Share on ${p.label}`
              }
            >
              {p.icon}
              {p.label}
            </button>
          ))}

          <button
            onClick={copyLink}
            className="flex items-center gap-1.5 rounded-xl border border-white/20 bg-white/5 px-3 py-2 text-xs font-medium text-slate-300 transition-all hover:bg-white/10"
          >
            {copied ? (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} className="h-4 w-4 text-emerald-400">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-emerald-400">Copied!</span>
              </>
            ) : (
              <>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-4 w-4">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                  <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
                </svg>
                Copy link
              </>
            )}
          </button>
        </div>

        {(platforms.some((p) => p.id === "instagram" || p.id === "tiktok")) && videoUrl && (
          <button
            onClick={async () => {
              await navigator.clipboard.writeText(videoUrl);
              setCopied(true);
              setTimeout(() => setCopied(false), 2500);
            }}
            className="mt-2 text-xs text-slate-500 underline-offset-2 hover:text-slate-300 hover:underline transition-colors"
          >
            Copy video URL for Instagram / TikTok upload
          </button>
        )}
      </div>
    </div>
  );
}
