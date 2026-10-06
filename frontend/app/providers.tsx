"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import { AuthProvider } from "@/lib/auth";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: (attempt, error) => {
          // A sleeping free-tier backend is worth waiting for; a 404 is not.
          if (error instanceof ApiError) return error.isRetryable && attempt < 3;
          return attempt < 2;
        },
        // Longer gaps than the default, because the wait being retried is a
        // cold start of up to a minute, not a blip.
        retryDelay: (attempt) => Math.min(2000 * 2 ** attempt, 15_000),
      },
      mutations: { retry: false },
    },
  });
}

export function Providers({ children }: { children: React.ReactNode }) {
  // One client per mount, created in state so a re-render does not discard the
  // cache.
  const [queryClient] = useState(makeQueryClient);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}
