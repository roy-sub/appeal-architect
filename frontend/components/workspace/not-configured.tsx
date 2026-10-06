import Link from "next/link";

/**
 * Shown on a data screen when the backend is not wired up.
 *
 * This is a development state, and it is a notice rather than an error: nothing
 * is broken, something is simply not set up yet. No red, an ink bar, and the
 * instruction.
 */
export function NotConfigured({ what }: { what: string }) {
  return (
    <div className="border-l-[3px] border-ink bg-surface px-5 py-4">
      <p className="m-0 text-[16px] leading-[26px] text-ink">
        {what} needs a backend, and this copy of the app does not have one
        configured yet.
      </p>
      <p className="mt-2 mb-0 text-[15px] leading-[24px] text-ink-muted">
        Set the Supabase and API values in{" "}
        <code className="font-mono text-[14px]">frontend/.env.local</code> and{" "}
        <code className="font-mono text-[14px]">backend/.env</code>. The four values and
        where to find them are in{" "}
        <code className="font-mono text-[14px]">docs/DEPLOY.md</code>.
      </p>
      <Link
        href="/"
        className="mt-3 inline-block text-[15px] text-clay-deep underline underline-offset-[3px]"
      >
        Back to the landing page
      </Link>
    </div>
  );
}
