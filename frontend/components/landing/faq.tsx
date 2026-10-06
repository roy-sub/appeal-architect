"use client";
import { Accordion, AccordionContent, AccordionHeader, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Reveal } from "@/components/reveal";
import { faqs } from "@/lib/landing-content";

// 07 — each row's hairline unrolls from the left; the open row turns clay.
export function Faq() {
  return (
    <section id="faq" className="mx-auto scroll-mt-[60px] px-5 pb-16 lg:max-w-[1440px] lg:scroll-mt-[72px] lg:px-14 lg:pb-28">
      <div className="mb-7 grid lg:mb-12 lg:grid-cols-[56px_1fr] lg:gap-x-8">
        <span className="mb-[18px] block font-mono text-[11px] tracking-[.18em] text-clay-deep lg:mb-0">07</span>
        <h2 className="m-0 max-w-[470px] text-[30px] leading-[37px] font-semibold tracking-[-0.028em] text-ink text-pretty lg:text-[40px] lg:leading-[46px]">
          The things worth knowing before you start.
        </h2>
      </div>
      <Accordion type="single" collapsible className="flex w-full flex-col">
        {faqs.map((f, i) => (
          <AccordionItem key={f.q} value={String(i)} className="group relative w-full">
            <Reveal
              as="span"
              gesture="drawRight"
              duration={0.62}
              delay={Math.min(i, 5) * 0.1}
              className="absolute inset-x-0 top-0 h-px origin-left bg-rule group-data-[state=open]:bg-clay"
            />
            <AccordionHeader className="m-0">
              <AccordionTrigger className="grid min-h-16 w-full grid-cols-[32px_1fr_28px] items-baseline gap-x-2 py-[22px] text-left lg:grid-cols-[56px_1fr_28px] lg:gap-x-8 lg:py-7">
                <span className="font-mono text-[11px] tracking-[.14em] text-ink-muted group-data-[state=open]:text-clay-deep">{String(i + 1).padStart(2, "0")}</span>
                <span className="text-[18px] leading-[27px] font-semibold tracking-[-0.015em] text-ink lg:text-[21px] lg:leading-[30px]">{f.q}</span>
                <span aria-hidden className="justify-self-end font-mono text-[18px] text-ink-muted group-data-[state=open]:text-clay">
                  <span className="group-data-[state=open]:hidden">+</span>
                  <span className="hidden group-data-[state=open]:inline">−</span>
                </span>
              </AccordionTrigger>
            </AccordionHeader>
            <AccordionContent className="grid pb-[26px] lg:grid-cols-[56px_1fr] lg:gap-x-8 lg:pb-[34px]">
              <p className="m-0 max-w-[680px] text-[16px] leading-[29px] text-ink-muted text-pretty lg:col-start-2 lg:text-[17px]">{f.a}</p>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </section>
  );
}
