"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useCase } from "@/components/workspace/case-context";
import { PageHead, card, label } from "@/components/workspace/shell";
import { Gated, LoadError, NeedsCase, Skeleton } from "@/components/workspace/states";
import { useCase as useCaseData, useEscalate, useTimeline } from "@/lib/hooks";
import { cn } from "@/lib/utils";

/** Plain-language names for the event kinds the backend logs. */
const EVENT_LABELS: Record<string, string> = {
  case_opened: "You opened this case",
  case_updated: "You changed the case details",
  document_uploaded: "You uploaded a document and we read it",
  fact_confirmed: "You confirmed a fact",
  fact_edited: "You corrected a fact",
  fact_rejected: "You rejected a proposed fact",
  route_computed: "We worked out your route and deadlines",
  arguments_computed: "We built your argument graph",
  evidence_attached: "You added evidence",
  letter_generated: "We wrote your appeal letter",
  letter_edited: "You edited the letter",
  letter_exported: "You exported the letter",
  escalated: "You recorded the insurer's final answer",
};

function formatWhen(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function TimelinePage() {
  const { caseId } = useCase();
  const timeline = useTimeline(caseId);
  const caseData = useCaseData(caseId);
  const escalate = useEscalate(caseId);
  const [finalDate, setFinalDate] = useState("");

  if (!caseId) return <NeedsCase />;

  return (
    <div>
      <PageHead
        title="Everything that happened"
        lead="The record of what was uploaded, confirmed, computed and sent, and when. This is the one you may need later."
      />

      {/* ---- escalation ---- */}
      {caseData.data && !caseData.data.final_adverse_date ? (
        <section className={cn(card, "mb-3.5 px-[22px] py-5")}>
          <div className={cn(label, "mb-3")}>IF THEY REFUSE AGAIN</div>
          <p className="mt-0 mb-4 text-pretty text-[16px] leading-[26px] text-ink">
            When the insurer answers your internal appeal and refuses it, record the
            date on their final letter. That is the date the external-review clock
            counts from, and until we have it we will not put a date on that step.
          </p>
          <label htmlFor="final-date" className={cn(label, "block mb-2")}>
            DATE ON THEIR FINAL ANSWER
          </label>
          <input
            id="final-date"
            type="date"
            value={finalDate}
            onChange={(e) => setFinalDate(e.target.value)}
            className="min-h-[46px] rounded-[6px] border-[1.5px] border-ink bg-surface px-3.5 text-[17px] text-ink outline-none"
          />
          <div className="mt-3.5">
            <Button
              disabled={!finalDate || escalate.isPending}
              onClick={() => escalate.mutate(finalDate)}
            >
              {escalate.isPending ? "Working it out…" : "Record it and date the next step"}
            </Button>
            {!finalDate ? (
              <p className="mt-2.5 mb-0 text-[15px] leading-[24px] text-ink-muted">
                Enter the date printed on their final letter.
              </p>
            ) : null}
          </div>
          {escalate.isError ? (
            <div className="mt-3.5">
              <LoadError error={escalate.error} what="that date" />
            </div>
          ) : null}
        </section>
      ) : caseData.data?.final_adverse_date ? (
        <div className="mb-3.5 border-l-[3px] border-standing bg-surface px-[18px] py-4">
          <p className="m-0 text-[16px] leading-[26px] text-ink">
            Their final answer is recorded as{" "}
            {new Date(caseData.data.final_adverse_date).toLocaleDateString("en-GB", {
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
            , so the external-review step now has a real deadline on your roadmap.
          </p>
        </div>
      ) : null}

      {timeline.isPending ? (
        <Skeleton rows={4} />
      ) : timeline.isError ? (
        <LoadError
          error={timeline.error}
          what="your timeline"
          onRetry={() => timeline.refetch()}
        />
      ) : timeline.data.length === 0 ? (
        <Gated reason="Nothing has happened on this case yet." />
      ) : (
        <ol className="m-0 flex list-none flex-col p-0">
          {timeline.data.map((event, i) => (
            <li key={event.id} className="flex gap-4">
              {/* The spine: a hairline with a node per event. */}
              <span className="relative flex w-3 shrink-0 justify-center" aria-hidden>
                <span
                  className={cn(
                    "absolute top-0 bottom-0 w-px bg-rule",
                    i === 0 && "top-2.5",
                    i === timeline.data.length - 1 && "bottom-auto h-2.5",
                  )}
                />
                <span className="relative mt-2 size-2 rounded-full bg-forest" />
              </span>
              <div className="min-w-0 flex-1 pb-6">
                <div className="text-[16px] leading-[24px] text-ink">
                  {EVENT_LABELS[event.kind] ?? event.kind.replace(/_/g, " ")}
                </div>
                <div className="tabular mt-0.5 font-mono text-[11px] text-ink-muted">
                  {formatWhen(event.created_at)}
                </div>
                {Object.keys(event.detail).length > 0 ? (
                  <div className="mt-1.5 font-mono text-[12px] leading-[20px] text-ink-muted">
                    {Object.entries(event.detail)
                      .map(([key, value]) => `${key.replace(/_/g, " ")}: ${String(value)}`)
                      .join(" · ")}
                  </div>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
