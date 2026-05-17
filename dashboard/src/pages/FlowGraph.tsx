import { useCallback, useMemo, useState } from 'react';
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
import { Play } from 'lucide-react';

import 'reactflow/dist/style.css';

import { GlassCard } from '@/components/ui/glass-card';
import {
  APIError,
  FlowGraph as FlowGraphData,
  FlowNode as APIFlowNode,
  getFlowGraph,
} from '@/lib/api';
import { cn } from '@/lib/utils';

// ---------------------------------------------------------------------------
// Node visual definition
// ---------------------------------------------------------------------------

type NodeKind = APIFlowNode['type'];

const NODE_STYLE: Record<
  NodeKind,
  {
    label: string;
    border: string;
    accent: string;
    glow: string;
    dotColor: string;
  }
> = {
  schema: {
    label: 'Schema',
    border: 'border-slate-600/60',
    accent: 'text-slate-300',
    glow: '',
    dotColor: 'bg-slate-400',
  },
  route: {
    label: 'Route Handler',
    border: 'border-slate-600/60',
    accent: 'text-slate-300',
    glow: '',
    dotColor: 'bg-slate-400',
  },
  error_handler: {
    label: 'Error Handler',
    border: 'border-rose-600/60',
    accent: 'text-rose-300',
    glow: 'shadow-[0_0_0_1px_rgba(225,29,72,0.25),0_8px_32px_-8px_rgba(225,29,72,0.45)]',
    dotColor: 'bg-rose-500',
  },
  sink: {
    label: 'PHI Sink',
    border: 'border-rose-900/80',
    accent: 'text-rose-200',
    glow: 'shadow-[0_0_0_1px_rgba(159,18,57,0.45),0_8px_36px_-6px_rgba(159,18,57,0.55)]',
    dotColor: 'bg-rose-700',
  },
};

interface FlowCardData {
  node: APIFlowNode;
  emphasized: boolean;
}

function FlowCardNode({ data }: NodeProps<FlowCardData>) {
  const { node, emphasized } = data;
  const style = NODE_STYLE[node.type];

  return (
    <div
      className={cn(
        'glass-strong group relative w-[244px] cursor-default overflow-hidden rounded-xl border text-left transition-all duration-200',
        style.border,
        style.glow,
        emphasized && style.glow,
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-1.5 !w-1.5 !border-0 !bg-white/30"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!h-1.5 !w-1.5 !border-0 !bg-white/30"
      />

      <div className="p-4">
        <div className="mb-2.5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className={cn('h-1.5 w-1.5 rounded-full', style.dotColor)} />
            <span className="text-[0.625rem] font-semibold uppercase tracking-[0.18em] text-ink-tertiary">
              {style.label}
            </span>
          </div>
          {emphasized && (
            <span className="text-[0.5625rem] font-semibold uppercase tracking-[0.14em] text-rose-300/90">
              PHI
            </span>
          )}
        </div>

        <div
          className={cn(
            'font-mono text-[0.8125rem] font-semibold leading-tight text-ink-primary',
          )}
        >
          {node.label}
        </div>

        <div className="mt-1.5 text-[0.75rem] leading-snug text-ink-secondary">
          {node.sublabel}
        </div>

        {node.file && (
          <div className="mt-3 flex items-center justify-between gap-2 border-t border-white/5 pt-2.5">
            <span className="truncate font-mono text-[0.6875rem] text-ink-tertiary">
              {node.file}
            </span>
            {node.line !== null && (
              <span className="tnum text-[0.625rem] uppercase tracking-[0.14em] text-ink-tertiary">
                L{node.line}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

const nodeTypes = { flowCard: FlowCardNode };

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

export default function FlowGraphPage() {
  const { data, isLoading, error } = useQuery<FlowGraphData, APIError>({
    queryKey: ['flow-graph'],
    queryFn: getFlowGraph,
  });

  const [replayKey, setReplayKey] = useState(0);

  const { nodes, edges } = useMemo<{ nodes: Node[]; edges: Edge[] }>(() => {
    if (!data) return { nodes: [], edges: [] };

    const apiNodes = data.nodes;
    const apiEdges = data.edges;

    const positions: Record<string, { x: number; y: number }> = {
      ...NODE_POSITIONS,
    };
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
      },
      draggable: true,
    }));

    const edges: Edge[] = apiEdges.map((e, idx) => {
      const emphasized = LEAK_PATH.has(e.from) && LEAK_PATH.has(e.to);
      return {
        id: `e-${idx}-${replayKey}`,
        source: e.from,
        target: e.to,
        label: e.label,
        type: 'smoothstep',
        animated: emphasized,
        labelStyle: {
          fill: emphasized ? '#fda4af' : '#94a3b8',
          fontFamily: 'ui-monospace, SFMono-Regular, monospace',
          fontSize: 10.5,
          fontWeight: 600,
          letterSpacing: '0.04em',
        },
        labelBgStyle: {
          fill: emphasized ? 'rgba(76, 5, 25, 0.85)' : 'rgba(15, 23, 42, 0.85)',
          fillOpacity: 1,
          stroke: emphasized ? 'rgba(225,29,72,0.4)' : 'rgba(255,255,255,0.08)',
        },
        labelBgPadding: [8, 5],
        labelBgBorderRadius: 6,
        style: {
          stroke: emphasized ? '#e11d48' : 'rgba(148, 163, 184, 0.35)',
          strokeWidth: emphasized ? 1.75 : 1,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: emphasized ? '#e11d48' : 'rgba(148, 163, 184, 0.5)',
          width: 16,
          height: 16,
        },
      };
    });

    return { nodes, edges };
  }, [data, replayKey]);

  const replay = useCallback(() => {
    setReplayKey((k) => k + 1);
  }, []);

  return (
    <div className="space-y-12">
      {/* Header */}
      <header className="space-y-4 animate-fade-in">
        <div className="flex items-center gap-3 text-eyebrow">
          <span className="h-1 w-1 rounded-full bg-rose-500 animate-pulse-glow" />
          Cross-File Analysis · § {data?.cfr_citation?.replace(/^§\s*/, '') ?? '164.312(b)'}
        </div>
        <h1 className="font-display max-w-[18ch] text-5xl tracking-display text-ink-primary sm:text-6xl lg:text-7xl">
          {data?.title ?? 'PHI Leak Through Error Handler'}
        </h1>
        <p className="max-w-[70ch] text-[1rem] leading-relaxed text-ink-secondary">
          {data?.description ??
            'A single PHI field flows from the patient schema through a route handler into an error logger — a vulnerability that per-file scanning cannot catch.'}
        </p>
      </header>

      {/* Graph canvas */}
      <div className="relative animate-fade-in" style={{ animationDelay: '120ms' }}>
        <GlassCard padding="none" className="overflow-hidden">
          <div className="flex items-center justify-between border-b border-white/5 px-5 py-3">
            <div className="flex items-center gap-2 text-eyebrow">
              <span>Flow Canvas</span>
              <span className="text-ink-tertiary/50">·</span>
              <span className="font-mono normal-case tracking-normal text-ink-tertiary">
                {data?.nodes.length ?? 0} nodes, {data?.edges.length ?? 0} edges
              </span>
            </div>
            <button
              type="button"
              onClick={replay}
              className="group inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[0.6875rem] font-medium text-ink-secondary transition-all duration-200 hover:border-white/20 hover:bg-white/[0.07] hover:text-ink-primary"
              title="Replay edge animations"
            >
              <Play className="h-3 w-3 fill-current" />
              Replay
            </button>
          </div>

          <div className="relative h-[520px] w-full">
            {/* Inner vignette */}
            <div
              aria-hidden="true"
              className="pointer-events-none absolute inset-0 z-10 rounded-b-xl"
              style={{
                boxShadow:
                  'inset 0 1px 0 rgba(255,255,255,0.04), inset 0 0 60px rgba(0,0,0,0.45)',
              }}
            />
            {isLoading && (
              <div className="flex h-full items-center justify-center text-sm text-ink-tertiary">
                Loading flow graph…
              </div>
            )}
            {error && !data && (
              <div className="flex h-full items-center justify-center text-sm text-rose-300/80">
                Failed to load flow graph.
              </div>
            )}
            {data && (
              <ReactFlow
                key={replayKey}
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{ padding: 0.22 }}
                nodesDraggable
                nodesConnectable={false}
                elementsSelectable={false}
                proOptions={{ hideAttribution: true }}
              >
                <Background
                  variant={BackgroundVariant.Dots}
                  gap={28}
                  size={1}
                  color="rgba(255,255,255,0.05)"
                />
                <Controls
                  showInteractive={false}
                  position="bottom-right"
                />
              </ReactFlow>
            )}
          </div>

          {/* Legend strip */}
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-white/5 px-5 py-3 text-[0.6875rem] text-ink-tertiary">
            <span className="text-eyebrow">Legend</span>
            {(Object.keys(NODE_STYLE) as NodeKind[]).map((k) => (
              <div key={k} className="flex items-center gap-1.5">
                <span className={cn('h-1.5 w-1.5 rounded-full', NODE_STYLE[k].dotColor)} />
                <span className="text-ink-secondary">{NODE_STYLE[k].label}</span>
              </div>
            ))}
            <div className="ml-auto flex items-center gap-1.5">
              <span
                aria-hidden="true"
                className="h-px w-6"
                style={{
                  background:
                    'repeating-linear-gradient(90deg, #e11d48 0 4px, transparent 4px 8px)',
                }}
              />
              <span className="text-rose-300/80">PHI leak path</span>
            </div>
          </div>
        </GlassCard>
      </div>

      {/* Why this matters */}
      <div
        className="grid gap-5 lg:grid-cols-[1.4fr_1fr] animate-fade-in"
        style={{ animationDelay: '180ms' }}
      >
        <GlassCard padding="lg">
          <div className="space-y-4">
            <div className="space-y-1">
              <span className="text-eyebrow">Why this matters</span>
              <h2 className="text-xl font-semibold tracking-tight text-ink-primary">
                Per-file scanning is structurally blind to this class of leak
              </h2>
            </div>
            <p className="max-w-[68ch] text-[0.9375rem] leading-relaxed text-ink-secondary">
              A traditional linter inspects each file in isolation. Looking at{' '}
              <span className="font-mono text-ink-primary">patient.py</span>{' '}
              alone, the schema is correct. Looking at{' '}
              <span className="font-mono text-ink-primary">routes.py</span>{' '}
              alone, the handler appears to merely surface an exception. Only
              when the call graph is traced across modules does it become
              visible that an{' '}
              <span className="text-rose-300">unhandled exception</span> is
              caught by a generic error handler that{' '}
              <span className="text-rose-300">logs the request body</span>,
              which contains <span className="font-mono">SSN</span> and{' '}
              <span className="font-mono">DOB</span> — protected health
              information per 45 CFR § 160.103.
            </p>
            <p className="max-w-[68ch] text-[0.9375rem] leading-relaxed text-ink-secondary">
              This is precisely the multi-file, cross-module reasoning that
              repo-wide analysis is built to surface — a violation of{' '}
              <span className="font-mono text-rose-300">§ 164.312(b)</span>{' '}
              (audit controls) and{' '}
              <span className="font-mono text-rose-300">
                § 164.308(a)(1)(ii)(D)
              </span>{' '}
              (information system activity review) operating together.
            </p>
          </div>
        </GlassCard>

        <GlassCard padding="lg">
          <div className="space-y-4">
            <span className="text-eyebrow">Citations</span>
            <div className="space-y-3">
              <CitationRow
                section="§ 164.312(b)"
                title="Audit controls"
                text="Implement hardware, software, and procedural mechanisms that record and examine activity in information systems containing electronic protected health information."
              />
              <div className="dotted-rule" />
              <CitationRow
                section="§ 164.308(a)(1)(ii)(D)"
                title="Information system activity review"
                text="Implement procedures to regularly review records of activity such as audit logs, access reports, and security incident tracking reports."
              />
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}

function CitationRow({
  section,
  title,
  text,
}: {
  section: string;
  title: string;
  text: string;
}) {
  return (
    <div className="space-y-1">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-mono text-[0.75rem] text-rose-300">
          {section}
        </span>
        <span className="text-[0.6875rem] uppercase tracking-[0.14em] text-ink-tertiary">
          HIPAA
        </span>
      </div>
      <div className="text-[0.8125rem] font-semibold text-ink-primary">
        {title}
      </div>
      <p className="text-[0.75rem] leading-relaxed text-ink-tertiary">
        {text}
      </p>
    </div>
  );
}
