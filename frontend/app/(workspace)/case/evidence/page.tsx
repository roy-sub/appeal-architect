"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useCase } from "@/components/workspace/case-context";
import { PageHead, card, label } from "@/components/workspace/shell";
import { Gated, LoadError, NeedsCase, Skeleton } from "@/components/workspace/states";
import { ApiError, type EvidenceItem } from "@/lib/api";
import { useArguments, useAttachEvidence, useEvidence } from "@/lib/hooks";
import { cn } from "@/lib/utils";

/** The four points a physician letter has to make for this kind of case. */
const PHYSICIAN_POINTS = [
  "What the condition is, and what the records show about how it has progressed.",
  "Why this treatment is the clinically appropriate one for it.",
  "Which covered alternatives were tried or ruled out, and on what grounds.",
  "What happens clinically if the treatment is delayed, and over what timeframe.",
];

const STATUS_PILL: Record<EvidenceItem["status"], string> = {
  have: "On file",
  missing: "Not yet",
  requested: "Requested",
  optional: "Optional",
};

export default function EvidencePage() {
  const { caseId, queuePulse, setNode } = useCase();
  const evidence = useEvidence(caseId);
  const graphQuery = useArguments(caseId);
  const attach = useAttachEvidence(caseId);

  if (!caseId) return <NeedsCase />;
  if (evidence.isPending) return <Skeleton rows={4} />;

  if (evidence.isError) {
    const notYet =
      evidence.error instanceof ApiError && evidence.error.code === "not_found";
    if (notYet) {
      return (
        <div>
          <PageHead
            title="What your arguments need"
            lead="This list comes from the arguments that hold, so every item is here because something specific depends on it."
          />
          <Gated
            reason="The checklist is derived from your arguments, and we have not built those yet."
            href="/case/arguments/"
            cta="Build the arguments"
          />
        </div>
      );
    }
    return (
      <LoadError
        error={evidence.error}
        what="your evidence checklist"
        onRetry={() => evidence.refetch()}
      />
    );
  }

  const items = evidence.data;
  const have = items.filter((i) => i.status === "have").length;
  const unlocking = items.filter(
    (i) => i.status !== "have" && (i.why_needed ?? "").includes("solid ground"),
  );

  return (
    <div>
      <PageHead
        title="What your arguments need"
        lead={
          items.length === 0
            ? "Nothing is needed yet."
            : `${have} of ${items.length} on file. Every item is here because a specific argument depends on it — nothing is busywork.`
        }
      />

      {/* ---- what would change the most ---- */}
      {unlocking.length > 0 ? (
        <div className="mb-3.5 border-l-[3px] border-standing bg-surface px-[18px] py-4">
          <div className={cn(label, "mb-2")}>START HERE</div>
          <p className="m-0 text-pretty text-[16px] leading-[26px] text-ink">
            {unlocking.length === 1
              ? `${unlocking[0].label} is the one that closes off the insurer's likely answer. Adding it moves an argument onto solid ground.`
              : `${unlocking.length} of these close off the insurer's likely answers. Each one moves an argument onto solid ground.`}
          </p>
        </div>
      ) : null}

      {items.length === 0 ? (
        <Gated reason="Once your arguments are built, this fills in with exactly what each one needs." />
      ) : (
        <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
          {items.map((item) => (
            <li
              key={item.key}
              className={cn(
                card,
                "px-[18px] py-4",
                item.status === "have" && "opacity-[.78]",
                item.status === "optional" && "border-dashed",
              )}
            >
              <div className="flex flex-wrap items-start gap-3.5">
                {/* 18px visual box inside a 44px hit area. */}
                <button
                  type="button"
                  aria-label={
                    item.status === "have"
                      ? `${item.label} is on file`
                      : `Mark ${item.label} as on file`
                  }
                  disabled={item.status === "have" || attach.isPending}
                  onClick={() => {
                    attach.mutate(
                      { key: item.key },
                      {
                        onSuccess: () => {
                          // The argument nodes this item feeds pulse once.
                          queuePulse(item.argument_node_ids);
                        },
                      },
                    );
                  }}
                  className="grid size-11 shrink-0 place-items-center bg-transparent"
                >
                  <span
                    className={cn(
                      "grid size-[18px] place-items-center border-[1.5px]",
                      item.status === "have"
                        ? "border-standing bg-standing"
                        : item.status === "optional"
                          ? "border-dashed border-ink-muted"
                          : "border-ink",
                    )}
                    aria-hidden
                  >
                    {item.status === "have" ? (
                      <span className="text-[10px] leading-none text-surface">●</span>
                    ) : null}
                  </span>
                </button>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="text-[17px] leading-[25px] font-medium text-ink">
                      {item.label}
                    </span>
                    <span className="font-mono text-[11px] tracking-[.05em] text-ink-muted">
                      {STATUS_PILL[item.status]}
                    </span>
                  </div>

                  {item.why_needed ? (
                    <p className="mt-1 mb-0 text-pretty text-[15px] leading-[23px] text-ink-muted">
                      {item.why_needed}
                    </p>
                  ) : null}

                  {item.argument_node_ids.length > 0 ? (
                    <div className="mt-2.5 flex flex-wrap items-center gap-2 border-t border-rule pt-2.5">
                      <span className="font-mono text-[11px] text-ink-muted">
                        SUPPORTS
                      </span>
                      {item.argument_node_ids.map((id) => (
                        <Link
                          key={id}
                          href="/case/arguments/"
                          onClick={() => setNode(id)}
                          className="font-mono text-[11px] text-clay-deep underline underline-offset-[3px]"
                        >
                          {id}
                        </Link>
                      ))}
                    </div>
                  ) : null}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {attach.isError ? (
        <div className="mt-3.5">
          <LoadError error={attach.error} what="that update" />
        </div>
      ) : null}

      {/* ---- the physician letter ---- */}
      <div className="mt-8">
        <div className="mb-3.5 flex items-baseline gap-3.5">
          <span className={cn(label, "whitespace-nowrap")}>The physician letter</span>
          <span className="h-px flex-1 bg-rule" />
        </div>
        <div className={cn(card, "px-[22px] py-5")}>
          <p className="mt-0 mb-4 text-pretty text-[16px] leading-[26px] text-ink">
            If you ask your doctor for one thing, ask for this. For your case it needs
            to make four specific points.
          </p>
          <ol className="m-0 flex list-none flex-col gap-3 p-0">
            {PHYSICIAN_POINTS.map((point, i) => (
              <li key={point} className="flex gap-3">
                <span className="font-mono text-[11px] leading-[22px] text-ink-muted">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span className="text-pretty text-[15px] leading-[23px] text-ink">
                  {point}
                </span>
              </li>
            ))}
          </ol>
          <div className="mt-5 flex flex-wrap gap-3">
            <Button
              variant="ghost"
              onClick={() => {
                void navigator.clipboard?.writeText(
                  PHYSICIAN_POINTS.map((p, i) => `${i + 1}. ${p}`).join("\n"),
                );
              }}
            >
              Copy these points
            </Button>
          </div>
          <p className="mt-4 mb-0 border-t border-rule pt-3.5 text-pretty text-[14px] leading-[22px] text-ink">
            We do not write this letter for the doctor. A reviewer can tell when a
            physician letter was not written by a physician.
          </p>
        </div>
      </div>

      {graphQuery.data ? (
        <div className="mt-6">
          <Button variant="ghost" asChild>
            <Link href="/case/arguments/">Back to the arguments</Link>
          </Button>
        </div>
      ) : null}
    </div>
  );
}
