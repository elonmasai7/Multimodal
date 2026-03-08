"use client";

import { useState } from "react";

import { CellStructureScene } from "@/3d-scenes/CellStructureScene";
import { DiagramPanel } from "@/components/content/DiagramPanel";
import { LessonSection } from "@/components/content/LessonSection";
import { DragDropCanvas } from "@/components/interaction/DragDropCanvas";
import { SimulationCanvas } from "@/components/visualization/SimulationCanvas";
import { Navbar } from "@/components/layout/Navbar";
import { PageContainer } from "@/components/layout/PageContainer";
import { Sidebar } from "@/components/layout/Sidebar";
import { LearningCanvas } from "@/components/canvas/LearningCanvas";
import { StreamControlPanel } from "@/components/StreamControlPanel";
import { StreamingRenderer } from "@/components/StreamingRenderer";
import { Toast } from "@/components/feedback/Toast";

export default function LessonPage() {
  const [toast, setToast] = useState("Ready for a live lesson");

  return (
    <PageContainer className="pb-28">
      <div data-theme="lesson">
        <Navbar />
        <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
          <LearningCanvas>
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-4">
                <LessonSection
                  heading="Photosynthesis Documentary"
                  text="Observe chloroplast dynamics through interactive diagrams and guided narration."
                />
                <DiagramPanel src="https://placehold.co/800x500/062b45/7dd3fc?text=Chloroplast+Diagram" caption="AI-enhanced chloroplast map" />
                <DragDropCanvas />
                <SimulationCanvas />
              </div>
              <div className="space-y-4">
                <CellStructureScene />
                <Toast message={toast} />
                <button
                  onClick={() => setToast("Excellent. Your model of light reactions improved by 18%")}
                  className="rounded-xl bg-emerald-400 px-3 py-2 text-sm font-semibold text-slate-950"
                >
                  Trigger Learning Feedback
                </button>
              </div>
            </div>
          </LearningCanvas>

          <Sidebar title="Live Lesson Stream">
            <div className="space-y-3">
              <StreamControlPanel kind="lesson" />
              <StreamingRenderer />
            </div>
          </Sidebar>
        </div>
      </div>
    </PageContainer>
  );
}
