"use client";
import { MotionConfig } from "motion/react";

// prefers-reduced-motion collapses every transition to an instant state change.
export function MotionProvider({ children }: { children: React.ReactNode }) {
  return <MotionConfig reducedMotion="user">{children}</MotionConfig>;
}
