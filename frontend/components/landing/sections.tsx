import Link from "next/link";
import { MediaSlot } from "@/components/media-slot";
import { Reveal } from "@/components/reveal";
import { Button } from "@/components/ui/button";
import { capabilities, personas, plans, stats, steps } from "@/lib/landing-content";
import { DISCLAIMER, RULES_STAMP } from "@/lib/site";
import { cn } from "@/lib/utils";

const step = 0.1; // stagger between siblings, seconds

function Index({ n, className }: { n: string; className?: string }) {
  return <span className={cn("mb-[18px] block font-mono text-[11px] tracking-[.18em] text-clay-deep lg:mb-0", className)}>{n}</span>;
}

const h2 = "m-0 text-[30px] leading-[37px] font-semibold tracking-[-0.028em] text-ink lg:text-[40px] lg:leading-[46px]";

// 02 — the emotional turn: numerals wiped up from their own baseline.
export function Stats() {
  return (
    <section className="relative overflow-hidden bg-band">
      <div className="absolute inset-0 opacity-[.13]">
        <MediaSlot fill slotId="stat-backdrop" kind="image" label="Quiet backdrop for the statistics band" intrinsic="2100×900" />
      </div>
      <div className="relative mx-auto px-5 py-14 lg:max-w-[1440px] lg:px-14 lg:py-24">
        <div className="mb-11 grid lg:mb-[72px] lg:grid-cols-[56px_1fr]">
          <span className="mb-4 font-mono text-[11px] tracking-[.18em] text-wheat lg:mb-0">02</span>
          <p className="m-0 max-w-[520px] text-[27px] leading-[34px] font-semibold tracking-[-0.025em] text-band-ink text-pretty lg:text-[40px] lg:leading-[48px]">
            Almost nobody appeals. It works more often than not.
          </p>
        </div>
        <div className="grid gap-y-[38px] lg:grid-cols-3 lg:gap-x-8 lg:gap-y-0">
          {stats.map((s, i) => (
            <div key={s.label} className="relative min-w-0 pt-[26px] lg:pt-[34px]">
              <Reveal as="span" gesture="drawRight" delay={i * step} className="absolute inset-x-0 top-0 h-px origin-left bg-[rgb(244_239_229/.32)]" />
              <Reveal
                  wrapClassName="overflow-hidden"
                  gesture="countUp"
                  delay={i * step}
                  className={cn(
                    "tabular block text-[68px] leading-[66px] font-semibold tracking-[-0.05em] lg:text-[128px] lg:leading-[116px]",
                    i === 1 ? "text-wheat" : "text-band-ink",
                  )}
                >
                  {s.n}
                  <span className="ml-[0.06em] text-[0.38em] tracking-[-0.02em]">{s.suf.trim()}</span>
                </Reveal>
              <div className="mt-3.5 max-w-[280px] text-[16px] leading-[25px] text-band-ink text-pretty lg:mt-5 lg:text-[17px] lg:leading-[26px]">{s.label}</div>
              <div className="mt-2.5 max-w-[300px] font-mono text-[12px] leading-[19px] text-band-muted">{s.note}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// 03 — one hairline across the top of the track; every station hangs beneath it
// from the same baseline. On mobile the same rule stands on its end.
export function Process() {
  return (
    <section id="how" className="mx-auto scroll-mt-[60px] px-5 py-16 lg:max-w-[1440px] lg:scroll-mt-[72px] lg:px-14 lg:pt-28 lg:pb-[124px]">
      <div className="mb-11 grid items-start lg:mb-20 lg:grid-cols-[56px_minmax(0,1.5fr)_minmax(0,1fr)] lg:gap-x-8">
        <Index n="03" />
        <h2 className={cn(h2, "text-balance")}>Three steps, and you are holding a filed appeal.</h2>
        <p className="mt-4 max-w-[340px] text-[16px] leading-[27px] text-ink-muted text-pretty lg:mt-1.5">
          No part of this asks you to understand insurance law. It asks you to confirm what your own letter says.
        </p>
      </div>
      <div className="relative grid pl-7 lg:grid-cols-3 lg:gap-x-12 lg:pt-px lg:pl-0">
        <Reveal as="span" gesture="drawDown" duration={1.1} className="absolute top-2 bottom-2 left-[3px] w-px origin-top bg-ink lg:hidden" />
        <Reveal as="span" gesture="drawRight" duration={1.2} className="absolute inset-x-0 top-0 hidden h-px origin-left bg-ink lg:block" />
        {steps.map((t, i) => (
          <div key={t.num} className="relative flex min-w-0 flex-col pb-11 lg:pb-0">
            <Reveal gesture="lift" duration={0.68} delay={i * 0.11} className="flex flex-col lg:pt-[34px]">
              <span className="mb-3.5 font-mono text-[12px] tracking-[.18em] text-clay-deep lg:text-[13px]">{t.num}</span>
              <h3 className="mt-0 mb-2.5 max-w-[270px] text-[21px] leading-[29px] font-semibold tracking-[-0.018em] text-ink text-balance lg:min-h-[62px] lg:max-w-[15ch] lg:text-[23px] lg:leading-[31px]">
                {t.title}
              </h3>
              <p className="m-0 max-w-[330px] text-[15px] leading-[26px] text-ink-muted text-pretty lg:max-w-[34ch]">{t.body}</p>
            </Reveal>
            <Reveal
              as="span"
              gesture="dot"
              delay={0.26 + i * 0.11}
              className="absolute top-1.5 -left-7 size-[7px] rounded-full bg-clay lg:-top-1 lg:-left-1 lg:size-[9px]"
            />
          </div>
        ))}
      </div>
    </section>
  );
}

// 04 — their quote arrives with a drawn margin rule; the answer nudges in beside it.
export function Capabilities() {
  return (
    <section id="does" className="mx-auto scroll-mt-[60px] px-5 pb-14 lg:max-w-[1440px] lg:scroll-mt-[72px] lg:px-14 lg:pb-24">
      <div className="mb-8 grid lg:mb-14 lg:grid-cols-[56px_1fr] lg:gap-x-8">
        <Index n="04" />
        <h2 className="m-0 text-[30px] leading-[37px] font-semibold tracking-[-0.03em] text-ink lg:text-[44px] lg:leading-[50px]">
          Their sentence on the left.
          <br />
          Your answer on the right.
        </h2>
      </div>
      {capabilities.map((c, i) => {
        const flip = i % 2 === 1;
        return (
          <article
            key={c.slot}
            className={cn(
              "grid items-start gap-y-[18px] border-t border-rule py-[34px] lg:gap-x-8 lg:gap-y-0 lg:py-16",
              flip ? "lg:grid-cols-[56px_4fr_7fr]" : "lg:grid-cols-[56px_7fr_4fr]",
            )}
          >
            <div className="order-1 hidden min-w-0 lg:block">
              <span className="block pt-1 font-mono text-[12px] tracking-[.1em] text-ink-muted">0{i + 1}</span>
            </div>
            <div className={cn("order-1 min-w-0", flip ? "lg:order-3" : "lg:order-2")}>
              <div className="mb-3.5 font-mono text-[11px] uppercase tracking-[.12em] text-ink-muted">{c.source}</div>
              <div className="relative pl-[22px]">
                <Reveal as="span" gesture="drawDown" delay={(i % 3) * step} className="absolute inset-y-0 left-0 w-0.5 origin-top bg-clay" />
                <blockquote className="m-0 max-w-[540px] font-doc text-[20px] leading-[33px] italic text-ink text-pretty lg:text-[23px] lg:leading-[37px]">
                  {c.quote}
                </blockquote>
              </div>
              <Reveal gesture="wipeRight" delay={((i + 1) % 3) * step} wrapClassName="mt-[26px] lg:mt-9" className="overflow-hidden">
                <MediaSlot slotId={c.slot} ratio={c.ratio} kind={c.kind} label={c.slotLabel} intrinsic={c.intrinsic} />
              </Reveal>
            </div>
            <Reveal
              gesture="nudge"
              delay={((i + 2) % 3) * step}
              className={cn("order-2 min-w-0 border-l-2 border-clay pl-[18px] lg:border-l-0 lg:pl-0", flip ? "lg:order-2" : "lg:order-3")}
            >
              <h3 className="mt-0 mb-3.5 text-[21px] leading-[29px] font-semibold tracking-[-0.018em] text-ink text-pretty lg:text-[25px] lg:leading-[33px]">{c.title}</h3>
              <p className="mt-0 mb-5 text-[16px] leading-[27px] text-ink-muted text-pretty">{c.body}</p>
              <div className="border-t border-rule pt-3 font-mono text-[11px] leading-[18px] tracking-[.03em] text-ink-muted">{c.cite}</div>
            </Reveal>
          </article>
        );
      })}
    </section>
  );
}

// 05 — portraits unmask; columns sit on a deliberate stagger.
export function Personas() {
  return (
    <section className="border-y border-rule bg-surface-sunk px-5 py-14 lg:px-14 lg:pt-[104px] lg:pb-[120px]">
      <div className="mx-auto mb-9 grid lg:mb-16 lg:max-w-[1440px] lg:grid-cols-[56px_1fr] lg:gap-x-8">
        <Index n="05" />
        <h2 className={cn(h2, "max-w-[520px] text-pretty")}>Three people arrive here, in three different states of mind.</h2>
      </div>
      <div className="mx-auto grid items-start gap-y-11 lg:max-w-[1440px] lg:grid-cols-3 lg:gap-x-8 lg:gap-y-0">
        {personas.map((p, i) => (
          <div key={p.slot} className={cn("min-w-0", ["lg:pt-0", "lg:pt-[72px]", "lg:pt-7"][i])}>
            <Reveal gesture="wipeRight" duration={0.9} delay={i * step} wrapClassName="" className="overflow-hidden">
              <MediaSlot slotId={p.slot} ratio={p.ratio} kind="image" label={p.alt} intrinsic={p.intrinsic} />
            </Reveal>
            <div className="mt-5 mb-3 flex items-center gap-3">
              <span className="whitespace-nowrap font-mono text-[10px] uppercase tracking-[.18em] text-clay-deep">{p.tag}</span>
              <span className="h-px flex-1 bg-rule" />
            </div>
            <h3 className="mt-0 mb-2.5 max-w-[250px] text-[21px] leading-[29px] font-semibold tracking-[-0.018em] text-ink lg:text-[22px] lg:leading-[30px]">{p.title}</h3>
            <p className="m-0 max-w-[330px] text-[15px] leading-[26px] text-ink-muted text-pretty">{p.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

// 06 — each plan's top rule draws in; the featured one in clay at 3px.
export function Pricing() {
  return (
    <section id="pricing" className="mx-auto scroll-mt-[60px] px-5 py-16 lg:max-w-[1440px] lg:scroll-mt-[72px] lg:px-14 lg:py-28">
      <div className="mb-10 grid items-end lg:mb-[72px] lg:grid-cols-[56px_1.45fr_1fr] lg:gap-x-12">
        <Index n="06" />
        <h2 className={cn(h2, "text-pretty")}>You find out whether you have a case before you pay.</h2>
        <p className="mt-4 mb-0 max-w-[350px] text-[16px] leading-[27px] text-ink-muted text-pretty lg:mt-0 lg:justify-self-end">
          The free check is the whole triage, not a teaser. If there is no route, it says so and you owe nothing.
        </p>
      </div>
      <div className="grid items-start gap-y-10 lg:grid-cols-3 lg:gap-x-8 lg:gap-y-0">
        {plans.map((p, i) => (
          <div key={p.name} className={cn("relative flex min-w-0 flex-col pt-[22px]", i > 0 && "lg:border-l lg:border-rule lg:pl-8")}>
            <Reveal
              as="span"
              gesture="drawRight"
              duration={0.76}
              delay={i * step}
              className={cn("absolute top-0 right-0 left-0 origin-left", i > 0 && "lg:left-8", p.featured ? "h-[3px] bg-clay" : "h-px bg-ink")}
            />
            <div className="mb-[18px] flex flex-wrap items-baseline gap-3">
              <span className="font-mono text-[12px] font-medium uppercase tracking-[.16em] text-ink">{p.name}</span>
              {p.featured && <span className="font-mono text-[10px] uppercase tracking-[.14em] text-clay-deep">Most people choose this</span>}
            </div>
            <div className="mb-3.5 flex items-baseline gap-[9px]">
              <span className="tabular text-[48px] leading-none font-semibold tracking-[-0.04em] text-ink lg:text-[60px]">{p.price}</span>
              <span className="text-[14px] text-ink-muted">{p.unit}</span>
            </div>
            <p className="mt-0 mb-6 max-w-[310px] text-[15px] leading-[25px] text-ink-muted text-pretty">{p.blurb}</p>
            <ul className="m-0 mb-7 flex list-none flex-col p-0">
              {p.items.map((t, j) => (
                <li key={t} className="flex items-baseline gap-3.5 border-t border-rule py-[11px]">
                  <span className="shrink-0 font-mono text-[10px] tracking-[.1em] text-ink-muted">{String(j + 1).padStart(2, "0")}</span>
                  <span className="text-[15px] leading-6 text-ink">{t}</span>
                </li>
              ))}
            </ul>
            <Button variant={p.featured ? "clayBlock" : "outlineBlock"} className="mt-auto" asChild>
              <Link href={p.href}>{p.cta}</Link>
            </Button>
          </div>
        ))}
      </div>
      <p className="mt-8 mb-0 font-mono text-[11px] leading-[18px] tracking-[.06em] text-ink-muted lg:mt-12">
        Advocate Pro, with multi-case dashboards, comes later. No price yet.
      </p>
    </section>
  );
}

// 08 — closing call: the line lifts out of its clip.
export function ClosingCall() {
  return (
    <section className="bg-clay text-paper">
      <div className="mx-auto px-5 py-14 lg:max-w-[1440px] lg:px-14 lg:pt-24 lg:pb-[104px]">
        <Reveal wrapClassName="overflow-hidden" as="h2" gesture="lineup" duration={0.82} className="m-0 text-[36px] leading-10 font-semibold tracking-[-0.04em] text-paper lg:text-[72px] lg:leading-[72px]">
            Find out what your deadline is.
          </Reveal>
        <div className="mt-7 grid items-end gap-[26px] border-t border-paper/30 pt-7 lg:mt-12 lg:grid-cols-[minmax(0,540px)_1fr] lg:gap-12 lg:pt-10">
          <p className="m-0 text-[16px] leading-7 text-paper/86 text-pretty lg:text-[17px]">
            Four questions. No account, no card. If there is no route left, it will tell you that instead of selling you something.
          </p>
          <Button variant="invert" className="justify-self-start lg:justify-self-end" asChild>
            <Link href="/triage/">Start the free check</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}

export function SiteFooter() {
  const col = "flex flex-col gap-3";
  const head = "mb-0.5 font-mono text-[10px] uppercase tracking-[.18em] text-band-muted";
  const link = "text-[14px] text-band-ink no-underline hover:underline";
  return (
    <footer className="bg-band px-5 pt-12 pb-9 text-band-ink lg:px-14 lg:pt-20 lg:pb-12">
      <div className="mx-auto grid gap-8 lg:max-w-[1440px] lg:grid-cols-[2fr_1fr_1fr] lg:gap-12">
        <div className="min-w-0">
          <div className="mb-3.5 font-mono text-[12px] font-medium uppercase tracking-[.2em] text-band-ink">Appeal Architect</div>
          <div className="max-w-[290px] text-[15px] leading-[25px] text-band-muted">Your denial, formally refuted. Every paragraph backed by a rule.</div>
        </div>
        <div className={col}>
          <span className={head}>Product</span>
          <Link href="/#how" className={link}>How it works</Link>
          <Link href="/pricing/" className={link}>Pricing</Link>
          <Link href="/#faq" className={link}>Questions</Link>
        </div>
        <div className={col}>
          <span className={head}>Legal</span>
          <Link href="/legal/" className={link}>Terms</Link>
          <Link href="/legal/" className={link}>Privacy, in plain language</Link>
          <Link href="/legal/" className={link}>Rules changelog</Link>
        </div>
      </div>
      <div className="mx-auto mt-9 flex flex-col gap-3.5 border-t border-band-rule pt-6 lg:mt-16 lg:max-w-[1440px]">
        <p className="m-0 max-w-[830px] text-[13px] leading-[22px] text-band-ink">{DISCLAIMER}</p>
        <p className="m-0 font-mono text-[10px] leading-[17px] uppercase tracking-[.1em] text-band-muted">{RULES_STAMP}</p>
      </div>
    </footer>
  );
}
