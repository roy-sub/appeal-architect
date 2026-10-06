"use client";
import Link from "next/link";
import { useState } from "react";
import { DeadlineRing } from "@/components/deadline-ring";
import { Reveal } from "@/components/reveal";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Sheet, SheetClose, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { PageHead, RuleQuote, card, label, well } from "@/components/workspace/shell";
import { roadSteps } from "@/lib/case-data";
import { tone } from "@/lib/time";
import { cn } from "@/lib/utils";

export default function RoadmapPage() {
  const [open, setOpen] = useState<number | null>(null);
  const d = roadSteps[open ?? 0];

  return (
    <div>
      <PageHead
        title="Your route, and when each door closes"
        lead="You are at step one. Nothing after it starts until the step before it finishes, so there is only ever one thing to do next."
      />

      <div className={card}>
        <div className="flex flex-wrap items-center gap-5 px-[22px] py-5">
          <span className="lg:hidden"><DeadlineRing days={168} total={180} size={64} /></span>
          <span className="hidden lg:block"><DeadlineRing days={168} total={180} size={76} /></span>
          <div className="min-w-0 flex-1">
            <div className={cn(label, "mb-1.5")}>Next thing due</div>
            <div className="text-[21px] leading-7 font-semibold text-ink">File the internal appeal by 22 March 2027</div>
            <p className="mt-1.5 mb-0 text-[15px] leading-6 text-ink-muted text-pretty">
              You have time. We will remind you at 30, 14, 7, 3 and 1 days, and again the morning it is due.
            </p>
          </div>
          <Button variant="ghost" asChild><Link href="/case/letter/">Open the draft</Link></Button>
        </div>
      </div>

      <div className="mt-7 mb-3.5 flex items-baseline gap-3.5">
        <span className={cn(label, "whitespace-nowrap")}>Four steps</span>
        <span className="h-px flex-1 bg-rule" />
      </div>

      <ol className="m-0 flex list-none flex-col items-stretch gap-3.5 p-0 lg:flex-row lg:gap-4">
        {roadSteps.map((s, i) => {
          const t = tone(s.days);
          return (
            <li key={s.n} className="min-w-0 lg:flex-1">
              <Reveal gesture="rise" trigger="load" delay={i * 0.06} className="h-full">
              <button
                onClick={() => setOpen(i)}
                className={cn(
                  card,
                  "h-full w-full p-[18px] text-left transition-colors hover:border-ink-muted lg:p-5",
                  s.current ? "border-[1.5px] border-ink" : "border-rule",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="font-mono text-[12px] text-ink-muted">{s.n}</span>
                  <StatusPill kind={s.current ? "ink" : "plain"}>{s.who}</StatusPill>
                </div>
                <div className="mt-3.5 flex items-center gap-3.5">
                  <span className="lg:hidden"><DeadlineRing days={s.days} total={s.total} size={60} /></span>
                  <span className="hidden lg:block"><DeadlineRing days={s.days} total={s.total} size={72} /></span>
                  <div className="min-w-0">
                    <div className="text-[17px] leading-6 font-semibold text-ink">{s.title}</div>
                    <div className="tabular text-[19px] font-semibold tracking-[-0.01em] text-ink lg:text-[21px]">{s.date}</div>
                    <div className="text-[14px]" style={{ color: t.color, fontWeight: t.weight }}>
                      {s.current ? `Open now · ${t.word}` : `Starts after step ${String(i).padStart(2, "0")}`}
                    </div>
                  </div>
                </div>
                <p className="mt-3.5 mb-0 text-[14px] leading-[22px] text-ink-muted text-pretty">{s.need}</p>
                <div className="mt-3.5 border-t border-rule pt-2.5 font-mono text-[11px] leading-[18px] text-ink-muted">{s.rule}</div>
              </button>
              </Reveal>
            </li>
          );
        })}
      </ol>
      <p className="mt-5 mb-0 max-w-[68ch] text-[15px] leading-6 text-ink-muted text-pretty">
        Open any step to see the date it was counted from and the exact words of the rule that sets the count. If we cannot work a date out with confidence, the step says so instead of showing a guess.
      </p>

      <Sheet open={open !== null} onOpenChange={(o) => !o && setOpen(null)}>
        <SheetContent aria-describedby={undefined}>
          <div className="mb-5 flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className={label}>Step {d.n}</div>
              <SheetTitle className="mt-1 mb-0 text-[26px] leading-[34px] font-semibold tracking-[-0.01em] text-ink">{d.title}</SheetTitle>
            </div>
            <SheetClose asChild><Button variant="small">Close</Button></SheetClose>
          </div>
          <div className="flex flex-col gap-[18px]">
            <div>
              <div className={cn(label, "mb-1.5")}>Due</div>
              <div className="tabular text-[26px] font-semibold tracking-[-0.01em] text-ink">{d.date}</div>
            </div>
            <div>
              <div className={cn(label, "mb-1.5")}>How that date was worked out</div>
              <p className="m-0 text-[16px] leading-[27px] text-ink text-pretty">{d.calc}</p>
            </div>
            <div className={well}>
              <div className="mb-2 font-mono text-[11px] tracking-[.05em] text-ink-muted">{d.rule}</div>
              <RuleQuote>{d.quote}</RuleQuote>
            </div>
            <div>
              <div className={cn(label, "mb-1.5")}>What this step needs</div>
              <p className="m-0 text-[16px] leading-[27px] text-ink">{d.need}</p>
            </div>
            <p className="m-0 border-t border-rule pt-4 text-[14px] leading-[22px] text-ink-muted">
              Deadlines are our best reading of your plan and the regulations. Check the date against your own letter before you rely on it.
            </p>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  );
}
