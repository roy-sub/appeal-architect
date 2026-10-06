"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useEffect, useMemo } from "react";

import {
  ArgumentCard,
  TIER_MARKER,
  type Tier,
} from "@/components/domain/argument-node";
import {
  missingFor,
  reference,
  shortTitle,
  tierOf,
  visibleArguments,
} from "@/components/domain/argument-graph";
import { Button } from "@/components/ui/button";
import { useCase } from "@/components/workspace/case-context";
import { PageHead, card, label, well } from "@/components/workspace/shell";
import { Gated, LoadError, NeedsCase, Skeleton } from "@/components/workspace/states";
import { ApiError, type ArgumentGraph } from "@/lib/api";
import { useArgumentDetail, useArguments, useComputeArguments } from "@/lib/hooks";
import { cn } from "@/lib/utils";

/**
 * React Flow and dagre are ~70 kB, and only desktop renders the graph -- mobile
 * gets the stacked list, which is not a fallback but the better reading on a
 * phone. Loading it lazily keeps that weight off the device least able to
 * afford it, and off the first paint of every other screen.
 */
const ArgumentFlow = dynamic(
  () => import("@/components/domain/argument-graph").then((m) => m.ArgumentFlow),
  {
    ssr: false,
    loading: () => (
      <div
        className="h-[560px] rounded-[16px] border border-rule bg-surface-sunk"
        aria-busy="true"
      />
    ),
  },
);

/** The lane order. Their reason first, because it is what everything attacks. */
const LANES: { tier: Tier; heading: string }[] = [
  { tier: "insurer", heading: "What they said" },
  { tier: "solid", heading: "Solid ground" },
  { tier: "add", heading: "Worth adding" },
  { tier: "out", heading: "Left out" },
];

export default function ArgumentsPage() {
  const { caseId, node, setNode, pulse, clearPulse } = useCase();
  const graphQuery = useArguments(caseId);
  const compute = useComputeArguments(caseId);
  const detail = useArgumentDetail(caseId, node);

  // The pulse plays once, then clears.
  useEffect(() => {
    if (pulse.length === 0) return;
    const timer = setTimeout(clearPulse, 900);
    return () => clearTimeout(timer);
  }, [pulse, clearPulse]);

  if (!caseId) return <NeedsCase />;
  if (graphQuery.isPending) return <Skeleton rows={4} />;

  if (graphQuery.isError) {
    const notYet =
      graphQuery.error instanceof ApiError && graphQuery.error.code === "not_found";
    if (notYet) {
      return (
        <div>
          <PageHead
            title="What holds against their reason"
            lead="We treat the insurer's reason as an argument and work out which counter-arguments survive what they would say back."
          />
          <div className="flex flex-col gap-3.5">
            <Gated reason="We have not built your argument graph yet. It needs your confirmed facts." />
            <div>
              <Button
                onClick={() => compute.mutate()}
                disabled={compute.isPending}
              >
                {compute.isPending ? "Working it out…" : "Build the arguments"}
              </Button>
              {compute.isError ? (
                <div className="mt-3.5">
                  <LoadError error={compute.error} what="the arguments" />
                </div>
              ) : null}
            </div>
          </div>
        </div>
      );
    }
    return (
      <LoadError
        error={graphQuery.error}
        what="your arguments"
        onRetry={() => graphQuery.refetch()}
      />
    );
  }

  const { graph, tier_explanations: explanations } = graphQuery.data;
  const nodes = visibleArguments(graph);
  const byTier = (tier: Tier) => nodes.filter((n) => tierOf(graph, n.id) === tier);

  return (
    <div>
      <PageHead
        title="What holds against their reason"
        lead="Their reason sits at the top. Everything beneath it attacks it. We computed which of those survive what they would say back — we did not pick them."
      />

      {/* ---- desktop: the graph ---- */}
      <div className="hidden lg:block">
        <ArgumentFlow
          graph={graph}
          selected={node}
          pulse={pulse}
          onSelect={setNode}
        />
      </div>

      {/* ---- mobile: the lanes. Same data, easier to read on a phone. ---- */}
      <div className="flex flex-col gap-6 lg:hidden">
        {LANES.map(({ tier, heading }) => {
          const lane = byTier(tier);
          if (lane.length === 0) return null;
          return (
            <section key={tier}>
              <div
                className={cn(
                  "mb-3 flex items-baseline gap-2.5 border-t pt-2.5",
                  tier === "solid"
                    ? "border-standing"
                    : tier === "add"
                      ? "border-dashed border-ink-muted"
                      : tier === "out"
                        ? "border-defeated"
                        : "border-ink",
                )}
              >
                <span className="font-mono text-[12px] text-ink-muted" aria-hidden>
                  {TIER_MARKER[tier]}
                </span>
                <h2 className="m-0 text-[17px] leading-6 font-semibold text-ink">
                  {heading}
                </h2>
                <span className="font-mono text-[11px] text-ink-muted">
                  {lane.length}
                </span>
              </div>
              {tier !== "insurer" && explanations[heading] ? (
                <p className="mt-0 mb-3 text-pretty text-[15px] leading-[23px] text-ink-muted">
                  {explanations[heading]}
                </p>
              ) : null}
              <div className="flex flex-col gap-2.5">
                {lane.map((argument) => (
                  <div key={argument.id}>
                    <ArgumentCard
                      tier={tier}
                      reference={reference(argument.id)}
                      title={shortTitle(argument.claim)}
                      assertion={argument.claim}
                      needs={missingFor(argument)}
                      active={node === argument.id}
                      pulsing={pulse.includes(argument.id)}
                      onSelect={() => setNode(node === argument.id ? null : argument.id)}
                    />
                    {/* On mobile the active node expands in place. */}
                    {node === argument.id ? (
                      <div className="mt-2.5">
                        <Detail
                          detail={detail.data}
                          pending={detail.isPending}
                          graph={graph}
                        />
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </div>

      {/* ---- desktop: the detail panel beside the graph ---- */}
      <div className="mt-3.5 hidden lg:block">
        {node ? (
          <Detail detail={detail.data} pending={detail.isPending} graph={graph} />
        ) : (
          <div className={cn(card, "px-[22px] py-5")}>
            <p className="m-0 text-pretty text-[16px] leading-[26px] text-ink-muted">
              Choose an argument to see what it asserts, what evidence it needs, and
              what the insurer would likely say back.
            </p>
          </div>
        )}
      </div>

      {/* ---- the legend ---- */}
      <div className="mt-7 border-t border-rule pt-5">
        <div className={cn(label, "mb-3")}>HOW TO READ THIS</div>
        <dl className="m-0 grid gap-3 lg:grid-cols-3">
          {(["solid", "add", "out"] as Tier[]).map((tier) => {
            const heading = LANES.find((l) => l.tier === tier)!.heading;
            return (
              <div key={tier} className={well}>
                <dt className="flex items-center gap-2 text-[15px] font-semibold text-ink">
                  <span className="font-mono text-[12px]" aria-hidden>
                    {TIER_MARKER[tier]}
                  </span>
                  {heading}
                </dt>
                <dd className="m-0 mt-1.5 text-pretty text-[14px] leading-[22px] text-ink-muted">
                  {explanations[heading]}
                </dd>
              </div>
            );
          })}
        </dl>
        <p className="mt-4 mb-0 font-mono text-[11px] tracking-[.05em] text-ink-muted">
          SCHEMES VERSION {graph.schemes_version} · COMPUTED BY SOLVER, NOT ASSIGNED
        </p>
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button variant="ghost" asChild>
          <Link href="/case/evidence/">What evidence this needs</Link>
        </Button>
        <Button variant="ghost" asChild>
          <Link href="/case/letter/">See the letter</Link>
        </Button>
      </div>
    </div>
  );
}

function Detail({
  detail,
  pending,
  graph,
}: {
  detail: ReturnType<typeof useArgumentDetail>["data"];
  pending: boolean;
  graph: ArgumentGraph;
}) {
  const argument = useMemo(
    () => graph.arguments.find((a) => a.id === detail?.id) ?? null,
    [graph, detail],
  );

  if (pending) {
    return (
      <div className={cn(card, "px-[22px] py-5")} aria-busy="true">
        <div className="h-[15px] w-[40%] rounded-[2px] bg-surface-sunk" />
        <div className="mt-3 h-[13px] w-[70%] rounded-[2px] bg-surface-sunk" />
      </div>
    );
  }
  if (!detail) return null;

  return (
    <div className={cn(card, "px-[22px] py-5")}>
      <div className="flex flex-wrap items-center gap-2.5">
        <span className={label}>{reference(detail.id)}</span>
        {detail.tier ? (
          <span className="font-mono text-[11px] tracking-[.05em] text-ink-muted">
            {detail.tier.toUpperCase()}
          </span>
        ) : null}
      </div>

      <p className="mt-2.5 mb-0 text-pretty text-[17px] leading-[27px] text-ink">
        {detail.claim}
      </p>

      {/* ---- what it rests on ---- */}
      {detail.premises.length > 0 ? (
        <>
          <div className={cn(label, "mt-5 mb-2.5")}>WHAT IT RESTS ON</div>
          <ul className="m-0 flex list-none flex-col gap-2 p-0">
            {detail.premises.map((premise) => (
              <li key={premise.id} className="flex items-start gap-2.5">
                <span
                  className={cn(
                    "mt-1 font-mono text-[11px]",
                    premise.satisfied ? "text-standing" : "text-time",
                  )}
                  aria-hidden
                >
                  {premise.satisfied ? "●" : "○"}
                </span>
                <span className="text-[15px] leading-[23px] text-ink">
                  {premise.text}
                  {!premise.satisfied && premise.evidence_key ? (
                    <span className="block text-[14px] text-time">
                      Needs {premise.evidence_key.replace(/_/g, " ")}
                    </span>
                  ) : null}
                </span>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {/* ---- what they would say back ---- */}
      {detail.insurer_replies.length > 0 ? (
        <>
          <div className={cn(label, "mt-5 mb-2.5")}>WHAT THEY WOULD SAY BACK</div>
          <div className="flex flex-col gap-2.5">
            {detail.insurer_replies.map((reply) => (
              <div key={reply.id} className={well}>
                <p className="m-0 text-pretty text-[15px] leading-[23px] text-ink">
                  {reply.text}
                </p>
                <p
                  className={cn(
                    "mt-2 mb-0 text-[14px] leading-[21px] font-medium",
                    reply.answered ? "text-standing" : "text-ink",
                  )}
                >
                  {reply.verdict}
                </p>
              </div>
            ))}
          </div>
        </>
      ) : null}

      {/* ---- the verdict, as a sentence ---- */}
      <div className="mt-5 border-t border-rule pt-3.5">
        <div className={cn(label, "mb-1.5")}>WHERE THAT LEAVES IT</div>
        <p className="m-0 text-[16px] leading-[25px] font-medium text-ink">
          {detail.verdict}
        </p>
        <p className="mt-1.5 mb-0 text-pretty text-[15px] leading-[23px] text-ink-muted">
          {detail.tier_explanation}
        </p>
      </div>

      {detail.missing_evidence.length > 0 ? (
        <div className="mt-3.5 border-l-[3px] border-time pl-3.5">
          <p className="m-0 text-pretty text-[15px] leading-[23px] text-ink">
            This one needs{" "}
            {detail.missing_evidence.map((k) => k.replace(/_/g, " ")).join(", ")} to
            hold.
          </p>
          <Link
            href="/case/evidence/"
            className="mt-1.5 inline-block text-[15px] text-clay-deep underline underline-offset-[3px]"
          >
            Add it to the checklist
          </Link>
        </div>
      ) : null}

      {argument && argument.citations.length > 0 ? (
        <p className="mt-3.5 mb-0 font-mono text-[11px] text-ink-muted">
          {argument.citations
            .map((c) => `${c.source} ${c.locator}`.trim())
            .join(" · ")}
        </p>
      ) : null}
    </div>
  );
}
