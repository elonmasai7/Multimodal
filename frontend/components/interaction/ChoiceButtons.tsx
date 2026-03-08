"use client";

import { motion } from "framer-motion";

export function ChoiceButtons({ choices, onPick }: { choices: string[]; onPick: (choice: string) => void }) {
  return (
    <div className="grid gap-2 md:grid-cols-2">
      {choices.map((choice) => (
        <motion.button
          whileHover={{ y: -3, scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          key={choice}
          onClick={() => onPick(choice)}
          className="rounded-xl border border-cyan-300/30 bg-cyan-500/10 px-4 py-3 text-left text-sm text-cyan-50"
        >
          {choice}
        </motion.button>
      ))}
    </div>
  );
}
