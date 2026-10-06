"use client";
import Link from "next/link";
import { motion, useReducedMotion } from "motion/react";
import { useEffect, useState } from "react";
import { Reveal } from "@/components/reveal";
import { useCase } from "@/components/workspace/case-context";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { PageHead, card, stack, well } from "@/components/workspace/shell";
import { args, claim, tierLabel, type Arg } from "@/lib/case-data";
import { ease } from "@/lib/motion";
import { cn } from "@/lib/utils";

// The refutation assembles (motion.md § "The argument graph sequence"), seconds:
const T = { bus: 0.4, solidHead: 0.7, solid: 0.76, add: 1.18, out: 1.62, done: 1.8, stagger: 0.11 };

const monoLabel = "font-mono text-[11px] tracking-[.05em] text-ink-muted";
const mark = { solid: "●", add: "◇", out: "✕" } as const;
const markColor = { solid: "text-standing", add: "text-ink-muted", out: "text-defeated" } as const;
const verdictColor = { solid: "text-standing", add: "text-ink", out: "text-defeated" } as const;

// ArgumentNode — tier is carried by border style and marker shape, not colour alone:
// solid ground = solid border + 3px standing edge + ●; worth adding = dashed + ◇;
// left out = hatched, struck through + ✕.
function ArgumentNode({ a, delay, instant, pulse, active, onPick }: { a: Arg; delay: number; instant: boolean; pulse: boolean; active: boolean; onPick: () => void }) {
  const out = a.tier === "out";
  return (
    // Defeated nodes arrive with their section and never animate out.
    <Reveal gesture={out ? "fade" : "rise"} trigger="load" delay={delay} instant={instant}>
      <motion.button
        // Evidence satisfied elsewhere pulses the node it feeds, once.
        animate={pulse ? { boxShadow: ["0 0 0 0px var(--standing)", "0 0 0 3px var(--standing)", "0 0 0 0px var(--standing)"] } : undefined}
        transition={{ duration: 0.3, delay: instant ? 0 : delay + 0.4 }}
        onClick={onPick}
        aria-pressed={active}
        className={cn(
          "relative w-full rounded-[10px] p-4 text-left lg:px-5 lg:py-[18px]",
          a.tier === "solid" && "border-[1.5px] border-l-[3px] border-solid border-standing bg-surface",
          a.tier === "add" && "border-[1.5px] border-dashed border-ink-muted bg-surface",
          out && "hatch border border-solid border-defeated bg-transparent",
          active && "shadow-[0_0_0_2px_var(--focus)]",
        )}
      >
        {!out && (
          <span aria-hidden className={cn("absolute -top-[18px] -left-px hidden h-[18px] w-px lg:block", a.tier === "solid" ? "bg-standing" : "bg-ink-muted")} />
        )}
        <div className="flex items-start gap-2.5">
          <span aria-hidden className={cn("text-[12px] leading-none", markColor[a.tier])}>{mark[a.tier]}</span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-baseline gap-[9px]">
              <span className={monoLabel}>{a.ref}</span>
              <h3 className={cn("m-0 text-[17px] leading-[25px] font-semibold", out ? "text-defeated line-through" : "text-ink")}>{a.title}</h3>
              <span className="sr-only">— {tierLabel[a.tier]}</span>
            </div>
            <p className="mt-2 mb-0 text-[15px] leading-6 text-ink-muted text-pretty">{out ? a.why : a.assert}</p>
            {!out && (
              <div className="mt-3">
                <StatusPill kind={a.ok ? "solid" : "plain"}>{a.status}</StatusPill>
              </div>
            )}
            {/* Mobile: the detail expands inline instead of in a side panel. */}
            {active && !out && (
              <div className="mt-3.5 flex flex-col gap-2.5 border-t border-rule pt-3 lg:hidden">
                <div>
                  <div className={cn(monoLabel, "mb-1")}>What they could say back</div>
                  <div className="text-[15px] leading-6 text-ink">{a.reply}</div>
                </div>
                <div className={cn("text-[15px] leading-6 font-medium", verdictColor[a.tier])}>{a.verdict}</div>
                <div className="text-[15px] leading-6 text-ink-muted">{a.why}</div>
                <div className="font-mono text-[11px] leading-[18px] text-ink-muted">Needs: {a.needs}</div>
              </div>
            )}
          </div>
        </div>
      </motion.button>
    </Reveal>
  );
}

function LaneHead({ tier, count, delay, instant, children }: { tier: "solid" | "add" | "out"; count: number; delay: number; instant: boolean; children: string }) {
  return (
    <Reveal
      gesture="fade"
      trigger="load"
      delay={delay}
      instant={instant}
      className={cn(
        "mb-3.5 pt-3",
        tier === "solid" && "border-t-[1.5px] border-solid border-standing",
        tier === "add" && "border-t-[1.5px] border-dashed border-ink-muted",
        tier === "out" && "border-t border-rule",
      )}
    >
      <div className="flex items-center gap-[9px]">
        <span aria-hidden className={cn("text-[13px] leading-none", markColor[tier])}>{mark[tier]}</span>
        <h2 className="m-0 text-[17px] font-semibold text-ink">{tierLabel[tier]}</h2>
        <span className="font-mono text-[12px] text-ink-muted">{count}</span>
      </div>
      <p className={cn("mt-1.5 mb-0 text-[14px] leading-[22px] text-ink-muted text-pretty", tier === "out" ? "max-w-[52ch]" : "max-w-[42ch]")}>{children}</p>
    </Reveal>
  );
}

export default function ArgumentsPage() {
  const { node, setNode, pulse, clearPulse, graphPlayed, markGraphPlayed } = useCase();
  const reduce = useReducedMotion();
  const [runKey, setRunKey] = useState(0);
  // The sequence plays once per case; coming back shows the static diagram.
  const [instant, setInstant] = useState(graphPlayed);
  const [pulseNow] = useState(pulse);

  useEffect(() => {
    clearPulse();
    const t = setTimeout(markGraphPlayed, T.done * 1000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const still = instant || !!reduce;
  const draw = (d: number, origin: string, axis: "x" | "y", length: number) => ({
    initial: still ? false : axis === "x" ? { scaleX: 0 } : { scaleY: 0 },
    animate: axis === "x" ? { scaleX: 1 } : { scaleY: 1 },
    transition: still ? { duration: 0 } : { duration: length, delay: d, ease: ease.move },
    style: { transformOrigin: origin },
  });
  const sel = args.find((a) => a.id === node) ?? args[0];
  const solid = args.filter((a) => a.tier === "solid");
  const add = args.filter((a) => a.tier === "add");
  const out = args.filter((a) => a.tier === "out");

  return (
    <div>
      <PageHead
        title="Their reason, and what answers it"
        lead="Three arguments hold up whatever the insurer says back. Two only help under a narrow reading. One does not work, and we have left it out of your letter."
        action={
          <div className="flex flex-wrap gap-2.5">
            {/* Skip is in the DOM from frame one (motion.md). */}
            {!still && <Button variant="ghost" onClick={() => setInstant(true)}>Show it all</Button>}
            <Button variant="ghost" onClick={() => { setInstant(false); setRunKey(runKey + 1); }}>Replay</Button>
          </div>
        }
      />

      <div className="grid items-start lg:grid-cols-[1fr_360px] lg:gap-8">
        <div className="min-w-0" key={`${runKey}-${instant}`}>
          <Reveal gesture="claim" trigger="load" instant={still} className="rounded-[2px] border-[1.5px] border-ink bg-surface p-[18px] lg:mx-auto lg:max-w-[620px] lg:px-6 lg:py-[22px]">
            <div className="mb-3 flex items-center gap-2.5">
              <span className="size-[9px] bg-ink" />
              <span className="font-mono text-[11px] tracking-[.06em] text-ink-muted">What the insurer says · {claim.code}</span>
            </div>
            <blockquote className="m-0 font-doc text-[19px] leading-8 italic text-ink">{claim.text}</blockquote>
            <div className="mt-3.5 border-t border-rule pt-2.5 font-mono text-[11px] text-ink-muted">{claim.meta}</div>
          </Reveal>

          {/* AttackConnector — the bus from the claim down into both lanes (desktop). */}
          <div aria-hidden className="relative mx-auto hidden h-12 w-full max-w-[760px] lg:block">
            <motion.div className="absolute top-0 left-1/2 h-6 w-px bg-rule" {...draw(T.bus, "top", "y", 0.18)} />
            <motion.div className="absolute top-6 right-1/4 left-1/4 h-px bg-rule" {...draw(T.bus + 0.18, "center", "x", 0.22)} />
            <motion.div className="absolute top-6 left-1/4 h-6 w-px bg-standing" {...draw(T.bus + 0.4, "top", "y", 0.12)} />
            <motion.div className="absolute top-6 left-3/4 h-6 w-px bg-ink-muted" {...draw(T.bus + 0.52, "top", "y", 0.12)} />
          </div>

          <div className="mt-7 grid gap-7 lg:mt-0 lg:grid-cols-2 lg:gap-8">
            <section className="min-w-0">
              <LaneHead tier="solid" count={solid.length} delay={T.solidHead} instant={still}>These stand up to whatever the insurer answers. Your letter leads with them.</LaneHead>
              <div className={stack}>
                {solid.map((a, i) => (
                  <ArgumentNode key={a.id} a={a} delay={T.solid + i * T.stagger} instant={still} pulse={pulseNow.includes(a.id)} active={node === a.id} onPick={() => setNode(a.id)} />
                ))}
              </div>
            </section>
            <section className="min-w-0">
              <LaneHead tier="add" count={add.length} delay={T.add} instant={still}>The insurer has a fair answer to each of these. Useful as extra weight, not as your main point.</LaneHead>
              <div className={stack}>
                {add.map((a, i) => (
                  <ArgumentNode key={a.id} a={a} delay={T.add + i * T.stagger} instant={still} pulse={pulseNow.includes(a.id)} active={node === a.id} onPick={() => setNode(a.id)} />
                ))}
              </div>
            </section>
          </div>

          <section className="mt-7">
            <LaneHead tier="out" count={out.length} delay={T.out} instant={still}>We checked this one and it does not hold. It stays visible so you know it was considered.</LaneHead>
            <div className={stack}>
              {out.map((a) => (
                <ArgumentNode key={a.id} a={a} delay={T.out} instant={still} pulse={false} active={node === a.id} onPick={() => setNode(a.id)} />
              ))}
            </div>
          </section>
        </div>

        <aside className={cn(card, "sticky top-24 hidden p-6 lg:block")} aria-live="polite">
          <div className="mb-3.5 flex items-center gap-2.5">
            <StatusPill kind={sel.tier}>{tierLabel[sel.tier]}</StatusPill>
            <span className={monoLabel}>{sel.ref}</span>
          </div>
          <h2 className="mt-0 mb-3 text-[21px] leading-7 font-semibold tracking-[-0.01em] text-ink">{sel.title}</h2>
          <p className="mt-0 mb-5 text-[16px] leading-[27px] text-ink text-pretty">{sel.assert}</p>
          <div className={well}>
            <div className={cn(monoLabel, "mb-1.5")}>What the insurer could say back</div>
            <div className="text-[16px] leading-[26px] text-ink">{sel.reply}</div>
          </div>
          <div className="mt-[18px]">
            <div className={cn("text-[16px] leading-[26px] font-medium", verdictColor[sel.tier])}>{sel.verdict}</div>
            <p className="mt-2 mb-0 text-[15px] leading-[25px] text-ink-muted text-pretty">{sel.why}</p>
          </div>
          <div className="mt-5 mb-5 border-t border-rule pt-3.5">
            <div className={cn(monoLabel, "mb-1.5")}>Evidence this argument needs</div>
            <div className="text-[15px] leading-6 text-ink">{sel.needs}</div>
            <div className="mt-3"><StatusPill kind={sel.tier}>{sel.status}</StatusPill></div>
          </div>
          <Button variant="ghost" asChild><Link href="/case/evidence/">Go to the evidence list</Link></Button>
        </aside>
      </div>
    </div>
  );
}
