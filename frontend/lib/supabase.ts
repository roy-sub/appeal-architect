"use client";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";

/**
 * Supabase browser client.
 *
 * Static export, so there is no server to hold a session: auth happens in the
 * browser and the access token is sent to the backend as a bearer token.
 *
 * Both values are `NEXT_PUBLIC_*` and therefore compiled into the bundle. The
 * anon key is safe there — RLS is what protects the data. The service-role key
 * must never appear in a `NEXT_PUBLIC_` variable.
 */
const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

/** False when the keys are absent, so screens can say so instead of breaking. */
export const supabaseConfigured = Boolean(url && anonKey);

let client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (!supabaseConfigured) {
    throw new Error(
      "Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and " +
        "NEXT_PUBLIC_SUPABASE_ANON_KEY in frontend/.env.local — see docs/DEPLOY.md.",
    );
  }
  client ??= createClient(url!, anonKey!, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      // The magic link returns with the session in the URL hash; the callback
      // screen exchanges it, so the client does not also race to do it.
      detectSessionInUrl: true,
      flowType: "pkce",
    },
  });
  return client;
}
