"use client";

/**
 * The argument card, in all four states.
 *
 * Colour never carries meaning alone. Each tier is distinguished by **four**
 * signals -- border weight, border style, marker glyph and fill -- of which
 * colour is one. Printed greyscale, or read with any form of colour blindness,
 * the tiers remain distinct.
 */

import { cn } from "@/lib/utils";

export type Tier = "insurer" | "solid" | "add" | "out";

export const TIER_MARKER: Record<Tier, string> = {
  insurer: "\u25a0",
  solid: "\u25cf",
  add: "\u25c7",
  out: "\u2715",
};

export const TIER_CLASS: Record<Tier, string> = {
  insurer: "border-[1.5px] border-solid border-ink rounded-[2px] bg-surface",
  solid:
    "border-[1.5px] border-solid border-standing border-l-[3px] border-l-standing rounded-[10px] bg-surface",
  add: "border-[1.5px] border-dashed border-ink-muted rounded-[10px] bg-surface",
  out: "border border-solid border-defeated rounded-[10px] hatch",
};

export const TIER_TITLE_CLASS: Record<Tier, string> = {
  insurer: "text-ink",
  solid: "text-ink",
  add: "text-ink",
  out: "text-defeated line-through",
};

export const TIER_LABEL: Record<Tier, string> = {
  insurer: "Their reason",
  solid: "Solid ground",
  add: "Worth adding",
  out: "Left out",
};

export function ArgumentCard({
  tier,
  reference,
  title,
  assertion,
  active,
  pulsing,
  needs,
  onSelect,
  compact,
}: {
  tier: Tier;
  reference: string;
  title: string;
  assertion?: string;
  active?: boolean;
  pulsing?: boolean;
  needs?: string | null;
  onSelect?: () => void;
  compact?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className={cn(
        "w-full text-left transition-shadow",
        TIER_CLASS[tier],
        compact ? "px-3.5 py-3" : "px-4 py-3.5",
        active && "shadow-[0_0_0_2px_var(--focus)]",
        pulsing && "animate-[nodePulse_700ms_ease-out_1]",
      )}
    >
      <span className="flex items-center gap-2">
        <span
          className={cn(
            "font-mono text-[12px] leading-none",
            tier === "solid"
              ? "text-standing"
              : tier === "out"
                ? "text-defeated"
                : "text-ink-muted",
          )}
          aria-hidden
        >
          {TIER_MARKER[tier]}
        </span>
        <span className="font-mono text-[11px] tracking-[.05em] text-ink-muted">
          {reference}
        </span>
      </span>
      <span
        className={cn(
          "mt-1.5 block text-[16px] leading-[23px] font-semibold",
          TIER_TITLE_CLASS[tier],
        )}
      >
        {title}
      </span>
      {assertion && !compact ? (
        <span className="mt-1.5 block text-pretty text-[14px] leading-[21px] text-ink-muted">
          {assertion}
        </span>
      ) : null}
      {needs ? (
        <span className="mt-2 block border-t border-rule pt-2 text-[13px] leading-[20px] text-time">
          {needs}
        </span>
      ) : null}
    </button>
  );
}
