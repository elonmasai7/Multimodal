"use client";

import { useEffect } from "react";

import { useLearningStore } from "@/store/learningStore";

export function useReducedMotionPreference() {
  const setReducedMotion = useLearningStore((s) => s.setReducedMotion);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setReducedMotion(mediaQuery.matches);
    apply();
    mediaQuery.addEventListener("change", apply);
    return () => mediaQuery.removeEventListener("change", apply);
  }, [setReducedMotion]);
}
