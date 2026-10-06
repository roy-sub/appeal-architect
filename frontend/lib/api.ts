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

// ---- types, mirroring the backend's Pydantic models ----------------------

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

export type PlanType =
  | "aca_marketplace"
  | "employer_fully_insured"
  | "employer_self_funded"
  | "medicare_advantage"
  | "medicaid"
  | "unknown";

export type ServiceTiming = "pre" | "post" | "concurrent";
export type Filer = "member" | "authorized_rep" | "provider";
export type FactStatus = "pending" | "confirmed" | "edited" | "rejected";
export type DocumentKind =
  | "denial_letter"
  | "eob"
  | "plan_doc"
  | "medical_record"
  | "physician_letter"
  | "other";

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
  plan_type: PlanType;
  state: string | null;
  denial_date: string | null;
  denial_received_date: string | null;
  service_date: string | null;
  service_timing: ServiceTiming | null;
  claim_amount_usd: string | null;
  is_urgent_medical: boolean;
  filer: Filer;
  final_adverse_date: string | null;
  /** Server-computed. The frontend never does date arithmetic beyond "days until". */
  next_deadline: string | null;
  next_deadline_label: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  source: string;
  locator: string;
  title: string | null;
  quote: string | null;
  url: string | null;
  /** False until a human has checked this against the real source. */
  verified: boolean;
}

export interface DeadlineItem {
  id: string;
  label: string;
  due_date: string;
  trigger_date: string;
  trigger_description: string;
  rule_id: string;
  citation: Citation;
  is_calendar_days: boolean;
  source_layer: string;
  count: number | null;
  /** True when the regulation's trigger is unclear. The note must be displayed. */
  ambiguous: boolean;
  ambiguity_note: string | null;
}

export interface RequiredElement {
  key: string;
  label: string;
  detail: string | null;
  rule_id: string;
  citation: Citation;
  mandatory: boolean;
}

export interface RouteStep {
  order: number;
  level: string;
  label: string;
  who_files: string;
  required_elements: RequiredElement[];
  review_body: string;
  insurer_response_window_days: number | null;
  /** Null when this step's trigger has not happened yet. */
  deadline: DeadlineItem | null;
  starts_after: number | null;
  pending_reason: string | null;
  citation: Citation | null;
}

export interface TraceNode {
  conclusion: string;
  rule_id: string;
  premises: string[];
  citation: Citation | null;
  explanation: string | null;
}

export interface RouteDetermination {
  id: string | null;
  case_id: string | null;
  rulebase_version: string;
  facts_hash: string;
  plan_type: PlanType;
  steps: RouteStep[];
  deadlines: DeadlineItem[];
  trace: TraceNode[];
  warnings: string[];
  computed_at: string | null;
}

export interface Premise {
  id: string;
  text: string;
  evidence_key: string | null;
  satisfied: boolean;
}

export interface ArgumentNode {
  id: string;
  side: "insurer" | "patient";
  scheme_id: string | null;
  claim: string;
  premises: Premise[];
  required_evidence: string[];
  citations: Citation[];
  strength: "strong" | "conditional";
}

export interface Attack {
  source_id: string;
  target_id: string;
  kind: "rebut" | "undermine" | "undercut";
  note: string;
}

export interface ArgumentGraph {
  id: string | null;
  case_id: string | null;
  schemes_version: string;
  arguments: ArgumentNode[];
  attacks: Attack[];
  /** "Solid ground" */
  grounded_extension: string[];
  preferred_extensions: string[][];
  stable_extensions: string[][];
  /** "Worth adding" */
  worth_adding: string[];
  /** "Left out" */
  defeated: string[];
  trace: TraceNode[];
  computed_at: string | null;
}

export interface GraphResponse {
  graph: ArgumentGraph;
  tier_explanations: Record<string, string>;
}

export interface ArgumentDetail {
  id: string;
  tier: string | null;
  tier_explanation: string;
  claim: string;
  strength: string;
  premises: Premise[];
  required_evidence: string[];
  missing_evidence: string[];
  holds_now: boolean;
  verdict: string;
  insurer_replies: {
    id: string;
    text: string;
    kind: string;
    answered: boolean;
    verdict: string;
  }[];
  citations: Citation[];
}

export interface ExtractedFact {
  id: string;
  document_id: string | null;
  field: string;
  value: unknown;
  edited_value: unknown;
  confidence: number;
  source_page: number | null;
  source_start: number | null;
  source_end: number | null;
  status: FactStatus;
  confirmed_at: string | null;
}

export interface FactsResponse {
  facts: ExtractedFact[];
  /** While non-empty, POST /route is a 409 and the roadmap stays gated. */
  pending_required: string[];
  ready_for_route: boolean;
}

export interface DocumentOut {
  id: string;
  kind: DocumentKind;
  filename: string;
  mime: string;
  page_count: number | null;
  ocr_used: boolean;
  uploaded_at: string;
}

export interface UploadResult {
  document: DocumentOut;
  facts_proposed: number;
  pages_transcribed: number;
}

export interface DocumentText {
  id: string;
  page_count: number;
  text: string;
  ocr_used: boolean;
}

export interface EvidenceItem {
  key: string;
  label: string;
  why_needed: string | null;
  argument_node_ids: string[];
  status: "missing" | "requested" | "have" | "optional";
  document_id: string | null;
}

export interface LetterParagraph {
  text: string;
  source: "argument" | "procedural";
  argument_node_id: string;
}

export interface Letter {
  id: string;
  case_id: string;
  argument_graph_id: string | null;
  version: number;
  body: {
    paragraphs: LetterParagraph[];
    disclaimer: string;
    rulebase_version?: string;
    schemes_version?: string;
    edited_by_user?: boolean;
  };
  storage_path_pdf: string | null;
  storage_path_docx: string | null;
  generated_at: string;
}

export interface TimelineEvent {
  id: string;
  kind: string;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface TriageDeadline {
  label: string;
  due_date: string;
  days_remaining: number;
  trigger_description: string;
  rule_id: string;
  citation: string;
  ambiguous: boolean;
  ambiguity_note: string | null;
}

export interface TriageResponse {
  /** Null when we cannot work it out. The tool says so rather than guessing. */
  track: string | null;
  levels: string[];
  deadline: TriageDeadline | null;
  worth_appealing: string;
  warnings: string[];
  rulebase_version: string;
  counted_from_today: string;
}

export interface TriageOptions {
  plan_types: { value: string; label: string }[];
  service_timings: { value: string; label: string }[];
  denial_reasons: { value: string; label: string }[];
}

export interface Entitlement {
  tier: string;
  can_generate_letter: boolean;
  always_available: string[];
}

export interface Health {
  ok: boolean;
  env: string;
  rulebase_version: string;
  schemes_version: string;
  services: Record<string, boolean>;
}

export interface DeletionReceipt {
  deleted: Record<string, number>;
  storage_objects_deleted: number;
  anything_left: boolean;
}

// ---- endpoint wrappers. One per endpoint, matching the backend's surface. ----

export const api = {
  health: () => apiRequest<Health>("/healthz", { anonymous: true }),

  me: () => apiRequest<Me>("/api/v1/me"),
  deleteMyData: () =>
    apiRequest<DeletionReceipt>("/api/v1/me/data", { method: "DELETE" }),

  listCases: () => apiRequest<CaseSummary[]>("/api/v1/cases"),
  createCase: (input: { title: string; insurer_name?: string | null }) =>
    apiRequest<CaseSummary>("/api/v1/cases", { method: "POST", body: input }),
  getCase: (id: string) => apiRequest<CaseSummary>(`/api/v1/cases/${id}`),
  patchCase: (id: string, patch: Partial<CaseSummary>) =>
    apiRequest<CaseSummary>(`/api/v1/cases/${id}`, { method: "PATCH", body: patch }),
  deleteCase: (id: string) =>
    apiRequest<void>(`/api/v1/cases/${id}`, { method: "DELETE" }),

  listDocuments: (caseId: string) =>
    apiRequest<DocumentOut[]>(`/api/v1/cases/${caseId}/documents`),
  getDocumentText: (caseId: string, documentId: string) =>
    apiRequest<DocumentText>(`/api/v1/cases/${caseId}/documents/${documentId}/text`),
  getDocumentUrl: (caseId: string, documentId: string) =>
    apiRequest<{ url: string; expires_in_seconds: number }>(
      `/api/v1/cases/${caseId}/documents/${documentId}/url`,
    ),

  listFacts: (caseId: string) =>
    apiRequest<FactsResponse>(`/api/v1/cases/${caseId}/facts`),
  confirmFact: (caseId: string, factId: string) =>
    apiRequest<ExtractedFact>(`/api/v1/cases/${caseId}/facts/${factId}/confirm`, {
      method: "POST",
    }),
  editFact: (caseId: string, factId: string, value: unknown) =>
    apiRequest<ExtractedFact>(`/api/v1/cases/${caseId}/facts/${factId}/edit`, {
      method: "POST",
      body: { value },
    }),
  rejectFact: (caseId: string, factId: string) =>
    apiRequest<ExtractedFact>(`/api/v1/cases/${caseId}/facts/${factId}/reject`, {
      method: "POST",
    }),

  computeRoute: (caseId: string) =>
    apiRequest<RouteDetermination>(`/api/v1/cases/${caseId}/route`, { method: "POST" }),
  getRoute: (caseId: string) =>
    apiRequest<RouteDetermination>(`/api/v1/cases/${caseId}/route`),

  computeArguments: (caseId: string) =>
    apiRequest<GraphResponse>(`/api/v1/cases/${caseId}/arguments`, { method: "POST" }),
  getArguments: (caseId: string) =>
    apiRequest<GraphResponse>(`/api/v1/cases/${caseId}/arguments`),
  getArgumentDetail: (caseId: string, argumentId: string) =>
    apiRequest<ArgumentDetail>(`/api/v1/cases/${caseId}/arguments/${argumentId}`),

  getEvidence: (caseId: string) =>
    apiRequest<EvidenceItem[]>(`/api/v1/cases/${caseId}/evidence`),
  attachEvidence: (caseId: string, key: string, documentId?: string | null) =>
    apiRequest<EvidenceItem>(`/api/v1/cases/${caseId}/evidence/${key}/attach`, {
      method: "POST",
      body: { document_id: documentId ?? null },
    }),

  generateLetter: (caseId: string) =>
    apiRequest<Letter>(`/api/v1/cases/${caseId}/letter`, { method: "POST" }),
  listLetters: (caseId: string) =>
    apiRequest<Letter[]>(`/api/v1/cases/${caseId}/letters`),
  editLetter: (
    caseId: string,
    letterId: string,
    paragraphs: { index: number; text: string }[],
  ) =>
    apiRequest<Letter>(`/api/v1/cases/${caseId}/letters/${letterId}`, {
      method: "PATCH",
      body: { paragraphs },
    }),
  exportLetter: (caseId: string, letterId: string, format: "pdf" | "docx") =>
    apiRequest<{ url: string; format: string; expires_in_seconds: number }>(
      `/api/v1/cases/${caseId}/letters/${letterId}/export?format=${format}`,
    ),

  getTimeline: (caseId: string) =>
    apiRequest<TimelineEvent[]>(`/api/v1/cases/${caseId}/timeline`),
  escalate: (caseId: string, finalAdverseDate: string) =>
    apiRequest<CaseSummary>(`/api/v1/cases/${caseId}/escalate`, {
      method: "POST",
      body: { final_adverse_date: finalAdverseDate },
    }),

  triage: (input: {
    plan_type: string;
    state: string;
    denial_date?: string | null;
    service_timing?: string;
    denial_reason?: string;
    is_urgent_medical?: boolean;
  }) =>
    apiRequest<TriageResponse>("/api/v1/public/triage", {
      method: "POST",
      body: input,
      anonymous: true,
    }),
  triageOptions: () =>
    apiRequest<TriageOptions>("/api/v1/public/triage/options", { anonymous: true }),

  getEntitlement: () => apiRequest<Entitlement>("/api/v1/billing/entitlement"),
  checkout: (input: {
    product: "appeal_package" | "subscription";
    success_url: string;
    cancel_url: string;
  }) =>
    apiRequest<{ url: string }>("/api/v1/billing/checkout", {
      method: "POST",
      body: input,
    }),
};

/** Upload needs multipart, so it bypasses the JSON wrapper. */
export async function uploadDocument(
  caseId: string,
  file: File,
  kind: DocumentKind = "denial_letter",
): Promise<UploadResult> {
  const { supabaseConfigured, getSupabase } = await import("@/lib/supabase");
  const headers: Record<string, string> = { Accept: "application/json" };
  if (supabaseConfigured) {
    const { data } = await getSupabase().auth.getSession();
    if (data.session) headers.Authorization = `Bearer ${data.session.access_token}`;
  }

  const form = new FormData();
  form.append("file", file);
  form.append("kind", kind);

  // Reading a scanned document can take a while: the model transcribes each
  // page without a text layer. No client-side timeout here, because cutting the
  // request off would lose work the user has already waited for.
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/v1/cases/${caseId}/documents`,
    { method: "POST", headers, body: form },
  );

  if (!response.ok) {
    let problem: Problem;
    try {
      problem = (await response.json()) as Problem;
    } catch {
      problem = {
        title: "That upload did not go through",
        status: response.status,
        detail: "Try again, or type the details in by hand instead.",
        code: "internal_error",
      };
    }
    throw new ApiError(problem);
  }
  return (await response.json()) as UploadResult;
}
