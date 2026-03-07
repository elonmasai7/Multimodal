import Link from "next/link";

const links = [
  { href: "/dashboard", label: "Student Dashboard" },
  { href: "/story", label: "Story Player" },
  { href: "/lesson", label: "Lesson Viewer" },
  { href: "/teacher", label: "Teacher Dashboard" }
];

export default function HomePage() {
  return (
    <main className="space-y-6">
      <h1 className="text-4xl font-bold">Multimodal AI Learning Platform</h1>
      <p className="max-w-3xl text-slate-700">
        Generate interactive storybooks, visual lessons, quizzes, and narrated explainers using a unified multimodal streaming pipeline.
      </p>
      <div className="grid gap-3 md:grid-cols-2">
        {links.map((link) => (
          <Link key={link.href} href={link.href} className="rounded border border-slate-200 bg-white p-4 hover:border-sky-400">
            {link.label}
          </Link>
        ))}
      </div>
    </main>
  );
}
