/**
 * The typed backend client.
 *
 * Three things it does that a bare `fetch` would not:
 *
 * 1. Attaches the Supabase access token, so `user_id` is always derived from a
 *    verified JWT on the server rather than sent by the client.
 * 2. Parses RFC 7807 problem+json into one error shape with a machine-readable
 *    `code`, so screens branch on the code and never on copy.
 * 3. Distinguishes "the backend is asleep" from "the backend is broken". Render's
 *    free tier sleeps after 15 minutes idle and the first request can take 30
 *    seconds or more; the UI shows a warming state rather than an error.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Matches `app/problem.py`. Add, never repurpose. */
export type ErrorCode =
  | "validation_failed"
  | "not_found"
  | "unauthenticated"
  | "forbidden"
  | "conflict"
  | "rate_limited"
  | "service_not_configured"
  | "facts_not_confirmed"
  | "unsupported_plan_type"
  | "llm_cap_reached"
  | "internal_error"
  // Client-side only: the request never reached the server.
  | "network_unreachable"
  | "backend_warming";

export interface Problem {
  type?: string;
  title: string;
  status: number;
  detail: string;
  code: ErrorCode;
  [key: string]: unknown;
}

export class ApiError extends Error {
  readonly code: ErrorCode;
  readonly status: number;
  readonly problem: Problem;

  constructor(problem: Problem) {
    super(problem.detail);
    this.name = "ApiError";
    this.code = problem.code;
    this.status = problem.status;
    this.problem = problem;
  }

  /** A sleeping free-tier backend is worth retrying; a 4xx is not. */
  get isRetryable(): boolean {
    return (
      this.code === "backend_warming" ||
      this.code === "network_unreachable" ||
      this.status >= 500
    );
  }
}

/** How long the first request may take before we call it warming, in ms. */
const WARMING_TIMEOUT_MS = 45_000;

async function accessToken(): Promise<string | null> {
  const { supabaseConfigured, getSupabase } = await import("@/lib/supabase");
  if (!supabaseConfigured) return null;
  const { data } = await getSupabase().auth.getSession();
  return data.session?.access_token ?? null;
}

async function toProblem(response: Response): Promise<Problem> {
  try {
    const body = (await response.json()) as Partial<Problem>;
    if (body && typeof body.code === "string") return body as Problem;
    return {
      title: "Something went wrong",
      status: response.status,
      detail: typeof body?.detail === "string" ? body.detail : response.statusText,
      code: response.status >= 500 ? "internal_error" : "validation_failed",
    };
  } catch {
    return {
      title: "Something went wrong",
      status: response.status,
      detail: response.statusText || "The server sent a reply we could not read.",
      code: "internal_error",
    };
  }
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  /** Send without a token. Used by the public triage tool. */
  anonymous?: boolean;
  signal?: AbortSignal;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, anonymous = false, signal } = options;

  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  if (!anonymous) {
    const token = await accessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  // Our own timeout, combined with any caller-supplied signal, so a sleeping
  // backend surfaces as a warming state rather than hanging indefinitely.
  const timeout = new AbortController();
  const timer = setTimeout(() => timeout.abort(), WARMING_TIMEOUT_MS);
  const composite =
    typeof AbortSignal !== "undefined" && "any" in AbortSignal && signal
      ? AbortSignal.any([signal, timeout.signal])
      : (signal ?? timeout.signal);

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: composite,
    });
  } catch (cause) {
    clearTimeout(timer);
    // The caller cancelled: not an error to report.
    if (signal?.aborted) throw cause;
    const warming = timeout.signal.aborted;
    throw new ApiError({
      title: warming ? "Still waking up" : "We cannot reach the server",
      status: 0,
      detail: warming
        ? "The server sleeps when it has not been used for a while. This first request can take up to a minute."
        : "Check your connection and try again. Nothing you entered was lost.",
      code: warming ? "backend_warming" : "network_unreachable",
    });
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) throw new ApiError(await toProblem(response));
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

// ---- endpoint wrappers. One per endpoint, matching the backend's surface. ----

export type CaseStage =
  | "uploaded"
  | "extracted"
  | "confirmed"
  | "routed"
  | "arguing"
  | "evidence"
  | "letter_ready"
  | "sent"
  | "responded"
  | "escalated"
  | "resolved";

export interface Me {
  id: string;
  email: string | null;
}

export interface CaseSummary {
  id: string;
  title: string;
  insurer_name: string | null;
  claim_number: string | null;
  stage: CaseStage;
  plan_type: string;
  denial_date: string | null;
  /** Server-computed. The frontend never does date arithmetic beyond "days until". */
  next_deadline: string | null;
  next_deadline_label: string | null;
  created_at: string;
  updated_at: string;
}

export interface Health {
  ok: boolean;
  env: string;
  rulebase_version: string;
  schemes_version: string;
  services: Record<string, boolean>;
}

export const api = {
  health: () => apiRequest<Health>("/healthz", { anonymous: true }),
  me: () => apiRequest<Me>("/api/v1/me"),
  listCases: () => apiRequest<CaseSummary[]>("/api/v1/cases"),
  createCase: (input: { title: string; insurer_name?: string | null }) =>
    apiRequest<CaseSummary>("/api/v1/cases", { method: "POST", body: input }),
};
