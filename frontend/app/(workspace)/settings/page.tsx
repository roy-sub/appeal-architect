"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { PageHead, card, label, well } from "@/components/workspace/shell";
import { LoadError } from "@/components/workspace/states";
import { api, ApiError, type DeletionReceipt } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useCases, useEntitlement, useMe } from "@/lib/hooks";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const me = useMe();
  const cases = useCases();
  const entitlement = useEntitlement();
  const { signOut } = useAuth();

  return (
    <div>
      <PageHead
        title="Settings"
        lead="Your account, what you are paying for, and how to leave."
      />

      <div className="flex flex-col gap-3.5">
        {/* ---- account ---- */}
        <section className={cn(card, "px-[22px] py-5")}>
          <div className={cn(label, "mb-3")}>ACCOUNT</div>
          <dl className="m-0 grid gap-2.5">
            <div className="flex flex-wrap gap-2">
              <dt className="w-[140px] text-[15px] text-ink-muted">Email</dt>
              <dd className="m-0 text-[16px] text-ink">
                {me.data?.email ?? "—"}
              </dd>
            </div>
            <div className="flex flex-wrap gap-2">
              <dt className="w-[140px] text-[15px] text-ink-muted">Open cases</dt>
              <dd className="m-0 text-[16px] text-ink">{cases.data?.length ?? 0}</dd>
            </div>
          </dl>
          <Button variant="ghost" className="mt-4" onClick={() => void signOut()}>
            Sign out
          </Button>
        </section>

        {/* ---- billing ---- */}
        <section className={cn(card, "px-[22px] py-5")}>
          <div className={cn(label, "mb-3")}>WHAT YOU HAVE</div>
          {entitlement.isPending ? (
            <p className="m-0 text-[15px] text-ink-muted">Checking…</p>
          ) : entitlement.isError ? (
            <p className="m-0 text-[15px] text-ink-muted">
              We could not check your plan just now. Nothing about your case has
              changed.
            </p>
          ) : (
            <>
              <p className="mt-0 mb-3.5 text-[16px] leading-[26px] text-ink">
                {entitlement.data.tier === "free"
                  ? "The free tier."
                  : entitlement.data.tier === "appeal_package"
                    ? "The Appeal Package."
                    : "A subscription."}
              </p>
              <div className={well}>
                <div className={cn(label, "mb-2")}>AVAILABLE TO YOU WHATEVER HAPPENS</div>
                <ul className="m-0 flex list-none flex-col gap-1.5 p-0">
                  {entitlement.data.always_available.map((item) => (
                    <li key={item} className="text-[15px] leading-[23px] text-ink">
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              {!entitlement.data.can_generate_letter ? (
                <Button variant="ghost" asChild className="mt-4">
                  <Link href="/pricing/">See the Appeal Package</Link>
                </Button>
              ) : null}
            </>
          )}
        </section>

        {/* ---- notifications ---- */}
        <section className={cn(card, "px-[22px] py-5")}>
          <div className={cn(label, "mb-3")}>DEADLINE REMINDERS</div>
          <p className="mt-0 mb-0 text-pretty text-[16px] leading-[26px] text-ink">
            We email you at 30, 14, 7, 3 and 1 days before each deadline, and again the
            morning it is due. Those emails carry the deadline and the case name and
            nothing clinical, because they may be read on a shared screen.
          </p>
          <p className="mt-2.5 mb-0 text-pretty text-[15px] leading-[24px] text-ink-muted">
            They are on for every case and we are not going to let you turn them off.
            That is the one piece of paternalism in this product, and a missed filing
            window is why.
          </p>
        </section>

        {/* ---- delete ---- */}
        <DeleteSection />
      </div>
    </div>
  );
}

function DeleteSection() {
  const [stage, setStage] = useState<"idle" | "confirming" | "done">("idle");
  const [typed, setTyped] = useState("");
  const [receipt, setReceipt] = useState<DeletionReceipt | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [working, setWorking] = useState(false);
  const { signOut } = useAuth();

  const phrase = "delete my data";
  const ready = typed.trim().toLowerCase() === phrase;

  async function run() {
    setWorking(true);
    setError(null);
    try {
      const result = await api.deleteMyData();
      setReceipt(result);
      setStage("done");
    } catch (cause) {
      setError(cause);
    } finally {
      setWorking(false);
    }
  }

  if (stage === "done" && receipt) {
    return (
      <section className="border-l-[3px] border-ink bg-surface px-[22px] py-5">
        <div className={cn(label, "mb-2.5")}>DELETED</div>
        <p className="mt-0 mb-3.5 text-[16px] leading-[26px] text-ink">
          {receipt.anything_left
            ? "Most of it is gone, but something did not delete. Tell us and we will finish it by hand."
            : "It is gone. Rows and files, not a hidden flag."}
        </p>
        <ul className="m-0 mb-4 flex list-none flex-col gap-1 p-0 font-mono text-[12px] text-ink-muted">
          {Object.entries(receipt.deleted)
            .filter(([, count]) => count > 0)
            .map(([table, count]) => (
              <li key={table}>
                {table.replace(/_/g, " ")}: {count}
              </li>
            ))}
          <li>files: {receipt.storage_objects_deleted}</li>
        </ul>
        <Button variant="ghost" onClick={() => void signOut()}>
          Sign out
        </Button>
      </section>
    );
  }

  return (
    <section className="border-l-[3px] border-ink bg-surface px-[22px] py-5">
      <div className={cn(label, "mb-3")}>DELETE MY DATA</div>
      <p className="mt-0 mb-3 text-pretty text-[16px] leading-[26px] text-ink">
        This removes your cases, your uploaded documents, the facts you confirmed, every
        route and argument we computed, your letters, and your account. Rows and files,
        not a hidden flag.
      </p>
      <p className="mt-0 mb-4 text-pretty text-[16px] leading-[26px] text-ink">
        <strong>It also removes your case history</strong> — the record of what was
        uploaded, confirmed, generated and sent. That is the record you might need later
        if a dispute carries on, and we would rather say so now than have you find out
        afterwards. Export anything you want to keep first.
      </p>

      {stage === "idle" ? (
        <Button variant="ghost" onClick={() => setStage("confirming")}>
          Delete my data
        </Button>
      ) : (
        <div>
          <label htmlFor="confirm-delete" className={cn(label, "block mb-2")}>
            TYPE &ldquo;{phrase.toUpperCase()}&rdquo; TO CONFIRM
          </label>
          <input
            id="confirm-delete"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            autoComplete="off"
            className="min-h-[46px] w-full max-w-[340px] rounded-[6px] border-[1.5px] border-ink bg-surface px-3.5 text-[17px] text-ink outline-none"
          />
          <div className="mt-3.5 flex flex-wrap gap-2.5">
            <Button disabled={!ready || working} onClick={() => void run()}>
              {working ? "Deleting…" : "Delete everything"}
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setStage("idle");
                setTyped("");
              }}
            >
              Keep my data
            </Button>
          </div>
          {!ready ? (
            <p className="mt-2.5 mb-0 text-[15px] leading-[24px] text-ink-muted">
              Type the phrase exactly and the button will work. This one cannot be
              undone, so it asks properly.
            </p>
          ) : null}
        </div>
      )}

      {error ? (
        <div className="mt-3.5">
          <LoadError
            error={error}
            what="that deletion"
            onRetry={ready ? () => void run() : undefined}
          />
          {error instanceof ApiError && error.status === 501 ? (
            <p className="mt-2 mb-0 text-[15px] text-ink-muted">
              This server does not have deletion wired up yet.
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
