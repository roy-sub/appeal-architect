"use client";
import { useState } from "react";
import { StatusPill, type PillKind } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { useCase } from "@/components/workspace/case-context";
import { PageHead, card, label, stack } from "@/components/workspace/shell";
import { doctorPoints, evidence, type EvState } from "@/lib/case-data";
import { cn } from "@/lib/utils";

const stMap: Record<EvState, [string, PillKind]> = {
  have: ["On file", "solid"], missing: ["Not yet", "plain"], progress: ["Requested", "plain"], optional: ["Optional", "add"],
};

export default function EvidencePage() {
  const { evidenceState: state, setEvidence } = useCase();
  const [copied, setCopied] = useState(false);
  const onFile = Object.values(state).filter((s) => s === "have").length;

  return (
    <div>
      <PageHead
        title="What to gather"
        lead={`Eight items. Each one says which argument needs it, so nothing here is padding. ${onFile === 6 ? "Six are" : `${onFile} ${onFile === 1 ? "is" : "are"}`} already on file.`}
      />
      <div className="grid items-start gap-5 lg:grid-cols-[1fr_340px] lg:gap-7">
        <div className={cn("min-w-0", stack)}>
          {evidence.map((e) => {
            const st = state[e.id];
            const have = st === "have";
            return (
              <div key={e.id} className={cn(card, "flex items-start gap-3.5 p-4 transition-opacity lg:px-5 lg:py-[18px]", have && "opacity-[.78]")}>
                <button
                  role="checkbox"
                  aria-checked={have}
                  aria-label={`${e.t}: mark as on file`}
                  onClick={() => setEvidence(e.id, have ? "missing" : "have")}
                  className="-m-[13px] flex size-11 shrink-0 items-center justify-center"
                >
                  <span
                    className={cn(
                      "mt-[3px] size-[18px] rounded-[2px] border-[1.5px]",
                      st === "optional" ? "border-dashed" : "border-solid",
                      have ? "border-standing bg-standing" : "border-rule bg-transparent",
                    )}
                  />
                </button>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-start justify-between gap-2.5">
                    <div className="min-w-0 text-[17px] leading-[25px] font-semibold text-ink">{e.t}</div>
                    <StatusPill kind={stMap[st][1]}>{stMap[st][0]}</StatusPill>
                  </div>
                  <p className="mt-1.5 mb-0 text-[15px] leading-[23px] text-ink-muted text-pretty">{e.how}</p>
                  <div className="mt-2.5 border-t border-rule pt-[9px] font-mono text-[11px] tracking-[.04em] text-ink-muted">Supports {e.why}</div>
                </div>
              </div>
            );
          })}
        </div>
        <div className={card}>
          <div className="p-[22px]">
            <div className={cn(label, "mb-3")}>Physician letter · what it has to say</div>
            <p className="mt-0 mb-4 text-[15px] leading-6 text-ink-muted text-pretty">
              Give these four points to the treating doctor. The letter has to be in their own words, on their letterhead, signed and dated.
            </p>
            <ol className="m-0 flex list-none flex-col gap-3 p-0">
              {doctorPoints.map((t, i) => (
                <li key={t} className="flex items-start gap-[11px]">
                  <span className="mt-[3px] shrink-0 font-mono text-[12px] text-ink-muted">0{i + 1}</span>
                  <span className="text-[15px] leading-6 text-ink">{t}</span>
                </li>
              ))}
            </ol>
            <div className="mt-5 flex flex-wrap gap-2.5">
              <Button
                variant="inkSmall"
                onClick={async () => {
                  try {
                    await navigator.clipboard.writeText(doctorPoints.map((t, i) => `${i + 1}. ${t}`).join("\n"));
                    setCopied(true);
                  } catch {}
                }}
              >
                {copied ? "Copied" : "Copy these points"}
              </Button>
              <Button variant="small">Download template</Button>
            </div>
            <p className="mt-[18px] mb-0 border-t border-rule pt-4 text-[14px] leading-[22px] text-ink-muted">
              We do not write this letter for the doctor. A reviewer can tell when a physician letter was not written by a physician.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
