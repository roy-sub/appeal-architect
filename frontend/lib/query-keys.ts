/**
 * One place for cache keys, so invalidation is not guesswork.
 *
 * Keys are hierarchical: invalidating `caseKeys.all` invalidates every case
 * query beneath it.
 */
export const caseKeys = {
  all: ["cases"] as const,
  list: () => [...caseKeys.all, "list"] as const,
  detail: (id: string) => [...caseKeys.all, "detail", id] as const,
  facts: (id: string) => [...caseKeys.all, "detail", id, "facts"] as const,
  route: (id: string) => [...caseKeys.all, "detail", id, "route"] as const,
  argumentsGraph: (id: string) => [...caseKeys.all, "detail", id, "arguments"] as const,
  evidence: (id: string) => [...caseKeys.all, "detail", id, "evidence"] as const,
  letters: (id: string) => [...caseKeys.all, "detail", id, "letters"] as const,
};

export const meKeys = {
  all: ["me"] as const,
};

export const healthKeys = {
  all: ["health"] as const,
};
