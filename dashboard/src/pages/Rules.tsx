import { useQuery } from '@tanstack/react-query';

import { GlassCard } from '@/components/ui/glass-card';
import { APIError, Rule, Severity, getRules } from '@/lib/api';
import { cn } from '@/lib/utils';

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

export default function RulesPage() {
  const { data, isLoading, error } = useQuery<Rule[], APIError>({
    queryKey: ['rules'],
    queryFn: getRules,
  });

  const rules = data ?? [];

  return (
    <div className="space-y-12">
      <header className="space-y-3 animate-fade-in">
        <span className="text-eyebrow">Rule catalog</span>
        <h1 className="font-display text-5xl text-ink-primary sm:text-6xl">
          Rules
        </h1>
        <p className="max-w-[70ch] text-[0.9375rem] text-ink-secondary">
          HIPAA Technical Safeguards rules enforced by the Aegis scanner. Every
          finding is anchored to one of these CFR-cited controls.
        </p>
      </header>

      {isLoading && (
        <div className="grid gap-5 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <GlassCard key={i} padding="lg" className="space-y-3">
              <div className="skeleton h-6 w-24" />
              <div className="skeleton h-4 w-2/3" />
              <div className="skeleton h-3 w-full" />
              <div className="skeleton h-3 w-3/4" />
            </GlassCard>
          ))}
        </div>
      )}
      {error && !rules.length && (
        <div className="text-sm text-rose-300/80">Failed to load rules.</div>
      )}

      <div className="grid gap-5 md:grid-cols-2">
        {rules.map((r, i) => (
          <div
            key={r.rule_id}
            className="animate-fade-in"
            style={{ animationDelay: `${Math.min(i, 8) * 40}ms` }}
          >
            <GlassCard interactive padding="lg" className="h-full">
              <div className="flex items-start justify-between gap-4">
                <div className="font-mono text-2xl font-bold uppercase tracking-tight text-ink-primary">
                  {r.rule_id}
                </div>
                <SeverityPill sev={r.severity} />
              </div>

              <h3 className="mt-4 text-[1.0625rem] font-semibold leading-snug tracking-tight text-ink-primary">
                {r.title}
              </h3>

              <div className="mt-1.5 text-[0.6875rem] font-semibold uppercase tracking-[0.16em] text-rose-300/80">
                45 CFR § {r.cfr_section}
              </div>

              <div className="dotted-rule my-4" />

              <p className="text-[0.875rem] leading-relaxed text-ink-secondary">
                {r.description}
              </p>
            </GlassCard>
          </div>
        ))}
      </div>

      {/* Acknowledgments */}
      <section className="pt-8 animate-fade-in" style={{ animationDelay: '200ms' }}>
        <GlassCard padding="lg" className="max-w-[70ch]">
          <span className="text-eyebrow">Acknowledgments</span>
          <h2 className="mt-2 text-base font-semibold tracking-tight text-ink-primary">
            About Aegis
          </h2>
          <p className="mt-2 text-[0.875rem] leading-relaxed text-ink-secondary">
            Aegis is an open-source HIPAA Technical Safeguards auditor. The
            cross-file PHI flow analysis is powered by repo-wide reasoning from
            IBM Bob. Citations reference the U.S. Department of Health & Human
            Services' regulations at 45 CFR § 164.
          </p>
        </GlassCard>
      </section>
    </div>
  );
}
