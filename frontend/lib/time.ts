// Urgency by proximity, never alarm. No hue at all above 60 days.
// Thresholds and words: design-handoff/project/components.md § DeadlineRing.
export type Tone = { color: string; weight: 500 | 600; word: string };

export function tone(days: number): Tone {
  if (days < 0) return { color: "var(--defeated)", weight: 600, word: "window closed — see options" };
  if (days > 60) return { color: "var(--time-ample)", weight: 500, word: "on track" };
  if (days > 14) return { color: "var(--time-approaching)", weight: 500, word: "approaching" };
  if (days > 3) return { color: "var(--time-near)", weight: 600, word: "close" };
  return { color: "var(--time-imminent)", weight: 600, word: "act now" };
}
