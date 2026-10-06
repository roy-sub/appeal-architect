"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { Reveal } from "@/components/reveal";
import { Button } from "@/components/ui/button";
import { ApiError, type TriageResponse } from "@/lib/api";
import { useTriage, useTriageOptions } from "@/lib/hooks";
import { cn } from "@/lib/utils";
import { tone } from "@/lib/time";

const label = "font-mono text-[11px] tracking-[.06em] text-ink-muted";
const card = "rounded-[16px] border border-rule bg-surface";
const pageTitle =
  "mt-0 mb-2.5 text-[27px] leading-[33px] font-semibold tracking-[-0.015em] text-ink lg:text-[36px] lg:leading-[42px]";

/** The four questions. Options come from the API so they cannot drift from
 *  what the engine accepts. */
type Answers = {
  plan_type?: string;
  denial_reason?: string;
  denial_date?: string | null;
  service_timing?: string;
};

/** Date buckets, resolved to a representative date for the estimate.
 *  The exact date comes from the letter once it is uploaded. */
const DATE_BUCKETS: { label: string; days: number | null }[] = [
  { label: "Within the last week", days: 3 },
  { label: "One to four weeks ago", days: 18 },
  { label: "One to three months ago", days: 60 },
  { label: "More than three months ago", days: 120 },
  { label: "I cannot find a date", days: null },
];

function dateFromBucket(days: number | null): string | null {
  if (days === null) return null;
  const when = new Date();
  when.setDate(when.getDate() - days);
  return when.toISOString().slice(0, 10);
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

export default function TriagePage() {
  const options = useTriageOptions();
  const triage = useTriage();

  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [result, setResult] = useState<TriageResponse | null>(null);

  const questions = useMemo(() => {
    const planTypes = options.data?.plan_types ?? [];
    const reasons = options.data?.denial_reasons ?? [];
    const timings = options.data?.service_timings ?? [];
    return [
      {
        key: "plan_type" as const,
        q: "Where does your health insurance come from?",
        help: "This decides which rulebook you are under, and that changes every deadline.",
        opts: planTypes.map((o) => ({ label: o.label, value: o.value })),
      },
      {
        key: "denial_reason" as const,
        q: "What reason does the letter give?",
        help: "It is usually one line near the top, often with a code beside it.",
        opts: reasons.map((o) => ({ label: o.label, value: o.value })),
      },
      {
        key: "denial_date" as const,
        q: "What date is on the letter?",
        help: "Most deadlines count from this date, not from when you opened it.",
        opts: DATE_BUCKETS.map((b) => ({
          label: b.label,
          value: dateFromBucket(b.days) ?? "",
        })),
      },
      {
        key: "service_timing" as const,
        q: "Has the treatment already happened?",
        help: "Claims before treatment and claims after treatment run on different clocks.",
        opts: timings.map((o) => ({ label: o.label, value: o.value })),
      },
    ];
  }, [options.data]);

  const done = result !== null;
  const current = questions[Math.min(step, questions.length - 1)];

  async function answer(value: string) {
    const next: Answers = { ...answers, [current.key]: value || null };
    setAnswers(next);

    if (step + 1 < questions.length) {
      setStep(step + 1);
      return;
    }

    // Last question answered: run the real engine.
    try {
      const response = await triage.mutateAsync({
        plan_type: next.plan_type ?? "unknown",
        // Not asked: a state mandate cannot shorten the federal window, so the
        // free check does not need it. The full case does.
        state: "CA",
        denial_date: next.denial_date ?? null,
        service_timing: next.service_timing ?? "post",
        denial_reason: next.denial_reason ?? "other",
      });
      setResult(response);
      setStep(questions.length);
    } catch {
      // The error surfaces from triage.error below.
    }
  }

  const outputs = [
    {
      t: "Which appeal track you are on",
      d: "The rulebook that governs your plan",
      done: step >= 1,
    },
    { t: "Your likely deadline", d: "With the regulation that sets it", done: step >= 3 },
    {
      t: "Whether appealing is worth it",
      d: "Honestly, including when it is not",
      done: step >= 4,
    },
  ];

  return (
    <div className="min-h-dvh bg-ground">
      <header className="sticky top-0 z-40 border-b border-rule bg-ground">
        <div className="mx-auto flex h-[60px] items-center justify-between gap-6 px-5 lg:h-[72px] lg:max-w-[1440px] lg:px-14">
          <Link
            href="/"
            className="font-mono text-[12px] font-medium uppercase tracking-[.14em] text-ink no-underline"
          >
            Appeal&nbsp;Architect
          </Link>
          <span className="font-mono text-[11px] tracking-[.05em] text-ink-muted">
            Free check · no account
          </span>
        </div>
      </header>

      <main className="mx-auto px-5 py-12 lg:max-w-[1280px] lg:px-20 lg:py-[88px]">
        <div className="grid items-start lg:grid-cols-[1fr_360px] lg:gap-8">
          <div className="min-w-0 max-w-[640px]" aria-live="polite">
            {done && result ? (
              <Verdict result={result} />
            ) : (
              <div>
                <div className={cn(label, "mb-3.5")}>
                  Question {Math.min(step + 1, questions.length)} of {questions.length}
                </div>
                <h1 className={pageTitle}>{current.q}</h1>
                <p className="mt-0 mb-7 text-[17px] leading-[27px] text-ink-muted text-pretty">
                  {current.help}
                </p>

                {options.isPending ? (
                  <div className="flex flex-col gap-2.5" aria-busy="true">
                    {[0, 1, 2, 3].map((i) => (
                      <div key={i} className="h-[60px] rounded-[10px] bg-surface-sunk" />
                    ))}
                  </div>
                ) : options.isError ? (
                  <Unreachable />
                ) : (
                  <div className="flex flex-col gap-2.5">
                    {current.opts.map((opt) => (
                      <button
                        key={opt.label}
                        type="button"
                        onClick={() => answer(opt.value)}
                        disabled={triage.isPending}
                        className="flex min-h-[60px] items-center gap-3.5 rounded-[10px] border border-rule bg-surface px-[18px] text-left text-[17px] leading-[25px] text-ink transition-colors hover:border-ink-muted disabled:opacity-45"
                      >
                        <span className="size-4 shrink-0 border border-ink-muted" />
                        {opt.label}
                      </button>
                    ))}
                  </div>
                )}

                {triage.isPending ? (
                  <p className="mt-5 mb-0 text-[15px] text-ink-muted">
                    Working out your track…
                  </p>
                ) : null}

                {triage.isError ? (
                  <div className="mt-5 border-l-[3px] border-ink bg-surface px-4 py-3.5">
                    <p className="m-0 text-[16px] leading-[26px] text-ink">
                      {triage.error instanceof ApiError
                        ? triage.error.problem.detail
                        : "We could not run the check just now. Try again in a moment."}
                    </p>
                  </div>
                ) : null}

                {step > 0 ? (
                  <Button
                    variant="ghost"
                    className="mt-5"
                    onClick={() => setStep(Math.max(0, step - 1))}
                  >
                    Back
                  </Button>
                ) : null}
              </div>
            )}
          </div>

          {/* ---- what the check will produce, filling in as it goes ---- */}
          <aside className="mt-10 lg:mt-0">
            <div className={cn(card, "p-5 lg:p-6")}>
              <div className={cn(label, "mb-4")}>What this check gives you</div>
              <ul className="m-0 flex list-none flex-col gap-4 p-0">
                {outputs.map((o) => (
                  <li key={o.t} className="flex gap-3">
                    <span
                      className={cn(
                        "mt-1 size-2.5 shrink-0 rounded-full border",
                        o.done ? "border-standing bg-standing" : "border-rule",
                      )}
                      aria-hidden
                    />
                    <span>
                      <span
                        className={cn(
                          "block text-[16px] leading-[24px]",
                          o.done ? "font-medium text-ink" : "text-ink-muted",
                        )}
                      >
                        {o.t}
                      </span>
                      <span className="block text-[14px] leading-[22px] text-ink-muted">
                        {o.d}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
              <p className="mt-5 mb-0 border-t border-rule pt-4 text-[13px] leading-[21px] text-ink-muted">
                No account, and nothing is stored. Upload the letter afterwards and we
                replace every estimate with the exact date and the clause it comes from.
              </p>
            </div>
          </aside>
        </div>
      </main>
    </div>
  );
}

function Unreachable() {
  return (
    <div className="border-l-[3px] border-ink bg-surface px-4 py-3.5">
      <p className="m-0 text-[16px] leading-[26px] text-ink">
        We cannot reach the rules engine right now, so we are not going to guess at
        your deadline. Try again in a moment.
      </p>
    </div>
  );
}

function Verdict({ result }: { result: TriageResponse }) {
  const t = result.deadline ? tone(result.deadline.days_remaining) : null;

  return (
    <div>
      <div className={cn(label, "mb-3.5")}>What we can tell you so far</div>
      <h1 className={pageTitle}>
        {result.track
          ? result.deadline
            ? `You are probably on the ${result.levels[0]?.toLowerCase() ?? "internal appeal"} track, and your window runs to ${formatDate(result.deadline.due_date)}.`
            : "Here is the track you are probably on."
          : "We cannot work out your track from this, and we are not going to guess."}
      </h1>

      <div className="my-7 flex flex-col gap-3.5">
        {/* ---- the track ---- */}
        <Reveal gesture="unfold" trigger="load" delay={0} className={card}>
          <div className="px-[22px] py-5">
            <div className={cn(label, "mb-2")}>Your track</div>
            {result.track ? (
              <>
                <div className="mb-2 text-[19px] font-semibold text-ink">
                  {result.track}
                </div>
                <ol className="m-0 mb-3 flex list-none flex-col gap-1.5 p-0">
                  {result.levels.map((level, i) => (
                    <li key={level} className="text-[16px] leading-[26px] text-ink-muted">
                      <span className="font-mono text-[12px] text-ink-muted">
                        {String(i + 1).padStart(2, "0")}
                      </span>{" "}
                      {level}
                    </li>
                  ))}
                </ol>
              </>
            ) : (
              <p className="mt-0 mb-3 text-[16px] leading-[26px] text-ink-muted text-pretty">
                The rules depend on what kind of plan you have, and we do not cover that
                kind yet. Everything below still applies.
              </p>
            )}
            <div className="border-t border-rule pt-2.5 font-mono text-[12px] text-ink-muted">
              Rules current as of today · version {result.rulebase_version}
            </div>
          </div>
        </Reveal>

        {/* ---- the deadline ---- */}
        {result.deadline ? (
          <Reveal gesture="unfold" trigger="load" delay={0.08} className={card}>
            <div className="px-[22px] py-5">
              <div className={cn(label, "mb-2")}>{result.deadline.label}</div>
              <div className="tabular text-[30px] font-semibold tracking-[-0.02em] text-ink">
                {formatDate(result.deadline.due_date)}
              </div>
              {t ? (
                <div
                  className="mt-1 text-[15px] font-medium"
                  style={{ color: t.color, fontWeight: t.weight }}
                >
                  About {result.deadline.days_remaining} days from today — {t.word}
                </div>
              ) : null}
              <p className="mt-3 mb-0 text-[15px] leading-[24px] text-ink-muted text-pretty">
                Counted as {result.deadline.trigger_description}.
              </p>
              {result.deadline.ambiguous && result.deadline.ambiguity_note ? (
                <p className="mt-2.5 mb-0 border-l-[3px] border-time pl-3 text-[15px] leading-[24px] text-ink">
                  {result.deadline.ambiguity_note}
                </p>
              ) : null}
              <div className="mt-3 border-t border-rule pt-2.5 font-mono text-[12px] text-ink-muted">
                {result.deadline.citation}
                {" · "}
                {result.deadline.rule_id}
              </div>
            </div>
          </Reveal>
        ) : null}

        {/* ---- the honest answer ---- */}
        <Reveal gesture="unfold" trigger="load" delay={0.16} className={card}>
          <div className="px-[22px] py-5">
            <div className={cn(label, "mb-2")}>Is it worth appealing</div>
            <p className="mt-0 mb-0 text-[16px] leading-[26px] text-ink text-pretty">
              {result.worth_appealing}
            </p>
          </div>
        </Reveal>

        {/* ---- anything we had to flag ---- */}
        {result.warnings.length > 0 ? (
          <Reveal gesture="unfold" trigger="load" delay={0.24}>
            <div className="border-l-[3px] border-ink bg-surface px-[18px] py-4">
              <div className={cn(label, "mb-2")}>Read this too</div>
              <ul className="m-0 flex list-none flex-col gap-2 p-0">
                {result.warnings.map((warning) => (
                  <li key={warning} className="text-[15px] leading-[24px] text-ink">
                    {warning}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        ) : null}
      </div>

      <div className="flex flex-wrap gap-3">
        <Button asChild>
          <Link href="/signin/">Upload the letter and get the exact date</Link>
        </Button>
        <Button variant="ghost" asChild>
          <Link href="/">Back to the start</Link>
        </Button>
      </div>
    </div>
  );
}
