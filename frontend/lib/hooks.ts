"use client";

/**
 * One hook per endpoint, as the spec requires.
 *
 * Two conventions worth knowing:
 *
 * - The **active case** lives in `localStorage`, because this is a static export
 *   with no server session and the workspace routes are fixed paths rather than
 *   `/case/[id]/...`. Switching case is explicit.
 * - A mutation that can change a computed result invalidates the things it could
 *   have changed. Attaching evidence recomputes the argument graph, so it
 *   invalidates the graph and the checklist — the user sees the argument move
 *   tier rather than being told it did.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";

import {
  api,
  uploadDocument,
  type DocumentKind,
  type EvidenceItem,
  type Letter,
} from "@/lib/api";
import { caseKeys, healthKeys, meKeys } from "@/lib/query-keys";
import { supabaseConfigured } from "@/lib/supabase";

const ACTIVE_CASE_KEY = "appeal-architect:active-case";

/** The case the workspace screens are showing. */
export function useActiveCase() {
  const [caseId, setCaseId] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      setCaseId(window.localStorage.getItem(ACTIVE_CASE_KEY));
    } catch {
      // A private window with storage blocked still gets a working app; the
      // user picks a case from the list each visit.
    }
    setReady(true);
  }, []);

  const select = useCallback((id: string | null) => {
    setCaseId(id);
    try {
      if (id) window.localStorage.setItem(ACTIVE_CASE_KEY, id);
      else window.localStorage.removeItem(ACTIVE_CASE_KEY);
    } catch {
      /* non-fatal */
    }
  }, []);

  return { caseId, select, ready };
}

const enabled = supabaseConfigured;

export function useHealth() {
  return useQuery({ queryKey: healthKeys.all, queryFn: api.health, retry: 1 });
}

export function useMe() {
  return useQuery({ queryKey: meKeys.all, queryFn: api.me, enabled });
}

export function useCases() {
  return useQuery({ queryKey: caseKeys.list(), queryFn: api.listCases, enabled });
}

export function useCase(caseId: string | null) {
  return useQuery({
    queryKey: caseKeys.detail(caseId ?? ""),
    queryFn: () => api.getCase(caseId!),
    enabled: enabled && Boolean(caseId),
  });
}

export function useCreateCase() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.createCase,
    onSuccess: () => client.invalidateQueries({ queryKey: caseKeys.all }),
  });
}

export function usePatchCase(caseId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (patch: Parameters<typeof api.patchCase>[1]) =>
      api.patchCase(caseId!, patch),
    onSuccess: () => {
      // Changing a date or the plan type changes the route, so both go.
      client.invalidateQueries({ queryKey: caseKeys.all });
    },
  });
}

export function useDocuments(caseId: string | null) {
  return useQuery({
    queryKey: [...caseKeys.detail(caseId ?? ""), "documents"],
    queryFn: () => api.listDocuments(caseId!),
    enabled: enabled && Boolean(caseId),
  });
}

export function useDocumentText(caseId: string | null, documentId: string | null) {
  return useQuery({
    queryKey: [...caseKeys.detail(caseId ?? ""), "documents", documentId, "text"],
    queryFn: () => api.getDocumentText(caseId!, documentId!),
    enabled: enabled && Boolean(caseId) && Boolean(documentId),
    // The document text does not change once stored.
    staleTime: Infinity,
  });
}

export function useUploadDocument(caseId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ file, kind }: { file: File; kind?: DocumentKind }) =>
      uploadDocument(caseId!, file, kind),
    onSuccess: () => {
      // An upload produces new proposals, so the facts list and the case stage
      // both change.
      client.invalidateQueries({ queryKey: caseKeys.detail(caseId ?? "") });
      client.invalidateQueries({ queryKey: caseKeys.list() });
    },
  });
}

export function useFacts(caseId: string | null) {
  return useQuery({
    queryKey: caseKeys.facts(caseId ?? ""),
    queryFn: () => api.listFacts(caseId!),
    enabled: enabled && Boolean(caseId),
  });
}

export function useFactAction(caseId: string | null) {
  const client = useQueryClient();
  const invalidate = () => {
    // Confirming a fact can unlock the route, so the gate is re-read.
    client.invalidateQueries({ queryKey: caseKeys.facts(caseId ?? "") });
    client.invalidateQueries({ queryKey: caseKeys.detail(caseId ?? "") });
  };

  const confirm = useMutation({
    mutationFn: (factId: string) => api.confirmFact(caseId!, factId),
    onSuccess: invalidate,
  });
  const edit = useMutation({
    mutationFn: ({ factId, value }: { factId: string; value: unknown }) =>
      api.editFact(caseId!, factId, value),
    onSuccess: invalidate,
  });
  const reject = useMutation({
    mutationFn: (factId: string) => api.rejectFact(caseId!, factId),
    onSuccess: invalidate,
  });

  return { confirm, edit, reject };
}

export function useRoute(caseId: string | null) {
  return useQuery({
    queryKey: caseKeys.route(caseId ?? ""),
    queryFn: () => api.getRoute(caseId!),
    enabled: enabled && Boolean(caseId),
    // A route determination that does not exist yet is a 404, not an error to
    // retry: the user has not confirmed their facts.
    retry: false,
  });
}

export function useComputeRoute(caseId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.computeRoute(caseId!),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: caseKeys.route(caseId ?? "") });
      client.invalidateQueries({ queryKey: caseKeys.list() });
    },
  });
}

export function useArguments(caseId: string | null) {
  return useQuery({
    queryKey: caseKeys.argumentsGraph(caseId ?? ""),
    queryFn: () => api.getArguments(caseId!),
    enabled: enabled && Boolean(caseId),
    retry: false,
  });
}

export function useComputeArguments(caseId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.computeArguments(caseId!),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: caseKeys.argumentsGraph(caseId ?? "") });
      client.invalidateQueries({ queryKey: caseKeys.evidence(caseId ?? "") });
    },
  });
}

export function useArgumentDetail(caseId: string | null, argumentId: string | null) {
  return useQuery({
    queryKey: [...caseKeys.argumentsGraph(caseId ?? ""), argumentId],
    queryFn: () => api.getArgumentDetail(caseId!, argumentId!),
    enabled: enabled && Boolean(caseId) && Boolean(argumentId),
  });
}

export function useEvidence(caseId: string | null) {
  return useQuery({
    queryKey: caseKeys.evidence(caseId ?? ""),
    queryFn: () => api.getEvidence(caseId!),
    enabled: enabled && Boolean(caseId),
    retry: false,
  });
}

export function useAttachEvidence(caseId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ key, documentId }: { key: string; documentId?: string | null }) =>
      api.attachEvidence(caseId!, key, documentId),
    onSuccess: (item: EvidenceItem) => {
      // Attaching evidence recomputes the graph server-side, so both the
      // checklist and the graph are re-read. This is how the user sees an
      // argument move from "Worth adding" to "Solid ground".
      client.invalidateQueries({ queryKey: caseKeys.evidence(caseId ?? "") });
      client.invalidateQueries({ queryKey: caseKeys.argumentsGraph(caseId ?? "") });
      return item;
    },
  });
}

export function useLetters(caseId: string | null) {
  return useQuery({
    queryKey: caseKeys.letters(caseId ?? ""),
    queryFn: () => api.listLetters(caseId!),
    enabled: enabled && Boolean(caseId),
    retry: false,
  });
}

export function useGenerateLetter(caseId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.generateLetter(caseId!),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: caseKeys.letters(caseId ?? "") });
      client.invalidateQueries({ queryKey: caseKeys.list() });
    },
  });
}

export function useEditLetter(caseId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      letterId,
      paragraphs,
    }: {
      letterId: string;
      paragraphs: { index: number; text: string }[];
    }) => api.editLetter(caseId!, letterId, paragraphs),
    onSuccess: (letter: Letter) => {
      client.invalidateQueries({ queryKey: caseKeys.letters(caseId ?? "") });
      return letter;
    },
  });
}

export function useExportLetter(caseId: string | null) {
  return useMutation({
    mutationFn: ({
      letterId,
      format,
    }: {
      letterId: string;
      format: "pdf" | "docx";
    }) => api.exportLetter(caseId!, letterId, format),
  });
}

export function useTimeline(caseId: string | null) {
  return useQuery({
    queryKey: [...caseKeys.detail(caseId ?? ""), "timeline"],
    queryFn: () => api.getTimeline(caseId!),
    enabled: enabled && Boolean(caseId),
  });
}

export function useEscalate(caseId: string | null) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (finalAdverseDate: string) => api.escalate(caseId!, finalAdverseDate),
    onSuccess: () => {
      // Escalating gives the external-review step a real date.
      client.invalidateQueries({ queryKey: caseKeys.all });
    },
  });
}

export function useEntitlement() {
  return useQuery({
    queryKey: ["entitlement"],
    queryFn: api.getEntitlement,
    enabled,
    retry: false,
  });
}

export function useTriageOptions() {
  return useQuery({
    queryKey: ["triage", "options"],
    queryFn: api.triageOptions,
    staleTime: Infinity,
  });
}

export function useTriage() {
  return useMutation({ mutationFn: api.triage });
}
