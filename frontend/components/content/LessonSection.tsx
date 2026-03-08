import { Card } from "@/components/content/Card";

export function LessonSection({ heading, text }: { heading: string; text: string }) {
  return (
    <Card>
      <h3 className="mb-2 text-lg font-semibold text-emerald-100">{heading}</h3>
      <p className="text-slate-200">{text}</p>
    </Card>
  );
}
