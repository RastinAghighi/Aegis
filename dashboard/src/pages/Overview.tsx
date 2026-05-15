import { useQuery } from '@tanstack/react-query';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { listFindings, severityColor, type Severity } from '@/lib/api';

const SEVERITIES: Severity[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
const SEVERITY_FILL: Record<Severity, string> = {
  CRITICAL: '#dc2626',
  HIGH: '#f97316',
  MEDIUM: '#eab308',
  LOW: '#94a3b8',
};

export default function Overview() {
  const { data: findings = [] } = useQuery({
    queryKey: ['findings'],
    queryFn: listFindings,
  });

  const bySeverity = SEVERITIES.map((s) => ({
    severity: s,
    count: findings.filter((f) => f.severity === s).length,
  }));

  const byRule = Object.entries(
    findings.reduce<Record<string, number>>((acc, f) => {
      acc[f.rule_id] = (acc[f.rule_id] || 0) + 1;
      return acc;
    }, {}),
  ).map(([rule, count]) => ({ rule, count }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
        <p className="text-muted-foreground">HIPAA compliance posture across scanned codebase.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {SEVERITIES.map((s) => (
          <Card key={s}>
            <CardHeader className="pb-2">
              <CardDescription>{s}</CardDescription>
              <CardTitle className="text-4xl">
                {findings.filter((f) => f.severity === s).length}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className={severityColor(s)}>{s}</Badge>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Findings by severity</CardTitle>
            <CardDescription>Total: {findings.length}</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={bySeverity}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="severity" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count">
                  {bySeverity.map((entry) => (
                    <Cell key={entry.severity} fill={SEVERITY_FILL[entry.severity]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Findings by rule</CardTitle>
            <CardDescription>HIPAA control distribution</CardDescription>
          </CardHeader>
          <CardContent className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byRule}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="rule" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="count" fill="#0f172a" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
