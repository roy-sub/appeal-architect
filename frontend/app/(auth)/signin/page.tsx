"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { DISCLAIMER } from "@/lib/site";

/**
 * Sign in / sign up. Email magic link, no password.
 *
 * The brief requires this screen to say what happens to their documents, here,
 * before they hand any over. Someone deciding whether to upload a letter naming
 * their diagnosis should not have to go looking for a privacy page.
 */
export default function SignInPage() {
  const { session, loading, configured, signInWithEmail } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && session) router.replace("/cases/");
  }, [loading, session, router]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setState("sending");
    try {
      await signInWithEmail(email.trim());
      setState("sent");
    } catch (cause) {
      setState("idle");
      setError(
        cause instanceof Error
          ? cause.message
          : "We could not send the link. Check the address and try again.",
      );
    }
  }

  return (
    <main className="mx-auto flex min-h-dvh max-w-[1120px] flex-col justify-center px-5 py-12 lg:px-10">
      <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-16">
        {/* ---- the form ---- */}
        <div className="max-w-[440px]">
          <Link
            href="/"
            className="font-mono text-[12px] tracking-[.06em] text-ink-muted no-underline"
          >
            APPEAL ARCHITECT
          </Link>

          <h1 className="mt-6 mb-2 text-[30px] leading-[38px] font-semibold tracking-[-0.02em] text-ink lg:text-[34px] lg:leading-[42px]">
            Sign in to your cases
          </h1>
          <p className="m-0 text-[17px] leading-[27px] text-ink-muted">
            We send a link to your email. There is no password to remember.
          </p>

          {!configured ? (
            // No red anywhere, including errors: an ink bar plus an instruction.
            <div className="mt-7 border-l-[3px] border-ink bg-surface px-4 py-3.5">
              <p className="m-0 text-[16px] leading-[26px] text-ink">
                Sign-in is not set up on this copy of the app yet. Set{" "}
                <code className="font-mono text-[14px]">NEXT_PUBLIC_SUPABASE_URL</code> and{" "}
                <code className="font-mono text-[14px]">NEXT_PUBLIC_SUPABASE_ANON_KEY</code> in{" "}
                <code className="font-mono text-[14px]">frontend/.env.local</code>, then restart.
                The steps are in <code className="font-mono text-[14px]">docs/DEPLOY.md</code>.
              </p>
            </div>
          ) : state === "sent" ? (
            <div className="mt-7 rounded-[2px] border border-rule bg-surface px-5 py-5">
              <h2 className="m-0 text-[19px] leading-7 font-semibold text-ink">
                Check your email
              </h2>
              <p className="mt-2 mb-0 text-[16px] leading-[26px] text-ink-muted">
                We sent a link to <span className="font-medium text-ink">{email}</span>. It
                signs you in when you open it, and it works once.
              </p>
              <button
                type="button"
                onClick={() => setState("idle")}
                className="mt-4 bg-transparent p-0 text-[15px] text-clay-deep underline underline-offset-[3px]"
              >
                Use a different address
              </button>
            </div>
          ) : (
            <form onSubmit={submit} className="mt-7">
              <label
                htmlFor="email"
                className="block font-mono text-[11px] tracking-[.06em] text-ink-muted"
              >
                EMAIL ADDRESS
              </label>
              {/* Label above the control, never a placeholder: placeholders
                  vanish exactly when a tired person needs them. */}
              <input
                id="email"
                type="email"
                inputMode="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-2 min-h-[46px] w-full rounded-[6px] border-[1.5px] border-ink bg-surface px-3.5 text-[17px] text-ink outline-none"
              />

              {error ? (
                <p className="mt-3 mb-0 border-l-[3px] border-ink pl-3 text-[15px] leading-6 text-ink">
                  {error}
                </p>
              ) : null}

              <Button
                type="submit"
                disabled={state === "sending" || email.trim().length === 0}
                className="mt-4 w-full"
              >
                {state === "sending" ? "Sending the link…" : "Email me a sign-in link"}
              </Button>
              {email.trim().length === 0 ? (
                // A disabled button always has its reason stated beside it.
                <p className="mt-2 mb-0 text-[14px] leading-[22px] text-ink-muted">
                  Enter your email address and we will send the link.
                </p>
              ) : null}
            </form>
          )}
        </div>

        {/* ---- what happens to their documents ---- */}
        <div className="rounded-[2px] border border-rule bg-surface p-6 lg:p-8">
          <h2 className="m-0 font-mono text-[11px] tracking-[.06em] text-ink-muted">
            WHAT HAPPENS TO YOUR DOCUMENTS
          </h2>
          <dl className="mt-5 grid gap-5">
            {[
              [
                "They are encrypted, in transit and at rest.",
                "Your denial letter and any medical records you add are stored in a private bucket. Nobody reaches a file without a signed link that expires.",
              ],
              [
                "Only you can see your cases.",
                "Every record is tied to your account at the database level, not just in the app. Another account asking for your case gets nothing back.",
              ],
              [
                "We read your letter with an AI model.",
                "That is the one point where the text leaves our servers. It is not used to train anything, and we never log what was sent — only that a call happened.",
              ],
              [
                "The AI does not decide anything.",
                "Your deadlines and your appeal route are worked out by a rules engine from the regulations, and every one shows the rule it came from. The model reads documents and writes sentences.",
              ],
              [
                "You can delete all of it.",
                "Deleting your data removes the files and the records, including the case history. It is a real delete, not a hidden flag.",
              ],
            ].map(([title, body]) => (
              <div key={title}>
                <dt className="text-[16px] leading-[25px] font-semibold text-ink">{title}</dt>
                <dd className="m-0 mt-1 text-[15px] leading-[24px] text-ink-muted text-pretty">
                  {body}
                </dd>
              </div>
            ))}
          </dl>
          <p className="mt-6 mb-0 border-t border-rule pt-4 text-[13px] leading-[21px] text-ink">
            {DISCLAIMER}
          </p>
        </div>
      </div>
    </main>
  );
}
