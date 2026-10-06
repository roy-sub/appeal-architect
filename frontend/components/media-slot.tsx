import { cn } from "@/lib/utils";

type Kind = "image" | "video" | "illustration" | "image strip";

type Props = {
  slotId: string;
  kind?: Kind;
  /** CSS aspect-ratio, e.g. "16 / 9". Ignored when `fill`. */
  ratio?: string;
  label: string;
  intrinsic: string;
  /** Background layer: absolute inset, no ratio, single corner caption. */
  fill?: boolean;
  className?: string;
};

const showIds = process.env.NODE_ENV !== "production" || process.env.NEXT_PUBLIC_SHOW_SLOTS === "1";

// Reserved media location (brief §5). Three modes, derived from the ratio:
// roomy (default), tight (≥5:1, one inline label) and fill (background layer).
// Slot ids and intrinsic sizes show in dev only.
export function MediaSlot({ slotId, kind = "image", ratio = "16 / 9", label, intrinsic, fill, className }: Props) {
  if (fill) {
    return (
      // Fill slots sit behind type and are decorative: alt="" / aria-hidden (media-manifest.md).
      <div data-slot={slotId} className={cn("absolute inset-0 overflow-hidden bg-surface-sunk", className)} aria-hidden>
        <div className="absolute inset-0 opacity-40" style={{ backgroundImage: "repeating-linear-gradient(45deg, transparent 0 9px, var(--stripe) 9px 10px)" }} />
        {showIds && (
          <div className="absolute bottom-3 left-3.5 flex items-center gap-2 font-mono text-[11px] leading-[14px] uppercase tracking-[.06em] text-ink-muted opacity-75">
            <span className="size-1.5 bg-ink-muted" />
            <span>{slotId}</span>·<span>{kind}</span>·<span>{intrinsic}</span>
          </div>
        )}
      </div>
    );
  }
  const [w, h] = ratio.split("/").map((n) => parseFloat(n) || 1);
  const tight = w / h >= 5;
  return (
    <div
      data-slot={slotId}
      role="img"
      aria-label={label}
      className={cn("relative flex w-full items-center justify-center overflow-hidden rounded-[10px] border border-rule bg-surface-sunk p-5", className)}
      style={{ aspectRatio: ratio }}
    >
      <div className="absolute inset-0 opacity-55" style={{ backgroundImage: "repeating-linear-gradient(45deg, transparent 0 7px, var(--stripe) 7px 8px)" }} />
      {tight ? (
        <div className="relative flex min-w-0 items-center gap-2 px-2">
          <span className="size-1.5 shrink-0 bg-ink-muted opacity-50" />
          <span className="truncate font-mono text-[11px] leading-[14px] uppercase tracking-[.06em] text-ink-muted">{label}</span>
        </div>
      ) : (
        <>
          <div className="relative flex max-w-[320px] flex-col items-center gap-1.5 text-center">
            <div className="rounded-[2px] border border-rule bg-surface px-[7px] py-0.5 font-mono text-[11px] leading-4 uppercase tracking-[.06em] text-ink-muted">{kind}</div>
            <div className="font-mono text-[12px] leading-[18px] text-ink-muted">{label}</div>
          </div>
          {showIds && (
            <>
              <div className="absolute bottom-[9px] left-2.5 font-mono text-[11px] leading-[14px] text-ink-muted opacity-80">{slotId}</div>
              <div className="absolute bottom-[9px] right-2.5 font-mono text-[11px] leading-[14px] text-ink-muted opacity-80">{intrinsic}</div>
            </>
          )}
        </>
      )}
    </div>
  );
}
