"use client";
import { createContext, useContext, useState } from "react";
import { evidence, type EvState } from "@/lib/case-data";

// Client-side case state shared across workspace screens until a backend owns it.
// - node: the selected argument. Selecting a letter paragraph selects its node everywhere.
// - evidence: checklist state; satisfying an item queues a one-time pulse on the
//   argument nodes it feeds (motion.md, "Evidence").
// - graphPlayed: the argument graph assembles once per case, then shows the static diagram.
type CaseState = {
  node: string;
  setNode: (id: string) => void;
  evidenceState: Record<string, EvState>;
  setEvidence: (id: string, st: EvState) => void;
  pulse: string[];
  clearPulse: () => void;
  graphPlayed: boolean;
  markGraphPlayed: () => void;
};

const Ctx = createContext<CaseState | null>(null);

export function CaseProvider({ children }: { children: React.ReactNode }) {
  const [node, setNode] = useState("a1");
  const [evidenceState, setEvState] = useState<Record<string, EvState>>(() => Object.fromEntries(evidence.map((e) => [e.id, e.st])));
  const [pulse, setPulse] = useState<string[]>([]);
  const [graphPlayed, setGraphPlayed] = useState(false);

  const setEvidence = (id: string, st: EvState) => {
    setEvState((s) => ({ ...s, [id]: st }));
    if (st === "have") {
      const item = evidence.find((e) => e.id === id);
      if (item) setPulse((p) => [...new Set([...p, ...item.why.toLowerCase().split(" ")])]);
    }
  };

  return (
    <Ctx.Provider
      value={{ node, setNode, evidenceState, setEvidence, pulse, clearPulse: () => setPulse([]), graphPlayed, markGraphPlayed: () => setGraphPlayed(true) }}
    >
      {children}
    </Ctx.Provider>
  );
}

export function useCase() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useCase must be used inside <CaseProvider>");
  return v;
}
