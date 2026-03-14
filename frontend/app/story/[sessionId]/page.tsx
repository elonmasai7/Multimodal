"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { StoryBook, StaticBookPage } from "@/components/content/StoryBook";
import { SharePanel } from "@/components/content/SharePanel";
import { getStoryPages } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export default function SavedStoryPage() {
  const { sessionId } = useParams();
  const token = useAuthStore((s) => s.token);
  const [pages, setPages] = useState<StaticBookPage[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const storyUrl = typeof window !== "undefined" ? window.location.href : "";

  useEffect(() => {
    if (!token || !sessionId) return;
    getStoryPages(token, String(sessionId))
      .then((res) => setPages(Array.isArray(res.data) ? res.data : []))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load story"))
      .finally(() => setLoading(false));
  }, [token, sessionId]);

  return (
    <PageContainer className="pb-24">
      <Navbar />
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="text-xs text-slate-400 hover:text-slate-200 transition-colors"
          >
            ← Back to dashboard
          </Link>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-20 text-sm text-slate-400">
            Loading your story…
          </div>
        )}

        {error && (
          <p className="text-sm text-red-300">{error}</p>
        )}

        {!loading && !error && pages !== null && pages.length === 0 && (
          <div className="rounded-3xl border border-white/15 bg-white/5 p-8 text-center">
            <p className="text-sm text-slate-400">
              This story has no saved pages yet. The book is built when a story stream completes.
            </p>
            <Link
              href={`/story`}
              className="mt-4 inline-block rounded-xl bg-violet-500/20 px-4 py-2 text-sm text-violet-300 hover:bg-violet-500/30 transition-colors"
            >
              Start a new story
            </Link>
          </div>
        )}

        {!loading && pages && pages.length > 0 && (
          <div className="mx-auto max-w-4xl space-y-6">
            <StoryBook pages={pages} />
            <SharePanel storyUrl={storyUrl} title="My Msomi Story" />
          </div>
        )}
      </div>
    </PageContainer>
  );
}
