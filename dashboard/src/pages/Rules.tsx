import { useQuery } from '@tanstack/react-query';
import { BookOpen } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { APIError, Rule, getRules, severityBadgeClass } from '@/lib/api';

export default function RulesPage() {
  const { data, isLoading, error } = useQuery<Rule[], APIError>({
    queryKey: ['rules'],
    queryFn: getRules,
  });

  const rules = data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Rules</h1>
        <p className="text-sm text-slate-400">
          HIPAA Technical Safeguards rules enforced by the Aegis scanner. Every
          finding is anchored to one of these CFR-cited controls.
        </p>
      </div>

      {isLoading && (
        <div className="text-sm text-slate-500">Loading rules...</div>
      )}
      {error && !rules.length && (
        <div className="text-sm text-rose-400">Failed to load rules.</div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {rules.map((r) => (
          <Card
            key={r.rule_id}
            className="border-slate-800 bg-slate-900/40 transition-colors hover:border-slate-700"
          >
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-slate-400" />
                  <span className="font-mono text-xs text-slate-400">
                    {r.rule_id}
                  </span>
                </div>
                <Badge className={severityBadgeClass(r.severity)}>
                  {r.severity}
                </Badge>
              </div>
              <CardTitle className="text-base text-slate-100">{r.title}</CardTitle>
              <CardDescription className="font-mono text-xs text-rose-300">
                45 CFR § {r.cfr_section}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed text-slate-300">
                {r.description}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
