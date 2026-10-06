"use client";
import Link from "next/link";
import { useState } from "react";
import { DeadlineRing } from "@/components/deadline-ring";
import { MediaSlot } from "@/components/media-slot";
import { Reveal } from "@/components/reveal";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { PageHead, card, stack } from "@/components/workspace/shell";
import { cases } from "@/lib/case-data";
import { tone } from "@/lib/time";
import { cn } from "@/lib/utils";

export default function CasesPage() {
  const [empty, setEmpty] = useState(false);
  return (
    <div>
      <PageHead
        title="Your cases"
        lead="Three open. Sorted by how soon each one needs you, not by when you added it."
        action={<Button variant="ghost" onClick={() => setEmpty(!empty)}>{empty ? "Show case list" : "Show empty state"}</Button>}
      />
      {empty ? (
        <div className="flex flex-col items-center gap-4 rounded-[16px] border-[1.5px] border-dashed border-rule bg-surface px-7 py-12 text-center">
          <div className="w-[120px]">
            <MediaSlot slotId="empty-cases" ratio="4 / 3" kind="illustration" label="A closed folder resting on a desk" intrinsic="640×480" className="p-2 [&_div]:text-[9px]" />
          </div>
          <h2 className="m-0 text-[21px] leading-7 font-semibold text-ink">No cases yet</h2>
          <p className="m-0 max-w-[44ch] text-[16px] leading-[26px] text-ink-muted text-pretty">
            Start with the denial letter. Photograph every page, or drop the PDF. We read it and tell you what your deadline is before you pay anything.
          </p>
          <Button asChild><Link href="/case/documents/">Add a denial letter</Link></Button>
        </div>
      ) : (
        <div className={stack}>
          {cases.map((c, i) => {
            const t = tone(c.days);
            return (
              <Reveal key={c.claim} gesture="riseSm" trigger="load" delay={i * 0.05}>
              <Link
                href="/case/roadmap/"
                className={cn(card, "flex w-full flex-col items-stretch gap-4 p-[18px] text-left no-underline transition-colors hover:border-ink-muted lg:flex-row lg:items-center lg:gap-6 lg:px-6 lg:py-[22px]")}
              >
                <span className="lg:hidden"><DeadlineRing days={c.days} total={c.total} size={56} /></span>
                <span className="hidden lg:block"><DeadlineRing days={c.days} total={c.total} size={64} /></span>
                <div className="min-w-0 flex-1">
                  <div className="text-[18px] leading-[26px] font-semibold text-ink">{c.ins}</div>
                  <div className="mt-0.5 text-[15px] leading-[23px] text-ink-muted">{c.reason}</div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <StatusPill>{c.stage}</StatusPill>
                    <StatusPill>{c.claim}</StatusPill>
                  </div>
                </div>
                <div className="shrink-0 text-left">
                  <div className="font-mono text-[11px] tracking-[.05em] text-ink-muted">NEXT DEADLINE</div>
                  <div className="tabular mt-1 text-[18px] font-semibold text-ink">{c.date}</div>
                  <div className="text-[14px]" style={{ color: t.color, fontWeight: t.weight }}>{c.days} days left · {t.word}</div>
                </div>
              </Link>
              </Reveal>
            );
          })}
          <Link
            href="/case/documents/"
            className="flex min-h-16 items-center rounded-[16px] border-[1.5px] border-dashed border-rule bg-transparent p-5 text-left text-[16px] text-ink-muted no-underline hover:border-ink-muted"
          >
            Add another case
          </Link>
        </div>
      )}
    </div>
  );
}
