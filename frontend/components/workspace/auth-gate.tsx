"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/lib/auth";

/**
 * Client-side guard for the case workspace.
 *
 * A static export has no middleware, so the gate lives here. It renders nothing
 * until the session check resolves: a flash of the signed-out state at someone
 * who is signed in reads as having been logged out, and a flash of case data at
 * someone who is not would be worse.
 */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { session, loading, configured } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (configured && !loading && !session) router.replace("/signin/");
  }, [configured, loading, session, router]);

  // Unconfigured: let the screens render so a developer with no Supabase
  // project can still see the workspace. They get an explicit notice instead of
  // a redirect loop into a sign-in page that cannot work.
  if (!configured) return <>{children}</>;

  if (loading || !session) {
    return (
      <div className="px-5 py-10 lg:px-10" aria-busy="true">
        <div className="h-[18px] w-[180px] rounded-[2px] bg-surface-sunk" />
        <div className="mt-4 h-[14px] w-[280px] rounded-[2px] bg-surface-sunk" />
        <span className="sr-only">Checking your sign-in</span>
      </div>
    );
  }

  return <>{children}</>;
}
