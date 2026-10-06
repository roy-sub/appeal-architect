import { cn } from "@/lib/utils";

export type PillKind = "solid" | "add" | "out" | "ink" | "plain";

// Standing is never colour alone: solid border = solid ground, dashed = worth adding.
const kinds: Record<PillKind, string> = {
  solid: "border-solid border-standing bg-standing-tint text-standing",
  add: "border-dashed border-ink-muted bg-transparent text-ink-muted",
  out: "border-solid border-defeated bg-transparent text-defeated",
  ink: "border-solid border-ink bg-transparent text-ink",
  plain: "border-solid border-rule bg-transparent text-ink-muted",
};

export function StatusPill({ kind = "plain", className, children }: { kind?: PillKind; className?: string; children: React.ReactNode }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-[2px] border px-[9px] py-1 font-mono text-[11px] font-medium tracking-[.04em]", kinds[kind], className)}>
      {children}
    </span>
  );
}
