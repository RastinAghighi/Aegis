import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import {
  AlertTriangle,
  ArrowRight,
  ChevronRight,
  Loader2,
  Network,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/components/ui/toast';
import {
  APIError,
  Finding,
  Report,
  SEVERITY_HEX,
  SEVERITY_ORDER,
  Severity,
  getFindings,
  runScan,
  severityBadgeClass,
} from '@/lib/api';

const TOP_RISK_RULES = ['AC-1', 'AC-3', 'EN-1'];

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return 'never';
  const d = new Date(iso);
  return d.toLocaleString();
}

function riskScoreClass(score: number): string {
  if (score >= 80) return 'text-emerald-400';
  if (score >= 50) return 'text-amber-400';
  if (score >= 25) return 'text-rose-400';
  return 'text-rose-500';
}

export default function Overview() {
  const qc = useQueryClient();
  const { toast } = useToast();

  const { data, isLoading, error } = useQuery<Report, APIError>({
    queryKey: ['findings'],
    queryFn: getFindings,
  });

  const scanMutation = useMutation({
    mutationFn: runScan,
    onSuccess: (report) => {
      qc.setQueryData(['findings'], report);
      toast({
        title: 'Scan complete',
        description: `${report.findings.length} findings — risk score ${report.risk_score}/100`,
        variant: 'success',
      });
    },
    onError: (err) => {
      if (err instanceof APIError && err.status === 429) {
        toast({
          title: 'Rate limited',
          description: 'Try again in 60 seconds.',
          variant: 'destructive',
        });
      } else {
        toast({
          title: 'Scan failed',
          description: err instanceof Error ? err.message : String(err),
          variant: 'destructive',
        });
      }
    },
  });

  const findings = data?.findings ?? [];
  const counts = data?.counts_by_severity ?? {
    CRITICAL: 0,
    HIGH: 0,
    MEDIUM: 0,
    LOW: 0,
  };
  const riskScore = data?.risk_score ?? 0;

  const donutData = useMemo(
    () =>
      SEVERITY_ORDER.map((s) => ({
        name: s,
        value: counts[s] ?? 0,
        fill: SEVERITY_HEX[s],
      })).filter((d) => d.value > 0),
    [counts],
  );

  const topRisks: Finding[] = useMemo(() => {
    const out: Finding[] = [];
    for (const id of TOP_RISK_RULES) {
      const match = findings.find((f) => f.rule_id === id);
      if (match) out.push(match);
    }
    // Fill remaining slots with worst remaining CRITICAL findings.
    if (out.length < 3) {
      const ids = new Set(out.map((f) => f.id));
      for (const f of findings) {
        if (out.length >= 3) break;
        if (ids.has(f.id)) continue;
        if (f.severity === 'CRITICAL') out.push(f);
      }
    }
    return out.slice(0, 3);
  }, [findings]);

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
          <p className="text-sm text-slate-400">
            HIPAA Technical Safeguards posture · target{' '}
            <span className="font-mono text-slate-300">
              {data?.target ?? 'demo/patient-portal'}
            </span>
          </p>
        </div>
        <Button
          onClick={() => scanMutation.mutate()}
          disabled={scanMutation.isPending}
          className="bg-slate-50 text-slate-950 hover:bg-slate-200"
        >
          {scanMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Scanning...
            </>
          ) : (
            <>
              <RefreshCw className="mr-2 h-4 w-4" />
              Run scan
            </>
          )}
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Risk score */}
        <Card className="border-slate-800 bg-slate-900/40 lg:col-span-1">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-widest text-slate-500">
              Risk Score
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-2">
            <div className="flex items-end gap-2">
              <span
                className={`text-7xl font-bold tabular-nums leading-none ${riskScoreClass(riskScore)}`}
              >
                {isLoading ? '—' : riskScore}
              </span>
              <span className="pb-2 text-2xl text-slate-500">/ 100</span>
            </div>
          </CardContent>
          <CardFooter className="block pt-0 text-xs leading-relaxed text-slate-500">
            <code className="text-slate-400">
              max(0, 100 − (10·crit + 5·high + 2·med + 1·low))
            </code>
            <div className="mt-1">
              Lower = more exposure. 100 = no findings detected.
            </div>
          </CardFooter>
        </Card>

        {/* Donut */}
        <Card className="border-slate-800 bg-slate-900/40 lg:col-span-1">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-widest text-slate-500">
              Severity Distribution
            </CardDescription>
            <CardTitle className="text-2xl">{findings.length} findings</CardTitle>
          </CardHeader>
          <CardContent className="h-52">
            {donutData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-slate-500">
                No findings to chart.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={donutData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={2}
                    stroke="rgb(15 23 42)"
                  >
                    {donutData.map((d) => (
                      <Cell key={d.name} fill={d.fill} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      background: 'rgb(15 23 42)',
                      border: '1px solid rgb(51 65 85)',
                      borderRadius: 6,
                      color: 'rgb(248 250 252)',
                      fontSize: 12,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
          <CardFooter className="flex flex-wrap gap-2 pt-0">
            {SEVERITY_ORDER.map((s) => (
              <div key={s} className="flex items-center gap-1.5 text-xs">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: SEVERITY_HEX[s] }}
                />
                <span className="font-mono text-slate-500">{s}</span>
                <span className="font-semibold text-slate-300">
                  {counts[s] ?? 0}
                </span>
              </div>
            ))}
          </CardFooter>
        </Card>

        {/* Scan meta */}
        <Card className="border-slate-800 bg-slate-900/40 lg:col-span-1">
          <CardHeader className="pb-2">
            <CardDescription className="text-xs uppercase tracking-widest text-slate-500">
              Last Scan
            </CardDescription>
            <CardTitle className="text-base font-medium text-slate-200">
              {formatTimestamp(data?.generated_at)}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Findings</span>
              <span className="font-mono font-semibold">{findings.length}</span>
            </div>
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-slate-400">Critical</span>
              <span className="font-mono font-semibold text-rose-400">
                {counts.CRITICAL ?? 0}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-slate-400">High</span>
              <span className="font-mono font-semibold text-amber-400">
                {counts.HIGH ?? 0}
              </span>
            </div>
          </CardContent>
          <CardFooter className="flex gap-2 pt-2">
            <Button asChild variant="outline" size="sm" className="border-slate-700 bg-transparent text-slate-200 hover:bg-slate-800">
              <Link to="/findings">
                View all findings <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm" className="border-slate-700 bg-transparent text-slate-200 hover:bg-slate-800">
              <Link to="/flow-graph">
                <Network className="mr-1 h-3 w-3" /> Cross-file analysis
              </Link>
            </Button>
          </CardFooter>
        </Card>
      </div>

      <Separator />

      {/* Top Risks */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold tracking-tight">Top Risks</h2>
            <p className="text-sm text-slate-400">
              The three most exposed CRITICAL findings.
            </p>
          </div>
          <Link
            to="/findings"
            className="flex items-center text-xs text-slate-400 hover:text-slate-200"
          >
            All findings <ChevronRight className="h-3 w-3" />
          </Link>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {topRisks.length === 0 ? (
            <Card className="border-slate-800 bg-slate-900/40 md:col-span-3">
              <CardContent className="py-8 text-center text-sm text-slate-500">
                {isLoading
                  ? 'Loading findings...'
                  : error
                    ? 'Backend unavailable.'
                    : 'No critical risks detected.'}
              </CardContent>
            </Card>
          ) : (
            topRisks.map((f) => <TopRiskCard key={f.id} f={f} />)
          )}
        </div>
      </section>
    </div>
  );
}

function TopRiskCard({ f }: { f: Finding }) {
  const sev: Severity = f.severity;
  return (
    <Card className="border-slate-800 bg-slate-900/40 transition-colors hover:border-slate-700">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            {sev === 'CRITICAL' ? (
              <ShieldAlert className="h-4 w-4 text-rose-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-amber-500" />
            )}
            <span className="font-mono text-xs text-slate-400">{f.rule_id}</span>
          </div>
          <Badge className={severityBadgeClass(sev)}>{sev}</Badge>
        </div>
        <CardTitle className="text-base text-slate-100">{f.rule_title}</CardTitle>
        <CardDescription className="text-xs">
          45 CFR § {f.cfr.section} — {f.cfr.title}
        </CardDescription>
      </CardHeader>
      <CardContent className="pb-2">
        <div className="rounded-md border border-slate-800 bg-slate-950/60 p-3">
          <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-slate-500">
            {f.evidence.file}:{f.evidence.line_start}
          </div>
          <pre className="overflow-hidden whitespace-pre-wrap break-words font-mono text-xs text-slate-300">
            {f.evidence.snippet.slice(0, 140)}
            {f.evidence.snippet.length > 140 ? '…' : ''}
          </pre>
        </div>
      </CardContent>
      <CardFooter className="pt-2 text-xs text-slate-400">
        <Link
          to="/findings"
          className="inline-flex items-center hover:text-slate-200"
        >
          View details <ArrowRight className="ml-1 h-3 w-3" />
        </Link>
      </CardFooter>
    </Card>
  );
}
