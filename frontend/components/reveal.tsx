"use client";
import { motion, useReducedMotion } from "motion/react";
import { gestures, type GestureName } from "@/lib/motion";

type Props = {
  gesture: GestureName;
  delay?: number;
  /** "view" plays once when scrolled into view; "load" plays on mount (above the fold). */
  trigger?: "view" | "load";
  as?: "div" | "span" | "h2" | "p";
  duration?: number;
  /**
   * For gestures that start fully clipped or translated out of an overflow-hidden
   * parent: the in-view trigger moves to this wrapper (an element that is visible),
   * because IntersectionObserver never reports a fully clipped element.
   */
  wrapClassName?: string;
  /** Render the end state immediately (e.g. a "Show it all" skip, or a sequence already played). */
  instant?: boolean;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
};

export function Reveal({ gesture, delay = 0, trigger = "view", as = "div", duration, wrapClassName, instant, className, style, children }: Props) {
  const reduce = useReducedMotion() || instant;
  const g = gestures[gesture];
  const Comp = motion[as];
  // Reduced motion: no entrance at all — content is simply there.
  const play =
    trigger === "load" || reduce
      ? { initial: reduce ? (false as const) : "hidden", animate: "shown" }
      : { initial: "hidden", whileInView: "shown", viewport: { once: true, amount: 0.25 } };
  const transition = reduce ? { duration: 0 } : { ...g.transition, ...(duration ? { duration } : {}), delay };

  if (wrapClassName !== undefined) {
    return (
      <motion.div className={wrapClassName} {...play}>
        <Comp className={className} style={style} variants={g.variants} transition={transition}>
          {children}
        </Comp>
      </motion.div>
    );
  }
  return (
    <Comp className={className} style={style} variants={g.variants} transition={transition} {...play}>
      {children}
    </Comp>
  );
}
