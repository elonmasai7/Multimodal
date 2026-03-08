"use client";

import { useReducedMotionPreference } from "@/hooks/useReducedMotionPreference";
import { useBootstrapAuth } from "@/hooks/useBootstrapAuth";

export function ClientProviders({ children }: { children: React.ReactNode }) {
  useReducedMotionPreference();
  useBootstrapAuth();
  return <>{children}</>;
}
