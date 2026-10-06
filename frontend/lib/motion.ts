import type { Transition, Variants } from "motion/react";

export const ease = {
  enter: [0.16, 0.84, 0.32, 1] as const,
  move: [0.65, 0, 0.35, 1] as const,
  expo: [0.19, 1, 0.22, 1] as const,
  exit: [0.4, 0, 1, 1] as const,
};

// Durations, seconds (motion.md § Tokens).
export const dur = { 1: 0.12, 2: 0.18, 3: 0.26, 4: 0.42, 5: 0.7 } as const;

type Gesture = { variants: Variants; transition: Transition };

// One gesture per landing section; none is reused across sections.
// Names match the keyframes in the design prototype (aa-*).
export const gestures = {
  // hero / closing call — line lifts out of its clip
  lineup: { variants: { hidden: { y: "104%" }, shown: { y: 0 } }, transition: { duration: 0.86, ease: ease.expo } },
  // hero copy, step bodies
  lift: { variants: { hidden: { opacity: 0, y: 26 }, shown: { opacity: 1, y: 0 } }, transition: { duration: 0.76, ease: ease.enter } },
  // workspace: case cards, letter paragraphs (y 8 → 0)
  riseSm: { variants: { hidden: { opacity: 0, y: 8 }, shown: { opacity: 1, y: 0 } }, transition: { duration: 0.42, ease: ease.enter } },
  // triage verdict cards
  unfold: { variants: { hidden: { opacity: 0, scale: 0.98 }, shown: { opacity: 1, scale: 1 } }, transition: { duration: 0.42, ease: ease.enter } },
  fade: { variants: { hidden: { opacity: 0 }, shown: { opacity: 1 } }, transition: { duration: 0.18, ease: ease.enter } },
  // argument graph: claim card arrives first and is held alone
  claim: { variants: { hidden: { opacity: 0, y: 12 }, shown: { opacity: 1, y: 0 } }, transition: { duration: 0.42, ease: ease.enter } },
  rise: { variants: { hidden: { opacity: 0, y: 10 }, shown: { opacity: 1, y: 0 } }, transition: { duration: 0.42, ease: ease.enter } },
  // stats — rule draws, numerals count up from their baseline
  drawRight: { variants: { hidden: { scaleX: 0 }, shown: { scaleX: 1 } }, transition: { duration: 0.82, ease: ease.move } },
  drawDown: { variants: { hidden: { scaleY: 0 }, shown: { scaleY: 1 } }, transition: { duration: 0.7, ease: ease.move } },
  countUp: { variants: { hidden: { opacity: 0, y: "42%" }, shown: { opacity: 1, y: 0 } }, transition: { duration: 0.78, ease: ease.enter } },
  // process — station dots
  dot: { variants: { hidden: { scale: 0 }, shown: { scale: 1 } }, transition: { duration: 0.42, ease: ease.enter } },
  // capabilities — media wipes right, note nudges in
  wipeRight: { variants: { hidden: { clipPath: "inset(0 100% 0 0)" }, shown: { clipPath: "inset(0 0% 0 0)" } }, transition: { duration: 0.88, ease: ease.move } },
  nudge: { variants: { hidden: { opacity: 0, x: -18 }, shown: { opacity: 1, x: 0 } }, transition: { duration: 0.64, ease: ease.enter } },
} satisfies Record<string, Gesture>;

export type GestureName = keyof typeof gestures;
