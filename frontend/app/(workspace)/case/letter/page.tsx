"use client";
import { useState } from "react";
import { Reveal } from "@/components/reveal";
import { StatusPill } from "@/components/status-pill";
import { useCase } from "@/components/workspace/case-context";
import { Button } from "@/components/ui/button";
import { Bullets, PageHead, card, label } from "@/components/workspace/shell";
import { args, letterParas, mailList, tierLabel } from "@/lib/case-data";
import { cn } from "@/lib/utils";

export default function LetterPage() {
  const [para, setPara] = useState<string | null>(null);
  const { node, setNode } = useCase();
  const sel = args.find((a) => a.id === node) ?? args[0];

  return (
    <div>
      <div className="no-print">
        <PageHead
          title="Your appeal letter"
          lead="Built from the arguments that hold. Tap any paragraph to see which argument put it there. Edit anything — it is your letter and your signature."
          action={
            <div className="flex flex-wrap gap-2.5">
              <Button variant="ghost" onClick={() => window.print()}>Export PDF</Button>
              <Button>Export DOCX</Button>
            </div>
          }
        />
      </div>
      <div className="grid items-start gap-5 lg:grid-cols-[1fr_320px] lg:gap-7">
        <div className="min-w-0">
          <article className={cn(card, "print-sheet rounded-[2px] px-[18px] py-[22px] shadow-e1 lg:px-14 lg:py-11")}>
            <div className="mb-[22px] border-b border-rule pb-3.5 font-mono text-[11px] leading-[18px] text-ink-muted">
              M. OKONKWO · 2219 LAUREL ST, RICHMOND VA 23220
              <br />
              ANTHEM BLUE CROSS, APPEALS · P.O. BOX 60007, LOS ANGELES CA 90060
              <br />
              RE: CLAIM CLM-4471902 · APPEAL OF ADVERSE DETERMINATION DATED 14 SEP 2026
            </div>
            <div className="mb-[18px] font-doc text-[17px] leading-[30px] text-ink">To the appeals reviewer,</div>
            <div className="flex flex-col gap-3.5">
              {letterParas.map((p, i) => {
                const active = para === p.id;
                // Paragraphs assemble top-down; each badge lands 80ms behind its sentence.
                return (
                  <Reveal key={p.id} gesture="riseSm" trigger="load" delay={i * 0.09}>
                    <Reveal gesture="fade" trigger="load" delay={i * 0.09 + 0.08} className="no-print mb-1.5">
                      <span
                        className={cn(
                          "rounded-[2px] border bg-surface px-1.5 py-0.5 font-mono text-[11px] tracking-[.04em]",
                          p.ref ? "border-standing text-standing" : "border-rule text-ink-muted",
                        )}
                      >
                        {p.ref ?? "procedural"}
                      </span>
                    </Reveal>
                    <button
                      onClick={() => {
                        setPara(active ? null : p.id);
                        if (p.ref) setNode(p.ref.toLowerCase());
                      }}
                      aria-pressed={active}
                      className={cn(
                        "block w-full rounded-[2px] border-l-2 px-3 py-2.5 text-left font-doc text-[17px] leading-[30px] text-ink lg:px-4 lg:py-3 lg:text-[18px] lg:leading-[31px]",
                        active ? "border-standing bg-standing-tint" : "border-transparent bg-transparent",
                      )}
                    >
                      {p.text}
                    </button>
                  </Reveal>
                );
              })}
            </div>
            <div className="mt-[22px] font-doc text-[17px] leading-[30px] text-ink">
              Sincerely,
              <br />
              <br />
              M. Okonkwo
              <br />
              Member ID AB4471902 · 5 October 2026
            </div>
            <p className="mt-[26px] mb-0 border-t border-rule pt-4 text-[14px] leading-[22px] text-ink">
              This letter was prepared with Appeal Architect, a document preparation tool. It is not legal advice and no lawyer has reviewed it. The member reviews, signs and files it themselves.
            </p>
          </article>
        </div>
        <div className="no-print flex min-w-0 flex-col gap-4">
          <div className={card} aria-live="polite">
            <div className="p-5">
              <div className="mb-3 flex items-center gap-2.5">
                <StatusPill kind={sel.tier}>{tierLabel[sel.tier]}</StatusPill>
                <span className="font-mono text-[11px] tracking-[.05em] text-ink-muted">{sel.ref}</span>
              </div>
              <div className="mb-2 text-[17px] leading-[25px] font-semibold text-ink">{sel.title}</div>
              <p className="mt-0 mb-3.5 text-[15px] leading-6 text-ink-muted text-pretty">{sel.why}</p>
              <div className="border-t border-rule pt-2.5 font-mono text-[11px] leading-[18px] text-ink-muted">Needs: {sel.needs}</div>
            </div>
          </div>
          <div className={card}>
            <div className="p-5">
              <div className={cn(label, "mb-3")}>Before you send it</div>
              <Bullets items={mailList} />
            </div>
          </div>
          <div className={card}>
            <div className="p-5">
              <div className={cn(label, "mb-2.5")}>Due 22 March 2027</div>
              <div className="text-[15px] leading-6 font-medium text-time-ample">168 days left — on track</div>
              <p className="mt-2.5 mb-0 text-[14px] leading-[22px] text-ink-muted">One item of evidence is still missing. The letter is complete without it, but A2 is stronger with it.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
