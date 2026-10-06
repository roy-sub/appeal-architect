"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useMemo } from "react";

import { DeadlineRing } from "@/components/deadline-ring";
import { MediaSlot } from "@/components/media-slot";
import { Reveal } from "@/components/reveal";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { NotConfigured } from "@/components/workspace/not-configured";
import { PageHead, card, stack } from "@/components/workspace/shell";
import { ApiError, api, type CaseSummary } from "@/lib/api";
import { caseKeys } from "@/lib/query-keys";
import { supabaseConfigured } from "@/lib/supabase";
import { tone } from "@/lib/time";
import { cn } from "@/lib/utils";

/** Days until a date, from today. The only date arithmetic the frontend does —
 *  every deadline itself is computed server-side and sent as a date. */
function daysUntil(iso: string): number {
  const due = new Date(iso);
  const today = new Date();
  due.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  return Math.round((due.getTime() - today.getTime()) / 86_400_000);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

const STAGE_LABELS: Record<CaseSummary["stage"], string> = {
  uploaded: "Letter uploaded",
  extracted: "Checking what we read",
  confirmed: "Facts confirmed",
  routed: "Route worked out",
  arguing: "Building the argument",
  evidence: "Gathering evidence",
  letter_ready: "Letter ready",
  sent: "Appeal sent",
  responded: "They answered",
  escalated: "External review",
  resolved: "Closed",
};

export default function CasesPage() {
  const query = useQuery({
    queryKey: caseKeys.list(),
    queryFn: api.listCases,
    enabled: supabaseConfigured,
  });

  const lead = useMemo(() => {
    const count = query.data?.length ?? 0;
    if (!query.isSuccess) return "Sorted by how soon each one needs you, not by when you added it.";
    if (count === 0) return "Nothing here yet. Start with the denial letter.";
    return `${count === 1 ? "One open" : `${count} open`}. Sorted by how soon each one needs you, not by when you added it.`;
  }, [query.isSuccess, query.data]);

  return (
    <div>
      <PageHead title="Your cases" lead={lead} />

      {!supabaseConfigured ? (
        <NotConfigured what="Your case list" />
      ) : query.isPending ? (
        <CaseListSkeleton />
      ) : query.isError ? (
        <LoadFailed error={query.error} onRetry={() => query.refetch()} />
      ) : query.data.length === 0 ? (
        <EmptyCases />
      ) : (
        <div className={stack}>
          {query.data.map((item, i) => (
            <Reveal key={item.id} gesture="riseSm" trigger="load" delay={i * 0.05}>
              <CaseRow item={item} />
            </Reveal>
          ))}
          <Link
            href="/case/documents/"
            className="flex min-h-16 items-center rounded-[16px] border-[1.5px] border-dashed border-rule bg-transparent p-5 text-left text-[16px] text-ink-muted no-underline hover:border-ink-muted"
          >
            Add another case
          </Link>
        </div>
      )}
    </div>
  );
}

function CaseRow({ item }: { item: CaseSummary }) {
  const days = item.next_deadline ? daysUntil(item.next_deadline) : null;
  const t = days === null ? null : tone(days);

  return (
    <Link
      href="/case/roadmap/"
      className={cn(
        card,
        "flex w-full flex-col items-stretch gap-4 p-[18px] text-left no-underline transition-colors hover:border-ink-muted lg:flex-row lg:items-center lg:gap-6 lg:px-6 lg:py-[22px]",
      )}
    >
      {days !== null ? (
        <>
          {/* The ring total is the filing window the engine used, so the arc
              shows elapsed proportion of the real window. Until the route is
              computed there is no window, so there is no ring. */}
          <span className="lg:hidden">
            <DeadlineRing days={days} total={180} size={56} />
          </span>
          <span className="hidden lg:block">
            <DeadlineRing days={days} total={180} size={64} />
          </span>
        </>
      ) : null}

      <div className="min-w-0 flex-1">
        <div className="text-[18px] leading-[26px] font-semibold text-ink">
          {item.insurer_name ?? item.title}
        </div>
        {item.insurer_name ? (
          <div className="mt-0.5 text-[15px] leading-[23px] text-ink-muted">{item.title}</div>
        ) : null}
        <div className="mt-3 flex flex-wrap gap-2">
          <StatusPill>{STAGE_LABELS[item.stage]}</StatusPill>
          {item.claim_number ? <StatusPill>{item.claim_number}</StatusPill> : null}
        </div>
      </div>

      <div className="shrink-0 text-left">
        <div className="font-mono text-[11px] tracking-[.05em] text-ink-muted">NEXT DEADLINE</div>
        {item.next_deadline && days !== null && t ? (
          <>
            <div className="tabular mt-1 text-[18px] font-semibold text-ink">
              {formatDate(item.next_deadline)}
            </div>
            <div className="text-[14px]" style={{ color: t.color, fontWeight: t.weight }}>
              {days} days left · {t.word}
            </div>
          </>
        ) : (
          // Honest rather than reassuring: we do not know the deadline until the
          // facts are confirmed and the engine has run.
          <div className="mt-1 max-w-[22ch] text-[15px] leading-[23px] text-ink-muted">
            Not known yet. Confirm the facts and we work it out.
          </div>
        )}
      </div>
    </Link>
  );
}

function EmptyCases() {
  return (
    <div className="flex flex-col items-center gap-4 rounded-[16px] border-[1.5px] border-dashed border-rule bg-surface px-7 py-12 text-center">
      <div className="w-[120px]">
        <MediaSlot
          slotId="empty-cases"
          ratio="4 / 3"
          kind="illustration"
          label="A closed folder resting on a desk"
          intrinsic="640×480"
          className="p-2 [&_div]:text-[9px]"
        />
      </div>
      <h2 className="m-0 text-[21px] leading-7 font-semibold text-ink">No cases yet</h2>
      <p className="m-0 max-w-[44ch] text-pretty text-[16px] leading-[26px] text-ink-muted">
        Start with the denial letter. Photograph every page, or drop the PDF. We read it and
        tell you what your deadline is before you pay anything.
      </p>
      <Button asChild>
        <Link href="/case/documents/">Add a denial letter</Link>
      </Button>
    </div>
  );
}

function CaseListSkeleton() {
  return (
    <div className={stack} aria-busy="true">
      {[0, 1, 2].map((i) => (
        <div key={i} className={cn(card, "flex items-center gap-6 px-6 py-[22px]")}>
          <div className="size-[64px] shrink-0 rounded-full bg-surface-sunk" />
          <div className="flex-1">
            <div className="h-[18px] w-[40%] rounded-[2px] bg-surface-sunk" />
            <div className="mt-2.5 h-[14px] w-[62%] rounded-[2px] bg-surface-sunk" />
          </div>
        </div>
      ))}
      <span className="sr-only">Loading your cases</span>
    </div>
  );
}

function LoadFailed({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const warming = error instanceof ApiError && error.code === "backend_warming";
  const problem = error instanceof ApiError ? error : null;

  return (
    // No red, including errors: an ink bar plus an instruction.
    <div className="border-l-[3px] border-ink bg-surface px-5 py-4">
      <p className="m-0 text-[16px] leading-[26px] font-medium text-ink">
        {problem?.problem.title ?? "We could not load your cases"}
      </p>
      <p className="mt-1.5 mb-0 text-[15px] leading-[24px] text-ink-muted">
        {problem?.problem.detail ?? "Check your connection and try again. Nothing was lost."}
      </p>
      <Button variant="ghost" onClick={onRetry} className="mt-3.5">
        {warming ? "Try again" : "Reload"}
      </Button>
    </div>
  );
}
