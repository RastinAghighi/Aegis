import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  Handle,
  MarkerType,
  Node,
  NodeProps,
  Position,
} from 'reactflow';
import { AlertOctagon, Database, FileWarning, Route, Terminal } from 'lucide-react';

import 'reactflow/dist/style.css';

import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  APIError,
  FlowGraph as FlowGraphData,
  FlowNode as APIFlowNode,
  getFlowGraph,
  severityBadgeClass,
} from '@/lib/api';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Node visual definition
// ---------------------------------------------------------------------------

type NodeKind = APIFlowNode['type'];

const NODE_STYLE: Record<
  NodeKind,
  {
    icon: typeof Database;
    color: string; // tailwind class for accent strip
    bg: string; // tailwind class for background
    border: string;
    label: string;
  }
> = {
  schema: {
    icon: Database,
    color: 'bg-slate-500',
    bg: 'bg-slate-800/90',
    border: 'border-slate-600',
    label: 'Schema',
  },
  route: {
    icon: Route,
    color: 'bg-slate-400',
    bg: 'bg-slate-700/90',
    border: 'border-slate-500',
    label: 'Route Handler',
  },
  error_handler: {
    icon: FileWarning,
    color: 'bg-rose-500',
    bg: 'bg-rose-700/90',
    border: 'border-rose-500',
    label: 'Error Handler',
  },
  sink: {
    icon: Terminal,
    color: 'bg-rose-700',
    bg: 'bg-rose-900/95',
    border: 'border-rose-700',
    label: 'PHI Sink',
  },
};

interface FlowCardData {
  node: APIFlowNode;
  emphasized: boolean;
  onClick: (n: APIFlowNode) => void;
}

function FlowCardNode({ data }: NodeProps<FlowCardData>) {
  const { node, emphasized, onClick } = data;
  const style = NODE_STYLE[node.type];
  const Icon = style.icon;

  return (
    <div
      onClick={() => onClick(node)}
      className={cn(
        'group relative w-[240px] cursor-pointer overflow-hidden rounded-lg border-2 text-left shadow-lg transition-transform hover:scale-[1.02]',
        style.border,
        style.bg,
        emphasized && 'ring-2 ring-rose-500/60 ring-offset-2 ring-offset-slate-950',
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-2 !w-2 !border-slate-300 !bg-slate-300"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-2 !w-2 !border-slate-300 !bg-slate-300"
      />

      <div className={cn('h-1 w-full', style.color)} />

      <div className="p-3">
        <div className="mb-1.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Icon className="h-4 w-4 text-slate-200" />
            <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-300">
              {style.label}
            </span>
          </div>
          {emphasized && (
            <AlertOctagon className="h-3.5 w-3.5 text-rose-300" />
          )}
        </div>

        <div className="mb-1 font-mono text-sm font-semibold text-slate-50">
          {node.label}
        </div>
        <div className="text-xs leading-snug text-slate-300">
          {node.sublabel}
        </div>
        {node.file && (
          <div className="mt-2 truncate border-t border-slate-800/60 pt-2 font-mono text-[10px] text-slate-400">
            {node.file}
            {node.line ? `:${node.line}` : ''}
          </div>
        )}
      </div>
    </div>
  );
}

const nodeTypes = { flowCard: FlowCardNode };

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

const NODE_POSITIONS: Record<string, { x: number; y: number }> = {
  'patient-model': { x: 0, y: 80 },
  'patient-route': { x: 320, y: 80 },
  'error-handler': { x: 640, y: 80 },
  logs: { x: 960, y: 80 },
};

const LEAK_PATH = new Set([
  'patient-model',
  'patient-route',
  'error-handler',
  'logs',
]);

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function FlowGraphPage() {
  const { data, isLoading, error } = useQuery<FlowGraphData, APIError>({
    queryKey: ['flow-graph'],
    queryFn: getFlowGraph,
  });

  const [selectedNode, setSelectedNode] = useState<APIFlowNode | null>(null);

  const { nodes, edges } = useMemo<{ nodes: Node[]; edges: Edge[] }>(() => {
    if (!data) return { nodes: [], edges: [] };

    const apiNodes = data.nodes;
    const apiEdges = data.edges;

    const positions: Record<string, { x: number; y: number }> = { ...NODE_POSITIONS };
    apiNodes.forEach((n, idx) => {
      if (!positions[n.id]) positions[n.id] = { x: idx * 320, y: 80 };
    });

    const nodes: Node[] = apiNodes.map((n) => ({
      id: n.id,
      type: 'flowCard',
      position: positions[n.id],
      data: {
        node: n,
        emphasized: LEAK_PATH.has(n.id),
        onClick: (clicked: APIFlowNode) => setSelectedNode(clicked),
      },
      draggable: true,
    }));

    const edges: Edge[] = apiEdges.map((e, idx) => {
      const emphasized = LEAK_PATH.has(e.from) && LEAK_PATH.has(e.to);
      return {
        id: `e-${idx}`,
        source: e.from,
        target: e.to,
        label: e.label,
        type: 'smoothstep',
        animated: emphasized,
        labelStyle: {
          fill: emphasized ? '#fda4af' : '#cbd5e1',
          fontFamily: 'ui-monospace, monospace',
          fontSize: 11,
          fontWeight: 600,
        },
        labelBgStyle: {
          fill: 'rgb(15 23 42)',
          fillOpacity: 0.9,
        },
        labelBgPadding: [6, 4],
        labelBgBorderRadius: 4,
        style: {
          stroke: emphasized ? '#e11d48' : '#475569',
          strokeWidth: emphasized ? 3 : 1.5,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: emphasized ? '#e11d48' : '#475569',
          width: 18,
          height: 18,
        },
      };
    });

    return { nodes, edges };
  }, [data]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs uppercase tracking-widest text-slate-500">
            <AlertOctagon className="h-3.5 w-3.5 text-rose-500" />
            Cross-File PHI Flow Analysis
          </div>
          <h1 className="text-3xl font-bold tracking-tight">
            {data?.title ?? 'PHI Flow Graph'}
          </h1>
          <div className="flex flex-wrap items-center gap-2">
            {data && (
              <>
                <Badge className="bg-slate-800 font-mono text-rose-300 hover:bg-slate-800">
                  {data.cfr_citation}
                </Badge>
                <Badge className={severityBadgeClass(data.severity)}>
                  {data.severity}
                </Badge>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">
          Legend
        </span>
        {(Object.keys(NODE_STYLE) as NodeKind[]).map((k) => (
          <div key={k} className="flex items-center gap-1.5">
            <span className={cn('h-3 w-3 rounded-sm', NODE_STYLE[k].color)} />
            <span>{NODE_STYLE[k].label}</span>
          </div>
        ))}
        <div className="ml-2 flex items-center gap-1.5 rounded-full border border-rose-900 px-2 py-0.5 text-rose-300">
          <span className="h-0.5 w-6 bg-rose-500" />
          PHI leak path
        </div>
      </div>

      {/* Graph */}
      <Card className="border-slate-800 bg-slate-900/40">
        <CardContent className="p-0">
          <div className="relative h-[480px] w-full overflow-hidden rounded-lg">
            {isLoading && (
              <div className="flex h-full items-center justify-center text-sm text-slate-500">
                Loading flow graph...
              </div>
            )}
            {error && !data && (
              <div className="flex h-full items-center justify-center text-sm text-rose-400">
                Failed to load flow graph.
              </div>
            )}
            {data && (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{ padding: 0.2 }}
                nodesDraggable
                nodesConnectable={false}
                elementsSelectable
                proOptions={{ hideAttribution: false }}
              >
                <Background
                  variant={BackgroundVariant.Dots}
                  gap={20}
                  size={1}
                  color="rgb(51 65 85)"
                />
                <Controls
                  showInteractive={false}
                  className="!bg-slate-900 !border-slate-700"
                />
              </ReactFlow>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Explanation */}
      <Card className="border-slate-800 bg-slate-900/40">
        <CardHeader>
          <CardTitle className="text-lg">Why per-file scanning misses this</CardTitle>
          <CardDescription>
            {data?.description ??
              'PHI flow that per-file scanning cannot catch — requires cross-module reasoning.'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-relaxed text-slate-300">
            Per-file scanning catches each violation in isolation, but cannot see
            that data flowing from the{' '}
            <span className="font-mono text-slate-100">Patient</span> model
            through the route handler ends up logged at the error handler.
            Bob&apos;s repo-wide reasoning identifies this multi-file pattern as
            a{' '}
            <span className="font-mono text-rose-300">§ 164.312(b)</span>{' '}
            audit control violation.
          </p>
        </CardContent>
      </Card>

      {/* Node detail dialog */}
      <Dialog open={!!selectedNode} onOpenChange={(o) => !o && setSelectedNode(null)}>
        <DialogContent className="max-w-lg border-slate-800 bg-slate-900 text-slate-50">
          {selectedNode && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">
                    {NODE_STYLE[selectedNode.type].label}
                  </span>
                  {LEAK_PATH.has(selectedNode.id) && (
                    <Badge className="bg-rose-900 text-rose-100 hover:bg-rose-900">
                      PHI flow
                    </Badge>
                  )}
                </div>
                <DialogTitle className="font-mono text-slate-100">
                  {selectedNode.label}
                </DialogTitle>
                <DialogDescription className="text-slate-300">
                  {selectedNode.sublabel}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-3 text-sm">
                {selectedNode.file ? (
                  <div className="rounded-md border border-slate-800 bg-slate-950 p-3 font-mono text-xs">
                    <div className="text-[10px] uppercase tracking-widest text-slate-500">
                      Source location
                    </div>
                    <div className="mt-1 text-slate-200">
                      {selectedNode.file}
                      {selectedNode.line ? `:${selectedNode.line}` : ''}
                    </div>
                  </div>
                ) : (
                  <div className="rounded-md border border-slate-800 bg-slate-950 p-3 text-xs italic text-slate-400">
                    No source file — this is a runtime sink, not a code location.
                  </div>
                )}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
