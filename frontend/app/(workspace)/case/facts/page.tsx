"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { MediaSlot } from "@/components/media-slot";
import { StatusPill, type PillKind } from "@/components/status-pill";
import { Button } from "@/components/ui/button";
import { PageHead, RuleQuote, card, label, well } from "@/components/workspace/shell";
import { extractionStages, facts, type FactState } from "@/lib/case-data";
import { cn } from "@/lib/utils";

const stLabel: Record<FactState, string> = { confirmed: "Confirmed", edited: "Edited by you", rejected: "Rejected", pending: "Needs a look" };
const stPill: Record<FactState, PillKind> = { confirmed: "solid", edited: "solid", pending: "plain", rejected: "out" };
const confLabel = { high: "Clear in the scan", medium: "Readable, worth checking", low: "The scan is unclear here" };
const barColor: Record<FactState, string> = { confirmed: "var(--standing)", edited: "var(--standing)", rejected: "var(--defeated)", pending: "var(--time)" };

export default function FactsPage() {
  const [extracting, setExtracting] = useState(false);
  const [state, setState] = useState<Record<string, FactState>>(() => Object.fromEntries(facts.map((f) => [f.id, f.st])));
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(facts.map((f) => [f.id, f.v])));
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [selected, setSelected] = useState("f4");
  const [stage, setStage] = useState(0);
  const sel = facts.find((f) => f.id === selected) ?? facts[0];

  // Demo pacing for the named stages. Real stages advance on real events (motion.md).
  useEffect(() => {
    if (!extracting) return;
    setStage(0);
    const iv = setInterval(() => setStage((s) => (s >= extractionStages.length ? s : s + 1)), 1400);
    return () => clearInterval(iv);
  }, [extracting]);

  const confirmed = facts.filter((f) => state[f.id] === "confirmed" || state[f.id] === "edited").length;
  const outstanding = facts.filter((f) => state[f.id] === "pending").length;
  const set = (id: string, st: FactState) => { setState({ ...state, [id]: st }); setEditing(null); };

  return (
    <div>
      <PageHead
        title="What we read in your letter"
        lead="Each fact sits next to the sentence it came from. Confirm it, correct it, or reject it. Two need your eyes."
        action={<Button variant="ghost" onClick={() => setExtracting(!extracting)}>{extracting ? "Show the review" : "Show it working"}</Button>}
      />

      {extracting ? (
        <div className="max-w-[560px]">
          <div className={card}>
            <div className="px-6 py-[26px]" aria-live="polite">
              <div className={cn(label, "mb-[18px]")}>Working through it — about 40 seconds</div>
              {extractionStages.map((t, i) => (
                <div key={t} className="flex items-center gap-3.5 border-b border-rule py-[13px]">
                  <span
                    className={cn("size-2.5 shrink-0 rounded-full border-[1.5px]", i <= stage ? "border-standing" : "border-rule", i < stage ? "bg-standing" : "bg-transparent")}
                  />
                  <span className={cn("text-[17px]", i <= stage ? "text-ink" : "text-ink-muted opacity-55", i === stage && "font-medium")}>{t}</span>
                  {i < stage && <span className="sr-only">done</span>}
                </div>
              ))}
              {stage >= extractionStages.length && (
                <p className="mt-5 mb-0 text-[15px] leading-6 font-medium text-ink">Done. Your facts are ready to review.</p>
              )}
              <p className="mt-5 mb-0 text-[15px] leading-6 text-ink-muted">You can close this page. We will email you when it is ready, and the case keeps its place.</p>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div className="grid items-start gap-5 lg:grid-cols-2 lg:gap-6">
            <div className="flex min-w-0 flex-col gap-3">
              {facts.map((f) => {
                const st = state[f.id];
                const isEditing = editing === f.id;
                return (
                  <div
                    key={f.id}
                    onClick={() => setSelected(f.id)}
                    className={cn(
                      "rounded-[2px_10px_10px_2px] border border-l-[3px] bg-surface px-[18px] py-4",
                      selected === f.id ? "border-ink-muted" : "border-rule",
                    )}
                    style={{ borderLeftColor: barColor[st] }}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="font-mono text-[11px] tracking-[.05em] text-ink-muted">{f.k}</div>
                        {isEditing ? (
                          <div className="mt-2">
                            <input
                              aria-label={`Correct ${f.k}`}
                              value={draft}
                              onChange={(e) => setDraft(e.target.value)}
                              className="min-h-[46px] w-full rounded-[6px] border-[1.5px] border-ink bg-surface px-[13px] py-[11px] text-[16px] text-ink"
                              autoFocus
                            />
                            <div className="mt-2.5 flex gap-2">
                              <Button variant="inkSmall" onClick={() => { setValues({ ...values, [f.id]: draft }); set(f.id, "edited"); }}>Save correction</Button>
                              <Button variant="small" onClick={() => setEditing(null)}>Cancel</Button>
                            </div>
                          </div>
                        ) : (
                          <div className="mt-[3px] text-[17px] leading-[26px] font-medium text-ink">{values[f.id]}</div>
                        )}
                      </div>
                      <StatusPill kind={stPill[st]}>{stLabel[st]}</StatusPill>
                    </div>
                    <div className="mt-3 flex flex-wrap items-center gap-3 border-t border-rule pt-3">
                      <span className="font-mono text-[11px] text-ink-muted">{f.span}</span>
                      <span className={cn("font-mono text-[11px]", f.conf === "low" ? "text-time" : "text-ink-muted")}>{confLabel[f.conf]}</span>
                      <span className="flex-1" />
                      {!isEditing && (
                        <div className="flex gap-2">
                          <Button variant="small" onClick={() => set(f.id, "confirmed")}>Confirm</Button>
                          <Button variant="small" onClick={() => { setDraft(values[f.id]); setEditing(f.id); }}>Correct</Button>
                          <Button variant="small" onClick={() => set(f.id, "rejected")}>Not in the letter</Button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className={cn(card, "static p-5 lg:sticky lg:top-24 lg:p-7")}>
              <div className="mb-3.5 flex items-center justify-between gap-3">
                <span className={label}>Your letter · page {sel.span.match(/page (\d)/)?.[1] ?? 1} of 3</span>
                <div className="flex gap-1.5">
                  {[1, 2, 3].map((n) => <Button key={n} variant="small" aria-label={`Page ${n}`}>{n}</Button>)}
                </div>
              </div>
              <MediaSlot slotId="doc-scan" ratio="17 / 22" kind="image" label="Page one of the denial letter, with the extracted spans highlighted" intrinsic="1700×2200" />
              <div className={cn(well, "mt-0")}>
                <div className="mb-2 font-mono text-[11px] tracking-[.05em] text-ink-muted">
                  {sel.span.charAt(0).toUpperCase() + sel.span.slice(1)} · {sel.k}
                </div>
                <RuleQuote>{sel.quote}</RuleQuote>
              </div>
              <p className="mt-4 mb-0 text-[14px] leading-[22px] text-ink-muted">Tap a fact to jump to its place on the page. Tap a highlight to see the fact it produced.</p>
            </div>
          </div>
          <div className="sticky bottom-[64px] mt-5 flex flex-wrap items-center justify-between gap-4 rounded-[12px] border border-rule bg-surface px-[18px] py-3.5 shadow-e2 lg:bottom-0">
            <div className="flex min-w-0 flex-wrap items-center gap-3.5">
              <div className="h-[3px] w-[180px] overflow-hidden rounded-[2px] bg-rule">
                <div className="h-full bg-ink transition-[width] duration-[260ms]" style={{ width: `${(confirmed / facts.length) * 100}%` }} />
              </div>
              <span className="text-[15px] text-ink">
                {confirmed} of {facts.length} facts confirmed{outstanding > 0 ? ` · ${outstanding} still need${outstanding === 1 ? "s" : ""} you` : ""}
              </span>
            </div>
            {outstanding > 0 ? (
              <div className="flex flex-wrap items-center gap-3">
                <span id="roadmap-reason" className="text-[14px] text-ink-muted">Confirm, correct or reject the last {outstanding === 1 ? "fact" : `${outstanding} facts`} first.</span>
                <Button disabled aria-describedby="roadmap-reason">Build my roadmap</Button>
              </div>
            ) : (
              <Button asChild><Link href="/case/roadmap/">Build my roadmap</Link></Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
