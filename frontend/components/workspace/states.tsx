"use client";

/**
 * The loading, empty and error states every data surface needs.
 *
 * Three rules they all obey:
 *
 * - **No red, including errors.** An ink bar, full contrast, and an
 *   instruction rather than an apology.
 * - **A disabled control always states its reason** beside it.
 * - **Waiting shows named stages, not a spinner.** Extraction takes time, and
 *   "reading the letter" tells someone what is happening; a spinner tells them
 *   only that something is.
 */

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/lib/api";
import { cn } from "@/lib/utils";

const label = "font-mono text-[11px] tracking-[.06em] text-ink-muted";

export function Bar({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-l-[3px] border-ink bg-surface px-[18px] py-4">{children}</div>
  );
}

export function LoadError({
  error,
  onRetry,
  what,
}: {
  error: unknown;
  onRetry?: () => void;
  what: string;
}) {
  const problem = error instanceof ApiError ? error : null;
  const warming = problem?.code === "backend_warming";

  return (
    <Bar>
      <p className="m-0 text-[16px] leading-[26px] font-medium text-ink">
        {problem?.problem.title ?? `We could not load ${what}`}
      </p>
      <p className="mt-1.5 mb-0 text-[15px] leading-[24px] text-ink-muted text-pretty">
        {problem?.problem.detail ??
          "Check your connection and try again. Nothing you entered was lost."}
      </p>
      {onRetry ? (
        <Button variant="ghost" onClick={onRetry} className="mt-3.5">
          {warming ? "Try again" : "Reload"}
        </Button>
      ) : null}
    </Bar>
  );
}

export function NeedsCase() {
  return (
    <Bar>
      <p className="m-0 text-[16px] leading-[26px] text-ink">
        Open a case first. This screen shows one case at a time.
      </p>
      <Link
        href="/cases/"
        className="mt-3 inline-block text-[15px] text-clay-deep underline underline-offset-[3px]"
      >
        Go to your cases
      </Link>
    </Bar>
  );
}

export function Gated({ reason, href, cta }: { reason: string; href?: string; cta?: string }) {
  return (
    <Bar>
      <p className="m-0 text-[16px] leading-[26px] text-ink text-pretty">{reason}</p>
      {href && cta ? (
        <Link
          href={href}
          className="mt-3 inline-block text-[15px] text-clay-deep underline underline-offset-[3px]"
        >
          {cta}
        </Link>
      ) : null}
    </Bar>
  );
}

export function Skeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-3" aria-busy="true">
      {Array.from({ length: rows }, (_, i) => (
        <div
          key={i}
          className="rounded-[16px] border border-rule bg-surface px-[22px] py-5"
        >
          <div className="h-[16px] w-[38%] rounded-[2px] bg-surface-sunk" />
          <div className="mt-3 h-[13px] w-[64%] rounded-[2px] bg-surface-sunk" />
        </div>
      ))}
      <span className="sr-only">Loading</span>
    </div>
  );
}

/**
 * Named stages, replacing every spinner in the product.
 *
 * Reading a letter takes real time — a scanned page is transcribed a page at a
 * time — so the wait says what is happening. The reassurance that the page can
 * be closed matters: a caregiver on a phone should not feel pinned to it.
 */
export function Stages({
  stages,
  active,
  note,
}: {
  stages: string[];
  active: number;
  note?: string;
}) {
  return (
    <div className="rounded-[16px] border border-rule bg-surface px-[22px] py-6">
      <div className={cn(label, "mb-4")}>Working</div>
      <ol className="m-0 flex list-none flex-col gap-3.5 p-0">
        {stages.map((stage, i) => {
          const complete = i < active;
          const current = i === active;
          return (
            <li key={stage} className="flex items-center gap-3.5">
              <span
                className={cn(
                  "grid size-5 shrink-0 place-items-center rounded-full border",
                  complete
                    ? "border-standing bg-standing"
                    : current
                      ? "border-standing"
                      : "border-rule",
                )}
                aria-hidden
              >
                {complete ? (
                  <span className="text-[11px] leading-none text-surface">●</span>
                ) : null}
              </span>
              <span
                className={cn(
                  "text-[16px] leading-[25px]",
                  current ? "font-medium text-ink" : complete ? "text-ink" : "text-ink-muted",
                )}
              >
                {stage}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="mt-5 mb-0 border-t border-rule pt-4 text-[14px] leading-[22px] text-ink-muted text-pretty">
        {note ??
          "You can close this page. We will email you when it is ready, and the case keeps its place."}
      </p>
    </div>
  );
}

/** A banner for a route determination resting on unverified legal values. */
export function UnverifiedBanner({ warnings }: { warnings: string[] }) {
  const unverified = warnings.filter((w) => w.startsWith("UNVERIFIED"));
  if (unverified.length === 0) return null;
  return (
    <div className="mb-5 border-l-[3px] border-time bg-surface px-[18px] py-4">
      <div className={cn(label, "mb-2")}>BEFORE YOU RELY ON THESE DATES</div>
      {unverified.map((warning) => (
        <p
          key={warning}
          className="m-0 text-[15px] leading-[24px] text-ink text-pretty"
        >
          {warning.replace(/^UNVERIFIED:\s*/, "")}
        </p>
      ))}
    </div>
  );
}

/** Everything the engine flagged, other than the unverified banner. */
export function Warnings({ warnings }: { warnings: string[] }) {
  const rest = warnings.filter((w) => !w.startsWith("UNVERIFIED"));
  if (rest.length === 0) return null;
  return (
    <div className="mt-5 rounded-[2px] border border-rule bg-surface-sunk px-[18px] py-4">
      <div className={cn(label, "mb-2.5")}>WORTH KNOWING</div>
      <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
        {rest.map((warning) => (
          <li key={warning} className="text-[15px] leading-[24px] text-ink text-pretty">
            {warning}
          </li>
        ))}
      </ul>
    </div>
  );
}
