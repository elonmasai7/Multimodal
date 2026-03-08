"use client";

import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";

export function ClientProviders({ children }: { children: React.ReactNode }) {
  useReducedMotionPreference();
  return <>{children}</>;
}
