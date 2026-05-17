import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ExternalLink } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  APIError,
  Finding,
  Report,
  SEVERITY_ORDER,
  Severity,
  getFindings,
  severityBadgeClass,
} from '@/lib/api';
import { cn } from '@/lib/utils';

function Chip({
  active,
  onClick,
  children,
  count,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  count?: number;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors',
        active
          ? 'border-slate-50 bg-slate-50 text-slate-950'
          : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:border-slate-700 hover:bg-slate-800',
      )}
    >
      {children}
      {typeof count === 'number' && (
        <span
          className={cn(
            'rounded-full px-1.5 py-0.5 text-[10px] font-mono',
            active ? 'bg-slate-900 text-slate-100' : 'bg-slate-800 text-slate-400',
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
}

export default function Findings() {
  const { data, isLoading, error } = useQuery<Report, APIError>({
    queryKey: ['findings'],
    queryFn: getFindings,
  });

  const findings = data?.findings ?? [];

  const [selected, setSelected] = useState<Finding | null>(null);
  const [sevFilter, setSevFilter] = useState<Severity | null>(null);
  const [ruleFilter, setRuleFilter] = useState<string | null>(null);

  const sevCounts = useMemo(() => {
    const out: Record<Severity, number> = {
      CRITICAL: 0,
      HIGH: 0,
      MEDIUM: 0,
      LOW: 0,
    };
    for (const f of findings) out[f.severity]++;
    return out;
  }, [findings]);

  const ruleIds = useMemo(() => {
    const set = new Set<string>();
    for (const f of findings) set.add(f.rule_id);
    return Array.from(set).sort();
  }, [findings]);

  const filtered = useMemo(
    () =>
      findings.filter(
        (f) =>
          (!sevFilter || f.severity === sevFilter) &&
          (!ruleFilter || f.rule_id === ruleFilter),
      ),
    [findings, sevFilter, ruleFilter],
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Findings</h1>
        <p className="text-sm text-slate-400">
          {isLoading
            ? 'Loading findings...'
            : error
              ? 'Backend unavailable.'
              : `${filtered.length} of ${findings.length} findings shown.`}
        </p>
      </div>

      {/* Filter chips */}
      <div className="space-y-3">
        <div className="space-y-1.5">
          <div className="text-xs font-semibold uppercase tracking-widest text-slate-500">
            Severity
          </div>
          <div className="flex flex-wrap gap-2">
            <Chip
              active={sevFilter === null}
              onClick={() => setSevFilter(null)}
              count={findings.length}
            >
              All
            </Chip>
            {SEVERITY_ORDER.map((s) => (
              <Chip
                key={s}
                active={sevFilter === s}
                onClick={() => setSevFilter(sevFilter === s ? null : s)}
                count={sevCounts[s]}
              >
                <span
                  className={cn(
                    'h-2 w-2 rounded-full',
                    s === 'CRITICAL' && 'bg-rose-600',
                    s === 'HIGH' && 'bg-amber-600',
                    s === 'MEDIUM' && 'bg-yellow-500',
                    s === 'LOW' && 'bg-blue-500',
                  )}
                />
                {s}
              </Chip>
            ))}
          </div>
        </div>

        {ruleIds.length > 0 && (
          <div className="space-y-1.5">
            <div className="text-xs font-semibold uppercase tracking-widest text-slate-500">
              Rule
            </div>
            <div className="flex flex-wrap gap-2">
              <Chip
                active={ruleFilter === null}
                onClick={() => setRuleFilter(null)}
              >
                All
              </Chip>
              {ruleIds.map((r) => (
                <Chip
                  key={r}
                  active={ruleFilter === r}
                  onClick={() => setRuleFilter(ruleFilter === r ? null : r)}
                >
                  <span className="font-mono">{r}</span>
                </Chip>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-900/40">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-800 hover:bg-transparent">
              <TableHead className="text-slate-400">ID</TableHead>
              <TableHead className="text-slate-400">Rule</TableHead>
              <TableHead className="text-slate-400">CFR</TableHead>
              <TableHead className="text-slate-400">Severity</TableHead>
              <TableHead className="text-slate-400">File:Line</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  className="py-10 text-center text-sm text-slate-500"
                >
                  No findings match the active filters.
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((f) => (
                <TableRow
                  key={f.id}
                  onClick={() => setSelected(f)}
                  className="cursor-pointer border-slate-800 hover:bg-slate-800/40"
                >
                  <TableCell className="font-mono text-xs text-slate-500">
                    {f.id.slice(0, 8)}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col">
                      <span className="font-mono text-xs text-slate-400">
                        {f.rule_id}
                      </span>
                      <span className="text-sm text-slate-100">{f.rule_title}</span>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-slate-400">
                    § {f.cfr.section}
                  </TableCell>
                  <TableCell>
                    <Badge className={severityBadgeClass(f.severity)}>
                      {f.severity}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-slate-400">
                    {f.evidence.file}:{f.evidence.line_start}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <Dialog open={!!selected} onOpenChange={(o) => !o && setSelected(null)}>
        <DialogContent className="max-w-3xl border-slate-800 bg-slate-900 text-slate-50">
          {selected && (
            <>
              <DialogHeader>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-mono text-sm text-slate-400">
                    {selected.rule_id}
                  </span>
                  <DialogTitle className="text-slate-100">
                    {selected.rule_title}
                  </DialogTitle>
                  <Badge className={severityBadgeClass(selected.severity)}>
                    {selected.severity}
                  </Badge>
                </div>
                <DialogDescription className="text-slate-400">
                  Finding {selected.id.slice(0, 8)} · detected{' '}
                  {new Date(selected.detected_at).toLocaleString()}
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 text-sm">
                <div className="rounded-md border border-rose-900/60 bg-rose-950/30 p-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-rose-400">
                    45 CFR § {selected.cfr.section}
                    {selected.cfr.url && (
                      <a
                        href={selected.cfr.url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="inline-flex items-center text-rose-300 hover:text-rose-200"
                      >
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-slate-100">
                    {selected.cfr.title}
                  </div>
                  <p className="mt-2 text-xs italic leading-relaxed text-slate-300">
                    {selected.cfr.text}
                  </p>
                </div>

                <div>
                  <div className="mb-1 text-xs font-semibold uppercase tracking-widest text-slate-500">
                    Evidence
                  </div>
                  <div className="mb-1 font-mono text-xs text-slate-400">
                    {selected.evidence.file}:{selected.evidence.line_start}-
                    {selected.evidence.line_end}
                  </div>
                  <pre className="overflow-x-auto rounded-md border border-slate-800 bg-slate-950 p-3 font-mono text-xs leading-relaxed text-slate-200">
                    <code>{selected.evidence.snippet}</code>
                  </pre>
                </div>

                <div>
                  <div className="mb-1 text-xs font-semibold uppercase tracking-widest text-slate-500">
                    Why this is a violation
                  </div>
                  <p className="leading-relaxed text-slate-300">
                    {selected.evidence.why}
                  </p>
                </div>

                <div>
                  <div className="mb-1 text-xs font-semibold uppercase tracking-widest text-slate-500">
                    Remediation
                  </div>
                  <pre className="overflow-x-auto rounded-md border border-emerald-900/60 bg-emerald-950/20 p-3 font-mono text-xs leading-relaxed text-emerald-100">
                    {selected.remediation}
                  </pre>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
