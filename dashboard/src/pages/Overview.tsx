import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts';
import { ArrowUpRight, Loader2, RefreshCw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  GlassCard,
  GlassCardEyebrow,
} from '@/components/ui/glass-card';
import { Tooltip } from '@/components/ui/tooltip';
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
} from '@/lib/api';
import { cn } from '@/lib/utils';

const TOP_RISK_RULES = ['AC-1', 'AC-3', 'EN-1'];

const SEV_LABEL: Record<Severity, string> = {
  CRITICAL: 'Critical',
  HIGH: 'High',
  MEDIUM: 'Medium',
  LOW: 'Low',
};

function useCountUp(target: number, duration = 1200) {
  const [value, setValue] = useState(0);
  const startRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const lastTarget = useRef(target);

  useEffect(() => {
    if (target === lastTarget.current && startRef.current !== null) return;
    lastTarget.current = target;
    startRef.current = null;

    const from = 0;
    const tick = (ts: number) => {
      if (startRef.current === null) startRef.current = ts;
      const elapsed = ts - startRef.current;
      const t = Math.min(1, elapsed / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(from + (target - from) * eased));
      if (t < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    };
    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [target, duration]);

  return value;
}

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return 'never';
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function Overview() {
  const qc = useQueryClient();
  const { toast } = useToast();

  const { data, isLoading } = useQuery<Report, APIError>({
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
  const target = data?.target ?? 'demo/patient-portal';
  const ruleCount = useMemo(
    () => new Set(findings.map((f) => f.rule_id)).size,
    [findings],
  );

  const findingCount = useCountUp(findings.length);
  const score = useCountUp(riskScore);

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
    <div className="space-y-16">
      {/* ============ HERO ============ */}
      <section className="grid gap-10 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-6 animate-fade-in">
          <div className="flex items-center justify-between gap-4">
            <span className="text-eyebrow">
              HIPAA Technical Safeguards · {target.toUpperCase()}
            </span>
            <Button
              onClick={() => scanMutation.mutate()}
              disabled={scanMutation.isPending}
              className="h-9 rounded-full border border-white/10 bg-white/5 px-4 text-[0.8125rem] font-medium text-ink-primary backdrop-blur transition hover:bg-white/10"
            >
              {scanMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                  Scanning
                </>
              ) : (
                <>
                  <RefreshCw className="mr-2 h-3.5 w-3.5" />
                  Run scan
                </>
              )}
            </Button>
          </div>

          <div className="space-y-3">
            <div className="font-display tnum text-[7rem] leading-[0.9] text-ink-primary sm:text-[8rem]">
              {isLoading ? '—' : findingCount}
            </div>
            <div className="max-w-xl text-[1.5rem] font-light leading-tight text-ink-secondary">
              violations identified across{' '}
              <span className="text-ink-primary">{ruleCount}</span> rule
              {ruleCount === 1 ? '' : 's'}
            </div>
          </div>

          <Tooltip
            label={
              <span className="font-mono text-[11px]">
                max(0, 100 − (10·crit + 5·high + 2·med + 1·low))
              </span>
            }
          >
            <span className="inline-flex cursor-help items-baseline gap-2 text-[1.125rem] text-ink-secondary">
              <span className="text-eyebrow">Risk Score</span>
              <span className="tnum text-ink-primary">{score}</span>
              <span className="text-ink-tertiary">/ 100</span>
            </span>
          </Tooltip>

          <div className="dotted-rule pt-1" />

          <div className="flex items-center gap-6 text-xs text-ink-tertiary">
            <span>
              Last scan{' '}
              <span className="text-ink-secondary">
                {formatTimestamp(data?.generated_at)}
              </span>
            </span>
            <span className="hidden h-3 w-px bg-white/10 sm:inline-block" />
            <Link
              to="/findings"
              className="hidden items-center gap-1 text-ink-secondary transition-colors hover:text-ink-primary sm:inline-flex"
            >
              View all findings
              <ArrowUpRight className="h-3 w-3" />
            </Link>
          </div>
        </div>

        {/* Right column: donut */}
        <div className="animate-fade-in" style={{ animationDelay: '80ms' }}>
          <GlassCard padding="lg" className="space-y-5">
            <div className="flex items-start justify-between">
              <div>
                <GlassCardEyebrow>Severity Distribution</GlassCardEyebrow>
                <div className="mt-1 text-lg font-semibold tracking-tight text-ink-primary">
                  {findings.length} findings
                </div>
              </div>
            </div>

            <div className="relative mx-auto h-44 w-44 animate-donut-in">
              {donutData.length === 0 ? (
                <div className="flex h-full items-center justify-center text-xs text-ink-tertiary">
                  No findings
                </div>
              ) : (
                <>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={donutData}
                        dataKey="value"
                        nameKey="name"
                        innerRadius={56}
                        outerRadius={82}
                        paddingAngle={3}
                        stroke="transparent"
                        startAngle={90}
                        endAngle={-270}
                      >
                        {donutData.map((d) => (
                          <Cell key={d.name} fill={d.fill} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                    <span className="tnum font-display text-3xl text-ink-primary">
                      {findings.length}
                    </span>
                    <span className="text-[0.625rem] uppercase tracking-[0.2em] text-ink-tertiary">
                      total
                    </span>
                  </div>
                </>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              {SEVERITY_ORDER.map((s, i) => (
                <div
                  key={s}
                  className="rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5 animate-fade-in"
                  style={{ animationDelay: `${120 + i * 50}ms` }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ background: SEVERITY_HEX[s] }}
                      />
                      <span className="text-[0.6875rem] uppercase tracking-[0.14em] text-ink-tertiary">
                        {SEV_LABEL[s]}
                      </span>
                    </div>
                    <span className="tnum text-sm font-semibold text-ink-primary">
                      {counts[s] ?? 0}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </section>

      {/* ============ TOP RISKS ============ */}
      <section className="space-y-6">
        <div className="flex items-end justify-between">
          <div className="space-y-1">
            <span className="text-eyebrow">Top Risks</span>
            <h2 className="text-2xl font-semibold tracking-tight text-ink-primary">
              Most exposed findings
            </h2>
          </div>
          <Link
            to="/findings"
            className="group inline-flex items-center gap-1 text-xs text-ink-secondary transition-colors hover:text-ink-primary"
          >
            All findings
            <ArrowUpRight className="h-3 w-3 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Link>
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <GlassCard key={i} padding="lg" className="space-y-3">
                <div className="skeleton h-3 w-24" />
                <div className="skeleton h-5 w-3/4" />
                <div className="skeleton h-3 w-full" />
                <div className="skeleton h-3 w-2/3" />
              </GlassCard>
            ))
          ) : topRisks.length === 0 ? (
            <GlassCard padding="lg" className="md:col-span-3 text-center text-sm text-ink-tertiary">
              No critical risks detected.
            </GlassCard>
          ) : (
            topRisks.map((f, i) => <TopRiskCard key={f.id} f={f} index={i} />)
          )}
        </div>
      </section>
    </div>
  );
}

function TopRiskCard({ f, index }: { f: Finding; index: number }) {
  const sev: Severity = f.severity;
  const sevToken = sev === 'CRITICAL' ? 'critical' : sev === 'HIGH' ? 'high' : 'default';
  return (
    <Link
      to="/findings"
      state={{ ruleFilter: f.rule_id }}
      className="block animate-fade-in"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <GlassCard
        interactive
        padding="lg"
        tone={sevToken}
        className="group h-full"
      >
        <div className="flex items-start justify-between gap-3">
          <span className="text-[0.6875rem] font-semibold uppercase tracking-[0.18em] text-ink-tertiary">
            45 CFR § {f.cfr.section}
          </span>
          <SeverityPill sev={sev} />
        </div>

        <h3 className="mt-3 text-[0.9375rem] font-semibold leading-snug tracking-tight text-ink-primary">
          {f.rule_title}
        </h3>

        <p className="mt-2 text-[0.8125rem] leading-relaxed text-ink-secondary">
          {f.evidence.why.length > 110
            ? f.evidence.why.slice(0, 110) + '…'
            : f.evidence.why}
        </p>

        <div className="mt-4 flex items-center justify-between border-t border-white/5 pt-3 text-[0.6875rem]">
          <span className="font-mono text-ink-tertiary">
            {f.rule_id} · {f.evidence.file.split('/').pop()}
          </span>
          <ArrowUpRight className="h-3.5 w-3.5 text-ink-tertiary transition-all group-hover:text-ink-primary group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
        </div>
      </GlassCard>
    </Link>
  );
}

function SeverityPill({ sev }: { sev: Severity }) {
  const tone: Record<Severity, string> = {
    CRITICAL:
      'border-rose-500/30 bg-rose-500/10 text-rose-300',
    HIGH: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
    MEDIUM: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-200',
    LOW: 'border-blue-500/30 bg-blue-500/10 text-blue-200',
  };
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-[0.625rem] font-semibold uppercase tracking-[0.14em]',
        tone[sev],
      )}
    >
      {sev}
    </span>
  );
}
