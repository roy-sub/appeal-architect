"use client";
import Link from "next/link";
import { useState } from "react";
import { Reveal } from "@/components/reveal";
import { Button } from "@/components/ui/button";
import { RULES_STAMP } from "@/lib/site";
import { cn } from "@/lib/utils";

const questions = [
  { q: "Where does your health insurance come from?", help: "This decides which rulebook you are under, and that changes every deadline.",
    opts: ["Through a job — mine or a family member’s", "I bought it myself on the marketplace", "Medicare or Medicare Advantage", "Medicaid", "I am not sure"] },
  { q: "What reason does the letter give?", help: "It is usually one line near the top, often with a code beside it.",
    opts: ["Not medically necessary", "Not covered by the plan", "No prior authorisation", "Out of network", "Experimental or investigational", "Something else"] },
  { q: "What date is on the letter?", help: "Most deadlines count from this date, not from when you opened it.",
    opts: ["Within the last week", "One to four weeks ago", "One to three months ago", "More than three months ago", "I cannot find a date"] },
  { q: "Has the treatment already happened?", help: "Claims before treatment and claims after treatment run on different clocks.",
    opts: ["No, it has not happened yet", "Yes, it already happened", "Partly — it started and then stopped"] },
];

const label = "font-mono text-[11px] tracking-[.06em] text-ink-muted";
const card = "rounded-[16px] border border-rule bg-surface";
const pageTitle = "mt-0 mb-2.5 text-[27px] leading-[33px] font-semibold tracking-[-0.015em] text-ink lg:text-[36px] lg:leading-[42px]";

export default function TriagePage() {
  const [tq, setTq] = useState(0);
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const done = tq >= questions.length;
  const cur = questions[Math.min(tq, questions.length - 1)];

  const outputs = [
    { t: "Which appeal track you are on", d: "The rulebook that governs your plan", done: tq >= 1 },
    { t: "Your likely deadline", d: "With the regulation that sets it", done: tq >= 3 },
    { t: "Whether appealing is worth it", d: "Honestly, including when it is not", done: tq >= 4 },
  ];

  return (
    <div className="min-h-dvh bg-ground">
      <header className="sticky top-0 z-40 border-b border-rule bg-ground">
        <div className="mx-auto flex h-[60px] items-center justify-between gap-6 px-5 lg:h-[72px] lg:max-w-[1440px] lg:px-14">
          <Link href="/" className="font-mono text-[12px] font-medium uppercase tracking-[.14em] text-ink no-underline">Appeal&nbsp;Architect</Link>
          <span className="font-mono text-[11px] tracking-[.05em] text-ink-muted">Free check · no account</span>
        </div>
      </header>

      <main className="mx-auto px-5 py-12 lg:max-w-[1280px] lg:px-20 lg:py-[88px]">
        <div className="grid items-start lg:grid-cols-[1fr_360px] lg:gap-8">
          <div className="min-w-0 max-w-[640px]" aria-live="polite">
            {done ? (
              <div>
                <div className={cn(label, "mb-3.5")}>What we can tell you so far</div>
                <h1 className={pageTitle}>You are probably on the ERISA track, and your door is open until late March.</h1>
                <div className="my-7 flex flex-col gap-3.5">
                  <Reveal gesture="unfold" trigger="load" delay={0.0} className={card}>
                    <div className="px-[22px] py-5">
                      <div className={cn(label, "mb-2")}>Your track</div>
                      <div className="mb-2 text-[19px] font-semibold text-ink">Employer plan — internal appeal, then independent external review</div>
                      <p className="mt-0 mb-3 text-[16px] leading-[26px] text-ink-muted text-pretty">
                        Employer-sponsored plans follow federal rules. You get at least one internal appeal, and if that is refused you can take it to a reviewer who does not work for the insurer. Their decision binds the insurer.
                      </p>
                      <div className="border-t border-rule pt-2.5 font-mono text-[12px] text-ink-muted">29 C.F.R. § 2560.503-1</div>
                    </div>
                  </Reveal>
                  <Reveal gesture="unfold" trigger="load" delay={0.04} className={card}>
                    <div className="flex flex-wrap items-center gap-5 px-[22px] py-5">
                      <div>
                        <div className={cn(label, "mb-2")}>Your likely deadline</div>
                        <div className="tabular text-[30px] font-semibold tracking-[-0.02em] text-ink">22 March 2027</div>
                        <div className="mt-1 text-[15px] font-medium text-time-ample">About 168 days from today — on track</div>
                      </div>
                      <p className="m-0 min-w-[220px] flex-1 text-[15px] leading-6 text-ink-muted">
                        Counted as 180 days from the date on your letter. Upload the letter and we will replace this estimate with the exact date and the clause it comes from.
                      </p>
                    </div>
                  </Reveal>
                  <Reveal gesture="unfold" trigger="load" delay={0.08} className={card}>
                    <div className="px-[22px] py-5">
                      <div className={cn(label, "mb-2")}>Is it worth appealing</div>
                      <p className="m-0 text-[16px] leading-[26px] text-ink text-pretty">
                        Probably yes. Denials for medical necessity turn on documentation, and documentation is the part you can still change. That is not a prediction about your case. Nobody can give you one.
                      </p>
                    </div>
                  </Reveal>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Button asChild className="min-h-12 px-[22px] py-3.5">
                    <Link href="/case/documents/">Upload the letter</Link>
                  </Button>
                  <Button variant="ghost" className="min-h-12 px-[22px] py-3.5 text-[16px]" onClick={() => { setTq(0); setAnswers({}); }}>
                    Start over
                  </Button>
                </div>
                <p className="mt-6 mb-0 font-mono text-[11px] leading-[18px] text-ink-muted">{RULES_STAMP}</p>
              </div>
            ) : (
              <div>
                <div className="mb-7 flex items-center gap-3.5">
                  <span className={cn(label, "whitespace-nowrap")}>Question {tq + 1} of {questions.length}</span>
                  <div className="h-[3px] max-w-[420px] flex-1 overflow-hidden rounded-[2px] bg-rule" role="progressbar" aria-valuemin={0} aria-valuemax={questions.length} aria-valuenow={tq}>
                    <div className="h-full bg-ink transition-[width] duration-[260ms] ease-move" style={{ width: `${(tq / questions.length) * 100}%` }} />
                  </div>
                </div>
                <h1 className={pageTitle}>{cur.q}</h1>
                <p className="mt-0 mb-7 max-w-[68ch] text-[17px] leading-7 text-ink-muted text-pretty lg:text-[18px] lg:leading-[29px]">{cur.help}</p>
                <div className="flex max-w-[560px] flex-col gap-2.5">
                  {cur.opts.map((o, i) => {
                    const picked = answers[tq] === i;
                    return (
                      <button
                        key={o}
                        onClick={() => { setAnswers({ ...answers, [tq]: i }); setTq(tq + 1); }}
                        className={cn(
                          "flex min-h-[60px] w-full items-center gap-3.5 rounded-[10px] border bg-surface px-[18px] py-3.5 text-left text-[17px] text-ink transition-colors hover:border-ink-muted",
                          picked ? "border-ink" : "border-rule",
                        )}
                      >
                        <span className={cn("size-4 shrink-0 rounded-[2px] border-[1.5px]", picked ? "border-ink bg-ink" : "border-rule bg-transparent")} />
                        <span>{o}</span>
                      </button>
                    );
                  })}
                </div>
                <div className="mt-6">
                  <button
                    onClick={() => setTq(Math.max(0, tq - 1))}
                    className={cn("min-h-11 rounded-[10px] border border-rule px-4 py-2.5 text-[15px] text-ink-muted", tq === 0 && "invisible")}
                  >
                    Back
                  </button>
                </div>
              </div>
            )}
          </div>

          <aside className={cn(card, "sticky top-[96px] hidden p-6 lg:block")}>
            <div className={cn(label, "mb-1.5")}>What this works out</div>
            {outputs.map((o) => (
              <div key={o.t} className={cn("flex items-start gap-3 border-t border-rule py-3.5 transition-opacity duration-[260ms]", !o.done && "opacity-45")}>
                <span className={cn("mt-[7px] size-[9px] shrink-0 rounded-full border-[1.5px]", o.done ? "border-standing bg-standing" : "border-rule bg-transparent")} />
                <div>
                  <div className="text-[16px] leading-6 font-medium text-ink">{o.t}</div>
                  <div className="mt-0.5 text-[14px] leading-[21px] text-ink-muted">{o.d}</div>
                </div>
              </div>
            ))}
            <p className="mt-[18px] mb-0 border-t border-rule pt-4 text-[14px] leading-[22px] text-ink-muted">No account, no card, nothing stored unless you choose to open a case.</p>
          </aside>
        </div>
      </main>
    </div>
  );
}
