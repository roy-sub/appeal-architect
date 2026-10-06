"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { getSupabase, supabaseConfigured } from "@/lib/supabase";

/**
 * Where the magic link lands.
 *
 * Static export, so there is no server to exchange the code: it happens here in
 * the browser. Supabase's client reads the `code` query parameter (PKCE) or the
 * token in the URL hash, depending on the flow, so this screen waits for a
 * session to appear rather than parsing the URL itself.
 */
export default function AuthCallbackPage() {
  const router = useRouter();
  const [failed, setFailed] = useState<string | null>(null);

  useEffect(() => {
    if (!supabaseConfigured) {
      setFailed("Sign-in is not set up on this copy of the app.");
      return;
    }

    const supabase = getSupabase();
    let done = false;

    function land() {
      if (done) return;
      done = true;
      router.replace("/cases/");
    }

    // The link may carry an error instead of a session — an expired or
    // already-used link is the common case, and it needs saying plainly.
    const hash = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const query = new URLSearchParams(window.location.search);
    const described = hash.get("error_description") ?? query.get("error_description");
    if (described) {
      setFailed(described);
      return;
    }

    supabase.auth.getSession().then(({ data }) => {
      if (data.session) land();
    });

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) land();
    });

    // If no session has arrived by now, the link did not work.
    const timer = setTimeout(() => {
      if (!done) {
        setFailed("That link did not sign you in. It may have expired, or it may already have been used.");
      }
    }, 8000);

    return () => {
      subscription.subscription.unsubscribe();
      clearTimeout(timer);
    };
  }, [router]);

  return (
    <main className="mx-auto flex min-h-dvh max-w-[560px] flex-col justify-center px-5 py-12">
      {failed ? (
        <div className="border-l-[3px] border-ink bg-surface px-5 py-5">
          <h1 className="m-0 text-[22px] leading-[30px] font-semibold text-ink">
            Sign in again
          </h1>
          <p className="mt-2 mb-0 text-[16px] leading-[26px] text-ink-muted">{failed}</p>
          <Link
            href="/signin/"
            className="mt-4 inline-block text-[16px] text-clay-deep underline underline-offset-[3px]"
          >
            Get a new link
          </Link>
        </div>
      ) : (
        <div>
          <h1 className="m-0 text-[22px] leading-[30px] font-semibold text-ink">
            Signing you in
          </h1>
          <p className="mt-2 mb-0 text-[16px] leading-[26px] text-ink-muted">
            One moment. This page will take you to your cases.
          </p>
        </div>
      )}
    </main>
  );
}
