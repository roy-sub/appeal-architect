import { tone } from "@/lib/time";

// Static ring: fills as the window is used up. Never animated continuously.
export function DeadlineRing({ days, total, size }: { days: number; total: number; size: number }) {
  const t = tone(days);
  const passed = days < 0;
  const pct = passed ? 1 : Math.max(0.04, Math.min(1, 1 - days / total));
  return (
    <div
      className="relative shrink-0 rounded-full"
      style={{ width: size, height: size, background: `conic-gradient(${t.color} ${pct * 360}deg, var(--time-track) 0)` }}
      role="img"
      aria-label={passed ? `Deadline passed, ${t.word}` : `${days} days remaining, ${t.word}`}
    >
      <div className="absolute inset-1 flex flex-col items-center justify-center gap-px rounded-full bg-surface">
        <span className="tabular leading-none" style={{ fontSize: size > 70 ? 22 : 17, fontWeight: t.weight, color: t.color }}>{passed ? "0" : days}</span>
        <span className="font-mono text-[9px] tracking-[.06em] text-ink-muted">DAYS</span>
      </div>
    </div>
  );
}
