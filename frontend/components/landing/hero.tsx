import Link from "next/link";
import { MediaSlot } from "@/components/media-slot";
import { Reveal } from "@/components/reveal";
import { Button } from "@/components/ui/button";
import { heroFacts, marquee } from "@/lib/landing-content";

export function SiteNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-ground">
      <div className="mx-auto flex h-[60px] items-center justify-between gap-6 px-5 lg:h-[72px] lg:max-w-[1440px] lg:px-14">
        <Link href="/" className="whitespace-nowrap font-mono text-[12px] font-medium uppercase tracking-[.2em] text-ink no-underline">
          Appeal Architect
        </Link>
        <nav aria-label="Primary" className="hidden items-center gap-9 lg:flex">
          {[
            ["#how", "How it works"],
            ["#does", "What it does"],
            ["#pricing", "Pricing"],
            ["#faq", "Questions"],
          ].map(([href, label]) => (
            <a key={href} href={href} className="whitespace-nowrap text-[14px] text-ink-muted no-underline hover:text-ink">
              {label}
            </a>
          ))}
          <Button variant="nav" asChild>
            <Link href="/triage/">Check my deadline</Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}

// 01 — full-bleed background media, headline lines lifting out of their clip.
export function Hero() {
  return (
    <section className="relative flex min-h-[620px] flex-col overflow-hidden bg-forest-deep lg:min-h-[780px]">
      <div className="absolute inset-0 animate-kenburns">
        <MediaSlot
          fill
          slotId="hero-bg"
          kind="video"
          label="Slow documentary footage: a person at a kitchen table opening a denial letter, late afternoon light"
          intrinsic="2560×1440"
        />
      </div>
      <div
        className="absolute inset-0"
        style={{ background: "linear-gradient(170deg, rgb(14 51 43 / .40) 0%, rgb(14 51 43 / .70) 46%, rgb(8 30 25 / .95) 100%)" }}
      />
      <div aria-hidden className="pointer-events-none absolute inset-y-0 left-14 right-14 hidden grid-cols-4 lg:grid">
        {[0, 1, 2, 3].map((i) => (
          <span key={i} className="border-r border-[rgb(244_239_229/.07)]" />
        ))}
      </div>

      <div className="relative mx-auto grid w-full flex-1 content-end px-5 pt-[92px] pb-9 lg:max-w-[1440px] lg:grid-cols-[56px_1fr] lg:px-14 lg:pt-32 lg:pb-12">
        <div className="mb-[26px] flex items-center gap-3 lg:mb-0 lg:flex-col lg:items-start lg:gap-3.5 lg:pt-2">
          <span className="font-mono text-[12px] tracking-[.18em] text-wheat">01</span>
          <span className="h-px w-7 bg-[rgb(244_239_229/.4)] lg:h-[72px] lg:w-px lg:bg-[rgb(244_239_229/.3)]" />
          <span className="whitespace-nowrap font-mono text-[10px] uppercase tracking-[.18em] text-[rgb(244_239_229/.62)] lg:[writing-mode:vertical-rl]">
            Self-help document preparation
          </span>
        </div>
        <div className="min-w-0">
          <h1 className="mb-9 text-[46px] leading-[47px] font-semibold tracking-[-0.042em] text-paper lg:text-[clamp(72px,7.2vw,104px)] lg:leading-[0.923]">
            <span className="block overflow-hidden">
              <Reveal as="span" gesture="lineup" trigger="load" delay={0.08} className="block">
                Your denial,
              </Reveal>
            </span>
            <span className="block overflow-hidden">
              <Reveal as="span" gesture="lineup" trigger="load" delay={0.2} className="block text-wheat">
                formally refuted.
              </Reveal>
            </span>
          </h1>
          <div className="grid items-end gap-[26px] lg:grid-cols-[minmax(0,560px)_1fr] lg:gap-14">
            <Reveal as="p" gesture="lift" trigger="load" delay={0.42} className="m-0 text-[16px] leading-7 text-[rgb(244_239_229/.78)] text-pretty lg:text-[17px] lg:leading-[29px]">
              Under two in a thousand people appeal a denied health claim. About half of the people who do appeal get the decision
              reversed. The gap is not courage. It is that nobody tells you which rules apply to you, or when your door closes.
            </Reveal>
            <Reveal gesture="lift" trigger="load" delay={0.54} className="flex flex-wrap gap-2.5 lg:justify-end">
              <Button variant="clay" asChild>
                <Link href="/triage/">Find my deadline — free</Link>
              </Button>
              <Button variant="heroGhost" asChild>
                <Link href="/cases/">See a worked case</Link>
              </Button>
            </Reveal>
          </div>
        </div>
      </div>

      <dl className="relative mx-auto grid w-full border-t border-[rgb(244_239_229/.16)] lg:max-w-[1440px] lg:grid-cols-3">
        {heroFacts.map((h, i) => (
          <Reveal
            key={h.k}
            gesture="lift"
            trigger="load"
            duration={0.7}
            delay={0.64 + i * 0.09}
            className={
              "flex flex-col gap-[7px] px-5 py-4 lg:px-7 lg:py-[22px] " +
              (i > 0 ? "border-t border-[rgb(244_239_229/.12)] lg:border-t-0 lg:border-l lg:border-l-[rgb(244_239_229/.16)]" : "")
            }
          >
            <dt className="font-mono text-[10px] uppercase tracking-[.18em] text-[rgb(169_189_178/.9)]">{h.k}</dt>
            <dd className="m-0 text-[15px] leading-[23px] font-medium text-band-ink">{h.v}</dd>
          </Reveal>
        ))}
      </dl>
    </section>
  );
}

// Promise strip — the only continuous motion on the page; reduced motion stops it.
export function Marquee() {
  return (
    <div className="overflow-hidden border-b border-rule bg-ground py-[13px] lg:py-[15px]">
      <div className="flex w-max animate-marquee">
        {[0, 1].map((pass) => (
          <div key={pass} className="flex" aria-hidden={pass === 1 || undefined}>
            {marquee.map((t, i) => (
              <span
                key={t}
                className={
                  "whitespace-nowrap border-r border-rule px-8 font-mono text-[11px] uppercase tracking-[.16em] " +
                  (i % 2 ? "text-clay-deep" : "text-ink-muted")
                }
              >
                {t}
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
