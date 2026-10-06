import Link from "next/link";

import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-[560px] flex-col justify-center px-5 py-12">
      <div className="font-mono text-[11px] tracking-[.06em] text-ink-muted">404</div>
      <h1 className="mt-3.5 mb-2.5 text-[28px] leading-[36px] font-semibold tracking-[-0.015em] text-ink">
        There is nothing at that address
      </h1>
      <p className="mt-0 mb-6 text-pretty text-[17px] leading-[28px] text-ink-muted">
        The link may be old, or there may be a typo in it. Nothing about your case has
        changed.
      </p>
      <div className="flex flex-wrap gap-3">
        <Button asChild>
          <Link href="/cases/">Go to your cases</Link>
        </Button>
        <Button variant="ghost" asChild>
          <Link href="/">Back to the start</Link>
        </Button>
      </div>
    </main>
  );
}
