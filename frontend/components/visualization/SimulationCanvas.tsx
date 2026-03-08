"use client";

import { useState } from "react";

import { InteractiveSlider } from "@/components/interaction/InteractiveSlider";

export function SimulationCanvas() {
  const [speed, setSpeed] = useState(40);

  return (
    <div className="rounded-2xl border border-cyan-200/20 bg-cyan-500/10 p-4">
      <p className="mb-2 text-sm text-cyan-100">Simulation speed control</p>
      <InteractiveSlider label="Velocity" value={speed} onChange={setSpeed} />
      <div className="mt-3 h-2 rounded-full bg-slate-900/80">
        <div className="h-2 rounded-full bg-cyan-300" style={{ width: `${speed}%` }} />
      </div>
    </div>
  );
}
