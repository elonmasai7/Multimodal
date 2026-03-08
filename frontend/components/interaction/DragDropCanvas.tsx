"use client";

import { useState } from "react";

const labels = ["CO2", "Stomata", "Chloroplast"];

export function DragDropCanvas() {
  const [drop, setDrop] = useState<string>("Drop label here");

  return (
    <div className="space-y-2 rounded-2xl border border-emerald-300/25 bg-emerald-500/10 p-3">
      <p className="text-sm text-emerald-100">Drag a label into the diagram target.</p>
      <div className="flex flex-wrap gap-2">
        {labels.map((item) => (
          <button
            key={item}
            draggable
            onDragStart={(e) => e.dataTransfer.setData("text/plain", item)}
            className="rounded-lg border border-emerald-200/40 px-3 py-1 text-xs text-emerald-50"
          >
            {item}
          </button>
        ))}
      </div>
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          setDrop(e.dataTransfer.getData("text/plain"));
        }}
        className="rounded-xl border border-dashed border-emerald-200/50 p-4 text-sm text-emerald-100"
      >
        {drop}
      </div>
    </div>
  );
}
