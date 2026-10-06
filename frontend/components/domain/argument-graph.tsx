"use client";

/**
 * The argument graph on desktop: React Flow with a dagre layout.
 *
 * Why React Flow rather than the prototype's hand-placed cards: the solver
 * produces graphs of varying shape, and hand-placement only works for one fixed
 * set of nodes. Dagre is configured to reproduce the prototype's reading -- the
 * insurer's claim alone at the top, counter-arguments beneath -- so the
 * structure generalises while the visual stays the designed one. PLAN.md 3.3.
 *
 * Below `lg` the stacked list is used instead. Neither is a degraded fallback:
 * both render the same data, and the list is genuinely easier on a phone.
 */

import dagre from "dagre";
import { useEffect, useMemo } from "react";
import ReactFlow, {
  Background,
  Handle,
  Position,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeProps,
} from "reactflow";

import { ArgumentCard, type Tier } from "@/components/domain/argument-node";
import type { ArgumentGraph } from "@/lib/api";

const NODE_WIDTH = 268;
const NODE_HEIGHT = 112;

interface NodeData {
  tier: Tier;
  reference: string;
  title: string;
  needs: string | null;
  active: boolean;
  pulsing: boolean;
  onSelect: () => void;
}

function GraphCard({ data }: NodeProps<NodeData>) {
  return (
    <>
      <Handle type="target" position={Position.Top} className="!opacity-0" />
      <div style={{ width: NODE_WIDTH }}>
        <ArgumentCard
          tier={data.tier}
          reference={data.reference}
          title={data.title}
          needs={data.needs}
          active={data.active}
          pulsing={data.pulsing}
          onSelect={data.onSelect}
          compact
        />
      </div>
      <Handle type="source" position={Position.Bottom} className="!opacity-0" />
    </>
  );
}

const nodeTypes = { argument: GraphCard };

function layout(nodes: Node<NodeData>[], edges: Edge[]): Node<NodeData>[] {
  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: "TB", nodesep: 28, ranksep: 56, marginx: 8, marginy: 8 });

  nodes.forEach((node) =>
    graph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT }),
  );
  edges.forEach((edge) => graph.setEdge(edge.source, edge.target));
  dagre.layout(graph);

  return nodes.map((node) => {
    const placed = graph.node(node.id);
    return {
      ...node,
      position: { x: placed.x - NODE_WIDTH / 2, y: placed.y - NODE_HEIGHT / 2 },
    };
  });
}

export function tierOf(graph: ArgumentGraph, id: string): Tier {
  if (graph.grounded_extension.includes(id)) return "solid";
  if (graph.worth_adding.includes(id)) return "add";
  if (graph.defeated.includes(id)) return "out";
  return "insurer";
}

/** True for the rebuttal scaffolding: real in the framework, not a card. */
export function isScaffolding(id: string): boolean {
  return id.includes(".rebuttal.") || id.endsWith(".answered");
}

export function visibleArguments(graph: ArgumentGraph) {
  return graph.arguments.filter((argument) => !isScaffolding(argument.id));
}

export function missingFor(
  argument: ArgumentGraph["arguments"][number],
): string | null {
  const missing = argument.premises.filter(
    (premise) => premise.evidence_key && !premise.satisfied,
  );
  if (missing.length === 0) return null;
  return `Needs ${missing.length} more ${missing.length === 1 ? "document" : "documents"} to hold`;
}

export function ArgumentFlow({
  graph,
  selected,
  pulse,
  onSelect,
}: {
  graph: ArgumentGraph;
  selected: string | null;
  pulse: string[];
  onSelect: (id: string) => void;
}) {
  const computed = useMemo(() => {
    const nodes: Node<NodeData>[] = visibleArguments(graph).map((argument) => ({
      id: argument.id,
      type: "argument",
      position: { x: 0, y: 0 },
      data: {
        tier: tierOf(graph, argument.id),
        reference: reference(argument.id),
        title: shortTitle(argument.claim),
        needs: missingFor(argument),
        active: selected === argument.id,
        pulsing: pulse.includes(argument.id),
        onSelect: () => onSelect(argument.id),
      },
    }));

    const ids = new Set(nodes.map((node) => node.id));
    const edges: Edge[] = graph.attacks
      .filter((attack) => ids.has(attack.source_id) && ids.has(attack.target_id))
      .map((attack) => ({
        id: `${attack.source_id}->${attack.target_id}`,
        source: attack.source_id,
        target: attack.target_id,
        type: "smoothstep",
        style: {
          stroke:
            tierOf(graph, attack.source_id) === "solid"
              ? "var(--standing)"
              : "var(--rule)",
          strokeWidth: 1.5,
        },
      }));

    return { nodes: layout(nodes, edges), edges };
  }, [graph, selected, pulse, onSelect]);

  const [nodes, setNodes, onNodesChange] = useNodesState(computed.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(computed.edges);

  useEffect(() => {
    setNodes(computed.nodes);
    setEdges(computed.edges);
  }, [computed, setNodes, setEdges]);

  return (
    <div className="h-[560px] rounded-[16px] border border-rule bg-surface-sunk">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.14 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        minZoom={0.4}
        maxZoom={1.3}
      >
        <Background color="var(--stripe)" gap={22} size={1} />
      </ReactFlow>
    </div>
  );
}

/** A short badge from a scheme id: `mn.plan_own_criteria` becomes `MN·PO`. */
export function reference(id: string): string {
  if (id.startsWith("insurer.")) return "THEIR REASON";
  const [prefix, ...rest] = id.split(".");
  const initials = rest
    .join("_")
    .split("_")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
  return `${prefix.toUpperCase()}·${initials}`;
}

/** The first clause of a claim, for a card that stays one or two lines. */
export function shortTitle(claim: string): string {
  const trimmed = claim.trim().replace(/\s+/g, " ");
  if (trimmed.length <= 76) return trimmed;
  const cut = trimmed.slice(0, 76);
  const lastSpace = cut.lastIndexOf(" ");
  return `${cut.slice(0, lastSpace > 40 ? lastSpace : 76)}…`;
}
