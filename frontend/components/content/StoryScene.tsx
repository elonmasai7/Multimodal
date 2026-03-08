import { motion } from "framer-motion";

import { Card } from "@/components/content/Card";

export function StoryScene({ title, narration }: { title: string; narration: string }) {
  return (
    <Card className="relative overflow-hidden">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="space-y-2"
      >
        <h3 className="text-xl font-semibold text-cyan-100">{title}</h3>
        <p className="text-slate-200">{narration}</p>
      </motion.div>
    </Card>
  );
}
