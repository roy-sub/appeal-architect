import Link from "next/link";

import { Button } from "@/components/ui/button";
import { DISCLAIMER } from "@/lib/site";

export const metadata = {
  title: "Pricing — Appeal Architect",
  description:
    "Your route, your deadlines and the rule behind each one are free. The letter is the paid part.",
};

const label = "font-mono text-[11px] tracking-[.06em] text-ink-muted";

const TIERS = [
  {
    name: "Free check",
    price: "£0",
    sub: "No account",
    lead: "Four questions, and an honest answer about where you stand.",
    includes: [
      "The appeal track your plan puts you on",
      "Your likely deadline, with the regulation that sets it",
      "An honest answer about whether appealing is worth it",
    ],
    cta: { href: "/triage/", text: "Run the free check" },
    variant: "ghost" as const,
  },
  {
    name: "Appeal Package",
    price: "£39",
    sub: "One case, one payment",
    lead: "Everything needed to file one appeal properly.",
    includes: [
      "Your denial letter read, with every fact shown next to its source",
      "Your full route and every deadline, each with its citation",
      "The argument graph: what holds, what is worth adding, what does not",
      "The evidence checklist, and what your doctor needs to write",
      "The appeal letter, every paragraph traceable to an argument",
      "PDF and Word export, and deadline reminders by email",
    ],
    cta: { href: "/signin/", text: "Start a case" },
    variant: "primary" as const,
    featured: true,
  },
  {
    name: "Subscription",
    price: "£12",
    sub: "Per month, cases unlimited",
    lead: "For anyone dealing with this more than once.",
    includes: [
      "Everything in the Appeal Package, for every case",
      "External review when an internal appeal is refused",
      "A running timeline of every case you have open",
      "Cancel whenever. Your deadlines and letters stay available.",
    ],
    cta: { href: "/signin/", text: "Start a subscription" },
    variant: "ghost" as const,
  },
];

export default function PricingPage() {
  return (
    <div className="min-h-dvh bg-ground">
      <header className="border-b border-rule">
        <div className="mx-auto flex h-[60px] items-center justify-between px-5 lg:h-[72px] lg:max-w-[1440px] lg:px-14">
          <Link
            href="/"
            className="font-mono text-[12px] font-medium uppercase tracking-[.14em] text-ink no-underline"
          >
            Appeal&nbsp;Architect
          </Link>
          <Link href="/triage/" className="text-[15px] text-clay-deep">
            Free check
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-[1180px] px-5 py-12 lg:px-14 lg:py-[88px]">
        <div className={label}>PRICING</div>
        <h1 className="mt-3.5 mb-3 max-w-[22ch] text-[32px] leading-[40px] font-semibold tracking-[-0.02em] text-ink lg:text-[46px] lg:leading-[54px]">
          Your deadline is never the paid part.
        </h1>
        <p className="mt-0 mb-10 max-w-[62ch] text-pretty text-[18px] leading-[29px] text-ink-muted">
          Finding out you have fourteen days left is the single most useful thing this
          product does, so it is free and it stays free. What you pay for is the work
          product: the letter, written from the arguments that hold.
        </p>

        <div className="grid gap-3.5 lg:grid-cols-3">
          {TIERS.map((tier) => (
            <section
              key={tier.name}
              className={
                tier.featured
                  ? "flex flex-col rounded-[2px] border-[1.5px] border-ink bg-surface p-6"
                  : "flex flex-col rounded-[2px] border border-rule bg-surface p-6"
              }
            >
              <div className={label}>{tier.name.toUpperCase()}</div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="tabular text-[38px] leading-none font-semibold tracking-[-0.02em] text-ink">
                  {tier.price}
                </span>
                <span className="text-[15px] text-ink-muted">{tier.sub}</span>
              </div>
              <p className="mt-3 mb-5 text-pretty text-[16px] leading-[25px] text-ink-muted">
                {tier.lead}
              </p>
              <ul className="m-0 mb-6 flex list-none flex-col gap-2.5 p-0">
                {tier.includes.map((item) => (
                  <li
                    key={item}
                    className="flex gap-2.5 text-pretty text-[15px] leading-[23px] text-ink"
                  >
                    <span className="mt-[7px] size-1.5 shrink-0 rounded-full bg-forest" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
              <Button variant={tier.variant} asChild className="mt-auto w-full">
                <Link href={tier.cta.href}>{tier.cta.text}</Link>
              </Button>
            </section>
          ))}
        </div>

        <div className="mt-8 border-l-[3px] border-ink bg-surface px-5 py-5">
          <div className={label}>IF YOU CANNOT PAY</div>
          <p className="mt-2.5 mb-0 max-w-[72ch] text-pretty text-[16px] leading-[26px] text-ink">
            Run the free check, open a case, upload your letter and confirm the facts.
            You will see your route, every deadline and the rule behind each one without
            paying anything, and we will email you before each deadline. If you then
            write the letter yourself, you will have everything you need to write a good
            one. That is not a trick to get you to pay — it is what we think a product
            about missed deadlines owes you.
          </p>
        </div>

        <p className="mt-10 mb-0 border-t border-rule pt-5 text-pretty text-[14px] leading-[23px] text-ink">
          {DISCLAIMER}
        </p>
      </main>
    </div>
  );
}
