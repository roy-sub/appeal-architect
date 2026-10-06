"use client";

/**
 * Shared workspace state.
 *
 * What lives here is cross-screen selection, not data: the selected argument
 * node (selecting a letter paragraph selects its node everywhere), the one-shot
 * graph assemble, and the evidence pulse. The case data itself comes from the
 * API through the hooks in `lib/hooks.ts`, so there is one source of truth and
 * it is the server.
 */

import { createContext, useCallback, useContext, useState } from "react";

import { useActiveCase } from "@/lib/hooks";

interface CaseState {
  /** The case the workspace is showing, from localStorage. */
  caseId: string | null;
  selectCase: (id: string | null) => void;
  caseReady: boolean;

  /** The selected argument node, shared across the graph, evidence and letter. */
  node: string | null;
  setNode: (id: string | null) => void;

  /** Argument nodes to pulse once, after their evidence was satisfied. */
  pulse: string[];
  queuePulse: (ids: string[]) => void;
  clearPulse: () => void;

  /** The graph assembles once per visit, then renders static. */
  graphPlayed: boolean;
  markGraphPlayed: () => void;
}

const Ctx = createContext<CaseState | null>(null);

export function CaseProvider({ children }: { children: React.ReactNode }) {
  const { caseId, select, ready } = useActiveCase();
  const [node, setNode] = useState<string | null>(null);
  const [pulse, setPulse] = useState<string[]>([]);
  const [graphPlayed, setGraphPlayed] = useState(false);

  const queuePulse = useCallback((ids: string[]) => {
    setPulse((current) => [...new Set([...current, ...ids])]);
  }, []);

  return (
    <Ctx.Provider
      value={{
        caseId,
        selectCase: select,
        caseReady: ready,
        node,
        setNode,
        pulse,
        queuePulse,
        clearPulse: () => setPulse([]),
        graphPlayed,
        markGraphPlayed: () => setGraphPlayed(true),
      }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useCase() {
  const value = useContext(Ctx);
  if (!value) throw new Error("useCase must be used inside <CaseProvider>");
  return value;
}
