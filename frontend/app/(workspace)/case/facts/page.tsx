"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { useCase } from "@/components/workspace/case-context";
import { PageHead, card, label, well } from "@/components/workspace/shell";
import { Gated, LoadError, NeedsCase, Skeleton } from "@/components/workspace/states";
import type { ExtractedFact } from "@/lib/api";
import {
  useComputeRoute,
  useDocumentText,
  useDocuments,
  useFactAction,
  useFacts,
} from "@/lib/hooks";
import { cn } from "@/lib/utils";

/** Human labels for the fields the extractor proposes. */
const FIELD_LABELS: Record<string, string> = {
  insurer_name: "Insurer",
  claim_number: "Claim number",
  member_id_present: "Member ID on the letter",
  denial_date: "Date on the letter",
  denial_received_date: "Date it reached you",
  service_date: "Date of service",
  service_timing: "Has the treatment happened",
  plan_type: "Kind of plan",
  state: "State",
  denial_reasons: "Reason given",
  cited_policy_language: "Policy language quoted",
  claim_amount_usd: "Amount in dispute",
};

const STATUS_COPY: Record<ExtractedFact["status"], { pill: string; bar: string }> = {
  pending: { pill: "Needs a look", bar: "border-time" },
  confirmed: { pill: "Confirmed", bar: "border-standing" },
  edited: { pill: "Edited by you", bar: "border-standing" },
  rejected: { pill: "Rejected", bar: "border-defeated" },
};

function fieldLabel(field: string): string {
  return FIELD_LABELS[field] ?? field.replace(/_/g, " ");
}

function displayValue(fact: ExtractedFact): string {
  const raw = fact.status === "edited" ? fact.edited_value : fact.value;
  if (raw === null || raw === undefined || raw === "") return "—";
  return String(raw);
}

export default function FactsPage() {
  const { caseId } = useCase();
  const facts = useFacts(caseId);
  const documents = useDocuments(caseId);
  const actions = useFactAction(caseId);
  const computeRoute = useComputeRoute(caseId);

  const [selected, setSelected] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState("");

  const documentId = documents.data?.[0]?.id ?? null;
  const text = useDocumentText(caseId, documentId);

  const selectedFact = useMemo(
    () => facts.data?.facts.find((f) => f.id === selected) ?? null,
    [facts.data, selected],
  );

  /** The sentence a proposal came from, sliced out of the stored text.
   *  These are real character offsets, so this is the actual source. */
  const sourceSentence = useMemo(() => {
    if (!selectedFact || !text.data) return null;
    const { source_start: start, source_end: end } = selectedFact;
    if (start === null || end === null) return null;
    const body = text.data.text;
    // Widen to sentence boundaries so the quote reads naturally.
    let from = start;
    while (from > 0 && !".\n".includes(body[from - 1])) from -= 1;
    let to = end;
    while (to < body.length && !".\n".includes(body[to])) to += 1;
    return {
      before: body.slice(from, start),
      match: body.slice(start, end),
      after: body.slice(end, Math.min(to + 1, body.length)),
    };
  }, [selectedFact, text.data]);

  if (!caseId) return <NeedsCase />;

  const pending = facts.data?.pending_required ?? [];
  const ready = facts.data?.ready_for_route ?? false;

  return (
    <div>
      <PageHead
        title="Check what we read"
        lead="Each line is what the model read, next to the sentence it came from. Nothing is worked out until you have confirmed or corrected every one. Getting one wrong here is normal — correct it."
      />

      {facts.isPending ? (
        <Skeleton rows={4} />
      ) : facts.isError ? (
        <LoadError
          error={facts.error}
          what="the extracted facts"
          onRetry={() => facts.refetch()}
        />
      ) : facts.data.facts.length === 0 ? (
        <Gated
          reason="There is nothing to check yet. Upload the denial letter and we will read it."
          href="/case/documents/"
          cta="Add a denial letter"
        />
      ) : (
        <div className="grid gap-3.5 lg:grid-cols-[1fr_380px] lg:items-start">
          {/* ---- the proposals ---- */}
          <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
            {facts.data.facts.map((fact) => {
              const status = STATUS_COPY[fact.status];
              const isEditing = editing === fact.id;
              const low = fact.confidence < 0.65;

              return (
                <li
                  key={fact.id}
                  className={cn(
                    "border-l-[3px] bg-surface",
                    status.bar,
                    // Square on the source side, rounded on the app side: the
                    // whole metaphor in one shape.
                    "rounded-[2px_10px_10px_2px] border-y border-r border-rule",
                    selected === fact.id && "ring-2 ring-focus",
                  )}
                >
                  <button
                    type="button"
                    onClick={() => setSelected(fact.id === selected ? null : fact.id)}
                    className="flex w-full flex-col items-start gap-1 bg-transparent px-[18px] py-4 text-left"
                  >
                    <span className="flex w-full flex-wrap items-center gap-2.5">
                      <span className={label}>{fieldLabel(fact.field).toUpperCase()}</span>
                      <span className="ml-auto font-mono text-[11px] tracking-[.05em] text-ink-muted">
                        {status.pill}
                      </span>
                    </span>
                    {!isEditing ? (
                      <span className="text-[18px] leading-[26px] font-medium text-ink">
                        {displayValue(fact)}
                      </span>
                    ) : null}
                    {low && !isEditing ? (
                      <span className="text-[14px] leading-[22px] text-time">
                        The scan is unclear here. Worth reading twice.
                      </span>
                    ) : null}
                    {fact.source_start === null && !isEditing ? (
                      <span className="text-[14px] leading-[22px] text-time">
                        We could not find this on the page. Check it against your letter.
                      </span>
                    ) : null}
                  </button>

                  {isEditing ? (
                    <div className="px-[18px] pb-4">
                      <label htmlFor={`edit-${fact.id}`} className={cn(label, "block mb-2")}>
                        CORRECT IT
                      </label>
                      <input
                        id={`edit-${fact.id}`}
                        value={draft}
                        onChange={(e) => setDraft(e.target.value)}
                        className="min-h-[46px] w-full rounded-[6px] border-[1.5px] border-ink bg-surface px-3.5 text-[17px] text-ink outline-none"
                      />
                      <div className="mt-3 flex gap-2.5">
                        <Button
                          variant="small"
                          disabled={actions.edit.isPending}
                          onClick={() => {
                            actions.edit.mutate(
                              { factId: fact.id, value: draft },
                              { onSuccess: () => setEditing(null) },
                            );
                          }}
                        >
                          Save
                        </Button>
                        <Button variant="ghost" onClick={() => setEditing(null)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : fact.status === "pending" ? (
                    <div className="flex flex-wrap gap-2.5 px-[18px] pb-4">
                      <Button
                        variant="small"
                        disabled={actions.confirm.isPending}
                        onClick={() => actions.confirm.mutate(fact.id)}
                      >
                        That is right
                      </Button>
                      <Button
                        variant="ghost"
                        onClick={() => {
                          setEditing(fact.id);
                          setDraft(displayValue(fact) === "—" ? "" : displayValue(fact));
                        }}
                      >
                        Correct it
                      </Button>
                      <Button
                        variant="ghost"
                        disabled={actions.reject.isPending}
                        onClick={() => actions.reject.mutate(fact.id)}
                      >
                        Not in the letter
                      </Button>
                    </div>
                  ) : null}
                </li>
              );
            })}
          </ul>

          {/* ---- the source, for the selected proposal ---- */}
          <aside className="lg:sticky lg:top-[88px]">
            <div className={cn(card, "p-5")}>
              <div className={cn(label, "mb-3")}>Where it came from</div>
              {!selectedFact ? (
                <p className="m-0 text-[15px] leading-[24px] text-ink-muted text-pretty">
                  Choose a line on the left and the sentence it came from appears here.
                </p>
              ) : text.isPending ? (
                <p className="m-0 text-[15px] text-ink-muted">Loading the document…</p>
              ) : sourceSentence ? (
                <blockquote className={cn(well, "m-0 border-l-[1.5px] border-l-ink")}>
                  <p className="m-0 font-doc text-[17px] leading-[28px] italic text-ink">
                    {sourceSentence.before}
                    <mark className="bg-wheat not-italic">{sourceSentence.match}</mark>
                    {sourceSentence.after}
                  </p>
                </blockquote>
              ) : (
                <p className="m-0 text-[15px] leading-[24px] text-ink text-pretty">
                  We could not locate this on the page, so there is nothing to show you.
                  Check it against your own letter before you confirm it.
                </p>
              )}
              {selectedFact ? (
                <p className="mt-3 mb-0 font-mono text-[11px] text-ink-muted">
                  {selectedFact.source_page !== null
                    ? `PAGE ${selectedFact.source_page}`
                    : "PAGE UNKNOWN"}
                  {" · CONFIDENCE "}
                  {Math.round(selectedFact.confidence * 100)}%
                </p>
              ) : null}
            </div>
          </aside>
        </div>
      )}

      {/* ---- the gate ---- */}
      {facts.data && facts.data.facts.length > 0 ? (
        <div className="mt-7 border-t border-rule pt-5">
          <Button
            disabled={!ready || computeRoute.isPending}
            onClick={() => computeRoute.mutate()}
          >
            {computeRoute.isPending ? "Working it out…" : "Build my roadmap"}
          </Button>
          {/* A disabled button always has its reason stated beside it. */}
          {!ready ? (
            <p className="mt-2.5 mb-0 max-w-[60ch] text-pretty text-[15px] leading-[24px] text-ink-muted">
              {pending.length === 1
                ? `We still need one thing before we can work out your deadlines: ${fieldLabel(pending[0])}.`
                : `We still need ${pending.length} things before we can work out your deadlines: ${pending
                    .map(fieldLabel)
                    .join(", ")}.`}{" "}
              Confirm them above, or add them on the case.
            </p>
          ) : null}
          {computeRoute.isError ? (
            <div className="mt-3.5">
              <LoadError error={computeRoute.error} what="your route" />
            </div>
          ) : null}
          {computeRoute.isSuccess ? (
            <div className="mt-3.5 border-l-[3px] border-standing bg-surface px-[18px] py-4">
              <p className="m-0 text-[16px] leading-[26px] text-ink">
                Your route is worked out, with the rule behind every date.
              </p>
              <Button asChild className="mt-3.5">
                <Link href="/case/roadmap/">See your roadmap</Link>
              </Button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
