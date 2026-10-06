"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useCase } from "@/components/workspace/case-context";
import { PageHead, card, label } from "@/components/workspace/shell";
import { Gated, LoadError, NeedsCase, Skeleton } from "@/components/workspace/states";
import { ApiError } from "@/lib/api";
import {
  useEditLetter,
  useEntitlement,
  useExportLetter,
  useGenerateLetter,
  useLetters,
} from "@/lib/hooks";
import { cn } from "@/lib/utils";

const PROCEDURAL = "procedural";

/** What to put in the envelope, and how to prove it was sent on time. */
const POSTING_CHECKLIST = [
  "The signed letter, dated.",
  "A copy of the denial letter you are appealing.",
  "Every document on your evidence checklist that you have.",
  "Send it so you can prove the date: certified mail with return receipt, or the insurer's portal with a screenshot of the confirmation.",
  "Keep a copy of everything you send, including the envelope's postmark.",
];

export default function LetterPage() {
  const { caseId, node, setNode } = useCase();
  const letters = useLetters(caseId);
  const entitlement = useEntitlement();
  const generate = useGenerateLetter(caseId);
  const edit = useEditLetter(caseId);
  const exportLetter = useExportLetter(caseId);

  const latest = letters.data?.[0] ?? null;
  const [editing, setEditing] = useState<number | null>(null);
  const [draft, setDraft] = useState("");

  // Selecting a paragraph selects its argument everywhere else in the app.
  useEffect(() => {
    if (editing !== null && latest) {
      setDraft(latest.body.paragraphs[editing]?.text ?? "");
    }
  }, [editing, latest]);

  if (!caseId) return <NeedsCase />;
  if (letters.isPending) return <Skeleton rows={4} />;

  if (letters.isError) {
    return (
      <LoadError
        error={letters.error}
        what="your letter"
        onRetry={() => letters.refetch()}
      />
    );
  }

  const gated = entitlement.data ? !entitlement.data.can_generate_letter : false;

  if (!latest) {
    return (
      <div>
        <PageHead
          title="Your appeal letter"
          lead="Written from the arguments that hold. Every paragraph traces back to one of them, or to the procedural parts a filing has to contain."
        />
        {gated ? (
          <div className="flex flex-col gap-3.5">
            <Gated
              reason="Writing the letter is part of the Appeal Package. Your route, your deadlines and the rule behind each one stay available either way — nothing about your case is hidden from you."
              href="/#pricing"
              cta="See what the package includes"
            />
            {entitlement.data ? (
              <div className={cn(card, "px-[22px] py-5")}>
                <div className={cn(label, "mb-3")}>ALWAYS FREE</div>
                <ul className="m-0 flex list-none flex-col gap-2 p-0">
                  {entitlement.data.always_available.map((item) => (
                    <li key={item} className="text-[15px] leading-[23px] text-ink">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : (
          <div>
            <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
              {generate.isPending ? "Writing it…" : "Write my appeal letter"}
            </Button>
            <p className="mt-2.5 mb-0 max-w-[58ch] text-pretty text-[15px] leading-[24px] text-ink-muted">
              It takes about half a minute. You can edit every paragraph afterwards,
              and the procedural parts stay fixed because a filing has to contain them.
            </p>
            {generate.isError ? (
              <div className="mt-3.5">
                <LoadError error={generate.error} what="the letter" />
              </div>
            ) : null}
          </div>
        )}
      </div>
    );
  }

  const paragraphs = latest.body.paragraphs;
  const fromArguments = paragraphs.filter((p) => p.source === "argument").length;

  return (
    <div>
      <PageHead
        title="Your appeal letter"
        lead={`Version ${latest.version}. ${fromArguments} of ${paragraphs.length} paragraphs come from an argument the solver accepted; the rest are the procedural parts a filing has to contain. Nothing here was written without something behind it.`}
      />

      <div className="grid gap-3.5 lg:grid-cols-[1fr_300px] lg:items-start">
        {/* ---- the letter ---- */}
        <article className="rounded-[2px] border border-rule bg-surface p-7 lg:p-[44px_56px] print:border-0 print:p-0">
          <div className="font-mono text-[11px] leading-[19px] text-ink-muted">
            <div>{new Date().toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}</div>
            <div>Appeals Department</div>
          </div>

          <p className="mt-7 mb-5 font-doc text-[17px] leading-[29px] text-ink">
            To the Appeals Department,
          </p>

          {paragraphs.map((paragraph, index) => {
            const isArgument = paragraph.source === "argument";
            const active = isArgument && node === paragraph.argument_node_id;

            return (
              <div key={index} className="mb-5">
                {/* The badge is an editing affordance; it is display:none in print. */}
                <button
                  type="button"
                  onClick={() => {
                    if (isArgument) {
                      setNode(active ? null : paragraph.argument_node_id);
                    }
                  }}
                  className={cn(
                    "mb-1.5 block bg-transparent p-0 font-mono text-[11px] tracking-[.05em] print:hidden",
                    isArgument ? "text-clay-deep underline underline-offset-[3px]" : "text-ink-muted",
                  )}
                >
                  {paragraph.argument_node_id === PROCEDURAL
                    ? "PROCEDURAL"
                    : paragraph.argument_node_id}
                </button>

                {editing === index ? (
                  <div>
                    <textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      rows={5}
                      className="w-full rounded-[6px] border-[1.5px] border-ink bg-surface p-3.5 font-doc text-[17px] leading-[29px] text-ink outline-none"
                    />
                    <div className="mt-2.5 flex gap-2.5">
                      <Button
                        variant="small"
                        disabled={edit.isPending}
                        onClick={() =>
                          edit.mutate(
                            {
                              letterId: latest.id,
                              paragraphs: [{ index, text: draft }],
                            },
                            { onSuccess: () => setEditing(null) },
                          )
                        }
                      >
                        Save
                      </Button>
                      <Button variant="ghost" onClick={() => setEditing(null)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p
                    className={cn(
                      "m-0 font-doc text-[17px] leading-[29px] text-ink",
                      active &&
                        "border-l-2 border-standing bg-standing-tint pl-3.5 print:border-0 print:bg-transparent print:pl-0",
                    )}
                    onDoubleClick={() => setEditing(index)}
                  >
                    {paragraph.text}
                  </p>
                )}

                {editing !== index ? (
                  <button
                    type="button"
                    onClick={() => setEditing(index)}
                    className="mt-1 bg-transparent p-0 text-[14px] text-ink-muted underline underline-offset-[3px] print:hidden"
                  >
                    Edit this paragraph
                  </button>
                ) : null}
              </div>
            );
          })}

          <div className="mt-9">
            <p className="m-0 mb-10 font-doc text-[17px] leading-[29px] text-ink">
              Sincerely,
            </p>
            <p className="m-0 font-doc text-[17px] leading-[29px] text-ink">
              _______________________________
            </p>
            <p className="m-0 font-doc text-[15px] leading-[26px] text-ink-muted">
              Member signature and date
            </p>
          </div>

          <p className="mt-10 mb-0 border-t border-rule pt-3.5 text-[13px] leading-[21px] text-ink">
            {latest.body.disclaimer}
          </p>
        </article>

        {/* ---- export and posting ---- */}
        <aside className="flex flex-col gap-3.5 print:hidden">
          <div className={cn(card, "px-5 py-5")}>
            <div className={cn(label, "mb-3")}>EXPORT</div>
            <div className="flex flex-col gap-2.5">
              {(["pdf", "docx"] as const).map((format) => (
                <Button
                  key={format}
                  variant="ghost"
                  disabled={exportLetter.isPending}
                  onClick={() =>
                    exportLetter.mutate(
                      { letterId: latest.id, format },
                      {
                        onSuccess: (result) => {
                          window.open(result.url, "_blank", "noopener");
                        },
                      },
                    )
                  }
                >
                  {exportLetter.isPending ? "Preparing…" : `Download ${format.toUpperCase()}`}
                </Button>
              ))}
              <Button variant="ghost" onClick={() => window.print()}>
                Print
              </Button>
            </div>
            {exportLetter.isError ? (
              <p className="mt-3 mb-0 border-l-[3px] border-ink pl-3 text-[14px] leading-[22px] text-ink">
                {exportLetter.error instanceof ApiError
                  ? exportLetter.error.problem.detail
                  : "That did not work. Try printing instead."}
              </p>
            ) : null}
          </div>

          <div className={cn(card, "px-5 py-5")}>
            <div className={cn(label, "mb-3")}>WHAT TO SEND, AND HOW</div>
            <ul className="m-0 flex list-none flex-col gap-2.5 p-0">
              {POSTING_CHECKLIST.map((item) => (
                <li
                  key={item}
                  className="text-pretty text-[15px] leading-[23px] text-ink"
                >
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className={cn(card, "px-5 py-5")}>
            <div className={cn(label, "mb-2.5")}>VERSIONS</div>
            <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
              {letters.data.map((letter) => (
                <li key={letter.id} className="text-[15px] text-ink-muted">
                  Version {letter.version}
                  {letter.body.edited_by_user ? " · edited by you" : ""}
                </li>
              ))}
            </ul>
            <Button
              variant="ghost"
              className="mt-3.5 w-full"
              disabled={generate.isPending || gated}
              onClick={() => generate.mutate()}
            >
              {generate.isPending ? "Writing…" : "Write a new version"}
            </Button>
            {gated ? (
              <p className="mt-2 mb-0 text-[14px] leading-[22px] text-ink-muted">
                A new version is part of the Appeal Package.
              </p>
            ) : null}
          </div>

          <Button variant="ghost" asChild>
            <Link href="/case/arguments/">See the arguments behind it</Link>
          </Button>
        </aside>
      </div>
    </div>
  );
}
