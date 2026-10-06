"use client";

import Link from "next/link";
import { useState } from "react";

import { DeadlineRing } from "@/components/deadline-ring";
import { Reveal } from "@/components/reveal";
import { StatusPill } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { Sheet, SheetClose, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { useCase } from "@/components/workspace/case-context";
import { PageHead, RuleQuote, card, label, well } from "@/components/workspace/shell";
import {
  Gated,
  LoadError,
  NeedsCase,
  Skeleton,
  UnverifiedBanner,
  Warnings,
} from "@/components/workspace/states";
import { ApiError, type RouteStep } from "@/lib/api";
import { useRoute } from "@/lib/hooks";
import { tone } from "@/lib/time";
import { cn } from "@/lib/utils";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

/** Days until a date. The only date arithmetic the frontend does. */
function daysUntil(iso: string): number {
  const due = new Date(iso);
  const today = new Date();
  due.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);
  return Math.round((due.getTime() - today.getTime()) / 86_400_000);
}

export default function RoadmapPage() {
  const { caseId } = useCase();
  const route = useRoute(caseId);
  const [open, setOpen] = useState<number | null>(null);

  if (!caseId) return <NeedsCase />;

  if (route.isPending) return <Skeleton rows={4} />;

  if (route.isError) {
    const notYet =
      route.error instanceof ApiError && route.error.code === "not_found";
    if (notYet) {
      return (
        <div>
          <PageHead
            title="Your route, and when each door closes"
            lead="We work this out from the facts you confirm, so every date comes with the rule it came from."
          />
          <Gated
            reason="We have not worked out your route yet. Confirm what we read from your denial letter and we will."
            href="/case/facts/"
            cta="Check what we read"
          />
        </div>
      );
    }
    return (
      <LoadError error={route.error} what="your route" onRetry={() => route.refetch()} />
    );
  }

  const determination = route.data;
  const next = determination.deadlines[0] ?? null;
  const steps = determination.steps;
  const detail = open !== null ? steps[open] : null;

  if (steps.length === 0) {
    return (
      <div>
        <PageHead
          title="Your route, and when each door closes"
          lead="We do not guess a track we cannot work out."
        />
        <Warnings warnings={determination.warnings} />
      </div>
    );
  }

  return (
    <div>
      <PageHead
        title="Your route, and when each door closes"
        lead={`You are at step one. Nothing after it starts until the step before it finishes, so there is only ever one thing to do next.`}
      />

      <UnverifiedBanner warnings={determination.warnings} />

      {/* ---- next thing due ---- */}
      {next ? (
        <div className={card}>
          <div className="flex flex-wrap items-center gap-5 px-[22px] py-5">
            <span className="lg:hidden">
              <DeadlineRing
                days={daysUntil(next.due_date)}
                total={next.count ?? 180}
                size={64}
              />
            </span>
            <span className="hidden lg:block">
              <DeadlineRing
                days={daysUntil(next.due_date)}
                total={next.count ?? 180}
                size={76}
              />
            </span>
            <div className="min-w-0 flex-1">
              <div className={cn(label, "mb-1.5")}>Next thing due</div>
              <div className="text-[21px] leading-7 font-semibold text-ink">
                {next.label} by {formatDate(next.due_date)}
              </div>
              <p className="mt-1.5 mb-0 text-pretty text-[15px] leading-6 text-ink-muted">
                We will remind you at 30, 14, 7, 3 and 1 days, and again the morning it
                is due.
              </p>
            </div>
            <Button variant="ghost" asChild>
              <Link href="/case/letter/">Open the draft</Link>
            </Button>
          </div>
        </div>
      ) : null}

      {/* ---- the steps ---- */}
      <div className="mt-7 mb-3.5 flex items-baseline gap-3.5">
        <span className={cn(label, "whitespace-nowrap")}>
          {steps.length === 1 ? "One step" : `${steps.length} steps`}
        </span>
        <span className="h-px flex-1 bg-rule" />
      </div>

      <ol className="m-0 flex list-none flex-col items-stretch gap-3.5 p-0 lg:flex-row lg:gap-4">
        {steps.map((step, i) => (
          <Reveal
            key={step.order}
            gesture="riseSm"
            trigger="load"
            delay={i * 0.08}
            className="flex-1"
          >
            <StepCard step={step} onOpen={() => setOpen(i)} current={i === 0} />
          </Reveal>
        ))}
      </ol>

      <Warnings warnings={determination.warnings} />

      <p className="mt-6 mb-0 font-mono text-[11px] tracking-[.05em] text-ink-muted">
        Rules current as of{" "}
        {determination.computed_at ? formatDate(determination.computed_at) : "today"} ·
        version {determination.rulebase_version}
      </p>

      {/* ---- the rule drawer ---- */}
      <Sheet open={open !== null} onOpenChange={(v) => !v && setOpen(null)}>
        <SheetContent>
          {detail ? <RuleDrawer step={detail} /> : null}
        </SheetContent>
      </Sheet>
    </div>
  );
}

function StepCard({
  step,
  onOpen,
  current,
}: {
  step: RouteStep;
  onOpen: () => void;
  current: boolean;
}) {
  const days = step.deadline ? daysUntil(step.deadline.due_date) : null;
  const t = days === null ? null : tone(days);

  return (
    <li
      className={cn(
        "flex h-full flex-col rounded-[16px] bg-surface p-[18px] lg:p-5",
        current ? "border-[1.5px] border-ink" : "border border-rule",
      )}
    >
      <div className="flex items-center gap-2.5">
        <span className="font-mono text-[11px] tracking-[.06em] text-ink-muted">
          {String(step.order).padStart(2, "0")}
        </span>
        <StatusPill>{step.who_files}</StatusPill>
      </div>

      <h3 className="mt-2.5 mb-0 text-[18px] leading-[25px] font-semibold text-ink">
        {step.label}
      </h3>

      {step.deadline && days !== null && t ? (
        <>
          <div className="mt-3 flex items-center gap-3.5">
            <DeadlineRing days={days} total={step.deadline.count ?? 180} size={48} />
            <div>
              <div className="tabular text-[17px] font-semibold text-ink">
                {formatDate(step.deadline.due_date)}
              </div>
              <div
                className="text-[14px]"
                style={{ color: t.color, fontWeight: t.weight }}
              >
                {days} days left · {t.word}
              </div>
            </div>
          </div>
          {step.deadline.ambiguous ? (
            <p className="mt-2.5 mb-0 border-l-[3px] border-time pl-2.5 text-[14px] leading-[21px] text-ink">
              This date is our more cautious reading. Open it to see why.
            </p>
          ) : null}
        </>
      ) : (
        <p className="mt-3 mb-0 text-pretty text-[15px] leading-[23px] text-ink-muted">
          Starts after step {step.starts_after ?? step.order - 1}. No date yet.
        </p>
      )}

      <p className="mt-3 mb-0 text-pretty text-[15px] leading-[23px] text-ink-muted">
        Decided by {step.review_body.toLowerCase()}.
      </p>

      <div className="mt-auto pt-4">
        <Button variant="ghost" onClick={onOpen} className="w-full">
          What this step needs
        </Button>
      </div>
    </li>
  );
}

function RuleDrawer({ step }: { step: RouteStep }) {
  const days = step.deadline ? daysUntil(step.deadline.due_date) : null;

  return (
    <div>
      <SheetTitle className="m-0 text-[15px] font-normal text-ink-muted">
        Step {String(step.order).padStart(2, "0")} · {step.label}
      </SheetTitle>

      {step.deadline ? (
        <>
          <div className="tabular mt-2 text-[30px] leading-[36px] font-semibold tracking-[-0.02em] text-ink">
            {formatDate(step.deadline.due_date)}
          </div>
          {days !== null ? (
            <div className="mt-1 text-[15px] text-ink-muted">
              {days} days from today
            </div>
          ) : null}

          <div className={cn(label, "mt-7 mb-2.5")}>HOW WE WORKED THAT OUT</div>
          <p className="m-0 text-pretty text-[16px] leading-[26px] text-ink">
            {step.deadline.count} {step.deadline.is_calendar_days ? "calendar" : ""}{" "}
            {step.deadline.trigger_description}. Counting from{" "}
            {formatDate(step.deadline.trigger_date)}.
          </p>

          {step.deadline.ambiguous && step.deadline.ambiguity_note ? (
            <div className="mt-3.5 border-l-[3px] border-time bg-surface-sunk px-3.5 py-3">
              <p className="m-0 text-pretty text-[15px] leading-[24px] text-ink">
                {step.deadline.ambiguity_note}
              </p>
            </div>
          ) : null}

          <div className={cn(label, "mt-7 mb-2.5")}>THE RULE</div>
          <RuleQuote>
            {step.deadline.citation.quote ??
              `${step.deadline.citation.source} ${step.deadline.citation.locator}${
                step.deadline.citation.title ? ` — ${step.deadline.citation.title}` : ""
              }`}
          </RuleQuote>
          <p className="mt-2.5 mb-0 font-mono text-[11px] text-ink-muted">
            {step.deadline.rule_id}
            {step.deadline.source_layer !== "federal"
              ? ` · ${step.deadline.source_layer.toUpperCase()} STATE LAW`
              : " · FEDERAL"}
            {step.deadline.citation.verified ? "" : " · UNVERIFIED"}
          </p>
          {step.deadline.citation.url ? (
            <a
              href={step.deadline.citation.url}
              target="_blank"
              rel="noreferrer"
              className="mt-2 inline-block text-[15px] text-clay-deep underline underline-offset-[3px]"
            >
              Read the regulation
            </a>
          ) : null}
        </>
      ) : (
        <>
          <div className="mt-2 text-[21px] leading-[28px] font-semibold text-ink">
            No date yet
          </div>
          <p className="mt-3 mb-0 text-pretty text-[16px] leading-[26px] text-ink">
            {step.pending_reason}
          </p>
        </>
      )}

      {step.required_elements.length > 0 ? (
        <>
          <div className={cn(label, "mt-7 mb-2.5")}>WHAT THIS FILING MUST INCLUDE</div>
          <ul className="m-0 flex list-none flex-col gap-3 p-0">
            {step.required_elements.map((element) => (
              <li key={element.key} className={well}>
                <div className="flex items-start gap-2.5">
                  <span
                    className="mt-1 font-mono text-[11px] text-ink-muted"
                    aria-hidden
                  >
                    {element.mandatory ? "●" : "◇"}
                  </span>
                  <div>
                    <div className="text-[16px] leading-[24px] font-medium text-ink">
                      {element.label}
                      {element.mandatory ? "" : " (optional)"}
                    </div>
                    {element.detail ? (
                      <p className="mt-1 mb-0 text-pretty text-[15px] leading-[23px] text-ink-muted">
                        {element.detail}
                      </p>
                    ) : null}
                    <p className="mt-1.5 mb-0 font-mono text-[11px] text-ink-muted">
                      {element.citation.source} {element.citation.locator}
                    </p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      <p className="mt-7 mb-0 border-t border-rule pt-4 text-pretty text-[14px] leading-[22px] text-ink">
        Deadlines are our best reading of your plan and the regulations. Check the date
        against your own letter before you rely on it.
      </p>

      <SheetClose asChild>
        <Button variant="ghost" className="mt-5 w-full">
          Close
        </Button>
      </SheetClose>
    </div>
  );
}
