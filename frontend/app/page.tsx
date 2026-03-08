import Link from "next/link";

import { PageContainer } from "@/components/layout/PageContainer";
import { Navbar } from "@/components/layout/Navbar";
import { LearningStats } from "@/components/analytics/LearningStats";

const stats = [
  { label: "Active learners", value: "12.4k" },
  { label: "Live sessions", value: "312" },
  { label: "Avg completion", value: "86%" },
  { label: "AI interactions", value: "1.2M" }
];

export default function HomePage() {
  return (
    <PageContainer className="pb-24">
      <Navbar />
      <section className="relative overflow-hidden rounded-[30px] border border-white/15 bg-white/5 p-8 shadow-glow md:p-12">
        <div className="pointer-events-none absolute -right-16 -top-16 h-48 w-48 rounded-full bg-cyan-400/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-20 left-0 h-56 w-56 rounded-full bg-orange-400/20 blur-3xl" />
        <p className="mb-3 text-xs uppercase tracking-[0.16em] text-cyan-200">Interactive Multimodal Learning</p>
        <h1 className="max-w-4xl text-5xl font-bold leading-[1.05] md:text-7xl">Step into an AI-powered learning world.</h1>
        <p className="mt-4 max-w-2xl text-base text-slate-200 md:text-lg">
          Cinematic storybooks, documentary-style explainers, tactile quizzes, and live generated visuals streamed in real time.
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link href="/story" className="rounded-xl bg-cyan-400 px-4 py-2 font-semibold text-slate-950">
            Enter Story Mode
          </Link>
          <Link href="/lesson" className="rounded-xl border border-white/30 px-4 py-2 font-semibold text-slate-100">
            Start Lesson Mode
          </Link>
        </div>
      </section>

      <section className="mt-8">
        <LearningStats stats={stats} />
      </section>
    </PageContainer>
  );
}
