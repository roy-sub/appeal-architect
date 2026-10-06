"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { StatusPill } from "@/components/status-pill";
import { CaseProvider } from "@/components/workspace/case-context";
import { cn } from "@/lib/utils";

const rail = [
  ["/cases/", "Case file"],
  ["/case/documents/", "Documents"],
  ["/case/facts/", "Extracted facts"],
  ["/case/roadmap/", "Roadmap"],
  ["/case/arguments/", "Arguments"],
  ["/case/evidence/", "Evidence"],
  ["/case/letter/", "Letter"],
] as const;

const mobileBar = [
  ["/cases/", "Case"],
  ["/case/roadmap/", "Route"],
  ["/case/arguments/", "Argument"],
  ["/case/evidence/", "Evidence"],
  ["/case/letter/", "Letter"],
] as const;

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const isActive = (href: string) => path === href || path + "/" === href;

  return (
    <CaseProvider>
    <div className="flex min-h-dvh flex-col bg-ground lg:flex-row">
      <nav aria-label="Case" className="sticky top-0 hidden h-dvh w-[252px] shrink-0 flex-col gap-1 self-start border-r border-rule bg-ground px-4 py-[22px] lg:flex">
        <Link href="/" className="flex items-center gap-2 px-3 pt-1 pb-[18px] font-mono text-[11px] font-medium uppercase tracking-[.14em] text-ink no-underline">
          Appeal&nbsp;Architect
        </Link>
        {rail.map(([href, name]) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-h-11 w-full items-center gap-2.5 rounded-[8px] border px-3 py-2.5 text-left text-[15px] no-underline",
                active ? "border-rule bg-surface font-medium text-ink" : "border-transparent bg-transparent text-ink-muted hover:text-ink",
              )}
            >
              <span className={cn("size-[5px] shrink-0 rounded-full", active ? "bg-ink" : "bg-rule")} />
              <span>{name}</span>
            </Link>
          );
        })}
        <div className="mt-auto border-t border-rule pt-4 font-mono text-[11px] leading-[17px] text-ink-muted">
          Rules current as of 5 Oct 2026
          <br />
          version 2026.10.1
        </div>
      </nav>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex flex-wrap items-center justify-between gap-4 border-b border-rule bg-ground px-5 py-3.5 lg:px-8 lg:py-[18px]">
          <div className="min-w-0">
            <h2 className="m-0 text-[17px] leading-6 font-semibold text-ink lg:text-[19px] lg:leading-[26px]">Anthem Blue Cross · infliximab infusion</h2>
            <div className="mt-[3px] font-mono text-[11px] tracking-[.04em] text-ink-muted">CLM-4471902 · denied 14 Sep 2026 · CO-50</div>
          </div>
          <StatusPill kind="ink">22 Mar 2027 · 168 days</StatusPill>
        </header>
        <main className="flex-1 px-5 pt-5 pb-8 lg:px-8 lg:pt-7 lg:pb-12">{children}</main>
      </div>

      <nav
        aria-label="Case sections"
        className="no-print sticky bottom-0 z-20 flex gap-0.5 border-t border-rule bg-surface px-1.5 pt-1 pb-[max(4px,env(safe-area-inset-bottom))] lg:hidden"
      >
        {mobileBar.map(([href, name]) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn("flex min-h-[52px] flex-1 flex-col items-center justify-center gap-1 text-[11px] no-underline", active ? "font-semibold text-ink" : "text-ink-muted")}
            >
              <span className={cn("h-0.5 w-4", active ? "bg-ink" : "bg-transparent")} />
              <span>{name}</span>
            </Link>
          );
        })}
      </nav>
    </div>
    </CaseProvider>
  );
}

// Shared workspace atoms.
export const card = "rounded-[16px] border border-rule bg-surface";
export const label = "font-mono text-[11px] tracking-[.06em] text-ink-muted";
export const well = "rounded-[2px] border border-rule bg-surface-sunk p-3.5 lg:px-[18px] lg:py-4";
export const stack = "flex flex-col gap-3 lg:gap-3.5";

export function PageHead({ title, lead, action }: { title: string; lead: string; action?: React.ReactNode }) {
  const head = (
    <div className="min-w-0">
      <h1 className="mt-0 mb-2.5 text-[27px] leading-[33px] font-semibold tracking-[-0.015em] text-ink lg:text-[36px] lg:leading-[42px]">{title}</h1>
      <p className="mt-0 mb-7 max-w-[68ch] text-[17px] leading-7 text-ink-muted text-pretty lg:text-[18px] lg:leading-[29px]">{lead}</p>
    </div>
  );
  if (!action) return head;
  return (
    <div className="mb-[22px] flex flex-wrap items-start justify-between gap-5">
      {head}
      {action}
    </div>
  );
}

export function RuleQuote({ children }: { children: React.ReactNode }) {
  return (
    <blockquote className="m-0 border-l-[1.5px] border-ink py-0.5 pl-4 font-doc text-[17px] leading-[29px] italic text-ink">{children}</blockquote>
  );
}

export function Bullets({ items }: { items: string[] }) {
  return (
    <ul className="m-0 flex list-none flex-col gap-[11px] p-0">
      {items.map((t) => (
        <li key={t} className="flex items-start gap-2.5 text-[15px] leading-[23px] text-ink">
          <span className="mt-2 size-[7px] shrink-0 bg-ink" />
          <span>{t}</span>
        </li>
      ))}
    </ul>
  );
}
