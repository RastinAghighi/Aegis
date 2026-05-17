import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ChevronDown, ExternalLink } from 'lucide-react';

import { GlassCard } from '@/components/ui/glass-card';
import {
  APIError,
  Finding,
  Report,
  SEVERITY_HEX,
  SEVERITY_ORDER,
  Severity,
  getFindings,
} from '@/lib/api';
import { cn } from '@/lib/utils';

const SEV_TEXT: Record<Severity, string> = {
  CRITICAL: 'text-rose-300',
  HIGH: 'text-amber-200',
  MEDIUM: 'text-yellow-200',
  LOW: 'text-blue-200',
};

const SEV_PILL: Record<Severity, string> = {
  CRITICAL: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
  HIGH: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
  MEDIUM: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-200',
  LOW: 'border-blue-500/30 bg-blue-500/10 text-blue-200',
};

function SeverityPill({ sev }: { sev: Severity }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-[0.625rem] font-semibold uppercase tracking-[0.14em]',
        SEV_PILL[sev],
      )}
    >
      {sev}
    </span>
  );
}

function Chip({
  active,
  onClick,
  children,
  count,
  glowColor,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  count?: number;
  glowColor?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={
        active && glowColor
          ? {
              boxShadow: `0 0 0 1px ${glowColor}55, 0 0 24px -6px ${glowColor}66`,
            }
          : undefined
      }
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[0.75rem] font-medium transition-all duration-200',
        active
          ? 'border-white/20 bg-white/[0.07] text-ink-primary'
          : 'border-white/10 bg-white/[0.02] text-ink-secondary hover:border-white/20 hover:text-ink-primary',
      )}
    >
      {children}
      {typeof count === 'number' && (
        <span
          className={cn(
            'tnum rounded-full px-1.5 py-0 text-[0.625rem]',
            active ? 'text-ink-primary/80' : 'text-ink-tertiary',
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
}

interface NavState {
  ruleFilter?: string | null;
  sevFilter?: Severity | null;
}

export default function Findings() {
  const { data, isLoading, error } = useQuery<Report, APIError>({
    queryKey: ['findings'],
    queryFn: getFindings,
  });

  const findings = data?.findings ?? [];

  const location = useLocation();
  const navState = (location.state as NavState | null) ?? null;

  const [expanded, setExpanded] = useState<string | null>(null);
  const [sevFilter, setSevFilter] = useState<Severity | null>(null);
  const [ruleFilter, setRuleFilter] = useState<string | null>(null);

  useEffect(() => {
    if (navState?.ruleFilter !== undefined) setRuleFilter(navState.ruleFilter);
    if (navState?.sevFilter !== undefined) setSevFilter(navState.sevFilter);
  }, [navState?.ruleFilter, navState?.sevFilter]);

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
    <div className="space-y-10">
      <header className="space-y-3 animate-fade-in">
        <span className="text-eyebrow">Detected violations</span>
        <h1 className="font-display tnum text-5xl text-ink-primary sm:text-6xl">
          Findings
        </h1>
        <p className="max-w-[70ch] text-[0.9375rem] text-ink-secondary">
          {isLoading
            ? 'Loading findings…'
            : error
              ? 'Backend unavailable.'
              : `${filtered.length} of ${findings.length} findings shown. Each finding is anchored to a specific HIPAA Technical Safeguards rule and CFR section.`}
        </p>
      </header>

      {/* Filter chips */}
      <div className="space-y-5">
        <div className="space-y-2">
          <div className="text-eyebrow">Severity</div>
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
                glowColor={SEVERITY_HEX[s]}
              >
                <span
                  className="h-1.5 w-1.5 rounded-full"
                  style={{ background: SEVERITY_HEX[s] }}
                />
                {s}
              </Chip>
            ))}
          </div>
        </div>

        {ruleIds.length > 0 && (
          <div className="space-y-2">
            <div className="text-eyebrow">Rule</div>
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

      {/* Finding cards */}
      <div className="space-y-6">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <GlassCard key={i} padding="lg" className="space-y-3">
              <div className="skeleton h-3 w-32" />
              <div className="skeleton h-5 w-2/3" />
              <div className="skeleton h-3 w-1/2" />
            </GlassCard>
          ))
        ) : filtered.length === 0 ? (
          <GlassCard padding="lg" className="text-center text-sm text-ink-tertiary">
            No findings match the active filters.
          </GlassCard>
        ) : (
          filtered.map((f, i) => (
            <FindingCard
              key={f.id}
              f={f}
              expanded={expanded === f.id}
              onToggle={() => setExpanded(expanded === f.id ? null : f.id)}
              index={i}
            />
          ))
        )}
      </div>
    </div>
  );
}

function FindingCard({
  f,
  expanded,
  onToggle,
  index,
}: {
  f: Finding;
  expanded: boolean;
  onToggle: () => void;
  index: number;
}) {
  const color = SEVERITY_HEX[f.severity];

  return (
    <div
      className="animate-fade-in"
      style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
    >
      <GlassCard
        interactive={!expanded}
        padding="none"
        className={cn(
          'overflow-hidden',
          expanded && 'border-white/15 bg-white/[0.05]',
        )}
      >
        <button
          type="button"
          onClick={onToggle}
          className="relative flex w-full items-stretch text-left"
        >
          {/* Severity strip */}
          <span
            aria-hidden="true"
            className="w-1 flex-shrink-0"
            style={{ background: color }}
          />

          <div className="flex-1 p-6">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1 space-y-1.5">
                <div className="flex flex-wrap items-center gap-3 text-[0.6875rem] uppercase tracking-[0.18em] text-ink-tertiary">
                  <span>45 CFR § {f.cfr.section}</span>
                  <span className="h-px w-3 bg-white/10" />
                  <span className="font-mono normal-case tracking-normal text-ink-secondary">
                    {f.rule_id}
                  </span>
                </div>
                <h3 className="text-[1.0625rem] font-semibold tracking-tight text-ink-primary">
                  {f.rule_title}
                </h3>
                <div className="font-mono text-[0.75rem] text-ink-tertiary">
                  {f.evidence.file}
                  <span className="text-ink-tertiary/60">:</span>
                  <span className="tnum">{f.evidence.line_start}</span>
                </div>
                <p className="text-[0.875rem] leading-relaxed text-ink-secondary">
                  {f.evidence.why.length > 180
                    ? f.evidence.why.slice(0, 180) + '…'
                    : f.evidence.why}
                </p>
              </div>

              <div className="flex flex-shrink-0 items-center gap-3">
                <SeverityPill sev={f.severity} />
                <ChevronDown
                  className={cn(
                    'h-4 w-4 text-ink-tertiary transition-transform duration-200',
                    expanded && 'rotate-180 text-ink-secondary',
                  )}
                />
              </div>
            </div>
          </div>
        </button>

        {expanded && (
          <div className="animate-fade-only border-t border-white/5 px-6 pb-6 pt-5">
            <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-eyebrow">Evidence</span>
                  <span className="font-mono text-[0.6875rem] text-ink-tertiary">
                    L{f.evidence.line_start}–{f.evidence.line_end}
                  </span>
                </div>
                <pre className="overflow-x-auto rounded-lg border border-white/5 bg-black/30 p-4 font-mono text-[0.75rem] leading-relaxed text-ink-secondary">
                  <code className={SEV_TEXT[f.severity]}>
                    {f.evidence.snippet}
                  </code>
                </pre>
              </div>

              <div className="space-y-5">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-eyebrow">CFR Citation</span>
                    {f.cfr.url && (
                      <a
                        href={f.cfr.url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="text-ink-tertiary transition-colors hover:text-ink-secondary"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                  <div className="text-[0.8125rem] font-semibold text-ink-primary">
                    § {f.cfr.section} — {f.cfr.title}
                  </div>
                  <p className="text-[0.75rem] italic leading-relaxed text-ink-tertiary">
                    {f.cfr.text}
                  </p>
                </div>

                <div className="space-y-2">
                  <span className="text-eyebrow">Remediation</span>
                  <pre className="whitespace-pre-wrap rounded-lg border border-emerald-500/15 bg-emerald-950/20 p-4 font-mono text-[0.75rem] leading-relaxed text-emerald-100">
                    {f.remediation}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </GlassCard>
    </div>
  );
}
